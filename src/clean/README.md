# Data Cleaning Module

## Overview
This module is responsible for cleaning the raw data from the corresponding fetching clients: World Bank, UN SDG, and ND-GAIN.

The data is passed from the fetching module to the cleaning module by reference. The raw data is **not** stored in production, it can be stored only for development for faster debugging.

## Running this Module
This module may be run from its main class, `CleanData` in `clean_data.py`, and will use the exiting data stored at `/data/raw`. It will not restart the entire pipeline from the fetching clients.

## Responsibilities of this Module
- Cleaning the raw data
  - Converting to Pandas DataFrames
  - Removing duplicates
  - Handling null values
  - Extracting relevant data
  - et cetera
- Converting the raw data to a tidy format
- Uploading the cleaned data to a CSV file to **Azure Blob Storage**

## Module Architecture
![cleaning](CLEANING.png)

This module implements the abstract factory pattern to create the appropriate cleaner objects based on the source of the data, as well as to allow for easy extension of the module to support additional sources in the future.
