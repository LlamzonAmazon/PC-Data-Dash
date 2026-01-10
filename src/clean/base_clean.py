from abc import ABC, abstractmethod
from typing import Optional, List
import pandas as pd
import logging

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
    def clean_data(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """
        Clean the data

        Returns:
            List[pd.DataFrame]: Cleaned data as dataframes to be forwarded to processing    
        """

        # TODO: Implement clean_data() method
        # NOTE: Each cleaner object should return a single dataframe representing the cleaned data from their corresponding source

        raise NotImplementedError

    @abstractmethod
    def forward_to_processing(self, df: pd.DataFrame) -> bool:
        """
        Forward the data to the processing stage

        Returns:
            bool: True if the data was forwarded to processing, False otherwise    
        """
        
        raise NotImplementedError
