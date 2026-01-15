"""
Test script to verify EAD_FORECAST is correctly calculated
(should be smaller than EAD_CURRENT due to prepayment/writeoff)
"""

import pandas as pd
import numpy as np
from src.config import BUCKETS_CANON

# ============================================================
# Create sample data
# ============================================================

# 1. Lifecycle forecast (cohort-level)
# Giả sử cohort có 1000 EAD hiện tại, forecast tại MOB 12:
# - DPD0: 600 (60%)
# - DPD30+: 150 (15%)
# - WRITEOFF: 50 (5%) - Đã xóa nợ, không còn EAD
# - PREPAY: 100 (10%) - Đã trả hết, không còn EAD
# Total forecast: 750 (giảm 25% so với hiện tại do writeoff + prepay)

df_lifecycle = pd.DataFrame([{
    'PRODUCT_TYPE': 'SALPIL',
    'RISK_SCORE': 'LOW',
    'VINTAGE_DATE': pd.to_datetime('2024-01-01'),
    'MOB': 12,
    'DPD0': 600,
    'DPD1+': 0,
    'DPD30+': 150,
    'DPD60+': 0,
    'DPD90+': 0,
    'DPD120+': 0,
    'DPD180+': 0,
    'WRITEOFF': 0,  # Writeoff không còn EAD
    'PREPAY': 0,    # Prepay không còn EAD
    'SOLDOUT': 0,
    'IS_FORECAST': 1
}])

# 2. Loan-level data (df_raw)
# 10 loans, mỗi loan có EAD = 100
# Total EAD current = 1000

loans = []
for i in range(10):
    loans.append({
        'AGREEMENT_ID': f'LOAN_{i+1:03d}',
        'PRODUCT_TYPE': 'SALPIL',
        'RISK_SCORE': 'LOW',
        'DISBURSAL_DATE': pd.to_datetime('2024-01-01'),
        'MOB': 1,  # MOB hiện tại
        'PRINCIPLE_OUTSTANDING': 100,  # EAD hiện tại
        'STATE_MODEL': 'DPD0',
        'CUTOFF_DATE': pd.to_datetime('2024-01-31')
    })

df_raw = pd.DataFrame(loans)

print("=" * 70)
print("TEST: EAD_FORECAST CALCULATION")
print("=" * 70)

print("\n1️⃣ Lifecycle forecast (cohort-level):")
print(f"   Total EAD forecast @ MOB 12: {df_lifecycle[BUCKETS_CANON].sum(axis=1).iloc[0]:,.0f}")
print(f"   Breakdown:")
for col in BUCKETS_CANON:
    val = df_lifecycle[col].iloc[0]
    if val > 0:
        print(f"      {col}: {val:,.0f}")

print("\n2️⃣ Loan-level current:")
print(f"   Number of loans: {len(df_raw)}")
print(f"   Total EAD current: {df_raw['PRINCIPLE_OUTSTANDING'].sum():,.0f}")
print(f"   Average EAD per loan: {df_raw['PRINCIPLE_OUTSTANDING'].mean():,.0f}")

print("\n3️⃣ Expected EAD_FORECAST per loan:")
total_ead_forecast = df_lifecycle[BUCKETS_CANON].sum(axis=1).iloc[0]
total_ead_current = df_raw['PRINCIPLE_OUTSTANDING'].sum()
ead_ratio = total_ead_forecast / total_ead_current

print(f"   EAD ratio (forecast/current): {ead_ratio:.4f}")
print(f"   Expected EAD_FORECAST per loan: {100 * ead_ratio:,.2f}")
print(f"   Expected total EAD_FORECAST: {total_ead_current * ead_ratio:,.0f}")

# ============================================================
# Test allocation
# ============================================================

print("\n" + "=" * 70)
print("RUNNING ALLOCATION...")
print("=" * 70)

from src.rollrate.allocation import allocate_forecast_to_loans_simple

df_allocated = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle,
    df_raw=df_raw,
    target_mob=12,
    forecast_only=True
)

# ============================================================
# Verify results
# ============================================================

print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)

if df_allocated.empty:
    print("❌ FAILED: No allocation results")
else:
    print(f"\n1️⃣ Number of loans allocated: {len(df_allocated)}")
    
    print(f"\n2️⃣ EAD comparison:")
    print(f"   EAD_CURRENT (avg): {df_raw['PRINCIPLE_OUTSTANDING'].mean():,.2f}")
    print(f"   EAD_FORECAST (avg): {df_allocated['EAD_FORECAST'].mean():,.2f}")
    
    ead_current_total = df_raw['PRINCIPLE_OUTSTANDING'].sum()
    ead_forecast_total = df_allocated['EAD_FORECAST'].sum()
    
    print(f"\n3️⃣ Total EAD:")
    print(f"   EAD_CURRENT (total): {ead_current_total:,.0f}")
    print(f"   EAD_FORECAST (total): {ead_forecast_total:,.0f}")
    print(f"   Difference: {ead_current_total - ead_forecast_total:,.0f}")
    print(f"   Reduction: {(1 - ead_forecast_total/ead_current_total)*100:.2f}%")
    
    print(f"\n4️⃣ Check if EAD_FORECAST < EAD_CURRENT:")
    
    # Merge để so sánh
    df_compare = df_allocated[[
        'AGREEMENT_ID', 'EAD_FORECAST'
    ]].merge(
        df_raw[['AGREEMENT_ID', 'PRINCIPLE_OUTSTANDING']],
        on='AGREEMENT_ID',
        how='left'
    )
    
    df_compare['EAD_CURRENT'] = df_compare['PRINCIPLE_OUTSTANDING']
    df_compare['DIFF'] = df_compare['EAD_CURRENT'] - df_compare['EAD_FORECAST']
    df_compare['DIFF_PCT'] = (df_compare['DIFF'] / df_compare['EAD_CURRENT'] * 100)
    
    print(df_compare[['AGREEMENT_ID', 'EAD_CURRENT', 'EAD_FORECAST', 'DIFF', 'DIFF_PCT']].head())
    
    # Check
    all_smaller = (df_compare['EAD_FORECAST'] <= df_compare['EAD_CURRENT']).all()
    
    if all_smaller:
        print("\n✅ PASSED: All EAD_FORECAST <= EAD_CURRENT")
    else:
        print("\n❌ FAILED: Some EAD_FORECAST > EAD_CURRENT")
        bad_loans = df_compare[df_compare['EAD_FORECAST'] > df_compare['EAD_CURRENT']]
        print(f"   Number of bad loans: {len(bad_loans)}")
    
    # Check total matches lifecycle
    lifecycle_total = df_lifecycle[BUCKETS_CANON].sum(axis=1).iloc[0]
    allocated_total = df_allocated['EAD_FORECAST'].sum()
    diff = abs(lifecycle_total - allocated_total)
    diff_pct = diff / lifecycle_total * 100
    
    print(f"\n5️⃣ Check total EAD matches lifecycle:")
    print(f"   Lifecycle total: {lifecycle_total:,.0f}")
    print(f"   Allocated total: {allocated_total:,.0f}")
    print(f"   Difference: {diff:,.0f} ({diff_pct:.4f}%)")
    
    if diff_pct < 0.01:
        print("   ✅ PASSED: Total EAD matches (< 0.01% diff)")
    else:
        print("   ❌ FAILED: Total EAD mismatch")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
