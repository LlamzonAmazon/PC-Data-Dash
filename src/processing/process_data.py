from __future__ import annotations
from pathlib import Path
import logging
import yaml

class ProcessData:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.log = logging.getLogger(__name__)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Missing config at {self.config_path}")

        self.cfg = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))

    def process(self) -> None:
        """
        TODO:
        - Read cleaned/interim outputs (e.g., World Bank cleaned CSV)
        - Create processed 'actuals' + 'forecasts' outputs for Power BI
        - Upload to blob with clear naming
        """
        self.log.info("[PROCESS] placeholder ProcessData.process() ran successfully")
        print("\n[PROCESS] (placeholder) ProcessData ran successfully\n")