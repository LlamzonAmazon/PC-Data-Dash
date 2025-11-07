from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, List
import json, requests, pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential
from src.pipeline.utils import setup_logger, ensure_dir

# Base URL for all World Bank API requests
BASE = "https://api.worldbank.org/v2"


class WorldBankClient:
    """
    Handles data fetching from the World Bank API.
    """

    def __init__(self, per_page=1000) -> None:
        self.per_page = per_page                # Records per page (pagination)
        self.session = requests.Session()       # Reusable HTTP session (faster)
        self.log = setup_logger()               # Logger for progress messages

    # Retry API calls up to 4 times on failure (exponential backoff)
    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=0.5, max=8))
    def _get(self, url: str, params: Dict[str, Any]):
        """
        Makes one API request with retry on failure.
        """
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()  # Raise error if response failed
        return r

    def fetch_indicator(
        self, indicator: str, countries: Iterable[str], start: int, end: int
    ) -> List[Dict[str, Any]]:
        """
        Fetches all pages of data for one indicator and list of countries.
        """
        country_str = ";".join(countries)  # Combine country codes for query
        page, out = 1, []

        while True:
            url = f"{BASE}/country/{country_str}/indicator/{indicator}"
            params = {
                "date": f"{start}:{end}",     # Year range
                "format": "json",             # Request JSON format
                "per_page": self.per_page,    # Records per page
                "page": page,                 # Current page
            }

            payload = self._get(url, params=params).json()

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

    @staticmethod
    def normalize(records: List[Dict[str, Any]], alias: str) -> pd.DataFrame:
        """
        Converts raw API records into a clean pandas DataFrame.
        """
        rows = []
        for rec in records or []:
            rows.append({
                "country": (rec.get("country") or {}).get("value"),
                "iso3": rec.get("countryiso3code"),
                "indicator": alias,                         # Use user-friendly name
                "year": int(rec.get("date")) if str(rec.get("date")).isdigit() else rec.get("date"),
                "value": rec.get("value")
            })

        # Build DataFrame and sort for readability
        df = pd.DataFrame(rows, columns=["country","iso3","indicator","year","value"])
        return df.sort_values(["indicator","iso3","year"], ascending=[True,True,False], na_position="last")


# ---------- Save helpers ----------

def save_raw_json(records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
    """
    Saves the unmodified API response to JSON (raw data).
    """
    ensure_dir(out_dir)
    (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")


def save_interim_csv(df: pd.DataFrame, out_path: Path) -> None:
    """
    Saves the tidy DataFrame as a CSV file.
    """
    ensure_dir(out_path.parent)
    df.to_csv(out_path, index=False)
