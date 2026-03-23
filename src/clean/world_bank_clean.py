
from typing import Dict, Any, List
import pandas as pd

from src.clean.base_clean import DataCleaner
from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput
from pathlib import Path

class WorldBankCleaner(DataCleaner):
    """
    Clean World Bank data
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def save_interim(self, df: pd.DataFrame, out_path: Path) -> None:
        """
        Saves the tidy DataFrame as a CSV file.
        """
        ensure_dir(out_path.parent)
        df.to_csv(out_path, index=False)
    
    def clean_data(self, indicator_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Conert raw API indicator_data into a tidy DataFrame.

        Args:
            indicator_data (List[Dict[str, Any]]): List of indicator_data to convert
            alias (str): User-friendly name for the indicator

        Returns:
            pd.DataFrame: Cleaned DataFrame with country_code (ISO3), country_name, indicator-code,
            indicator, year, and value (aligned with other interim CSVs).
        """

        # Debug: Check first few records
        # if indicator_data:
        #     print(f"\n=== First 3 raw records ===")
        #     for i, rec in enumerate(indicator_data[:3]):
        #         print(f"\nRecord {i}:")
        #         print(f"  country: {rec.get('country')}")
        #         print(f"  countryiso3code: {rec.get('countryiso3code')}")
        #         print(f"  indicator: {rec.get('indicator')}")
        #         print(f"  date: {rec.get('date')}")
        #         print(f"  value: {rec.get('value')}")
    
        rows = []
        for rec in indicator_data or []:
            rows.append({
                "country_code": rec.get("countryiso3code"),
                "country_name": (rec.get("country") or {}).get("value"),
                "indicator-code": (rec.get("indicator") or {}).get("id"),
                "indicator": (rec.get("indicator") or {}).get("value"),
                "year": int(rec.get("date")) if str(rec.get("date")).isdigit() else rec.get("date"),
                "value": rec.get("value")
            })

        df = pd.DataFrame(
            rows,
            columns=[
                "country_code",
                "country_name",
                "indicator-code",
                "indicator",
                "year",
                "value",
            ],
        )

        df = df.sort_values(
            ["country_name", "year"], ascending=[True, True], na_position="last"
        )

        TerminalOutput.summary("  Records", f"{len(df):,}")
        
        return df