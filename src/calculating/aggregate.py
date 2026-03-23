from __future__ import annotations

from typing import Dict, Iterable, Tuple

import pandas as pd

from .hierarchy import INDICATORS, IndicatorMeta
from .weights import DOMAIN_WEIGHTS, SECTOR_WEIGHTS, SUBSECTOR_WEIGHTS, get_ihr_component_weights


def _available_case_mean(series: pd.Series) -> float:
    return float(series.dropna().mean()) if series.notna().any() else float("nan")


def _attach_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Annotate scored indicator rows with domain/sector/subsector metadata.
    """
    meta_df = (
        pd.DataFrame.from_records(
            [
                {
                    "series_code": meta.series_code,
                    "indicator_id": meta.indicator_id,
                    "domain_id": meta.domain_id,
                    "sector_id": meta.sector_id,
                    "subsector_id": meta.subsector_id,
                }
                for meta in INDICATORS.values()
            ]
        )
        .set_index("series_code")
    )

    return df.join(meta_df, on="series_code", how="left")


def _prefer_aggregate_value(group: pd.DataFrame, column: str, aggregate_value: str) -> pd.DataFrame:
    """
    Within a single country/year/indicator group, prefer the aggregate value
    (e.g., BOTHSEX, ALLAREA, _T) *if it exists*; otherwise, keep whatever
    disaggregations are present.
    """
    values = group[column].dropna().unique()
    if aggregate_value in values:
        return group[group[column] == aggregate_value]
    return group


def _filter_for_composites(df: pd.DataFrame) -> pd.DataFrame:
    """
    Restrict to appropriate rows for composite calculation.

    Rule:
    - For each country/year/indicator, if aggregate codes (BOTHSEX, ALLAREA,
      _T, etc.) exist, use only those.
    - If an indicator is only reported for a single category (e.g. FEMALE
      only for SH_STA_MORT), keep that category; do not drop it just because
      BOTHSEX/ALLAREA are absent.
    """
    groups = []
    for _, g in df.groupby(
        ["country_code", "country_name", "year", "series_code"],
        dropna=False,
    ):
        # Prefer BOTHSEX when present; otherwise keep MALE/FEMALE/etc.
        g = _prefer_aggregate_value(g, "sex", "BOTHSEX")
        # Prefer ALLAREA when present; otherwise keep URBAN/RURAL/etc.
        g = _prefer_aggregate_value(g, "location", "ALLAREA")
        # Prefer _T for quantile and education_level when present.
        g = _prefer_aggregate_value(g, "quantile", "_T")
        g = _prefer_aggregate_value(g, "education_level", "_T")
        # Age: if ALLAGE exists for this indicator, prefer it; otherwise keep
        # the age bands that are present (e.g., <5Y for child indicators).
        age_values = g["age"].dropna().unique()
        if "ALLAGE" in age_values:
            g = g[g["age"] == "ALLAGE"]
        groups.append(g)

    if not groups:
        return df.iloc[0:0]

    return pd.concat(groups, axis=0)


def compute_subsector_scores(scored_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute subsector-level scores via available-case indicator averaging.
    """
    df = _attach_hierarchy(scored_df)
    df = _filter_for_composites(df)

    group_cols = [
        "country_code",
        "country_name",
        "year",
        "series_code",
        "indicator_id",
        "domain_id",
        "sector_id",
        "subsector_id",
    ]

    # First aggregate to indicator level (in case there are multiple rows
    # per country/year/indicator after filtering).
    def _indicator_aggregate(g: pd.DataFrame) -> float:
        # Special-case 3.d.1 (SH_IHR_CAPS): weighted average by `class_code`.
        if g["series_code"].iloc[0] == "SH_IHR_CAPS":
            weights = get_ihr_component_weights(g["class_code"].tolist())
            if not weights:
                return _available_case_mean(g["score"])

            w = g["class_code"].astype(str).map(weights)
            # For any codes still missing (e.g., NaN class_code), default to equal
            # weight across the remaining rows in this group.
            missing_mask = w.isna()
            if missing_mask.any():
                remaining = 1.0 - float(w.dropna().sum())
                if remaining <= 0:
                    w = pd.Series(1.0, index=g.index)
                else:
                    w = w.where(~missing_mask, other=(remaining / missing_mask.sum()))

            valid = g["score"].notna() & w.notna()
            if not valid.any():
                return float("nan")
            return float((g.loc[valid, "score"] * w.loc[valid]).sum() / w.loc[valid].sum())

        return _available_case_mean(g["score"])

    indicator_means = (
        df.groupby(group_cols, dropna=False)
        .apply(_indicator_aggregate)
        .reset_index(name="score")
    )

    subsector_group_cols = [
        "country_code",
        "country_name",
        "year",
        "domain_id",
        "sector_id",
        "subsector_id",
    ]

    # Aggregate indicators to subsector using configurable weights.
    records = []
    for (country_code, country_name, year, domain_id, sector_id, subsector_id), group in indicator_means.groupby(
        subsector_group_cols,
        dropna=False,
    ):
        weights = SUBSECTOR_WEIGHTS.get(subsector_id, {})
        values = [
            (row["indicator_id"], row["score"])
            for _, row in group.iterrows()
        ]
        score = _weighted_mean(values, weights)
        records.append(
            {
                "country_code": country_code,
                "country_name": country_name,
                "year": year,
                "domain_id": domain_id,
                "sector_id": sector_id,
                "subsector_id": subsector_id,
                "subsector_score": score,
            }
        )

    return pd.DataFrame.from_records(records)


def _weighted_mean(
    values: Iterable[Tuple[str, float]],
    weights: Dict[str, float],
) -> float:
    num = 0.0
    den = 0.0
    for key, val in values:
        if pd.isna(val):
            continue
        w = weights.get(key)
        if w is None or w == 0:
            continue
        num += w * float(val)
        den += w
    if den == 0:
        return float("nan")
    return num / den


def compute_sector_scores(subsector_scores: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate subsector scores to sector level using configurable weights.
    """
    records = []
    for (country_code, country_name, year, domain_id, sector_id), group in subsector_scores.groupby(
        ["country_code", "country_name", "year", "domain_id", "sector_id"],
        dropna=False,
    ):
        weights = SECTOR_WEIGHTS.get(sector_id, {})
        values = [
            (row["subsector_id"], row["subsector_score"])
            for _, row in group.iterrows()
        ]
        score = _weighted_mean(values, weights)
        records.append(
            {
                "country_code": country_code,
                "country_name": country_name,
                "year": year,
                "domain_id": domain_id,
                "sector_id": sector_id,
                "sector_score": score,
            }
        )

    return pd.DataFrame.from_records(records)


def compute_domain_scores(sector_scores: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sector scores to domain level using configurable weights.
    """
    records = []
    for (country_code, country_name, year, domain_id), group in sector_scores.groupby(
        ["country_code", "country_name", "year", "domain_id"],
        dropna=False,
    ):
        weights = DOMAIN_WEIGHTS.get(str(domain_id), {})
        values = [
            (row["sector_id"], row["sector_score"])
            for _, row in group.iterrows()
        ]
        score = _weighted_mean(values, weights)
        records.append(
            {
                "country_code": country_code,
                "country_name": country_name,
                "year": year,
                "domain_id": domain_id,
                "domain_score": score,
            }
        )

    return pd.DataFrame.from_records(records)

