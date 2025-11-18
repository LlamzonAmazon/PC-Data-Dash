from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json, requests, pandas as pd

from src.pipeline.utils import ensure_dir

from .base_fetch import DataClient 

class UNSDGClient(DataClient):
    """
    UN SDG API data fetching client
    """

    def __init__(self, api_url: str, credentials: Optional[dict] = None):
        # Initialize base class and base API URL (currently https://unstats.un.org/SDGAPI/v1/sdg)
        
        super().__init__(api_url, credentials)
        self.base_url = f"{self.api_url}"

    def fetch(self, endpoint, parameters) -> pd.DataFrame:
        # Makes the request to the specified endpoint and returns raw JSON response
        
        self._log_fetch_start()
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=parameters)
        response.raise_for_status()
        self._log_fetch_complete(len(response.json()))
        
        return response.json()

    def validate(self) -> bool:
        # Validates fetched UN SDG data
        
        # Validate non-empty DataFrame
        if not self.data:
            self.logger.warning("No UN SDG data fetched to validate.")
            return False

        # Validate each DataFrame in self.data dictionary
        for key, df in self.data.items():
            if df.empty:
                self.logger.warning(f"{key} DataFrame is empty.")
                return False
        return True
    
    def save_raw_json(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        """
        Saves the unmodified API response to JSON (raw data).
        """
        ensure_dir(out_dir)
        (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")

    def save_interim_csv(self, df: pd.DataFrame, out_path: Path) -> None:
        """
        Saves the tidy DataFrame as a CSV file.
        """
        ensure_dir(out_path.parent)
        df.to_csv(out_path, index=False)


    """ ################################# 
    CLIENT-SPECIFIC METHODS 
    ################################# """
    
    def _goals_list_to_dataframes(self, goals_data):
        # Transforms nested JSON into tidy DataFrames
        
        goal_rows, target_rows, indicator_rows = [], [], []

        for goal in goals_data:
            goal_rows.append({
                "goal_code": goal["code"],
                "goal_title": goal["title"],
                "goal_description": goal.get("description", "")
            })

            for target in goal.get("targets", []):
                target_rows.append({
                    "goal_code": goal["code"],
                    "target_code": target["code"],
                    "target_title": target["title"]
                })

                for indicator in target.get("indicators", []):
                    indicator_rows.append({
                        "goal_code": goal["code"],
                        "target_code": target["code"],
                        "indicator_code": indicator["code"],
                        "indicator_description": indicator.get("description", "")
                    })

        df_goals = pd.DataFrame(goal_rows)
        df_targets = pd.DataFrame(target_rows)
        df_indicators = pd.DataFrame(indicator_rows)

        return df_goals, df_targets, df_indicators

