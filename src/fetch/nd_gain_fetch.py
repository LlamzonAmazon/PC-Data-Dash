import zipfile
import sys
from pathlib import Path, PurePosixPath

import pandas as pd

# Path to the ND-GAIN ZIP file
ZIP_PATH = Path("data/external/nd_gain_countryindex.zip")

CHUNK_SIZE = 10000

# Get all indicator score.csv files in the ZIP file
def list_indicator_score_files(zip_path: Path):

    # Get all file/folder names in the ZIP file
    with zipfile.ZipFile(zip_path, "r") as zf:
        all_names = zf.namelist()

    # Filter for only indicator score.csv files
    score_files = [
        name for name in all_names
        if name.startswith("resources/indicators/")
        and name.endswith("/score.csv")
    ]

    return score_files

# Load all indicator score.csv files into a single DataFrame
def load_indicator_scores(zip_path: Path):
    frames = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        score_files = list_indicator_score_files(zip_path)

        # Handle empty list of score files by returning empty DataFrame
        if not score_files:
            print("No indicator score.csv files found in the ZIP.")
            return pd.DataFrame()

        for path in score_files:   
            # Break path into parts (directory/files)
            p = PurePosixPath(path)
            try:
                # Index into the indicator name 
                indicator_name = p.parts[2]
            except IndexError:
                print(f"WARNING: Unexpected path structure: {path}")
                continue

            print(f"{indicator_name} data loaded.")

            with zf.open(path) as f:
                # Read data in chunks to avoid memory issues
                chunk_list = []
                for chunk in pd.read_csv(f, chunksize=CHUNK_SIZE):
                    chunk["indicator"] = indicator_name
                    chunk_list.append(chunk)
                
                # Combine chunks into dataframe and add to frames list
                if chunk_list:
                    df = pd.concat(chunk_list, ignore_index=True)
                    frames.append(df)

    # Handle empty list of frames by returning empty DataFrame
    if not frames:
        return pd.DataFrame()

    # Combine all indicator DataFrames
    combined = pd.concat(frames, ignore_index=True)
    return combined

# Print the dataset in a readable format
def print_dataset(df: pd.DataFrame):

    # Handle empty DataFrame
    if df.empty:
        print("No data to display.")
        return

    # Get all indicators (remove duplicates and sort alphabetically)
    indicators = sorted(df["indicator"].unique())
    
    # Summary header
    print("\n" + "="*100)
    print("ND-GAIN INDICATOR SCORE DATA - COMPLETE DATASET".center(100))
    print("="*100)
    print(f"Total Indicators: {len(indicators)}")
    print(f"Total Rows: {df.shape[0]:,}")
    print(f"Total Columns: {df.shape[1]}")
    print("="*100)
    sys.stdout.flush()  # Force output to be written
    
    # Get year columns (all columns except ISO3, Name, indicator)
    year_columns = [col for col in df.columns if col not in ['ISO3', 'Name', 'indicator']]
    year_columns = sorted([col for col in year_columns if col.isdigit()])  # Only numeric year columns
    
    # Display each indicator with all its data
    for idx, indicator in enumerate(indicators, 1):
        try:
            indicator_data = df[df["indicator"] == indicator].copy()
            
            print(f"\n\n{'='*100}")
            print(f"INDICATOR {idx}/{len(indicators)}: {indicator.upper()}".center(100))
            print(f"{'='*100}")
            print(f"Number of Countries: {len(indicator_data)}")
            print(f"Year Range: {year_columns[0]} - {year_columns[-1]} ({len(year_columns)} years)")
            print(f"{'-'*100}")
            sys.stdout.flush()
            
            # Display all countries for this indicator
            for country_idx, (_, row) in enumerate(indicator_data.iterrows(), 1):
                country_name = row['Name']
                country_code = row['ISO3']
                
                print(f"\n  [{country_idx:3d}] {country_name} ({country_code})")
                print(f"      {'-'*94}")
                
                # Display values by year in a readable format
                # Group years into rows for better readability
                years_per_line = 5
                for i in range(0, len(year_columns), years_per_line):
                    year_batch = year_columns[i:i+years_per_line]
                    value_strings = []
                    
                    for year in year_batch:
                        value = row[year]
                        if pd.notna(value):
                            # Format with appropriate decimal places
                            if abs(value) >= 1000:
                                value_str = f"{value:>10.2f}"
                            elif abs(value) >= 1:
                                value_str = f"{value:>10.4f}"
                            else:
                                value_str = f"{value:>10.6f}"
                            value_strings.append(f"{year}: {value_str}")
                        else:
                            value_strings.append(f"{year}: {'N/A':>10}")
                    
                    # Print the line with proper spacing
                    print(f"      {' | '.join(value_strings)}")
            
            print(f"\n{'-'*100}")
            print(f"[OK] Completed: {indicator} ({len(indicator_data)} countries)")
            sys.stdout.flush()  # Force output after each indicator
            
        except Exception as e:
            # Print error to stderr so it's visible even when redirecting stdout
            print(f"\nERROR processing indicator {indicator}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            continue  # Continue with next indicator
    
    print(f"\n\n{'='*100}")
    print("END OF ALL INDICATOR DATA".center(100))
    print(f"{'='*100}\n")
    sys.stdout.flush()

# Handle file not found error
if not ZIP_PATH.exists():
    raise FileNotFoundError(
        f"ZIP not found at {ZIP_PATH}. Download it first or adjust ZIP_PATH."
    )

all_scores = load_indicator_scores(ZIP_PATH)
print_dataset(all_scores)