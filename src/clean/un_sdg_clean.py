
from typing import Dict, Any, List
import pandas as pd
from pathlib import Path

from src.clean.base_clean import DataCleaner
from src.pipeline.utils import ensure_dir

class UNSDGCleaner(DataCleaner):
    """
    Clean UN SDG data
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def save_interim(self, df: pd.DataFrame, out_path: Path) -> None:
        """
        Saves the cleaned DataFrame as a CSV file.
        """
        ensure_dir(out_path.parent)
        df.to_csv(out_path, index=False)
    
    def clean_data(self, indicator_data: List) -> pd.DataFrame:
        """
        NOTE: from un_sdg_fetch.py

        Convert UN SDG data from a List of Dictionaries to a structured DataFrame.
        
        Args:
            indicator_data: Response dictionary from /v1/sdg/Indicator/Data endpoint
            
        Returns:
            pandas.DataFrame with the actual indicator values and metadata
        """
        
        if not indicator_data:
            print("### No indicator data found in the response. ###")
            return pd.DataFrame() # Return empty DataFrame if no data

        rows = []
        for record in indicator_data:
            row = {
                'country_code': record.get('geoAreaCode'),
                'country': record.get('geoAreaName'),
                'year': record.get('timePeriodStart'),
                'value': record.get('value'),
                'indicator': record.get('indicator', [None])[0],
                'series_code': record.get('series'),
                'nature': record.get('attributes', {}).get('Nature'),
                'reporting_type': record.get('dimensions', {}).get('Reporting Type')
            }
            rows.append(row)

        print(f'Extracted {len(rows)} rows.')        
        df = pd.DataFrame(rows)
        
        # Convert value to numeric and coerce errors to NaN
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        # Convert year to integer and coerce errors to NaN
        df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        # Sort by country and year for time series analysis
        df = df.sort_values(['country_code', 'year']).reset_index(drop=True)
        
        # Calculate data quality metrics
        total_records = len(df)
        records_with_values = df['value'].notna().sum()
        countries_count = df['country'].nunique()
        year_range = (df['year'].min(), df['year'].max())
        
        # Count data by nature type
        nature_counts = df['nature'].value_counts().to_dict()
        
        # Identify countries with insufficient data for forecasting
        country_data_counts = df.groupby('country_code').size()
        countries_sufficient = (country_data_counts >= 3).sum()
        countries_insufficient = (country_data_counts < 3).sum()
        
        # Set display options
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_colwidth', 45)
        pd.set_option('display.width', 180)
        pd.set_option('display.expand_frame_repr', False)
        
        print("Converted to Pandas DataFrame.")
        return df

    