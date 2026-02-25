## World Bank Blob Output Documentation 
# Overview

The processing stage generates two separate CSV files for World Bank data:

- Historical actuals
- Forecasted projections

These outputs are structured for direct consumption in Power BI and stored in clearly separated Blob paths.

### Blob Paths
# Actuals
processed/worldbank/actuals/world_bank_actuals.csv

(Contains historical observed values only.)

# Forecasts (Projections)
processed/worldbank/forecasts/world_bank_forecasts.csv

(Contains baseline projections generated using a last-value-carried-forward method.)

# File Format

Both files use the same core schema:

Column |Description
-------------------------------------------------------------------
country | Country name
iso3	| ISO3 country code
indicator-code	| Stable indicator code (e.g., EN.POP.DNST)
indicator	| Indicator display name
year	| Year of observation
value	| Numeric value
record_type	| "actual" or "forecast"
generated_at	| UTC timestamp of file generation
model_name	| Present in forecasts only (e.g., baseline_last_value)

# Power BI Integration Notes

- Use record_type to distinguish historical vs projected values.
- Join on iso3 and indicator-code for stable relationships.
- Actuals and forecasts are intentionally stored in separate Blob paths to prevent dataset mixing.