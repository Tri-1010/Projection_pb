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

### 2. Hai Phương Pháp Phân Bổ

#### **A. Proportional Allocation (Chi Tiết)**

Mỗi loan nhận EAD từ nhiều states theo tỷ lệ.

**Ưu điểm:**
- Giữ nguyên phân phối state từ cohort
- Tổng EAD khớp 100%
- Phản ánh đúng uncertainty

**Nhược điểm:**
- Mỗi loan có nhiều dòng (1 dòng per state)
- Khó visualize

**Code:**
```python
from src.rollrate.allocation import allocate_forecast_to_loans

df_allocated = allocate_forecast_to_loans(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    allocation_method="proportional",  # "proportional", "equal", "risk_weighted"
    forecast_only=True,
)
```

#### **B. Simple Allocation (1 State Per Loan)**

Mỗi loan chỉ được assign vào 1 state duy nhất (Monte Carlo sampling).

**Ưu điểm:**
- Đơn giản, dễ hiểu
- Mỗi loan chỉ 1 dòng
- Dễ tạo action list

**Nhược điểm:**
- Có yếu tố random (cần set seed)
- Tổng EAD có thể chênh nhẹ do sampling

**Code:**
```python
from src.rollrate.allocation import allocate_forecast_to_loans_simple

df_allocated_simple = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    forecast_only=True,
)
```

### 3. Validation: Kiểm Tra Tổng EAD

```python
from src.rollrate.allocation import validate_allocation

compare_df = validate_allocation(
    df_allocated=df_allocated,
    df_lifecycle_final=df_lifecycle_final,
    group_cols=["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE", "MOB"]
)

# Xem các cohort có lỗi
errors = compare_df[compare_df["STATUS"] != "OK"]
print(errors)
```

**Output:**
```
📊 Validation Summary:
OK         1234
WARNING      12
ERROR         0
```

### 4. Enrich: Thêm Thông Tin Bổ Sung

```python
from src.rollrate.allocation import enrich_loan_forecast

additional_cols = [
    "CUSTOMER_ID",
    "CUSTOMER_NAME",
    "BRANCH_CODE",
    "PRODUCT_NAME",
    "LOAN_TERM",
    "INTEREST_RATE",
]

df_enriched = enrich_loan_forecast(
    df_allocated=df_allocated_simple,
    df_raw=df_raw,
    additional_cols=additional_cols,
)
```

### 5. Use Cases

#### **A. Tạo Action List cho Collection Team**

```python
# Lọc các loan dự báo sẽ rơi vào DPD90+ tại MOB 12
high_risk_loans = df_enriched[
    (df_enriched["MOB"] == 12) &
    (df_enriched["STATE_FORECAST"].isin(["DPD90+", "DPD120+", "DPD180+", "WRITEOFF"]))
].copy()

# Export cho collection team
high_risk_loans.to_excel(
    "outputs/High_Risk_Loans_MOB12.xlsx",
    columns=["AGREEMENT_ID", "CUSTOMER_NAME", "BRANCH_CODE", 
             "STATE_FORECAST", "EAD_FORECAST", "PHONE_NUMBER"],
    index=False
)
```

#### **B. Phân Tích Theo Branch**

```python
# Tổng EAD rủi ro cao theo branch
branch_risk = (
    high_risk_loans.groupby("BRANCH_CODE")["EAD_FORECAST"]
    .sum()
    .sort_values(ascending=False)
)

print("Top 10 branches có EAD rủi ro cao nhất:")
print(branch_risk.head(10))
```

#### **C. Phân Tích Theo Customer Segment**

```python
# Tổng EAD theo customer segment
segment_risk = (
    df_enriched.groupby(["CUSTOMER_SEGMENT", "STATE_FORECAST"])["EAD_FORECAST"]
    .sum()
    .unstack(fill_value=0)
)

print(segment_risk)
```

### 6. Workflow Hoàn Chỉnh

```python
# ===== BƯỚC 1: Forecast cohort-level (đã có từ trước) =====
# df_lifecycle_final = ...

# ===== BƯỚC 2: Phân bổ xuống loan-level =====
df_allocated = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    forecast_only=True,
)

# ===== BƯỚC 3: Validate =====
compare_df = validate_allocation(df_allocated, df_lifecycle_final)

# ===== BƯỚC 4: Enrich =====
df_enriched = enrich_loan_forecast(
    df_allocated=df_allocated,
    df_raw=df_raw,
    additional_cols=["CUSTOMER_ID", "CUSTOMER_NAME", "BRANCH_CODE"],
)

# ===== BƯỚC 5: Phân tích & Export =====
# Tạo action list
high_risk = df_enriched[
    df_enriched["STATE_FORECAST"].isin(["DPD90+", "WRITEOFF"])
]

# Export
with pd.ExcelWriter("outputs/Loan_Level_Forecast.xlsx") as writer:
    df_enriched.to_excel(writer, sheet_name="All_Loans", index=False)
    high_risk.to_excel(writer, sheet_name="High_Risk", index=False)
    compare_df.to_excel(writer, sheet_name="Validation", index=False)
```

### 7. Lưu Ý Quan Trọng

1. **Allocation Method:**
   - Dùng `"proportional"` nếu cần giữ nguyên phân phối state
   - Dùng `"simple"` nếu cần 1 state per loan (dễ action)
   - Dùng `"equal"` nếu muốn phân bổ đều (ít dùng)

2. **Validation:**
   - Luôn chạy `validate_allocation()` sau khi phân bổ
   - Chênh lệch < 0.1% là OK
   - Chênh lệch > 1% cần kiểm tra lại

3. **Performance:**
   - Với data lớn (> 1M loans), dùng `simple` sẽ nhanh hơn
   - Có thể filter forecast_only=True để giảm data

4. **Random Seed:**
   - `simple` method dùng random sampling
   - Đã set `np.random.seed(42)` để reproducible
   - Có thể thay đổi seed nếu cần

### 8. Troubleshooting

**Vấn đề: Tổng EAD không khớp**
- Kiểm tra df_lifecycle_final có đủ các cột state không
- Kiểm tra df_raw có đủ loans trong cohort không
- Thử allocation_method khác

**Vấn đề: Thiếu loans trong kết quả**
- Kiểm tra VINTAGE_DATE có khớp giữa lifecycle và raw không
- Kiểm tra PRODUCT_TYPE, RISK_SCORE có khớp không
- Kiểm tra cutoff_date (chỉ lấy snapshot mới nhất)

**Vấn đề: Enrich thiếu columns**
- Kiểm tra additional_cols có tồn tại trong df_raw không
- Kiểm tra loan_id có unique không (có thể bị duplicate)

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15
