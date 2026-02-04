# Step 1: Data Loading (Read in Data from APIs, Import packages and such)

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from pmdarima import auto_arima # Tentative (I really have no clue what's happening here yet)

# Next we read in data from APIs
# But for now we'll read in a .csv file with some data while we figure out how to read api data




# Step 2: Exploratory Data Analysis (Identify null values, Plot random countries to gauge trends we’re working with)

# Step 3: Data Cleaning / Preprocessing (Get rid of null values, Get rid of null countries / years where no data was collected)

# Step 4: Train/Test Split

# Step 5: Model Building (Holt-Winters, ARIMA)

# Step 6: Model Evaluation (Use MAE, RMSE, MAPE (for interpretability?, Create confidence intervals?)

# Step 7: Conclusion