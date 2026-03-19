from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

import pandas as pd


class IndicatorScorer(ABC):
    """
    Abstract base for all indicator scoring strategies.

    Implementations receive a DataFrame filtered to a single indicator/series
    and must return a pandas Series of 0–100 scores aligned to the input index.
    """

    @abstractmethod
    def score(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    @staticmethod
    def clamp_0_100(series: pd.Series) -> pd.Series:
        return series.clip(lower=0.0, upper=100.0)


class ScorerFactory(Protocol):
    """
    Protocol for factories that create IndicatorScorer instances.
    """

    def for_series(self, series_code: str) -> IndicatorScorer:
        ...

