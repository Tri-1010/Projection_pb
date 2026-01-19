# Code Đơn Giản: Lấy Tất Cả Cohorts Tháng 2025-10 và 2025-01

## 🚀 Copy Code Này Vào Notebook

### Option 1: Export Tất Cả Cohorts (Recommended)

```python
# ============================================================
# LẤY TẤT CẢ COHORTS CHO THÁNG 2025-10 VÀ 2025-01
# ============================================================

from export_cohort_details import export_cohort_forecast_details
import pandas as pd

print("="*60)
print("🔍 TÌM TẤT CẢ COHORTS CHO THÁNG 2025-10 VÀ 2025-01")
print("="*60)

# Target months
target_months = ['2025-10-01', '2025-01-01']

# Find all cohorts
all_cohorts = []

for month in target_months:
    month_dt = pd.to_datetime(month)
    df_month = df_raw[df_raw['VINTAGE_DATE'] == month_dt]
    
    if len(df_month) == 0:
        print(f"⚠️  No data for {month}")
        continue
    
    # Get unique (Product, Risk_Score) combinations
    cohorts = df_month.groupby(['PRODUCT_TYPE', 'RISK_SCORE'])['AGREEMENT_ID'].nunique()
    
    print(f"\n📊 {month}: {len(cohorts)} cohorts, {cohorts.sum():,} loans")
    
    for (product, score), n_loans in cohorts.items():
        all_cohorts.append((product, score, month))

print(f"\n✅ Total: {len(all_cohorts)} cohorts")

# Export
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

print(f"\n✅ Exported: {filename}")
```

---

### Option 2: Chỉ Lấy Top N Cohorts (Nếu Quá Nhiều)

```python
# ============================================================
# LẤY TOP 20 COHORTS CHO THÁNG 2025-10 VÀ 2025-01
# ============================================================

from export_cohort_details import export_cohort_forecast_details
import pandas as pd

print("="*60)
print("🔍 LẤY TOP 20 COHORTS (by N_Loans)")
print("="*60)

# Target months
target_months = ['2025-10-01', '2025-01-01']

# Find all cohorts with stats
cohort_stats = []

for month in target_months:
    month_dt = pd.to_datetime(month)
    df_month = df_raw[df_raw['VINTAGE_DATE'] == month_dt]
    
    if len(df_month) == 0:
        continue
    
    # Get stats for each cohort
    stats = df_month.groupby(['PRODUCT_TYPE', 'RISK_SCORE']).agg({
        'AGREEMENT_ID': 'nunique',
        'DISBURSAL_AMOUNT': 'sum',
    }).reset_index()
    
    stats.columns = ['Product', 'Risk_Score', 'N_Loans', 'Total_Disb']
    stats['Vintage'] = month
    
    cohort_stats.append(stats)

# Combine and sort
df_all = pd.concat(cohort_stats, ignore_index=True)
df_all = df_all.sort_values('N_Loans', ascending=False)

print(f"\nTotal cohorts: {len(df_all)}")
print(f"\nTop 20:")
print(df_all.head(20).to_string(index=False))

# Take top 20
top_cohorts = [
    (row['Product'], row['Risk_Score'], row['Vintage'])
    for _, row in df_all.head(20).iterrows()
]

# Export
filename = export_cohort_forecast_details(
    cohorts=top_cohorts,
    df_raw=df_raw,
    matrices_by_mob=matrices_by_mob,
    k_raw_by_mob=k_raw_by_mob,
    k_smooth_by_mob=k_smooth_by_mob,
    alpha_by_mob=alpha_by_mob,
    target_mob=TARGET_MOBS[0] if isinstance(TARGET_MOBS, list) else TARGET_MOBS,
    output_dir='cohort_details',
)

print(f"\n✅ Exported top 20 cohorts: {filename}")
```

---

### Option 3: Lấy Theo Product

```python
# ============================================================
# LẤY TẤT CẢ COHORTS CHO PRODUCT C VÀ S
# ============================================================

from export_cohort_details import export_cohort_forecast_details
import pandas as pd

# Target months and products
target_months = ['2025-10-01', '2025-01-01']
target_products = ['C', 'S']  # Thay đổi theo data của bạn

all_cohorts = []

for month in target_months:
    for product in target_products:
        month_dt = pd.to_datetime(month)
        
        df_filter = df_raw[
            (df_raw['VINTAGE_DATE'] == month_dt) &
            (df_raw['PRODUCT_TYPE'] == product)
        ]
        
        if len(df_filter) == 0:
            continue
        
        # Get all risk scores for this product-month
        risk_scores = df_filter['RISK_SCORE'].unique()
        
        print(f"{product} - {month}: {len(risk_scores)} risk scores")
        
        for score in risk_scores:
            all_cohorts.append((product, score, month))

print(f"\n✅ Total: {len(all_cohorts)} cohorts")

# Export
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

print(f"\n✅ Exported: {filename}")
```

---

## 📊 Xem Trước Cohorts

Trước khi export, xem có bao nhiêu cohorts:

```python
# Xem số lượng cohorts
target_months = ['2025-10-01', '2025-01-01']

for month in target_months:
    month_dt = pd.to_datetime(month)
    df_month = df_raw[df_raw['VINTAGE_DATE'] == month_dt]
    
    if len(df_month) > 0:
        n_cohorts = df_month.groupby(['PRODUCT_TYPE', 'RISK_SCORE']).ngroups
        n_loans = df_month['AGREEMENT_ID'].nunique()
        
        print(f"{month}:")
        print(f"  Cohorts: {n_cohorts}")
        print(f"  Loans: {n_loans:,}")
        print()
```

---

## 💡 Tips

### Nếu Có Quá Nhiều Cohorts (>50)

Chọn 1 trong các cách:

1. **Top N by volume**:
```python
# Lấy top 30 cohorts có nhiều loans nhất
top_cohorts = df_all.head(30)
```

2. **Filter by product**:
```python
# Chỉ lấy Product C
cohorts_c = [c for c in all_cohorts if c[0] == 'C']
```

3. **Filter by risk score**:
```python
# Chỉ lấy risk scores A, B, C
cohorts_abc = [c for c in all_cohorts if c[1] in ['A', 'B', 'C']]
```

---

## 🎯 Recommended Approach

**Bước 1**: Xem trước số lượng cohorts

```python
target_months = ['2025-10-01', '2025-01-01']
for month in target_months:
    month_dt = pd.to_datetime(month)
    n = df_raw[df_raw['VINTAGE_DATE'] == month_dt].groupby(['PRODUCT_TYPE', 'RISK_SCORE']).ngroups
    print(f"{month}: {n} cohorts")
```

**Bước 2**: 
- Nếu < 30 cohorts → Dùng **Option 1** (export tất cả)
- Nếu 30-100 cohorts → Dùng **Option 2** (top 20-30)
- Nếu > 100 cohorts → Dùng **Option 3** (filter by product)

---

**Date**: 2026-01-18  
**Ready to use**: ✅
