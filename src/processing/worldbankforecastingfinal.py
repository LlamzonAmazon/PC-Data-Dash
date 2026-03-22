# Import packages and warnings
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from pmdarima import auto_arima
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", message="Non-stationary starting autoregressive parameters")
warnings.filterwarnings("ignore", category=UserWarning)
warnings.simplefilter('ignore', ConvergenceWarning)

from src.pipeline.utils import project_root
project_root = project_root()
df = pd.read_csv(project_root / 'data/interim/world_bank_interim.csv')
future_predictions = []

for country in df["country"].unique():
    # 1. Clean and Prepare
    df_subset = df[df["country"] == country].sort_values("year").dropna(subset=["value"])
    
    # Need enough history to train ARIMA(1,1,0)
    if len(df_subset) < 5: 
        continue

    y = df_subset["value"]
    y.index = pd.PeriodIndex(df_subset["year"], freq="Y")

    try:
        # 2. Train on ALL available data
        model = ARIMA(y, order=(1, 1, 0)).fit()
        
        # 3. Forecast 6 years ahead (2024, 2025, 2026, 2027, 2028, 2029)
        # Assuming your data ends in 2023
        forecast_series = model.forecast(steps=6)
        
        # 4. Map the forecasts to the specific years
        # forecast_series[3] = 2027, [4] = 2028, [5] = 2029
        years = [2027, 2028, 2029]
        forecast_values = forecast_series.iloc[3:].values 

        for year, val in zip(years, forecast_values):
            future_predictions.append({
                "country": country,
                "year": year,
                "predicted_value": round(val, 4)
            })
            
    except Exception as e:
        continue

# 5. Output the results
final_predictions_df = pd.DataFrame(future_predictions)

output_path = project_root / 'data' / 'processed' / 'forecastedworldbank.csv'
final_predictions_df.to_csv(output_path, index=False)