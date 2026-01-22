# ✅ Fix: Transition Matrix Structure

**Date**: 2026-01-19  
**Issue**: Transition matrices không hiển thị  
**Status**: ✅ FIXED (v2 - with score matching)

---

## 🐛 Vấn Đề

1. Code cũ giả định structure sai
2. Score key có thể là string hoặc type khác → cần flexible matching

**Structure thực tế** (từ `compute_transition_by_mob`):
```python
matrices_by_mob[product][mob][score] = {
    "P": DataFrame,  # Ma trận transition
    "is_fallback": bool,
    "reason": str
}
```

---

## ✅ Giải Pháp (v2)

1. Truy cập đúng structure: `matrices_by_mob[product][mob][score]['P']`
2. Flexible score matching: thử cả original type và string conversion
3. Debug output để track issues

```python
# Flexible score matching
score_str = str(score)
score_key = None

if score in product_matrices[mob]:
    score_key = score
elif score_str in product_matrices[mob]:
    score_key = score_str
else:
    for s in product_matrices[mob].keys():
        if str(s) == score_str:
            score_key = s
            break

if score_key:
    tm_entry = product_matrices[mob][score_key]
    if isinstance(tm_entry, dict) and 'P' in tm_entry:
        tm = tm_entry['P']  # ← Lấy DataFrame từ key 'P'
```

---

## 🔧 Files Updated

1. `export_cohort_details_v4.py` - Added flexible score matching + debug output
2. `notebooks/Final_Workflow copy.ipynb` - Added debug section + module reload

---

## 🚀 How to Run

1. **Mở notebook**: `jupyter notebook "notebooks/Final_Workflow copy.ipynb"`
2. **Run all cells**: Cell → Run All
3. **Check debug output**: Xem console để verify structure
4. **Check Excel**: `cohort_details/Cohort_Forecast_Details_v4_*.xlsx`

---

## 📊 Expected Debug Output

```
🔍 DEBUG: matrices_by_mob structure
   Products: ['ProductA', 'ProductB']
   Product 'ProductA': MOBs = [0, 1, 2, 3, 4]...
      MOB 0: Scores = ['ScoreA', 'ScoreB']
      Entry type: <class 'dict'>
      Entry keys: ['P', 'is_fallback', 'reason']
      P shape: (10, 10)
```

---

**Transition matrices should now display correctly!** ✅

