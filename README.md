# PlanCatalyst Data Dashboard

We're building an interactive dashboard for [PlanCatalyst](https://www.PlanCatalyst.org)’s redesigned website that forecasts country-level development progress on:
* __UN SDGs__ (United Nations Sustainable Development Goals) – Human Rights & Gender Equity
* __ND-GAIN__ (Notre Dame Global Adaptation Index) – Climate Change Resilience
* __World Bank Data__ – Financial Capacity

We are exploring ML **regression** techniques (XGBoost/Random Forest) using scikit-learn to forecast country-level development, and NumPy to construct **composite indexes**. **AWS** automates data fetching and data storage, while **Microsoft Power BI** delivers the interactive frontend.

## 🏙️ Code Structure
***The structure of this project is still being designed.***
```
PC-Data-Dash/
├── data/                         # DATA
│   ├── raw/                      # Unmodified API/CSV outputs
│   ├── interim/                  # Cleaned/intermediate data
│   └── processed/                # Final data for PowerBI
│
├── src/                          # SOURCE CODE
│   ├── fetch/                    # Data fetching (APIs, CSV ingestion)
│   │   ├── un_sdg_fetch.py
│   │   ├── nd_gain_fetch.py
│   │   └── world_bank_fetch.py
│   │
│   ├── transform/                # Cleaning + structuring scripts
│   │   ├── clean_un_sdg.py
│   │   ├── clean_nd_gain.py
│   │   └── clean_world_bank.py
│   │
│   ├── models/                   # Data modeling (ML/indices, scikit-learn, XGBoost?)
│   │   ├── regression.py
│   │   └── forecasting.py
│   │
│   ├── pipeline/                 # Handling data pipeline flow
│   │   ├── run_pipeline.py       
│   │   └── utils.py              # Helpers? (logging, config, etc.)
│   │
│   ├── config/                   # Config files (API keys, URLs, paths)
│   │   └── settings.yaml
│   │
│   └── aws/                      # AWS (S3 storage? Lambda automation?)
│       ├── 
│
├── notebooks/                    # Model testing/analysis?
│   ├── EDA_un_sdg.ipynb
│   └── EDA_world_bank.ipynb
│
├── powerbi/                      # POWERBI
│   ├── data_export.py
│   └── schema_definition.json
│
├── requirements.txt              # venv dependencies
├── dockerfile                    # 🐳
├── README.md                     
└── LICENSE
```
## 📌 References/Resources
* [UN SDG API V5](https://unstats.un.org/sdgs/UNSDGAPIV5/swagger/index.html) – UN SDGs, indicators, and targets data API
* [UN SDG Data Commons](https://unstats.un.org/UNSDWebsite/undatacommons/sdgs) – Shows SDG progress by goal, indicator, and country.
  * Can also be used to see REST V2 API request code for a query
* [ND-GAIN Kaggle](https://www.kaggle.com/datasets/shabou/ndgain-country-index/data/code)
* [ND-GAIN CSV](https://gain.nd.edu/our-work/country-index/download-data/)
* 

## 🌐 Team
This dashboard is made by __[Tech for Social Impact](https://www.uwotsi.com) (TSI)__.

* __Project Managers__: Thomas Llamzon, Anthony Lam
* __Developers__: Adeline Lue Sang, Caroline Shen, Christina Wong, Kayden Jaffer, Tyler Asai
