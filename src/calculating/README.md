# Data Scoring & Aggregation Module 

## Overview
This module is responsible for normalizing raw indicator data into a unified scoring system and aggregating those scores into a multi-level hierarchy (Subsector, Sector, Domain) to for the dashboard

## Running this module
To run this module, use the following command:
```zsh
python3 -m src.calculating.pipeline
```

## Module Architecture
Module follows an Abstract Factory Pattern:
- scorers.py : Contains the mathematical formulas
- factory.py : Maps each indicator/series code to the calculation required
- aggregate.py : Performs the weighting arithmetic means 
- hierarchy.py : Defines which indicators belong to which subsectors -> sectors -> domains
- weights.py : Defines the importance of each component in aggregation (default is equal)
    - change this .py file to alter weighting 

## Scoring Framework
The pipeline converts all data into a 0-100 scale, where higher scores represent 'higher level of need' or an impact gap. **Score of 0 indicates goal has been met** 

#### Harmoniation to 0 (Flooring Logic)
If a indicator's raw value is "better" than the defined SDG target, or global average, it is harmonized to zero. floored_to_zero (column)= true, if a score is floored

### Aggregation for domain, sector & subsector composite score
Currently all domain, sector & subsector scores have an equal weighting as default. These weightings can be changed in the weights.py file (example at the bottom)

### UN-SDG Inidcator: 3.d.1
Currently 3.d.1 calculates an individual score for all classifications (There is no one score for 3.d.1). 
- 3.d.1 is the only indicator in subsector: reproductive health and family planning
    - Thus, currently, all classfification scores are averaged to get the composite score for this sector 
- These weightings can be changed in the weights.py file (example at the bottom)
    - 3.d.1 uses a dynamic weighting strategy
        - This is to ensure that if you prioritize one category, it is strictly maintained for all countries/years

## Naming & ID Rules
Domain 1: Impact
- Sector 1.1: Healthcare
    - 1.1.1: Resilient primary healthcare (PHC) systems
    - 1.1.2: Infectious disease control
    - 1.1.3: Maternal, newborn, and child health
    - 1.1.4: Nutrition
    - 1.1.5: Reproductive health and family planning
    - 1.1.6: Health risk reduction and management
- Sector 1.2: Agriculture
    - 1.2.1: Food security
    - 1.2.2: Agricultural systems and value chain strengthening
- Sector 1.3: Social Infrastructure
    - 1.3.1: Water, sanitation, and hygiene (WASH)
    - 1.3.2: Off-grid power
    - 1.3.3: Digital financial inclusion
- Sector 1.5: Context
    - 1.5.1: Additional country considerations (Poverty, Density, etc.)

## Data Output Structure
Paths come from `paths.data_interim_validated` in `src/config/settings.yaml` (default `data/interim/validated/`).

├── validated/
│    ├── domainscores.csv               # Domain composite scores
│    ├── sectorscores.csv               # Sector composite scores
│    ├── subsectorscores.csv            # Sub-sector composite scores
│    ├── Indicator_Scores_Full.csv      # Full scored indicator rows (all disaggregations)
│    ├── indicatorscores/               # Per-series scored slices
│    │    ├── indicator-3-8-1.csv
│    │    ├── indicator-3-3-2.csv
│    │    ├── ...






