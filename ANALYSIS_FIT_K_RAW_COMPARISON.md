# Phân Tích Chi Tiết: fit_k_raw - Projection_done vs Final_Workflow

## 📊 So Sánh Parameters

### Projection_done

#### Version 1: WLS (Baseline)
```python
k_raw_by_mob, weight_by_mob, k_raw_df = fit_k_raw(
    actual_results=actual_results_fit,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    states=states,
    s30_states=s30_states,
    include_co=True,
    denom_mode="disb",                    # ← Dùng DISB làm denominator
    disb_total_by_vintage=disb_total_by_vintage_fit,
    min_disb=1e-10,
    weight_mode="equal",                  # ← Equal weight cho mọi vintage
    method="wls",                         # ← Weighted Least Squares
    eps=1e-8,
    min_denom=1e-10,
    min_obs=5,
    fallback_k=1.0,
    fallback_weight=0.0,
    return_detail=True,
)
```

#### Version 2: WLS with Regularization
```python
LAMBDA_K = 1e-4
K_PRIOR = 0.0

k_raw_reg_by_mob, weight_reg_by_mob, k_raw_reg_df = fit_k_raw(
    actual_results=actual_results_fit,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    states=states,
    s30_states=s30_states,
    include_co=True,
    denom_mode="disb",
    disb_total_by_vintage=disb_total_by_vintage_fit,
    min_disb=1e-10,
    weight_mode="equal",
    method="wls_reg",                     # ← Regularized WLS
    lambda_k=LAMBDA_K,                    # ← Regularization strength = 1e-4
    k_prior=K_PRIOR,                      # ← Prior value = 0.0
    eps=1e-8,
    min_denom=1e-10,
    min_obs=5,
    fallback_k=1.0,
    fallback_weight=0.0,
    return_detail=True,
)
```

### Final_Workflow

```python
k_raw_by_mob, weight_by_mob, _ = fit_k_raw(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    states=BUCKETS_CANON,
    s30_states=BUCKETS_30P,
    include_co=True,
    denom_mode="disb",                    # ← Dùng DISB làm denominator
    disb_total_by_vintage=disb_total_by_vintage,
    return_detail=True,
    # Không có: weight_mode, method, lambda_k, k_prior
    # → Sử dụng defaults
)
```

**Defaults** (từ function signature):
```python
method="ratio"           # ← Default method
weight_mode="ead"        # ← Default weight mode
lambda_k=0.0            # ← No regularization
k_prior=0.0
```

---

## 🔍 Sự Khác Biệt Quan Trọng

### 1. Method ⚠️ CRITICAL

| Notebook | Method | Formula |
|----------|--------|---------|
| **Projection_done (v1)** | `wls` | `k_m = Σ(w·a·d) / Σ(w·a²)` |
| **Projection_done (v2)** | `wls_reg` | `k_m = [Σ(w·a·d) + λ·k_prior] / [Σ(w·a²) + λ]` |
| **Final_Workflow** | `ratio` (default) | `k = d/a` per vintage, then aggregate |

**Impact**: ⚠️ **CRITICAL**
- `ratio`: Tính k cho từng vintage riêng lẻ, sau đó aggregate
- `wls`: Tính k tối ưu cho tất cả vintages cùng lúc
- `wls_reg`: Tính k tối ưu với regularization

### 2. Weight Mode

| Notebook | Weight Mode | Meaning |
|----------|-------------|---------|
| **Projection_done** | `equal` | Mọi vintage có weight = 1 |
| **Final_Workflow** | `ead` (default) | Weight theo EAD của vintage |

**Impact**: ⚠️ HIGH
- `equal`: Vintage nhỏ và lớn có ảnh hưởng như nhau
- `ead`: Vintage lớn (nhiều EAD) có ảnh hưởng lớn hơn

### 3. Regularization

| Notebook | Regularization | Lambda | K_Prior |
|----------|----------------|--------|---------|
| **Projection_done (v1)** | No | 0 | 0 |
| **Projection_done (v2)** | Yes | 1e-4 | 0.0 |
| **Final_Workflow** | No | 0 | 0 |

**Impact**: ⚠️ HIGH
- Regularization "shrinks" k về k_prior (0.0)
- Giảm overfitting
- K values nhỏ hơn → Conservative hơn

---

## 📐 Công Thức Chi Tiết

### Method: ratio (Final_Workflow default)

```python
# Cho mỗi vintage:
a = y_hat - y_vm    # Markov increment
d = y_tar - y_vm    # Actual increment

k_vintage = d / a   # Ratio per vintage
k_vintage = clip(k_vintage, 0, 1)  # Clip to [0, 1]

# Aggregate across vintages:
k_m = weighted_median(k_vintage, weights)
```

**Ưu điểm**:
- Đơn giản, dễ hiểu
- Robust với outliers (dùng median)

**Nhược điểm**:
- Không tối ưu toàn cục
- Có thể bị ảnh hưởng bởi vintages có a nhỏ

### Method: wls (Projection_done v1)

```python
# Tối ưu k cho tất cả vintages cùng lúc:
k_m = Σ(w_i · a_i · d_i) / Σ(w_i · a_i²)

where:
  w_i = weight của vintage i
  a_i = Markov increment của vintage i
  d_i = Actual increment của vintage i
```

**Ưu điểm**:
- Tối ưu toàn cục (minimize squared error)
- Sử dụng tất cả data hiệu quả

**Nhược điểm**:
- Có thể overfit nếu data ít
- Sensitive với outliers

### Method: wls_reg (Projection_done v2)

```python
# Regularized WLS:
k_m = [Σ(w_i · a_i · d_i) + λ · k_prior] / [Σ(w_i · a_i²) + λ]

where:
  λ = lambda_k = 1e-4 (regularization strength)
  k_prior = 0.0 (prior value)
```

**Ưu điểm**:
- Giảm overfitting
- Stable hơn với data ít
- Bias k về k_prior (conservative)

**Nhược điểm**:
- Cần tune λ
- Có thể underfit nếu λ quá lớn

---

## 🎯 Độ Chính Xác: Cái Nào Tốt Hơn?

### Trường Hợp 1: Data Nhiều, Chất Lượng Tốt

**Winner**: `wls` (Projection_done v1)

**Lý do**:
- Tối ưu toàn cục
- Sử dụng tất cả data hiệu quả
- Không bị bias bởi regularization

**Khi nào**: 
- Có nhiều vintages (>20)
- Data quality tốt
- Ít outliers

### Trường Hợp 2: Data Ít, Noisy

**Winner**: `wls_reg` (Projection_done v2)

**Lý do**:
- Regularization giảm overfitting
- Stable hơn với data ít
- Conservative (an toàn hơn)

**Khi nào**:
- Ít vintages (<20)
- Data noisy
- Cần forecast conservative

### Trường Hợp 3: Data Có Outliers

**Winner**: `ratio` (Final_Workflow default)

**Lý do**:
- Dùng median → Robust với outliers
- Không bị ảnh hưởng bởi extreme values

**Khi nào**:
- Data có outliers
- Cần robust estimation
- Đơn giản, dễ explain

---

## 📊 So Sánh Thực Tế

### Ví Dụ: 3 Vintages

```
Vintage 1: a=0.05, d=0.06, w=100
Vintage 2: a=0.04, d=0.05, w=200
Vintage 3: a=0.10, d=0.08, w=50  (outlier)
```

#### Method: ratio
```python
k1 = 0.06/0.05 = 1.20 → clip to 1.0
k2 = 0.05/0.04 = 1.25 → clip to 1.0
k3 = 0.08/0.10 = 0.80

k_m = weighted_median([1.0, 1.0, 0.80], [100, 200, 50])
    = 1.0  (median)
```

#### Method: wls (equal weight)
```python
k_m = (1·0.05·0.06 + 1·0.04·0.05 + 1·0.10·0.08) / 
      (1·0.05² + 1·0.04² + 1·0.10²)
    = (0.003 + 0.002 + 0.008) / (0.0025 + 0.0016 + 0.01)
    = 0.013 / 0.0141
    = 0.92
```

#### Method: wls_reg (λ=1e-4, k_prior=0)
```python
k_m = (0.013 + 1e-4·0) / (0.0141 + 1e-4)
    = 0.013 / 0.0142
    = 0.916  (slightly lower than wls)
```

**Kết quả**:
- `ratio`: 1.0 (robust, không bị ảnh hưởng bởi outlier)
- `wls`: 0.92 (bị kéo xuống bởi vintage 3)
- `wls_reg`: 0.916 (giữa wls và prior)

---

## 🎯 Khuyến Nghị

### Cho Projection_done

**Hiện tại**: Dùng cả 2 versions (wls và wls_reg)

**Khuyến nghị**: ✅ **TỐT**

**Lý do**:
- So sánh được 2 approaches
- wls_reg conservative hơn cho long-term (36 months)
- Có thể chọn version phù hợp với risk appetite

**Best practice**:
```python
# Use wls_reg for final forecast (conservative)
forecast_results = forecast_all_vintages_partial_step(
    ...,
    k_by_mob=k_final_reg_by_mob,  # From wls_reg
)
```

### Cho Final_Workflow

**Hiện tại**: Dùng `ratio` (default)

**Khuyến nghị**: ⚠️ **NÊN THAY ĐỔI**

**Lý do**:
- `ratio` không tối ưu cho short-term forecast
- `wls` tốt hơn khi có nhiều data (19M rows)
- Không cần regularization vì data nhiều

**Recommended change**:
```python
k_raw_by_mob, weight_by_mob, _ = fit_k_raw(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    states=BUCKETS_CANON,
    s30_states=BUCKETS_30P,
    include_co=True,
    denom_mode="disb",
    disb_total_by_vintage=disb_total_by_vintage,
    method="wls",              # ← ADD THIS
    weight_mode="equal",       # ← ADD THIS (or "ead")
    return_detail=True,
)
```

**Impact**:
- Forecast chính xác hơn
- Tối ưu toàn cục
- Consistent với Projection_done approach

---

## 📊 Bảng Tổng Hợp

| Aspect | Projection_done | Final_Workflow | Winner |
|--------|-----------------|----------------|--------|
| **Method** | wls / wls_reg | ratio (default) | Projection_done |
| **Weight Mode** | equal | ead (default) | Depends |
| **Regularization** | Yes (v2) | No | Depends |
| **Optimization** | Global | Per-vintage | Projection_done |
| **Robustness** | Medium | High | Final_Workflow |
| **Accuracy (nhiều data)** | High | Medium | Projection_done |
| **Accuracy (ít data)** | Medium (wls_reg: High) | Medium | wls_reg |
| **Simplicity** | Medium | High | Final_Workflow |

---

## 🎓 Kết Luận

### Độ Chính Xác

**Với data hiện tại (19M rows, 130 segments)**:

1. **wls_reg** (Projection_done v2): ⭐⭐⭐⭐⭐
   - Tốt nhất cho long-term
   - Conservative, stable
   - Giảm overfitting

2. **wls** (Projection_done v1): ⭐⭐⭐⭐
   - Tốt cho short-term
   - Tối ưu toàn cục
   - Cần data quality tốt

3. **ratio** (Final_Workflow): ⭐⭐⭐
   - Robust với outliers
   - Đơn giản
   - Không tối ưu toàn cục

### Khuyến Nghị Cuối Cùng

#### Cho Final_Workflow
```python
# RECOMMENDED: Change to wls
method="wls",
weight_mode="equal",  # or "ead" if want to weight by size
```

#### Cho Projection_done
```python
# KEEP: wls_reg for conservative long-term forecast
method="wls_reg",
lambda_k=1e-4,
k_prior=0.0,
```

---

**Date**: 2026-01-17  
**Status**: ✅ Analyzed  
**Recommendation**: Final_Workflow should use `wls` instead of `ratio`
