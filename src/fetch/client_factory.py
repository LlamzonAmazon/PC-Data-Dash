from typing import Dict, Type

from .base_fetch import DataClient
from .un_sdg_fetch import UNSDGClient
from .nd_gain_fetch import NDGAINClient
from .world_bank_fetch import WorldBankClient

import yaml
import logging
from src.pipeline.utils import project_root

logger = logging.getLogger(__name__)

class DataClientFactory:

    def __init__(self, config_path: str = project_root() / "src/config/settings.yaml"):
        
        # Load YAML configuration file
        try:
            self.config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
        print("\nLoaded configuration from", config_path)

        # Dictionary containing available client types
        self._clients: Dict[str, Type[DataClient]] = {
            'unsdg': UNSDGClient,
            'ndgain': NDGAINClient,
            'worldbank': WorldBankClient
        }
     
    def create_client(self, client_type: str) -> DataClient:
        """
        Creates a data client based on the specified type.
        
        Args:
            client_type (str): Type of client ('unsdg', 'ndgain', 'worldbank')
        
        Returns:
            data_client (DataClient): Instance of the requested DataClient subclass
        """
        
        client_type_lower = client_type.lower()
        
        # Raise a ValueError if client type is invalid
        if client_type_lower not in self._clients:
            raise ValueError(
                f"Unknown client type: {client_type}. "
                f"Available types: {list(self._clients.keys())}"
            )
        
        # Get data client instance from clients dictionary
        data_client = self._clients[client_type_lower]
        
        # Get configurations for this client
        print(f'Loaded configs for client: {client_type_lower}, ', end="")
        client_config = self.config.get(client_type_lower, {})
        
        logger.info(f"Creating {client_type} client")
        
        print(f'now returning {client_type_lower} instance.')
        
        source = 'api_paths'
        if client_type_lower == 'ndgain':
            source = 'zip_path'
        
        return data_client(
            base=client_config[source]['base'],  # Passing in base API URL upon instantiation
            credentials=None # Use None for now; None of the APIs require keys
        )
    
    def create_all_clients(self) -> Dict[str, DataClient]:
        """
        Create all configured clients.
        
        Returns:
            Dictionary mapping client names to instances
        """
        return {
            name: self.create_client(name) 
            for name in self._clients.keys()
        }
    
    def register_client(self, name: str, client_class: Type[DataClient]):
        """
        Register a new client type (useful for making new data source clients).
        
        Args:
            name: Identifier for the client
            client_class: Class that implements DataClient interface
        """
        if not issubclass(client_class, DataClient):
            raise TypeError(f"{client_class} must inherit from DataClient")
        
        self._clients[name] = client_class
        logger.info(f"Registered new client type: {name}")
        
    def get_config(self) -> Dict:
        """
        Returns the full configuration dictionary loaded from YAML.
        """
        return self.config