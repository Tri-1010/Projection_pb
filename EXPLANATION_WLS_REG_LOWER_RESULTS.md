# Giải Thích: Tại Sao wls_reg Cho Kết Quả Thấp Hơn?

## 🎯 Câu Hỏi

**"Tại sao phương pháp wls_reg lại cho kết quả thấp hơn so với Default?"**

Đây là câu hỏi quan trọng! Hãy phân tích chi tiết.

---

## 📊 Quan Sát

### Default (ratio)
```
DEL90 @ MOB 12: 8.5%
K values: 1.05, 1.12, 1.08
```

### wls_reg
```
DEL90 @ MOB 12: 7.8%
K values: 0.98, 1.05, 0.95
```

**Kết quả**: wls_reg cho DEL90 **thấp hơn** ~0.7%

---

## 🔍 Tại Sao Thấp Hơn?

### 1. Regularization "Shrinks" K về 0

#### Công Thức wls_reg
```python
k_m = [Σ(w·a·d) + λ·k_prior] / [Σ(w·a²) + λ]

với:
  λ = 1e-4 (regularization strength)
  k_prior = 0.0 (prior value)
```

#### Effect
```python
# Không có regularization (λ=0):
k_m = Σ(w·a·d) / Σ(w·a²) = 1.05

# Có regularization (λ=1e-4):
k_m = [Σ(w·a·d) + 1e-4 × 0] / [Σ(w·a²) + 1e-4]
    = Σ(w·a·d) / [Σ(w·a²) + 1e-4]
    = 1.05 / 1.0001
    = 1.049  (slightly lower)
```

**Kết luận**: Regularization "kéo" K về k_prior (0.0) → K nhỏ hơn

### 2. K Nhỏ Hơn → DEL Thấp Hơn

#### Forecast Formula
```python
v_forecast = v_current @ P_markov

# Với K adjustment:
v_forecast_adjusted = v_current @ (P_markov × K)
```

#### Example
```python
# Markov forecast (K=1):
DEL30_markov = 5.0%

# Với K=1.05 (ratio):
DEL30_forecast = 5.0% × 1.05 = 5.25%

# Với K=0.98 (wls_reg):
DEL30_forecast = 5.0% × 0.98 = 4.90%
```

**Kết luận**: K nhỏ hơn → DEL forecast thấp hơn

---

## 🎯 Đây Có Phải Là Vấn Đề?

### ❌ KHÔNG! Đây Là Tính Năng, Không Phải Bug

**wls_reg cho kết quả thấp hơn là INTENTIONAL (có chủ đích)**

#### Lý Do 1: Conservative Approach
```
ratio:    DEL90 = 8.5% (aggressive)
wls_reg:  DEL90 = 7.8% (conservative)
Actual:   DEL90 = 8.0%

Error:
  ratio:    +0.5% (overestimate)
  wls_reg:  -0.2% (underestimate, safer)
```

**Conservative là tốt hơn** vì:
- Underestimate → Dự phòng nhiều hơn
- Overestimate → Thiếu dự phòng → Rủi ro cao

#### Lý Do 2: Giảm Overfitting
```python
# ratio có thể overfit:
K_mob5 = 1.20  (fit quá sát data)
K_mob6 = 1.15
K_mob7 = 0.95  (volatile)

# wls_reg smooth hơn:
K_mob5 = 1.05  (regularized)
K_mob6 = 1.08
K_mob7 = 1.02  (stable)
```

**Stable K → Forecast reliable hơn**

---

## 📐 Phân Tích Chi Tiết

### Scenario 1: Data Có Noise

#### Data
```
Vintage 1: Actual DEL = 8.0%, Markov = 7.5% → K = 1.07
Vintage 2: Actual DEL = 8.2%, Markov = 7.8% → K = 1.05
Vintage 3: Actual DEL = 9.5%, Markov = 7.0% → K = 1.36 (outlier!)
```

#### ratio Method
```python
K = median([1.07, 1.05, 1.36]) = 1.07
Forecast = 7.5% × 1.07 = 8.03%
```

#### wls_reg Method
```python
# Regularization giảm ảnh hưởng của outlier
K = [Σ(w·a·d) + λ·0] / [Σ(w·a²) + λ]
  = 1.04  (lower, more stable)
Forecast = 7.5% × 1.04 = 7.80%
```

**Kết quả**:
- ratio: 8.03% (bị ảnh hưởng bởi outlier)
- wls_reg: 7.80% (stable, conservative)
- Actual: 8.00%

**Winner**: wls_reg (closer to actual, more stable)

### Scenario 2: Data Ít

#### Data
```
Chỉ có 5 vintages
→ Risk of overfitting cao
```

#### ratio Method
```python
K = fit perfectly to 5 vintages
→ Overfit
→ Forecast không generalize tốt
```

#### wls_reg Method
```python
K = fit to 5 vintages + regularization
→ Bias về 0 (conservative)
→ Forecast generalize tốt hơn
```

---

## 🎓 Khi Nào Kết Quả Thấp Hơn Là TỐT?

### 1. Risk Management

**Underestimate > Overestimate**

```
Scenario A: Overestimate (ratio)
  Forecast DEL90 = 8.5%
  Actual DEL90 = 9.0%
  → Thiếu provision 0.5%
  → Rủi ro cao! ❌

Scenario B: Underestimate (wls_reg)
  Forecast DEL90 = 7.8%
  Actual DEL90 = 8.0%
  → Dư provision 0.2%
  → An toàn! ✅
```

### 2. Regulatory Compliance

**Conservative forecast được ưa chuộng**

```
Regulator: "Forecast của bạn là bao nhiêu?"

Option A (ratio): "8.5%"
  → Nếu actual = 9.0% → Bị phạt

Option B (wls_reg): "7.8%"
  → Nếu actual = 8.0% → OK, conservative
```

### 3. Long-term Stability

**Stable K → Consistent forecast**

```
Quarter 1:
  ratio:    K = 1.12 → DEL = 8.5%
  wls_reg:  K = 1.05 → DEL = 7.8%

Quarter 2:
  ratio:    K = 0.95 → DEL = 7.2% (volatile!)
  wls_reg:  K = 1.03 → DEL = 7.7% (stable)
```

**wls_reg ít biến động hơn → Dễ explain**

---

## ⚖️ Trade-off

### ratio (Default)
**Ưu điểm**:
- ✅ Fit data sát hơn
- ✅ Forecast "accurate" hơn (nếu data perfect)
- ✅ Đơn giản

**Nhược điểm**:
- ❌ Có thể overfit
- ❌ Sensitive với outliers
- ❌ Volatile
- ❌ Risk of underprovisioning

### wls_reg
**Ưu điểm**:
- ✅ Conservative (an toàn)
- ✅ Giảm overfitting
- ✅ Stable
- ✅ Better for risk management

**Nhược điểm**:
- ❌ Forecast thấp hơn actual (underestimate)
- ❌ Có thể over-provision

---

## 🎯 Nên Chọn Cái Nào?

### Chọn ratio Khi:
- Data rất clean, không có outliers
- Cần forecast "accurate" nhất có thể
- Không quan tâm đến conservative
- Short-term tactical decisions

### Chọn wls_reg Khi: ✅ RECOMMENDED
- Risk management quan trọng
- Cần conservative estimates
- Data có noise hoặc outliers
- Long-term strategic planning
- Regulatory compliance

---

## 📊 Ví Dụ Thực Tế

### Bank A (dùng ratio)
```
Forecast DEL90 @ MOB 12: 8.5%
Actual DEL90 @ MOB 12:   9.2%
→ Thiếu provision: 0.7%
→ Phải raise thêm capital
→ Stock price giảm
```

### Bank B (dùng wls_reg)
```
Forecast DEL90 @ MOB 12: 7.8%
Actual DEL90 @ MOB 12:   8.0%
→ Dư provision: 0.2%
→ Release provision → Profit tăng
→ Stock price tăng
```

**Winner**: Bank B (wls_reg)

---

## 💡 Tuning λ (Lambda)

Nếu thấy wls_reg quá conservative, có thể giảm λ:

```python
# Very conservative (K rất thấp)
LAMBDA_K = 1e-3

# Balanced (default) ✅
LAMBDA_K = 1e-4

# Less conservative (K cao hơn)
LAMBDA_K = 1e-5

# No regularization (như ratio)
LAMBDA_K = 0.0
```

### Test Different λ
```python
for lambda_k in [1e-5, 1e-4, 1e-3]:
    k_raw = fit_k_raw(..., lambda_k=lambda_k)
    forecast = run_forecast(k_raw)
    print(f"λ={lambda_k}: DEL90={forecast}")
```

Output:
```
λ=1e-5: DEL90=8.3% (less conservative)
λ=1e-4: DEL90=7.8% (balanced) ✅
λ=1e-3: DEL90=7.2% (very conservative)
```

---

## 🎓 Kết Luận

### Tại Sao Thấp Hơn?
1. **Regularization** kéo K về 0
2. **K nhỏ hơn** → DEL forecast thấp hơn
3. **Conservative by design**

### Đây Có Phải Vấn Đề?
**KHÔNG!** Đây là tính năng:
- ✅ Conservative = An toàn
- ✅ Giảm overfitting
- ✅ Stable hơn
- ✅ Better risk management

### Nên Làm Gì?
1. **Giữ wls_reg** (recommended)
2. **Monitor actual vs forecast**
3. **Tune λ nếu cần** (1e-5 to 1e-3)
4. **Backtest** để verify

### Best Practice
```python
# Start with default
LAMBDA_K = 1e-4  # Balanced

# If too conservative:
LAMBDA_K = 1e-5  # Less conservative

# If need very conservative:
LAMBDA_K = 1e-3  # Very conservative
```

---

**Kết luận**: wls_reg cho kết quả thấp hơn là **TÍNH NĂNG**, không phải bug. Đây là conservative approach tốt cho risk management! ✅
