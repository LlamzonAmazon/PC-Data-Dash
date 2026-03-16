from __future__ import annotations

import logging
import os
from pathlib import Path
import yaml
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from src.pipeline.utils import project_root, setup_logger


class UploadValidated:
    """
    Upload validated (interim) CSVs to Azure Blob Storage.
    Uses paths from config; does not upload raw data.
    Azure credentials are read from the project .env file (see .env.example for keys).

    Instance variables (set in __init__ / _load_config):
      config_path      Path to settings.yaml
      log              Logger
      AZURE_*          From .env (tenant, client, secret, storage URL)
      credential       ClientSecretCredential if all AZURE_* set, else None
      azure_enabled    True if credential is set
      cfg              Full parsed settings.yaml dict
      runtime          cfg["runtime"] (upload_azure, interim_data, ...)
      azure_cfg        cfg["azure"] (container_name, blob_prefix)
    """

    def __init__(self, config_path: Path) -> None:
        load_dotenv(project_root() / ".env")

        self.config_path = Path(config_path)
        self.log = setup_logger()

        # credentials from .env file
        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        self.AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")

        # all azure credentials that are required
        has_all_azure_creds = all(
            [
                self.AZURE_TENANT_ID,
                self.AZURE_CLIENT_ID,
                self.AZURE_CLIENT_SECRET,
                self.AZURE_STORAGE_ACCOUNT_URL,
            ]
        )

        # If credentials are set, create credential object + enable Azure upload
        if has_all_azure_creds:
            self.credential = ClientSecretCredential(
                tenant_id=self.AZURE_TENANT_ID,
                client_id=self.AZURE_CLIENT_ID,
                client_secret=self.AZURE_CLIENT_SECRET,
            )
            self.azure_enabled = True
        
        # Handle when credentials aren't set
        else:
            self.credential = None
            self.azure_enabled = False
            self.log.warning(
                "Azure credentials not set in environment or .env. Azure upload will be skipped."
            )

        self._load_config()

    # loads configs + set instance vars
    def _load_config(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        
        # open and load config file (f)
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f) or {}
        
        # get respective setions of settings.yaml
        self.runtime = self.cfg.get("runtime") or {}
        self.azure_cfg = self.cfg.get("azure") or {}

    # upload files to azure blob storage
    def upload(self) -> None:
        # if upload_azure is false, skip upload
        if not self.runtime.get("upload_azure", False):
            self.log.info("upload_azure is false; skipping upload.")
            return
        
        # if azure is disabled, skip upload
        if not self.azure_enabled:
            self.log.warning("Azure disabled; skipping upload.")
            return

        # get interim data paths from settings.yaml
        interim_data = self.runtime.get("interim_data") or {}
        sources_to_upload = self.azure_cfg.get("sources_to_upload") or list(interim_data.keys())
        container_name = self.azure_cfg.get("container_name") or "unprocessed-data"
        blob_prefix = self.azure_cfg.get("blob_prefix") or ""
        if blob_prefix and not blob_prefix.endswith("/"):
            blob_prefix = blob_prefix + "/"

        root = project_root()
        blob_service_client = BlobServiceClient(
            account_url=self.AZURE_STORAGE_ACCOUNT_URL,
            credential=self.credential,
        )
        container_client = blob_service_client.get_container_client(container_name)

        for source_key in sources_to_upload:
            if source_key not in interim_data:
                continue
            relative_path = interim_data[source_key]
            local_path = root / relative_path
            if not local_path.exists():
                self.log.warning("Skipping %s: file not found at %s", source_key, local_path)
                continue
            blob_name = blob_prefix + Path(relative_path).name
            self._upload_file(container_client, local_path, blob_name)

        self.log.info("Upload stage finished.")

    def _upload_file(
        self,
        container_client,
        local_path: Path,
        blob_name: str,
    ) -> None:
        try:
            blob_client = container_client.get_blob_client(blob_name)
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            self.log.info("Uploaded %s -> %s", local_path.name, blob_name)
        except Exception as e:
            self.log.error("Failed to upload %s: %s", local_path.name, e)
