from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from src.pipeline.utils import ensure_dir
from src.pipeline.terminal_output import TerminalOutput

from .base_fetch import DataFetcher
from .fetch_handler import FetchHandler, FetchHandlerConfig


"""
UN SDG API data fetching client
"""
class UNSDGFetcher(DataFetcher):

    def __init__(
        self,
        base: str,
        credentials: Optional[dict] = None,
        handler_config: Optional[FetchHandlerConfig] = None,
    ):
        super().__init__(base, credentials)
        # Use provided config or defaults (robust for autonomous execution)
        self._handler = FetchHandler(handler_config or FetchHandlerConfig())
    
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

    def fetch_indicator_data(
        self,
        endpoint: str,
        parameters,
        dimension_filters=None,
    ) -> Dict[str, Any]:
        """
            Fetches data from the API by pageSize using FetchHandler for robust retries.
            URL: https://unstats.un.org/sdgs/UNSDGAPIV5/v1/sdg/Indicator/Data
            
            Args:
                endpoint (str): Used to store endpoint URL only in `settings.yaml`; should be `/indicator/data`.
                parameters (Dict[str,str]): Parameters for endpoint call.
                dimension_filters (List[str]): Optional list of dimension values to filter by

            Returns:
                Dict[str, Any]: Dictionary containing the indicator data.
        """
        # Get Valid Country Codes first
        valid_countries = self._get_country_codes()
        
        url = f"{self.base}{endpoint}"
        all_data: Dict[str, Any] = {}
        page = parameters.get('page', 1)
        total_pages = 1
        
        while True:
            parameters['page'] = page
            context = f"bulk page {page}"
            
            # FetchHandler handles retries, timeouts, 5xx, etc.
            response = self._handler.get(url, params=parameters, context=context)
            data = response.json()
            
            if not data or len(data) == 0:
                break
            
            if page <= 1:
                all_data = data
                total_pages = data.get('totalPages', 1)
            else:
                all_data['data'].extend(data.get('data', []))
            
            TerminalOutput.print_progress(page, total_pages, prefix="  Fetching pages: ")
            
            if page >= total_pages:
                break
            page += 1

        flat_records = [self._flatten_record(r) for r in all_data.get('data', [])]
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

    def fetch_indicator_by_dimension(
        self,
        endpoint: str,
        indicator_code: str,
        dimension_name: str,
        dimension_values: List[str],
        time_period_array: List[int],
        page_size: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetches one indicator by requesting each dimension value separately.
        Use for indicators where the API returns correct dimension labels only
        when filtered (e.g. 3.d.1 with IHR Capacity IHR01–IHR13).

        Args:
            endpoint: e.g. /Indicator/Data
            indicator_code: e.g. "3.d.1"
            dimension_name: API dimension name, e.g. "IHR Capacity"
            dimension_values: list of values to request, e.g. ["IHR01", "IHR02", ...]
            time_period_array: years to request
            page_size: records per page

        Returns:
            List of records in the same shape as fetch_indicator_data()["data"].
        """
        valid_countries = self._get_country_codes()
        url = f"{self.base}{endpoint}"
        all_records: List[Dict[str, Any]] = []

        for dim_value in dimension_values:
            params = {
                "indicator": indicator_code,
                "timePeriod": time_period_array,
                "page": 1,
                "pageSize": page_size,
                "dimensions": json.dumps([{"name": dimension_name, "values": [dim_value]}]),
            }
            page = 1
            while True:
                params["page"] = page
                context = f"{indicator_code} {dim_value} page {page}"
                
                # FetchHandler handles retries, timeouts, 5xx, etc.
                response = self._handler.get(url, params=params, context=context)
                data = response.json()
                
                if not data or not data.get("data"):
                    break
                for record in data["data"]:
                    flat = self._flatten_record(record)
                    if valid_countries and str(flat.get("geoAreaCode", "")) not in valid_countries:
                        continue
                    all_records.append(flat)
                total_pages = data.get("totalPages", 1)
                TerminalOutput.print_progress(page, total_pages, prefix=f"  {indicator_code} {dim_value} ")
                if page >= total_pages:
                    break
                page += 1

        TerminalOutput.summary(f"  {indicator_code} by {dimension_name}", f"{len(all_records)} records")
        return all_records

    """ ################################################################## 
    ### CLIENT-SPECIFIC METHODS ###
    ################################################################## """

    def _flatten_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten a single API record by merging the 'dimensions' dict into the top level.
        Used by fetch_indicator_data and fetch_indicator_by_dimension.
        """
        flat = {k: v for k, v in record.items() if k != "dimensions"}
        dims = record.get("dimensions") or {}
        if isinstance(dims, dict):
            flat.update(dims)
        return flat

    def _get_country_codes(self) -> set[str]:
        """
        Fetches the GeoArea Tree and extracts all codes that are of type 'Country'.
        Returns a set of country codes (as strings).
        """
        url = "https://unstats.un.org/sdgs/UNSDGAPIV5/v1/sdg/GeoArea/Tree"
        
        try:
            response = self._handler.get(url, context="GeoArea/Tree")
            tree_data = response.json()
            
            country_codes: set[str] = set()
            
            def _traverse(node):
                if node.get('type') == 'Country':
                    country_codes.add(str(node.get('geoAreaCode')))
                children = node.get('children')
                if children and isinstance(children, list):
                    for child in children:
                        _traverse(child)
            
            for root_node in tree_data:
                _traverse(root_node)
                
            TerminalOutput.info(f"Identified {len(country_codes)} countries", indent=1)
            return country_codes
            
        except Exception as e:
            TerminalOutput.info(f"Warning: Failed to fetch country codes: {e}", indent=1)
            return set()