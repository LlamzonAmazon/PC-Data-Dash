# Plotting Module

Two distinct plotting layers — one reads cleaned (pre-scoring) data, one reads validated scored data and powers the dashboard prototype.

---

## Layer 1 — Interim Data Plotter (pre-scoring)

Reads `data/interim/cleaned/un_sdg_interim.csv` and produces raw indicator time series.

```bash
python -m src.plotting.un_sdg_plotter Afghanistan
```

---

## Layer 2 — Dashboard Plotters (post-scoring)

Reads `data/interim/validated/` (the structured Power BI output). Organised into two modes matching the Power BI dashboard layout.

### Quick start

```python
from src.plotting.dashboard_data import DashboardDataLoader
from src.plotting.dashboard_plotter import HeatmapModePlotter, CountryModePlotter

loader       = DashboardDataLoader()
heatmap      = HeatmapModePlotter(loader)
country_mode = CountryModePlotter(loader)
```

Or open the interactive notebook:

```bash
# Cursor opens .ipynb natively; or:
jupyter notebook notebooks/dashboard_explorer.ipynb
```

---

## Heatmap Mode — `HeatmapModePlotter`

Mirrors the Power BI globe view: select one indicator → all countries coloured 0–100.

| Method | Description |
|--------|-------------|
| `plot_indicator_heatmap(indicator_id, year=None)` | Seaborn heatmap: countries × years. When `year` is specified, produces a ranked horizontal bar chart instead. |
| `plot_indicator_heatmap_by_region(indicator_id, year=None)` | Same data but rows are continent averages (AF/AS/EU/NA/SA/OC). |
| `plot_score_distribution(indicator_id, year=None)` | Histogram + KDE of score distribution across all countries. |
| `generate_indicator_selector_list()` | Prints the hierarchical indicator list (domain → sector → subsector → indicator) — matches the Power BI right-sidebar layout. |

### CLI — Heatmap Mode

```bash
# Full heatmap across all years
python -m src.plotting.dashboard heatmap --indicator "3.8.1"

# Single-year ranking bar chart
python -m src.plotting.dashboard heatmap --indicator "3.8.1" --year 2022

# Region averages heatmap
python -m src.plotting.dashboard heatmap --indicator "3.8.1" --by-region

# Print indicator selector list
python -m src.plotting.dashboard heatmap --list-indicators
```

---

## Country Selector Mode — `CountryModePlotter`

Mirrors the Power BI country view: click a country → right sidebar shows its indicators grouped by sector.

| Method | Description |
|--------|-------------|
| `plot_country_profile(country, year=None)` | One panel per sector — all indicator scores for one country. Core "right sidebar" view. |
| `plot_country_sector_detail(country, sector_id, year=None)` | Drill-down: subsector + indicator bars for one sector. |
| `plot_country_trend(country, indicator_id)` | Score over time for one country on one indicator. |
| `plot_country_vs_region(country, indicator_id, region=None)` | Country trend vs its regional (continent) average. |
| `plot_compare_countries(country_a, country_b, indicator_id=None, sector_id=None)` | Two countries: overlaid time series (indicator) or grouped bars (sector). |
| `plot_compare_regions(region_a, region_b, indicator_id=None, sector_id=None)` | Same as compare_countries but using continent averages. |

### CLI — Country Mode

```bash
# Full country profile (all sectors)
python -m src.plotting.dashboard country --country "Afghanistan"

# Drill into one sector
python -m src.plotting.dashboard country --country "Afghanistan" --sector "1.1"

# Compare two countries on an indicator
python -m src.plotting.dashboard country --compare "Afghanistan" "Ethiopia" --indicator "3.8.1"

# Compare two regions on a sector
python -m src.plotting.dashboard country --compare-regions "AF" "AS" --sector "1.1"

# Generate all plots for a country
python -m src.plotting.dashboard country --country "Afghanistan" --all
```

---

## Data Schemas — `data/interim/validated/`

| File | Key columns |
|------|------------|
| `domainscores.csv` | `country_code, country_name, year, domain_id, domain_score, floored_to_zero` |
| `sectorscores.csv` | `country_code, country_name, year, sector_id, sector_score, floored_to_zero` |
| `subsectorscores.csv` | `country_code, country_name, year, subsector_id, subsector_score, floored_to_zero` |
| `Indicator_Scores_Full.csv` | `country_code, country_name, year, value, indicator, series_code, score, floored_to_zero` (+ dimension cols) |
| `indicatorscores/indicator-*.csv` | Same schema as `Indicator_Scores_Full` — one file per indicator |

**Join key**: always `country_code` (ISO alpha-3). Never join on `country_name` — it differs across data sources.

---

## Indicator Hierarchy

IDs in the CSVs (`1.1`, `1.1.3`, etc.) are positionally assigned by the scoring pipeline and match the structure in `indicators/indicators.yaml`:

```
Domain 1: Impact
  1.1  Healthcare
    1.1.1  Resilient primary healthcare (PHC) systems  → 3.8.1
    1.1.2  Infectious disease control                  → 3.3.2, 3.3.3
    1.1.3  Maternal, newborn, and child health          → 3.1.1, 3.2.1
    1.1.4  Nutrition                                   → 2.2.1, 2.2.2, 2.2.3
    1.1.5  Reproductive health and family planning     → 3.7.1, 3.7.2
    1.1.6  Health risk reduction and management        → 3.d.1
  1.2  Agriculture
    1.2.1  Food security                               → 2.1.1, 2.1.2
    1.2.2  Agricultural systems and value chain        → 2.3.1
  1.3  Social Infrastructure
    1.3.1  WASH                                        → 6.1.1, 6.2.1
    1.3.2  Off-grid power                              → 7.1.1
    1.3.3  Digital financial inclusion                 → 17.3.1 (stub)
  1.5  Additional Country Considerations
    1.5.1  Poverty                                     → 1.1.1, 1.2.1, 1.2.2
```

Use `loader.get_indicator_hierarchy()` to get this as a nested dict.

---

## Region Mapping

Countries are grouped into six continents via `src/utils/country_names.py`:

| Code | Region |
|------|--------|
| `AF` | Africa |
| `AS` | Asia |
| `EU` | Europe |
| `NA` | North America |
| `SA` | South America |
| `OC` | Oceania |

Region aggregation = arithmetic mean across all countries in the continent for a given score column.

**For Power BI**: use `country_code` as the join key for the region mapping — never `country_name`.

---

## Plot Output

All plots are saved to `data/plots/dashboard/`:

```
data/plots/dashboard/
  heatmap/
    indicator-3-8-1_all_years.png
    indicator-3-8-1_2022_ranking.png
    indicator-3-8-1_all_years_by_region.png
    distribution_3-8-1.png
    AF_vs_AS_3-8-1.png
  country/
    Afghanistan/
      profile_2022.png
      sector_1-1_Healthcare_2022.png
      trend_3-8-1.png
      vs_region_3-8-1_AS.png
    compare/
      AFG_vs_ETH_3-8-1.png
      AF_vs_AS_sector_1-1.png
```

## Naming Convention (legacy `un_sdg_plotter`)

```
{SectorNumber}_{SectorAbbrev}_{SubTheme}
```
- `HC` Healthcare · `AG` Agriculture · `SI` Social Infrastructure  
- `CC` Cross-Cutting Themes · `AC` Additional Considerations  

Example: `1_HC_Nutrition`
