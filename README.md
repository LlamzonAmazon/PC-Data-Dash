# PlanCatalyst Data Dashboard
__🌍 Check out [PlanCatalyst](https://www.PlanCatalyst.org) today!__

We're building an interactive dashboard for PlanCatalyst’s redesigned website that models country-level development progress such as:
* __UN SDGs__ (United Nations Sustainable Development Goals) – Human Rights & Gender Equity
* __ND-GAIN__ (Notre Dame Global Adaptation Index) – Climate Change Resilience
* __World Bank Data__ – Financial Capacity

This dashboard features live and predictive data insights using __composite indexes__ and __regression for development forecasting__ to emphasize the organization's committment to data-driven decicsion making.

## 💻 Stack
* __Data Sources__:
  * World Bank (Bulk download)
  * UN SDGs (API)
  * ND-GAIN (API)
* __Data Processing__: Python, Pandas, Scikit-learn
*  __Data Storage__: AWS S3
* __Automated Data Parsing__: AWS Lambda
* __Data Visualization__: Microsoft PowerBI

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
