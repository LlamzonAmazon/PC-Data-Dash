'''
This module cleans data from all sources.
Cleaning involves extracting the relevant data and transforming it into a standardized format.

Responsible for cleaning data and uploading it to Azure Blob Storage.
'''


from __future__ import annotations

import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
import logging
from src.pipeline.utils import setup_logger

from src.clean.clean_factory import DataCleanFactory

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

from dotenv import load_dotenv
import os

class CleanData:
    """
    Essentially the main of the module.
    """
    
    def __init__(self, config_path):
        
        load_dotenv()

        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        self.AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")

      # Only create credential if all Azure credentials are present
        if all([self.AZURE_TENANT_ID, self.AZURE_CLIENT_ID, self.AZURE_CLIENT_SECRET, self.AZURE_STORAGE_ACCOUNT_URL]):
            self.credential = ClientSecretCredential(
                tenant_id=self.AZURE_TENANT_ID,
                client_id=self.AZURE_CLIENT_ID,
                client_secret=self.AZURE_CLIENT_SECRET
            )
            self.azure_enabled = True
        else:
            self.credential = None
            self.azure_enabled = False
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Azure credentials not found. Azure uploads will be disabled.")


        self.config_path = config_path

        self.cleanFactory = DataCleanFactory(self.config_path)

        # Load config
        # Cleaner Factory uses config for runtime settings NOT for file paths, indicator settings, etc.
        self.cfg = self.cleanFactory.get_config()

        self.logger = logging.getLogger(__name__)

    def upload_to_azure(self, container_client, csv_path: Path, blob_name: str, log) -> None:
        """
        
        Uploads cleaned CSV files to Azure Blob Storage container.
        
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

    def to_wide(df: pd.DataFrame) -> pd.DataFrame:
        return df.pivot_table(index=["country","iso3","year"], columns="indicator", values="value").reset_index()

    def clean(self, df: Optional[Dict[str, list]] = None) -> Dict[str, pd.DataFrame]:
        """
        Cleans the raw data and returns a dictionary of DataFrames containing the indicator data.

        Args:
            df: Dictionary containing ALL fetched indicator data by source.
                If None, will load data from /raw directory (for debugging).

        Returns:
            Dictionary containing cleaned indicator data by source
        """
        
        # If no data passed, load from /raw directory (debugging mode)
        if df is None:
            self.logger.info("DEBUGGING MODE – LOADING DATA FROM LOCAL")
            df = self.load_raw_data()

        log = setup_logger()

        container_name = "unprocessed-data" # where raw data is stored

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

        # Load configs
        paths, runtime = self.cfg["paths"], self.cfg["runtime"]
        
        """ ################################################################## 
        ### UN SDG CLEANING ###
        ################################################################## """
        
        # Setup
        unsdgCleaner = self.cleanFactory.create_cleaner("unsdg")
        unsdg_raw = df["unsdg"]

        # Clean raw data and save in a DataFrame
        unsdg_cleaned = unsdgCleaner.clean_data(unsdg_raw)

        # Save cleaned CSV locally
        unsdg_csv_path = Path(runtime["interim_data"]["unsdg"])

        if runtime["save_cleaned"]:
            unsdgCleaner.save_interim(unsdg_cleaned, unsdg_csv_path)

        # Upload cleaned CSV to Azure
        if runtime["upload_azure"]:
            self.upload_to_azure(
                container_client=container_client, 
                csv_path=unsdg_csv_path, 
                blob_name="interim/unsdg/un_sdg_interim.csv",
                log=log
            )

        """ ################################################################## 
        ### WORLD BANK CLEANING ###
        ################################################################## """

        # Setup
        wbCleaner = self.cleanFactory.create_cleaner("worldbank")
        wb_raw = df["worldbank"]

        # Clean raw data and save in a DataFrame
        wb_cleaned = wbCleaner.clean_data(wb_raw)

        # Save cleaned CSV locally
        wb_csv_path = Path(runtime["interim_data"]["worldbank"])

        if runtime["save_cleaned"]:
            wbCleaner.save_interim(wb_cleaned, wb_csv_path)

        # Upload CSV to Azure
        if runtime["upload_azure"]:
            self.upload_to_azure(
                container_client=container_client,
                csv_path=wb_csv_path,
                blob_name="raw/worldbank/world_bank_raw.json",
                log=log
            )

        """ ################################################################## 
        ### ND-GAIN CLEANING ###
        ################################################################## """
        
        # Setup
        ndGainClient = self.cleanFactory.create_cleaner("ndgain")
        ndgain_raw = df["ndgain"]

        # Clean raw data and save in a DataFrame
        ndgain_cleaned = ndGainClient.clean_data(ndgain_raw)

        # Save cleaned CSV locally
        ndgain_csv_path = Path(runtime["interim_data"]["ndgain"])

        if runtime["save_cleaned"]:
            ndGainClient.save_interim(ndgain_cleaned, ndgain_csv_path)

        # Upload CSV to Azure
        if runtime["upload_azure"]:
            self.upload_to_azure(
                container_client=container_client,
                csv_path=ndgain_csv_path,
                blob_name="interim/ndgain/ndgain_interim.csv",
                log=log
            )
        

        return {
            "unsdg": unsdg_cleaned,
            "worldbank": wb_cleaned,
            "ndgain": ndgain_cleaned
        }

    def load_raw_data(self) -> Dict[str, list]:
        """
        Load raw data from /raw directory for debugging purposes.
        This allows running CleanData without going through FetchData.
        
        Returns:
            Dictionary containing raw data by source (same format as FetchData.fetch())
        """
        from src.pipeline.utils import project_root
        import json
        
        raw_dir = project_root() / "data" / "raw"
        
        # Load UN SDG data
        unsdg_path = raw_dir / "un_sdg_raw.json"
        with open(unsdg_path, 'r') as f:
            unsdg_data = json.load(f)
        
        # Load World Bank data
        wb_path = raw_dir / "world_bank_raw.json"
        with open(wb_path, 'r') as f:
            wb_data = json.load(f)
        
        # Load ND-GAIN data (saved as JSON despite .csv extension)
        ndgain_path = raw_dir / "nd_gain_raw.csv"
        with open(ndgain_path, 'r') as f:
            ndgain_data = json.load(f)
        
        return {
            "unsdg": unsdg_data,
            "worldbank": wb_data,
            "ndgain": ndgain_data
        }


if __name__ == "__main__":
    # For debugging: loads data from /raw directory instead of requiring FetchData
    cleanData = CleanData(Path("src/config/settings.yaml"))
    
    # Clean the loaded data
    cleaned_data = cleanData.clean()
    print(f"\nCleaned data sources: {list(cleaned_data.keys())}")