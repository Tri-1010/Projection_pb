# Hướng Dẫn Sử Dụng Dự Án Roll Rate Model - Calibration

## 📋 Tổng Quan Dự Án

Dự án **Roll Rate Model** là một hệ thống dự báo rủi ro tín dụng dựa trên **Markov Chain**, cho phép:
- Tính toán ma trận chuyển trạng thái DPD (Days Past Due)
- Dự báo phân phối rủi ro 12-36 tháng tới
- **Calibration** để điều chỉnh dự báo sát với thực tế
- Backtest và validation

---

## 🎯 Phần CALIBRATION - Trọng Tâm

### 1. Calibration Là Gì?

**Calibration** là quá trình điều chỉnh dự báo từ mô hình Markov để khớp với dữ liệu thực tế. Mô hình Markov thuần túy có thể:
- Dự báo quá cao hoặc quá thấp
- Không phản ánh đúng xu hướng thị trường hiện tại
- Thiếu tính mùa vụ (seasonality)

### 2. Các Phương Pháp Calibration

Dự án cung cấp **3 phương pháp calibration** chính:

#### **A. Calibration Per Product (calibration.py)**

**Mục đích:** Điều chỉnh theo từng sản phẩm với hệ số k cố định

**Công thức:**
```
k_product = DEL90_actual / DEL90_forecast
DEL90_adjusted = DEL90_raw × k_product
```

**Khi nào dùng:**
- Khi muốn điều chỉnh đơn giản, nhanh chóng
- Khi các sản phẩm có đặc điểm rủi ro khác biệt rõ rệt

**File:** `src/rollrate/calibration.py`

**Các hàm chính:**
```python
# Tính k per product
k_dict = compute_k_per_product_ifrs_fullhistory(
    df_actual=df_actual,
    df_forecast=df_forecast,
    H_map={"CDLPIL": 12, "TWLPIL": 12},  # MOB anchor
    method="trimmed_mean",  # hoặc "median"
    clip_min=0.3,
    clip_max=3.0
)

# Áp dụng k vào lifecycle
df_calibrated = apply_k_to_lifecycle(
    df_lifecycle=df_lifecycle,
    k_dict=k_dict,
    m_apply_map={"CDLPIL": 4},  # Bắt đầu áp k từ MOB 4
    blend_n=2  # Blend 2 kỳ đầu
)
```

**Tham số quan trọng:**
- `H_map`: MOB anchor để tính k (thường 12 hoặc 24)
- `m_apply`: MOB bắt đầu áp dụng k (thường 4)
- `blend_n`: Số kỳ blend để tránh nhảy đột ngột
- `clip_min/max`: Giới hạn k để tránh outlier

---

#### **B. Calibration Per Product + Seasonality (calibration2.py)**

**Mục đích:** Kết hợp điều chỉnh theo sản phẩm VÀ theo tháng giải ngân

**Công thức:**
```
k_product = mean(Actual @ MOB=H) / mean(Model @ MOB=H)
F_month = mean(Loss_month) / mean(Loss_all)
DEL_adjusted = DEL_raw × k_product × F_month
```

**Khi nào dùng:**
- Khi có hiện tượng mùa vụ rõ rệt (ví dụ: Tết, cuối năm)
- Khi muốn tăng độ chính xác cho từng cohort

**File:** `src/rollrate/calibration2.py`

**Workflow:**
```python
# Bước 1: Build lifecycle actual only
df_actual = build_actual_lifecycle_amount_only(df_raw)

# Bước 2: Build lifecycle model only (forecast)
df_model = build_model_lifecycle_amount_only(
    df_raw=df_raw,
    matrices_by_mob=matrices_by_mob,
    max_mob=29
)

# Bước 3: Tính k per product
k_dict = compute_k_per_product_auto(
    df_actual=df_actual,
    df_model=df_model,
    horizon_mob=12,
    metric_col="DEL90_PCT"
)

# Bước 4: Tính seasonality factor
month_factor = compute_month_seasonality(
    df_actual=df_actual,
    horizon_mob=12,
    metric_col="DEL90_PCT",
    min_cohort=5
)

# Bước 5: Áp dụng cả 2 layer
df_calibrated = apply_product_calibration(df_lifecycle, k_dict)
df_calibrated = apply_month_seasonality(df_calibrated, month_factor)
```

---

#### **C. Calibration Per MOB - WLS Method (calibration_kmob.py)** ⭐ **NÂNG CAO**

**Mục đích:** Điều chỉnh chi tiết theo từng MOB với phương pháp Weighted Least Squares

**Đặc điểm:**
- Hệ số k khác nhau cho mỗi MOB
- Sử dụng WLS để fit k từ one-step forecast
- Smoothing để tránh k nhảy đột ngột
- Optional alpha scaling để fit long-horizon target

**File:** `src/rollrate/calibration_kmob.py`

**Workflow đầy đủ:**

```python
# ===== BƯỚC 1: Chuẩn bị dữ liệu =====
states = BUCKETS_CANON
s30_states = BUCKETS_30P

# Actual lifecycle (history)
actual_results = get_actual_all_vintages_amount(df_raw)

# DISB_TOTAL map (cohort-based)
loan_disb = df_raw.groupby(
    ["PRODUCT_TYPE", "RISK_SCORE", "DISBURSAL_DATE", "AGREEMENT_ID"]
)["DISBURSAL_AMOUNT"].first()

cohort_disb = loan_disb.groupby(level=[0, 1, 2]).sum()
disb_total_by_vintage = cohort_disb.to_dict()

# ===== BƯỚC 2: Fit k_raw theo MOB =====
k_raw_by_mob, weight_by_mob, k_raw_df = fit_k_raw(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    states=states,
    s30_states=s30_states,
    include_co=True,
    
    # Chọn phương pháp
    method="wls",  # "wls", "wls_reg", hoặc "ratio"
    
    # WLS parameters
    eps=1e-8,
    min_denom=1e-10,
    min_obs=5,
    fallback_k=1.0,
    
    # Denominator mode
    denom_mode="disb",  # "disb" hoặc "ead"
    disb_total_by_vintage=disb_total_by_vintage,
    min_disb=1e-10,
    
    # Weight mode
    weight_mode="equal",  # "equal" hoặc "ead"
    
    return_detail=True
)

# ===== BƯỚC 3: Smooth k curve =====
mob_min = min(k_raw_by_mob.keys())
mob_max = max(k_raw_by_mob.keys())

k_smooth_by_mob, mobs, k_vals = smooth_k(
    k_raw_by_mob=k_raw_by_mob,
    weight_by_mob=weight_by_mob,
    mob_min=mob_min,
    mob_max=mob_max,
    gamma=10.0,        # Penalty cho second-difference
    monotone=False,    # True nếu muốn k tăng dần
    use_cvxpy=True,    # Dùng CVXPY nếu có
    default_k=1.0
)

# ===== BƯỚC 4: Fit alpha (optional) =====
alpha, k_final_by_mob, alpha_scores = fit_alpha(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    states=states,
    s30_states=s30_states,
    k_smooth_by_mob=k_smooth_by_mob,
    mob_target=24,     # MOB target để fit alpha
    include_co=True,
    alpha_grid=None,   # Mặc định: np.arange(0.5, 1.5, 0.01)
    val_frac=0.2       # 20% vintages gần nhất làm validation
)

# ===== BƯỚC 5: Forecast với k_final =====
forecast_results_calibrated = forecast_all_vintages_partial_step(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    max_mob=36,
    k_by_mob=k_final_by_mob,
    states=states
)

# ===== BƯỚC 6: Backtest =====
backtest_df = backtest_error_by_mob(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    parent_fallback=parent_fallback,
    states=states,
    s30_states=s30_states,
    k_by_mob=k_final_by_mob,
    denom_mode="disb",
    disb_total_by_vintage=disb_total_by_vintage
)
```

**Giải thích các tham số:**

| Tham số | Ý nghĩa | Giá trị đề xuất |
|---------|---------|-----------------|
| `method` | Phương pháp fit k | `"wls"` (chuẩn), `"wls_reg"` (có regularization), `"ratio"` (legacy) |
| `denom_mode` | Mẫu số tính DEL | `"disb"` (chuẩn IFRS9), `"ead"` (theo EAD) |
| `weight_mode` | Trọng số vintages | `"equal"` (mỗi vintage = 1), `"ead"` (theo EAD) |
| `gamma` | Penalty smoothing | 10.0 (càng cao càng smooth) |
| `monotone` | Ép k tăng dần | `False` (thường không cần) |
| `alpha_grid` | Grid search alpha | `None` (auto: 0.5→1.5) |
| `val_frac` | Tỷ lệ validation | 0.2 (20% vintages gần nhất) |

---

### 3. So Sánh Các Phương Pháp

| Tiêu chí | Per Product | + Seasonality | Per MOB (WLS) |
|----------|-------------|---------------|---------------|
| **Độ phức tạp** | ⭐ Đơn giản | ⭐⭐ Trung bình | ⭐⭐⭐ Nâng cao |
| **Độ chính xác** | Trung bình | Cao | Rất cao |
| **Thời gian chạy** | Nhanh | Trung bình | Chậm hơn |
| **Yêu cầu data** | Ít | Trung bình | Nhiều |
| **Khi nào dùng** | Quick check | Production | Research/Fine-tuning |

---

### 4. Lựa Chọn Phương Pháp Calibration

**Dùng Per Product khi:**
- Cần kết quả nhanh
- Data ít (< 12 tháng)
- Chỉ quan tâm trend tổng thể

**Dùng + Seasonality khi:**
- Có hiện tượng mùa vụ rõ
- Data đủ (> 24 tháng)
- Cần độ chính xác cao hơn

**Dùng Per MOB (WLS) khi:**
- Cần độ chính xác tối đa
- Data nhiều (> 36 tháng)
- Có thời gian để tune parameters
- Cần giải thích chi tiết cho regulator

---

### 5. Kiểm Tra Kết Quả Calibration

```python
# Visualize k curves
plot_k_curves(k_raw_by_mob, k_smooth_by_mob, k_final_by_mob)

# Backtest error by MOB
backtest_df = backtest_error_by_mob(...)
print(backtest_df.groupby("mob")[["mae_adj", "mae_mkv"]].mean())

# So sánh actual vs adjusted vs markov
forecast_vintage(
    actual_results=actual_results,
    matrices_by_mob=matrices_by_mob,
    vintage_key=("CDLPIL", "A", pd.Timestamp("2023-01-01")),
    states=states,
    s30_states=s30_states,
    k_by_mob=k_final_by_mob,
    mob_target=24
)
```

---

## 📂 Cấu Trúc File Calibration

```
src/rollrate/
├── calibration.py          # Per Product (đơn giản)
├── calibration2.py         # + Seasonality
├── calibration_kmob.py     # Per MOB WLS (nâng cao)
└── forecast.py             # Forecast engine (dùng chung)
```

---

## 🔧 Tham Số Cấu Hình Quan Trọng

**Trong `src/rollrate/calibration.py`:**
```python
H_MAP_CALIB = {
    "CDLPIL": 12,  # MOB anchor để tính k
    "TWLPIL": 12,
    "SPLPIL": 12,
}

M_APPLY_MAP = {
    "CDLPIL": 4,   # MOB bắt đầu áp k
    "SALPIL": 4,
    "SPLPIL": 4,
}

DEFAULT_M_APPLY = 4
```

**Trong `src/rollrate/calibration_kmob.py`:**
```python
# WLS parameters
min_obs = 5          # Số quan sát tối thiểu
min_denom = 1e-10    # Mẫu số tối thiểu
eps = 1e-8           # Epsilon cho zero check

# Smoothing parameters
gamma = 10.0         # Penalty cho second-difference
monotone = False     # Ép k tăng dần

# Alpha fitting
alpha_grid = np.arange(0.5, 1.5, 0.01)
val_frac = 0.2       # 20% validation
```

---

## 🚀 Workflow Hoàn Chỉnh (End-to-End)

```python
# 1. Load data
from src.data_loader import load_data
df_raw = load_data("path/to/parquet")

# 2. Build transition matrices
from src.rollrate.transition import compute_transition_by_mob
matrices_by_mob, parent_fallback = compute_transition_by_mob(df_raw)

# 3. Build lifecycle
from src.rollrate.lifecycle import (
    get_actual_all_vintages_amount,
    build_full_lifecycle_amount,
    add_del_metrics
)

actual_results = get_actual_all_vintages_amount(df_raw)
df_lifecycle = build_full_lifecycle_amount(df_raw, matrices_by_mob, max_mob=36)
df_lifecycle = add_del_metrics(df_lifecycle, df_raw)

# 4. Calibration (chọn 1 trong 3 phương pháp)

# Option A: Per Product
from src.rollrate.calibration import (
    compute_k_per_product_ifrs_fullhistory,
    apply_k_to_lifecycle
)
k_dict = compute_k_per_product_ifrs_fullhistory(...)
df_calibrated = apply_k_to_lifecycle(df_lifecycle, k_dict)

# Option B: + Seasonality
from src.rollrate.calibration2 import (
    compute_k_per_product_auto,
    compute_month_seasonality,
    apply_product_calibration,
    apply_month_seasonality
)
k_dict = compute_k_per_product_auto(...)
month_factor = compute_month_seasonality(...)
df_calibrated = apply_product_calibration(df_lifecycle, k_dict)
df_calibrated = apply_month_seasonality(df_calibrated, month_factor)

# Option C: Per MOB WLS
from src.rollrate.calibration_kmob import (
    fit_k_raw,
    smooth_k,
    fit_alpha,
    forecast_all_vintages_partial_step
)
k_raw_by_mob, _, _ = fit_k_raw(...)
k_smooth_by_mob, _, _ = smooth_k(...)
alpha, k_final_by_mob, _ = fit_alpha(...)
forecast_calibrated = forecast_all_vintages_partial_step(..., k_by_mob=k_final_by_mob)

# 5. Export results
from src.rollrate.lifecycle import export_lifecycle_all_products_one_file
export_lifecycle_all_products_one_file(
    df_calibrated,
    actual_info,
    filename="Lifecycle_Calibrated.xlsx"
)
```

---

## 📊 Output & Reporting

Sau khi calibration, bạn có thể:

1. **Export Excel với heatmap:**
```python
export_lifecycle_all_products_one_file(
    df_del_prod=df_calibrated,
    actual_info=actual_info,
    filename="outputs/Lifecycle_Calibrated.xlsx"
)
```

2. **Aggregate lên Product level:**
```python
df_product = aggregate_to_product(df_calibrated)
```

3. **Aggregate lên Portfolio level:**
```python
df_portfolio = aggregate_products_to_portfolio(
    df_product,
    portfolio_name="PORTFOLIO_ALL"
)
```

4. **Pivot tables:**
```python
pivot_del30 = make_metric_pivot(df_product, "DEL30_PCT")
pivot_del90 = make_metric_pivot(df_product, "DEL90_PCT")
```

---

## ⚠️ Lưu Ý Quan Trọng

1. **DISB_TOTAL phải tính đúng:**
   - Mỗi loan chỉ đóng góp 1 lần DISBURSAL_AMOUNT
   - Sum theo (PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE)

2. **MOB anchor (H) nên chọn:**
   - 12 cho sản phẩm ngắn hạn (< 24 tháng)
   - 24 cho sản phẩm dài hạn (> 24 tháng)

3. **Blend k để tránh nhảy đột ngột:**
   - `blend_n=2`: blend 2 kỳ đầu
   - MOB < m_apply: k = 1.0
   - MOB = m_apply: k = 0.5 + 0.5*k
   - MOB = m_apply+1: k = 0.75 + 0.25*k
   - MOB >= m_apply+2: k = k

4. **Clip k để tránh outlier:**
   - `clip_min=0.3, clip_max=3.0` (mặc định)
   - Điều chỉnh theo business logic

5. **Validation:**
   - Luôn backtest trên out-of-sample data
   - So sánh MAE: adjusted vs markov
   - Check k curve có hợp lý không

---

## 🔍 Troubleshooting

**Vấn đề: k quá cao/thấp**
- Kiểm tra H_map (MOB anchor)
- Kiểm tra DISB_TOTAL có đúng không
- Thử method khác (median thay vì trimmed_mean)

**Vấn đề: k nhảy đột ngột**
- Tăng gamma trong smooth_k
- Dùng monotone=True
- Tăng blend_n

**Vấn đề: Forecast sau calibration vẫn sai**
- Kiểm tra m_apply (có thể cần áp sớm hơn)
- Thử denom_mode="ead" thay vì "disb"
- Fit alpha với mob_target khác

---

## 📚 Tài Liệu Tham Khảo

- `README.md`: Tổng quan dự án
- `src/rollrate/calibration.py`: Code chi tiết per product
- `src/rollrate/calibration2.py`: Code chi tiết + seasonality
- `src/rollrate/calibration_kmob.py`: Code chi tiết per MOB WLS
- `notebooks/Projection_done.ipynb`: Ví dụ workflow đầy đủ

---

## 📍 Phần 8: PHÂN BỔ NGƯỢC FORECAST XUỐNG LOAN-LEVEL

### 1. Tại Sao Cần Phân Bổ Ngược?

Sau khi có kết quả forecast ở cohort-level (PRODUCT_TYPE × RISK_SCORE × VINTAGE_DATE × MOB), bạn có thể cần:
- **Lấy thông tin chi tiết** của từng hợp đồng (customer info, branch, product details)
- **Phân tích rủi ro** theo từng loan cụ thể
- **Tạo action list** cho collection team
- **Báo cáo chi tiết** cho regulator

### 2. Phương Pháp Phân Bổ (allocation_v2_fast.py)

#### **Công Thức Quan Trọng**

```
PROB_DEL30 = DEL30_PCT từ lifecycle (KHÔNG tính từ transition matrix)
EAD_DEL30 = DISBURSAL_AMOUNT × PROB_DEL30
```

**Giải thích:**
- `DEL30_PCT` được tính từ lifecycle forecast: `DEL30_AMT / DISB_TOTAL`
- Khi phân bổ ngược, mỗi loan nhận cùng `PROB_DEL30` = `DEL30_PCT` của cohort
- `EAD_DEL30 = DISBURSAL_AMOUNT × PROB_DEL30`
- **Kết quả:** Tổng `EAD_DEL30 / DISBURSAL_AMOUNT` = `DEL30_PCT` từ lifecycle ✅

**Tại sao KHÔNG tính PROB_DEL30 từ transition matrix?**
- Lifecycle đã tính sẵn `DEL30_PCT` cho toàn cohort từ MOB=0
- Nếu tính từ transition matrix cho từng loan (dựa trên STATE_CURRENT), loan đã ở DPD30+ sẽ có PROB cao hơn
- Kết quả: Tổng không khớp với lifecycle forecast

#### **Output Columns**

```python
# Per MOB (12, 24):
- STATE_FORECAST_MOB{X}: State dự báo (sampled từ transition matrix)
- EAD_FORECAST_MOB{X}: Dư nợ dự báo còn lại
- PROB_DEL30_MOB{X}: Tỉ lệ DEL30+ từ lifecycle (= DEL30_PCT)
- PROB_DEL90_MOB{X}: Tỉ lệ DEL90+ từ lifecycle (= DEL90_PCT)
- EAD_DEL30_MOB{X}: DISBURSAL_AMOUNT × PROB_DEL30
- EAD_DEL90_MOB{X}: DISBURSAL_AMOUNT × PROB_DEL90
- DEL30_FLAG_MOB{X}: 1 nếu STATE_FORECAST ∈ DEL30+
- DEL90_FLAG_MOB{X}: 1 nếu STATE_FORECAST ∈ DEL90+
```

#### **Code Sử Dụng**

```python
from src.rollrate.allocation_v2_fast import allocate_multi_mob_fast

df_loan_forecast = allocate_multi_mob_fast(
    df_loans_latest=df_loans_latest,
    df_lifecycle_final=df_lifecycle_final,
    matrices_by_mob=matrices_by_mob,
    target_mobs=[12, 24],
    parent_fallback=parent_fallback,
    include_del30=True,
    include_del90=True,
    seed=42,
)
```

### 3. Validation: Kiểm Tra Tổng EAD_DEL

```python
# Kiểm tra DEL30 rate khớp với lifecycle
total_disbursal = df_loan_forecast['DISBURSAL_AMOUNT'].sum()
total_ead_del30_mob24 = df_loan_forecast['EAD_DEL30_MOB24'].sum()

del30_rate_calc = total_ead_del30_mob24 / total_disbursal
print(f"DEL30 rate từ allocation: {del30_rate_calc * 100:.2f}%")

# So sánh với lifecycle
lifecycle_del30_pct = df_lifecycle_final[df_lifecycle_final['MOB'] == 24]['DEL30_PCT'].mean()
print(f"DEL30_PCT từ lifecycle: {lifecycle_del30_pct * 100:.2f}%")
print(f"Khớp: {abs(del30_rate_calc - lifecycle_del30_pct) < 0.001}")
```

### 4. Use Cases

#### **A. Tạo Action List cho Collection Team**

```python
# Lọc các loan có DEL90 flag = 1 tại MOB 12
high_risk_loans = df_loan_forecast[
    df_loan_forecast['DEL90_FLAG_MOB12'] == 1
].copy()

# Export cho collection team
high_risk_loans.to_excel(
    "outputs/High_Risk_Loans_MOB12.xlsx",
    columns=["AGREEMENT_ID", "CUSTOMER_NAME", "BRANCH_CODE", 
             "STATE_FORECAST_MOB12", "EAD_DEL90_MOB12"],
    index=False
)
```

#### **B. Phân Tích Theo Cohort**

```python
# Tính DEL30 rate theo cohort
cohort_analysis = df_loan_forecast.groupby('VINTAGE_DATE').agg({
    'DISBURSAL_AMOUNT': 'sum',
    'EAD_DEL30_MOB24': 'sum',
}).reset_index()

cohort_analysis['DEL30_RATE'] = cohort_analysis['EAD_DEL30_MOB24'] / cohort_analysis['DISBURSAL_AMOUNT']
print(cohort_analysis)
```

### 5. Lưu Ý Quan Trọng

1. **PROB_DEL30 = DEL30_PCT từ lifecycle:**
   - Giống nhau cho tất cả loans trong cùng cohort
   - KHÔNG tính từ transition matrix

2. **EAD_DEL30 = DISBURSAL_AMOUNT × PROB_DEL30:**
   - Dùng DISBURSAL_AMOUNT (số tiền giải ngân ban đầu)
   - KHÔNG dùng EAD_CURRENT

3. **Validation:**
   - Tổng `EAD_DEL30 / DISBURSAL_AMOUNT` phải = `DEL30_PCT` từ lifecycle
   - Nếu không khớp → kiểm tra lại code

4. **STATE_FORECAST vs DEL flags:**
   - `STATE_FORECAST`: Sampled từ transition matrix (có yếu tố random)
   - `DEL30_FLAG`: 1 nếu STATE_FORECAST ∈ BUCKETS_30P
   - `PROB_DEL30`: Tỉ lệ từ lifecycle (deterministic)

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15
