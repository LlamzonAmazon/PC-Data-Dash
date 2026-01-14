from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DataCleaner(ABC):
    """
    Base class for data cleaners.
    """

    @abstractmethod
    def __init__(self, base: str, credentials: Optional[dict] = None) -> None:
        """
        Initialize the data cleaner.

        Args:
            base (str): Base URL for the data source
            credentials (Optional[dict]): Optional authentication credentials
        """
        
        self.base = base
        self.credentials = credentials or {}
        self.logger = logger

    @abstractmethod
    def save_interim(self, df: pd.DataFrame, out_path: Path) -> None:
        """
        Save the interim data.
        """
        pass

    @abstractmethod
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the data.
        NOTE: Each cleaner object should return a single dataframe representing the cleaned data from their corresponding source

        Returns:
            pd.DataFrame: Cleaned data as a dataframe to be forwarded to processing    
        """
        
        pass

