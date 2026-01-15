"""
Test script to verify IS_FORECAST column is preserved through aggregation
"""
import pandas as pd
import numpy as np

# Create sample data with IS_FORECAST column
data = {
    'PRODUCT_TYPE': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B'],
    'RISK_SCORE': ['LOW', 'LOW', 'HIGH', 'HIGH', 'LOW', 'LOW', 'HIGH', 'HIGH'],
    'VINTAGE_DATE': ['2024-01', '2024-01', '2024-01', '2024-01', '2024-01', '2024-01', '2024-01', '2024-01'],
    'MOB': [1, 1, 1, 1, 1, 1, 1, 1],
    'DISB_TOTAL': [1000, 1000, 500, 500, 800, 800, 600, 600],
    'DEL30_PCT': [0.05, 0.10, 0.08, 0.12, 0.06, 0.11, 0.09, 0.13],
    'DEL60_PCT': [0.03, 0.06, 0.05, 0.08, 0.04, 0.07, 0.06, 0.09],
    'DEL90_PCT': [0.01, 0.03, 0.02, 0.04, 0.02, 0.04, 0.03, 0.05],
    'IS_FORECAST': [0, 1, 0, 1, 0, 1, 0, 1]
}

df = pd.DataFrame(data)

print("=" * 60)
print("BEFORE AGGREGATION")
print("=" * 60)
print(f"Total rows: {len(df)}")
print(f"Actual rows (IS_FORECAST=0): {(df['IS_FORECAST']==0).sum()}")
print(f"Forecast rows (IS_FORECAST=1): {(df['IS_FORECAST']==1).sum()}")
print("\nSample data:")
print(df[['PRODUCT_TYPE', 'RISK_SCORE', 'MOB', 'IS_FORECAST', 'DEL30_PCT']].head(8))

# Import the fixed function
from src.rollrate.lifecycle import aggregate_to_product

# Test aggregation
df_agg = aggregate_to_product(df)

print("\n" + "=" * 60)
print("AFTER AGGREGATION")
print("=" * 60)
print(f"Total rows: {len(df_agg)}")

if 'IS_FORECAST' in df_agg.columns:
    print(f"✅ IS_FORECAST column preserved!")
    print(f"Actual rows (IS_FORECAST=0): {(df_agg['IS_FORECAST']==0).sum()}")
    print(f"Forecast rows (IS_FORECAST=1): {(df_agg['IS_FORECAST']==1).sum()}")
    print("\nAggregated data:")
    print(df_agg[['PRODUCT_TYPE', 'MOB', 'IS_FORECAST', 'DEL30_PCT', 'PRODUCT_DISB']])
else:
    print("❌ IS_FORECAST column LOST during aggregation!")
    print("\nAvailable columns:")
    print(df_agg.columns.tolist())

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
