'''
This module cleans data from all sources.
Cleaning involves extracting the relevant data and transforming it into a standardized format.

Cleaned (interim) output is saved locally; upload to Azure Blob is a separate pipeline stage
(see src.upload.upload_validated) and runs only on this validated output, not raw.
'''

 
from __future__ import annotations

import sys
import pandas as pd
from typing import Dict, Optional
from pathlib import Path
import logging
from src.pipeline.terminal_output import clean_header, TerminalOutput

from src.clean.clean_factory import DataCleanFactory
from src.upload.upload_validated import UploadValidated


class CleanData:
    """
    Cleans raw data and saves validated (interim) CSVs locally.
    Upload to Blob is handled by the Upload stage (see pipeline orchestrator).
    """
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.cleanFactory = DataCleanFactory(self.config_path)
        self.cfg = self.cleanFactory.get_config()
        self.logger = logging.getLogger(__name__)

    def to_wide(df: pd.DataFrame) -> pd.DataFrame:
        return df.pivot_table(
            index=["country_code", "country_name", "year"],
            columns="indicator",
            values="value",
        ).reset_index()

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

        cfg_path = Path(self.config_path)
        if not cfg_path.exists():
            self.logger.error("Missing config at %s", cfg_path)
            sys.exit(1)

        runtime = self.cfg["runtime"]
        
        """ ################################################################## 
        ### UN SDG CLEANING ###
        ################################################################## """
        
        clean_header("UN SDG")
        
        # Setup
        unsdgCleaner = self.cleanFactory.create_cleaner("unsdg")
        unsdg_raw = df["unsdg"]

        # Clean raw data and save in a DataFrame
        unsdg_cleaned = unsdgCleaner.clean_data(unsdg_raw)

        # Save cleaned CSV locally
        unsdg_csv_path = Path(runtime["interim_data"]["unsdg"])

        if runtime["save_cleaned"]:
            unsdgCleaner.save_interim(unsdg_cleaned, unsdg_csv_path)

        """ ################################################################## 
        ### WORLD BANK CLEANING ###
        ################################################################## """

        clean_header("World Bank")

        # Setup
        wbCleaner = self.cleanFactory.create_cleaner("worldbank")
        wb_raw = df["worldbank"]

        # Clean raw data and save in a DataFrame
        wb_cleaned = wbCleaner.clean_data(wb_raw)

        # Save cleaned CSV locally
        wb_csv_path = Path(runtime["interim_data"]["worldbank"])

        if runtime["save_cleaned"]:
            wbCleaner.save_interim(wb_cleaned, wb_csv_path)

        """ ################################################################## 
        ### ND-GAIN CLEANING ###
        ################################################################## """
        
        clean_header("ND-GAIN")
        
        # Setup
        ndGainClient = self.cleanFactory.create_cleaner("ndgain")
        ndgain_raw = df["ndgain"]

        # Clean raw data and save in a DataFrame
        ndgain_cleaned = ndGainClient.clean_data(ndgain_raw)

        # Save cleaned CSV locally
        ndgain_csv_path = Path(runtime["interim_data"]["ndgain"])

        if runtime["save_cleaned"]:
            ndGainClient.save_interim(ndgain_cleaned, ndgain_csv_path)

        print("\n" + "="*60)
        TerminalOutput.complete("All data sources cleaned successfully")
        print("="*60 + "\n")

        return {
            "unsdg": unsdg_cleaned,
            "worldbank": wb_cleaned,
            "ndgain": ndgain_cleaned,
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
            "ndgain": ndgain_data,
        }

if __name__ == "__main__":
    # For debugging: loads data from /raw directory instead of requiring FetchData
    from src.pipeline.utils import project_root
    config = project_root() / "src" / "config" / "settings.yaml"
    cleanData = CleanData(config)

    # Clean the loaded data
    cleaned_data = cleanData.clean()
    print(f"\nCleaned data sources: {list(cleaned_data.keys())}")

    # Test Azure upload
    # uploader = UploadValidated(config)
    # uploader.upload()