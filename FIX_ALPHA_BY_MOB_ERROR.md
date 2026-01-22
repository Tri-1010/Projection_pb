# Fix: NameError 'alpha_by_mob' is not defined

## 🐛 Error

```python
NameError: name 'alpha_by_mob' is not defined
```

## 🔍 Root Cause

The notebook creates a single `alpha` value, but the export function expects `alpha_by_mob` (a dictionary with alpha values for each MOB).

**What the notebook creates**:
```python
alpha, k_final_by_mob, _ = fit_alpha(...)
# alpha is a single float value, e.g., 0.8234
```

**What the export function expects**:
```python
alpha_by_mob = {
    0: 0.8234,
    1: 0.8234,
    2: 0.8234,
    # ... one value per MOB
}
```

## ✅ Solution

The code has been updated to automatically create `alpha_by_mob` from the single `alpha` value.

### Updated Code (Already Fixed)

All export files now include this automatic conversion:

```python
# Create alpha_by_mob if it doesn't exist (use single alpha value for all MOBs)
if 'alpha_by_mob' not in globals():
    if 'alpha' in globals():
        # Use single alpha value for all MOBs
        alpha_by_mob = {mob: alpha for mob in k_raw_by_mob.keys()}
        print(f"   ℹ️  Created alpha_by_mob from single alpha value: {alpha:.4f}")
    else:
        # Default alpha = 0.5 if not available
        alpha_by_mob = {mob: 0.5 for mob in k_raw_by_mob.keys()}
        print(f"   ⚠️  Alpha not found, using default: 0.5")
```

## 📝 Files Updated

- ✅ `export_2025_10_and_2025_01.py`
- ✅ `notebook_cell_export_2025_cohorts.py`
- ✅ `get_cohorts_for_months.py`

## 🚀 How to Use

### Option 1: Use Updated Code (Recommended)

Just copy the updated code from any of these files:
- `export_2025_10_and_2025_01.py` (simplest)
- `notebook_cell_export_2025_cohorts.py` (same as above)
- `get_cohorts_for_months.py` (with stats)

The code will automatically handle the conversion.

### Option 2: Manual Fix (If Using Old Code)

If you're using old code, add this before the export call:

```python
# Create alpha_by_mob from single alpha value
if 'alpha' in globals():
    alpha_by_mob = {mob: alpha for mob in k_raw_by_mob.keys()}
    print(f"Created alpha_by_mob from alpha: {alpha:.4f}")
else:
    alpha_by_mob = {mob: 0.5 for mob in k_raw_by_mob.keys()}
    print("Alpha not found, using default: 0.5")
```

## 💡 Understanding Alpha

### What is Alpha?

Alpha is a blending parameter that controls how much to use:
- **K values** (from historical data)
- **Transition matrices** (from current state)

**Formula**: `Final_K = alpha * K_smooth + (1 - alpha) * K_from_matrix`

### Why Single Alpha?

In the Final_Workflow, a single alpha value is fitted for all MOBs because:
1. Simpler model
2. More stable
3. Easier to interpret
4. Usually sufficient for forecasting

### Alpha by MOB

Some workflows (like Projection_done) fit different alpha values for each MOB:
```python
alpha_by_mob = {
    0: 0.75,
    1: 0.82,
    2: 0.79,
    # ... different value per MOB
}
```

This is more flexible but also more complex.

## 🎯 What the Fix Does

The fix converts:

**From** (single value):
```python
alpha = 0.8234
```

**To** (dictionary):
```python
alpha_by_mob = {
    0: 0.8234,
    1: 0.8234,
    2: 0.8234,
    3: 0.8234,
    # ... same value for all MOBs
}
```

This makes it compatible with the export function while preserving the single-alpha approach.

## ✅ Verification

After running the updated code, you should see:

```
📤 Exporting X cohorts...
   ℹ️  Created alpha_by_mob from single alpha value: 0.8234
```

This confirms the conversion happened successfully.

## 🔄 For Future Reference

### If You See This Error Again

1. **Check if you're using updated code**
   - Updated files have the automatic conversion
   - Look for "Create alpha_by_mob if it doesn't exist" comment

2. **Verify alpha exists**
   - Run: `print(f"Alpha: {alpha}")`
   - Should show a value like `Alpha: 0.8234`

3. **Check k_raw_by_mob exists**
   - Run: `print(f"MOBs: {list(k_raw_by_mob.keys())}")`
   - Should show list like `MOBs: [0, 1, 2, 3, ...]`

4. **If still fails**
   - Check that all cells in notebook were run
   - Verify no errors in previous cells
   - Try "Kernel → Restart & Run All"

## 📚 Related Files

- `export_2025_10_and_2025_01.py` - Main export code (FIXED)
- `notebook_cell_export_2025_cohorts.py` - Notebook template (FIXED)
- `get_cohorts_for_months.py` - Alternative code (FIXED)
- `FIX_VINTAGE_DATE_ERROR.md` - Other common error
- `verify_export_ready.py` - Verification script

---

**Date**: 2026-01-19  
**Status**: ✅ Fixed  
**Error**: NameError: name 'alpha_by_mob' is not defined  
**Solution**: Auto-convert single alpha to alpha_by_mob dictionary

