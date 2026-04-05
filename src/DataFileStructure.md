Data File structure

data/
│
├── raw/                               # Raw fetched data
│   ├── nd_gain_raw.csv
│   ├── un_sdg_raw.json
│   └── world_bank_raw.json
│
├── interim/
│   ├── cleaned/                       # Outputs from src/clean (standardized interim CSVs)
│   │   ├── nd_gain_interim.csv
│   │   ├── un_sdg_interim.csv
│   │   └── world_bank_interim.csv
│   │   
│   └── validated/                     # Outputs from src/calculating (scoring & composites)
│       ├── domainscores.csv
│       ├── sectorscores.csv
│       ├── subsectorscores.csv
│       │
│       ├── unsdg
│       │    ├── Indicator_Scores_Full.csv
│       │    └── indicatorscores/           # Per-series scored rows (one CSV per mapped series)
│       │       ├── indicator-3-8-1.csv
│       │       ├── indicator-3-3-2.csv
│       │       └── ...
│       │
│       ├── ndgain
│       │   ├── ecosystem
│       │   │   ├── id_ecos_01.csv
│       │   │   └── ...
│       │   ├── food
│       │   │   ├── id_food_01.csv
│       │   │   └── ...
│       │   ├── habitat
│       │   │   ├── id_habi_01.csv
│       │   │   └── ...
│       │   ├── health
│       │   │   ├── id_health_01.csv
│       │   │   └── ...
│       │   ├── infrastructure
│       │   │   ├── id_infr_01.csv
│       │   │   └── ...
│       │   ├── water
│       │   │   ├── id_wate_01.csv
│       │   │   └── ...
│       │   │   
│       │   └── vulnerability.csv
│       │
│       ├── worldbank
│       │   └── world_bank_validated.csv
│       │
│       ├── undp
│       │   ├── 
│       │   └── ...
│       │
│       └── gii
│           ├── 
│           └── ...
│
├── processed/                         # Projections of indicator progress (src/processing)
│   └── worldbank/
│       ├── actuals/                   # Historical observed values
│       └── forecasts/                 # Projected future years (e.g. baseline carry-forward)
└── plots/                             # Any plotted outputs
