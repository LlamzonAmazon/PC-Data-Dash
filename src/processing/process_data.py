"""
Processing stage: writes **projections of indicator progress** under ``data/processed/``.

Today this is implemented for World Bank interim data only: historical actuals plus
simple forward-year projections (baseline last-value carry-forward). Those CSVs are
what the pipeline treats as *processed* outputs—distinct from cleaned interim files
and from scored *validated* outputs under ``data/interim/validated/``.
"""
from __future__ import annotations
from pathlib import Path
import logging
import yaml

import pandas as pd
from datetime import datetime
import logging
import os

from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv

from src.pipeline.utils import project_root


def upload_to_azure(container_client, csv_path: Path, blob_name: str, log) -> None:
    try:
        if not csv_path.exists():
            log.warning(f"CSV file not found: {csv_path}, skipping upload")
            return

        blob_client = container_client.get_blob_client(blob_name)

        with open(csv_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        log.info(f"Uploaded {csv_path.name} to Azure as {blob_name}")
    except Exception as e:
        log.error(f"Failed to upload {csv_path.name} to Azure: {e}")

class ProcessData:
    """Build indicator progress projections (actuals + forecast rows) for supported sources."""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.log = logging.getLogger(__name__)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Missing config at {self.config_path}")

        self.cfg = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))

    def process(self) -> None:
        # 1) Load config paths
        paths = self.cfg.get("paths", {})
        runtime = self.cfg.get("runtime", {})

        wb_rel = (runtime.get("interim_data") or {}).get("worldbank")
        if not wb_rel:
            raise ValueError("settings.yaml missing runtime.interim_data.worldbank")
        wb_interim_path = project_root() / wb_rel

        # Projections / processed outputs (see module docstring)
        processed_root = Path(paths.get("data_processed", "data/processed/")) / "worldbank"
        actuals_path = processed_root / "actuals" / "world_bank_actuals.csv"
        forecasts_path = processed_root / "forecasts" / "world_bank_forecasts.csv"
        actuals_path.parent.mkdir(parents=True, exist_ok=True)
        forecasts_path.parent.mkdir(parents=True, exist_ok=True)

        # 2) Read interim WB CSV
        if not wb_interim_path.exists():
            raise FileNotFoundError(f"Missing World Bank interim CSV at: {wb_interim_path}")

        wb = pd.read_csv(wb_interim_path)

        needed = {
            "country_code",
            "country_name",
            "year",
            "indicator-code",
            "indicator",
            "value",
        }
        missing = needed - set(wb.columns)
        if missing:
            raise ValueError(f"World Bank interim missing columns: {missing}. Found: {list(wb.columns)}")

        wb = wb.copy()  # avoid chained-assignment warnings in pandas 3.0
        wb.loc[:, "year"] = pd.to_numeric(wb["year"], errors="coerce").astype("Int64")
        wb.loc[:, "value"] = pd.to_numeric(wb["value"], errors="coerce")

        # 3) Write ACTUALS (just the cleaned series)
        actuals = wb.dropna(
            subset=["country_code", "country_name", "year", "indicator", "value"]
        ).copy()
        actuals["record_type"] = "actual"
        actuals["generated_at"] = datetime.utcnow().isoformat()
        actuals = actuals.copy()
        actuals.loc[:, "indicator_code"] = actuals["indicator-code"]

        actuals.to_csv(actuals_path, index=False)
        self.log.info(f"Wrote actuals: {actuals_path} (rows={len(actuals)})")

        # 4) Create FORECASTS (baseline: last value carried forward)
        # Choose how many future years you want:
        # - simplest: 5 years
        forecast_horizon = int(runtime.get("forecast_horizon_years", 5))

        last_obs = (
            actuals.sort_values(
                ["country_code", "country_name", "indicator_code", "year"]
            )
            .groupby(
                ["country_code", "country_name", "indicator_code"],
                as_index=False,
            )
            .tail(1)
            .rename(columns={"year": "last_year", "value": "last_value"})
        )

        # Build rows for (last_year+1 ... last_year+forecast_horizon)
        forecast_rows = []
        for row in last_obs.itertuples(index=False):
            base_year = int(row.last_year)
            for y in range(base_year + 1, base_year + 1 + forecast_horizon):
                forecast_rows.append({
                    "country_code": row.country_code,
                    "country_name": row.country_name,
                    "indicator-code": getattr(row, "indicator_code", None)
                    or getattr(row, "indicator-code", None),
                    "indicator": getattr(row, "indicator", None),
                    "year": y,
                    "value": row.last_value,
                    "record_type": "forecast",
                    "generated_at": datetime.utcnow().isoformat(),
                    "model_name": "baseline_last_value",
                })

        forecasts = pd.DataFrame(forecast_rows)
        forecasts.to_csv(forecasts_path, index=False)
        self.log.info(f"Wrote forecasts: {forecasts_path} (rows={len(forecasts)})")

        # 5) Upload to Azure Blob (optional; only if creds exist)
        load_dotenv()
        tenant = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        secret = os.getenv("AZURE_CLIENT_SECRET")
        account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")

        azure_enabled = all([tenant, client_id, secret, account_url]) and runtime.get("upload_azure", False)
        if not azure_enabled:
            self.log.warning("Azure upload disabled (missing creds or runtime.upload_azure is false). Done.")
            return

        credential = ClientSecretCredential(tenant_id=tenant, client_id=client_id, client_secret=secret)
        blob_service = BlobServiceClient(account_url=account_url, credential=credential)

        # Use the same container your team uses (CleanData used "unprocessed-data")
        container_name = runtime.get("azure_container_processed", "unprocessed-data")
        container_client = blob_service.get_container_client(container_name)

        # REQUIRED blob paths (per your instructions)
        upload_to_azure(container_client, actuals_path, "processed/worldbank/actuals/world_bank_actuals.csv", self.log)
        upload_to_azure(container_client, forecasts_path, "processed/worldbank/forecasts/world_bank_forecasts.csv", self.log)