# 🚀 Quick Start: Export Cohorts 2025-10 & 2025-01

## ⚡ 3 Steps Only

### 1️⃣ Open Notebook
```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

### 2️⃣ Run All Cells
Click: **Cell → Run All**

### 3️⃣ Add & Run Export Cell

**Option A**: Copy from file
```python
%load export_2025_10_and_2025_01.py
```
Then run the cell.

**Option B**: Copy-paste
Open `export_2025_10_and_2025_01.py`, copy all content, paste into new cell, run.

**Option C**: Use template
Open `notebook_cell_export_2025_cohorts.py`, copy all, paste, run.

---

## ✅ Done!

Output: `cohort_details/Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx`

---

## 🔍 Verify First (Optional)

Before step 3, add this cell:
```python
%run verify_export_ready.py
```

If all checks pass → Continue to step 3

---

## 💡 Change Target Months

In the export code, change this line:
```python
target_months = ['2025-10-01', '2025-01-01']  # ← Change here
```

Examples:
```python
# 1 month only
target_months = ['2025-10-01']

# 3 months
target_months = ['2025-10-01', '2025-09-01', '2025-08-01']

# Different months
target_months = ['2024-12-01', '2024-11-01']
```

---

## 📚 More Info

- **Complete Guide**: `GUIDE_NEXT_STEPS.md`
- **Status**: `STATUS_EXPORT_COHORTS.md`
- **Error Fix**: `FIX_VINTAGE_DATE_ERROR.md`
- **Detailed Usage**: `HOW_TO_USE_EXPORT_COHORT.md`

---

## 🆘 Troubleshooting

### No data for month?
```python
# Check available months
df_raw['VINTAGE_DATE'].value_counts().head(20)
```

### Too many cohorts?
See "Filter Top N Cohorts" in `GUIDE_NEXT_STEPS.md`

### Memory error?
Export months separately (see guide)

---

**That's it!** Simple and fast. 🎉

