# ✅ Fix: KeyError 'BUCKET'

**Date**: 2026-01-19  
**Error**: `KeyError: 'BUCKET'`  
**Status**: ✅ FIXED

---

## 🐛 Vấn Đề

Code đang dùng hardcoded column names:
```python
df_current['BUCKET']  # ❌ Column không tồn tại
df_current['PRINCIPLE_OUTSTANDING']  # ❌ Có thể khác tên
df_current['AGREEMENT_ID']  # ❌ Có thể khác tên
df_current['MOB']  # ❌ Có thể khác tên
```

**Lỗi**: `KeyError: 'BUCKET'` vì column thực tế là `STATE` (không phải `BUCKET`)

---

## ✅ Giải Pháp

Sử dụng **column names từ CFG** thay vì hardcode:

```python
# Get column names from config
from src.config import CFG

state_col = CFG.get("state", "STATE")  # Thường là "STATE"
ead_col = CFG.get("ead", "PRINCIPLE_OUTSTANDING")
loan_col = CFG.get("loan", "AGREEMENT_ID")
mob_col = CFG.get("mob", "MOB")

# Use config column names
df_current[df_current[state_col] == bucket][ead_col].sum()
df_current[df_current[state_col] == bucket][loan_col].nunique()
df_cohort[mob_col].max()
```

---

## 🔧 Những Gì Đã Sửa

### File: `export_cohort_details_v3.py`

**Before** (hardcoded):
```python
balance = df_current[df_current['BUCKET'] == bucket]['PRINCIPLE_OUTSTANDING'].sum()
n_loans = df_current[df_current['BUCKET'] == bucket]['AGREEMENT_ID'].nunique()
current_mob = df_cohort['MOB'].max()
```

**After** (from config):
```python
# At function start
state_col = CFG.get("state", "STATE")
ead_col = CFG.get("ead", "PRINCIPLE_OUTSTANDING")
loan_col = CFG.get("loan", "AGREEMENT_ID")
mob_col = CFG.get("mob", "MOB")

# Use config names
balance = df_current[df_current[state_col] == bucket][ead_col].sum()
n_loans = df_current[df_current[state_col] == bucket][loan_col].nunique()
current_mob = df_cohort[mob_col].max()
```

---

## 📝 Sections Fixed

1. ✅ **Function initialization** - Get column names from CFG
2. ✅ **Current MOB calculation** - Use `mob_col`
3. ✅ **Current balance calculation** - Use `state_col` and `ead_col`
4. ✅ **Number of loans calculation** - Use `state_col` and `loan_col`
5. ✅ **Summary sheet** - Use all config column names

---

## 🎯 Lợi Ích

### 1. Flexible ✅
Code hoạt động với bất kỳ column names nào được define trong CFG

### 2. No Hardcoding ✅
Không còn hardcode column names → dễ maintain

### 3. Config-Driven ✅
Tất cả column names đều từ `src/config.py` → single source of truth

### 4. Backward Compatible ✅
Có default values nếu CFG không có key:
```python
CFG.get("state", "STATE")  # Default to "STATE" if not in CFG
```

---

## 📚 Column Names Mapping

| Purpose | CFG Key | Default Value | Actual Column |
|---------|---------|---------------|---------------|
| State/Bucket | `state` | `STATE` | `STATE` |
| Balance/EAD | `ead` | `PRINCIPLE_OUTSTANDING` | `PRINCIPLE_OUTSTANDING` |
| Loan ID | `loan` | `AGREEMENT_ID` | `AGREEMENT_ID` |
| MOB | `mob` | `MOB` | `MOB` |

---

## ✅ Verification

```bash
python -c "from export_cohort_details_v3 import export_cohort_forecast_details_v3; print('✅ Import OK')"
```

Output:
```
✅ Import OK
```

---

## 🚀 Next Steps

1. **Mở notebook**: `jupyter notebook "notebooks/Final_Workflow copy.ipynb"`
2. **Run all cells**: Cell → Run All
3. **Check output**: `cohort_details/Cohort_Forecast_Details_v3_*.xlsx`

**Lỗi BUCKET đã được fix!** ✅

---

## 💡 Lưu Ý

Nếu gặp lỗi tương tự với column khác, check `src/config.py`:

```python
CFG = dict(
    loan="AGREEMENT_ID",
    mob="MOB",
    state="STATE",  # ← This is the bucket/state column
    ead="PRINCIPLE_OUTSTANDING",
    # ... other columns
)
```

Đảm bảo column names trong CFG match với columns trong df_raw.

