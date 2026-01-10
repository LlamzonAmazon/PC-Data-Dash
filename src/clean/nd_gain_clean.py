
from typing import Dict, Any, List

class NDGAINClean(DataCleaner):
    """
    Clean ND-GAIN data
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def clean_data(self, indicator_data: List[Dict[str, Any]]) -> pd.DataFrame:
            """
            NOTE: from nd_gain_fetch.py 

            Convert ND-GAIN raw data to a structured, tidy DataFrame.
            Transforms wide format (years as columns) to long format (year as a column).
            
            Args:
                indicator_data (List[Dict[str, Any]]): Raw data from ZIP file as list of dictionaries
                
            Returns:
                pd.DataFrame: Tidy DataFrame with columns: country_code, country, indicator, year, value
            """
            if not indicator_data:
                print("### No indicator data found in the records. ###")
                return pd.DataFrame()
            
            print("Converting ND-GAIN data to tidy format...")
            
            # Convert list of dicts back to DataFrame
            raw_data = pd.DataFrame(indicator_data)
            
            # Identify year columns (numeric columns representing years)
            year_columns = [col for col in raw_data.columns 
                        if col not in ['ISO3', 'Name', 'indicator'] and str(col).isdigit()]
            
            # Melt the DataFrame from wide to long format
            df_long = raw_data.melt(
                id_vars=['ISO3', 'Name', 'indicator'],
                value_vars=year_columns,
                var_name='year',
                value_name='value'
            )
            
            # Rename columns to match standard schema
            df_long = df_long.rename(columns={
                'ISO3': 'country_code',
                'Name': 'country'
            })
            
            # Convert data types
            df_long['year'] = pd.to_numeric(df_long['year'], errors='coerce').astype('Int64')
            df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
            
            # Remove rows with missing values
            df_long = df_long.dropna(subset=['value'])
            
            # Sort by country, indicator, and year
            df_long = df_long.sort_values(['country_code', 'indicator', 'year']).reset_index(drop=True)
            
            # Reorder columns for consistency with other clients
            df_long = df_long[['country_code', 'country', 'indicator', 'year', 'value']]
            
            print(f"Extracted {len(df_long)} rows.")
            print("Converted to Pandas DataFrame.")
            return df_long
