"""
Code để lấy tất cả cohorts cho tháng 2025-10 và 2025-01
Copy và paste vào notebook Final_Workflow copy
"""

# ============================================================
# LẤY TẤT CẢ COHORTS CHO THÁNG 2025-10 VÀ 2025-01
# ============================================================

import pandas as pd
from src.config import parse_date_column

print("="*60)
print("🔍 TÌM TẤT CẢ COHORTS CHO THÁNG 2025-10 VÀ 2025-01")
print("="*60)

# ============================
# 0. TẠO VINTAGE_DATE NẾU CHƯA CÓ
# ============================

if 'VINTAGE_DATE' not in df_raw.columns:
    print("⚠️  Creating VINTAGE_DATE from DISBURSAL_DATE...")
    df_raw['VINTAGE_DATE'] = parse_date_column(df_raw['DISBURSAL_DATE'])
    print("✅ VINTAGE_DATE created")
else:
    # Ensure datetime format
    df_raw['VINTAGE_DATE'] = pd.to_datetime(df_raw['VINTAGE_DATE'])

# ============================
# 1. DEFINE TARGET MONTHS
# ============================

target_months = ['2025-10-01', '2025-01-01']

print(f"\n📅 Target months: {target_months}")

# ============================
# 2. TÌM TẤT CẢ COHORTS
# ============================

all_cohorts = []

for month in target_months:
    month_dt = pd.to_datetime(month)
    
    # Filter data for this month
    df_month = df_raw[df_raw['VINTAGE_DATE'] == month_dt]
    
    if len(df_month) == 0:
        print(f"\n⚠️  No data for {month}")
        continue
    
    # Get all unique combinations of (Product, Risk_Score)
    cohorts_month = df_month.groupby(['PRODUCT_TYPE', 'RISK_SCORE']).agg({
        'AGREEMENT_ID': 'nunique',
        'DISBURSAL_AMOUNT': 'sum',
    }).reset_index()
    
    cohorts_month.columns = ['Product', 'Risk_Score', 'N_Loans', 'Total_Disbursement']
    cohorts_month['Vintage_Date'] = month
    
    # Sort by N_Loans descending
    cohorts_month = cohorts_month.sort_values('N_Loans', ascending=False)
    
    print(f"\n📊 {month}: Found {len(cohorts_month)} cohorts")
    print(f"   Total loans: {cohorts_month['N_Loans'].sum():,}")
    print(f"   Total disbursement: {cohorts_month['Total_Disbursement'].sum():,.2f}")
    
    # Add to list
    for _, row in cohorts_month.iterrows():
        all_cohorts.append((
            row['Product'],
            row['Risk_Score'],
            row['Vintage_Date']
        ))

print(f"\n{'='*60}")
print(f"✅ TỔNG CỘNG: {len(all_cohorts)} cohorts")
print(f"{'='*60}")

# ============================
# 3. SHOW TOP COHORTS
# ============================

print(f"\n📋 TOP 20 COHORTS (by N_Loans):")
print("="*60)

# Create summary dataframe
summary_data = []
for product, score, vintage in all_cohorts:
    vintage_dt = pd.to_datetime(vintage)
    mask = (
        (df_raw['PRODUCT_TYPE'] == product) &
        (df_raw['RISK_SCORE'] == score) &
        (df_raw['VINTAGE_DATE'] == vintage_dt)
    )
    n_loans = df_raw[mask]['AGREEMENT_ID'].nunique()
    total_disb = df_raw[mask]['DISBURSAL_AMOUNT'].sum()
    
    summary_data.append({
        'Product': product,
        'Risk_Score': score,
        'Vintage': vintage,
        'N_Loans': n_loans,
        'Total_Disb': total_disb,
    })

df_summary = pd.DataFrame(summary_data)
df_summary = df_summary.sort_values('N_Loans', ascending=False)

print(df_summary.head(20).to_string(index=False))

# ============================
# 4. EXPORT ALL COHORTS
# ============================

print(f"\n{'='*60}")
print(f"📤 EXPORT ALL COHORTS")
print(f"{'='*60}")

from export_cohort_details import export_cohort_forecast_details

# Export all cohorts
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
print(f"📊 Total cohorts: {len(all_cohorts)}")
print(f"\n💡 File chứa:")
print(f"   - Summary: Tổng quan {len(all_cohorts)} cohorts")
print(f"   - TM_*: Transition matrices")
print(f"   - K_Values: K raw, K smooth, Alpha")
print(f"   - Actual_*: Dữ liệu thực tế")
print(f"   - Forecast_Steps: Chi tiết từng bước tính")
print(f"   - Instructions: Hướng dẫn sử dụng")
print(f"\n🎯 Sẵn sàng gửi cho sếp!")
print(f"{'='*60}")

# ============================
# 5. SAVE COHORT LIST TO CSV
# ============================

# Save cohort list for reference
df_summary.to_csv('cohort_details/cohort_list_2025_10_and_2025_01.csv', index=False)
print(f"\n📝 Cohort list saved to: cohort_details/cohort_list_2025_10_and_2025_01.csv")
