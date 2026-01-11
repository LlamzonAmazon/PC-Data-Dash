# Source Code

This directory contains the source code for the data pipeline.

The data pipeline is split into three main modules:

- **Fetch**: Fetches data from various sources; does not store in Azure Blob Storage; stored locally in `/raw/`.
- **Clean**: Cleans the data and uploads it to Azure Blob Storage.
- **Process**: Processes the data and uploads it to Azure Blob Storage.

The data pipeline is run using the `run_pipeline.py` script.