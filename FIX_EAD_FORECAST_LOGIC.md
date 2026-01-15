# Fix: EAD_FORECAST Logic - Phải nhỏ hơn EAD_CURRENT

## Vấn đề (Problem)

User phát hiện: **EAD_FORECAST_MOB12 = EAD_CURRENT**, nhưng nó phải nhỏ hơn do:
- Prepayment (trả trước)
- Writeoff (xóa nợ)
- Natural amortization (trả nợ theo kỳ hạn)

## Nguyên nhân (Root Cause)

Trong `src/rollrate/allocation.py`, hàm `allocate_forecast_to_loans_simple()` có logic SAI:

### Code CŨ (SAI) ❌

```python
# Line ~445
df_cohort_loans["EAD_FORECAST"] = df_cohort_loans[ead_col]
```

**Vấn đề:**
- Lấy EAD hiện tại (EAD_CURRENT) làm EAD_FORECAST
- Không tính đến prepayment, writeoff
- EAD_FORECAST = EAD_CURRENT → SAI!

## Giải pháp (Solution)

### Code MỚI (ĐÚNG) ✅

```python
# Line ~420-450
# 🔥 Tổng EAD forecast từ lifecycle (tất cả states)
total_ead_forecast = row_lc[BUCKETS_CANON].sum()

# 🔥 Tổng EAD hiện tại của cohort
total_ead_current = df_cohort_loans[ead_col].sum()

# 🔥 FIX: EAD_FORECAST phải tính theo tỷ lệ từ lifecycle forecast
# EAD_FORECAST_loan = EAD_CURRENT_loan * (Total_EAD_Forecast / Total_EAD_Current)
ead_ratio = total_ead_forecast / total_ead_current
df_cohort_loans["EAD_FORECAST"] = df_cohort_loans[ead_col] * ead_ratio
```

**Logic đúng:**
1. Lấy tổng EAD forecast từ lifecycle (cohort-level)
2. Lấy tổng EAD current từ loans (loan-level)
3. Tính tỷ lệ: `ead_ratio = total_ead_forecast / total_ead_current`
4. Phân bổ xuống từng loan: `EAD_FORECAST_loan = EAD_CURRENT_loan * ead_ratio`

## Ví dụ minh họa

### Scenario: Cohort có 10 loans, mỗi loan EAD = 100

**Lifecycle forecast @ MOB 12:**
- DPD0: 600
- DPD30+: 150
- WRITEOFF: 0 (đã xóa nợ, không còn EAD)
- PREPAY: 0 (đã trả hết, không còn EAD)
- **Total EAD forecast: 750**

**Loan-level current:**
- 10 loans × 100 = **1,000 EAD current**

**Tính toán:**
```
ead_ratio = 750 / 1,000 = 0.75
EAD_FORECAST per loan = 100 × 0.75 = 75
```

**Kết quả:**
- EAD_CURRENT = 100
- EAD_FORECAST = 75 ✅
- Reduction = 25% (do prepayment + writeoff)

## Test Results

### Test script: `test_ead_forecast_fix.py`

```bash
python test_ead_forecast_fix.py
```

**Output:**
```
2️⃣ EAD comparison:
   EAD_CURRENT (avg): 100.00
   EAD_FORECAST (avg): 75.00

3️⃣ Total EAD:
   EAD_CURRENT (total): 1,000
   EAD_FORECAST (total): 750
   Difference: 250
   Reduction: 25.00%

4️⃣ Check if EAD_FORECAST < EAD_CURRENT:
✅ PASSED: All EAD_FORECAST <= EAD_CURRENT

5️⃣ Check total EAD matches lifecycle:
   Lifecycle total: 750
   Allocated total: 750
   Difference: 0 (0.0000%)
   ✅ PASSED: Total EAD matches (< 0.01% diff)
```

## Thay đổi chi tiết

### File: `src/rollrate/allocation.py`

#### 1. Xóa phần tính `_PCT` không cần thiết (line ~390)

**Trước:**
```python
# 2️⃣ Tính phân phối state cho mỗi cohort × MOB
df_lc["TOTAL_EAD"] = df_lc[BUCKETS_CANON].sum(axis=1)

for st in BUCKETS_CANON:
    df_lc[f"{st}_PCT"] = df_lc[st] / df_lc["TOTAL_EAD"]
```

**Sau:**
```python
# 2️⃣ Tính tổng EAD cho mỗi cohort × MOB (để tính phân phối state)
df_lc["TOTAL_EAD"] = df_lc[BUCKETS_CANON].sum(axis=1)
```

#### 2. Sửa logic tính EAD_FORECAST (line ~420-450)

**Trước:**
```python
# Phân phối state (xác suất)
state_probs = {st: row_lc[f"{st}_PCT"] for st in BUCKETS_CANON}
...
df_cohort_loans["EAD_FORECAST"] = df_cohort_loans[ead_col]  # ❌ SAI!
```

**Sau:**
```python
# 🔥 Tổng EAD forecast từ lifecycle (tất cả states)
total_ead_forecast = row_lc[BUCKETS_CANON].sum()

# Phân phối state (xác suất)
state_probs = {st: row_lc[st] / total_ead_forecast for st in BUCKETS_CANON}
...

# 🔥 Tổng EAD hiện tại của cohort
total_ead_current = df_cohort_loans[ead_col].sum()

# 🔥 FIX: EAD_FORECAST phải tính theo tỷ lệ từ lifecycle forecast
ead_ratio = total_ead_forecast / total_ead_current
df_cohort_loans["EAD_FORECAST"] = df_cohort_loans[ead_col] * ead_ratio
```

#### 3. Thêm validation (line ~460-480)

```python
# 5️⃣ Validation: Kiểm tra tổng EAD
print("\n✅ Phân bổ hoàn tất. Kiểm tra tổng EAD...")

# Tổng EAD từ lifecycle (cohort-level)
total_ead_lifecycle = df_lc[BUCKETS_CANON].sum().sum()

# Tổng EAD từ allocation (loan-level)
total_ead_allocated = df_result["EAD_FORECAST"].sum()

diff = abs(total_ead_lifecycle - total_ead_allocated)
diff_pct = diff / total_ead_lifecycle * 100 if total_ead_lifecycle > 0 else 0

print(f"  - Tổng EAD lifecycle: {total_ead_lifecycle:,.0f}")
print(f"  - Tổng EAD allocated: {total_ead_allocated:,.0f}")
print(f"  - Chênh lệch: {diff:,.0f} ({diff_pct:.4f}%)")

if diff_pct > 0.01:
    print(f"⚠️ Chênh lệch > 0.01%, có thể do làm tròn hoặc missing loans.")
else:
    print("✅ Tổng EAD khớp (chênh lệch < 0.01%).")
```

## Impact

### Trước fix:
```
EAD_CURRENT = 100
EAD_FORECAST_MOB12 = 100  ❌ SAI
EAD_FORECAST_MOB24 = 100  ❌ SAI
```

### Sau fix:
```
EAD_CURRENT = 100
EAD_FORECAST_MOB12 = 75   ✅ ĐÚNG (giảm 25% do prepay/writeoff)
EAD_FORECAST_MOB24 = 60   ✅ ĐÚNG (giảm 40% do prepay/writeoff)
```

## Lưu ý quan trọng

### 1. EAD_FORECAST có thể = EAD_CURRENT

Trong một số trường hợp đặc biệt:
- Không có prepayment
- Không có writeoff
- Không có amortization
- → EAD_FORECAST = EAD_CURRENT (hợp lệ)

Nhưng thông thường: **EAD_FORECAST < EAD_CURRENT**

### 2. Validation tự động

Sau fix, hàm tự động validate:
- Tổng EAD allocated = Tổng EAD lifecycle
- Nếu chênh lệch > 0.01% → Warning

### 3. Không ảnh hưởng proportional method

Hàm `allocate_forecast_to_loans()` (proportional method) đã đúng từ đầu:
```python
ead_allocated = ead_state * weight  # ✅ Đúng
```

Chỉ có `allocate_forecast_to_loans_simple()` bị sai.

## Files thay đổi

1. ✅ `src/rollrate/allocation.py`
   - Line ~390: Xóa tính `_PCT`
   - Line ~420-450: Sửa logic tính EAD_FORECAST
   - Line ~460-480: Thêm validation

2. ✅ `test_ead_forecast_fix.py` (new)
   - Test script verify fix

3. ✅ `FIX_EAD_FORECAST_LOGIC.md` (new)
   - Document giải thích fix

## Kết luận

✅ **Fix hoàn tất**
- EAD_FORECAST bây giờ tính đúng theo lifecycle forecast
- EAD_FORECAST < EAD_CURRENT (do prepayment/writeoff)
- Validation tự động đảm bảo tổng EAD khớp
- Test đã pass

🎯 **Next steps:**
1. Re-run `Complete_Workflow.ipynb`
2. Verify EAD_FORECAST_MOB12 < EAD_CURRENT
3. Verify EAD_FORECAST_MOB24 < EAD_FORECAST_MOB12
4. Push changes lên Git
