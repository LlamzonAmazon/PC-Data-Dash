from typing import Dict, Any, List
import pandas as pd
from pathlib import Path

from src.clean.base_clean import DataCleaner
from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput

class HDRCleaner(DataCleaner):
    """
    Clean HDR (Human Development Report) data
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def save_interim(self, df: pd.DataFrame, out_path: Path) -> None:
        """
        Saves the cleaned DataFrame as a CSV file.
        """
        ensure_dir(out_path.parent)
        df.to_csv(out_path, index=False)
    
    def clean_data(self, indicator_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert HDR data from a List of Dictionaries to a structured DataFrame.
        
        Args:
            indicator_data: List of indicator data records from HDR API
            
        Returns:
            pandas.DataFrame with standardized columns
        """
        
        if not indicator_data:
            TerminalOutput.info("No indicator data found", indent=1)
            return pd.DataFrame()

        rows = []
        for record in indicator_data:
            # Extract common fields - adjust based on actual API response structure
            row = {
                'country_code': record.get('iso3') or record.get('countryCode') or record.get('ISO3'),
                'country': record.get('country') or record.get('countryName') or record.get('Country'),
                'year': record.get('year'),
                'value': record.get('value') or record.get('index') or record.get('Value'),
                'indicator': record.get('indicator')
            }
            
            # Add any additional fields that might be present
            for key, value in record.items():
                if key not in ['iso3', 'countryCode', 'ISO3', 'country', 'countryName', 'Country', 
                              'year', 'value', 'index', 'Value', 'indicator']:
                    row[key.lower().replace(' ', '_')] = value
            
            rows.append(row)

        TerminalOutput.summary("  Extracted", f"{len(rows)} rows")
        df = pd.DataFrame(rows)
        
        # Convert value to numeric and coerce errors to NaN
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        # Convert year to integer and coerce errors to NaN
        df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        
        # Remove rows with missing values
        df = df.dropna(subset=['value'])
        
        # Ensure standard column order
        standard_cols = ['country_code', 'country', 'indicator', 'year', 'value']
        available_cols = [c for c in standard_cols if c in df.columns]
        df = df[available_cols + [c for c in df.columns if c not in standard_cols]]
        
        # Sort by country, indicator, then by year
        df = df.sort_values(['country', 'indicator', 'year'], ascending=[True, True, True]).reset_index(drop=True)
        
        TerminalOutput.complete("Converted to DataFrame")
        return df
