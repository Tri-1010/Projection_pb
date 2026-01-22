"""
Script để verify rằng notebook đã sẵn sàng export cohorts
Chạy script này trong notebook để check tất cả requirements
"""

import pandas as pd
from pathlib import Path

print("="*70)
print("🔍 VERIFICATION: Export Cohorts Ready Check")
print("="*70)

# ============================
# 1. CHECK VARIABLES
# ============================

print("\n1️⃣ Checking required variables...")

required_vars = [
    'df_raw',
    'matrices_by_mob',
    'k_raw_by_mob',
    'k_smooth_by_mob',
    'TARGET_MOBS',
]

# alpha_by_mob is optional (can be created from alpha)
optional_vars = [
    'alpha',
    'alpha_by_mob',
]

missing_vars = []
for var in required_vars:
    if var not in globals():
        missing_vars.append(var)
        print(f"   ❌ {var} - NOT FOUND")
    else:
        print(f"   ✅ {var} - OK")

# Check optional alpha variables
alpha_status = None
if 'alpha_by_mob' in globals():
    print(f"   ✅ alpha_by_mob - OK")
    alpha_status = 'alpha_by_mob'
elif 'alpha' in globals():
    print(f"   ✅ alpha - OK (will be converted to alpha_by_mob)")
    alpha_status = 'alpha'
else:
    print(f"   ⚠️  alpha/alpha_by_mob - NOT FOUND (will use default 0.5)")
    alpha_status = 'default'

if missing_vars:
    print(f"\n⚠️  Missing variables: {missing_vars}")
    print("   → Please run all cells in notebook first!")
else:
    print("\n✅ All required variables exist")
    if alpha_status == 'alpha':
        print("   ℹ️  Note: alpha will be auto-converted to alpha_by_mob")

# ============================
# 2. CHECK VINTAGE_DATE
# ============================

print("\n2️⃣ Checking VINTAGE_DATE column...")

if 'df_raw' in globals():
    if 'VINTAGE_DATE' not in df_raw.columns:
        print("   ❌ VINTAGE_DATE column NOT FOUND")
        print("   → Need to create VINTAGE_DATE from DISBURSAL_DATE")
        print("\n   Add this code:")
        print("   " + "="*60)
        print("   from src.config import parse_date_column")
        print("   df_raw['VINTAGE_DATE'] = parse_date_column(df_raw['DISBURSAL_DATE'])")
        print("   " + "="*60)
    else:
        print(f"   ✅ VINTAGE_DATE exists")
        print(f"      Type: {df_raw['VINTAGE_DATE'].dtype}")
        print(f"      Unique dates: {df_raw['VINTAGE_DATE'].nunique()}")
        print(f"      Range: {df_raw['VINTAGE_DATE'].min()} to {df_raw['VINTAGE_DATE'].max()}")
        
        # Check if datetime
        if not pd.api.types.is_datetime64_any_dtype(df_raw['VINTAGE_DATE']):
            print("   ⚠️  VINTAGE_DATE is not datetime type")
            print("   → Converting to datetime...")
            df_raw['VINTAGE_DATE'] = pd.to_datetime(df_raw['VINTAGE_DATE'])
            print("   ✅ Converted to datetime")

# ============================
# 3. CHECK SEGMENT COLUMNS
# ============================

print("\n3️⃣ Checking segment columns...")

if 'df_raw' in globals():
    segment_cols = ['PRODUCT_TYPE', 'RISK_SCORE']
    
    for col in segment_cols:
        if col not in df_raw.columns:
            print(f"   ❌ {col} - NOT FOUND")
        else:
            n_unique = df_raw[col].nunique()
            print(f"   ✅ {col} - OK ({n_unique} unique values)")

# ============================
# 4. CHECK TARGET MONTHS DATA
# ============================

print("\n4️⃣ Checking target months data...")

if 'df_raw' in globals() and 'VINTAGE_DATE' in df_raw.columns:
    target_months = ['2025-10-01', '2025-01-01']
    
    for month in target_months:
        month_dt = pd.to_datetime(month)
        df_month = df_raw[df_raw['VINTAGE_DATE'] == month_dt]
        
        if len(df_month) == 0:
            print(f"   ⚠️  {month}: NO DATA")
        else:
            n_loans = df_month['AGREEMENT_ID'].nunique()
            n_cohorts = df_month.groupby(['PRODUCT_TYPE', 'RISK_SCORE']).ngroups
            print(f"   ✅ {month}: {n_cohorts} cohorts, {n_loans:,} loans")

# ============================
# 5. CHECK EXPORT FUNCTION
# ============================

print("\n5️⃣ Checking export function...")

try:
    from export_cohort_details import export_cohort_forecast_details
    print("   ✅ export_cohort_forecast_details - OK")
except ImportError as e:
    print(f"   ❌ Cannot import export_cohort_forecast_details")
    print(f"      Error: {e}")

# ============================
# 6. CHECK OUTPUT DIRECTORY
# ============================

print("\n6️⃣ Checking output directory...")

output_dir = Path('cohort_details')
if not output_dir.exists():
    print(f"   ⚠️  Directory 'cohort_details' does not exist")
    print(f"   → Creating directory...")
    output_dir.mkdir(exist_ok=True)
    print(f"   ✅ Directory created")
else:
    print(f"   ✅ Directory 'cohort_details' exists")

# ============================
# SUMMARY
# ============================

print("\n" + "="*70)
print("📋 SUMMARY")
print("="*70)

all_checks = [
    ('df_raw' in globals(), "Required variables"),
    ('df_raw' in globals() and 'VINTAGE_DATE' in df_raw.columns, "VINTAGE_DATE column"),
    ('df_raw' in globals() and 'PRODUCT_TYPE' in df_raw.columns, "Segment columns"),
    ('alpha' in globals() or 'alpha_by_mob' in globals(), "Alpha variable"),
]

passed = sum(1 for check, _ in all_checks if check)
total = len(all_checks)

if passed == total:
    print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
    print("\n🚀 Ready to export cohorts!")
    print("\nNext step:")
    print("   Copy code from 'export_2025_10_and_2025_01.py' to a new cell and run")
else:
    print(f"⚠️  SOME CHECKS FAILED ({passed}/{total})")
    print("\n📝 Please fix the issues above before exporting")

print("="*70)
