# PlanCatalyst Global Development Dashboard

## Role
I (Thomas) am the Project Manager. I review all PRs and merges to main.

## What This Is
A data pipeline + Power BI dashboard for **PlanCatalyst** (Plan International Canada subsidiary, est. 2022), a consultancy serving development funders, impact investors, social enterprises, corporations (ESG), and government agencies. The dashboard surfaces which regions are most vulnerable to specific areas of underdevelopment so PlanCatalyst's clients can direct their own interventions. "Impact" is not defined by the dashboard — it guides clients toward need.

## How It Works
```
Fetch (3 APIs) → Clean/Validate → Score/Aggregate → Upload (Azure Blob) → Power BI
```
- **Indicators**: Country development indicators measuring vulnerability (0-100 scale). **`indicators/indicators.yaml`** is the authoritative reference: it lists every indicator grouped by **domain**, **sector**, and **subsector**. Use it to understand **what data the pipeline must produce** and **how the dashboard intends to visualize** those indicators (definitions, scoring, sources). The **impact** domain is the primary focus — it carries the largest share of indicators.
- **Data sources**: UN SDG API, World Bank API, ND-GAIN (ZIP export)
- **Output**: Scored CSVs uploaded to Azure Blob → Power BI connects via blob connection string URL + credentials

## Current Sprint (MVP)
- **Goal**: Local Power BI dashboard pulling validated data from Azure Blob
- **Focus**: Validating cleaned data, verifying pipeline from clean → Azure Blob → Power BI, structuring data for dashboard usability
- **Data quirks**: Null entries and odd-looking values may be legitimate (real-world data). Visual inspection needed to confirm cleanliness.
- **Projections**: A dev is working on this but data range (2014-2024) makes reliable projections difficult. MVP has no projections — just visualizes indicator progress.

## Caution Areas
- **Fetching module** (`src/fetch/`): Be careful modifying — UN SDG fetch is rate-limited (~30 min), has complex dimension-filtered strategies. Don't trigger unnecessary API calls.
- **Never commit secrets** (`.env`, credentials). Always verify `.gitignore` coverage.

## Module Documentation
For detailed implementation context, load on-demand from `.claude/docs/`:
- [ARCHITECTURE.md](.claude/docs/ARCHITECTURE.md) — Top-level overview, module map, design patterns
- [fetch.md](.claude/docs/fetch.md) — Data fetching (APIs, retry logic)
- [clean.md](.claude/docs/clean.md) — Data cleaning (schemas, transformations)
- [processing.md](.claude/docs/processing.md) — Actuals + forecasts (MVP stub)
- [calculating.md](.claude/docs/calculating.md) — Scoring strategies, hierarchical aggregation
- [pipeline.md](.claude/docs/pipeline.md) — Orchestration, entry points
- [upload.md](.claude/docs/upload.md) — Azure Blob upload
- [config.md](.claude/docs/config.md) — Settings, env vars, YAML configs
- [data.md](.claude/docs/data.md) — Data directory structure & schemas
- [indicators.md](.claude/docs/indicators.md) — Full indicator taxonomy & scoring reference
- [infrastructure.md](.claude/docs/infrastructure.md) — Docker, CI/CD, Azure architecture
- [qa.md](.claude/docs/qa.md) — Duplicate detection & validation
- [plotting.md](.claude/docs/plotting.md) — Visualization (in development)

## References
- `Azure-Arch.png` — Azure pipeline architecture
- `Data-Flow.png` — Data flow through the pipeline
- `indicators/indicators.yaml` — Full indicator catalog by domain / sector / subsector; drives data requirements and visualization intent (impact domain is the main concentration)
