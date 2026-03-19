Data File structure

data/
│
├── raw/                               # Raw fetched data
│   ├── nd_gain_raw.csv
│   ├── un_sdg_raw.json
│   └── world_bank_raw.json
├── interim/
│   ├── nd_gain_interim.csv
│   ├── un_sdg_interim.csv
│   └── world_bank_interim.csv subsectorscores.csv            # Stores Sub-Sector composite scores
├── processed/
│    ├── domainscores.csv               # Stores Domain composite scores 
│    ├── sectorscores.csv               # Stores Sector composite scores
│    ├── subsectorscores.csv            # Stores Sub-Sector composite scores
│    ├── indicatorscores/               # Stores per-indicator cleaned values
│    │    ├── indicator-3-8-1.csv       # Each indicator has its own value CSV file containing all region/reporting types/etc.
│    │    ├── indicator-3-3-2.csv
│    │    ├── ...
├── plots/                              # Any data that we have plotted to visualize          

