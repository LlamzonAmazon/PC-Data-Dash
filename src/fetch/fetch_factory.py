from typing import Dict, Type

from .base_fetch import DataFetcher
from .un_sdg_fetch import UNSDGFetcher
from .nd_gain_fetch import NDGAINFetcher
from .world_bank_fetch import WorldBankFetcher
from .hdr_fetch import HDRFetcher
from .owid_fetch import OWIDFetcher

import yaml
import logging

logger = logging.getLogger(__name__)

class DataFetcherFactory:

    def __init__(self, config_path):
        
        # Load YAML configuration file
        try:
            self.config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
        print("\nLoaded configuration from", config_path)

        # Dictionary containing available client types
        self._clients: Dict[str, Type[DataFetcher]] = {
            'unsdg': UNSDGFetcher,
            'ndgain': NDGAINFetcher,
            'worldbank': WorldBankFetcher,
            'hdr': HDRFetcher,
            'owid': OWIDFetcher
        }
     
    def create_client(self, client_type: str) -> DataFetcher:
        """
        Creates a data client based on the specified type.
        
        Args:
            client_type (str): Type of client ('unsdg', 'ndgain', 'worldbank', 'hdr', 'owid')
        
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
        data_fetcher = self._clients[client_type_lower]
        
        # Get configurations for this client
        print(f'Loaded configs for client: {client_type_lower}, ', end="")
        client_config = self.config.get(client_type_lower, {})
        
        logger.info(f"Creating {client_type} client")
        
        print(f'now returning {client_type_lower} instance.')
        
        # Get base URL/path - handle special cases
        if client_type_lower == 'owid':
            # OWID doesn't need base, URL is passed directly to fetch_indicator_data
            base = ""
        elif client_type_lower == 'ndgain':
            base = client_config['zip_path']['base']
        else:
            base = client_config['api_paths']['base']
        
        return data_fetcher(
            base = base,  # Passing in base API URL upon instantiation
            credentials = None # Use None for now; None of the APIs require keys
        )
    
    def create_all_clients(self) -> Dict[str, DataFetcher]:
        """
        Create all configured clients.
        
        Returns:
            Dictionary mapping client names to instances
        """
        return {
            name: self.create_client(name) 
            for name in self._clients.keys()
        }
        
    def get_config(self) -> Dict:
        """
        Returns the full configuration dictionary loaded from YAML.
        """
        return self.config