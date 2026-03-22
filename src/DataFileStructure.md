Data File structure

data/
│
├── raw/                               # Raw fetched data
│   ├── nd_gain_raw.csv
│   ├── un_sdg_raw.json
│   └── world_bank_raw.json
├── interim/
│   ├── cleaned/                       # Outputs from src/clean (standardized interim CSVs)
│   │   ├── nd_gain_interim.csv
│   │   ├── un_sdg_interim.csv
│   │   └── world_bank_interim.csv
│   └── validated/                     # Outputs from src/calculating (scoring & composites)
│       ├── Indicator_Scores_Full.csv
│       ├── domainscores.csv
│       ├── sectorscores.csv
│       ├── subsectorscores.csv
│       └── indicatorscores/           # Per-series scored rows (one CSV per mapped series)
│           ├── indicator-3-8-1.csv
│           ├── indicator-3-3-2.csv
│           └── ...
├── processed/                         # Projections of indicator progress (src/processing)
│   └── worldbank/
│       ├── actuals/                   # Historical observed values
│       └── forecasts/                 # Projected future years (e.g. baseline carry-forward)
└── plots/                             # Any plotted outputs
