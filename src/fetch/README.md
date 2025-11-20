# Data Fetching Module
These scripts are used to fetch data from the UN SDG, ND-GAIN, and World Bank APIs.

# How to Run 
* Run `python3 -m src.fetch.data_fetch` from project root.

## UN SDG
The UN SDG Fetching Client is currently just configured to fetch goals, indicators, and targets from one specific url: 
* `https://unstats.un.org/SDGAPI/v1/sdg/Goal/List`
* 

## ND-GAIN
The `resources/indicators/` folder contains all raw ND-GAIN climate indicators. These indicators are the inputs used to build the ND-GAIN Vulnerability Index, Readiness Index, and overall ND-GAIN score. Each indicator is defined in the ND-GAIN Country Index Codebook (`/data/external/ND_GAIN Country Index Codebook.pdf`).

ND-GAIN indicators quantify how climate change affects a country across __six vulnerability sectors__ to make __the ND-GAIN Vulnerability Index__:
1. Food (`id_food_X`)
2. Water (`id_wate_X`)
3. Health (`id_heal_X`)
4. Ecosystem Services (`id_ecos_X`)
5. Human Habitat (`id_habi_X`)
6. Infrastructure (`id_infr_X`)

Each sector contains _six_ indicators where each indicator measures a specific climate exposure, sensitivity, or capacity (e.g., projected cereal yield change, freshwater withdrawal rate, flood hazard, medical staff, etc.). Additional indicators exist the __three Readiness sectors__ (economic, governance, social). A __sector score__ is the mean of its six indicators for a specific country—a single number that summarizes a country’s vulnerability in that domain. Sector scores only have meaning per country, since they’re derived from country-specific indicator data. All sector scores are required to compute _the Vulnerability Index_. Readiness indicators help compute _the Readiness Index_.

We use all raw indicators in resources/indicators/ because they:
* Represent the fundamental climate-risk variables per country
* Allow construction of sector scores, vulnerability, readiness, and custom indices
* Create interpretable measures for cross-country comparison
* e=Enable time-series modeling and forecasting once combined with UN SDG/World Bank data

These composites give the dashboard meaningful, policy-relevant climate development metrics that can be tracked and forecasted over time.

## World Bank Group
* `WorldBankClient` is currently fetching multiple countries' indicator data and storing the data in a combined DataFrame
* CSV written to `/data/interim` as well
