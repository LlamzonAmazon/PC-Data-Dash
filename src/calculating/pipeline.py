from __future__ import annotations

from pathlib import Path

import pandas as pd

from .aggregate import (
    compute_domain_scores,
    compute_sector_scores,
    compute_subsector_scores,
)
from .factory import IndicatorScorerFactory
from .hierarchy import INDICATORS, SERIES_CODE_TO_FILENAME


INDICATOR_BENCHMARKS = {
    "1.2.1": "SDG Target: 0.0% Poverty Elimination",
    "2.1.2": "IPC Risk Threshold: 20%",
    "2.2.1": "Low Level Threshold: 12%",
    "2.2.2": "Low Level Threshold: 2.5%",
    "2.2.3": "Low Level Threshold: 25%",
    "2.a.2": "Investment Target Index: 0.02",
    "3.1.1": "SDG Target: 70",
    "3.2.1": "SDG Target: 25",
    "3.3.2": "TB High-Incidence: 40",
    "3.3.3": "Malaria Transmission: 10",
    "3.7.1": "Global Satisfaction Mean: 11.5%",
    "3.7.2": "Elevated Birth Rate: 20",
    "3.9.2": "Global Average Mortality Rate",
    "7.1.1": "Global Lack of Access Mean: 9.8%",
    "7.1.2": "Universal Access Target: 100%",
    "7.2.1": "Renewable Target Share",
    "8.10.2": "Global Unbanked Mean: 45%",
    "3.d.1": "Absolute Capacity: 100% Index",
    "3.8.1": "Absolute Capacity: 100% Index",
    "6.1.1": "Universal Access Target: 100%",
    "6.2.1": "Universal Access Target: 100%",
    "GII": "Low Inequality Benchmark: 0.32 Index",
}


RATIO_THRESHOLD_GLOBAL_AVERAGES = {
    "SH_TBS_INCD": 40.0,
    "SH_STA_MALR": 10.0,
    "SH_STA_MORT": 70.0,
    "SH_DYN_MORT": 25.0,
    "SH_STA_STNT": 12.0,
    "SN_STA_OVWGT": 2.5,
    "SH_STA_ANEM": 25.0,
    "SP_DYN_ADKL": 20.0,
    "AG_PRD_FIESMS": 20.0,
    "SH_STA_WASHARI": 10.0,
    "SI_POV_NAHC": 10.0,
}


INVERSE_RATIO_GAP_BENCHMARKS = {
    "SH_FPL_MTMM": 11.5,
    "SH_H2O_SAFE": 27.1,
    "SH_SAN_SAFE": 43.0,
    "EG_ACS_ELEC": 9.8,
    "EG_EGY_CLEAN": 30.4,
    "EG_FEC_RNEW": 20.0,
    "FB_BNK_ACCSS": 45.0,
}


TARGET_THRESHOLDS = {
    "SI_POV_NAHC": 0.0,
    "AG_PRD_FIESMS": 20.0,
    "SH_STA_STNT": 12.0,
    "SN_STA_OVWGT": 2.5,
    "SH_STA_ANEM": 25.0,
    "DC_TOF_AGRL": 0.02,
    "SH_STA_MORT": 70.0,
    "SH_DYN_MORT": 25.0,
    "SH_TBS_INCD": 40.0,
    "SH_STA_MALR": 10.0,
    "SP_DYN_ADKL": 20.0,
    "SH_ACS_UNHC_25": 100.0,
    "SH_IHR_CAPS": 100.0,
    "SH_H2O_SAFE": 100.0,
    "SH_SAN_SAFE": 100.0,
    "EG_EGY_CLEAN": 100.0,
}


GLOBAL_MEAN_BENCHMARKS = {
    "SH_FPL_MTMM": 11.5,
    "EG_ACS_ELEC": 9.8,
    "FB_BNK_ACCSS": 45.0,
    "SH_STA_WASHARI": 10.0,
}


def _meets_target(row: pd.Series) -> bool:
    if pd.isna(row["value"]) or pd.isna(row["score"]) or row["score"] != 0.0:
        return False

    series_code = row.get("series_code")
    value = float(row["value"])

    # Higher-is-better targets.
    if series_code in {"SH_ACS_UNHC_25", "SH_IHR_CAPS", "SH_H2O_SAFE", "SH_SAN_SAFE", "EG_EGY_CLEAN"}:
        return value >= TARGET_THRESHOLDS[series_code]

    # DC_TOF_AGRL uses inverse ratio against a goal; higher value reaches goal.
    if series_code == "DC_TOF_AGRL":
        return value >= TARGET_THRESHOLDS[series_code]

    # Lower-is-better thresholds.
    if series_code in TARGET_THRESHOLDS:
        return value <= TARGET_THRESHOLDS[series_code]

    return False


def _meets_global_mean(row: pd.Series) -> bool:
    if pd.isna(row["value"]) or pd.isna(row["score"]) or row["score"] != 0.0:
        return False

    series_code = row.get("series_code")
    value = float(row["value"])

    if series_code in GLOBAL_MEAN_BENCHMARKS:
        if series_code in {"SH_FPL_MTMM", "EG_ACS_ELEC", "FB_BNK_ACCSS"}:
            country_gap = 100.0 - value
            return country_gap <= GLOBAL_MEAN_BENCHMARKS[series_code]
        return value <= GLOBAL_MEAN_BENCHMARKS[series_code]

    # Inverse-ratio family: compare country gap (100 - value) against
    # framework gap benchmark.
    if series_code in INVERSE_RATIO_GAP_BENCHMARKS:
        country_gap = 100.0 - value
        return country_gap <= INVERSE_RATIO_GAP_BENCHMARKS[series_code]

    if series_code in RATIO_THRESHOLD_GLOBAL_AVERAGES:
        return value <= RATIO_THRESHOLD_GLOBAL_AVERAGES[series_code]

    return False


def _assign_zero_meaning(df: pd.DataFrame) -> pd.Series:
    labels = pd.Series(pd.NA, index=df.index, dtype="object")

    value_missing = df["value"].isna()
    labels.loc[value_missing] = "Data Unavailable"

    true_zero = df["value"].eq(0.0) & ~value_missing
    labels.loc[true_zero] = "Elimination Reached"

    full_success = df["value"].eq(100.0) & ~value_missing
    labels.loc[full_success] = "Full Success Reached"

    candidate_zero = df["score"].eq(0.0) & ~value_missing & ~true_zero & ~full_success
    meets_target = df.apply(_meets_target, axis=1)
    meets_global = df.apply(_meets_global_mean, axis=1)

    labels.loc[candidate_zero & meets_target] = "Target Achieved"
    labels.loc[candidate_zero & ~meets_target & meets_global] = "Harmonized Success"
    labels.loc[candidate_zero & labels.isna()] = "Target Achieved"

    return labels


def score_indicators(interim_path: Path) -> pd.DataFrame:
    df = pd.read_csv(interim_path)

    factory = IndicatorScorerFactory()
    scores = []

    for series_code, group in df.groupby("series_code", dropna=False):
        try:
            scorer = factory.for_series(series_code)
        except KeyError:
            # Leave indicators without explicit scoring rules unchanged.
            scores.append(pd.Series(index=group.index, data=pd.NA, dtype="float"))
            continue

        scores.append(scorer.score(group))

    df["score"] = pd.concat(scores).sort_index()
    df["indicator_benchmark"] = df["indicator"].map(INDICATOR_BENCHMARKS)
    df["zero_meaning"] = _assign_zero_meaning(df)
    return df


def write_indicator_files(scored_df: pd.DataFrame, processed_dir: Path) -> None:
    indicators_dir = processed_dir / "indicatorscores"
    indicators_dir.mkdir(parents=True, exist_ok=True)

    for series_code, group in scored_df.groupby("series_code", dropna=False):
        filename = SERIES_CODE_TO_FILENAME.get(series_code)
        if not filename:
            continue
        out_path = indicators_dir / filename
        group.to_csv(out_path, index=False)


def run_pipeline(
    interim_csv: Path,
    processed_dir: Path,
) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)

    scored_df = score_indicators(interim_csv)

    # Phase 1 – full indicator scores with all disaggregations.
    scored_path = processed_dir / "Indicator_Scores_Full.csv"
    scored_df.to_csv(scored_path, index=False)

    # Per-indicator files.
    write_indicator_files(scored_df, processed_dir)

    # Phase 2 – composites using aggregate rows only.
    subsector_scores = compute_subsector_scores(scored_df)
    sector_scores = compute_sector_scores(subsector_scores)
    domain_scores = compute_domain_scores(sector_scores)

    # Sort outputs for deterministic, human-friendly ordering.
    # (We sort before dropping redundant columns so order is stable.)
    subsector_scores = subsector_scores.sort_values(
        by=["country", "year", "domain_id", "sector_id", "subsector_id"],
        kind="mergesort",
    )
    sector_scores = sector_scores.sort_values(
        by=["country", "year", "domain_id", "sector_id"],
        kind="mergesort",
    )
    domain_scores = domain_scores.sort_values(
        by=["country", "year", "domain_id"],
        kind="mergesort",
    )

    # Drop redundant hierarchy columns in outputs.
    # - `subsector_id` already encodes domain+sector.
    # - `sector_id` already encodes domain.
    subsector_scores = subsector_scores.drop(columns=["domain_id", "sector_id"], errors="ignore")
    sector_scores = sector_scores.drop(columns=["domain_id"], errors="ignore")

    subsector_scores.to_csv(processed_dir / "subsectorscores.csv", index=False)
    sector_scores.to_csv(processed_dir / "sectorscores.csv", index=False)
    domain_scores.to_csv(processed_dir / "domainscores.csv", index=False)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    interim_csv = repo_root / "data" / "interim" / "un_sdg_interim.csv"
    processed_dir = repo_root / "data" / "processed"
    run_pipeline(interim_csv, processed_dir)

