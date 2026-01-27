"""
Abstract base class for all data plotters.

This module defines the interface that all plotter implementations must follow,
enabling a consistent plotting API across different domains and data sources.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import pandas as pd

from src.pipeline.utils import project_root


class DataPlotter(ABC):
    """
    Abstract base class for all data plotters.
    
    Each concrete plotter implementation should handle:
    - Loading data from a specific source (UN SDG, ND-GAIN, World Bank, etc.)
    - Organizing data by domain/sector/indicator structure
    - Generating time series plots for a given country
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the plotter.
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        self.root = project_root()
        self.config_path = config_path or self.root / "src" / "config" / "settings.yaml"
        
        # Data storage - subclasses should initialize these
        self.data: Optional[pd.DataFrame] = None
        self.country_data: Optional[pd.DataFrame] = None
    
    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        """
        Load data from the appropriate interim CSV file.
        
        Returns:
            DataFrame with loaded data
        """
        pass
    
    @abstractmethod
    def filter_by_country(self, country: str) -> pd.DataFrame:
        """
        Filter data for a specific country.
        
        Args:
            country: Country name or country code to filter by
            
        Returns:
            Filtered DataFrame for the specified country
        """
        pass
    
    @abstractmethod
    def get_indicator_data(self, indicator: str, series_code: Optional[str] = None) -> pd.DataFrame:
        """
        Extract data for a specific indicator (and optionally series code).
        
        Args:
            indicator: Indicator code or identifier
            series_code: Optional series code for data sources that use it
            
        Returns:
            DataFrame with filtered data, sorted appropriately
        """
        pass
    
    @abstractmethod
    def plot_domain(self, country: str, domain: str) -> Dict[str, List[Path]]:
        """
        Main method to plot all sectors for a domain and country.
        
        Args:
            country: Country name or code to plot
            domain: Domain identifier (e.g., "domain1", "domain2")
            
        Returns:
            Dictionary mapping sector names to lists of saved plot file paths
        """
        pass
    
    def get_output_base(self, domain: str) -> Path:
        """
        Get the base output directory for plots.
        
        Args:
            domain: Domain identifier
            
        Returns:
            Path to output directory
        """
        return self.root / "data" / "processed" / "plots" / domain
