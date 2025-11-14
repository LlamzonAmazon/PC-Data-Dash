# Data Fetchign Module
These scripts are used to fetch data from the UN SDG, ND-GAIN, and World Bank APIs.

# How to Run 
* Run `python3 -m src.fetch.data_fetch` from `/` (root).

# Module Status
* UN SDG and World Bank fetching done, interim CSV files written to `data/interim/`.
* Factory pattern still in the process of being implemented (`client_factory.py`)
* `settings.yaml` to be cleaned
* **Note**: We will be fetching specific indicators to be defined by PlanCatalyst. For now, we're just establishing a basis for the code architecture.

## UN SDG
The UN SDG Fetching Client is currently just configured to fetch goals, indicators, and targets from one specific url: 

* `https://unstats.un.org/SDGAPI/v1/sdg/Goal/List`


## ND-GAIN
* 

## World Bank Group
* `WorldBankClient` is currently fetching multiple countries' indicator data and storing the data in a combined DataFrame
* CSV written to `/data/interim` as well