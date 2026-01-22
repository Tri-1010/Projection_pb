"""
Code export cohorts - V4
- Tất cả cohorts trong 1 sheet
- Mỗi cohort cách nhau 2 dòng trống
- Layout: Current + K + Transition Matrix
"""

# ============================================================
# EXPORT TẤT CẢ COHORTS THÁNG 2025-10 VÀ 2025-01 (V4)
# ============================================================

from export_cohort_details_v4 import export_cohort_forecast_details_v4
import pandas as pd
from src.config import parse_date_column

print("="*60)
print("📊 EXPORT COHORTS V4: 2025-10 và 2025-01")
print("   Layout: 1 sheet, mỗi cohort cách 2 dòng")
print("="*60)

# ============================
# 0. TẠO VINTAGE_DATE NẾU CHƯA CÓ
# ============================

if 'VINTAGE_DATE' not in df_raw.columns:
    print("⚠️  Creating VINTAGE_DATE from DISBURSAL_DATE...")
    df_raw['VINTAGE_DATE'] = parse_date_column(df_raw['DISBURSAL_DATE'])
    print("✅ VINTAGE_DATE created")
else:
    df_raw['VINTAGE_DATE'] = pd.to_datetime(df_raw['VINTAGE_DATE'])

# ============================
# 1. TÌM TẤT CẢ COHORTS
# ============================

target_months = ['2025-10-01', '2025-01-01']
all_cohorts = []

for month in target_months:
    month_dt = pd.to_datetime(month)
    df_month = df_raw[df_raw['VINTAGE_DATE'] == month_dt]
    
    if len(df_month) == 0:
        print(f"⚠️  No data for {month}")
        continue
    
    cohorts = df_month.groupby(['PRODUCT_TYPE', 'RISK_SCORE'])['AGREEMENT_ID'].nunique()
    
    print(f"\n{month}:")
    print(f"  Cohorts: {len(cohorts)}")
    print(f"  Loans: {cohorts.sum():,}")
    
    for (product, score), n_loans in cohorts.items():
        all_cohorts.append((product, score, month))

print(f"\n{'='*60}")
print(f"✅ Total cohorts: {len(all_cohorts)}")
print(f"{'='*60}")

# ============================
# 2. EXPORT (V4 - SINGLE SHEET)
# ============================

if len(all_cohorts) > 0:
    print(f"\n📤 Exporting {len(all_cohorts)} cohorts (v4 - single sheet)...")
    
    # Create alpha_by_mob if it doesn't exist
    if 'alpha_by_mob' not in globals():
        if 'alpha' in globals():
            alpha_by_mob = {mob: alpha for mob in k_raw_by_mob.keys()}
            print(f"   ℹ️  Created alpha_by_mob from single alpha: {alpha:.4f}")
        else:
            alpha_by_mob = {mob: 0.5 for mob in k_raw_by_mob.keys()}
            print(f"   ⚠️  Alpha not found, using default: 0.5")
    
    filename = export_cohort_forecast_details_v4(
        cohorts=all_cohorts,
        df_raw=df_raw,
        matrices_by_mob=matrices_by_mob,
        k_raw_by_mob=k_raw_by_mob,
        k_smooth_by_mob=k_smooth_by_mob,
        alpha_by_mob=alpha_by_mob,
        target_mob=TARGET_MOBS[0] if isinstance(TARGET_MOBS, list) else TARGET_MOBS,
        output_dir='cohort_details',
    )
    
    print(f"\n{'='*60}")
    print(f"✅ HOÀN THÀNH!")
    print(f"{'='*60}")
    print(f"📄 File: {filename}")
    print(f"📊 Cohorts: {len(all_cohorts)}")
    print(f"\n💡 Layout V4:")
    print(f"   - 1 sheet duy nhất (All_Cohorts)")
    print(f"   - Mỗi cohort cách nhau 2 dòng")
    print(f"   - Có đầy đủ: Current + K + Transition Matrix")
    print(f"\n🎯 Sẵn sàng gửi cho sếp!")
    print(f"{'='*60}")
else:
    print(f"\n❌ Không tìm thấy cohorts")
