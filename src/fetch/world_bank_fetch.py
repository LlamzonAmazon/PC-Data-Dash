from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json, requests, pandas as pd

from tenacity import retry, stop_after_attempt, wait_exponential
from src.pipeline.utils import setup_logger, ensure_dir

from .base_fetch import DataClient

"""
World Bank API data fetching client
"""
class WorldBankClient(DataClient):
    
    def __init__(self, base: str, credentials: Optional[dict] = None):
                
        super().__init__(base, credentials)        
        
        self.per_page = 1000                    # Records per page (pagination)
        self.session = requests.Session()       # Reusable HTTP session (faster)
        self.log = setup_logger()               # Logger for progress messages

    def save_raw_json(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        # Saves the unmodified API response to JSON (raw data).

        ensure_dir(out_dir)
        (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")

    def save_interim_csv(self, df: pd.DataFrame, out_path: Path) -> None:
        """
        Saves the tidy DataFrame as a CSV file.
        """
        ensure_dir(out_path.parent)
        df.to_csv(out_path, index=False)
    
    # TODO: Combine these two methods into one as fetch_indicator_data as defined by the abstract class (DataClient – base_fetch.py)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=0.5, max=8))
    def fetch(self, base: str, parameters: Dict[str, Any]):   
        """
        Fetches data from a World Bank API with retry logic.
        
        Returns:
            r: Response object from the requests library
        """

        r = self.session.get(base, params=parameters, timeout=30)
        r.raise_for_status()  # Raise error if response failed
        return r
    
    def fetch_indicator(
        self, 
        indicator: str, 
        countries: Iterable[str], 
        start: int, 
        end: int
    ) -> List[Dict[str, Any]]:
        """
        Fetches all data for a given indicator and list of countries over a year range.
        Returns:
            List of records (dictionaries) from the API response
        """

        country_str = ";".join(countries)  # Combine country codes for query
        page, out = 1, []

        while True:
            url = f"{self.base}/country/{country_str}/indicator/{indicator}"
            params = {
                "date": f"{start}:{end}",     # Year range
                "format": "json",             # Request JSON format
                "per_page": self.per_page,    # Records per page
                "page": page,                 # Current page
            }

            payload = self.fetch(url, parameters=params).json()

            # API returns [metadata, data]; stop if structure invalid
            if not isinstance(payload, list) or len(payload) < 2:
                break

            meta, data = payload[0], payload[1]
            out.extend(data if isinstance(data, list) else [])  # Add this page’s data
            self.log.info("WB %s page %s/%s", indicator, page, meta.get("pages", 1))

            # Stop when all pages are fetched
            if page >= meta.get("pages", 1):
                break
            page += 1

        return out
    

    """ ################################################################## 
    ### CLIENT-SPECIFIC METHODS ###
    ################################################################## """
