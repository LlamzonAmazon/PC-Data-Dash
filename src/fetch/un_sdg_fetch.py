from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json, requests, time, pandas as pd

from src.pipeline.utils import ensure_dir

from .base_fetch import DataClient 

"""
UN SDG API data fetching client
"""
class UNSDGClient(DataClient):

    def __init__(self, base: str, credentials: Optional[dict] = None):
        
        super().__init__(base, credentials)
    
    def save_raw_json(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        # Saves the unmodified API response to JSON (raw data).
        
        ensure_dir(out_dir)
        (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")

    def save_interim_csv(self, df: pd.DataFrame, out_path: Path) -> None:
        # Saves the tidy DataFrame as a CSV file.
        
        ensure_dir(out_path.parent)
        df.to_csv(out_path, index=False)


    """ ################################################################## 
    ### CLIENT-SPECIFIC METHODS ###
    ################################################################## """

    def fetch_indicator_data(self, endpoint: str, parameters) -> pd.DataFrame:
        """
            Fetches data from the API by pageSize.\n
            Then calls `indicator_data_to_dataframe` to convert parsed data into DataFrame.
            URL: https://unstats.un.org/sdgs/UNSDGAPIV5/v1/sdg/Indicator/Data
            
            Args:
                endpoint (str): Used to store endpoint URL only in `settings.yaml`; should be `/indicator/data`.
                parameters (Dict[str,str]): Parameters for endpoint call.
        """
        
        # Initialize loop variables
        url = f"{self.base}{endpoint}" 
        all_data = {}
        page = parameters['page']
        page_size = parameters['pageSize']
        totalElements = 0
        
        self._log_fetch_start()
        print('Pages parsed: ', end="")
        
        while True:
            # Update parameters with current page
            parameters['page'] = page
            parameters['pageSize'] = page_size
                
            # Make request        
            response = requests.get(url, params=parameters)
            response.raise_for_status()
            data = response.json()
            
            # Validate response
            if not data or len(data) == 0:
                print(f"No more data on page {page}")
                break
            
            # Add data to all data
            if page <= 1:
                all_data = data
                totalPages = data['totalPages'] # response includes number of pages included in response
                totalElements = data['totalElements'] # response includes number of elements included in response
            else:
                for record in data['data']:
                    all_data['data'].append(record)
                    
            print(f'{page}/{totalPages} ', end="")
            
            # Check if this was the last page
            if page >= totalPages:
                break
            
            # Prep next loop
            page += 1
            time.sleep(0.5)
        
        print(f'Done! \nExporting indicator data to Pandas DataFrame ...')
        self._log_fetch_complete(totalElements)
        
        return self.indicator_data_to_dataframe(all_data)
    
    def indicator_data_to_dataframe(self, indicator_data) -> pd.DataFrame:
        """
        Convert UN SDG API indicator data response to a structured DataFrame.
        
        Args:
            indicator_data: Response dictionary from /v1/sdg/Indicator/Data endpoint
            
        Returns:
            pandas.DataFrame with the actual indicator values and metadata
        """
        
        # Extract the data array
        data_list = indicator_data.get('data', [])
        
        if not data_list:
            print("### No indicator data found in the response. ###")
            return pd.DataFrame() # Return empty DataFrame if no data
        
        rows = []
        for record in data_list:
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
        
        # Convert value to numeric, coercing errors to NaN
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        # Convert year to integer
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
