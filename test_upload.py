"""
Uploads existing validated data to Azure without running the full pipeline.

Skips fetch, clean, and scoring stages. Reads files already present under
data/interim/validated/ and uploads them to Azure Blob Storage using the
same logic as the full orchestrator.

Useful for testing Azure connectivity and upload configuration.
"""

from dotenv import load_dotenv
from src.pipeline.utils import project_root
from src.upload.upload_validated import UploadValidated

load_dotenv(project_root() / ".env")


def main() -> None:
    config_path = project_root() / "src/config/settings.yaml"
    uploader = UploadValidated(config_path)
    uploader.upload()


if __name__ == "__main__":
    main()
