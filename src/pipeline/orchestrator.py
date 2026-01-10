'''
Orchestrates the entire data pipeline.

Orchestrator class is created and run in run_pipeline.py
'''

from pathlib import Path
from dotenv import load_dotenv
import os

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
from src.pipeline.utils import project_root, setup_logger

from src.fetch.data_fetch import main as fetch_main
from src.clean.data_clean import clean_main

class Orchestrator:
    def __init__(self):
        pass

    def setup_azure(self):
        pass

    def upload_to_azure(self, container_client, csv_path: Path, blob_name: str, log) -> None:
        """
        NOTE: from data_fetch.py; needs credentials and other relevant logic that's in data_fetch.py
        
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
        pass

    def clean(self) -> Dict[str, pd.DataFrame]:
        """
        Clean data from all sources.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping source names to cleaned DataFrames
                e.g., {'unsdg': df_unsdg, 'ndgain': df_ndgain, 'worldbank': df_wb}
        """

        cleaned_data = clean_main()

        return cleaned_data

    def process(self):
        pass

    def run(self):
        pass
