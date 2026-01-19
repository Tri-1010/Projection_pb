# Export Cohorts Tháng 2025-10 và 2025-01

## 🚀 Cách Nhanh Nhất (3 Bước)

### Bước 1: Mở notebook
```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

### Bước 2: Chạy tất cả cells
Click: **Cell → Run All**

### Bước 3: Add cell mới và chạy

Copy code từ file `export_2025_10_and_2025_01.py` vào cell mới:

```python
from export_cohort_details import export_cohort_forecast_details
import pandas as pd

print("="*60)
print("📊 EXPORT COHORTS: 2025-10 và 2025-01")
print("="*60)

# Tìm tất cả cohorts
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

print(f"\n✅ Total cohorts: {len(all_cohorts)}")

# Export
if len(all_cohorts) > 0:
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

## 📊 Output

**File**: `cohort_details/Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx`

**Chứa**:
- Tất cả cohorts của tháng 2025-10
- Tất cả cohorts của tháng 2025-01
- Chi tiết: Transition matrices, K values, Actual data, Forecast steps

---

## 💡 Nếu Muốn Thay Đổi Tháng

Sửa dòng này:

```python
target_months = ['2025-10-01', '2025-01-01']  # Thay đổi tháng ở đây
```

Ví dụ:
```python
# Lấy 3 tháng
target_months = ['2025-10-01', '2025-09-01', '2025-08-01']

# Lấy 1 tháng
target_months = ['2025-10-01']

# Lấy tháng khác
target_months = ['2024-12-01', '2024-11-01']
```

---

## 🔍 Xem Trước Số Lượng Cohorts

Trước khi export, chạy code này để xem có bao nhiêu cohorts:

```python
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
```

---

## 📚 Files Liên Quan

- `export_2025_10_and_2025_01.py` - Code đơn giản nhất
- `SIMPLE_CODE_GET_ALL_COHORTS.md` - Nhiều options khác nhau
- `get_cohorts_for_months.py` - Code đầy đủ với stats
- `export_cohort_details.py` - Main function

---

**Date**: 2026-01-18  
**Status**: ✅ Ready to use
