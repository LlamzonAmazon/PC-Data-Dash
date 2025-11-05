# PlanCatalyst Data Dashboard
__🌍 Check out [PlanCatalyst](https://www.PlanCatalyst.org) today!__

We're building an interactive dashboard for PlanCatalyst’s redesigned website that models country-level development progress such as:
* __UN SDGs__ (United Nations Sustainable Development Goals) – Human Rights & Gender Equity
* __ND-GAIN__ (Notre Dame Global Adaptation Index) – Climate Change Resilience
* __World Bank Data__ – Financial Capacity

This dashboard features live and predictive data insights using __composite indexes__ and __regression for development forecasting__ to emphasize the organization's committment to data-driven decicsion making.

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
│   └── aws/                      # AWS (S3 storage, Lambda automation, etc.)
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

## 🌐 Team
This dashboard is made by __[Tech for Social Impact](https://www.uwotsi.com) (TSI)__.

* __Project Managers__: Thomas Llamzon, Anthony Lam
* __Developers__: Adeline Lue Sang, Caroline Shen, Christina Wong, Kayden Jaffer, Tyler Asai
