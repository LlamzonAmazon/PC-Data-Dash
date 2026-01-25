from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json, requests, pandas as pd

from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput

from .base_fetch import DataFetcher 

"""
Our World in Data (OWID) CSV data fetching client
Downloads CSV files from OWID grapher URLs
"""
class OWIDFetcher(DataFetcher):

    def __init__(self, base: str, credentials: Optional[dict] = None):
        
        super().__init__(base, credentials)
    
    def save_raw_data(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        """
        Saves the unmodified data to JSON (raw data).
        
        Args:
            records (List[Dict[str, Any]]): List of records to save.
            out_dir (Path): Directory to save the file to.
            filename (str): Name of the file to save.
        """
        
        ensure_dir(out_dir)
        (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")

    def fetch_indicator_data(self, csv_url: str) -> List[Dict[str, Any]]:
        """
        Downloads and fetches data from an OWID CSV URL.
        
        Args:
            csv_url (str): Full URL to the OWID CSV file
            
        Returns:
            List[Dict[str, Any]]: List of indicator data records
        """
        
        self._log_fetch_start()
        
        try:
            TerminalOutput.info(f"Downloading CSV from: {csv_url}", indent=1)
            
            # Download CSV file and read directly into DataFrame
            response = requests.get(csv_url, timeout=60)
            response.raise_for_status()
            
            # Read CSV from response content
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            TerminalOutput.info(f"Downloaded CSV with {len(df)} rows, {len(df.columns)} columns", indent=1)
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            TerminalOutput.summary("  Records fetched", f"{len(records)}")
            self._log_fetch_complete(len(records))
            
            return records
            
        except requests.exceptions.HTTPError as e:
            TerminalOutput.info(f"HTTP error downloading CSV: {e}", indent=1)
            raise
        except requests.exceptions.RequestException as e:
            TerminalOutput.info(f"Request error downloading CSV: {e}", indent=1)
            raise
        except Exception as e:
            TerminalOutput.info(f"Error processing CSV: {e}", indent=1)
            raise
