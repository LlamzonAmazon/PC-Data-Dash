"""
Dashboard CLI — batch generation of dashboard plots.

This is the command-line interface for generating static PNG exports.
For interactive exploration, use the Jupyter notebook at notebooks/dashboard_explorer.ipynb.

USAGE
-----
# HEATMAP MODE
python -m src.plotting.dashboard heatmap --indicator 3.8.1
python -m src.plotting.dashboard heatmap --indicator 3.8.1 --year 2022
python -m src.plotting.dashboard heatmap --indicator 3.8.1 --year 2022 --by-region
python -m src.plotting.dashboard heatmap --list-indicators

# COUNTRY SELECTOR MODE
python -m src.plotting.dashboard country --country Afghanistan
python -m src.plotting.dashboard country --country AFG --year 2022
python -m src.plotting.dashboard country --country AFG --sector 1.1
python -m src.plotting.dashboard country --compare AFG ETH --indicator 3.8.1
python -m src.plotting.dashboard country --compare AFG ETH --sector 1.1
python -m src.plotting.dashboard country --compare-regions AF AS --indicator 3.8.1
python -m src.plotting.dashboard country --compare-regions AF AS --sector 1.1
python -m src.plotting.dashboard country --country AFG --vs-region --indicator 3.8.1
python -m src.plotting.dashboard country --country AFG --all

All plots are saved to data/plots/dashboard/.
"""

from __future__ import annotations

import argparse
import logging
import sys

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for CLI use

from src.plotting.dashboard_data import DashboardDataLoader
from src.plotting.dashboard_plotter import HeatmapModePlotter, CountryModePlotter


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        stream=sys.stdout,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.plotting.dashboard",
        description="PlanCatalyst Dashboard — local plot generation",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # ------------------------------------------------------------------ heatmap
    hm = sub.add_parser("heatmap", help="Heatmap Mode — global indicator views")
    hm.add_argument("--indicator", "-i", metavar="ID",
                    help="Indicator code, e.g. '3.8.1'")
    hm.add_argument("--year", "-y", metavar="YEAR", type=int,
                    help="Single year; omit for all-years heatmap")
    hm.add_argument("--by-region", action="store_true",
                    help="Group by continent region instead of individual countries")
    hm.add_argument("--distribution", "-d", action="store_true",
                    help="Plot score distribution (histogram + KDE)")
    hm.add_argument("--list-indicators", "-l", action="store_true",
                    help="Print the hierarchical indicator list and exit")
    hm.add_argument("--all", "-a", action="store_true",
                    help="Generate all heatmap views for the given indicator")

    # ------------------------------------------------------------------ country
    ct = sub.add_parser("country", help="Country Selector Mode — country views + comparisons")
    ct.add_argument("--country", "-c", metavar="COUNTRY",
                    help="Country ISO-3 code or name (e.g. 'AFG' or 'Afghanistan')")
    ct.add_argument("--year", "-y", metavar="YEAR", type=int,
                    help="Year; defaults to most recent available")
    ct.add_argument("--sector", "-s", metavar="SECTOR_ID",
                    help="Sector ID for drill-down (e.g. '1.1')")
    ct.add_argument("--indicator", "-i", metavar="ID",
                    help="Indicator code for trend or comparison")
    ct.add_argument("--compare", nargs=2, metavar=("COUNTRY_A", "COUNTRY_B"),
                    help="Compare two countries")
    ct.add_argument("--compare-regions", nargs=2, metavar=("REGION_A", "REGION_B"),
                    help="Compare two regions, e.g. 'AF AS'")
    ct.add_argument("--vs-region", action="store_true",
                    help="Compare country against its region average (requires --indicator)")
    ct.add_argument("--all", "-a", action="store_true",
                    help="Generate all views for the specified country")

    return parser


def cmd_heatmap(args: argparse.Namespace) -> None:
    loader = DashboardDataLoader()
    hm = HeatmapModePlotter(loader)

    if args.list_indicators:
        hm.generate_indicator_selector_list()
        return

    if not args.indicator:
        print("Error: --indicator is required for heatmap mode (or use --list-indicators)")
        sys.exit(1)

    ind = args.indicator

    if getattr(args, "all", False):
        print(f"Generating all heatmap views for {ind}...")
        fig = hm.plot_indicator_heatmap(ind)
        fig = hm.plot_indicator_heatmap(ind, year=args.year) if args.year else fig
        hm.plot_indicator_heatmap_by_region(ind)
        if args.year:
            hm.plot_indicator_heatmap_by_region(ind, year=args.year)
        hm.plot_score_distribution(ind, year=args.year)
        print("Done.")
        return

    if args.distribution:
        hm.plot_score_distribution(ind, year=args.year)
        return

    if args.by_region:
        hm.plot_indicator_heatmap_by_region(ind, year=args.year)
    else:
        hm.plot_indicator_heatmap(ind, year=args.year)


def cmd_country(args: argparse.Namespace) -> None:
    loader = DashboardDataLoader()
    ct = CountryModePlotter(loader)

    # -- region vs region comparison
    if args.compare_regions:
        region_a, region_b = args.compare_regions
        if not args.indicator and not args.sector:
            print("Error: --compare-regions requires --indicator or --sector")
            sys.exit(1)
        ct.plot_compare_regions(
            region_a, region_b,
            indicator_id=args.indicator,
            sector_id=args.sector,
            year=args.year,
        )
        return

    # -- two-country comparison
    if args.compare:
        ca, cb = args.compare
        if not args.indicator and not args.sector:
            print("Error: --compare requires --indicator or --sector")
            sys.exit(1)
        ct.plot_compare_countries(
            ca, cb,
            indicator_id=args.indicator,
            sector_id=args.sector,
            year=args.year,
        )
        return

    # -- single country
    if not args.country:
        print("Error: --country is required (or use --compare / --compare-regions)")
        sys.exit(1)

    country = args.country

    if args.vs_region:
        if not args.indicator:
            print("Error: --vs-region requires --indicator")
            sys.exit(1)
        ct.plot_country_vs_region(country, args.indicator)
        return

    if getattr(args, "all", False):
        print(f"Generating all views for {country}...")
        ct.plot_country_profile(country, year=args.year)
        loader_ref = DashboardDataLoader()
        for sector_id, _ in loader_ref.get_sector_list():
            try:
                ct.plot_country_sector_detail(country, sector_id, year=args.year)
            except Exception as e:
                logging.warning("Skipping sector %s: %s", sector_id, e)
        print("Done. Plots saved to data/plots/dashboard/country/")
        return

    if args.sector:
        ct.plot_country_sector_detail(country, args.sector, year=args.year)
        return

    if args.indicator:
        ct.plot_country_trend(country, args.indicator)
        return

    # Default: full profile
    ct.plot_country_profile(country, year=args.year)


def main() -> None:
    _setup_logging()
    parser = _build_parser()
    args = parser.parse_args()

    if args.mode == "heatmap":
        cmd_heatmap(args)
    elif args.mode == "country":
        cmd_country(args)


if __name__ == "__main__":
    main()
