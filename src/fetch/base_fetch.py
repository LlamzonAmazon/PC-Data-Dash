from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

"""
Abstract base class for all data source clients (UN SDG, ND-GAIN, World Bank, etc.).
"""
class DataFetcher(ABC):
    
    def __init__(self, base: str, credentials: Optional[dict] = None, **kwargs):
        """
        Initializes a DataFetcher with their **base** API URL (`base`), optional credentials (`credentials`), and an empty data container (`data`).
        
        Args:
            base (str): __Base__ API URL __OR__ ZIP file path for the data source
            credentials (Optional[dict]): Optional authentication credentials. Defaults to None.
            **kwargs: Additional arguments for subclass-specific configuration
        """
        
        self.base = base
        self.credentials = credentials or {}
        self.logger = logger
    
    @abstractmethod
    def save_raw_data(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        """
            Saves raw data to JSON file in /raw/ directory

        Args:
            records (List[Dict[str, Any]]): List of records to save as JSON
            out_dir (Path): Destination directory for JSON file
            filename (str): Name of the JSON file
        """        
        pass
    
    @abstractmethod
    def fetch_indicator_data(self):
        """
        Fetches indicator data from the data source (source differs among clients)
        """
        pass

    def get_base_url(self) -> str:
        # Returns base location for a given source
        return self.base
    
    def _log_fetch_start(self):
        # Helper method for logging
        self.logger.info(f"Starting data fetch from {self.base}")
    
    def _log_fetch_complete(self, row_count: int):
        # Helper method for logging
        self.logger.info(f"Fetch complete. Retrieved {row_count} rows")