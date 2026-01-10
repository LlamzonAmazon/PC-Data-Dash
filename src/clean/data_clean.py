from __future__ import annotations

import sys, pandas as pd
from pathlib import Path

from typing import Dict, Any
from src.clean.clean_factory import DataCleanFactory

class DataClean:
    """
    Essentially the main of the module.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def main(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the data
        """

        # Setup & load configs

        # Create factory
        cleanFactory = DataCleanFactory(self.config)

        # UN SDG

        # World Bank

        # ND-GAIN


        cleaned_data = cleanFactory.create_cleaner('unsdg').clean_data(df)
        return cleaned_data

if __name__ == "__main__":

    config_path = project_root() / "src" / "config" / "settings.yaml"

    DataCleaner = DataClean(config_path)

    DataCleaner.main()