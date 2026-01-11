from __future__ import annotations

import sys, pandas as pd
from pathlib import Path

from typing import Dict, Any
from src.clean.clean_factory import DataCleanFactory

class CleanData:
    """
    Essentially the main of the module.
    """
    
    def __init__(self):
        pass

    def main(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the data
        """

        # Setup & load configs

        # Create factory
        cleanFactory = DataCleanFactory()

        # UN SDG


        # Upload cleaned CSV to Azure
        self.upload_to_azure(
            container_client, 
            unsdg_csv_path, 
            "raw/unsdg/un_sdg_raw.json",
            log
        )

        # World Bank

        # Upload CSV to Azure
        self.upload_to_azure(
            container_client,
            wb_csv_path,
            "raw/worldbank/world_bank_raw.json",
            log
        )



        # Normalize JSON into a DataFrame and add resulting DataFrame to list
        frames.append(wbClient.clean_data(recs, alias))

        # Combine all indicator dataframes
        if frames:
            combined = pd.concat(frames, ignore_index=True)

            # Save cleaned combined CSV if enabled
            if runtime.get("save_local", True):
                wb_csv_path = project_root() / paths["wb_raw"]
                wbClient.save_raw_json(
                    combined, 
                    wb_csv_path
                )
                
        # ND-GAIN
        
        # Convert to DataFrame
        ndgain_indicator_scores_df = ndGainClient.indicator_data_to_dataframe(ndgain_indicator_scores)

        # Upload CSV to Azure
        self.upload_to_azure(
            container_client,
            ndgain_csv_path,
            "interim/ndgain/ndgain_interim.csv",
            log
        )

        cleaned_data = cleanFactory.create_cleaner('unsdg').clean_data(df)
        return cleaned_data

    def to_wide(df: pd.DataFrame) -> pd.DataFrame:
        return df.pivot_table(index=["country","iso3","year"], columns="indicator", values="value").reset_index()
