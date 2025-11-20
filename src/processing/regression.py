''' Regression class to be used on interim data after model R&D in ../../notebooks/ '''

# Simple scikit-learn pipeline stub
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

def train_rf(df_wide: pd.DataFrame, target: str):
    X = df_wide.drop(columns=[target]).select_dtypes("number").fillna(0)
    y = df_wide[target]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=300, random_state=42).fit(Xtr, ytr)
    return model, model.score(Xte, yte)
