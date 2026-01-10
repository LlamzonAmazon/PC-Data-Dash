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
    

    """ ################################################################## 
    ### CLIENT-SPECIFIC METHODS ###
    ################################################################## """