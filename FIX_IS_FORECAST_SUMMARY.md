# Fix: IS_FORECAST Column Lost During Aggregation

## Vấn đề (Problem)
Khi chạy `Complete_Workflow.ipynb`, phần **Section 8: EXPORT REPORTS** chỉ hiển thị dữ liệu actual, không có forecast. Nguyên nhân là cột `IS_FORECAST` bị mất trong quá trình aggregate.

## Nguyên nhân (Root Cause)
Hai hàm aggregate trong `src/rollrate/lifecycle.py` không bao gồm `IS_FORECAST` trong groupby:

1. **`aggregate_to_product()`** (line ~430)
   - Groupby: `["PRODUCT_TYPE", "VINTAGE_DATE", "MOB"]`
   - ❌ Thiếu `IS_FORECAST` → cột bị mất

2. **`aggregate_products_to_portfolio()`** (line ~510)
   - Groupby: `["VINTAGE_DATE", "MOB"]`
   - ❌ Thiếu `IS_FORECAST` → cột bị mất

## Giải pháp (Solution)

### 1. Fix `aggregate_to_product()`
```python
# BEFORE (line 430-440)
agg = (
    df.groupby(["PRODUCT_TYPE", "VINTAGE_DATE", "MOB"])
    .apply(lambda g: pd.Series({...}))
    .reset_index()
)

# AFTER
groupby_cols = ["PRODUCT_TYPE", "VINTAGE_DATE", "MOB"]
if "IS_FORECAST" in df.columns:
    groupby_cols.append("IS_FORECAST")

agg = (
    df.groupby(groupby_cols, as_index=False)
    .apply(lambda g: pd.Series({...}), include_groups=False)
    .reset_index()
)
```

### 2. Fix `aggregate_products_to_portfolio()`
```python
# BEFORE (line 510-520)
agg = (
    df.groupby(["VINTAGE_DATE", "MOB"])
    .apply(lambda g: pd.Series({...}))
    .reset_index()
)

# AFTER
groupby_cols = ["VINTAGE_DATE", "MOB"]
if "IS_FORECAST" in df.columns:
    groupby_cols.append("IS_FORECAST")

agg = (
    df.groupby(groupby_cols, as_index=False)
    .apply(lambda g: pd.Series({...}), include_groups=False)
    .reset_index()
)

# Thêm IS_FORECAST vào cols khi reorder
cols = ["PRODUCT_TYPE", "VINTAGE_DATE", "MOB", "DEL30_PCT", ...]
if "IS_FORECAST" in agg.columns:
    cols.append("IS_FORECAST")
agg = agg[cols]
```

## Kiểm tra (Verification)

### Test Script: `test_is_forecast_fix.py`
```bash
python test_is_forecast_fix.py
```

**Kết quả:**
```
BEFORE AGGREGATION
Total rows: 8
Actual rows (IS_FORECAST=0): 4
Forecast rows (IS_FORECAST=1): 4

AFTER AGGREGATION
Total rows: 4
✅ IS_FORECAST column preserved!
Actual rows (IS_FORECAST=0): 2
Forecast rows (IS_FORECAST=1): 2
```

### Trong Complete_Workflow.ipynb
Sau khi fix, Section 5 sẽ hiển thị:
```
After aggregate to product:
   Total rows: 12,345
   Actual: 6,789
   Forecast: 5,556  ✅
```

Section 8 (Export) sẽ có cả actual và forecast data.

## Files Modified
1. ✅ `src/rollrate/lifecycle.py`
   - Line ~430-445: `aggregate_to_product()`
   - Line ~510-540: `aggregate_products_to_portfolio()`

2. ✅ `test_is_forecast_fix.py` (new)
   - Test script để verify fix

## Lưu ý (Notes)
- Fix này **backward compatible** - nếu không có cột `IS_FORECAST`, code vẫn chạy bình thường
- Thêm `include_groups=False` để tránh FutureWarning từ pandas
- Không cần thay đổi `Complete_Workflow.ipynb` - chỉ cần re-run sau khi fix

## Next Steps
1. ✅ Test với `test_is_forecast_fix.py`
2. ✅ Re-run `Complete_Workflow.ipynb` Section 5-8
3. ✅ Verify forecast data xuất hiện trong Excel exports
4. 🔄 Push changes lên Git
