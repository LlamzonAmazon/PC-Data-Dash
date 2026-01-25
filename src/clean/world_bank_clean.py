
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
        Convert raw API indicator_data into a tidy DataFrame.

        Args:
            indicator_data (List[Dict[str, Any]]): List of indicator_data to convert

        Returns:
            pd.DataFrame: Cleaned DataFrame with country, iso3, indicator, year, and value columns.
        """
    
        rows = []
        for rec in indicator_data or []:
            rows.append({
                "country": (rec.get("country") or {}).get("value"),
                "iso3": rec.get("countryiso3code"),
                "indicator": (rec.get("indicator") or {}).get("value"),
                "year": int(rec.get("date")) if str(rec.get("date")).isdigit() else rec.get("date"),
                "value": rec.get("value")
            })

        # Build DataFrame
        df = pd.DataFrame(rows)

        # Convert data types
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        
        # Remove rows with missing values
        df = df.dropna(subset=['value'])
        
        # Sort by country, indicator, then by year
        df = df.sort_values(['country', 'indicator', 'year'], ascending=[True, True, True]).reset_index(drop=True)

        TerminalOutput.summary("  Extracted", f"{len(df):,} rows")
        TerminalOutput.complete("Converted to DataFrame")
        
        return df