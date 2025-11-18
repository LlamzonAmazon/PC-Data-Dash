from __future__ import annotations

from pathlib import Path
import sys, yaml, pandas as pd

# Import data clients
from src.fetch.world_bank_fetch import WorldBankClient
from src.fetch.un_sdg_fetch import UNSDGClient
from src.pipeline.utils import project_root, setup_logger


def main():
    # Set up console logger for clean [INFO]/[ERROR] messages
    log = setup_logger()

    # Path to your configuration file
    cfg_path = project_root() / "src" / "config" / "settings.yaml"

    # Stop if config file is missing
    if not cfg_path.exists():
        log.error("Missing config at %s", cfg_path)
        sys.exit(1)

    # Load configuration from YAML file
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    print("\nLoaded configuration from", cfg_path)

    ''' ########## UN SDG Data Fetching ########### '''
    
    base_url = f"{cfg['un_sdg']['api_paths']['base']}"

    unsdgClient = UNSDGClient(api_url=base_url)
    print("Fetching UN SDG Goals data...")
    goals_data = unsdgClient.fetch("/Goal/List", parameters={
        "includeChildren": "true"
        })
    
    # 3 DATAFRAMES: GOALS, TARGETS, INDICATORS
    df_goals, df_targets, df_indicators = unsdgClient._goals_list_to_dataframes(goals_data)
    
    temp = df_indicators.copy()
    for col in temp.columns:
        if temp[col].dtype == "object":
            # TRUNCATING LONG TEXT FIELDS FOR BETTER DISPLAY
            temp[col] = temp[col].astype(str).str.slice(0, 20)

    print("\n=== UN SDG Indicators Data (preview) ===")
    print(temp.head(50).to_string(index=False))
    
    # Export indicators DataFrame to CSV for now
    if cfg["runtime"].get("write_files", True):
        unsdgClient.save_interim_csv(
            df_indicators,
            project_root() / cfg["paths"]["unsdg_interim_csv"]
        )

    ''' ########## World Bank Data Fetching ########### '''

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
    


# Run main() only if this file is executed directly
if __name__ == "__main__":
    main()
