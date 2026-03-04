
from typing import Dict, Any, List, Optional
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
                'country': record.get('geoAreaName'),
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
        # Sort by country (ascending), indicator (ascending), then by year (ascending)
        df = df.sort_values(['country', 'indicator', 'year'], ascending=[True, True, True]).reset_index(drop=True)
        
        # Calculate data quality metrics
        total_records = len(df)
        records_with_values = df['value'].notna().sum()
        countries_count = df['country'].nunique()
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

    