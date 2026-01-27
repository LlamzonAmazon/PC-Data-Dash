"""
Factory class for creating data plotters.

This factory creates the appropriate plotter instance based on the data source
and domain, following the abstract factory pattern used throughout the codebase.
"""

from typing import Dict, Type, Optional
from pathlib import Path
import logging
import yaml

from src.plotting.base_plotter import DataPlotter
from src.plotting.un_sdg_plotter import UNSDGDomain1Plotter
from src.pipeline.utils import project_root


class DataPlotterFactory:
    """
    Factory class for creating data plotters based on source and domain.
    
    Usage:
        factory = DataPlotterFactory()
        plotter = factory.create_plotter('unsdg', 'domain1')
        plots = plotter.plot_domain('Afghanistan', 'domain1')
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the factory.
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        self.logger = logging.getLogger(__name__)
        self.root = project_root()
        self.config_path = config_path or self.root / "src" / "config" / "settings.yaml"
        
        # Load configuration
        try:
            self.config = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            raise
        
        # Register available plotters: (source, domain) -> PlotterClass
        # Format: ('source', 'domain') -> PlotterClass
        self._plotters: Dict[tuple, Type[DataPlotter]] = {
            ('unsdg', 'domain1'): UNSDGDomain1Plotter,
            # Add more plotters as they are implemented:
            # ('unsdg', 'domain2'): UNSDGDomain2Plotter,
            # ('ndgain', 'domain1'): NDGAINDomain1Plotter,
            # ('worldbank', 'domain1'): WorldBankDomain1Plotter,
        }
    
    def create_plotter(self, source: str, domain: str) -> DataPlotter:
        """
        Create a plotter for the specified source and domain.
        
        Args:
            source: Data source ('unsdg', 'ndgain', 'worldbank')
            domain: Domain identifier ('domain1', 'domain2', etc.)
            
        Returns:
            DataPlotter instance
            
        Raises:
            ValueError: If the (source, domain) combination is not supported
        """
        key = (source.lower(), domain.lower())
        
        if key not in self._plotters:
            available = [f"{s}/{d}" for s, d in self._plotters.keys()]
            raise ValueError(
                f"Unknown plotter: {source}/{domain}. "
                f"Available plotters: {available}"
            )
        
        plotter_class = self._plotters[key]
        self.logger.info(f"Creating {source}/{domain} plotter: {plotter_class.__name__}")
        
        return plotter_class(config_path=self.config_path)
    
    def register_plotter(self, source: str, domain: str, plotter_class: Type[DataPlotter]):
        """
        Register a new plotter class.
        
        Args:
            source: Data source identifier
            domain: Domain identifier
            plotter_class: Plotter class that inherits from DataPlotter
        """
        key = (source.lower(), domain.lower())
        self._plotters[key] = plotter_class
        self.logger.info(f"Registered plotter: {source}/{domain} -> {plotter_class.__name__}")
    
    def get_config(self) -> Dict:
        """
        Returns the full configuration dictionary loaded from YAML.
        """
        return self.config
