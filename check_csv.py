#!/usr/bin/env python3
"""Comprehensive CSV analysis script."""
import pandas as pd

df = pd.read_csv('data/interim/un_sdg_interim.csv')

print("=" * 80)
print("COMPREHENSIVE CSV ANALYSIS")
print("=" * 80)
print()

# 1. BASIC STATS
print("1. BASIC STATISTICS")
print("-" * 80)
print(f"Total rows: {len(df):,}")
print(f"Total columns: {len(df.columns)}")
print(f"Unique countries: {df['country'].nunique()}")
print(f"Unique indicators: {df['indicator'].nunique()}")
print(f"Year range: {int(df['year'].min())} - {int(df['year'].max())}")
print(f"Indicators: {sorted(df['indicator'].unique())}")
print()

# 2. DUPLICATE CHECK
print("2. DUPLICATE ANALYSIS")
print("-" * 80)
key_cols = ['country_code', 'year', 'indicator', 'series_code']
dupes = df[df.duplicated(subset=key_cols, keep=False)].sort_values(key_cols)

if len(dupes) > 0:
    print(f"❌ FOUND {len(dupes)} DUPLICATE ROWS")
    print(f"   (same country_code/year/indicator/series_code)")
    print()
    print("Breakdown by indicator:")
    dup_counts = dupes.groupby('indicator').size().sort_values(ascending=False)
    for ind, count in dup_counts.items():
        print(f"   {ind}: {count} duplicate rows")
    print()
    print("Sample duplicates (first 10):")
    sample_cols = key_cols + ['value', 'sex', 'age', 'urbanisation', 'location']
    print(dupes[sample_cols].head(10).to_string())
    print()
else:
    print("✅ NO DUPLICATES FOUND")
    print()

# 3. CHECK SPECIFIC INDICATORS
print("3. INDICATOR-SPECIFIC CHECKS")
print("-" * 80)
indicators_to_check = ['2.1.2', '2.2.1', '2.2.2', '2.2.3', '3.2.1', '3.7.2', '3.d.1', '6.1.1', '6.2.1', '7.1.1', '7.1.2']

for ind in indicators_to_check:
    subset = df[df['indicator'] == ind]
    if len(subset) == 0:
        print(f"⚠️  {ind}: NO DATA")
        continue
    
    dupes_sub = subset[subset.duplicated(subset=key_cols, keep=False)]
    has_dupes = len(dupes_sub) > 0
    
    status = "❌ HAS DUPLICATES" if has_dupes else "✅ OK"
    print(f"{status} {ind}: {len(subset):,} rows", end="")
    
    if has_dupes:
        print(f" ({len(dupes_sub)} duplicates)")
        # Show sample
        sample = dupes_sub[key_cols + ['value']].head(3)
        for idx, row in sample.iterrows():
            val = row['value'] if pd.notna(row['value']) else 'NULL'
            print(f"      Sample: {row['country_code']} {row['year']} {row['series_code']} = {val}")
    else:
        print()
print()

# 4. DATA QUALITY
print("4. DATA QUALITY CHECKS")
print("-" * 80)
null_count = df['value'].isna().sum()
print(f"Rows with null values: {null_count:,} ({null_count/len(df)*100:.1f}%)")
print()

# Check for indicators with high null rates
print("Indicators with null values:")
null_by_ind = df.groupby('indicator')['value'].apply(lambda x: x.isna().sum())
null_pct_by_ind = df.groupby('indicator')['value'].apply(lambda x: x.isna().sum() / len(x) * 100)
for ind in sorted(null_by_ind[null_by_ind > 0].index):
    print(f"   {ind}: {null_by_ind[ind]:,} nulls ({null_pct_by_ind[ind]:.1f}%)")
print()

# 5. CHECK 2.1.2 SPECIFICALLY
print("5. 2.1.2 FOOTNOTE DEDUP VERIFICATION")
print("-" * 80)
ind_212 = df[df['indicator'] == '2.1.2']
if len(ind_212) > 0:
    dupes_212 = ind_212[ind_212.duplicated(subset=['country_code', 'year', 'series_code'], keep=False)]
    if len(dupes_212) > 0:
        print(f"❌ 2.1.2 still has {len(dupes_212)} duplicate rows")
        print("   Sample duplicates:")
        sample = dupes_212[['country_code', 'year', 'series_code', 'value']].head(10)
        for idx, row in sample.iterrows():
            val = row['value'] if pd.notna(row['value']) else 'NULL'
            print(f"      {row['country_code']} {row['year']} {row['series_code']} = {val}")
    else:
        print("✅ 2.1.2: No duplicates found")
    
    year_counts = ind_212.groupby('year').size().sort_index()
    print(f"\n   2.1.2 year distribution:")
    print(f"   Years: {int(year_counts.index.min())} - {int(year_counts.index.max())}")
    print(f"   Total years: {len(year_counts)}")
    print(f"   Rows per year (avg): {year_counts.mean():.1f}")
print()

# 6. CHECK DIMENSION FIELDS
print("6. DIMENSION FIELDS")
print("-" * 80)
print(f"Rows with sex populated: {df['sex'].notna().sum():,} ({df['sex'].notna().sum()/len(df)*100:.1f}%)")
print(f"Rows with age populated: {df['age'].notna().sum():,} ({df['age'].notna().sum()/len(df)*100:.1f}%)")
print(f"Rows with urbanisation populated: {df['urbanisation'].notna().sum():,} ({df['urbanisation'].notna().sum()/len(df)*100:.1f}%)")
print(f"Rows with location populated: {df['location'].notna().sum():,} ({df['location'].notna().sum()/len(df)*100:.1f}%)")
print()

# 7. SUMMARY
print("=" * 80)
print("SUMMARY")
print("=" * 80)
total_dupes = len(df[df.duplicated(subset=key_cols, keep=False)])
if total_dupes == 0:
    print("✅ NO DUPLICATES - CSV is clean!")
else:
    print(f"❌ {total_dupes} DUPLICATE ROWS FOUND")
print()
print(f"Total rows: {len(df):,}")
print(f"Unique (country, year, indicator, series) combinations: {df[key_cols].drop_duplicates().shape[0]:,}")
