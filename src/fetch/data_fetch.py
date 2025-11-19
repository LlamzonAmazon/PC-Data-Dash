from __future__ import annotations

import sys, pandas as pd

from src.fetch.client_factory import DataClientFactory
from src.pipeline.utils import project_root, setup_logger


"""
    Main script to run data fetching; `python3 -m src.fetch.data_fetch`
"""
def main():

    # Set up console logger for clean [INFO]/[ERROR] messages
    log = setup_logger()

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

    """ ################################################################## 
    ### UN SDG FETCHING ###
    ################################################################## """
    
    unsdgClient = client_factory.create_client('unsdg')
    
    unsdg_indicator_data_endpoint = cfg['unsdg']['api_paths']['indicator_data_endpoint']
    unsdg_indicator_codes = [indicator['code'] for indicator in cfg['unsdg']['indicators']]
    
    # Fetch indicator data for ALL countries and specified years
    print("Fetching UN SDG data...")
    indicator_data_df = unsdgClient.fetch_indicator_data(unsdg_indicator_data_endpoint, 
        parameters={
        "indicator": unsdg_indicator_codes,
        # areaCode excluded; returns ALL if not specified
        "timePeriodStart": cfg['unsdg']['start_year'], 
        "timePeriodEnd": cfg['unsdg']['end_year'],
        "page" : 1, # Page Number
        "pageSize": 1000 # Number of Records per Page/Response
        })
    

    # Send dataframe to /data/interim/ as CSV if enabled
    if cfg['runtime'].get("write_files", True):
        unsdgClient.save_interim_csv(
            indicator_data_df, 
            project_root() / cfg['paths']['unsdg_interim_csv']
        )
    
    """ ################################################################## 
    ### WORLD BANK FETCHING ###
    ################################################################## """

    wb, paths, runtime = cfg["world_bank"], cfg["paths"], cfg["runtime"]

    # Initialize API client with per_page setting from config
    wbClient = WorldBankClient(per_page=runtime.get("per_page", 1000))
    frames = []  # List to store dataframes for each indicator

    # Loop through each indicator and fetch its data
    print("Fetching World Bank indicator data...")
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

        # Normalize JSON → DataFrame and add to list
        frames.append(wbClient.normalize(recs, alias))

    # Combine all indicator dataframes
    if frames:
        combined = pd.concat(frames, ignore_index=True)

        # Print a preview in terminal (first 50 rows)
        print("\n=== Tidy World Bank Data (preview) ===")
        print(combined.head(50).to_string(index=False))

        # Save cleaned combined CSV if enabled
        if runtime.get("write_files", True):
            wbClient.save_interim_csv(combined, project_root() / paths["wb_interim_csv"])
            
    """ ################################################################## 
    ### ND-GAIN FETCHING ###
    ################################################################## """
    

# Run main() only if this file is executed directly
if __name__ == "__main__":
    main()
    

