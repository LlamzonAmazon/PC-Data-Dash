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

## Indicator Documentations
- 3.8.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-08-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-08-01.pdf)
- 3.3.2 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-03-02.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-03-02.pdf)
- 3.3.3 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-03-03.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-03-03.pdf)
- 3.1.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-01-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-01-01.pdf)
- 3.2.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-01-02.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-01-02.pdf)
- 2.2.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-02-02-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-02-02-01.pdf)
- 2.2.2 – [https://unstats.un.org/sdgs/metadata/files/Metadata-02-02-02a.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-02-02-02a.pdf)
- 2.2.3 – [https://unstats.un.org/sdgs/metadata/files/Metadata-02-02-03.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-02-02-03.pdf)
- 3.7.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-07-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-07-01.pdf)
- 3.7.2 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-07-02.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-07-02.pdf)
- 3.d.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-0D-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-0D-01.pdf)
- 2.1.2 – [https://unstats.un.org/sdgs/metadata/files/Metadata-02-01-02.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-02-01-02.pdf)
- 2.4.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-02-04-01proxy.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-02-04-01proxy.pdf)
- 2.a.2 – [https://unstats.un.org/sdgs/metadata/files/Metadata-02-0A-02.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-02-0A-02.pdf)
- 6.1.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-06-01-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-06-01-01.pdf)
- 6.2.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-06-02-01a.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-06-02-01a.pdf)
- 3.9.2 – [https://unstats.un.org/sdgs/metadata/files/Metadata-03-09-02.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-03-09-02.pdf)
- 7.1.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-07-01-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-07-01-01.pdf)
- 7.1.2 – [https://unstats.un.org/sdgs/metadata/files/Metadata-07-01-02.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-07-01-02.pdf)
- 7.2.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-07-02-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-07-02-01.pdf)
- 8.10.2 – [https://unstats.un.org/sdgs/metadata/files/Metadata-08-10-02.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-08-10-02.pdf)
- Gender Inequality Index – [https://hdr.undp.org/sites/default/files/2023-24_HDR/hdr2023-24_technical_notes.pdf](https://hdr.undp.org/sites/default/files/2023-24_HDR/hdr2023-24_technical_notes.pdf)
- ND-GAIN Vulnerability Index – [https://gain.nd.edu/assets/522870/nd_gain_countryindextechreport_2023_01.pdf](https://gain.nd.edu/assets/522870/nd_gain_countryindextechreport_2023_01.pdf)
- State Capacity Index – [http://www-personal.umich.edu/~jkhanson/state_capacity.html](http://www-personal.umich.edu/~jkhanson/state_capacity.html)
- 1.2.1 – [https://unstats.un.org/sdgs/metadata/files/Metadata-01-02-01.pdf](https://unstats.un.org/sdgs/metadata/files/Metadata-01-02-01.pdf)
- Global Multidimensional Poverty Index (MPI) – [https://hdr.undp.org/mpi-2024-faqs](https://hdr.undp.org/mpi-2024-faqs)

