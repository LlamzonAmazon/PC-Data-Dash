
from typing import Dict, Any, List
import pandas as pd
from src.clean.base_clean import DataCleaner
from src.pipeline.utils import ensure_dir
from pathlib import Path

class WorldBankCleaner(DataCleaner):

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
            pd.DataFrame: Cleaned DataFrame with country, iso3, indicator, year, and value columns.
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
                "country": (rec.get("country") or {}).get("value"),
                "iso3": rec.get("countryiso3code"),
                "indicator-code": (rec.get("indicator") or {}).get("id"),
                "indicator": (rec.get("indicator") or {}).get("value"),
                "year": int(rec.get("date")) if str(rec.get("date")).isdigit() else rec.get("date"),
                "value": rec.get("value")
            })

        # Build DataFrame and sort for readability
        df = pd.DataFrame(rows, columns=["country","iso3","indicator-code","indicator","year","value"])

        # indicator: User-friendly indicator name
        # iso3: country code
        # year: year recorded from
        # value: numerical value of the indicator (NaN if null)
        # country: User-friendly country name
        df = df.sort_values(["indicator-code","iso3","year"], ascending=[True,True,False], na_position="last")

        # print(f'World Bank Cleaned Data:\n {df.head(15)}')
        
        return df