"""
Plotting module for PlanCatalyst dashboard visualisations.

Two distinct layers:

  1. Interim data plotters (pre-scoring, raw indicator time series):
       UNSDGDomain1Plotter — reads data/interim/cleaned/un_sdg_interim.csv

  2. Dashboard plotters (post-scoring, structured for Power BI):
       DashboardDataLoader  — loads data/interim/validated/ (reference implementation)
       HeatmapModePlotter   — global indicator views (mirrors Power BI globe/heatmap mode)
       CountryModePlotter   — country profiles + comparisons (mirrors Power BI country sidebar)

Quick start:
    from src.plotting.dashboard_data import DashboardDataLoader
    from src.plotting.dashboard_plotter import HeatmapModePlotter, CountryModePlotter

    loader = DashboardDataLoader()
    heatmap = HeatmapModePlotter(loader)
    country = CountryModePlotter(loader)

Or via the notebook:
    notebooks/dashboard_explorer.ipynb
"""

from src.plotting.plot_factory import DataPlotterFactory
from src.plotting.base_plotter import DataPlotter
from src.plotting.un_sdg_plotter import UNSDGDomain1Plotter
from src.plotting.dashboard_data import DashboardDataLoader
from src.plotting.dashboard_plotter import HeatmapModePlotter, CountryModePlotter

__all__ = [
    "DataPlotterFactory",
    "DataPlotter",
    "UNSDGDomain1Plotter",
    "DashboardDataLoader",
    "HeatmapModePlotter",
    "CountryModePlotter",
]
