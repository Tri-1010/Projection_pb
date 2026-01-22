# 🎯 Next Steps: Export Cohorts 2025-10 và 2025-01

## ✅ Current Status

**FIXED**: KeyError 'VINTAGE_DATE' đã được fix hoàn toàn.

**Code đã sẵn sàng**:
- ✅ `export_2025_10_and_2025_01.py` - Code đơn giản nhất
- ✅ `get_cohorts_for_months.py` - Code đầy đủ với stats
- ✅ `export_cohort_details.py` - Main export function
- ✅ `verify_export_ready.py` - Script kiểm tra trước khi export

---

## 🚀 Cách Sử Dụng (3 Bước)

### Bước 1: Mở Notebook

```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

### Bước 2: Chạy Tất Cả Cells

Click: **Cell → Run All**

Hoặc: **Kernel → Restart & Run All**

### Bước 3: Verify & Export

#### 3a. Verify (Optional nhưng recommended)

Add cell mới và chạy:

```python
%run verify_export_ready.py
```

Nếu tất cả checks pass → Tiếp tục bước 3b

Nếu có lỗi → Fix theo hướng dẫn trong output

#### 3b. Export Cohorts

Add cell mới và copy code từ `export_2025_10_and_2025_01.py`:

```python
from export_cohort_details import export_cohort_forecast_details
import pandas as pd
from src.config import parse_date_column

print("="*60)
print("📊 EXPORT COHORTS: 2025-10 và 2025-01")
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
```

---

## 📊 Output

**File**: `cohort_details/Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx`

**Sheets**:
1. **Summary** - Tổng quan tất cả cohorts
2. **TM_*** - Transition matrices by segment
3. **K_Values** - K raw, K smooth, Alpha values
4. **Actual_*** - Dữ liệu thực tế by segment
5. **Forecast_Steps** - Chi tiết từng bước tính forecast
6. **Instructions** - Hướng dẫn sử dụng

---

## 🔧 Troubleshooting

### Lỗi: KeyError 'VINTAGE_DATE'

**Nguyên nhân**: VINTAGE_DATE chưa được tạo

**Giải pháp**: Code đã có sẵn phần tạo VINTAGE_DATE (section 0 trong code export)

### Lỗi: No data for 2025-10-01

**Nguyên nhân**: Không có data cho tháng này

**Giải pháp**: 
- Check data range: `df_raw['VINTAGE_DATE'].min()` và `.max()`
- Thay đổi `target_months` thành tháng có data

### Lỗi: MemoryError

**Nguyên nhân**: Quá nhiều cohorts

**Giải pháp**:
- Export từng tháng riêng biệt
- Hoặc filter top N cohorts (by số lượng loans)

---

## 💡 Customization

### Thay Đổi Tháng

```python
# Lấy 1 tháng
target_months = ['2025-10-01']

# Lấy nhiều tháng
target_months = ['2025-10-01', '2025-09-01', '2025-08-01']

# Lấy tháng khác
target_months = ['2024-12-01', '2024-11-01']
```

### Filter Top N Cohorts

```python
# Sau khi tìm all_cohorts, filter top 20
# Get cohort sizes
cohort_sizes = []
for product, score, vintage in all_cohorts:
    vintage_dt = pd.to_datetime(vintage)
    mask = (
        (df_raw['PRODUCT_TYPE'] == product) &
        (df_raw['RISK_SCORE'] == score) &
        (df_raw['VINTAGE_DATE'] == vintage_dt)
    )
    n_loans = df_raw[mask]['AGREEMENT_ID'].nunique()
    cohort_sizes.append((product, score, vintage, n_loans))

# Sort by size and take top 20
cohort_sizes.sort(key=lambda x: x[3], reverse=True)
all_cohorts = [(p, s, v) for p, s, v, _ in cohort_sizes[:20]]

print(f"Filtered to top 20 cohorts")
```

### Export Từng Tháng Riêng

```python
# Export 2025-10
cohorts_2025_10 = [(p, s, v) for p, s, v in all_cohorts if v == '2025-10-01']
filename_10 = export_cohort_forecast_details(
    cohorts=cohorts_2025_10,
    # ... other params
)

# Export 2025-01
cohorts_2025_01 = [(p, s, v) for p, s, v in all_cohorts if v == '2025-01-01']
filename_01 = export_cohort_forecast_details(
    cohorts=cohorts_2025_01,
    # ... other params
)
```

---

## 📚 Related Files

### Main Files
- `export_2025_10_and_2025_01.py` - **USE THIS** - Code đơn giản nhất
- `export_cohort_details.py` - Main export function
- `verify_export_ready.py` - Verification script

### Documentation
- `README_EXPORT_COHORTS_2025.md` - Quick start guide
- `FIX_VINTAGE_DATE_ERROR.md` - VINTAGE_DATE fix explanation
- `HOW_TO_USE_EXPORT_COHORT.md` - Detailed usage guide
- `GUIDE_EXPORT_COHORT_DETAILS.md` - Export function guide

### Alternative Code
- `get_cohorts_for_months.py` - Code với stats chi tiết
- `SIMPLE_CODE_GET_ALL_COHORTS.md` - Nhiều options khác nhau

---

## ✅ Checklist

Trước khi export:

- [ ] Đã mở notebook `Final_Workflow copy.ipynb`
- [ ] Đã chạy tất cả cells (Cell → Run All)
- [ ] (Optional) Đã chạy `verify_export_ready.py` và pass tất cả checks
- [ ] Đã copy code từ `export_2025_10_and_2025_01.py` vào cell mới
- [ ] Đã chạy cell export
- [ ] Đã check output file trong folder `cohort_details/`

---

## 🎯 Expected Result

```
============================================================
📊 EXPORT COHORTS: 2025-10 và 2025-01
============================================================
✅ VINTAGE_DATE created

2025-10-01:
  Cohorts: 15
  Loans: 12,345

2025-01-01:
  Cohorts: 18
  Loans: 15,678

============================================================
✅ Total cohorts: 33
============================================================

📤 Exporting 33 cohorts...

============================================================
✅ HOÀN THÀNH!
============================================================
📄 File: cohort_details/Cohort_Forecast_Details_20260119_143022.xlsx
📊 Cohorts: 33
🎯 Sẵn sàng gửi cho sếp!
============================================================
```

---

**Date**: 2026-01-19  
**Status**: ✅ Ready to use  
**Last Update**: Fixed VINTAGE_DATE error, code is clean and tested

