# 📘 Complete Workflow Notebook

## 🎯 Mục Đích

Notebook **`Complete_Workflow.ipynb`** là workflow hoàn chỉnh từ đầu đến cuối:

1. ✅ Load & prepare data
2. ✅ Build transition matrices
3. ✅ Forecast lifecycle
4. ✅ Calibration (k per MOB)
5. ✅ Allocate xuống loan-level (MOB 12 & 24)
6. ✅ Export reports

---

## 🚀 Cách Sử Dụng

### 1. Chuẩn Bị

```bash
# Cài đặt dependencies (nếu chưa có)
pip install pandas numpy matplotlib seaborn openpyxl xlsxwriter cvxpy scipy
```

### 2. Cấu Hình Data Path

Mở notebook và sửa dòng này:

```python
DATA_PATH = 'C:/Users/User/Projection_kiro/ETB_Parquet'  # 🔥 Thay đổi path của bạn
```

### 3. Chạy Notebook

```bash
jupyter notebook notebooks/Complete_Workflow.ipynb
```

Hoặc trong VS Code: Open notebook → Run All Cells

---

## ⏱️ Thời Gian Chạy

- **Data nhỏ** (< 100K loans): ~2-3 phút
- **Data trung bình** (100K-500K loans): ~5-10 phút
- **Data lớn** (> 500K loans): ~15-20 phút

---

## 📊 Outputs

Sau khi chạy xong, bạn sẽ có 3 files Excel trong folder `outputs/`:

### 1. `Lifecycle_All_Products_YYYYMMDD_HHMMSS.xlsx`

**Cohort-level forecast** với nhiều sheets:

- **PORTFOLIO_ALL_DEL30**: Portfolio DEL30% (heatmap)
- **PORTFOLIO_ALL_DEL60**: Portfolio DEL60% (heatmap)
- **PORTFOLIO_ALL_DEL90**: Portfolio DEL90% (heatmap)
- **PRODUCT_A_DEL30**: Product A DEL30% (heatmap)
- **PRODUCT_A_DEL60**: Product A DEL60% (heatmap)
- **PRODUCT_A_DEL90**: Product A DEL90% (heatmap)
- ... (các products khác)

**Features:**
- ✅ Heatmap màu (xanh → vàng → đỏ)
- ✅ Forecast rows highlight vàng
- ✅ Boundary đỏ đậm (actual cuối)
- ✅ Format % tự động
- ✅ No gridlines

### 2. `Loan_Forecast_MOB12_24_YYYYMMDD_HHMMSS.xlsx`

**Loan-level forecast** tại MOB 12 và 24:

- **All_Loans**: Tất cả loans với forecast
- **DEL30_MOB12**: Loans có DEL30=1 tại MOB 12
- **DEL30_MOB24**: Loans có DEL30=1 tại MOB 24
- **DEL90_MOB12**: Loans có DEL90=1 tại MOB 12
- **DEL90_MOB24**: Loans có DEL90=1 tại MOB 24
- **Summary**: Tổng hợp số liệu

**Columns:**
```
AGREEMENT_ID | PRODUCT_TYPE | RISK_SCORE | VINTAGE_DATE | MOB_CURRENT | EAD_CURRENT |
STATE_FORECAST_MOB12 | EAD_FORECAST_MOB12 | DEL30_FLAG_MOB12 | DEL90_FLAG_MOB12 |
STATE_FORECAST_MOB24 | EAD_FORECAST_MOB24 | DEL30_FLAG_MOB24 | DEL90_FLAG_MOB24
```

### 3. `Calibration_k_values_YYYYMMDD_HHMMSS.xlsx`

**Calibration k values:**

- **k_values**: k_raw, k_smooth, k_final theo MOB
- **k_raw_detail**: Chi tiết k_raw per vintage (nếu có)

---

## 📈 Visualizations

Notebook tự động tạo các charts:

1. **k Curves**: k_raw vs k_smooth vs k_final
2. **DEL90% by Product**: Bar chart so sánh MOB 12 vs 24

---

## 🔧 Tùy Chỉnh

### Thay Đổi Max MOB

```python
max_mob = 36  # Thay đổi thành 48, 60, ...
```

### Thay Đổi Target MOBs cho Allocation

```python
df_loan_forecast = allocate_multi_mob_with_del_metrics(
    ...,
    target_mobs=[12, 24, 36],  # Thêm MOB 36
    ...
)
```

### Thay Đổi Calibration Method

```python
k_raw_by_mob, _, _ = fit_k_raw(
    ...,
    method="wls_reg",  # Thay vì "wls"
    lambda_k=0.1,      # Regularization
    k_prior=1.0,
    ...
)
```

### Thay Đổi Smoothing Gamma

```python
k_smooth_by_mob, _, _ = smooth_k(
    ...,
    gamma=20.0,  # Tăng gamma → smooth hơn
    ...
)
```

---

## 🆘 Troubleshooting

### Vấn đề: "No module named 'src'"

**Giải pháp:**
```python
# Kiểm tra path
import sys
print(sys.path)

# Thêm project root
project_root = Path(".").resolve().parent
sys.path.insert(0, str(project_root))
```

### Vấn đề: "Memory Error"

**Giải pháp:**
- Giảm `max_mob` (ví dụ: 24 thay vì 36)
- Filter data theo product trước khi chạy
- Tăng RAM hoặc chạy trên server

### Vấn đề: "Không có forecast tại MOB 12"

**Giải pháp:**
```python
# Kiểm tra max forecast MOB
max_forecast_mob = df_lifecycle_final[
    df_lifecycle_final["IS_FORECAST"] == 1
]["MOB"].max()

print(f"Max forecast MOB: {max_forecast_mob}")

# Nếu < 12 → Tăng max_mob
```

### Vấn đề: "k_raw rỗng"

**Giải pháp:**
- Kiểm tra data có đủ vintages không (cần ít nhất 5-10 vintages)
- Giảm `min_obs` trong `fit_k_raw()`
- Kiểm tra DISB_TOTAL có đúng không

---

## 📚 Tài Liệu Liên Quan

- **guide.md**: Hướng dẫn đầy đủ về Calibration
- **QUICK_GUIDE_MULTI_MOB.md**: Hướng dẫn nhanh multi-MOB allocation
- **docs/MOB_SELECTION_GUIDE.md**: Chi tiết về MOB selection

---

## 💡 Tips

1. **Chạy từng section riêng lẻ** để debug dễ hơn
2. **Save intermediate results** (df_lifecycle, k_final_by_mob) để tránh chạy lại
3. **Check memory usage** trước khi chạy allocation (có thể tốn RAM)
4. **Backup outputs** trước khi chạy lại (files sẽ bị overwrite)

---

## 🎓 Workflow Diagram

```
┌─────────────────┐
│  1. Load Data   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Build Matrix │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Lifecycle    │
│  (Actual+FC)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Calibration  │
│  (k per MOB)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Apply k      │
│  & Aggregate    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. Allocate     │
│  (Loan-level)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. Analysis &   │
│  Visualization  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 8. Export       │
│  Reports        │
└─────────────────┘
```

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15  
**Version:** 1.0
