
from typing import Any, Dict, List, Optional

import pandas as pd
from pathlib import Path
import yaml

from src.clean.base_clean import DataCleaner
from src.pipeline.utils import ensure_dir, project_root
from src.pipeline.terminal_output import TerminalOutput

class UNSDGCleaner(DataCleaner):
    """
    Clean UN SDG data
    """
    
    # Keep exactly one series_code per indicator (source of truth: dashboard spec table).
    _KEEP_SERIES_BY_INDICATOR = {
        "1.2.1": "SI_POV_NAHC",
        "2.1.2": "AG_PRD_FIESMS",
        "2.2.1": "SH_STA_STNT",
        "2.2.2": "SN_STA_OVWGT",
        "2.2.3": "SH_STA_ANEM",
        "2.4.1": "AG_LND_SUST",
        "2.a.2": "DC_TOF_AGRL",
        "3.1.1": "SH_STA_MORT",
        "3.2.1": "SH_DYN_MORT",
        "3.3.2": "SH_TBS_INCD",
        "3.3.3": "SH_STA_MALR",
        "3.7.1": "SH_FPL_MTMM",
        "3.7.2": "SP_DYN_ADKL",
        "3.8.1": "SH_ACS_UNHC_25",
        "3.9.2": "SH_STA_WASHARI",
        "3.d.1": "SH_IHR_CAPS",
        "6.1.1": "SH_H2O_SAFE",
        "6.2.1": "SH_SAN_SAFE",
        "7.1.1": "EG_ACS_ELEC",
        "7.1.2": "EG_EGY_CLEAN",
        "7.2.1": "EG_FEC_RNEW",
        "8.10.2": "FB_BNK_ACCSS",
    }
    
    _UN_SDG_COUNTRY_CODES = {
        "004": "AFG",
        "248": "ALA",
        "008": "ALB",
        "012": "DZA",
        "016": "ASM",
        "020": "AND",
        "024": "AGO",
        "660": "AIA",
        "010": "ATA",
        "028": "ATG",
        "032": "ARG",
        "051": "ARM",
        "533": "ABW",
        "036": "AUS",
        "040": "AUT",
        "031": "AZE",
        "044": "BHS",
        "048": "BHR",
        "050": "BGD",
        "052": "BRB",
        "112": "BLR",
        "056": "BEL",
        "084": "BLZ",
        "204": "BEN",
        "060": "BMU",
        "064": "BTN",
        "068": "BOL",
        "535": "BES",
        "070": "BIH",
        "072": "BWA",
        "074": "BVT",
        "076": "BRA",
        "086": "IOT",
        "092": "VGB",
        "096": "BRN",
        "100": "BGR",
        "854": "BFA",
        "108": "BDI",
        "132": "CPV",
        "116": "KHM",
        "120": "CMR",
        "124": "CAN",
        "136": "CYM",
        "140": "CAF",
        "148": "TCD",
        "152": "CHL",
        "156": "CHN",
        "344": "HKG",
        "446": "MAC",
        "162": "CXR",
        "166": "CCK",
        "170": "COL",
        "174": "COM",
        "178": "COG",
        "184": "COK",
        "188": "CRI",
        "384": "CIV",
        "191": "HRV",
        "192": "CUB",
        "531": "CUW",
        "196": "CYP",
        "203": "CZE",
        "408": "PRK",
        "180": "COD",
        "208": "DNK",
        "262": "DJI",
        "212": "DMA",
        "214": "DOM",
        "218": "ECU",
        "818": "EGY",
        "222": "SLV",
        "226": "GNQ",
        "232": "ERI",
        "233": "EST",
        "748": "SWZ",
        "231": "ETH",
        "238": "FLK",
        "234": "FRO",
        "242": "FJI",
        "246": "FIN",
        "250": "FRA",
        "254": "GUF",
        "258": "PYF",
        "260": "ATF",
        "266": "GAB",
        "270": "GMB",
        "268": "GEO",
        "276": "DEU",
        "288": "GHA",
        "292": "GIB",
        "300": "GRC",
        "304": "GRL",
        "308": "GRD",
        "312": "GLP",
        "316": "GUM",
        "320": "GTM",
        "831": "GGY",
        "324": "GIN",
        "624": "GNB",
        "328": "GUY",
        "332": "HTI",
        "334": "HMD",
        "336": "VAT",
        "340": "HND",
        "348": "HUN",
        "352": "ISL",
        "356": "IND",
        "360": "IDN",
        "364": "IRN",
        "368": "IRQ",
        "372": "IRL",
        "833": "IMN",
        "376": "ISR",
        "380": "ITA",
        "388": "JAM",
        "392": "JPN",
        "832": "JEY",
        "400": "JOR",
        "398": "KAZ",
        "404": "KEN",
        "296": "KIR",
        "414": "KWT",
        "417": "KGZ",
        "418": "LAO",
        "428": "LVA",
        "422": "LBN",
        "426": "LSO",
        "430": "LBR",
        "434": "LBY",
        "438": "LIE",
        "440": "LTU",
        "442": "LUX",
        "450": "MDG",
        "454": "MWI",
        "458": "MYS",
        "462": "MDV",
        "466": "MLI",
        "470": "MLT",
        "584": "MHL",
        "474": "MTQ",
        "478": "MRT",
        "480": "MUS",
        "175": "MYT",
        "484": "MEX",
        "583": "FSM",
        "492": "MCO",
        "496": "MNG",
        "499": "MNE",
        "500": "MSR",
        "504": "MAR",
        "508": "MOZ",
        "104": "MMR",
        "516": "NAM",
        "520": "NRU",
        "524": "NPL",
        "528": "NLD",
        "540": "NCL",
        "554": "NZL",
        "558": "NIC",
        "562": "NER",
        "566": "NGA",
        "570": "NIU",
        "574": "NFK",
        "807": "MKD",
        "580": "MNP",
        "578": "NOR",
        "512": "OMN",
        "586": "PAK",
        "585": "PLW",
        "591": "PAN",
        "598": "PNG",
        "600": "PRY",
        "604": "PER",
        "608": "PHL",
        "612": "PCN",
        "616": "POL",
        "620": "PRT",
        "630": "PRI",
        "634": "QAT",
        "410": "KOR",
        "498": "MDA",
        "638": "REU",
        "642": "ROU",
        "643": "RUS",
        "646": "RWA",
        "652": "BLM",
        "654": "SHN",
        "659": "KNA",
        "662": "LCA",
        "663": "MAF",
        "666": "SPM",
        "670": "VCT",
        "882": "WSM",
        "674": "SMR",
        "678": "STP",
        "682": "SAU",
        "686": "SEN",
        "688": "SRB",
        "690": "SYC",
        "694": "SLE",
        "702": "SGP",
        "534": "SXM",
        "703": "SVK",
        "705": "SVN",
        "090": "SLB",
        "706": "SOM",
        "710": "ZAF",
        "239": "SGS",
        "728": "SSD",
        "724": "ESP",
        "144": "LKA",
        "275": "PSE",
        "729": "SDN",
        "740": "SUR",
        "744": "SJM",
        "752": "SWE",
        "756": "CHE",
        "760": "SYR",
        "762": "TJK",
        "764": "THA",
        "626": "TLS",
        "768": "TGO",
        "772": "TKL",
        "776": "TON",
        "780": "TTO",
        "788": "TUN",
        "792": "TUR",
        "795": "TKM",
        "796": "TCA",
        "798": "TUV",
        "800": "UGA",
        "804": "UKR",
        "784": "ARE",
        "826": "GBR",
        "834": "TZA",
        "581": "UMI",
        "840": "USA",
        "850": "VIR",
        "858": "URY",
        "860": "UZB",
        "548": "VUT",
        "862": "VEN",
        "704": "VNM",
        "876": "WLF",
        "732": "ESH",
        "887": "YEM",
        "894": "ZMB",
        "716": "ZWE",
    }

    @classmethod
    def _geo_area_code_to_iso3(cls, code: Any) -> Optional[str]:
        """Map UN M49-style geoAreaCode to ISO 3166-1 alpha-3 using _UN_SDG_COUNTRY_CODES keys (zero-padded 3-digit strings)."""
        if code is None or (isinstance(code, float) and pd.isna(code)):
            return None
        try:
            n = int(float(str(code).strip()))
        except (TypeError, ValueError):
            return None
        key = str(n).zfill(3)
        return cls._UN_SDG_COUNTRY_CODES.get(key)

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Load indicator class mappings
        classes_path = project_root() / "src" / "config" / "unsdg_indicator_classes.yaml"
        with open(classes_path, 'r') as f:
            self.indicator_classes = yaml.safe_load(f).get('indicator_classes', {})

    def save_interim(self, df: pd.DataFrame, out_path: Path) -> None:
        """
        Saves the cleaned DataFrame as a CSV file.
        """
        ensure_dir(out_path.parent)
        df.to_csv(out_path, index=False)
    
    def clean_data(self, indicator_data: List) -> pd.DataFrame:
        """
        NOTE: from un_sdg_fetch.py

        Convert UN SDG data from a List of Dictionaries to a structured DataFrame.
        
        Args:
            indicator_data: Response dictionary from /v1/sdg/Indicator/Data endpoint
            
        Returns:
            pandas.DataFrame with the actual indicator values and metadata
        """
        
        if not indicator_data:
            print("### No indicator data found in the response. ###")
            return pd.DataFrame() # Return empty DataFrame if no data

        rows = []
        for record in indicator_data:
            indicator = record.get('indicator', [None])[0]
            
            row = {
                'country_code': record.get('geoAreaCode'),
                'country_name': record.get('geoAreaName'),
                'year': record.get('timePeriodStart'),
                'value': record.get('value'),
                'indicator': indicator,
                'series_code': record.get('series'),
                'nature': record.get('attributes', {}).get('Nature'),
                'reporting_type': record.get('Reporting Type'),
                'age': record.get('Age'),
                'sex': record.get('Sex'),
                'location': record.get('Location'),
                'quantile': record.get('Quantile'),
                'education_level': record.get('Education level'),
            }
            
            # Extract class code and name if this indicator has classes defined
            if indicator and indicator in self.indicator_classes:
                class_config = self.indicator_classes[indicator]
                dimension_field = class_config.get('dimension_field')
                classes = class_config.get('classes', {})
                
                if dimension_field:
                    # Get the class code from the appropriate field
                    if dimension_field == "series_code":
                        class_code = record.get('series')
                    else:
                        # For dimension-based fields like "IHR Capacity"
                        class_code = record.get(dimension_field)
                    
                    # Map class code to human-readable name
                    class_name = classes.get(class_code) if class_code else None
                    
                    row['class_code'] = class_code
                    row['class_name'] = class_name
                else:
                    row['class_code'] = None
                    row['class_name'] = None
            else:
                row['class_code'] = None
                row['class_name'] = None
            
            rows.append(row)

        TerminalOutput.summary("  Extracted", f"{len(rows)} rows")        
        df = pd.DataFrame(rows)

        # Keep only the one series_code we want per indicator (drop all extra series).
        # Note: indicators not listed in _KEEP_SERIES_BY_INDICATOR are dropped here.
        before = len(df)
        expected_series = df["indicator"].map(self._KEEP_SERIES_BY_INDICATOR)
        df = df[expected_series.notna() & (df["series_code"] == expected_series)].copy()
        TerminalOutput.summary("  Series filtered", f"{before} -> {len(df)} rows")
        
        # Convert value to numeric and coerce errors to NaN
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        # Convert year to integer and coerce errors to NaN
        df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')

        iso3 = df['country_code'].map(self._geo_area_code_to_iso3)
        unmapped = iso3.isna() & df['country_code'].notna()
        if unmapped.any():
            raw_sample = df.loc[unmapped, 'country_code'].drop_duplicates().head(15).tolist()
            TerminalOutput.summary(
                "  UN M49 unmapped (dropped)",
                f"{int(unmapped.sum())} rows; sample geoAreaCode: {raw_sample}",
            )
        df['country_code'] = iso3
        df = df.dropna(subset=['country_code'])

        # Sort by country name, indicator, year
        df = df.sort_values(
            ['country_name', 'indicator', 'year'], ascending=[True, True, True]
        ).reset_index(drop=True)

        _ordered_cols = [
            'country_code',
            'country_name',
            'year',
            'value',
            'indicator',
            'series_code',
            'nature',
            'reporting_type',
            'age',
            'sex',
            'location',
            'quantile',
            'education_level',
            'class_code',
            'class_name',
        ]
        df = df[[c for c in _ordered_cols if c in df.columns]]

        # Calculate data quality metrics
        total_records = len(df)
        records_with_values = df['value'].notna().sum()
        countries_count = df['country_name'].nunique()
        year_range = (df['year'].min(), df['year'].max())
        
        # Count data by nature type
        nature_counts = df['nature'].value_counts().to_dict()
        
        # Identify countries with insufficient data for forecasting
        country_data_counts = df.groupby('country_code').size()
        countries_sufficient = (country_data_counts >= 3).sum()
        countries_insufficient = (country_data_counts < 3).sum()
        
        # Set display options
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_colwidth', 45)
        pd.set_option('display.width', 180)
        pd.set_option('display.expand_frame_repr', False)
        
        TerminalOutput.complete("Converted to DataFrame")
        return df

    