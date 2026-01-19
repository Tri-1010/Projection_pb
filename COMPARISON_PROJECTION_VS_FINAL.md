# So Sánh Logic: Projection_done vs Final_Workflow

## 🎯 Tóm Tắt

Kết quả forecast khác nhau giữa 2 notebooks do **4 sự khác biệt chính** trong cấu hình và parameters.

---

## 📊 Các Sự Khác Biệt Chi Tiết

### 1️⃣ MAX_MOB - Forecast Horizon

#### Projection_done
```python
max_mob = 36  # hoac 48, 60 tuy y
```
- Forecast đến MOB 36
- Phù hợp cho long-term projection
- Cần nhiều data hơn

#### Final_Workflow
```python
MAX_MOB = 13  # Forecast đến MOB n
```
- Forecast đến MOB 13
- Phù hợp cho short-term projection
- Ít data requirement hơn

**Impact**: ⚠️ **HIGH**
- Forecast horizon khác nhau → Kết quả khác nhau
- MOB 13 vs MOB 36 là sự khác biệt lớn

---

### 2️⃣ fit_k_raw() - Regularization

#### Projection_done
```python
# WLS with regularization (k_prior=0 to bias k downward)
LAMBDA_K = 1e-4
K_PRIOR = 0.0

k_raw_reg_by_mob, weight_reg_by_mob, k_raw_reg_df = fit_k_raw(
    actual_results=actual_results_fit,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    s30_states=s30_states,
    method="wls_reg",        # ← Regularized WLS
    lambda_k=LAMBDA_K,       # ← Regularization strength
    k_prior=K_PRIOR,         # ← Prior value for K
    eps=1e-8,
    min_denom=1e-10,
)
```

**Regularization Effect**:
- K values bị "shrink" về K_PRIOR (0.0)
- Giảm overfitting
- K values nhỏ hơn → Forecast conservative hơn

#### Final_Workflow
```python
# Default WLS (no regularization)
k_raw_by_mob, weight_by_mob, _ = fit_k_raw(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    s30_states=BUCKETS_30P,
    # No method, lambda_k, k_prior specified
    # → Uses default method='wls'
)
```

**No Regularization**:
- K values không bị shrink
- Fit data tốt hơn nhưng có thể overfit
- K values lớn hơn → Forecast aggressive hơn

**Impact**: ⚠️ **HIGH**
- K values khác nhau → k_smooth khác nhau → k_final khác nhau → Forecast khác nhau

---

### 3️⃣ fit_alpha() - Calibration Target MOB

#### Projection_done
```python
ALPHA_TARGET_MOB = min(max_mob, mob_max) if mob_max else max_mob
# With max_mob=36 → ALPHA_TARGET_MOB ≈ 36

alpha, k_final_by_mob, alpha_scores = fit_alpha(
    actual_results=actual_results_fit,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    s30_states=s30_states,
    k_smooth_by_mob=k_smooth_by_mob,
    mob_target=ALPHA_TARGET_MOB,  # ← Target MOB 36
    include_co=True,
    alpha_grid=None,
)
```

**Alpha Calibration at MOB 36**:
- Optimize alpha để forecast tốt nhất tại MOB 36
- Alpha được tune cho long-term
- k_final = k_smooth * (1 + alpha * adjustment)

#### Final_Workflow
```python
# mob_target = min(MAX_MOB, mob_max)
# With MAX_MOB=13 → mob_target ≈ 13

alpha, k_final_by_mob, _ = fit_alpha(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    s30_states=BUCKETS_30P,
    k_smooth_by_mob=k_smooth_by_mob,
    mob_target=min(MAX_MOB, mob_max) if mob_max else MAX_MOB,  # ← Target MOB 13
    include_co=True,
)
```

**Alpha Calibration at MOB 13**:
- Optimize alpha để forecast tốt nhất tại MOB 13
- Alpha được tune cho short-term
- k_final khác do alpha khác

**Impact**: ⚠️ **HIGH**
- Alpha khác nhau → k_final khác nhau → Forecast khác nhau
- MOB 13 vs MOB 36 là target khác nhau hoàn toàn

---

### 4️⃣ forecast_all_vintages_partial_step() - Forecast Execution

#### Projection_done
```python
forecast_results = forecast_all_vintages_partial_step(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    max_mob=max_mob,              # ← 36
    k_by_mob=k_final_by_mob,      # ← From alpha(36) with regularization
    states=states,
    s30_states=s30_states,
)
```

#### Final_Workflow
```python
forecast_calibrated = forecast_all_vintages_partial_step(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    max_mob=MAX_MOB,              # ← 13
    k_by_mob=k_final_by_mob,      # ← From alpha(13) without regularization
    states=BUCKETS_CANON,
    s30_states=BUCKETS_30P,
)
```

**Impact**: ⚠️ **HIGH**
- max_mob khác → Forecast horizon khác
- k_by_mob khác → Forecast values khác

---

## 🔍 Phân Tích Sâu

### Chuỗi Ảnh Hưởng

```
1. MAX_MOB khác (36 vs 13)
   ↓
2. fit_k_raw với/không regularization
   ↓ K values khác
3. smooth_k (same logic nhưng input khác)
   ↓ k_smooth khác
4. fit_alpha với mob_target khác (36 vs 13)
   ↓ alpha khác
5. k_final = k_smooth * (1 + alpha * ...)
   ↓ k_final khác
6. forecast_all_vintages_partial_step
   ↓ Forecast results khác
```

### Ví Dụ Cụ Thể

Giả sử cho 1 cohort tại MOB 5:

#### Projection_done
```
k_raw = 1.2 (with regularization → shrink về 0)
k_smooth = 1.15 (smoothed)
alpha = 0.05 (calibrated for MOB 36)
k_final = 1.15 * (1 + 0.05 * adjustment) = 1.20
→ Forecast tại MOB 13: X
→ Forecast tại MOB 36: Y
```

#### Final_Workflow
```
k_raw = 1.3 (no regularization → larger)
k_smooth = 1.25 (smoothed, larger than Projection_done)
alpha = 0.08 (calibrated for MOB 13, different)
k_final = 1.25 * (1 + 0.08 * adjustment) = 1.35
→ Forecast tại MOB 13: X' (khác X)
```

**Kết quả**: X ≠ X' do k_final khác nhau

---

## 📊 Bảng So Sánh Tổng Hợp

| Aspect | Projection_done | Final_Workflow | Impact |
|--------|-----------------|----------------|--------|
| **MAX_MOB** | 36 | 13 | HIGH |
| **Forecast Horizon** | Long-term (36 months) | Short-term (13 months) | HIGH |
| **fit_k_raw Method** | wls_reg (regularized) | wls (default) | HIGH |
| **Regularization** | Yes (LAMBDA_K=1e-4) | No | HIGH |
| **K_PRIOR** | 0.0 (bias downward) | N/A | HIGH |
| **K Values** | Smaller (conservative) | Larger (aggressive) | HIGH |
| **mob_target for alpha** | ~36 | ~13 | HIGH |
| **Alpha Calibration** | Long-term optimized | Short-term optimized | HIGH |
| **k_final** | From alpha(36) + reg | From alpha(13) no reg | HIGH |
| **Forecast Results** | Different | Different | HIGH |

---

## 🎯 Nguyên Nhân Gốc Rễ

### Tại Sao Kết Quả Khác Nhau?

1. **Forecast Horizon Khác Nhau**
   - Projection_done: Forecast đến MOB 36
   - Final_Workflow: Forecast đến MOB 13
   - → Mục tiêu khác nhau → Calibration khác nhau

2. **Regularization Khác Nhau**
   - Projection_done: Có regularization → K conservative
   - Final_Workflow: Không regularization → K aggressive
   - → K values khác nhau → Forecast khác nhau

3. **Alpha Calibration Target Khác Nhau**
   - Projection_done: Optimize cho MOB 36
   - Final_Workflow: Optimize cho MOB 13
   - → Alpha khác nhau → k_final khác nhau

4. **Tổng Hợp**
   - Tất cả factors trên cộng lại
   - → Forecast results khác nhau là **EXPECTED**

---

## ✅ Kết Luận

### Kết Quả Khác Nhau Là BÌN THƯỜNG

Hai notebooks có **mục đích khác nhau**:

#### Projection_done
- **Mục đích**: Long-term projection (36 months)
- **Use case**: Strategic planning, long-term forecasting
- **Approach**: Conservative với regularization
- **Target**: MOB 36

#### Final_Workflow
- **Mục đích**: Short-term projection (13 months)
- **Use case**: Operational planning, near-term forecasting
- **Approach**: Straightforward không regularization
- **Target**: MOB 13

### Cả Hai Đều ĐÚNG

- Projection_done đúng cho long-term
- Final_Workflow đúng cho short-term
- Không nên expect kết quả giống nhau

---

## 💡 Khuyến Nghị

### Option 1: Giữ Nguyên (RECOMMENDED)

**Lý do**:
- Hai notebooks phục vụ mục đích khác nhau
- Final_Workflow (MOB 13) phù hợp hơn cho operational use
- Projection_done (MOB 36) phù hợp cho strategic planning

**Action**: Không cần thay đổi gì

### Option 2: Match Projection_done Config

Nếu muốn kết quả giống nhau, sửa Final_Workflow:

```python
# In Final_Workflow, change:
MAX_MOB = 36  # Instead of 13

# Add regularization to fit_k_raw:
LAMBDA_K = 1e-4
K_PRIOR = 0.0

k_raw_by_mob, weight_by_mob, _ = fit_k_raw(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    s30_states=BUCKETS_30P,
    method="wls_reg",        # Add this
    lambda_k=LAMBDA_K,       # Add this
    k_prior=K_PRIOR,         # Add this
)
```

**Lưu ý**: Điều này sẽ làm Final_Workflow chậm hơn và phức tạp hơn

### Option 3: Document Differences

Thêm comment vào đầu mỗi notebook:

#### Projection_done
```python
"""
Long-term Projection Notebook
- MAX_MOB = 36 (forecast đến 36 months)
- Uses regularization (conservative)
- Optimized for long-term accuracy
"""
```

#### Final_Workflow
```python
"""
Short-term Operational Workflow
- MAX_MOB = 13 (forecast đến 13 months)
- No regularization (straightforward)
- Optimized for near-term accuracy and speed
"""
```

---

## 🧪 Verification

Để verify sự khác biệt, có thể:

### Test 1: Check K Values
```python
# In both notebooks, after fit_k_raw:
print("K values at MOB 5:")
print(f"Projection_done: {k_raw_by_mob.get(5, 'N/A')}")
print(f"Final_Workflow: {k_raw_by_mob.get(5, 'N/A')}")
```

### Test 2: Check Alpha
```python
# In both notebooks, after fit_alpha:
print(f"Alpha: {alpha}")
print(f"mob_target: {mob_target}")
```

### Test 3: Check Forecast at MOB 13
```python
# Compare forecast results at MOB 13
# Should be different due to different calibration
```

---

## 📚 Tài Liệu Liên Quan

- `compare_notebooks_logic.py` - Script so sánh tự động
- `src/rollrate/calibration_kmob.py` - fit_k_raw, smooth_k, fit_alpha
- `src/rollrate/forecast.py` - forecast_all_vintages_partial_step

---

**Date**: 2026-01-17  
**Status**: ✅ Analyzed  
**Conclusion**: Differences are expected and correct
