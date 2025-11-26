# PlanCatalyst Data Dashboard

We're building an interactive dashboard for [PlanCatalyst](https://www.PlanCatalyst.org)’s redesigned website that forecasts country-level development progress on:
* __UN SDGs__ (United Nations Sustainable Development Goals) – Human Rights & Gender Equity
* __ND-GAIN__ (Notre Dame Global Adaptation Index) – Climate Change Resilience
* __World Bank Data__ – Financial Capacity

We are exploring ML **regression** techniques using scikit-learn to forecast country-level development and NumPy to construct **composite indexes**. **AWS** automates data fetching and data storage, while **Microsoft Power BI** delivers the interactive frontend.


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

## ☁️ AWS Architecture
***The AWS architecture of this project is still being designed & developed.***
![AWS Architecture Diagram](./AWS-arch.png)

## 🏙️ Code Structure
***The structure of this project is still being designed.***
```
PC-DATA-DASH/
├── .vscode/
│
├── data/                             # LOCAL ONLY - for development/testing
│   ├── external/                     # Keep structure
│   ├── interim/
│   │   ├── ndgain/
│   │   ├── unsdg/
│   │   └── worldbank/
│   ├── processed/
│   └── raw/
│
├── notebooks/                        # For analysis
│   ├── EDA_un_sdg.ipynb
│   └── EDA_world_bank.ipynb
│
├── src/                              # DEPLOYABLE CODE
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.yaml
│   │   └── config.py                 # Config loader class ?
│   │
│   ├── fetch/                        # Keep your existing structure
│   │   ├── __init__.py
│   │   ├── base_fetch.py             # DataClient Template (interface)
│   │   ├── client_factory.py         # DataClient Factory
│   │   ├── un_sdg_fetch.py
│   │   ├── nd_gain_fetch.py
│   │   ├── world_bank_fetch.py
│   │   ├── data_fetch.py             # Main fetching script
│   │   └── README.md
│   │
│   ├── transform/                    # Data Processing
│   │   ├── __init__.py
│   │   ├── processor.py              # Cleaning logic
│   │   ├── clean_un_sdg.py 
│   │   ├── clean_nd_gain.py
│   │   └── clean_world_bank.py
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # Main pipeline controller
│   │   ├── run_pipeline.py           # Orchestrator
│   │   └── utils.py
│   │
│   ├── aws/                          # AWS Plans
│   │   ├── __init__.py
│   │   ├── s3.py                     # S3 upload operations
│   │   └── logger.py                 # CloudWatch logging
│   │
│   └── models/                       # Keep for future ML
│       ├── __init__.py
│       ├── regression.py
│       └── forecasting.py
│
├── lambda/                           # NEW: Lambda deployment package
│   ├── handler.py                    # Lambda entry point
│   ├── requirements.txt              # Runtime dependencies
│   └── README.md                     # Deployment notes
│
├── infrastructure/                  # IaC templates
│   ├── cloudformation/  
│   │   ├── s3-buckets.yaml          # S3 bucket definitions
│   │   ├── lambda.yaml              # Lambda + IAM roles
│   │   ├── eventbridge.yaml         # Scheduling
│   │   └── glue-database.yaml       # Glue catalog (for Athena)
│   │
│   ├── terraform/                    # Future migration
│   │   └── (empty for now)
│   │
│   └── athena-schemas/               # SQL DDL for Athena tables
│       ├── sdg_indicators.sql        # Run once in Athena console
│       ├── nd_gain_scores.sql
│       └── world_bank_data.sql
│
├── deployment/                      # Deployment automation
│   ├── build-lambda.sh              # Package Lambda code
│   ├── deploy-lambda.sh             # Deploy to AWS
│   └── setup-athena.sh              # Run Athena DDL scripts
│
├── powerbi/                         # Power BI connection info
│   ├── athena-connection.md         # How to connect to Athena
│   └── example-queries.sql          # Sample queries for testing
│
├── tests/                            # Tests
│   ├── test_fetch.py
│   ├── test_transform.py
│   └── test_pipeline.py
│
├── .env.example                      # Environment variables template ?
├── .gitignore
├── AWS-arch.png
├── requirements.txt
├── README.md
└── LICENSE
```

## 🌐 Team
This dashboard is made by __[Tech for Social Impact](https://www.uwotsi.com) (TSI)__.

* __Project Managers__: Thomas Llamzon, Anthony Lam
* __Developers__: Adeline Lue Sang, Caroline Shen, Christina Wong, Kayden Jaffer, Tyler Asai
