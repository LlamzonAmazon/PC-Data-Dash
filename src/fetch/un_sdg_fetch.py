from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json, requests, time

from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput

from .base_fetch import DataFetcher 

"""
UN SDG API data fetching client
"""
class UNSDGFetcher(DataFetcher):

    def __init__(self, base: str, credentials: Optional[dict] = None):
        
        super().__init__(base, credentials)
    
    def save_raw_data(self, records: Dict[str, Any], out_dir: Path, filename: str) -> None:
        """
        Saves the unmodified API response to JSON (raw data).
        
        Args:
            records (Dict[str, Any]): Dictionary of records to save.
            out_dir (Path): Directory to save the file to.
            filename (str): Name of the file to save.
        """
        
        ensure_dir(out_dir)
        (out_dir / filename).write_text(json.dumps(records, indent=2), encoding="utf-8")

    def fetch_indicator_data(self, endpoint: str, parameters, dimension_filters=None) -> Dict[str, Any]:
        """
            Fetches data from the API by pageSize.
            Then calls `indicator_data_to_dataframe` to convert parsed data into DataFrame.
            URL: https://unstats.un.org/sdgs/UNSDGAPIV5/v1/sdg/Indicator/Data
            
            Args:
                endpoint (str): Used to store endpoint URL only in `settings.yaml`; should be `/indicator/data`.
                parameters (Dict[str,str]): Parameters for endpoint call.
                dimension_filters (List[str]): Optional list of dimension values to filter by

            Returns:
                Dict[str, Any]: Dictionary containing the indicator data. (currently 13009 records over 14 pages)
        """
        
        # 0. Get Valid Country Codes first
        valid_countries = self._get_country_codes()
        
        # Initialize loop variables
        url = f"{self.base}{endpoint}" 
        all_data = {}
        page = parameters['page']
        totalElements = 0
        
        while True:
            # Update parameters with current page
            parameters['page'] = page
            
            # Make request with retry logic for rate limiting
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    response = requests.get(url, params=parameters, timeout=90)
                    response.raise_for_status()
                    data = response.json()
                    break  # Success, exit retry loop
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limited
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 2 ** retry_count  # Exponential backoff: 2, 4, 8 seconds
                            TerminalOutput.info(f"Rate limited, retrying in {wait_time}s...", indent=1)
                            time.sleep(wait_time)
                        else:
                            raise  # Max retries exceeded
                    else:
                        raise  # Other HTTP error, don't retry
                        
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count
                        TerminalOutput.info(f"Request failed, retrying in {wait_time}s...", indent=1)
                        time.sleep(wait_time)
                    else:
                        raise  # Max retries exceeded
            
            # Validate response
            if not data or len(data) == 0:
                break
            
            # Handle first page initialization
            if page <= 1:
                all_data = data
                totalPages = data.get('totalPages', 1) 
                totalElements = data.get('totalElements', 0)
            else:
                # Append subsequent pages' data
                all_data['data'].extend(data.get('data', []))
            
            # Show progress
            TerminalOutput.print_progress(page, totalPages, prefix="  Fetching pages: ")
            
            # Check if this was the last page
            if page >= totalPages:
                break
            
            # Prep next loop
            page += 1

        flat_records = []
        for record in all_data.get('data', []):
            flat_rec = {k: v for k, v in record.items() if k != 'dimensions'}
            dims = record.get('dimensions', {})
            if dims and isinstance(dims, dict):
                flat_rec.update(dims)
            
            flat_records.append(flat_rec)
        
        all_data['data'] = flat_records
        filtered_data = []

        for record in all_data['data']:
            keep_record = True
            
            if valid_countries:
                geo_code = str(record.get('geoAreaCode', ''))
                if geo_code not in valid_countries:
                    keep_record = False
            
            if keep_record and dimension_filters:
                record_values = str(list(record.values()))
                if not any(f_val in record_values for f_val in dimension_filters):
                    keep_record = False
            
            if keep_record:
                filtered_data.append(record)

        TerminalOutput.summary("  Filtered", f"{len(all_data['data'])} -> {len(filtered_data)} records")
        all_data['data'] = filtered_data

        return all_data

    def fetch_series_data(self, series_codes: list[str], start_year: int = 2010) -> Dict[str, Any]:
    

        #Fetches data from /Series/Data for specific series codes.
        #NOTE: API requires repeated seriesCode params (not comma-separated).


        url = f"{self.base}/Series/Data"

        # 0) Get valid country codes first
        valid_countries = self._get_country_codes()

        page = 1
        page_size = 2000
        total_pages = None
        all_data: Dict[str, Any] = {"data": []}

        while True:
            params = []
            for code in series_codes:
                params.append(("seriesCode", code))
            params += [
                ("startPeriod", start_year),
                ("page", page),
                ("pageSize", page_size),
            ]

            response = requests.get(url, params=params, timeout=90)
            response.raise_for_status()
            data = response.json()

            if total_pages is None:
                total_pages = data.get("totalPages", 1)
                # keep top-level metadata
                for k in ["size", "totalElements", "totalPages", "pageNumber", "attributes", "dimensions"]:
                    if k in data:
                        all_data[k] = data[k]

            all_data["data"].extend(data.get("data", []))

            TerminalOutput.print_progress(page, total_pages, prefix="  Fetching pages: ")

            if page >= total_pages:
                break
            page += 1

        # Flatten dimensions (same as your indicator fetch)
        flat_records = []
        for record in all_data.get("data", []):
            flat_rec = {k: v for k, v in record.items() if k != "dimensions"}
            dims = record.get("dimensions", {})
            if dims and isinstance(dims, dict):
                flat_rec.update(dims)
            flat_records.append(flat_rec)
        all_data["data"] = flat_records

        # Filter: country codes + optional “Reporting Type” == G
        filtered = []
        for rec in all_data["data"]:
            keep = True

            if valid_countries:
                geo_code = str(rec.get("geoAreaCode", ""))
                if geo_code not in valid_countries:
                    keep = False

            # if Reporting Type exists, force country-level only
            if keep and "Reporting Type" in rec:
                if rec.get("Reporting Type") != "G":
                    keep = False

            if keep:
                filtered.append(rec)

        TerminalOutput.summary("  Filtered", f"{len(all_data['data'])} -> {len(filtered)} records")
        all_data["data"] = filtered

        return all_data

    

    """ ################################################################## 
    ### CLIENT-SPECIFIC METHODS ###
    ################################################################## """
    
    def _get_country_codes(self) -> set[str]:
        """
        Fetches the GeoArea Tree and extracts all codes that are of type 'Country'.
        Returns a set of country codes (as strings).
        """
        url = "https://unstats.un.org/sdgs/UNSDGAPIV5/v1/sdg/GeoArea/Tree"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            tree_data = response.json()
            
            country_codes = set()
            
            # Helper to recursively find countries
            def _traverse(node):
                if node.get('type') == 'Country':
                    country_codes.add(str(node.get('geoAreaCode')))
                
                children = node.get('children')
                if children and isinstance(children, list):
                    for child in children:
                        _traverse(child)
            
            # Start traversal on all root nodes
            for root_node in tree_data:
                _traverse(root_node)
                
            TerminalOutput.info(f"Identified {len(country_codes)} countries", indent=1)
            return country_codes
            
        except Exception as e:
            TerminalOutput.info(f"Warning: Failed to fetch country codes: {e}", indent=1)
            return set()
        

    