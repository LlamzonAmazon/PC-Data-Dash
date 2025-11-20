# Data Processing Module
Composite index construction and regression modelling.

### Composite Index Construction
Composite indices matter because they turn dozens of heterogeneous climate indicators into clean, comparable development metrics aligned with the client’s needs. The pipeline uses the raw indicator values to construct _three_ kinds of composite metrics:

__1. Sector Scores__
_For each country and each sector_ (food, water, etc.):
  $$ sector\_score = mean(indicator\_1 ... indicator\_6) $$
This compresses six related climate variables into one interpretable number.

__2. Climate Vulnerability Index__
The _vulnerability index of a country_ is the simple mean of the six sector scores, with all indicators weighted equally:
  $$ vulnerability = mean(food, water, health, ecosystem, habitat, infrastructure) $$

__3. Readiness & Composite Resilience Metrics__
Readiness scores (economic, governance, social) are computed the same way, and combined with vulnerability to form custom composite resilience indices for the dashboard.

### Forecasting
ND-GAIN indicators themselves are not time-series—most are static or long-term projections. But once you compute sector scores, vulnerability, readiness, and custom composite indices, you can align them across years with:
* World Bank time-series indicators
* UN SDG time-series indicators

This creates meaningful multi-year datasets (time series) for each country. A __time series__ is simply a metric observed across multiple years. By computing composite indices for each available year, we generate time series such as:
* Vulnerability Index over time
* Food Vulnerability over time
* Readiness Index over time
* Custom climate-development composites over time

These become inputs to regression models to forecast:
* future vulnerability trajectories
* future development-climate resilience trends
* sector-specific improvements or deteriorations

This supports the client's requirement to “forecast country-level development indicators” using combined ND-GAIN, SDG, and World Bank data.