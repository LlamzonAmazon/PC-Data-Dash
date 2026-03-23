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
    # Flag rows where a valid value was pushed down to 0.0
    df["floored_to_zero"] = df["score"].eq(0.0) & df["value"].notna()
    return df


def write_indicator_files(scored_df: pd.DataFrame, validated_dir: Path) -> None:
    indicators_dir = validated_dir / "indicatorscores"
    indicators_dir.mkdir(parents=True, exist_ok=True)

    for series_code, group in scored_df.groupby("series_code", dropna=False):
        filename = SERIES_CODE_TO_FILENAME.get(series_code)
        if not filename:
            continue
        out_path = indicators_dir / filename
        group.to_csv(out_path, index=False)


def run_pipeline(
    interim_csv: Path,
    validated_dir: Path,
) -> None:
    validated_dir.mkdir(parents=True, exist_ok=True)

    scored_df = score_indicators(interim_csv)

    # Phase 1 – full indicator scores with all disaggregations.
    scored_path = validated_dir / "Indicator_Scores_Full.csv"
    scored_df.to_csv(scored_path, index=False)

    # Per-indicator files.
    write_indicator_files(scored_df, validated_dir)

    # Phase 2 – composites using aggregate rows only.
    subsector_scores = compute_subsector_scores(scored_df)
    sector_scores = compute_sector_scores(subsector_scores)
    domain_scores = compute_domain_scores(sector_scores)

    # Flag composites that land exactly at 0.0 (all contributing scores at floor).
    subsector_scores["floored_to_zero"] = subsector_scores["subsector_score"].eq(0.0)
    sector_scores["floored_to_zero"] = sector_scores["sector_score"].eq(0.0)
    domain_scores["floored_to_zero"] = domain_scores["domain_score"].eq(0.0)

    # Sort outputs for deterministic, human-friendly ordering.
    # (We sort before dropping redundant columns so order is stable.)
    subsector_scores = subsector_scores.sort_values(
        by=["country_name", "year", "domain_id", "sector_id", "subsector_id"],
        kind="mergesort",
    )
    sector_scores = sector_scores.sort_values(
        by=["country_name", "year", "domain_id", "sector_id"],
        kind="mergesort",
    )
    domain_scores = domain_scores.sort_values(
        by=["country_name", "year", "domain_id"],
        kind="mergesort",
    )

    # Drop redundant hierarchy columns in outputs.
    # - `subsector_id` already encodes domain+sector.
    # - `sector_id` already encodes domain.
    subsector_scores = subsector_scores.drop(columns=["domain_id", "sector_id"], errors="ignore")
    sector_scores = sector_scores.drop(columns=["domain_id"], errors="ignore")

    subsector_scores.to_csv(validated_dir / "subsectorscores.csv", index=False)
    sector_scores.to_csv(validated_dir / "sectorscores.csv", index=False)
    domain_scores.to_csv(validated_dir / "domainscores.csv", index=False)


if __name__ == "__main__":
    import yaml

    repo_root = Path(__file__).resolve().parents[2]
    settings_path = repo_root / "src" / "config" / "settings.yaml"
    with open(settings_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    paths = cfg.get("paths") or {}
    runtime = cfg.get("runtime") or {}
    interim_data = runtime.get("interim_data") or {}
    unsdg_rel = interim_data.get("unsdg")
    validated_rel = paths.get("data_interim_validated", "data/interim/validated/")
    if not unsdg_rel:
        raise ValueError("settings.yaml missing runtime.interim_data.unsdg")
    interim_csv = repo_root / unsdg_rel
    validated_dir = repo_root / validated_rel
    run_pipeline(interim_csv, validated_dir)

