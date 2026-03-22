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
    Upload validated scoring outputs (src/calculating) to Azure Blob Storage.

    Reads files under paths.data_interim_validated (default data/interim/validated/):
    composite CSVs, Indicator_Scores_Full.csv, and indicatorscores/*.csv.

    Blob names preserve relative paths under that folder (optionally under azure.blob_prefix)
    for straightforward Power BI folder connections.

    Azure credentials come from the project .env (see .env.example).

    Instance variables (set in __init__ / _load_config):
      config_path      Path to settings.yaml
      log              Logger
      AZURE_*          From .env (tenant, client, secret, storage URL)
      credential       ClientSecretCredential if all AZURE_* set, else None
      azure_enabled    True if credential is set
      cfg              Full parsed settings.yaml dict
      runtime          cfg["runtime"] (upload_azure, ...)
      paths_cfg        cfg["paths"] (data_interim_validated, ...)
      azure_cfg        cfg["azure"] (container_name, blob_prefix, validated_upload_paths)
    """

    def __init__(self, config_path: Path) -> None:
        load_dotenv(project_root() / ".env")

        self.config_path = Path(config_path)
        self.log = setup_logger()

        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        self.AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")

        has_all_azure_creds = all(
            [
                self.AZURE_TENANT_ID,
                self.AZURE_CLIENT_ID,
                self.AZURE_CLIENT_SECRET,
                self.AZURE_STORAGE_ACCOUNT_URL,
            ]
        )

        if has_all_azure_creds:
            self.credential = ClientSecretCredential(
                tenant_id=self.AZURE_TENANT_ID,
                client_id=self.AZURE_CLIENT_ID,
                client_secret=self.AZURE_CLIENT_SECRET,
            )
            self.azure_enabled = True
        else:
            self.credential = None
            self.azure_enabled = False
            self.log.warning(
                "Azure credentials not set in environment or .env. Azure upload will be skipped."
            )

        self._load_config()

    def _load_config(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f) or {}

        self.runtime = self.cfg.get("runtime") or {}
        self.paths_cfg = self.cfg.get("paths") or {}
        self.azure_cfg = self.cfg.get("azure") or {}

    def _iter_local_files(self, validated_root: Path) -> list[Path]:
        """
        Return files to upload, sorted for deterministic order.
        If azure.validated_upload_paths is set, only those entries (files or dirs);
        otherwise all files under validated_root recursively.
        """
        if "validated_upload_paths" not in self.azure_cfg:
            return sorted(p for p in validated_root.rglob("*") if p.is_file())

        explicit = self.azure_cfg.get("validated_upload_paths") or []
        if not explicit:
            return []

        out: list[Path] = []
        for entry in explicit:
            local = validated_root / str(entry).strip("/")
            if local.is_file():
                out.append(local)
            elif local.is_dir():
                out.extend(sorted(p for p in local.rglob("*") if p.is_file()))
            else:
                self.log.warning("Skipping validated_upload_paths entry (not found): %s", entry)
        return sorted(set(out))

    def upload(self) -> None:
        if not self.runtime.get("upload_azure", False):
            self.log.info("upload_azure is false; skipping upload.")
            return

        if not self.azure_enabled:
            self.log.warning("Azure disabled; skipping upload.")
            return

        validated_rel = self.paths_cfg.get("data_interim_validated", "data/interim/validated/")
        container_name = self.azure_cfg.get("container_name") or "unprocessed-data"
        blob_prefix = self.azure_cfg.get("blob_prefix") or ""
        if blob_prefix and not blob_prefix.endswith("/"):
            blob_prefix = blob_prefix + "/"

        root = project_root()
        validated_root = (root / validated_rel).resolve()

        if not validated_root.is_dir():
            self.log.warning(
                "Validated data directory missing at %s; skipping upload.", validated_root
            )
            return

        files = self._iter_local_files(validated_root)
        if not files:
            self.log.warning("No files to upload under %s", validated_root)
            return

        blob_service_client = BlobServiceClient(
            account_url=self.AZURE_STORAGE_ACCOUNT_URL,
            credential=self.credential,
        )
        container_client = blob_service_client.get_container_client(container_name)

        for local_path in files:
            try:
                rel = local_path.relative_to(validated_root)
            except ValueError:
                self.log.warning("Skipping path outside validated root: %s", local_path)
                continue
            blob_name = blob_prefix + rel.as_posix()
            self._upload_file(container_client, local_path, blob_name)

        self.log.info("Upload stage finished (%d files).", len(files))

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
