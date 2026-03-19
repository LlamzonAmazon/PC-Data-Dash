from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .base import IndicatorScorer


class SimpleDirectionalScorer(IndicatorScorer):
    """Score = 100 - value (the “gap” or “need”), clamped to [0, 100]."""

    def score(self, df: pd.DataFrame) -> pd.Series:
        return self.clamp_0_100(100.0 - df["value"].astype(float))


class RatioThresholdScorer(IndicatorScorer):
    """
    Standard logic used for many “lower is better” indicators:

        score_raw = 1 - (threshold / value)
        score = clamp_0_100(score_raw * 100)

    Optionally harmonizes to 0 when the country is better than a
    specified global-average value.
    """

    def __init__(self, threshold: float, global_average: Optional[float] = None):
        self.threshold = float(threshold)
        self.global_average = (
            float(global_average) if global_average is not None else None
        )

    def score(self, df: pd.DataFrame) -> pd.Series:
        values = df["value"].astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            raw = 1.0 - (self.threshold / values)
        scores = self.clamp_0_100(raw * 100.0)

        # If a global average is provided, harmonize: values better than the
        # global average (directionality implied by threshold) are set to 0.
        if self.global_average is not None:
            mask = values < self.global_average
            scores = scores.where(~mask, other=0.0)

        return scores


class InverseRatioScorer(IndicatorScorer):
    """
    Two-step logic used for some “gap” indicators (e.g., water, finance):

        gap_country = 100 - value
        gap_global  = 100 - global_avg_val
        score_raw   = 1 - (gap_global / gap_country)
        score       = clamp_0_100(score_raw * 100)

    Harmonizes to 0 if the country gap is smaller (better) than the
    global-average gap.
    """

    def __init__(self, global_avg_val: float):
        # Client framework provides the benchmark as the *gap* directly.
        self.threshold_gap = float(global_avg_val)

    def score(self, df: pd.DataFrame) -> pd.Series:
        country_gap = 100.0 - df["value"].astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            raw = 1.0 - (self.threshold_gap / country_gap)
        scores = self.clamp_0_100(raw * 100.0)
        scores = scores.where(country_gap >= self.threshold_gap, other=0.0)
        return scores


class RatioGoalInverseScorer(IndicatorScorer):
    """
    Logic for 2.4.1 (sustainable agriculture):

        transformed = 1 / value^2
        score_raw   = 1 - (goal_transformed / transformed)
        score       = clamp_0_100(score_raw * 100)
    """

    def __init__(self, goal_transformed: float = 0.04):
        self.goal = float(goal_transformed)

    def score(self, df: pd.DataFrame) -> pd.Series:
        values = df["value"].astype(float)
        transformed = 1.0 / np.square(values)
        with np.errstate(divide="ignore", invalid="ignore"):
            raw = 1.0 - (self.goal / transformed)
        scores = self.clamp_0_100(raw * 100.0)
        return scores


class GoalRatioScorer(IndicatorScorer):
    """
    Logic for indicators with an explicit goal as a ratio (e.g., DC_TOF_AGRL):

        score_raw = 1 - (value / goal)
        score     = clamp_0_100(score_raw * 100)
    """

    def __init__(self, goal: float, global_average: Optional[float] = None):
        self.goal = float(goal)
        self.global_average = (
            float(global_average) if global_average is not None else None
        )

    def score(self, df: pd.DataFrame) -> pd.Series:
        values = df["value"].astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            raw = 1.0 - (values / self.goal)
        scores = self.clamp_0_100(raw * 100.0)

        if self.global_average is not None:
            mask = values > self.global_average
            scores = scores.where(~mask, other=0.0)

        return scores


class DensityScorer(IndicatorScorer):
    """Continuous scoring for population density."""

    def score(self, df: pd.DataFrame) -> pd.Series:
        v = df["value"].astype(float)
        scores = (v / 0.7) * 100.0
        return self.clamp_0_100(scores)