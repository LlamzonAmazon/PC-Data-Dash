Data File structure

data/
│
├── raw/
├── interim/
│    ├── subsectorscores.csv            # Stores Sub-Sector composite scores
│    ├── sectorscores.csv               # Stores Sector composite scores
│    ├── domainscores.csv               # Stores Domain composite scores
│    ├── indicatorscores/               # Stores per-indicator cleaned values
│    │    ├── indicator-3-8-1.csv       # Each indicator has its own value CSV file containing all region/reporting types/etc.
│    │    ├── indicator-3-3-2.csv
│    │    ├── ...
│    ├── raw/
├── processed/
│ 
└── 

My favourite aspect of this project is how we get to use real world census data to create insights that actually guide our client organization's humanitarian efforts  