# Example transform: pivot to wide for Power BI if needed
import pandas as pd

def to_wide(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index=["country","iso3","year"], columns="indicator", values="value").reset_index()
