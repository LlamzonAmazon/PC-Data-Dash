from __future__ import annotations

import sys, pandas as pd
from pathlib import Path

from src.fetch.fetch_factory import DataFetcherFactory
from src.pipeline.utils import project_root, setup_logger

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

from dotenv import load_dotenv
import os

class FetchData:
    """
    Essentially the main of the module.
    """

    def __init__(self, config_path):
        
        load_dotenv()

        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        self.AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")

        self.credential = ClientSecretCredential(
            tenant_id=self.AZURE_TENANT_ID,
            client_id=self.AZURE_CLIENT_ID,
            client_secret=self.AZURE_CLIENT_SECRET
        )

        self.config_path = config_path

    def upload_to_azure(container_client, csv_path: Path, blob_name: str, log) -> None:
        """
        
        Upload a CSV file to Azure Blob Storage container.
        
        Args:
            container_client: Azure container client
            csv_path: Local path to the CSV file
            blob_name: Name/path for the blob in Azure (e.g., "interim/unsdg/un_sdg_interim.csv")
            log: Logger instance
        """
        try:
            if not csv_path.exists():
                log.warning(f"CSV file not found: {csv_path}, skipping upload")
                return
            
            blob_client = container_client.get_blob_client(blob_name)
            
            # Read the CSV file and upload
            with open(csv_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            log.info(f"Successfully uploaded {csv_path.name} to Azure as {blob_name}")
        except Exception as e:
            log.error(f"Failed to upload {csv_path.name} to Azure: {e}")

    def fetch(self):
        """
        Fetch data from all sources and upload raw data to Azure Blob Storage.
        """

        container_name = "unprocessed-data" # where raw data is stored

        # Set up console logger for clean [INFO]/[ERROR] messages
        log = setup_logger()

        blob_service_client = BlobServiceClient(
            account_url=self.AZURE_STORAGE_ACCOUNT_URL,
            credential=self.credential
        )

        container_client = blob_service_client.get_container_client(container_name)

        # Path to your configuration file
        cfg_path = self.config_path

        # Stop if config file is missing
        if not cfg_path.exists():
            log.error("Missing config at %s", cfg_path)
            sys.exit(1)

        # Create Data Fetcher Factory
        fetcher_factory = DataFetcherFactory(config_path=cfg_path)
        
        # Load full configuration file
        cfg = fetcher_factory.get_config()  
        paths, runtime = cfg["paths"], cfg["runtime"]

        """ ################################################################## 
        ### UN SDG FETCHING ###
        ################################################################## """
        
        # unsdgFetcher = fetcher_factory.create_client('unsdg')
        
        # unsdg_indicator_data_endpoint = cfg['unsdg']['api_paths']['indicator_data_endpoint']
        # unsdg_indicator_codes = [indicator['code'] for indicator in cfg['unsdg']['indicators']]
        
        # # Fetch indicator data for ALL countries and specified years
        # print(f'Fetching UN SDG data for {len(unsdg_indicator_codes)} indicators...')
        # indicator_data_dict = unsdgFetcher.fetch_indicator_data(unsdg_indicator_data_endpoint, 
        #     parameters={
        #     "indicator": unsdg_indicator_codes,
        #     # areaCode excluded; returns ALL if not specified
        #     "timePeriodStart": cfg['unsdg']['start_year'], 
        #     "timePeriodEnd": cfg['unsdg']['end_year'],
        #     "page" : 1, # Page Number
        #     "pageSize": cfg['runtime']['per_page'] # Number of records per page/response
        #     })
        
        # # Save raw data as JSON (locally)
        # if runtime.get("save_local", True):
        #     unsdg_csv_path = project_root() / paths['data_raw']
        #     unsdgFetcher.save_raw_data(
        #         indicator_data_dict, 
        #         unsdg_csv_path,
        #         "un_sdg_raw.json"
        #     )
        
        """ ################################################################## 
        ### WORLD BANK FETCHING ###
        ################################################################## """

        # wbClient = fetcher_factory.create_client('worldbank')
        
        # frames = []  # List to store dataframes for each indicator
        # wb = cfg["worldbank"]

        # # Loop through each indicator and fetch its data
        # print("Fetching World Bank data...")
        # for item in wb["indicators"]:
        #     code, alias = item["code"], item.get("alias", item["code"])

        #     # Fetch all records (2010–2024, all countries)
        #     recs = wbClient.fetch_indicator_data(code, wb["countries"], wb["start_year"], wb["end_year"])

        #     # Save raw JSON output if enabled
        #     if runtime.get("save_local", True):
        #         wbClient.save_raw_data(
        #             recs,
        #             project_root() / paths["data_raw"],
        #             "world_bank_raw.json"
        #         )
        
        
        """ ################################################################## 
        ### ND-GAIN FETCHING ###
        ################################################################## """
        
        ndGainClient = fetcher_factory.create_client('ndgain')
        
        ndgain_vulnerability_indicators = cfg['ndgain']['indicators']['vulnerability']
        
        # Get vulnerability scores as a list of dictionaries
        ndgain_indicator_scores = ndGainClient.fetch_indicator_data(
            indicator_codes=ndgain_vulnerability_indicators, 
            chunkSize=cfg['runtime']['chunk_size']
        )
        
        # Save raw CSV (locally)
        if runtime.get("save_local", True):
            ndGainClient.save_raw_data(
                ndgain_indicator_scores,
                project_root() / paths['data_raw'],
                "nd_gain_raw.csv"
            )
        
        
        """ ################################################################## """
        print("\n===== ALL CLIENTS DONE. =====\n")
        """ ################################################################## """


if __name__ == "__main__":
    fetchData = FetchData("config/settings.yaml")
    fetchData.fetch()
    