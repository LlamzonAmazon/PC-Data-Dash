from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional
import json, zipfile, pandas as pd

from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput

from .base_fetch import DataFetcher

"""
ND-GAIN data fetching client
Extracts indicator data from local ZIP file containing CSV files
"""
class NDGAINFetcher(DataFetcher):

    def __init__(self, base: str, credentials: Optional[dict] = None):
        
        super().__init__(base, credentials)
        self.base = Path(base)
        
        # Validate ZIP file exists
        if not self.base.exists():
            raise FileNotFoundError(
                f"ND-GAIN ZIP file not found at {self.base}. "
                "Please download it first or adjust the path in settings.yaml"
            )
    
    def save_raw_data(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        """Saves the unmodified data to JSON (raw data)."""
        ensure_dir(out_dir)
        (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")

    def fetch_indicator_data(self, indicator_codes: List[str] = None, chunkSize: int = 10000) -> List[Dict[str, Any]]:
        """
        Fetches all indicator score data from the ND-GAIN ZIP file.
        Returns raw data as list of dictionaries (similar to API response format).
        
        Args:
            indicator_codes (List[str], optional): List of indicator codes to fetch. 
                                                   If None, fetches all available indicators.
        
        Returns:
            List[Dict[str, Any]]: List of records with indicator data
        """
        # Get list of all score files in ZIP
        score_files = self._list_indicator_score_files()
        
        if not score_files:
            TerminalOutput.info("No indicator score files found", indent=1)
            return []
        
        # Load all indicator data
        all_records = []
        
        # Extract ZIP file
        with zipfile.ZipFile(self.base, "r") as zf:
            
            # Iterate over every path leading to a score file for an indicator
            for idx, path in enumerate(score_files, 1):
                # Extract indicator name from path
                p = PurePosixPath(path)
                try:
                    indicator_name = p.parts[2]
                except IndexError:
                    continue
                
                # Skip if filtering and this indicator not in filter list
                if indicator_codes and indicator_name[:7] not in indicator_codes:
                    continue
                
                TerminalOutput.print_progress(idx, len(score_files), prefix="  Loading indicators: ")
                
                try:
                    # Open file from zip file object at current iteration path
                    with zf.open(path) as f:
                        # Read data in chunks to avoid memory issues
                        chunk_list = []
                        for chunk in pd.read_csv(f, chunksize=chunkSize):
                            chunk["indicator"] = indicator_name
                            chunk_list.append(chunk)
                        
                        # Combine chunks and convert to records
                        if chunk_list:
                            df = pd.concat(chunk_list, ignore_index=True)
                            records = df.to_dict('records')
                            all_records.extend(records)
                            
                except Exception as e:
                    TerminalOutput.info(f"Error loading {indicator_name}: {e}", indent=1)
                    continue
        
        TerminalOutput.summary("  Records", f"{len(all_records):,}")
        return all_records

    def fetch_vulnerability_index(self, chunkSize: int = 10000) -> List[Dict[str, Any]]:
        """
        Fetches vulnerability index data from the ND-GAIN ZIP file.
        Looks for CSV files in resources/vulnerability/ folder.
        Returns raw data as list of dictionaries.
        
        Args:
            chunkSize (int): Number of lines to read per file chunk
            
        Returns:
            List[Dict[str, Any]]: List of records with vulnerability index data
        """
        self._log_fetch_start()
        
        # Get list of vulnerability index files in ZIP
        vulnerability_files = self._list_vulnerability_files()
        
        if not vulnerability_files:
            TerminalOutput.info("No vulnerability index files found", indent=1)
            return []
        
        # Load all vulnerability index data
        all_records = []
        
        # Extract ZIP file
        with zipfile.ZipFile(self.base, "r") as zf:
            
            # Iterate over every vulnerability file
            for idx, path in enumerate(vulnerability_files, 1):
                # Extract file name for indicator identification
                p = PurePosixPath(path)
                try:
                    file_name = p.stem  # e.g., "vulnerability_index" or "vulnerability"
                    indicator_name = "vulnerability_index"
                except Exception:
                    indicator_name = "vulnerability_index"
                
                TerminalOutput.print_progress(idx, len(vulnerability_files), prefix="  Loading vulnerability files: ")
                
                try:
                    # Open file from zip file object
                    with zf.open(path) as f:
                        # Read data in chunks to avoid memory issues
                        chunk_list = []
                        for chunk in pd.read_csv(f, chunksize=chunkSize):
                            chunk["indicator"] = indicator_name
                            chunk_list.append(chunk)
                        
                        # Combine chunks and convert to records
                        if chunk_list:
                            df = pd.concat(chunk_list, ignore_index=True)
                            records = df.to_dict('records')
                            all_records.extend(records)
                            
                except Exception as e:
                    TerminalOutput.info(f"Error loading {path}: {e}", indent=1)
                    continue
        
        TerminalOutput.summary("  Records", f"{len(all_records):,}")
        self._log_fetch_complete(len(all_records))
        return all_records

    """ ################################################################## 
    ### CLIENT-SPECIFIC METHODS ###
    ################################################################## """

    def _list_indicator_score_files(self) -> List[str]:
        """
        Get all indicator score.csv files in the ZIP file.
        
        Returns:
            List[str]: List of file paths to score.csv files
        """
        with zipfile.ZipFile(self.base, "r") as zf:
            all_names = zf.namelist()
        
        # Filter for only indicator score.csv files
        score_files = [
            name for name in all_names
            if name.startswith("resources/indicators/")
            and name.endswith("/score.csv")
        ]
        
        TerminalOutput.info(f"Found {len(score_files)} indicator files", indent=1)
        return score_files
    
    def _list_vulnerability_files(self) -> List[str]:
        """
        Get all CSV files in the resources/vulnerability/ folder of the ZIP file.
        
        Returns:
            List[str]: List of file paths to vulnerability CSV files
        """
        with zipfile.ZipFile(self.base, "r") as zf:
            all_names = zf.namelist()
        
        # Filter for CSV files in vulnerability folder
        vulnerability_files = [
            name for name in all_names
            if name.startswith("resources/vulnerability/")
            and name.endswith(".csv")
        ]
        
        TerminalOutput.info(f"Found {len(vulnerability_files)} vulnerability index files", indent=1)
        return vulnerability_files 
    
    '''
    # TOO MUCH OUTPUT – WILL FLOOD YOUR SHIT
    def print_dataset(self, df: pd.DataFrame) -> None:
        """
        Print the dataset in a detailed, readable format.
        Shows all indicators with their data organized by country and year.
        
        Args:
            df (pd.DataFrame): Tidy DataFrame to display
        """

        if len(df) <= 0:
            print("No data to display.")
            return

        # Get all indicators (remove duplicates and sort alphabetically)
        indicators = sorted(df["indicator"].unique())
        
        # Summary header
        print("\n" + "="*100)
        print("ND-GAIN INDICATOR SCORE DATA - COMPLETE DATASET".center(100))
        print("="*100)
        print(f"Total Indicators: {len(indicators)}")
        print(f"Total Rows: {df.shape[0]:,}")
        print(f"Total Columns: {df.shape[1]}")
        print("="*100)
        sys.stdout.flush()
        
        # Get year range from data
        year_range = sorted(df['year'].unique())
        
        # Display each indicator with all its data
        for idx, indicator in enumerate(indicators, 1):
            try:
                indicator_data = df[df["indicator"] == indicator].copy()
                countries = sorted(indicator_data['country_code'].unique())
                
                print(f"\n\n{'='*100}")
                print(f"INDICATOR {idx}/{len(indicators)}: {indicator.upper()}".center(100))
                print(f"{'='*100}")
                print(f"Number of Countries: {len(countries)}")
                print(f"Year Range: {year_range[0]} - {year_range[-1]} ({len(year_range)} years)")
                print(f"{'-'*100}")
                sys.stdout.flush()
                
                # Display all countries for this indicator
                for country_idx, country_code in enumerate(countries, 1):
                    country_data = indicator_data[indicator_data['country_code'] == country_code]
                    country_name = country_data['country'].iloc[0]
                    
                    print(f"\n  [{country_idx:3d}] {country_name} ({country_code})")
                    print(f"      {'-'*94}")
                    
                    # Display values by year in a readable format
                    years_per_line = 5
                    year_values = country_data.set_index('year')['value'].to_dict()
                    
                    for i in range(0, len(year_range), years_per_line):
                        year_batch = year_range[i:i+years_per_line]
                        value_strings = []
                        
                        for year in year_batch:
                            value = year_values.get(year)
                            if pd.notna(value):
                                # Format with appropriate decimal places
                                if abs(value) >= 1000:
                                    value_str = f"{value:>10.2f}"
                                elif abs(value) >= 1:
                                    value_str = f"{value:>10.4f}"
                                else:
                                    value_str = f"{value:>10.6f}"
                                value_strings.append(f"{year}: {value_str}")
                            else:
                                value_strings.append(f"{year}: {'N/A':>10}")
                        
                        # Print the line with proper spacing
                        print(f"      {' | '.join(value_strings)}")
                
                print(f"\n{'-'*100}")
                print(f"[OK] Completed: {indicator} ({len(countries)} countries)")
                sys.stdout.flush()
                
            except Exception as e:
                print(f"\nERROR processing indicator {indicator}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                continue
        
        print(f"\n\n{'='*100}")
        print("END OF ALL INDICATOR DATA".center(100))
        print(f"{'='*100}\n")
        sys.stdout.flush()
    '''
