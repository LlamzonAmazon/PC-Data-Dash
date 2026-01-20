'''
This module fetches data from all sources.

Responsible for fetching and structuring data from all sources.
'''

from __future__ import annotations

import sys, pandas as pd
from pathlib import Path
import logging
from typing import Dict

from src.fetch.fetch_factory import DataFetcherFactory
from src.pipeline.utils import project_root, setup_logger

class FetchData:
    """
    Essentially the main of the module.
    """

    def __init__(self, config_path):

        self.config_path = config_path
        self.log = logging.getLogger(__name__)

    def fetch(self) -> Dict[str, list]:
        """
        Fetch data from all sources.
        Returns a dictionary containing all the fetched data.
        """

        # Path to your configuration file
        cfg_path = Path(self.config_path)

        # Stop if config file is missing
        if not cfg_path.exists():
            self.log.error("Missing config at %s", cfg_path)
            sys.exit(1)

        # Create Data Fetcher Factory
        fetcher_factory = DataFetcherFactory(config_path=cfg_path)
        
        # Load full configuration file
        cfg = fetcher_factory.get_config()  
        paths, runtime = cfg["paths"], cfg["runtime"]

        """ ################################################################## 
        ### UN SDG FETCHING ###
        ################################################################## """
        
        unsdgClient = fetcher_factory.create_client('unsdg')
        
        unsdg_indicator_data_endpoint = cfg['unsdg']['api_paths']['indicator_data_endpoint']
        unsdg_indicator_codes = [indicator['code'] for indicator in cfg['unsdg']['indicators']]
        
        # Fetch indicator data for ALL countries and specified years
        print(f'Fetching UN SDG data for {len(unsdg_indicator_codes)} indicators...')

        # indicator_data_dict: Dictionary containing all indicator data
        # indicator_data_dict['data']: List of all indicator data records
        # NOTE: Using timePeriod array instead of timePeriodStart/End
        #       because the API only returns start year when using range params
        start_year = cfg['unsdg']['start_year']
        end_year = cfg['unsdg']['end_year']
        time_period_array = list(range(start_year, end_year + 1))  # e.g. [2010, 2011, ..., 2024]
        
        indicator_data_dict = unsdgClient.fetch_indicator_data(
            unsdg_indicator_data_endpoint, 
            parameters={
                "indicator": unsdg_indicator_codes,
                # areaCode excluded; returns ALL if not specified
                "timePeriod": time_period_array,  # Use array of years, NOT start/end range!
                "page" : 1, # Page Number
                "pageSize": cfg['runtime']['per_page'] # Number of records per page/response
            },
            dimension_filters=cfg['unsdg'].get('dimension_filters', None)
        )
        
        # Only saving the raw indicator data contained in the dictionary
        # NOTE: Still have the dictionary structure, just extracting the list of records
        # May be useful to keep the dictionary structure for later processing
        unsdg_indicator_list = indicator_data_dict['data']

        # Save raw data locally
        if runtime.get("save_raw", True):
            unsdg_csv_path = project_root() / paths['data_raw']
            unsdgClient.save_raw_data(
                unsdg_indicator_list, 
                unsdg_csv_path,
                "un_sdg_raw.json"
            )
        
        """ ################################################################## 
        ### WORLD BANK FETCHING ###
        ################################################################## """

        wbClient = fetcher_factory.create_client('worldbank')
        
        wb = cfg["worldbank"]
        recs = []

        # Loop through each indicator and fetch its data
        print("Fetching World Bank data...")
        for ind in wb["indicators"]:
            code, alias = ind["code"], ind.get("alias", ind["code"])

            # Fetch all records (2010–2024, all countries)
            # NOTE: Countries are aggregated into income classification groups because we're using 'all'
            # e.g. High income, low income, lower middle, etc.
            # This is done by the API

            # fetch_indicator_data() returns a LIST of indicator records
            recs.extend(wbClient.fetch_indicator_data(code, 
                wb["countries"], 
                wb["start_year"], 
                wb["end_year"]
            ))

        # Save raw data locally
        # Saves recs – a LIST of indicator records
        if runtime.get("save_raw", True):
            wbClient.save_raw_data(
                recs,
                project_root() / paths["data_raw"],
                "world_bank_raw.json"
            )
        
        
        """ ################################################################## 
        ### ND-GAIN FETCHING ###
        ################################################################## """
        
        ndGainClient = fetcher_factory.create_client('ndgain')
        
        ndgain_vulnerability_indicators = cfg['ndgain']['indicators']['vulnerability']
        
        # Get vulnerability scores as a list of dictionaries
        # fetch_indicator_data() returns a LIST of indicator records
        ndgain_indicator_scores = ndGainClient.fetch_indicator_data(
            indicator_codes=ndgain_vulnerability_indicators, 
            chunkSize=cfg['runtime']['chunk_size']
        )
        
        # Save raw data locally
        # Saves a CSV file since the course is the ZIP file containing CSV files
        if runtime.get("save_raw", True):
            ndGainClient.save_raw_data(
                ndgain_indicator_scores,
                project_root() / paths['data_raw'],
                "nd_gain_raw.csv"
            )
        
        print("\n===== ALL CLIENTS DONE. =====\n")

        # Return a dictionary containing all the fetched data
        return {
            "unsdg": unsdg_indicator_list,
            "worldbank": recs,
            "ndgain": ndgain_indicator_scores
        }


if __name__ == "__main__":
    fetchData = FetchData("src/config/settings.yaml")
    fetchData.fetch()
    