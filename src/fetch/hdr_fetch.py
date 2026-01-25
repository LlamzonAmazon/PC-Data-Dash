from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json, requests, time
import os
from dotenv import load_dotenv

from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput

from .base_fetch import DataFetcher 

"""
HDR (Human Development Report) API data fetching client
"""
class HDRFetcher(DataFetcher):

    def __init__(self, base: str, credentials: Optional[dict] = None):
        
        super().__init__(base, credentials)
        load_dotenv()
        self.api_key = os.getenv("HDR_API_KEY")
        
        if not self.api_key:
            raise ValueError("HDR_API_KEY not found in environment variables. Please set it in .env file.")
    
    def save_raw_data(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        """
        Saves the unmodified API response to JSON (raw data).
        
        Args:
            records (List[Dict[str, Any]]): List of records to save.
            out_dir (Path): Directory to save the file to.
            filename (str): Name of the file to save.
        """
        
        ensure_dir(out_dir)
        (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")

    def fetch_indicator_data(self, indicators_config: List[Dict[str, Any]], start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Fetches data from the HDR API for specified indicators and year range.
        Supports both /query and /query-detailed endpoints.
        
        Args:
            indicators_config (List[Dict[str, Any]]): List of indicator configs with 'code' and optional 'endpoint'
                Example: [{'code': 'GII', 'endpoint': 'query'}, {'code': 'MPI', 'endpoint': 'query-detailed'}]
            start_year (int): Start year for data range
            end_year (int): End year for data range

        Returns:
            List[Dict[str, Any]]: List of indicator data records
        """
        
        self._log_fetch_start()
        all_records = []
        
        # Fetch data for each indicator and year
        for indicator_config in indicators_config:
            indicator = indicator_config['code']
            endpoint = indicator_config.get('endpoint', 'query')  # Default to 'query' if not specified
            
            TerminalOutput.info(f"Fetching indicator: {indicator} (endpoint: {endpoint})", indent=1)
            
            for year in range(start_year, end_year + 1):
                url = f"{self.base}/CompositeIndices/{endpoint}"
                params = {
                    "apikey": self.api_key,
                    "year": year,
                    "indicator": indicator
                }
                
                try:
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        # If response is a list, add indicator and year to each record
                        for record in data:
                            record['indicator'] = indicator
                            record['year'] = year
                            all_records.append(record)
                    elif isinstance(data, dict):
                        # If response is a dict, add indicator and year
                        data['indicator'] = indicator
                        data['year'] = year
                        all_records.append(data)
                    
                    TerminalOutput.print_progress(
                        year - start_year + 1, 
                        end_year - start_year + 1, 
                        prefix=f"  {indicator} ({year}): "
                    )
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        TerminalOutput.info(f"Authentication failed for {indicator} {year}. Check API key.", indent=2)
                    else:
                        TerminalOutput.info(f"HTTP error for {indicator} {year}: {e}", indent=2)
                    continue
                except requests.exceptions.RequestException as e:
                    TerminalOutput.info(f"Request error for {indicator} {year}: {e}", indent=2)
                    continue
        
        TerminalOutput.summary("  Records fetched", f"{len(all_records)}")
        self._log_fetch_complete(len(all_records))
        
        return all_records
