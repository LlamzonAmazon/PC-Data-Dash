"""
Dashboard Data Loader — reference implementation for Power BI data consumption.

This module loads the structured dashboard output from data/interim/validated/
exactly the way Power BI should consume it. It is the authoritative reference for:

  1. How to load and parse each validated CSV
  2. How indicators are organised (domain > sector > subsector > indicator)
  3. How to join tables — always on country_code (ISO-3), never country_name
  4. How to group countries by region (continent)
  5. How to compute region averages for comparative views

DATA SCHEMAS
------------
domainscores.csv:
    country_code, country_name, year, domain_id, domain_score, floored_to_zero

sectorscores.csv:
    country_code, country_name, year, sector_id, sector_score, floored_to_zero

subsectorscores.csv:
    country_code, country_name, year, subsector_id, subsector_score, floored_to_zero

Indicator_Scores_Full.csv:
    country_code, country_name, year, value, indicator, series_code,
    nature, reporting_type, age, sex, location, quantile, education_level,
    class_code, class_name, score, floored_to_zero

indicatorscores/indicator-*.csv:
    Same schema as Indicator_Scores_Full — one file per indicator_id.

HIERARCHY
---------
domain_id 1   "Domain 1: Impact"
  sector_id 1.1   "Healthcare"
    subsector_id 1.1.1  "Resilient primary healthcare systems"
    subsector_id 1.1.2  "Infectious disease control"
    ...
  sector_id 1.2   "Agriculture"
  sector_id 1.3   "Social Infrastructure"
  sector_id 1.5   "Additional Country Considerations"

POWER BI DEVELOPER NOTE
-----------------------
  - Always join tables on: country_code (ISO alpha-3, e.g. "AFG", "NGA")
  - For display, use: loader.get_canonical_name(country_code)
  - Never join on country_name — it differs across the three data sources.
  - The hierarchy IDs in the CSVs (1.1, 1.1.3, etc.) are defined in
    src/calculating/hierarchy.py and used here directly.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.calculating.hierarchy import INDICATORS, IndicatorMeta
from src.utils.helpers import project_root
from src.utils.country_names import (
    COUNTRY_NAMES,
    COUNTRY_REGIONS,
    REGION_NAMES,
    get_canonical_name,
    get_region,
    get_region_name,
)


# Human-readable names for hierarchy levels — derived from indicators.yaml
# and kept in sync with src/calculating/hierarchy.py

DOMAIN_NAMES: dict[str, str] = {
    "1": "Domain 1: Impact",
    "2": "Domain 2: Feasibility",
    "3": "Domain 3: Priority Alignment",
}

SECTOR_NAMES: dict[str, str] = {
    "1.1": "Healthcare",
    "1.2": "Agriculture",
    "1.3": "Social Infrastructure",
    "1.5": "Additional Country Considerations",
}

SUBSECTOR_NAMES: dict[str, str] = {
    "1.1.1": "Resilient primary healthcare (PHC) systems",
    "1.1.2": "Infectious disease control",
    "1.1.3": "Maternal, newborn, and child health",
    "1.1.4": "Nutrition",
    "1.1.5": "Reproductive health and family planning",
    "1.1.6": "Health risk reduction and management",
    "1.2.1": "Food security",
    "1.2.2": "Agricultural systems and value chain strengthening",
    "1.3.1": "Water, sanitation, and hygiene (WASH)",
    "1.3.2": "Off-grid power",
    "1.3.3": "Digital financial inclusion",
    "1.5.1": "Poverty",
}


class DashboardDataLoader:
    """
    Reference implementation: loads structured dashboard data the same way
    Power BI should consume it from Azure Blob.

    All public methods return plain pandas DataFrames with canonical
    country_code (ISO-3) as the join key.

    Usage:
        loader = DashboardDataLoader()
        domains = loader.load_domain_scores()
        sectors = loader.load_sector_scores()
        country_list = loader.get_country_list()
        hierarchy = loader.get_indicator_hierarchy()
    """

    def __init__(self, data_dir: Optional[Path] = None, config_path: Optional[Path] = None):
        """
        Args:
            data_dir: Path to the validated data directory. Defaults to
                      data/interim/validated/ relative to project root.
            config_path: Path to settings.yaml. Defaults to src/config/settings.yaml.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        root = project_root()

        if data_dir is not None:
            self.data_dir = Path(data_dir)
        else:
            config_path = config_path or root / "src" / "config" / "settings.yaml"
            try:
                cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                rel = cfg.get("paths", {}).get("data_interim_validated", "data/interim/validated/")
            except Exception:
                rel = "data/interim/validated/"
            self.data_dir = root / rel.rstrip("/")

        self.log.info("DashboardDataLoader initialised — data_dir: %s", self.data_dir)

        # Lazy-loaded caches
        self._domain_scores: Optional[pd.DataFrame] = None
        self._sector_scores: Optional[pd.DataFrame] = None
        self._subsector_scores: Optional[pd.DataFrame] = None
        self._indicator_scores: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # CSV Loading — one method per file (mirrors Power BI dataset tables)
    # ------------------------------------------------------------------

    def load_domain_scores(self) -> pd.DataFrame:
        """Load domainscores.csv.

        Columns: country_code, country_name, year, domain_id, domain_score, floored_to_zero

        Power BI use: top-level aggregated scores per country per year.
        Join key: country_code
        """
        if self._domain_scores is None:
            path = self.data_dir / "domainscores.csv"
            self._domain_scores = self._load_csv(path)
        return self._domain_scores.copy()

    def load_sector_scores(self) -> pd.DataFrame:
        """Load sectorscores.csv.

        Columns: country_code, country_name, year, sector_id, sector_score, floored_to_zero

        sector_id notation: "1.1", "1.2", "1.3", "1.5"
        Use get_sector_name(sector_id) for human-readable labels.
        Join key: country_code
        """
        if self._sector_scores is None:
            path = self.data_dir / "sectorscores.csv"
            self._sector_scores = self._load_csv(path)
        return self._sector_scores.copy()

    def load_subsector_scores(self) -> pd.DataFrame:
        """Load subsectorscores.csv.

        Columns: country_code, country_name, year, subsector_id, subsector_score, floored_to_zero

        subsector_id notation: "1.1.1", "1.1.2", ... "1.3.3", "1.5.1"
        Use get_subsector_name(subsector_id) for human-readable labels.
        Join key: country_code
        """
        if self._subsector_scores is None:
            path = self.data_dir / "subsectorscores.csv"
            self._subsector_scores = self._load_csv(path)
        return self._subsector_scores.copy()

    def load_indicator_scores(self) -> pd.DataFrame:
        """Load Indicator_Scores_Full.csv — all indicators for all countries.

        Columns: country_code, country_name, year, value, indicator, series_code,
                 nature, reporting_type, age, sex, location, quantile,
                 education_level, class_code, class_name, score, floored_to_zero

        For individual indicator views, prefer load_single_indicator() — it is
        faster for interactive use since the full file is ~100k rows.
        Join key: country_code
        """
        if self._indicator_scores is None:
            path = self.data_dir / "Indicator_Scores_Full.csv"
            self._indicator_scores = self._load_csv(path)
        return self._indicator_scores.copy()

    def load_single_indicator(self, indicator_id: str) -> pd.DataFrame:
        """Load a single per-indicator CSV from indicatorscores/.

        Args:
            indicator_id: Indicator code, e.g. "3.8.1" or "1.2.1"

        Returns:
            DataFrame with same schema as Indicator_Scores_Full for that indicator.
        """
        filename = "indicator-" + indicator_id.replace(".", "-") + ".csv"
        path = self.data_dir / "indicatorscores" / filename
        if not path.exists():
            raise FileNotFoundError(
                f"No per-indicator file found for '{indicator_id}' at {path}. "
                f"Available: {[f.name for f in (self.data_dir / 'indicatorscores').glob('*.csv')]}"
            )
        return self._load_csv(path)

    def load_all(self) -> dict[str, pd.DataFrame]:
        """Load all validated datasets into a dict.

        Returns:
            {
                "domain_scores":    DataFrame,
                "sector_scores":    DataFrame,
                "subsector_scores": DataFrame,
                "indicator_scores": DataFrame,
            }
        """
        return {
            "domain_scores": self.load_domain_scores(),
            "sector_scores": self.load_sector_scores(),
            "subsector_scores": self.load_subsector_scores(),
            "indicator_scores": self.load_indicator_scores(),
        }

    # ------------------------------------------------------------------
    # Indicator Hierarchy
    # ------------------------------------------------------------------

    def get_indicator_hierarchy(self) -> dict:
        """Return the full indicator hierarchy as a nested dict.

        Structure:
            {
                "1": {
                    "name": "Domain 1: Impact",
                    "sectors": {
                        "1.1": {
                            "name": "Healthcare",
                            "subsectors": {
                                "1.1.1": {
                                    "name": "Resilient primary healthcare (PHC) systems",
                                    "indicators": [
                                        {"indicator_id": "3.8.1", "series_code": "SH_ACS_UNHC_25",
                                         "name": "Universal health coverage ..."}
                                    ]
                                },
                                ...
                            }
                        },
                        ...
                    }
                }
            }

        This mirrors how the Power BI right-sidebar indicator list should
        be structured: domain -> sector -> subsector -> indicator.
        """
        hierarchy: dict = {}

        for meta in INDICATORS.values():
            d = meta.domain_id
            s = meta.sector_id
            ss = meta.subsector_id

            if d not in hierarchy:
                hierarchy[d] = {"name": DOMAIN_NAMES.get(d, f"Domain {d}"), "sectors": {}}

            sectors = hierarchy[d]["sectors"]
            if s not in sectors:
                sectors[s] = {"name": SECTOR_NAMES.get(s, f"Sector {s}"), "subsectors": {}}

            subsectors = sectors[s]["subsectors"]
            if ss not in subsectors:
                subsectors[ss] = {
                    "name": SUBSECTOR_NAMES.get(ss, f"Subsector {ss}"),
                    "indicators": [],
                }

            subsectors[ss]["indicators"].append({
                "indicator_id": meta.indicator_id,
                "series_code": meta.series_code,
                "name": meta.name,
            })

        return hierarchy

    def get_indicator_name(self, indicator_id: str) -> str:
        """Return the human-readable name for an indicator code."""
        for meta in INDICATORS.values():
            if meta.indicator_id == indicator_id:
                return meta.name
        return indicator_id

    def get_sector_name(self, sector_id: str) -> str:
        """Return the human-readable name for a sector_id (e.g. '1.1' -> 'Healthcare')."""
        return SECTOR_NAMES.get(sector_id, sector_id)

    def get_subsector_name(self, subsector_id: str) -> str:
        """Return the human-readable name for a subsector_id."""
        return SUBSECTOR_NAMES.get(subsector_id, subsector_id)

    def get_domain_name(self, domain_id: str) -> str:
        """Return the human-readable name for a domain_id (e.g. '1' -> 'Domain 1: Impact')."""
        return DOMAIN_NAMES.get(str(domain_id), f"Domain {domain_id}")

    def get_sector_list(self) -> list[tuple[str, str]]:
        """Return list of (sector_id, sector_name) tuples in hierarchy order."""
        return [(sid, name) for sid, name in sorted(SECTOR_NAMES.items())]

    def get_subsector_list(self, sector_id: str | None = None) -> list[tuple[str, str]]:
        """Return list of (subsector_id, subsector_name) tuples, optionally filtered."""
        items = sorted(SUBSECTOR_NAMES.items())
        if sector_id:
            items = [(k, v) for k, v in items if k.startswith(sector_id + ".")]
        return items

    def get_indicator_flat_list(self) -> list[tuple[str, str, str]]:
        """Return flat list of (indicator_id, series_code, name) for all indicators.

        Useful for building dropdown options in the notebook or Power BI slicer.
        Ordered by subsector hierarchy.
        """
        result = []
        seen = set()
        for meta in sorted(INDICATORS.values(), key=lambda m: (m.subsector_id, m.indicator_id)):
            if meta.indicator_id not in seen:
                result.append((meta.indicator_id, meta.series_code, meta.name))
                seen.add(meta.indicator_id)
        return result

    # ------------------------------------------------------------------
    # Region / Country Grouping
    # ------------------------------------------------------------------

    def get_canonical_name(self, country_code: str) -> str:
        """Return canonical display name for a country code."""
        return get_canonical_name(country_code)

    def get_region_for_country(self, country_code: str) -> str:
        """Return continent code (AF/AS/EU/NA/SA/OC) for an ISO-3 country code."""
        return get_region(country_code)

    def get_region_name(self, region_code: str) -> str:
        """Return full region name (e.g. 'AF' -> 'Africa')."""
        return get_region_name(region_code)

    def get_countries_in_region(self, region_code: str) -> list[str]:
        """Return all ISO-3 codes mapped to a given region."""
        return [code for code, r in COUNTRY_REGIONS.items() if r == region_code]

    def get_region_list(self) -> list[tuple[str, str]]:
        """Return list of (region_code, region_name) tuples."""
        return [(code, name) for code, name in sorted(REGION_NAMES.items())]

    def get_region_average(
        self,
        df: pd.DataFrame,
        region_code: str,
        score_col: str,
        group_by: list[str] | None = None,
    ) -> pd.DataFrame:
        """Compute mean score for all countries in a region.

        Args:
            df: DataFrame containing country_code and score_col columns.
            region_code: Continent code, e.g. "AF".
            score_col: Name of the score column to average.
            group_by: Additional columns to group by (e.g. ["year", "sector_id"]).
                      Defaults to ["year"] if present, otherwise no grouping.

        Returns:
            DataFrame with region average score. country_code is set to the
            region_code for easy comparison with individual-country DataFrames.
        """
        country_codes = self.get_countries_in_region(region_code)
        region_df = df[df["country_code"].isin(country_codes)].copy()

        if region_df.empty:
            self.log.warning("No data found for region %s", region_code)
            return region_df

        if group_by is None:
            present_cols = [c for c in ["year"] if c in region_df.columns]
            group_by = present_cols

        if group_by:
            agg = region_df.groupby(group_by, as_index=False)[score_col].mean()
        else:
            agg = pd.DataFrame({score_col: [region_df[score_col].mean()]})

        agg["country_code"] = region_code
        agg["country_name"] = get_region_name(region_code)
        return agg

    # ------------------------------------------------------------------
    # Convenience Filters
    # ------------------------------------------------------------------

    def get_latest_year(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter a DataFrame to only the most recent year per country.

        Args:
            df: DataFrame containing a 'year' column.

        Returns:
            DataFrame filtered to max year per country_code (or globally
            if country_code is not present).
        """
        if "country_code" in df.columns:
            idx = df.groupby("country_code")["year"].idxmax()
            return df.loc[idx].reset_index(drop=True)
        else:
            return df[df["year"] == df["year"].max()].copy()

    def filter_country(self, df: pd.DataFrame, country: str) -> pd.DataFrame:
        """Filter a DataFrame to rows for a single country.

        Args:
            country: ISO-3 code (e.g. "AFG") or canonical display name.

        Returns:
            Filtered DataFrame.
        """
        if len(country) == 3 and country.isupper():
            return df[df["country_code"] == country].copy()
        # Try matching canonical name
        code = next(
            (k for k, v in COUNTRY_NAMES.items() if v.lower() == country.lower()),
            None,
        )
        if code:
            return df[df["country_code"] == code].copy()
        # Fallback: match against country_name column (less reliable)
        if "country_name" in df.columns:
            return df[df["country_name"].str.lower() == country.lower()].copy()
        self.log.warning("Could not resolve country '%s' to a code", country)
        return df.iloc[0:0].copy()

    def filter_region(self, df: pd.DataFrame, region_code: str) -> pd.DataFrame:
        """Filter a DataFrame to all countries in a region.

        Args:
            region_code: Continent code, e.g. "AF".

        Returns:
            Filtered DataFrame.
        """
        country_codes = self.get_countries_in_region(region_code)
        return df[df["country_code"].isin(country_codes)].copy()

    def get_country_list(self) -> list[tuple[str, str]]:
        """Return list of (country_code, display_name) for all countries in domain scores.

        Sorted alphabetically by display name. Useful for building dropdown options.
        """
        df = self.load_domain_scores()
        codes = df["country_code"].unique()
        pairs = [(code, get_canonical_name(code)) for code in codes]
        return sorted(pairs, key=lambda x: x[1])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_csv(self, path: Path) -> pd.DataFrame:
        """Load a CSV with standard column typing."""
        if not path.exists():
            raise FileNotFoundError(
                f"Validated data file not found: {path}\n"
                f"Run the pipeline first to generate data/interim/validated/"
            )
        self.log.info("Loading %s", path.name)
        df = pd.read_csv(path, low_memory=False)
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        return df
