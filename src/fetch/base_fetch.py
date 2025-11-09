# Interface for all data fetching clients

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

"""
Abstract base class for all data source clients (UN SDG, ND-GAIN, World Bank, etc.).
"""
class DataClient(ABC):
    
    def __init__(self, api_url: str, credentials: Optional[dict] = None):
        # api_endpoint: Base URL for the API
        # credentials: Optional authentication credentials

        self.api_url = api_url
        self.credentials = credentials or {}
        self.data: Optional[pd.DataFrame] = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def fetch(self, api_url: str, parameters: Any, credentials: Optional[dict] = None) -> pd.DataFrame:
        # Fetch data from API and return as DataFrame
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        # Validate fetched data
        pass
    
    def _log_fetch_start(self):
        # Helper method for logging
        self.logger.info(f"Starting data fetch from {self.api_url}")
    
    def _log_fetch_complete(self, row_count: int):
        # Helper method for logging
        self.logger.info(f"Fetch complete. Retrieved {row_count} rows")