from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional
import zipfile
import pandas as pd

from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput

from .base_fetch import DataFetcher

"""
ND-GAIN data fetching client
Extracts indicator data from local ZIP file containing CSV files
"""
class NDGAINFetcher(DataFetcher):

    def __init__(self, base: str, credentials: Optional[dict] = None, **kwargs):
        super().__init__(base, credentials, **kwargs)
        self.base = Path(base)
        self.composite_source = kwargs.get("composite_source", "resources/vulnerability/vulnerability.csv")
        self.indicator_root = kwargs.get("indicator_root", "resources/indicators/")
        
        # Validate ZIP file exists
        if not self.base.exists():
            raise FileNotFoundError(
                f"ND-GAIN ZIP file not found at {self.base}. "
                "Please download it first or adjust the path in settings.yaml"
            )
    
    def save_raw_data(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        """Saves wide ND-GAIN rows to a CSV file."""
        ensure_dir(out_dir)
        pd.DataFrame.from_records(records).to_csv(out_dir / filename, index=False)

    def fetch_indicator_data(self, indicator_codes: Optional[List[str]] = None, chunkSize: int = 10000) -> List[Dict[str, Any]]:
        """
        Fetches indicator score data and composite vulnerability time-series
        from the ND-GAIN ZIP file.
        Returns raw data as list of dictionaries (similar to API response format).
        
        Args:
            indicator_codes (List[str], optional): List of indicator codes to fetch. 
                                                   If None, fetches all available indicators.
        
        Returns:
            List[Dict[str, Any]]: List of records with indicator data
        """
        # Get list of all indicator score files in ZIP
        score_files = self._list_indicator_score_files()
        
        if not score_files:
            TerminalOutput.info("No indicator score files found", indent=1)
            return []
        
        all_records: List[Dict[str, Any]] = []
        
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
                
                # Skip if filtering and this indicator not in filter list.
                # Accept both exact indicator IDs and legacy 7-char prefixes.
                if indicator_codes:
                    if indicator_name not in indicator_codes and indicator_name[:7] not in indicator_codes:
                        continue

                TerminalOutput.print_progress(idx, len(score_files), prefix="  Loading indicators: ")

                try:
                    with zf.open(path) as f:
                        chunk_list = []
                        for chunk in pd.read_csv(f, chunksize=chunkSize):
                            chunk["indicator"] = indicator_name
                            chunk_list.append(chunk)

                        if chunk_list:
                            df = pd.concat(chunk_list, ignore_index=True)
                            records = df.to_dict("records")
                            all_records.extend(records)

                except Exception as e:
                    TerminalOutput.info(f"Error loading {indicator_name}: {e}", indent=1)
                    continue

            # Composite vulnerability time-series is loaded as a pseudo-indicator
            # so it can flow through cleaning/scoring with the same schema.
            if self.composite_source in zf.namelist():
                try:
                    with zf.open(self.composite_source) as f:
                        composite_df = pd.read_csv(f)
                        composite_df["indicator"] = "nd_vulnerability"
                        all_records.extend(composite_df.to_dict("records"))
                except Exception as e:
                    TerminalOutput.info(f"Error loading composite vulnerability series: {e}", indent=1)
            else:
                TerminalOutput.info(
                    f"Composite source not found in archive: {self.composite_source}",
                    indent=1,
                )
        
        TerminalOutput.summary("  Records", f"{len(all_records):,}")
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
        
        indicator_root = self.indicator_root.rstrip("/") + "/"
        # Filter for only indicator score.csv files
        score_files = [
            name for name in all_names
            if name.startswith(indicator_root)
            and name.endswith("/score.csv")
        ]
        
        TerminalOutput.info(f"Found {len(score_files)} indicator files", indent=1)
        return score_files 
    
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
                    country_name = country_data['country_name'].iloc[0]
                    
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
