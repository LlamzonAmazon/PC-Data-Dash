"""
Comprehensive CSV analysis utility.

Moved from check_csv.py (project root) — now parameterized so it can be
run against any interim CSV, not just un_sdg_interim.csv.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from src.utils.helpers import project_root


def run_csv_check(csv_path: str | Path | None = None) -> None:
    """
    Run a comprehensive analysis of an interim CSV file.

    Args:
        csv_path: Path to the CSV file. Defaults to data/interim/cleaned/un_sdg_interim.csv.
    """
    root = project_root()
    if csv_path is None:
        csv_path = root / "data" / "interim" / "cleaned" / "un_sdg_interim.csv"
    else:
        csv_path = Path(csv_path)

    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    print("=" * 80)
    print("COMPREHENSIVE CSV ANALYSIS")
    print(f"File: {csv_path}")
    print("=" * 80)
    print()

    # 1. BASIC STATS
    print("1. BASIC STATISTICS")
    print("-" * 80)
    print(f"Total rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")
    if "country_name" in df.columns:
        print(f"Unique countries: {df['country_name'].nunique()}")
    if "indicator" in df.columns:
        print(f"Unique indicators: {df['indicator'].nunique()}")
        print(f"Indicators: {sorted(df['indicator'].unique())}")
    if "year" in df.columns:
        print(f"Year range: {int(df['year'].min())} - {int(df['year'].max())}")
    print()

    # 2. DUPLICATE CHECK
    key_cols = [c for c in ["country_code", "year", "indicator", "series_code"] if c in df.columns]
    if key_cols:
        print("2. DUPLICATE ANALYSIS")
        print("-" * 80)
        dupes = df[df.duplicated(subset=key_cols, keep=False)].sort_values(key_cols)

        if len(dupes) > 0:
            print(f"FOUND {len(dupes)} DUPLICATE ROWS")
            print(f"   (same {'/'.join(key_cols)})")
            if "indicator" in dupes.columns:
                print("\nBreakdown by indicator:")
                dup_counts = dupes.groupby("indicator").size().sort_values(ascending=False)
                for ind, count in dup_counts.items():
                    print(f"   {ind}: {count} duplicate rows")
            print("\nSample duplicates (first 10):")
            sample_cols = key_cols + [c for c in ["value", "sex", "age", "location"] if c in df.columns]
            print(dupes[sample_cols].head(10).to_string())
        else:
            print("NO DUPLICATES FOUND")
        print()

    # 3. DATA QUALITY
    print("3. DATA QUALITY CHECKS")
    print("-" * 80)
    if "value" in df.columns:
        null_count = df["value"].isna().sum()
        print(f"Rows with null values: {null_count:,} ({null_count / len(df) * 100:.1f}%)")
        if "indicator" in df.columns:
            print("\nIndicators with null values:")
            null_by_ind = df.groupby("indicator")["value"].apply(lambda x: x.isna().sum())
            null_pct = df.groupby("indicator")["value"].apply(lambda x: x.isna().sum() / len(x) * 100)
            for ind in sorted(null_by_ind[null_by_ind > 0].index):
                print(f"   {ind}: {null_by_ind[ind]:,} nulls ({null_pct[ind]:.1f}%)")
    print()

    # 4. DIMENSION FIELDS
    dim_cols = ["sex", "age", "urbanisation", "location", "class_code"]
    present = [c for c in dim_cols if c in df.columns]
    if present:
        print("4. DIMENSION FIELDS")
        print("-" * 80)
        for col in present:
            pop = df[col].notna().sum()
            print(f"Rows with {col} populated: {pop:,} ({pop / len(df) * 100:.1f}%)")
        print()

    # 5. SUMMARY
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if key_cols:
        total_dupes = len(df[df.duplicated(subset=key_cols, keep=False)])
        if total_dupes == 0:
            print("NO DUPLICATES - CSV is clean!")
        else:
            print(f"{total_dupes} DUPLICATE ROWS FOUND")
    print(f"\nTotal rows: {len(df):,}")
    if key_cols:
        print(f"Unique ({'/'.join(key_cols)}) combinations: {df[key_cols].drop_duplicates().shape[0]:,}")


if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_csv_check(path_arg)
