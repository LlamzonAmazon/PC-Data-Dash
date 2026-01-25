from typing import Dict, Any, List
import pandas as pd
from pathlib import Path

from src.clean.base_clean import DataCleaner
from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput

class OWIDCleaner(DataCleaner):
    """
    Clean Our World in Data (OWID) CSV data
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
        Convert OWID CSV data from a List of Dictionaries to a structured DataFrame.
        Handles both wide format (years as columns) and long format (year as a column).
        
        Args:
            indicator_data: List of indicator data records from OWID CSV
            
        Returns:
            pandas.DataFrame with standardized columns
        """
        
        if not indicator_data:
            TerminalOutput.info("No indicator data found", indent=1)
            return pd.DataFrame()

        # Convert list of dicts to DataFrame
        df = pd.DataFrame(indicator_data)
        
        TerminalOutput.info(f"Processing CSV with columns: {list(df.columns)}", indent=1)
        
        # Identify common OWID column name patterns
        entity_col = None
        code_col = None
        year_col = None
        value_col = None
        
        # Try to identify entity/country column
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['entity', 'country', 'country_name', 'name']:
                entity_col = col
            elif col_lower in ['code', 'iso3', 'iso_code', 'country_code']:
                code_col = col
            elif col_lower in ['year', 'date']:
                year_col = col
            elif col_lower in ['value', 'state_capacity_index']:
                value_col = col
        
        # If no year column found, assume wide format (years as columns)
        if year_col is None:
            # Identify year columns (numeric columns)
            year_columns = [col for col in df.columns 
                          if col not in [entity_col, code_col] and str(col).replace('.', '').isdigit()]
            
            if year_columns:
                # Wide format - melt to long format
                id_vars = [c for c in [entity_col, code_col] if c is not None]
                df_long = df.melt(
                    id_vars=id_vars,
                    value_vars=year_columns,
                    var_name='year',
                    value_name='value'
                )
                df = df_long
                year_col = 'year'
                value_col = 'value'
        
        # Standardize column names
        rename_map = {}
        if entity_col:
            rename_map[entity_col] = 'country'
        if code_col:
            rename_map[code_col] = 'country_code'
        if year_col and year_col != 'year':
            rename_map[year_col] = 'year'
        if value_col and value_col != 'value':
            # Keep original value column name as indicator if it's not just 'value'
            if value_col.lower() not in ['value', 'val']:
                # We'll add this as indicator name
                pass
        
        if rename_map:
            df = df.rename(columns=rename_map)
        
        # Ensure required columns exist
        if 'country' not in df.columns and entity_col:
            df['country'] = df.get(entity_col, 'Unknown')
        if 'country_code' not in df.columns:
            if code_col:
                df['country_code'] = df.get(code_col, '')
            else:
                df['country_code'] = ''
        
        # Extract indicator name from value column or use default
        indicator_name = 'state_capacity_index'  # Default, can be configured
        if value_col and value_col.lower() not in ['value', 'val']:
            indicator_name = value_col.lower().replace(' ', '_')
        
        # If value column exists, use it; otherwise try to find it
        if 'value' not in df.columns:
            # Try to find numeric column that's not country/year/code
            numeric_cols = df.select_dtypes(include=['number']).columns
            numeric_cols = [c for c in numeric_cols if c not in ['year', 'country_code']]
            if numeric_cols:
                df['value'] = df[numeric_cols[0]]
            else:
                TerminalOutput.info("Warning: No value column found", indent=1)
                df['value'] = None
        
        # Add indicator column
        df['indicator'] = indicator_name
        
        # Convert data types
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        
        # Remove rows with missing values
        df = df.dropna(subset=['value'])
        
        # Ensure standard column order
        standard_cols = ['country_code', 'country', 'indicator', 'year', 'value']
        available_cols = [c for c in standard_cols if c in df.columns]
        df = df[available_cols + [c for c in df.columns if c not in standard_cols]]
        
        # Sort by country, indicator, then by year
        sort_cols = [c for c in ['country', 'indicator', 'year'] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols, ascending=[True] * len(sort_cols)).reset_index(drop=True)
        
        TerminalOutput.summary("  Extracted", f"{len(df)} rows")
        TerminalOutput.complete("Converted to DataFrame")
        
        return df
