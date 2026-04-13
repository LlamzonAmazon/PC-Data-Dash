"""
Dashboard Plotter — local simulation of the Power BI dashboard.

Two mode-specific plotter classes that mirror the two dashboard modes:

  HeatmapModePlotter   — global views: select one indicator, see all countries
  CountryModePlotter   — country views: select a country, see all its indicators;
                          also handles 2-country and region comparison

Both classes take a DashboardDataLoader as their data source, keeping all data
access consistent. Plots are saved to data/plots/dashboard/ and also returned
as matplotlib Figure objects for inline display in the Jupyter notebook.

USAGE (standalone):
    from src.plotting.dashboard_data import DashboardDataLoader
    from src.plotting.dashboard_plotter import HeatmapModePlotter, CountryModePlotter

    loader = DashboardDataLoader()
    heatmap = HeatmapModePlotter(loader)
    country = CountryModePlotter(loader)

    fig = heatmap.plot_indicator_heatmap("3.8.1")
    fig = country.plot_country_profile("AFG")
    fig = country.plot_compare_countries("AFG", "ETH", indicator_id="3.8.1")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

from src.plotting.dashboard_data import DashboardDataLoader, SECTOR_NAMES, SUBSECTOR_NAMES
from src.utils.helpers import ensure_dir
from src.utils.country_names import get_canonical_name, get_region_name, REGION_NAMES

matplotlib.rcParams["figure.dpi"] = 120
sns.set_theme(style="whitegrid", palette="muted", font_scale=0.9)

_SCORE_CMAP = "RdYlGn"  # red = high vulnerability (low score), green = low vulnerability
_PLOT_BASE = "data/plots/dashboard"


def _score_color(score: float) -> str:
    """Return a hex color from the RdYlGn colormap for a 0-100 score."""
    cmap = plt.cm.get_cmap(_SCORE_CMAP)
    return matplotlib.colors.to_hex(cmap(score / 100.0))


class HeatmapModePlotter:
    """
    Heatmap Mode — mirrors the Power BI globe view where one indicator is selected
    and countries are colored by their score.

    In the local module this is implemented as:
      - Seaborn heatmap: countries (rows) x years (columns), colored 0-100
      - Region-aggregated version: continent averages instead of individual countries
      - Score distribution histogram
    """

    def __init__(self, loader: DashboardDataLoader):
        self.loader = loader
        self.log = logging.getLogger(self.__class__.__name__)
        self._out_dir = loader.data_dir.parent.parent.parent / _PLOT_BASE / "heatmap"

    def plot_indicator_heatmap(
        self,
        indicator_id: str,
        year: Optional[int] = None,
        save: bool = True,
    ) -> plt.Figure:
        """
        Heatmap of country scores for one indicator across years.

        Countries are grouped by region (rows sorted AF -> AS -> EU -> NA -> SA -> OC).
        When year is specified, shows a ranked horizontal bar chart for that year only.

        Args:
            indicator_id: e.g. "3.8.1"
            year: If given, plot single-year ranking bar chart; otherwise all years.
            save: Whether to save the figure to disk.

        Returns:
            matplotlib Figure
        """
        df = self.loader.load_single_indicator(indicator_id)
        ind_name = self.loader.get_indicator_name(indicator_id)

        # Use latest available score per country-year (collapse any dimension splits)
        df = df.dropna(subset=["score"])
        df = df.groupby(["country_code", "year"], as_index=False)["score"].mean()

        if year is not None:
            return self._plot_single_year_ranking(df, indicator_id, ind_name, year, save)

        # Build pivot: country x year
        pivot = df.pivot_table(index="country_code", columns="year", values="score")
        pivot.index = [get_canonical_name(c) for c in pivot.index]

        # Sort by region then country name
        region_order = list(REGION_NAMES.keys())
        region_map = {get_canonical_name(c): get_region_name(get_region_name(r))
                      for c, r in {}.items()}

        code_to_region = {get_canonical_name(c): rcode
                         for c, rcode in self.loader.loader.COUNTRY_REGIONS.items()
                         if get_canonical_name(c) in pivot.index} if hasattr(self.loader, 'loader') else {}

        # Simple sort by region code then name
        def _sort_key(name):
            code = next((k for k, v in __import__('src.utils.country_names',
                         fromlist=['COUNTRY_NAMES']).COUNTRY_NAMES.items() if v == name), "ZZZ")
            region = self.loader.get_region_for_country(code)
            return (region_order.index(region) if region in region_order else 99, name)

        sorted_countries = sorted(pivot.index.tolist(), key=_sort_key)
        pivot = pivot.loc[sorted_countries]

        n_countries = len(pivot)
        fig_height = max(8, n_countries * 0.22)
        fig, ax = plt.subplots(figsize=(max(12, len(pivot.columns) * 0.6), fig_height))

        sns.heatmap(
            pivot,
            ax=ax,
            cmap=_SCORE_CMAP,
            vmin=0,
            vmax=100,
            linewidths=0.3,
            linecolor="white",
            cbar_kws={"label": "Score (0-100)", "shrink": 0.6},
            annot=False,
        )
        ax.set_title(f"{indicator_id} — {ind_name}\nAll Countries, All Years", fontsize=13, pad=12)
        ax.set_xlabel("Year")
        ax.set_ylabel("")
        ax.tick_params(axis="y", labelsize=7)
        plt.tight_layout()

        if save:
            path = self._out_dir / f"indicator-{indicator_id.replace('.', '-')}_all_years.png"
            ensure_dir(self._out_dir)
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def _plot_single_year_ranking(
        self,
        df: pd.DataFrame,
        indicator_id: str,
        ind_name: str,
        year: int,
        save: bool,
    ) -> plt.Figure:
        """Horizontal bar chart ranking all countries for a single year."""
        year_df = df[df["year"] == year].copy()
        if year_df.empty:
            available = sorted(df["year"].unique())
            raise ValueError(f"No data for year {year}. Available years: {available}")

        year_df["display_name"] = year_df["country_code"].apply(get_canonical_name)
        year_df["region"] = year_df["country_code"].apply(self.loader.get_region_for_country)
        year_df = year_df.sort_values("score", ascending=True)

        region_palette = {
            "AF": "#E57373", "AS": "#FFB74D", "EU": "#64B5F6",
            "NA": "#81C784", "SA": "#CE93D8", "OC": "#4DB6AC",
        }
        colors = year_df["region"].map(region_palette).fillna("#BDBDBD")

        n = len(year_df)
        fig, ax = plt.subplots(figsize=(10, max(8, n * 0.22)))
        bars = ax.barh(year_df["display_name"], year_df["score"], color=colors, height=0.7)
        ax.set_xlim(0, 105)
        ax.set_xlabel("Score (0 = most vulnerable, 100 = least vulnerable)")
        ax.set_title(f"{indicator_id} — {ind_name}\nCountry Rankings, {year}", fontsize=12, pad=10)
        ax.axvline(50, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

        legend_handles = [
            mpatches.Patch(color=c, label=get_region_name(r))
            for r, c in region_palette.items()
        ]
        ax.legend(handles=legend_handles, loc="lower right", fontsize=8, title="Region")
        plt.tight_layout()

        if save:
            path = self._out_dir / f"indicator-{indicator_id.replace('.', '-')}_{year}_ranking.png"
            ensure_dir(self._out_dir)
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def plot_indicator_heatmap_by_region(
        self,
        indicator_id: str,
        year: Optional[int] = None,
        save: bool = True,
    ) -> plt.Figure:
        """
        Heatmap using region (continent) averages rather than individual countries.

        Rows: AF, AS, EU, NA, SA, OC
        Columns: years (or single year bar chart when year is specified)

        Args:
            indicator_id: e.g. "3.8.1"
            year: If specified, show single-year grouped bar; otherwise heatmap.
            save: Whether to save the figure.

        Returns:
            matplotlib Figure
        """
        df = self.loader.load_single_indicator(indicator_id)
        ind_name = self.loader.get_indicator_name(indicator_id)
        df = df.dropna(subset=["score"])
        df = df.groupby(["country_code", "year"], as_index=False)["score"].mean()
        df["region"] = df["country_code"].apply(self.loader.get_region_for_country)
        region_df = df.groupby(["region", "year"], as_index=False)["score"].mean()
        region_df = region_df[region_df["region"].isin(REGION_NAMES.keys())]
        region_df["region_name"] = region_df["region"].apply(get_region_name)

        if year is not None:
            yd = region_df[region_df["year"] == year].sort_values("score")
            fig, ax = plt.subplots(figsize=(8, 4))
            colors = [_score_color(s) for s in yd["score"]]
            ax.barh(yd["region_name"], yd["score"], color=colors)
            ax.set_xlim(0, 105)
            ax.set_xlabel("Score (0-100)")
            ax.set_title(f"{indicator_id} — {ind_name}\nRegion Averages, {year}", fontsize=12)
            ax.axvline(50, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
            plt.tight_layout()
        else:
            pivot = region_df.pivot_table(index="region_name", columns="year", values="score")
            fig, ax = plt.subplots(figsize=(max(10, len(pivot.columns) * 0.7), 5))
            sns.heatmap(
                pivot, ax=ax, cmap=_SCORE_CMAP, vmin=0, vmax=100,
                annot=True, fmt=".0f", linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Score (0-100)"},
            )
            ax.set_title(f"{indicator_id} — {ind_name}\nRegion Averages, All Years", fontsize=12)
            ax.set_xlabel("Year")
            ax.set_ylabel("")
            plt.tight_layout()

        if save:
            suffix = f"_{year}" if year else "_all_years"
            path = self._out_dir / f"indicator-{indicator_id.replace('.', '-')}{suffix}_by_region.png"
            ensure_dir(self._out_dir)
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def plot_score_distribution(
        self,
        indicator_id: str,
        year: Optional[int] = None,
        save: bool = True,
    ) -> plt.Figure:
        """
        Histogram + KDE of score distribution across all countries for one indicator.

        Shows spread and skew — helps assess how differentiated the indicator is.

        Args:
            indicator_id: e.g. "3.8.1"
            year: Filter to a specific year; defaults to latest available.
            save: Whether to save the figure.

        Returns:
            matplotlib Figure
        """
        df = self.loader.load_single_indicator(indicator_id)
        ind_name = self.loader.get_indicator_name(indicator_id)
        df = df.dropna(subset=["score"])
        df = df.groupby(["country_code", "year"], as_index=False)["score"].mean()

        if year is None:
            df = self.loader.get_latest_year(df)
            year_label = f"Latest year ({df['year'].max()})"
        else:
            df = df[df["year"] == year]
            year_label = str(year)

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(df["score"], bins=20, kde=True, ax=ax, color="#5C6BC0", alpha=0.7)
        ax.axvline(df["score"].median(), color="#E53935", linestyle="--",
                   label=f"Median: {df['score'].median():.1f}")
        ax.axvline(df["score"].mean(), color="#FB8C00", linestyle=":",
                   label=f"Mean: {df['score'].mean():.1f}")
        ax.set_xlabel("Score (0-100)")
        ax.set_ylabel("Number of Countries")
        ax.set_title(
            f"{indicator_id} — {ind_name}\nScore Distribution, {year_label}", fontsize=12
        )
        ax.legend(fontsize=9)
        plt.tight_layout()

        if save:
            path = self._out_dir / f"distribution_{indicator_id.replace('.', '-')}.png"
            ensure_dir(self._out_dir)
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def generate_indicator_selector_list(self) -> str:
        """
        Return the hierarchical indicator list as a formatted string.

        Mirrors how the Power BI right sidebar should present the indicator
        selector list in Heatmap Mode: domain > sector > subsector > indicator.
        """
        hierarchy = self.loader.get_indicator_hierarchy()
        lines = []
        for domain_id, domain in sorted(hierarchy.items()):
            lines.append(f"\n=== {domain['name']} ===")
            for sector_id, sector in sorted(domain["sectors"].items()):
                lines.append(f"\n  {sector_id}  {sector['name']}")
                for sub_id, sub in sorted(sector["subsectors"].items()):
                    lines.append(f"    {sub_id}  {sub['name']}")
                    for ind in sub["indicators"]:
                        lines.append(f"       {ind['indicator_id']}  {ind['name']}")
        result = "\n".join(lines)
        print(result)
        return result


class CountryModePlotter:
    """
    Country Selector Mode — mirrors the Power BI view when a user clicks a country
    on the globe and the right sidebar shows that country's indicator data.

    Also handles the comparative views the client requested:
      - Two countries side by side
      - Two regions side by side
      - One country vs its region average
    """

    def __init__(self, loader: DashboardDataLoader):
        self.loader = loader
        self.log = logging.getLogger(self.__class__.__name__)
        self._out_dir = loader.data_dir.parent.parent.parent / _PLOT_BASE / "country"

    def plot_country_profile(
        self,
        country: str,
        year: Optional[int] = None,
        save: bool = True,
    ) -> plt.Figure:
        """
        Full country profile — one panel per sector showing all indicator scores.

        This is the core "right sidebar" view in Country Selector Mode.
        Indicators are grouped by sector and subsector following the hierarchy
        in indicators.yaml / src/calculating/hierarchy.py.

        Args:
            country: ISO-3 code (e.g. "AFG") or canonical name (e.g. "Afghanistan").
            year: Year to display. Defaults to most recent available year.
            save: Whether to save the figure.

        Returns:
            matplotlib Figure with one subplot per sector.
        """
        ind_df = self.loader.load_indicator_scores()
        country_code = self._resolve_country(country)
        display_name = get_canonical_name(country_code)

        df = self.loader.filter_country(ind_df, country_code)
        df = df.dropna(subset=["score"])
        df = df.groupby(["indicator", "year"], as_index=False)["score"].mean()

        if year is None:
            year = int(df["year"].max())
        df = df[df["year"] == year]

        hierarchy = self.loader.get_indicator_hierarchy()
        sectors = sorted(hierarchy.get("1", {}).get("sectors", {}).items())

        n_sectors = len(sectors)
        if n_sectors == 0:
            raise ValueError("No sectors found in hierarchy")

        fig, axes = plt.subplots(1, n_sectors, figsize=(6 * n_sectors, 9))
        if n_sectors == 1:
            axes = [axes]

        fig.suptitle(
            f"{display_name} — Indicator Profile, {year}",
            fontsize=14, fontweight="bold", y=1.01
        )

        for ax, (sector_id, sector) in zip(axes, sectors):
            self._draw_sector_bars(ax, df, sector_id, sector, display_name, year)

        plt.tight_layout()

        if save:
            out_dir = self._out_dir / display_name.replace(" ", "_")
            ensure_dir(out_dir)
            path = out_dir / f"profile_{year}.png"
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def _draw_sector_bars(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        sector_id: str,
        sector: dict,
        display_name: str,
        year: int,
    ) -> None:
        """Draw horizontal bars for all indicators in a sector."""
        rows = []
        for sub_id, sub in sorted(sector["subsectors"].items()):
            for ind in sub["indicators"]:
                ind_id = ind["indicator_id"]
                match = df[df["indicator"] == ind_id]
                score = float(match["score"].iloc[0]) if not match.empty else np.nan
                rows.append({
                    "label": f"{ind_id}\n{ind['name'][:35]}",
                    "score": score,
                    "subsector": sub["name"],
                })

        if not rows:
            ax.set_visible(False)
            return

        labels = [r["label"] for r in rows]
        scores = [r["score"] for r in rows]
        colors = [_score_color(s) if not np.isnan(s) else "#BDBDBD" for s in scores]
        display_scores = [s if not np.isnan(s) else 0 for s in scores]

        y_pos = range(len(labels))
        ax.barh(list(y_pos), display_scores, color=colors, height=0.6)
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlim(0, 105)
        ax.set_xlabel("Score (0-100)", fontsize=8)
        ax.set_title(f"{sector_id} {sector['name']}", fontsize=9, fontweight="bold")
        ax.axvline(50, color="gray", linestyle="--", linewidth=0.7, alpha=0.5)

        for i, (s, label) in enumerate(zip(scores, labels)):
            if not np.isnan(s):
                ax.text(s + 1, i, f"{s:.0f}", va="center", fontsize=7)
            else:
                ax.text(2, i, "N/A", va="center", fontsize=7, color="#999")

    def plot_country_sector_detail(
        self,
        country: str,
        sector_id: str,
        year: Optional[int] = None,
        save: bool = True,
    ) -> plt.Figure:
        """
        Drill-down view: subsector and indicator scores for one sector.

        Shows both the aggregated subsector score and the individual indicator
        scores that compose it. Mirrors "click a sector in the sidebar to expand".

        Args:
            country: ISO-3 code or canonical name.
            sector_id: e.g. "1.1" for Healthcare.
            year: Year to display. Defaults to most recent.
            save: Whether to save the figure.

        Returns:
            matplotlib Figure.
        """
        country_code = self._resolve_country(country)
        display_name = get_canonical_name(country_code)
        sector_name = self.loader.get_sector_name(sector_id)

        # Load subsector scores
        sub_df = self.loader.load_subsector_scores()
        sub_df = self.loader.filter_country(sub_df, country_code)
        sub_df = sub_df[sub_df["subsector_id"].str.startswith(sector_id + ".")]
        sub_df = sub_df.dropna(subset=["subsector_score"])

        # Load indicator scores
        ind_df = self.loader.load_indicator_scores()
        ind_df = self.loader.filter_country(ind_df, country_code)
        ind_df = ind_df.dropna(subset=["score"])
        ind_df = ind_df.groupby(["indicator", "year"], as_index=False)["score"].mean()

        if year is None:
            year = int(sub_df["year"].max()) if not sub_df.empty else int(ind_df["year"].max())

        sub_year = sub_df[sub_df["year"] == year]
        ind_year = ind_df[ind_df["year"] == year]

        hierarchy = self.loader.get_indicator_hierarchy()
        sector = hierarchy.get("1", {}).get("sectors", {}).get(sector_id, {})
        subsectors = sorted(sector.get("subsectors", {}).items())

        fig, ax = plt.subplots(figsize=(10, max(6, len(subsectors) * 1.8)))
        y_ticks = []
        y_labels = []
        y_pos = 0

        for sub_id, sub in subsectors:
            sub_match = sub_year[sub_year["subsector_id"] == sub_id]
            sub_score = float(sub_match["subsector_score"].iloc[0]) if not sub_match.empty else np.nan

            # Subsector label row
            ax.barh(
                y_pos,
                sub_score if not np.isnan(sub_score) else 0,
                color=_score_color(sub_score) if not np.isnan(sub_score) else "#BDBDBD",
                height=0.5,
                alpha=0.9,
            )
            y_ticks.append(y_pos)
            y_labels.append(f"[SUBSECTOR] {sub['name']}")
            if not np.isnan(sub_score):
                ax.text(sub_score + 1, y_pos, f"{sub_score:.0f}", va="center", fontsize=8, fontweight="bold")
            y_pos -= 0.7

            # Individual indicators in this subsector
            for ind in sub["indicators"]:
                ind_match = ind_year[ind_year["indicator"] == ind["indicator_id"]]
                ind_score = float(ind_match["score"].iloc[0]) if not ind_match.empty else np.nan

                ax.barh(
                    y_pos,
                    ind_score if not np.isnan(ind_score) else 0,
                    color=_score_color(ind_score) if not np.isnan(ind_score) else "#E0E0E0",
                    height=0.4,
                    alpha=0.75,
                )
                y_ticks.append(y_pos)
                y_labels.append(f"  {ind['indicator_id']} {ind['name'][:40]}")
                if not np.isnan(ind_score):
                    ax.text(ind_score + 1, y_pos, f"{ind_score:.0f}", va="center", fontsize=7)
                else:
                    ax.text(2, y_pos, "N/A", va="center", fontsize=7, color="#999")
                y_pos -= 0.6

            y_pos -= 0.4  # gap between subsectors

        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels, fontsize=7.5)
        ax.set_xlim(0, 110)
        ax.set_xlabel("Score (0-100)")
        ax.axvline(50, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.set_title(
            f"{display_name} — {sector_id} {sector_name}\nSubsector + Indicator Detail, {year}",
            fontsize=12, fontweight="bold"
        )
        plt.tight_layout()

        if save:
            out_dir = self._out_dir / display_name.replace(" ", "_")
            ensure_dir(out_dir)
            sector_slug = sector_id.replace(".", "-") + "_" + sector_name.replace(" ", "_").replace("/", "")
            path = out_dir / f"sector_{sector_slug}_{year}.png"
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def plot_country_trend(
        self,
        country: str,
        indicator_id: str,
        save: bool = True,
    ) -> plt.Figure:
        """
        Time series of one indicator score over all available years for one country.

        This is the plot shown when a user clicks a specific indicator in the
        right sidebar — shows whether the country is improving or declining.

        Args:
            country: ISO-3 code or canonical name.
            indicator_id: e.g. "3.8.1"
            save: Whether to save the figure.

        Returns:
            matplotlib Figure.
        """
        country_code = self._resolve_country(country)
        display_name = get_canonical_name(country_code)
        ind_name = self.loader.get_indicator_name(indicator_id)

        df = self.loader.load_single_indicator(indicator_id)
        df = self.loader.filter_country(df, country_code)
        df = df.dropna(subset=["score"])
        df = df.groupby("year", as_index=False)["score"].mean()
        df = df.sort_values("year")

        if df.empty:
            raise ValueError(f"No score data for {display_name} / {indicator_id}")

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["year"].astype(int), df["score"], marker="o", linewidth=2,
                color="#5C6BC0", markersize=6, label=display_name)
        ax.fill_between(df["year"].astype(int), df["score"], alpha=0.1, color="#5C6BC0")
        ax.set_ylim(0, 105)
        ax.set_xlim(df["year"].min() - 0.5, df["year"].max() + 0.5)
        ax.axhline(50, color="gray", linestyle="--", linewidth=0.8, alpha=0.6, label="Score = 50")
        ax.set_xlabel("Year")
        ax.set_ylabel("Score (0-100)")
        ax.set_title(
            f"{display_name} — {indicator_id} {ind_name}\nScore Over Time",
            fontsize=12, fontweight="bold"
        )
        ax.legend(fontsize=9)
        plt.tight_layout()

        if save:
            out_dir = self._out_dir / display_name.replace(" ", "_")
            ensure_dir(out_dir)
            path = out_dir / f"trend_{indicator_id.replace('.', '-')}.png"
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def plot_compare_countries(
        self,
        country_a: str,
        country_b: str,
        indicator_id: Optional[str] = None,
        sector_id: Optional[str] = None,
        year: Optional[int] = None,
        save: bool = True,
    ) -> plt.Figure:
        """
        Side-by-side comparison of two countries.

        - If indicator_id is given: overlaid time series for both countries.
        - If sector_id is given: grouped bar chart of all indicators in that sector.
        - If both given, indicator_id takes precedence.

        This is the primary comparative view the client requested.

        Args:
            country_a: First country ISO-3 or name.
            country_b: Second country ISO-3 or name.
            indicator_id: Compare on a specific indicator (time series).
            sector_id: Compare on all indicators in a sector (bar chart, uses year).
            year: Year for sector comparison. Defaults to most recent.
            save: Whether to save the figure.

        Returns:
            matplotlib Figure.
        """
        code_a = self._resolve_country(country_a)
        code_b = self._resolve_country(country_b)
        name_a = get_canonical_name(code_a)
        name_b = get_canonical_name(code_b)

        if indicator_id:
            return self._compare_indicator_trend(code_a, code_b, name_a, name_b, indicator_id, save)
        elif sector_id:
            return self._compare_sector_bars(code_a, code_b, name_a, name_b, sector_id, year, save)
        else:
            raise ValueError("Either indicator_id or sector_id must be provided.")

    def _compare_indicator_trend(
        self,
        code_a: str,
        code_b: str,
        name_a: str,
        name_b: str,
        indicator_id: str,
        save: bool,
    ) -> plt.Figure:
        """Overlaid time series for two countries on one indicator."""
        df = self.loader.load_single_indicator(indicator_id)
        ind_name = self.loader.get_indicator_name(indicator_id)

        def _get_trend(code: str) -> pd.DataFrame:
            d = self.loader.filter_country(df, code).dropna(subset=["score"])
            return d.groupby("year", as_index=False)["score"].mean().sort_values("year")

        trend_a = _get_trend(code_a)
        trend_b = _get_trend(code_b)

        fig, ax = plt.subplots(figsize=(11, 5))
        ax.plot(trend_a["year"].astype(int), trend_a["score"], marker="o", linewidth=2,
                color="#1565C0", label=name_a, markersize=6)
        ax.plot(trend_b["year"].astype(int), trend_b["score"], marker="s", linewidth=2,
                color="#C62828", label=name_b, markersize=6, linestyle="--")
        ax.fill_between(trend_a["year"].astype(int), trend_a["score"], alpha=0.08, color="#1565C0")
        ax.fill_between(trend_b["year"].astype(int), trend_b["score"], alpha=0.08, color="#C62828")
        ax.axhline(50, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
        ax.set_ylim(0, 105)
        ax.set_xlabel("Year")
        ax.set_ylabel("Score (0-100)")
        ax.set_title(
            f"{indicator_id} — {ind_name}\n{name_a} vs {name_b}",
            fontsize=12, fontweight="bold"
        )
        ax.legend(fontsize=10)
        plt.tight_layout()

        if save:
            out_dir = self._out_dir / "compare"
            ensure_dir(out_dir)
            slug_a = code_a
            slug_b = code_b
            path = out_dir / f"{slug_a}_vs_{slug_b}_{indicator_id.replace('.', '-')}.png"
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def _compare_sector_bars(
        self,
        code_a: str,
        code_b: str,
        name_a: str,
        name_b: str,
        sector_id: str,
        year: Optional[int],
        save: bool,
    ) -> plt.Figure:
        """Grouped bar chart of sector indicators for two countries."""
        sector_name = self.loader.get_sector_name(sector_id)
        ind_df = self.loader.load_indicator_scores()

        def _get_scores(code: str) -> pd.Series:
            d = self.loader.filter_country(ind_df, code).dropna(subset=["score"])
            d = d.groupby(["indicator", "year"], as_index=False)["score"].mean()
            if year is not None:
                d = d[d["year"] == year]
            else:
                d = self.loader.get_latest_year(d)
            return d.set_index("indicator")["score"]

        scores_a = _get_scores(code_a)
        scores_b = _get_scores(code_b)

        from src.calculating.hierarchy import INDICATORS
        sector_inds = [
            m for m in INDICATORS.values()
            if m.sector_id == sector_id
        ]
        seen = set()
        unique_inds = []
        for m in sorted(sector_inds, key=lambda m: m.subsector_id):
            if m.indicator_id not in seen:
                unique_inds.append(m)
                seen.add(m.indicator_id)

        ind_ids = [m.indicator_id for m in unique_inds]
        ind_names = [f"{m.indicator_id}\n{m.name[:30]}" for m in unique_inds]
        vals_a = [scores_a.get(i, np.nan) for i in ind_ids]
        vals_b = [scores_b.get(i, np.nan) for i in ind_ids]

        x = np.arange(len(ind_ids))
        width = 0.35
        fig, ax = plt.subplots(figsize=(max(10, len(ind_ids) * 1.4), 6))
        bars_a = ax.bar(x - width / 2, [v if not np.isnan(v) else 0 for v in vals_a],
                        width, label=name_a, color="#1565C0", alpha=0.85)
        bars_b = ax.bar(x + width / 2, [v if not np.isnan(v) else 0 for v in vals_b],
                        width, label=name_b, color="#C62828", alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels(ind_names, fontsize=8, rotation=15, ha="right")
        ax.set_ylim(0, 110)
        ax.set_ylabel("Score (0-100)")
        ax.axhline(50, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.set_title(
            f"{sector_id} {sector_name}\n{name_a} vs {name_b}" + (f", {year}" if year else ""),
            fontsize=12, fontweight="bold"
        )
        ax.legend(fontsize=10)
        plt.tight_layout()

        if save:
            out_dir = self._out_dir / "compare"
            ensure_dir(out_dir)
            path = out_dir / f"{code_a}_vs_{code_b}_sector_{sector_id.replace('.', '-')}.png"
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    def plot_compare_regions(
        self,
        region_a: str,
        region_b: str,
        indicator_id: Optional[str] = None,
        sector_id: Optional[str] = None,
        year: Optional[int] = None,
        save: bool = True,
    ) -> plt.Figure:
        """
        Compare two regions (continent averages) on an indicator or sector.

        Mirrors country comparison but uses the mean of all countries in each region.

        Args:
            region_a: Region code, e.g. "AF".
            region_b: Region code, e.g. "AS".
            indicator_id: Compare on this indicator (time series of region averages).
            sector_id: Compare on sector indicators (bar chart, uses year).
            year: Year for sector comparison; defaults to most recent.
            save: Whether to save the figure.

        Returns:
            matplotlib Figure.
        """
        name_a = get_region_name(region_a)
        name_b = get_region_name(region_b)

        if indicator_id:
            df = self.loader.load_single_indicator(indicator_id)
            ind_name = self.loader.get_indicator_name(indicator_id)
            df = df.dropna(subset=["score"])
            df = df.groupby(["country_code", "year"], as_index=False)["score"].mean()

            avg_a = self.loader.get_region_average(df, region_a, "score", group_by=["year"])
            avg_b = self.loader.get_region_average(df, region_b, "score", group_by=["year"])

            fig, ax = plt.subplots(figsize=(11, 5))
            ax.plot(avg_a["year"].astype(int), avg_a["score"], marker="o", linewidth=2,
                    color="#2E7D32", label=name_a, markersize=6)
            ax.plot(avg_b["year"].astype(int), avg_b["score"], marker="s", linewidth=2,
                    color="#6A1B9A", label=name_b, markersize=6, linestyle="--")
            ax.fill_between(avg_a["year"].astype(int), avg_a["score"], alpha=0.08, color="#2E7D32")
            ax.fill_between(avg_b["year"].astype(int), avg_b["score"], alpha=0.08, color="#6A1B9A")
            ax.axhline(50, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
            ax.set_ylim(0, 105)
            ax.set_xlabel("Year")
            ax.set_ylabel("Score (0-100, region average)")
            ax.set_title(
                f"{indicator_id} — {ind_name}\n{name_a} vs {name_b} (Region Averages)",
                fontsize=12, fontweight="bold"
            )
            ax.legend(fontsize=10)
            plt.tight_layout()

            if save:
                out_dir = self._out_dir.parent / "heatmap"
                ensure_dir(out_dir)
                path = out_dir / f"{region_a}_vs_{region_b}_{indicator_id.replace('.', '-')}.png"
                fig.savefig(path, bbox_inches="tight")
                self.log.info("Saved: %s", path)

            return fig

        elif sector_id:
            sector_name = self.loader.get_sector_name(sector_id)
            ind_df = self.loader.load_indicator_scores()
            ind_df = ind_df.dropna(subset=["score"])
            ind_df = ind_df.groupby(["country_code", "indicator", "year"], as_index=False)["score"].mean()

            from src.calculating.hierarchy import INDICATORS
            sector_inds = sorted(
                {m.indicator_id: m for m in INDICATORS.values() if m.sector_id == sector_id}.values(),
                key=lambda m: m.subsector_id
            )

            def _region_sector_scores(region_code: str) -> dict[str, float]:
                codes = self.loader.get_countries_in_region(region_code)
                df_r = ind_df[ind_df["country_code"].isin(codes)]
                if year is not None:
                    df_r = df_r[df_r["year"] == year]
                else:
                    df_r = self.loader.get_latest_year(df_r)
                return df_r.groupby("indicator")["score"].mean().to_dict()

            scores_a = _region_sector_scores(region_a)
            scores_b = _region_sector_scores(region_b)

            ind_ids = [m.indicator_id for m in sector_inds]
            ind_labels = [f"{m.indicator_id}\n{m.name[:30]}" for m in sector_inds]
            vals_a = [scores_a.get(i, np.nan) for i in ind_ids]
            vals_b = [scores_b.get(i, np.nan) for i in ind_ids]

            x = np.arange(len(ind_ids))
            width = 0.35
            fig, ax = plt.subplots(figsize=(max(10, len(ind_ids) * 1.4), 6))
            ax.bar(x - width / 2, [v if not np.isnan(v) else 0 for v in vals_a],
                   width, label=name_a, color="#2E7D32", alpha=0.85)
            ax.bar(x + width / 2, [v if not np.isnan(v) else 0 for v in vals_b],
                   width, label=name_b, color="#6A1B9A", alpha=0.85)
            ax.set_xticks(x)
            ax.set_xticklabels(ind_labels, fontsize=8, rotation=15, ha="right")
            ax.set_ylim(0, 110)
            ax.set_ylabel("Score (0-100, region average)")
            ax.axhline(50, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
            ax.set_title(
                f"{sector_id} {sector_name}\n{name_a} vs {name_b}" + (f", {year}" if year else ""),
                fontsize=12, fontweight="bold"
            )
            ax.legend(fontsize=10)
            plt.tight_layout()

            if save:
                out_dir = self._out_dir / "compare"
                ensure_dir(out_dir)
                path = out_dir / f"{region_a}_vs_{region_b}_sector_{sector_id.replace('.', '-')}.png"
                fig.savefig(path, bbox_inches="tight")
                self.log.info("Saved: %s", path)

            return fig
        else:
            raise ValueError("Either indicator_id or sector_id must be provided.")

    def plot_country_vs_region(
        self,
        country: str,
        indicator_id: str,
        region: Optional[str] = None,
        save: bool = True,
    ) -> plt.Figure:
        """
        Country score vs its region average over time on one indicator.

        Shows where the country sits relative to its regional peers — useful
        for contextualising whether performance is good or bad for the region.

        Args:
            country: ISO-3 code or canonical name.
            indicator_id: e.g. "3.8.1"
            region: Region code to compare against. Defaults to the country's own region.
            save: Whether to save the figure.

        Returns:
            matplotlib Figure.
        """
        country_code = self._resolve_country(country)
        display_name = get_canonical_name(country_code)
        ind_name = self.loader.get_indicator_name(indicator_id)

        if region is None:
            region = self.loader.get_region_for_country(country_code)
        region_label = get_region_name(region)

        df = self.loader.load_single_indicator(indicator_id)
        df = df.dropna(subset=["score"])
        df = df.groupby(["country_code", "year"], as_index=False)["score"].mean()

        country_trend = (
            self.loader.filter_country(df, country_code)
            .sort_values("year")
        )
        region_avg = self.loader.get_region_average(df, region, "score", group_by=["year"]).sort_values("year")

        fig, ax = plt.subplots(figsize=(11, 5))
        ax.plot(country_trend["year"].astype(int), country_trend["score"],
                marker="o", linewidth=2.5, color="#1565C0", label=display_name, markersize=7)
        ax.plot(region_avg["year"].astype(int), region_avg["score"],
                marker="", linewidth=1.5, color="#E53935", linestyle="--",
                alpha=0.8, label=f"{region_label} Average")
        ax.fill_between(
            country_trend["year"].astype(int), country_trend["score"], region_avg["score"],
            where=(country_trend["score"].values >= region_avg["score"].values),
            alpha=0.1, color="#1565C0", interpolate=True
        )
        ax.fill_between(
            country_trend["year"].astype(int), country_trend["score"], region_avg["score"],
            where=(country_trend["score"].values < region_avg["score"].values),
            alpha=0.1, color="#E53935", interpolate=True
        )
        ax.axhline(50, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
        ax.set_ylim(0, 105)
        ax.set_xlabel("Year")
        ax.set_ylabel("Score (0-100)")
        ax.set_title(
            f"{display_name} vs {region_label} Average\n{indicator_id} — {ind_name}",
            fontsize=12, fontweight="bold"
        )
        ax.legend(fontsize=10)
        plt.tight_layout()

        if save:
            out_dir = self._out_dir / display_name.replace(" ", "_")
            ensure_dir(out_dir)
            path = out_dir / f"vs_region_{indicator_id.replace('.', '-')}_{region}.png"
            fig.savefig(path, bbox_inches="tight")
            self.log.info("Saved: %s", path)

        return fig

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve_country(self, country: str) -> str:
        """Resolve a country name or code to an ISO-3 code."""
        from src.utils.country_names import COUNTRY_NAMES
        if len(country) == 3 and country.isupper() and country in COUNTRY_NAMES:
            return country
        # Try matching by canonical display name
        match = next(
            (code for code, name in COUNTRY_NAMES.items() if name.lower() == country.lower()),
            None,
        )
        if match:
            return match
        raise ValueError(
            f"Could not resolve country '{country}' to a known ISO-3 code. "
            f"Use a 3-letter code (e.g. 'AFG') or a canonical name (e.g. 'Afghanistan')."
        )
