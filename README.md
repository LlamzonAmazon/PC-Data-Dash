# PlanCatalyst Data Dashboard

We're building an interactive dashboard for [PlanCatalyst](https://www.PlanCatalyst.org)’s redesigned website that forecasts country-level development progress on:
* __UN SDGs__ (United Nations Sustainable Development Goals) – Human Rights & Gender Equity
* __ND-GAIN__ (Notre Dame Global Adaptation Index) – Climate Change Resilience
* __World Bank Data__ – Financial Capacity

We are exploring ML **regression** techniques using scikit-learn to forecast country-level development, and NumPy to construct **composite indexes**. **AWS** automates data fetching and data storage, while **Microsoft Power BI** delivers the interactive frontend.


## 📌 References/Resources
### UN SDGs
* [UN SDG **API** V1](https://unstats.un.org/sdgapi/swagger/#!/)
* [UN SDG **API** V5](https://unstats.un.org/sdgs/UNSDGAPIV5/swagger/index.html) 
* [UN Statistics Division](https://unstats.un.org/UNSDWebsite/#) – **Gateway** to UN SDG data
  * Provides lots of background on the goals, indicators, methodology, statistics, etc.
* [UN SDG Data Commons](https://unstats.un.org/UNSDWebsite/undatacommons/sdgs) – **Resource** that shows SDG progress by goal, indicator, and country
  * Can be used to preview API request for a given query
  * Features interactive maps (good reference)
* [UN SDG Indicators Home](https://unstats.un.org/sdgs/) – **Gateway** to UN SDG data resources
  * Provides background on lots of SDG information as well 
* [UN SDG Data Portal](https://unstats.un.org/sdgs/dataportal) – **Database** of all indicator data
### ND-GAIN Index
* [ND-GAIN CSV](https://gain.nd.edu/our-work/country-index/download-data/) – Official University of Notre Dame source for downloading the latest ND-GAIN Country Index in CSV format
* [ND-GAIN Technical Report](https://gain.nd.edu/assets/522870/nd_gain_countryindextechreport_2023_01.pdf)
* [ND-GAIN Indicators](https://gain.nd.edu/assets/522870/nd_gain_countryindextechreport_2023_01.pdf)
### World Bank Group
* [World Bank Open Data](https://data.worldbank.org/) – Repo of global development & economic indicators
  * Features an interactive map (good reference)
* [World Bank DataBank](https://databank.worldbank.org/home.aspx) – Browser tool; helps define API parameters to use before making API calls
* [API V2 Documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation?utm_source=chatgpt.com) – API Guide
* [World Bank API Documentation](https://documents.worldbank.org/en/publication/documents-reports/api) – API guide


## 🏙️ Code Structure
***The structure of this project is still being designed.***
```
PC-Data-Dash/
├── data/
│   ├── raw/                      # Unmodified API/CSV outputs
│   ├── interim/                  # Cleaned/intermediate data
│   └── processed/                # Final data for PowerBI
│
├── src/
│   ├── fetch/                    # Data Fetching Module
│   │   ├── data_fetch.py         # Main script
│   │   ├── un_sdg_fetch.py       # UN SDG Client
│   │   ├── nd_gain_fetch.py      # ND-GAIN Client
│   │   ├── world_bank_fetch.py   # World Bank Client
│   │   ├── base_fetch.py         # Data client interface (template)
│   │   ├── client_factory.py     # Client Factory Class
│   │   └── README.md
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
│   ├── config/                   # Config files (indicators, URLs, request constraints, etc.)
│   │   └── settings.yaml
│   │
│   └── aws/                      # AWS (S3 storage? Lambda automation?)
│       ├── 
│
├── notebooks/
│   ├── EDA_un_sdg.ipynb
│   └── EDA_world_bank.ipynb
│
├── powerbi/
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
