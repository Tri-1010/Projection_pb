# Fix: KeyError 'VINTAGE_DATE'

## 🐛 Lỗi

```
KeyError: 'VINTAGE_DATE'
```

## 🔍 Nguyên Nhân

`VINTAGE_DATE` chưa được tạo trong `df_raw`. Column này cần được tạo từ `DISBURSAL_DATE`.

## ✅ Giải Pháp

### Thêm code này TRƯỚC KHI sử dụng VINTAGE_DATE:

```python
from src.config import parse_date_column

# Tạo VINTAGE_DATE nếu chưa có
if 'VINTAGE_DATE' not in df_raw.columns:
    print("⚠️  Creating VINTAGE_DATE from DISBURSAL_DATE...")
    df_raw['VINTAGE_DATE'] = parse_date_column(df_raw['DISBURSAL_DATE'])
    print("✅ VINTAGE_DATE created")
else:
    # Ensure datetime format
    df_raw['VINTAGE_DATE'] = pd.to_datetime(df_raw['VINTAGE_DATE'])
```

## 📝 Code Đã Fix

### File: export_2025_10_and_2025_01.py

```python
from export_cohort_details import export_cohort_forecast_details
import pandas as pd
from src.config import parse_date_column  # ← ADD THIS

print("="*60)
print("📊 EXPORT COHORTS: 2025-10 và 2025-01")
print("="*60)

# ============================
# 0. TẠO VINTAGE_DATE NẾU CHƯA CÓ  ← ADD THIS SECTION
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
    
    # ... rest of code
```

## 🎯 Cách Sử Dụng Trong Notebook

### Bước 1: Chạy cells load data

Chạy các cells:
1. Load data
2. Create segment columns

### Bước 2: Add cell tạo VINTAGE_DATE

```python
from src.config import parse_date_column

# Tạo VINTAGE_DATE
if 'VINTAGE_DATE' not in df_raw.columns:
    print("Creating VINTAGE_DATE...")
    df_raw['VINTAGE_DATE'] = parse_date_column(df_raw['DISBURSAL_DATE'])
    print(f"✅ VINTAGE_DATE created: {df_raw['VINTAGE_DATE'].nunique()} unique dates")
else:
    print("✅ VINTAGE_DATE already exists")
    df_raw['VINTAGE_DATE'] = pd.to_datetime(df_raw['VINTAGE_DATE'])
```

### Bước 3: Verify

```python
# Check VINTAGE_DATE
print("VINTAGE_DATE info:")
print(f"  Type: {df_raw['VINTAGE_DATE'].dtype}")
print(f"  Unique values: {df_raw['VINTAGE_DATE'].nunique()}")
print(f"  Min: {df_raw['VINTAGE_DATE'].min()}")
print(f"  Max: {df_raw['VINTAGE_DATE'].max()}")
print(f"\nSample values:")
print(df_raw['VINTAGE_DATE'].value_counts().head(10))
```

### Bước 4: Chạy export code

Bây giờ có thể chạy code export cohorts.

## 🔧 Files Đã Fix

- ✅ `export_2025_10_and_2025_01.py`
- ✅ `get_cohorts_for_months.py`
- ✅ `SIMPLE_CODE_GET_ALL_COHORTS.md`
- ✅ `README_EXPORT_COHORTS_2025.md`

## 💡 Lưu Ý

### parse_date_column() làm gì?

```python
def parse_date_column(col):
    """
    Convert YYYYMM (int) hoặc datetime string thành datetime.
    
    Examples:
        202510 → 2025-10-01
        '2025-10-15' → 2025-10-15
    """
    if pd.api.types.is_integer_dtype(col):
        # YYYYMM format
        return pd.to_datetime(col.astype(str), format='%Y%m')
    else:
        # Already datetime or string
        return pd.to_datetime(col)
```

### Tại sao cần VINTAGE_DATE?

`VINTAGE_DATE` là ngày giải ngân (disbursal date) của loan, dùng để:
- Group loans thành cohorts
- Track lifecycle theo vintage
- Forecast theo cohort

## ✅ Checklist

Trước khi chạy export code:

- [ ] Đã load data (`df_raw` exists)
- [ ] Đã create segment columns (`PRODUCT_TYPE`, `RISK_SCORE`)
- [ ] Đã tạo `VINTAGE_DATE` (add code ở trên)
- [ ] Verify `VINTAGE_DATE` có data đúng
- [ ] Chạy export code

---

**Date**: 2026-01-18  
**Status**: ✅ Fixed  
**Error**: KeyError 'VINTAGE_DATE'  
**Solution**: Add `parse_date_column()` to create VINTAGE_DATE
