'''
Orchestrates the entire data pipeline.

Orchestrator class is created and run in run_pipeline.py
'''

from pathlib import Path
from dotenv import load_dotenv
from src.pipeline.utils import project_root

from src.fetch.fetch_data import FetchData
from src.clean.clean_data import CleanData

class Orchestrator:
    def __init__(self, config_path: str = project_root() / "src/config/settings.yaml") -> None:

        load_dotenv()
        self.config_path = config_path

    def run(self):

        # ============================================================
        # FETCH
        # ============================================================
        
        # Fetch data from all sources and upload raw data to Azure Blob Storage.
        fetchData = FetchData(self.config_path)
        fetchData.fetch()

        # ============================================================
        # CLEAN
        # ============================================================
        
        # Clean data from all sources.
        cleanData = CleanData(self.config_path)
        cleanData.clean()
        
        # ============================================================
        # PROCESS
        # ============================================================

        # TBD
        raise NotImplementedError
