from __future__ import annotations

import sys, pandas as pd
from pathlib import Path

from src.fetch.client_factory import DataClientFactory
from src.pipeline.utils import project_root, setup_logger
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

load_dotenv()

AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")


credential = ClientSecretCredential(
    tenant_id=AZURE_TENANT_ID,
    client_id=AZURE_CLIENT_ID,
    client_secret=AZURE_CLIENT_SECRET
)

"""
    Main script to run data fetching; `python3 -m src.fetch.data_fetch`

    TODO: MOVE AZURE UPLOADING FUNCTIONALITY TO ORCHESTRATOR CLASS
"""
def main():
    container_name = "unprocessed-data"

    # Set up console logger for clean [INFO]/[ERROR] messages
    log = setup_logger()

    blob_service_client = BlobServiceClient(
        account_url=AZURE_STORAGE_ACCOUNT_URL,
        credential=credential
    )

    container_client = blob_service_client.get_container_client(container_name)

    # Path to your configuration file
    cfg_path = project_root() / "src" / "config" / "settings.yaml"

    # Stop if config file is missing
    if not cfg_path.exists():
        log.error("Missing config at %s", cfg_path)
        sys.exit(1)

    # Create Data Client Factory
    client_factory = DataClientFactory(config_path=cfg_path)
    
    # Load full configuration file
    cfg = client_factory.get_config()  
    paths, runtime = cfg["paths"], cfg["runtime"]

    """ ################################################################## 
    ### UN SDG FETCHING ###
    ################################################################## """
    
    unsdgClient = client_factory.create_client('unsdg')
    
    unsdg_indicator_data_endpoint = cfg['unsdg']['api_paths']['indicator_data_endpoint']
    unsdg_indicator_codes = [indicator['code'] for indicator in cfg['unsdg']['indicators']]
    
    # Fetch indicator data for ALL countries and specified years
    print(f'Fetching UN SDG data for {len(unsdg_indicator_codes)} indicators...')
    indicator_data_df = unsdgClient.fetch_indicator_data(unsdg_indicator_data_endpoint, 
        parameters={
        "indicator": unsdg_indicator_codes,
        # areaCode excluded; returns ALL if not specified
        "timePeriodStart": cfg['unsdg']['start_year'], 
        "timePeriodEnd": cfg['unsdg']['end_year'],
        "page" : 1, # Page Number
        "pageSize": cfg['runtime']['per_page'] # Number of records per page/response
        })
    

    # Send dataframe to /data/interim/ as CSV if enabled
    if runtime.get("write_files", True):
        unsdg_csv_path = project_root() / paths['unsdg_interim_csv']
        unsdgClient.save_interim_csv(
            indicator_data_df, 
            unsdg_csv_path
        )
        # Upload CSV to Azure
        upload_csv_to_azure(
            container_client, 
            unsdg_csv_path, 
            "interim/unsdg/un_sdg_interim.csv",
            log
        )
    
    
    """ ################################################################## 
    ### WORLD BANK FETCHING ###
    ################################################################## """

    wbClient = client_factory.create_client('worldbank')
    
    frames = []  # List to store dataframes for each indicator
    wb = cfg["worldbank"]

    # Loop through each indicator and fetch its data
    print("Fetching World Bank data...")
    for item in wb["indicators"]:
        code, alias = item["code"], item.get("alias", item["code"])

        # Fetch all records (2010–2024, multiple countries)
        recs = wbClient.fetch_indicator(code, wb["countries"], wb["start_year"], wb["end_year"])

        # Save raw JSON output if enabled
        if runtime.get("write_files", True):
            wbClient.save_raw_json(
                recs,
                project_root() / paths["data_raw"],
                f"{alias}_{wb['start_year']}_{wb['end_year']}.json"
            )

        # Normalize JSON into a DataFrame and add resulting DataFrame to list
        frames.append(wbClient.normalize(recs, alias))

    # Combine all indicator dataframes
    if frames:
        combined = pd.concat(frames, ignore_index=True)

        # Save cleaned combined CSV if enabled
        if runtime.get("write_files", True):
            wb_csv_path = project_root() / paths["wb_interim_csv"]
            wbClient.save_interim_csv(
                combined, 
                wb_csv_path
            )
            # Upload CSV to Azure
            upload_csv_to_azure(
                container_client,
                wb_csv_path,
                "interim/worldbank/world_bank_interim.csv",
                log
            )
    
       
    """ ################################################################## 
    ### ND-GAIN FETCHING ###
    ################################################################## """
    
    ndGainClient = client_factory.create_client('ndgain')
    
    ndgain_vulnerability_indicators = cfg['ndgain']['indicators']['vulnerability']
    
    # Get vulnerability scores as a list of dictionaries
    ndgain_indicator_scores = ndGainClient.fetch_indicator(
        indicator_codes=ndgain_vulnerability_indicators, 
        chunkSize=cfg['runtime']['chunk_size']
    )
    
    # Convert to DataFrame
    ndgain_indicator_scores_df = ndGainClient.indicator_data_to_dataframe(ndgain_indicator_scores)
    
    # Print DataFrame
    if runtime.get("write_files", True):
        ndgain_csv_path = project_root() / paths['ndgain_interim_csv']
        ndGainClient.save_interim_csv(
            ndgain_indicator_scores_df,
            ndgain_csv_path
        )
        # Upload CSV to Azure
        upload_csv_to_azure(
            container_client,
            ndgain_csv_path,
            "interim/ndgain/ndgain_interim.csv",
            log
        )
    
    
    """ ################################################################## """
    print("\n===== ALL CLIENTS DONE. =====\n")

if __name__ == "__main__":
    main()
    