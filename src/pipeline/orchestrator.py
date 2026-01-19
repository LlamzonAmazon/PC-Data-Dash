'''
Orchestrates the entire data pipeline.

Orchestrator class is created and run in run_pipeline.py
'''

from pathlib import Path
import sys

from dotenv import load_dotenv
from src.pipeline.utils import project_root

from src.fetch.fetch_data import FetchData
from src.clean.clean_data import CleanData

class Orchestrator:
    def __init__(self, config_path: str = project_root() / "src/config/settings.yaml") -> None:

        load_dotenv()
        self.config_path = config_path

    def run(self) -> None:

        # ============================================================
        # FETCH
        # ============================================================
        
        # Fetch data from all sources and upload raw data to Azure Blob Storage or local files.
        fetchData = FetchData(self.config_path)
        fetched_data = fetchData.fetch() # Dictionary containing ALL fetched indicator data by source

        # ============================================================
        # CLEAN
        # ============================================================
        
        # Using Method A for Fetch -> Clean
        # This is because Fetched data is already in memory
        # Writing to Blob then immediately reading it back doubles memory usage temporarily and adds I/O cost 
        cleanData = CleanData(self.config_path)
        cleanData.clean(fetched_data)
        
        # ============================================================
        # PROCESS
        # ============================================================

        # Using Method B for Clean -> Processing
        # This is because we want to be able to resume the pipeline if it fails without having to re-run the pipeline
        # and we want to be able to inspect the intermediate files

        sys.exit(0)
        # raise NotImplementedError


        '''

        Method A: Store to Storage (Local/Azure Blob)

        Pros:
        Lower memory footprint - data is offloaded after each stage
        Fault tolerance - if a stage fails, previous results are persisted
        Easier debugging - can inspect intermediate files
        Supports resumable pipelines

        Cons:
        Slower - I/O operations (read/write) add latency
        More Azure Blob transactions = higher cost
        Serialization/deserialization overhead (JSON parsing, etc.)


        Method B: Pass via Variable (In-Memory)

        Pros:
        Faster - no I/O overhead
        No storage transaction costs
        Data stays in native Python format (no serialization)

        Cons:
        Higher peak memory usage - all data in RAM simultaneously
        If pipeline fails mid-way, you lose everything
        Harder to debug intermediate states

        '''
        
        