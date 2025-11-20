# Data Fetching Module
These scripts are used to fetch data from the UN SDG, ND-GAIN, and World Bank APIs.

## Module Information
* Run `python3 -m src.fetch.data_fetch` from project root.
  * You'll motice 3 CSVs written to the `/data` folder
* This module implements _the Factory Pattern_ to easily design and instantiate clients for new data sources, as well as easily manage the existing clients.
* Currently working on: 
  * reconfiguring this module for AWS cloud automation and computing
  * unifying client implementations and addressing overlapping behaviours
  * optimizing outputs for input into data processing module

### United Nations Sustainable Development Goals (UN SGDs)
The SDG framework measures global development through a hierarchy of:
- 17 Goals – Broad global development objectives 
- 169 Targets – Measurable sub-objectives under each goal
- ~250+ Indicators – Numerical metrics used to assess progress toward a target
- Series – Statistical definitions used to publish values for an indicator

__Indicators__ are the concepts being measured and series are the actual numeric data published for each indicator. These series form year-by-year development time series for every country, covering health, education, poverty, sustainability, infrastructure, and governance.

The `UNSDGClient` currently gathers a specific set of 22 indicators (can be found in `/src/config/settings.yaml`) from the UN SDGs public API V5: https://unstats.un.org/sdgs/UNSDGAPIV5/v1/sdg. It uses only the indicator data endpoint: `/Indicator/Data`, which returns a specified country's observation value of a specific development indicator for all years within the specified time range.

### Notre Dame Global Adaptation Index (ND-GAIN)
We are currently using the ZIP file from the ND-GAIN [bulk download page](https://gain.nd.edu/our-work/country-index/download-data/) on their website. This is the only viable, and most up-to-date data source we can currently find.

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
* Enable time-series modeling and forecasting once combined with UN SDG/World Bank data

These composites give the dashboard meaningful, policy-relevant climate development metrics that can be tracked and forecasted over time.

### World Bank Group
The World Bank publishes one of the __largest collections of global development, economic, demographic, and environmental time-series__. Each metric is defined as an indicator (e.g., GDP per capita, CO₂ emissions, school enrollment), and nearly all indicators provide annual values by country, often spanning decades.

Our WorldBankClient retrieves a configurable set of indicators (defined in `/src/config/settings.yaml`) using the World Bank’s `/country/{codes}/indicator/{id}` endpoint. For each indicator, the API returns:

- annual numeric observations
- the year
- simple metadata (source, units, etc.)

These indicators fill the __economic and demographic__ layer of the project. They provide reliable long-term signals such as population growth, economic productivity, trade, emissions, and resource use.

We use World Bank data because it:

- Supplies stable __long-horizon time series__ needed for regression and forecasting
- Complements SDG social metrics and ND-GAIN climate metrics
- Supports building __composite indexes__ that combine economic, social, and climate dimensions
- Enables interpretable country-level comparisons grounded in widely trusted, standardized data

In short, World Bank indicators give us the economic and demographic backbone required for robust modeling, forecasting, and index construction.
