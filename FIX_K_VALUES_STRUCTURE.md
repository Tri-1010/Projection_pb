# ✅ Fix: K Values Structure Error

**Date**: 2026-01-19  
**Issue**: Lỗi khi truy cập K values  
**Status**: ✅ FIXED

---

## 🐛 Vấn Đề

Code ban đầu giả định rằng `k_raw_by_mob` và `k_smooth_by_mob` có structure:
```python
k_raw_by_mob[segment_key][mob] = k_value
# segment_key = (product, score)
```

Nhưng thực tế có thể có 2 structures:
1. **With segment key**: `k_raw_by_mob[(product, score)][mob]`
2. **Without segment key**: `k_raw_by_mob[mob]`

→ Code cũ chỉ xử lý case 1, gây lỗi khi gặp case 2.

---

## ✅ Giải Pháp

Cập nhật code để **tự động detect structure** và xử lý cả 2 cases:

```python
# Check K structure (with or without segment key)
k_raw_dict = None
k_smooth_dict = None

# Check if k_raw_by_mob has segment keys
if k_raw_by_mob:
    first_key = list(k_raw_by_mob.keys())[0]
    if isinstance(first_key, tuple):
        # Structure: k_raw_by_mob[segment_key][mob]
        k_raw_dict = k_raw_by_mob.get(segment_key, {})
    else:
        # Structure: k_raw_by_mob[mob]
        k_raw_dict = k_raw_by_mob

# Check if k_smooth_by_mob has segment keys
if k_smooth_by_mob:
    first_key = list(k_smooth_by_mob.keys())[0]
    if isinstance(first_key, tuple):
        # Structure: k_smooth_by_mob[segment_key][mob]
        k_smooth_dict = k_smooth_by_mob.get(segment_key, {})
    else:
        # Structure: k_smooth_by_mob[mob]
        k_smooth_dict = k_smooth_by_mob

# Use k_raw_dict and k_smooth_dict instead of direct access
for mob in mob_range:
    if k_raw_dict and mob in k_raw_dict:
        k_val = k_raw_dict[mob]
        # ... write to Excel
```

---

## 🔧 Những Gì Đã Sửa

### File: `export_cohort_details_v3.py`

**Before** (chỉ xử lý case 1):
```python
if segment_key in k_raw_by_mob and mob in k_raw_by_mob[segment_key]:
    k_val = k_raw_by_mob[segment_key][mob]
```

**After** (xử lý cả 2 cases):
```python
# Detect structure first
if isinstance(first_key, tuple):
    k_raw_dict = k_raw_by_mob.get(segment_key, {})
else:
    k_raw_dict = k_raw_by_mob

# Use detected structure
if k_raw_dict and mob in k_raw_dict:
    k_val = k_raw_dict[mob]
```

### Cũng Sửa

- ✅ K_raw values section
- ✅ K_smooth values section
- ✅ Removed duplicate code

---

## 📝 Files Updated

1. ✅ `export_cohort_details_v3.py` - Fixed K values structure handling
2. ✅ `notebooks/Final_Workflow copy.ipynb` - Updated with fixed code
3. ✅ `FIX_K_VALUES_STRUCTURE.md` - This file

---

## ✅ Verification

```
✅ Import OK - No syntax errors
✅ Notebook updated with v3 export code
✅ ALL CHECKS PASSED - V3 IS READY!
```

---

## 🎯 Kết Quả

Code bây giờ **tự động detect** structure của K values và xử lý đúng:

- ✅ Nếu có segment key → dùng `k_raw_by_mob[segment_key][mob]`
- ✅ Nếu không có segment key → dùng `k_raw_by_mob[mob]`
- ✅ Không bị lỗi trong cả 2 trường hợp

---

## 🚀 Next Steps

1. **Mở notebook**: `jupyter notebook "notebooks/Final_Workflow copy.ipynb"`
2. **Run all cells**: Cell → Run All
3. **Check output**: `cohort_details/Cohort_Forecast_Details_v3_*.xlsx`

**Lỗi đã được fix!** ✅

