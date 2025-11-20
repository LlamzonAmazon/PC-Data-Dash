# Interface for all data fetching clients

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Any, List, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

"""
Abstract base class for all data source clients (UN SDG, ND-GAIN, World Bank, etc.).
"""
class DataClient(ABC):
    
    def __init__(self, api_url: str, credentials: Optional[dict] = None):
        """
        Initializes a DataClient with their **base** API URL (`api_url`), optional credentials (`credentials`), and an empty data container (`data`).
        
        Args:
            api_url (str): **Base** API URL for the data source
            credentials (Optional[dict]): Optional authentication credentials. Defaults to None.
        """
        
        self.api_url = api_url
        self.credentials = credentials or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def validate(self) -> bool:
        """
            Validates non-empty API response data.
        """
        pass
    
    @abstractmethod
    def save_raw_json(self, records: List[Dict[str, Any]], out_dir: Path, filename: str) -> None:
        """
            Saves the tidy DataFrame as a JSON file.

        Args:
            df (pd.DataFrame): DataFrame to convert to JSON
            out_path (Path): Destination path of JSON file
        """        
        pass
    
    @abstractmethod
    def save_interim_csv(self, df: pd.DataFrame, out_path: Path) -> None:
        """
            Saves the tidy DataFrame as a CSV file.

        Args:
            df (pd.DataFrame): DataFrame to convert to CSV
            out_path (Path): Destination path of CSV file
        """
        pass
    
    def get_api_url(self) -> str:
        # Returns base API URL
        return self.api_url
    
    def _log_fetch_start(self):
        # Helper method for logging
        self.logger.info(f"Starting data fetch from {self.api_url}")
    
    def _log_fetch_complete(self, row_count: int):
        # Helper method for logging
        self.logger.info(f"Fetch complete. Retrieved {row_count} rows")