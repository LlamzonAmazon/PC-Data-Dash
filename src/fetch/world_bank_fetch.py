from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json, requests, pandas as pd

from tenacity import retry, stop_after_attempt, wait_exponential
from src.pipeline.utils import setup_logger, ensure_dir

from .base_fetch import DataFetcher

"""
World Bank API data fetching client
"""
class WorldBankFetcher(DataFetcher):
    
    def __init__(self, base: str, credentials: Optional[dict] = None):
                
        super().__init__(base, credentials)        
        
        self.per_page = 1000                    # Records per page (pagination)
        self.session = requests.Session()       # Reusable HTTP session (faster)
        self.log = setup_logger()               # Logger for progress messages

    def save_raw_data(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        # Saves the unmodified API response to JSON (raw data).

        ensure_dir(out_dir)
        (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")

    
    def fetch_indicator_data(self, indicator: str, countries: Iterable[str], start: int, end: int) -> Dict[str, Any]:
        """
        Fetches all data for a given indicator and list of countries over a year range.

        Args:
            indicator (str): Indicator code to fetch data for.
            countries (Iterable[str]): List of country codes to fetch data for.
            start (int): Start year for data range.
            end (int): End year for data range.

        Returns:
            Dict[str, Any]: Dictionary of records (dictionaries) from the API response
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
            out.extend(data if isinstance(data, list) else []) # Add this page's data if it is a list
            self.log.info("WB %s page %s/%s", indicator, page, meta.get("pages", 1))

            # Stop when all pages are fetched
            if page >= meta.get("pages", 1):
                break
            page += 1

        return out # returns a LIST of indicator records
    

    """ ################################################################## 
    ### CLIENT-SPECIFIC METHODS ###
    ################################################################## """
        
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