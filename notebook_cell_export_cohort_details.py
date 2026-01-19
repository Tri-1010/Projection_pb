"""
Cell mẫu để add vào Final_Workflow copy notebook
Copy và paste vào notebook sau khi đã build model
"""

# ============================================================
# EXPORT CHI TIẾT FORECAST CHO SPECIFIC COHORTS
# ============================================================

from export_cohort_details import export_cohort_forecast_details

print("="*60)
print("📊 EXPORT CHI TIẾT FORECAST CHO SẾP")
print("="*60)

# ============================
# 1. DEFINE COHORTS CẦN EXPORT
# ============================

# Ví dụ: Export các cohorts gần đây và có volume lớn
cohorts = [
    # Product X - Recent vintages
    ('X', 'A', '2025-10-01'),
    ('X', 'B', '2025-10-01'),
    ('X', 'C', '2025-10-01'),
    
    # Product X - Older vintages (for comparison)
    ('X', 'A', '2024-10-01'),
    ('X', 'B', '2024-10-01'),
    
    # Product T - Recent vintages
    ('T', 'A', '2025-10-01'),
    ('T', 'B', '2025-10-01'),
]

print(f"\n📋 Cohorts to export: {len(cohorts)}")
for product, score, vintage in cohorts:
    print(f"   - {product}, {score}, {vintage}")

# ============================
# 2. VERIFY COHORTS TỒN TẠI
# ============================

print(f"\n🔍 Verifying cohorts...")

valid_cohorts = []
for product, score, vintage_date in cohorts:
    vintage_dt = pd.to_datetime(vintage_date)
    
    mask = (
        (df_raw['PRODUCT_TYPE'] == product) &
        (df_raw['RISK_SCORE'] == score) &
        (df_raw['VINTAGE_DATE'] == vintage_dt)
    )
    
    n_loans = df_raw[mask]['AGREEMENT_ID'].nunique()
    
    if n_loans > 0:
        print(f"   ✅ {product}, {score}, {vintage_date}: {n_loans:,} loans")
        valid_cohorts.append((product, score, vintage_date))
    else:
        print(f"   ⚠️  {product}, {score}, {vintage_date}: No data")

print(f"\n✅ Valid cohorts: {len(valid_cohorts)}/{len(cohorts)}")

# ============================
# 3. EXPORT
# ============================

if len(valid_cohorts) > 0:
    print(f"\n📤 Exporting...")
    
    filename = export_cohort_forecast_details(
        cohorts=valid_cohorts,
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
    print(f"📊 Cohorts: {len(valid_cohorts)}")
    print(f"\n💡 File này chứa:")
    print(f"   1. Summary: Tổng quan các cohorts")
    print(f"   2. TM_*: Transition matrices")
    print(f"   3. K_Values: K raw, K smooth, Alpha")
    print(f"   4. Actual_*: Dữ liệu thực tế")
    print(f"   5. Forecast_Steps: Chi tiết từng bước tính")
    print(f"   6. Instructions: Hướng dẫn sử dụng")
    print(f"\n🎯 Sẵn sàng gửi cho sếp!")
    print(f"{'='*60}")
else:
    print(f"\n❌ Không có cohorts hợp lệ để export")

# ============================
# 4. QUICK PREVIEW
# ============================

# Preview một cohort để verify
if len(valid_cohorts) > 0:
    product, score, vintage_date = valid_cohorts[0]
    
    print(f"\n📊 PREVIEW: {product}, {score}, {vintage_date}")
    print("="*60)
    
    # Get actual data
    vintage_dt = pd.to_datetime(vintage_date)
    mask = (
        (df_raw['PRODUCT_TYPE'] == product) &
        (df_raw['RISK_SCORE'] == score) &
        (df_raw['VINTAGE_DATE'] == vintage_dt)
    )
    df_cohort = df_raw[mask]
    
    max_mob = df_cohort['MOB'].max()
    
    print(f"Current MOB: {max_mob}")
    print(f"Target MOB: {TARGET_MOBS[0] if isinstance(TARGET_MOBS, list) else TARGET_MOBS}")
    print(f"Forecast steps: {(TARGET_MOBS[0] if isinstance(TARGET_MOBS, list) else TARGET_MOBS) - max_mob}")
    
    # Get forecast result
    target_mob = TARGET_MOBS[0] if isinstance(TARGET_MOBS, list) else TARGET_MOBS
    
    mask_lc = (
        (df_lifecycle_final['PRODUCT_TYPE'] == product) &
        (df_lifecycle_final['RISK_SCORE'] == score) &
        (df_lifecycle_final['VINTAGE_DATE'] == vintage_dt) &
        (df_lifecycle_final['MOB'] == target_mob)
    )
    
    df_forecast = df_lifecycle_final[mask_lc]
    
    if len(df_forecast) > 0:
        print(f"\nForecast @ MOB {target_mob}:")
        if 'DEL30_PCT' in df_forecast.columns:
            print(f"   DEL30: {df_forecast['DEL30_PCT'].iloc[0]*100:.2f}%")
        if 'DEL60_PCT' in df_forecast.columns:
            print(f"   DEL60: {df_forecast['DEL60_PCT'].iloc[0]*100:.2f}%")
        if 'DEL90_PCT' in df_forecast.columns:
            print(f"   DEL90: {df_forecast['DEL90_PCT'].iloc[0]*100:.2f}%")
    
    print("="*60)
