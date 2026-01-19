"""
Code đơn giản nhất để export tất cả cohorts tháng 2025-10 và 2025-01
Copy toàn bộ code này vào 1 cell mới trong notebook Final_Workflow copy
"""

# ============================================================
# EXPORT TẤT CẢ COHORTS THÁNG 2025-10 VÀ 2025-01
# ============================================================

from export_cohort_details import export_cohort_forecast_details
import pandas as pd

print("="*60)
print("📊 EXPORT COHORTS: 2025-10 và 2025-01")
print("="*60)

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
    
    # Get all (Product, Risk_Score) combinations
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
# 2. EXPORT
# ============================

if len(all_cohorts) > 0:
    print(f"\n📤 Exporting {len(all_cohorts)} cohorts...")
    
    filename = export_cohort_forecast_details(
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
    print(f"🎯 Sẵn sàng gửi cho sếp!")
    print(f"{'='*60}")
else:
    print(f"\n❌ Không tìm thấy cohorts")
