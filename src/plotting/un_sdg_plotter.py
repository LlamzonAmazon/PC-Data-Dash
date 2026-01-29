"""
UN SDG Domain 1 (Impact) Plotting Module

This module generates time series plots for Domain 1 indicators organized by sector
and indicator groups. Each group gets its own plot showing all indicator time series
within that group on the same graph.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from src.pipeline.utils import project_root, ensure_dir
from src.plotting.base_plotter import DataPlotter


class UNSDGDomain1Plotter(DataPlotter):
    """
    Plotter for Domain 1 (Impact) UN SDG indicators organized by sector and groups.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the Domain 1 plotter.
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        super().__init__(config_path)
        
        # Sector name to number and abbreviation mapping (for filename generation)
        self.sector_mapping = {
            "Sector 1: Healthcare": {"number": "1", "abbrev": "HC"},
            "Sector 2: Agriculture": {"number": "2", "abbrev": "AG"},
            "Sector 3: Social Infrastructure": {"number": "3", "abbrev": "SI"},
            "Sector 4: Cross-Cutting Themes": {"number": "4", "abbrev": "CC"},
            "Sector 5: Additional Country Considerations": {"number": "5", "abbrev": "AC"}
        }
        
        # Domain 1 indicator mapping: sector -> groups -> indicators
        self.domain1_mapping = {
            "Sector 1: Healthcare": {
                "Resilient primary healthcare (PHC) systems": [
                    {"indicator": "3.8.1", "series_code": "SH_ACS_UNHC_25", "name": "Coverage of essential health services"}
                ],
                "Infectious Disease Control": [
                    {"indicator": "3.3.2", "series_code": "SH_TBS_INCD", "name": "Tuberculosis incidence"},
                    {"indicator": "3.3.3", "series_code": "SH_STA_MALR", "name": "Incidence of malaria"}
                ],
                "Maternal, newborn, and child health": [
                    {"indicator": "3.1.1", "series_code": "SH_STA_MORT", "name": "Maternal Mortality Ratio"},
                    {"indicator": "3.2.1", "series_code": "SH_DYN_MORT", "name": "Under-5 Mortality Ratio"}
                ],
                "Nutrition": [
                    {"indicator": "2.2.1", "series_code": "SH_STA_STNT", "name": "Prevalence of stunting (children <5)"},
                    {"indicator": "2.2.2", "series_code": "SN_STA_OVWGT", "name": "Prevalence of malnutrition (overweight)"},
                    {"indicator": "2.2.3", "series_code": "SH_STA_ANEM", "name": "Prevalence of anemia in women"}
                ],
                "Reproductive health and family planning": [
                    {"indicator": "3.7.1", "series_code": "SH_FPL_MTMM", "name": "Family planning satisfaction"},
                    {"indicator": "3.7.2", "series_code": "SP_DYN_ADKL", "name": "Adolescent birth rate"}
                ],
                "Health risk reduction and management": [
                    {"indicator": "3.d.1", "series_code": "SH_IHR_CAPS", "name": "International Health Regulations (IHR) capacity"}
                ]
            },
            "Sector 2: Agriculture": {
                "Food Security": [
                    {"indicator": "2.1.2", "series_code": "AG_PRD_FIESMS", "name": "Prevalence of moderate/severe food insecurity (FIES)"},
                    {"indicator": "2.4.1", "series_code": "AG_LND_SUSAG", "name": "Agricultural area under sustainable agriculture"}
                ],
                "Agricultural systems and value chain strengthening": [
                    {"indicator": "2.a.2", "series_code": "DC_TOF_AGRL", "name": "Total official flows to the agriculture sector"}
                ]
            },
            "Sector 3: Social Infrastructure": {
                "Water, sanitation, and hygiene (WASH)": [
                    {"indicator": "6.1.1", "series_code": "SH_H2O_SAFE", "name": "Safely managed drinking water services"},
                    {"indicator": "6.2.1", "series_code": "SH_SAN_SAFE", "name": "Safely managed sanitation services"},
                    {"indicator": "3.9.2", "series_code": "SH_STA_WASHARI", "name": "Mortality rate attributed to unsafe water/sanitation"}
                ],
                "Off-grid power": [
                    {"indicator": "7.1.1", "series_code": "EG_ACS_ELEC", "name": "Access to electricity"},
                    {"indicator": "7.1.2", "series_code": "EG_EGY_CLEAN", "name": "Primary reliance on clean fuels (cooking/heating)"},
                    {"indicator": "7.2.1", "series_code": "EG_FEC_RNEW", "name": "Renewable energy share"}
                ],
                "Digital financial inclusion": [
                    {"indicator": "8.10.2", "series_code": "FB_CBK_ACCT", "name": "Account ownership at a bank or mobile-money provider"}
                ]
            },
            "Sector 4: Cross-Cutting Themes": {
                "Women's Empowerment": [
                    # Gender Inequality Index (GII) / UNDP - not in UN SDG data
                    {"indicator": None, "series_code": None, "name": "Gender Inequality Index (GII) - Not available in UN SDG data"}
                ],
                "Climate Adaptation": [
                    # ND-GAIN Vulnerability Index / ND - not in UN SDG data
                    {"indicator": None, "series_code": None, "name": "ND-GAIN Vulnerability Index - Not available in UN SDG data"}
                ]
            },
            "Sector 5: Additional Country Considerations": {
                "Poverty": [
                    {"indicator": "1.2.1", "series_code": "SI_POV_NAHC", "name": "Population below national poverty line"}
                ],
                "Demographics": [
                    # Population Density - World Bank data, not UN SDG
                    {"indicator": None, "series_code": None, "name": "Population Density - Not available in UN SDG data"}
                ]
            }
        }
        
        # Set data paths
        self.data_path = self.root / "data" / "interim" / "un_sdg_interim.csv"
    
    def load_data(self) -> pd.DataFrame:
        """
        Load UN SDG interim data from CSV.
        
        Returns:
            DataFrame with UN SDG data
        """
        if self.data is None:
            self.log.info(f"Loading UN SDG data from {self.data_path}")
            self.data = pd.read_csv(self.data_path)
            self.log.info(f"Loaded {len(self.data)} rows")
        return self.data
    
    def filter_by_country(self, country: str) -> pd.DataFrame:
        """
        Filter data for a specific country.
        
        Args:
            country: Country name or country code to filter by
            
        Returns:
            Filtered DataFrame for the specified country
        """
        if self.data is None:
            self.load_data()
        
        # Try filtering by country name first, then by country code
        country_data = self.data[
            (self.data['country'].str.contains(country, case=False, na=False)) |
            (self.data['country_code'].astype(str) == str(country))
        ].copy()
        
        if len(country_data) == 0:
            self.log.warning(f"No data found for country: {country}")
        else:
            self.log.info(f"Filtered to {len(country_data)} rows for country: {country}")
            # Get the actual country name from the data
            actual_country = country_data['country'].iloc[0]
            self.log.info(f"Using country name: {actual_country}")
        
        self.country_data = country_data
        return country_data
    
    def get_indicator_data(self, indicator: str, series_code: Optional[str] = None) -> pd.DataFrame:
        """
        Extract data for a specific indicator and series code combination.
        
        Args:
            indicator: Indicator code (e.g., "3.8.1")
            series_code: Series code (e.g., "SH_ACS_UNHC_25")
            
        Returns:
            DataFrame with filtered data, sorted by year
        """
        if self.country_data is None:
            raise ValueError("Must filter by country first using filter_by_country()")
        
        if indicator is None:
            return pd.DataFrame()
        
        # Filter by indicator
        filtered = self.country_data[
            (self.country_data['indicator'] == indicator)
        ].copy()
        
        # If series_code is provided, filter by it as well
        if series_code is not None:
            filtered = filtered[filtered['series_code'] == series_code].copy()
        
        # Sort by year
        filtered = filtered.sort_values('year').reset_index(drop=True)
        
        return filtered
    
    def plot_group(self, group_name: str, indicators: List[Dict[str, Any]], 
                   country_name: str, sector_name: str) -> Optional[plt.Figure]:
        """
        Create a single plot for an indicator group showing all indicator time series.
        
        Args:
            group_name: Name of the indicator group
            indicators: List of indicator dictionaries with 'indicator', 'series_code', 'name'
            country_name: Name of the country being plotted
            sector_name: Name of the sector (for title context)
            
        Returns:
            matplotlib Figure object, or None if no data available
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        has_data = False
        colors = plt.cm.tab10(range(len(indicators)))
        linestyles = ['-', '--', '-.', ':'][:len(indicators)]
        
        for idx, ind_info in enumerate(indicators):
            indicator = ind_info.get('indicator')
            series_code = ind_info.get('series_code')
            name = ind_info.get('name', f"{indicator} / {series_code}")
            
            # Skip if indicator/series_code is None (not available)
            if indicator is None or series_code is None:
                continue
            
            data = self.get_indicator_data(indicator, series_code)
            
            if len(data) == 0:
                self.log.warning(f"No data for {indicator} / {series_code} in group {group_name}")
                continue
            
            # Filter out NaN values
            data_clean = data[data['value'].notna()].copy()
            
            if len(data_clean) == 0:
                self.log.warning(f"No valid values for {indicator} / {series_code} in group {group_name}")
                continue
            
            has_data = True
            
            # Plot the time series
            ax.plot(data_clean['year'], data_clean['value'], 
                   label=f"{indicator} - {name}",
                   color=colors[idx], linestyle=linestyles[idx % len(linestyles)],
                   marker='o', markersize=4, linewidth=2)
        
        if not has_data:
            plt.close(fig)
            self.log.warning(f"No data available for group: {group_name}")
            return None
        
        # Formatting
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title(f"{group_name}\n{country_name} - {sector_name}", fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(left=ax.get_xlim()[0] - 1, right=ax.get_xlim()[1] + 1)
        
        plt.tight_layout()
        return fig
    
    def plot_sector(self, sector_name: str, sector_groups: Dict[str, List[Dict[str, Any]]], 
                   country_name: str) -> List[Path]:
        """
        Generate all group plots for a sector.
        
        Args:
            sector_name: Name of the sector
            sector_groups: Dictionary mapping group names to indicator lists
            country_name: Name of the country being plotted
            
        Returns:
            List of paths to saved plot files
        """
        saved_paths = []
        
        for group_name, indicators in sector_groups.items():
            fig = self.plot_group(group_name, indicators, country_name, sector_name)
            
            if fig is None:
                continue
            
            # Create output directory
            sanitized_country = country_name.replace(' ', '_').replace('/', '_')
            sanitized_group = group_name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace(',', '')
            
            # Get sector number and abbreviation for filename
            sector_info = self.sector_mapping.get(sector_name, {"number": "?", "abbrev": "?"})
            sector_num = sector_info["number"]
            sector_abbrev = sector_info["abbrev"]
            
            output_dir = self.get_output_base("domain1") / sanitized_country
            ensure_dir(output_dir)
            
            # Save plot with format: {sector_number}_{sector_abbrev}_{group_name}.png
            filename = f"{sector_num}_{sector_abbrev}_{sanitized_group}.png"
            filepath = output_dir / filename
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            saved_paths.append(filepath)
            self.log.info(f"Saved plot: {filepath}")
        
        return saved_paths
    
    def plot_domain(self, country: str, domain: str = "domain1") -> Dict[str, List[Path]]:
        """
        Main method to plot all Domain 1 sectors for a country.
        Implements the abstract method from DataPlotter.
        
        Args:
            country: Country name or code to plot
            domain: Domain identifier (should be "domain1" for this plotter)
            
        Returns:
            Dictionary mapping sector names to lists of saved plot file paths
        """
        if domain != "domain1":
            self.log.warning(f"This plotter only supports domain1, but received: {domain}")
        
        # Load and filter data
        self.load_data()
        country_data = self.filter_by_country(country)
        
        if len(country_data) == 0:
            self.log.error(f"Cannot plot: No data found for country {country}")
            return {}
        
        country_name = country_data['country'].iloc[0]
        self.log.info(f"Plotting Domain 1 data for: {country_name}")
        
        # Plot each sector
        all_plots = {}
        
        for sector_name, sector_groups in self.domain1_mapping.items():
            self.log.info(f"Plotting sector: {sector_name}")
            saved_paths = self.plot_sector(sector_name, sector_groups, country_name)
            all_plots[sector_name] = saved_paths
        
        self.log.info(f"Completed plotting Domain 1 for {country_name}")
        return all_plots
    
    def plot_domain1(self, country: str) -> Dict[str, List[Path]]:
        """
        Convenience method for backward compatibility.
        Delegates to plot_domain().
        
        Args:
            country: Country name or code to plot
            
        Returns:
            Dictionary mapping sector names to lists of saved plot file paths
        """
        return self.plot_domain(country, "domain1")


def main():
    """
    Example usage of the Domain1Plotter.
    """
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    
    # Create plotter using factory (or directly for backward compatibility)
    from src.plotting.plot_factory import DataPlotterFactory
    
    factory = DataPlotterFactory()
    plotter = factory.create_plotter('unsdg', 'domain1')
    
    if len(sys.argv) > 1:
        country = sys.argv[1]
    else:
        country = "Afghanistan"  # Default for testing
    
    plots = plotter.plot_domain(country, "domain1")
    
    print(f"\nGenerated {sum(len(paths) for paths in plots.values())} plots for {country}")
    for sector, paths in plots.items():
        print(f"  {sector}: {len(paths)} plots")


if __name__ == "__main__":
    main()
