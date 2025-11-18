# Using the Factory Pattern to create data fetching client instances
# This guy definitely paid attention in 3307 🔥🔥

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
        self.config = self._load_config(config_path)
        
        # Dictionary containing available client types
        self._clients: Dict[str, Type[DataClient]] = {
            'unsdg': UNSDGClient,
            'ndgain': NDGAINClient,
            'worldbank': WorldBankClient
        }
    
    def _load_config(self, config_path: str) -> dict:
        
        # Load YAML configuration file
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def create_client(self, client_type: str) -> DataClient:
        """
        client_type: Type of client ('unsdg', 'ndgain', 'worldbank')
        """
        
        client_type_lower = client_type.lower()
        
        # Raise a ValueError if client type is invalid
        if client_type_lower not in self._clients:
            raise ValueError(
                f"Unknown client type: {client_type}. "
                f"Available types: {list(self._clients.keys())}"
            )
        
        # Get client instance from clients dictionary
        client_class = self._clients[client_type_lower]
        
        # Get configurations for this client
        print("Configs for client:\n", client_type_lower)
        client_config = self.config['data_sources'].get(client_type_lower, {})
        
        # Create and return client instance
        logger.info(f"Creating {client_type} client")
        return client_class(
            api_endpoint=client_config.get('api_endpoint'),
            credentials=client_config.get('credentials', {})
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
        Register a new client type (useful for extensions).
        
        Args:
            name: Identifier for the client
            client_class: Class that implements DataClient interface
        """
        if not issubclass(client_class, DataClient):
            raise TypeError(f"{client_class} must inherit from DataClient")
        
        self._clients[name] = client_class
        logger.info(f"Registered new client type: {name}")