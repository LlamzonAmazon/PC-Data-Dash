
import yaml
import logging

from typing import Dict, Type
from src.clean.base_clean import DataCleaner
from src.clean.un_sdg_clean import UNSDGCleaner
from src.clean.nd_gain_clean import NDGAINCleaner
from src.clean.world_bank_clean import WorldBankCleaner

from src.pipeline.utils import project_root

logger = logging.getLogger(__name__)

class DataCleanFactory:
    """
    Factory class for creating data cleaners.
    """
    
    def __init__(self) -> None:
        """
        Initialize the factory.
        """
        
        try:
            self.config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise

        print("\nLoaded configuration from", config_path)

        self.cleaners: Dict[str, Type[DataCleaner]] = {
            'unsdg': UNSDGClean,
            'ndgain': NDGAINClean,
            'worldbank': WorldBankClean
        }

    def create_cleaner(self, source: str) -> DataCleaner:
        """
        Create a data cleaner for the given source.
        """

        if source not in self.cleaners:
            raise ValueError(f"Unknown source: {source}")

        return self.cleaners[source](self.config)

    def create_all_cleaners(self) -> Dict[str, DataCleaner]:
        """
        Create all configured cleaners.
        """
        return {
            name: self.create_cleaner(name) 
            for name in self.cleaners.keys()
        }

    def get_config(self) -> Dict:
        """
        Returns the full configuration dictionary loaded from YAML.
        """
        return self.config
    