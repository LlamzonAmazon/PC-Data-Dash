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
├── data/                         # Datasets (stored data, additional CSV files)
├── src/
│   ├── data_fetch/               # Fetch, clean, and structure data
│   |   ├── un_sdg_fetch.py
│   |   ├── nd_gain_fetch.py
│   |   ├── world_bank_fetch.py
│   ├── data_sources/             # Maintaining sources of data (API/CSV)
│   |   ├── un_sdg_src.py
│   |   ├── nd_gain_srcs.py
│   |   ├── world_bank_srcs.py
│   ├── model/                    # Data modelling scripts (scikit-learn)
│   ├── powerbi/                  # Pipelining processed data into PowerBI
│   ├── aws/                      # AWS (S3 storage, Lambda automation)
├── requirements.txt              # Install dependencies
├── README.md
└── LICENSE
```

## 📝 Environment Setup
We are using a Python Virtual Environment to ensure all team members' development environments are synced. All team members will have to:
1. Create your own virtual environment with `python3 -m venv venv`
2. Activate venv with `source venv/bin/activate` (MacOS) or `venv\Scripts\Activate.ps1` (Windows)
3. Install dependencies from `requirements.txt` with `pip install -r requirements.txt`
4. Verify Setup with `pip list`

**Important Note**: the venv folder is NEVER pushed to the public repo as it exposes sensitive machine configuration data.

## 🌐 Team
This dashboard is made by __[Tech for Social Impact](https://www.uwotsi.com) (TSI)__.

* __Project Managers__: Thomas Llamzon, Anthony Lam
* __Developers__: Adeline Lue Sang, Caroline Shen, Christina Wong, Kayden Jaffer, Tyler Asai
