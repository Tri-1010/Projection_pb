# Hướng Dẫn Export Chi Tiết Forecast Cho Specific Cohorts

## 🎯 Mục Đích

Export tất cả thông số cần thiết để tính forecast cho các cohorts cụ thể, dùng để:
- Gửi cho sếp xem chi tiết cách tính toán
- Verify kết quả forecast
- Hiểu rõ từng bước tính toán

## 📊 Nội Dung Export

File Excel sẽ chứa các sheets sau:

### 1. **Summary**
Tổng quan các cohorts:
- Product, Risk_Score, Vintage_Date
- Số lượng loans
- Total Disbursement
- Current MOB và EAD
- Target MOB

### 2. **TM_[Product]_[Score]**
Transition matrices theo segment:
- Tất cả transition matrices từ MOB 0 đến target_mob
- Format: MOB | From_State | To_State_1 | To_State_2 | ...

### 3. **K_Values**
Giá trị K và Alpha:
- K_Raw: K chưa smooth
- K_Smooth: K đã smooth (dùng để forecast)
- Alpha: Hệ số smooth

### 4. **Actual_[Product]_[Score]**
Dữ liệu thực tế theo MOB:
- EAD theo từng state
- DEL30, DEL60, DEL90

### 5. **Forecast_Steps**
Chi tiết từng bước tính forecast:
- From_MOB → To_MOB
- K value
- Total EAD
- DEL30, DEL60, DEL90
- DEL rates (%)

### 6. **Instructions**
Hướng dẫn sử dụng và công thức tính toán

---

## 🚀 Cách Sử Dụng

### Bước 1: Chạy Final_Workflow copy đến hết phần build model

```python
# Chạy các cells:
# 1. Load data
# 2. Build transition matrices
# 3. Build lifecycle + calibration
```

### Bước 2: Import function

```python
from export_cohort_details import export_cohort_forecast_details
```

### Bước 3: Define cohorts cần export

```python
# Ví dụ: Export 3 cohorts
cohorts = [
    ('X', 'A', '2025-10-01'),  # Product X, Risk Score A, Vintage Oct 2025
    ('X', 'B', '2024-10-01'),  # Product X, Risk Score B, Vintage Oct 2024
    ('T', 'A', '2025-10-01'),  # Product T, Risk Score A, Vintage Oct 2025
]
```

**Lưu ý**: 
- Product: Lấy từ PRODUCT_TYPE trong data
- Risk_Score: Lấy từ RISK_SCORE (đã được tạo từ SEGMENT_COLS)
- Vintage_Date: Format 'YYYY-MM-DD' hoặc 'YYYY-MM-01'

### Bước 4: Export

```python
filename = export_cohort_forecast_details(
    cohorts=cohorts,
    df_raw=df_raw,
    matrices_by_mob=matrices_by_mob,
    k_raw_by_mob=k_raw_by_mob,
    k_smooth_by_mob=k_smooth_by_mob,
    alpha_by_mob=alpha_by_mob,
    target_mob=24,  # Hoặc TARGET_MOBS[0]
    output_dir='cohort_details',
)

print(f'✅ Exported: {filename}')
```

---

## 📝 Ví Dụ Đầy Đủ

### Code trong notebook:

```python
# ============================
# EXPORT CHI TIẾT CHO SẾP
# ============================

from export_cohort_details import export_cohort_forecast_details

# Define cohorts cần export
cohorts = [
    # Product X
    ('X', 'A', '2025-10-01'),
    ('X', 'A', '2024-10-01'),
    ('X', 'B', '2025-10-01'),
    ('X', 'B', '2024-10-01'),
    
    # Product T
    ('T', 'A', '2025-10-01'),
    ('T', 'A', '2024-10-01'),
]

# Export
filename = export_cohort_forecast_details(
    cohorts=cohorts,
    df_raw=df_raw,
    matrices_by_mob=matrices_by_mob,
    k_raw_by_mob=k_raw_by_mob,
    k_smooth_by_mob=k_smooth_by_mob,
    alpha_by_mob=alpha_by_mob,
    target_mob=24,
    output_dir='cohort_details',
)

print(f'✅ File đã sẵn sàng gửi cho sếp: {filename}')
```

### Output:

```
📊 Exporting forecast details for 6 cohorts...
   Target MOB: 24
   Output: cohort_details/Cohort_Forecast_Details_20260118_143022.xlsx
✅ Exported to: cohort_details/Cohort_Forecast_Details_20260118_143022.xlsx
   📊 6 cohorts
   📄 15 sheets
✅ File đã sẵn sàng gửi cho sếp: cohort_details/Cohort_Forecast_Details_20260118_143022.xlsx
```

---

## 📊 Cách Đọc File Excel

### Sheet "Summary"

| Product | Risk_Score | Vintage_Date | N_Loans | Total_Disbursement | Current_MOB | Current_EAD | Target_MOB | Forecast_MOBs |
|---------|------------|--------------|---------|-------------------|-------------|-------------|------------|---------------|
| X | A | 2025-10-01 | 1,234 | 123,456,789 | 2 | 120,000,000 | 24 | 22 |
| X | B | 2024-10-01 | 2,345 | 234,567,890 | 14 | 180,000,000 | 24 | 10 |

**Giải thích**:
- Cohort X-A-2025-10 hiện tại ở MOB 2, cần forecast đến MOB 24 (22 bước)
- Cohort X-B-2024-10 hiện tại ở MOB 14, cần forecast đến MOB 24 (10 bước)

### Sheet "TM_X_A" (Transition Matrix)

| MOB | From_State | DPD0 | DPD1+ | DPD30+ | DPD60+ | ... |
|-----|------------|------|-------|--------|--------|-----|
| 0 | DPD0 | 0.95 | 0.03 | 0.01 | 0.01 | ... |
| 0 | DPD1+ | 0.20 | 0.60 | 0.15 | 0.05 | ... |
| 1 | DPD0 | 0.94 | 0.04 | 0.01 | 0.01 | ... |
| 1 | DPD1+ | 0.18 | 0.62 | 0.15 | 0.05 | ... |

**Giải thích**:
- Dòng 1: Tại MOB 0, loans ở DPD0 có 95% xác suất ở DPD0, 3% chuyển sang DPD1+, ...
- Dòng 2: Tại MOB 0, loans ở DPD1+ có 20% xác suất về DPD0, 60% ở DPD1+, ...

### Sheet "K_Values"

| Product | Risk_Score | Vintage_Date | MOB | K_Raw | K_Smooth | Alpha |
|---------|------------|--------------|-----|-------|----------|-------|
| X | A | 2025-10-01 | 0 | 1.05 | 1.03 | 0.3 |
| X | A | 2025-10-01 | 1 | 1.08 | 1.05 | 0.3 |
| X | A | 2025-10-01 | 2 | 1.02 | 1.04 | 0.3 |

**Giải thích**:
- K_Raw: K tính từ actual data (có thể volatile)
- K_Smooth: K đã smooth (dùng để forecast, stable hơn)
- Alpha: Hệ số smooth (0.3 = 30% weight cho K_Raw, 70% cho K trước đó)

### Sheet "Forecast_Steps"

| Product | Risk_Score | Vintage_Date | From_MOB | To_MOB | K | Total_EAD | DEL30 | DEL90 | DEL30_PCT | DEL90_PCT |
|---------|------------|--------------|----------|--------|---|-----------|-------|-------|-----------|-----------|
| X | A | 2025-10-01 | 2 | 3 | 1.04 | 120,000,000 | 8,400,000 | 3,600,000 | 7.00% | 3.00% |
| X | A | 2025-10-01 | 3 | 4 | 1.05 | 118,000,000 | 9,440,000 | 4,130,000 | 8.00% | 3.50% |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| X | A | 2025-10-01 | 23 | 24 | 1.03 | 95,000,000 | 11,400,000 | 5,700,000 | 12.00% | 6.00% |

**Giải thích**:
- Mỗi dòng là 1 bước forecast
- Dòng cuối cùng (To_MOB = 24) là kết quả cuối cùng
- DEL30_PCT = 12.00% là forecast DEL30 tại MOB 24

---

## 🧮 Công Thức Tính Toán

### Bước 1: Khởi tạo vector state

```python
# Tại MOB hiện tại (ví dụ MOB 2)
v_current = [
    EAD_DPD0,      # 100,000,000
    EAD_DPD1+,     # 15,000,000
    EAD_DPD30+,    # 3,000,000
    EAD_DPD60+,    # 1,500,000
    EAD_DPD90+,    # 500,000
    ...
]
Total = 120,000,000
```

### Bước 2: Forecast từ MOB 2 → 3

```python
# 1. Lấy transition matrix P tại MOB 2
P = TM_X_A[MOB=2]

# 2. Markov forecast
v_markov = v_current @ P
# = [95,000,000, 18,000,000, 4,500,000, 2,000,000, 500,000, ...]

# 3. Lấy K tại MOB 2
K = 1.04

# 4. Apply K
v_forecast = v_markov * K
# = [98,800,000, 18,720,000, 4,680,000, 2,080,000, 520,000, ...]

# 5. Tính DEL
DEL30 = v_forecast[DPD30+] + v_forecast[DPD60+] + v_forecast[DPD90+] + ...
      = 4,680,000 + 2,080,000 + 520,000 + ...
      = 8,400,000

DEL30_PCT = 8,400,000 / 120,000,000 = 7.00%
```

### Bước 3: Lặp lại cho MOB 3 → 4, 4 → 5, ..., 23 → 24

```python
v_current = v_forecast  # Update
# Lặp lại bước 2
```

### Bước 4: Kết quả cuối cùng tại MOB 24

```python
# Xem sheet "Forecast_Steps" dòng cuối cùng
DEL30_PCT @ MOB 24 = 12.00%
DEL90_PCT @ MOB 24 = 6.00%
```

---

## 💡 Tips

### 1. Chọn Cohorts Đại Diện

```python
# Chọn cohorts có:
# - Số lượng loans lớn (representative)
# - Vintage gần đây (relevant)
# - Risk scores khác nhau (diverse)

cohorts = [
    # High volume, recent
    ('X', 'A', '2025-10-01'),
    ('X', 'B', '2025-10-01'),
    
    # High volume, older (for comparison)
    ('X', 'A', '2024-10-01'),
    ('X', 'B', '2024-10-01'),
]
```

### 2. Verify Kết Quả

```python
# So sánh với lifecycle output
df_lifecycle_check = df_lifecycle_final[
    (df_lifecycle_final['PRODUCT_TYPE'] == 'X') &
    (df_lifecycle_final['RISK_SCORE'] == 'A') &
    (df_lifecycle_final['VINTAGE_DATE'] == '2025-10-01') &
    (df_lifecycle_final['MOB'] == 24)
]

print(df_lifecycle_check[['DEL30_PCT', 'DEL90_PCT']])
# Should match với sheet "Forecast_Steps" dòng cuối cùng
```

### 3. Giải Thích Cho Sếp

**Điểm nhấn**:
- ✅ Dữ liệu thực tế (sheet Actual_*)
- ✅ Transition matrices (sheet TM_*)
- ✅ K values (sheet K_Values)
- ✅ Từng bước tính toán (sheet Forecast_Steps)
- ✅ Kết quả cuối cùng (dòng cuối sheet Forecast_Steps)

**Câu chuyện**:
1. "Đây là dữ liệu thực tế của cohort X-A-2025-10 tại MOB 2"
2. "Chúng ta dùng transition matrix này để forecast"
3. "Apply K = 1.04 để điều chỉnh"
4. "Kết quả: DEL30 @ MOB 24 = 12.00%"

---

## 🎯 Checklist Trước Khi Gửi Sếp

- [ ] Đã chọn cohorts đại diện
- [ ] Đã verify kết quả với lifecycle output
- [ ] Đã kiểm tra tất cả sheets có data
- [ ] Đã đọc sheet Instructions
- [ ] Đã chuẩn bị câu chuyện giải thích

---

**Date**: 2026-01-18  
**File**: `export_cohort_details.py`  
**Output**: `cohort_details/Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx`
