from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from .aggregate import (
    compute_domain_scores,
    compute_sector_scores,
    compute_subsector_scores,
    filter_for_composites,
    format_output_df,
)
from .factory import IndicatorScorerFactory
from .hierarchy import INDICATORS, SERIES_CODE_TO_FILENAME

# Excluded from unsdg/Indicator_Scores_Full.csv (non-UN-SDG sources).
UNSDG_MASTER_EXCLUDE = frozenset({"nd_vulnerability", "EN.POP.DNST", "GII_INDEX"})


def score_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    factory = IndicatorScorerFactory()
    scores = []

    for series_code, group in df.groupby("series_code", dropna=False):
        try:
            scorer = factory.for_series(series_code)
        except KeyError:
            scores.append(pd.Series(index=group.index, data=pd.NA, dtype="float"))
            continue

        scores.append(scorer.score(group))

    df["score"] = pd.concat(scores).sort_index()
    return df


def _save_csv(df: pd.DataFrame, path: Path, level: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    formatted = format_output_df(df, level=level)
    formatted.to_csv(path, index=False)


def write_indicator_files(scored_df: pd.DataFrame, validated_dir: Path) -> None:
    unsdg_dir = validated_dir / "unsdg" / "indicatorscores"

    for series_code, group in scored_df.groupby("series_code", dropna=False):
        filename = SERIES_CODE_TO_FILENAME.get(series_code)
        if not filename:
            continue

        if filename.startswith("ndgain/") or filename.startswith("worldbank/"):
            out_path = validated_dir / filename
        else:
            out_path = unsdg_dir / filename

        _save_csv(group, out_path, level="indicator")


def run_pipeline(
    interim_df: pd.DataFrame,
    validated_dir: Path,
) -> None:
    validated_dir.mkdir(parents=True, exist_ok=True)

    scored_df = score_indicators(interim_df)

    # Per-series files (full disaggregation preserved for deep-dive charts).
    write_indicator_files(scored_df, validated_dir)

    # UNSDG master: hierarchy-mapped UN SDG series only, aggregate rows only.
    unsdg_series = {k for k in INDICATORS if k not in UNSDG_MASTER_EXCLUDE}
    unsdg_scored = scored_df[scored_df["series_code"].isin(unsdg_series)]
    master = filter_for_composites(unsdg_scored)
    _save_csv(
        master,
        validated_dir / "unsdg" / "Indicator_Scores_Full.csv",
        level="indicator",
    )

    # Composites: all hierarchy-mapped indicators (includes ND-GAIN + World Bank).
    df_for_aggregation = scored_df[scored_df["series_code"].isin(INDICATORS.keys())]
    subsector_scores = compute_subsector_scores(df_for_aggregation)
    sector_scores = compute_sector_scores(subsector_scores)
    domain_scores = compute_domain_scores(sector_scores)

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

    _save_csv(subsector_scores, validated_dir / "subdomainscores.csv", level="subsector")
    _save_csv(sector_scores, validated_dir / "sectorscores.csv", level="sector")
    _save_csv(domain_scores, validated_dir / "pillarscores.csv", level="pillar")


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
    ndgain_rel = interim_data.get("ndgain")
    worldbank_rel = interim_data.get("worldbank")
    validated_rel = paths.get("data_interim_validated", "data/interim/validated/")

    missing = [
        key
        for key, value in {
            "unsdg": unsdg_rel,
            "ndgain": ndgain_rel,
            "worldbank": worldbank_rel,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(
            f"settings.yaml missing runtime.interim_data entries: {', '.join(missing)}"
        )

    unsdg_df = pd.read_csv(repo_root / unsdg_rel)
    ndgain_df = pd.read_csv(repo_root / ndgain_rel)
    worldbank_df = pd.read_csv(repo_root / worldbank_rel)
    worldbank_df = worldbank_df.rename(columns={"indicator-code": "series_code"})
    interim_df = pd.concat([unsdg_df, ndgain_df, worldbank_df], ignore_index=True)

    validated_dir = repo_root / validated_rel
    run_pipeline(interim_df, validated_dir)
