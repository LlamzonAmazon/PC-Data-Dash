"""
Detect collision duplicates in the UN SDG interim CSV.

A collision duplicate is when every dimension is the same (year, indicator,
series_code, country_name, nature, reporting_type, age, sex, location, class_code,
class_name, and any other columns in the CSV) but the numeric 'value' differs.
So we use all columns except 'value' as the dimension key.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pandas as pd
import yaml

from src.pipeline.utils import project_root, setup_logger

logger = setup_logger("unsdg-duplicate-check")

VALUE_COL = "value"
SERIES_COL = "series_code"


def _load_settings() -> dict:
    """Load settings.yaml from project config."""
    root = project_root()
    path = root / "src" / "config" / "settings.yaml"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_unsdg_csv(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the UN SDG interim CSV. If csv_path is None, use path from settings.yaml
    (runtime.interim_data.unsdg).
    """
    if csv_path is not None:
        path = Path(csv_path)
    else:
        settings = _load_settings()
        rel = settings.get("runtime", {}).get("interim_data", {}).get("unsdg")
        if not rel:
            raise ValueError("settings.yaml has no runtime.interim_data.unsdg")
        path = project_root() / rel
    if not path.is_file():
        raise FileNotFoundError(f"UN SDG CSV not found: {path}")
    logger.info("Loading UN SDG CSV: %s", path)
    return pd.read_csv(path)


def get_configured_indicators() -> List[str]:
    """Return list of UN SDG indicator codes from settings (unsdg.indicators[].code)."""
    settings = _load_settings()
    indicators = settings.get("unsdg", {}).get("indicators", []) or []
    return [str(i["code"]) for i in indicators if i.get("code")]


def check_unsdg_collision_duplicates(
    df: pd.DataFrame,
    indicators: Optional[Sequence[str]] = None,
    tolerance: float = 0.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect collision duplicates: same on every dimension, different numeric value.

    Dimension key = all columns in df except 'value' (year, indicator, series_code,
    country_name, nature, reporting_type, age, sex, location, class_code, class_name,
    country_code, etc.). Collision = group with at least 2 non-null values and
    at least 2 distinct values whose range is > tolerance.

    Returns:
        detail_df: one row per collision group (dimension key + n_rows, value_min,
                   value_max, value_range, value_std, values_sample).
        summary_df: aggregated by (indicator, country_name): collision_group_count,
                    rows_impacted, max_value_range, mean_value_range.
    """
    if VALUE_COL not in df.columns:
        raise ValueError(f"DataFrame must have a '{VALUE_COL}' column")
    # Every column except value is a dimension; same dims + different value = collision
    dimension_cols = [c for c in df.columns if c != VALUE_COL]

    work = df.copy()
    if indicators is not None and "indicator" in work.columns:
        codes = {str(c) for c in indicators}
        work = work[work["indicator"].astype(str).isin(codes)]
    work[VALUE_COL] = pd.to_numeric(work[VALUE_COL], errors="coerce")
    if "year" in dimension_cols:
        work["year"] = pd.to_numeric(work["year"], errors="coerce").astype("Int64")

    grouped = work.groupby(dimension_cols, dropna=False)
    rows: List[dict] = []

    for keys, grp in grouped:
        vals = grp[VALUE_COL].dropna()
        n_rows = len(grp)
        n_uniq = vals.nunique()
        if len(vals) < 2 or n_uniq < 2:
            continue
        v_min = float(vals.min())
        v_max = float(vals.max())
        rng = v_max - v_min
        if rng <= tolerance:
            continue
        v_std = float(vals.std(ddof=0)) if len(vals) > 1 else 0.0
        sample = sorted(vals.unique())[:5]
        row = dict(zip(dimension_cols, keys))
        row["n_rows"] = n_rows
        row["n_non_null"] = int(len(vals))
        row["n_unique_values"] = int(n_uniq)
        row["value_min"] = v_min
        row["value_max"] = v_max
        row["value_range"] = rng
        row["value_std"] = v_std
        row["values_sample"] = [float(x) for x in sample]
        rows.append(row)

    if not rows:
        detail_df = pd.DataFrame(
            columns=dimension_cols
            + [
                "n_rows",
                "n_non_null",
                "n_unique_values",
                "value_min",
                "value_max",
                "value_range",
                "value_std",
                "values_sample",
            ]
        )
        summary_df = pd.DataFrame(
            columns=[
                "indicator",
                "country_name",
                "collision_group_count",
                "rows_impacted",
                "max_value_range",
                "mean_value_range",
            ]
        )
        return detail_df, summary_df

    detail_df = pd.DataFrame(rows)
    summary_df = (
        detail_df.groupby(["indicator", "country_name"], as_index=False)
        .agg(
            collision_group_count=("indicator", "size"),
            rows_impacted=("n_rows", "sum"),
            max_value_range=("value_range", "max"),
            mean_value_range=("value_range", "mean"),
        )
        .sort_values(["collision_group_count", "rows_impacted"], ascending=[False, False])
        .reset_index(drop=True)
    )
    return detail_df, summary_df


def run_unsdg_duplicate_check(
    csv_path: Optional[Path] = None,
    indicators: Optional[Sequence[str]] = None,
    tolerance: float = 0.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load UN SDG CSV, run collision check, print summary by indicator and series_code.

    If indicators is None, uses configured unsdg.indicators codes.
    Returns (detail_df, summary_df) from check_unsdg_collision_duplicates.
    """
    df = load_unsdg_csv(csv_path)
    if indicators is None:
        indicators = get_configured_indicators()

    logger.info("Running UN SDG collision-duplicate check...")
    detail_df, summary_df = check_unsdg_collision_duplicates(
        df, indicators=indicators, tolerance=tolerance
    )

    total_groups = len(detail_df)
    total_rows = int(detail_df["n_rows"].sum()) if not detail_df.empty else 0

    stats_cols = {"n_rows", "n_non_null", "n_unique_values", "value_min", "value_max", "value_range", "value_std", "values_sample"}
    dimension_cols_used = [c for c in detail_df.columns if c not in stats_cols]
    logger.info("=== UN SDG Collision-Duplicate Summary ===")
    logger.info("Total collision groups: %s", total_groups)
    logger.info("Total rows impacted:    %s", total_rows)
    logger.info(
        "Dimensions used (all columns except value): %s",
        ", ".join(dimension_cols_used),
    )

    if detail_df.empty:
        logger.info("No collision duplicates detected.")
        return detail_df, summary_df

    # Attribute colliding rows to indicator + series_code using original df
    if SERIES_COL not in df.columns:
        logger.info("'series_code' not in CSV; cannot report per-series_code.")
        return detail_df, summary_df

    df_work = df.copy()
    df_work["year"] = pd.to_numeric(df_work["year"], errors="coerce").astype("Int64")
    df_work[VALUE_COL] = pd.to_numeric(df_work[VALUE_COL], errors="coerce")
    collision_keys = detail_df[dimension_cols_used].drop_duplicates().copy()
    # Align dtypes so merge works (e.g. class_code/class_name can be object vs float)
    for col in dimension_cols_used:
        if col == "year":
            continue
        df_work[col] = df_work[col].astype(str).replace({"nan": "", "<NA>": ""})
        collision_keys[col] = collision_keys[col].astype(str).replace({"nan": "", "<NA>": ""})
    colliding = df_work.merge(collision_keys, on=dimension_cols_used, how="inner")
    by_series = (
        colliding.groupby(["indicator", SERIES_COL], as_index=False)
        .agg(
            countries_affected=("country_name", "nunique"),
            rows_in_collisions=("indicator", "size"),
        )
    )
    combo_count = (
        colliding[dimension_cols_used]
        .drop_duplicates()
        .groupby(["indicator", SERIES_COL])
        .size()
        .reset_index(name="dimension_combo_count")
    )
    by_series = by_series.merge(combo_count, on=["indicator", SERIES_COL], how="left")
    by_series["mean_rows_per_country"] = (
        by_series["rows_in_collisions"] / by_series["countries_affected"].replace(0, pd.NA)
    )
    by_series = by_series.sort_values(
        ["rows_in_collisions", "countries_affected"], ascending=[False, False]
    ).reset_index(drop=True)

    logger.info("")
    logger.info("Indicator + series_code involved in collision duplicates:")
    logger.info(by_series.to_string(index=False))

    return detail_df, summary_df


if __name__ == "__main__":
    run_unsdg_duplicate_check()
