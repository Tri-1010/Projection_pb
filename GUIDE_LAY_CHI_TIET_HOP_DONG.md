# Hướng dẫn: Lấy chi tiết hợp đồng sau khi allocate forecast

## Câu hỏi: Tôi có thể lấy chi tiết hợp đồng sau khi allocate forecast lại từ bảng nào?

## Trả lời ngắn gọn

Sau khi allocate forecast, bạn có **2 cách** để lấy chi tiết hợp đồng:

### Cách 1: Tự động (Đã có sẵn trong kết quả allocate) ✅ KHUYẾN NGHỊ
```python
from src.rollrate.allocation import allocate_forecast_to_loans

# Allocate forecast xuống loan-level
df_loan_forecast = allocate_forecast_to_loans(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=12  # hoặc None cho tất cả MOB
)

# ✅ df_loan_forecast ĐÃ CÓ SẴN các cột từ df_raw:
# - AGREEMENT_ID (mã hợp đồng)
# - CUSTOMER_ID (mã khách hàng)
# - PRODUCT_TYPE (loại sản phẩm)
# - RISK_SCORE (điểm rủi ro)
# - DISBURSAL_DATE (ngày giải ngân)
# - BRANCH_CODE (mã chi nhánh)
# - ... và TẤT CẢ các cột khác từ df_raw

print(df_loan_forecast.columns)
# Output: ['AGREEMENT_ID', 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE', 
#          'MOB', 'STATE_FORECAST', 'EAD_FORECAST', 'CUSTOMER_ID', 
#          'BRANCH_CODE', 'PRODUCT_NAME', ...]
```

**Giải thích:**
- Hàm `allocate_forecast_to_loans()` **TỰ ĐỘNG** copy tất cả các cột từ `df_raw` vào kết quả
- Bạn **KHÔNG CẦN** merge thêm gì cả
- Xem code tại `src/rollrate/allocation.py` line 260-265:
  ```python
  # Thêm các cột khác từ df_raw (customer info, product info, ...)
  for col in df_loans_latest.columns:
      if col not in result_row and col != ead_col:
          result_row[col] = loan_row[col]
  ```

---

### Cách 2: Thêm cột bổ sung (Nếu cần thêm thông tin khác)
```python
from src.rollrate.allocation import enrich_loan_forecast

# Nếu bạn muốn thêm các cột cụ thể từ bảng khác
df_loan_forecast_enriched = enrich_loan_forecast(
    df_allocated=df_loan_forecast,
    df_raw=df_raw,
    additional_cols=[
        'CUSTOMER_NAME',
        'CUSTOMER_SEGMENT',
        'BRANCH_NAME',
        'PRODUCT_CATEGORY',
        'LOAN_PURPOSE',
        # ... các cột khác bạn cần
    ]
)
```

**Khi nào dùng Cách 2?**
- Khi bạn cần thêm thông tin từ bảng khác (không có trong `df_raw`)
- Khi bạn muốn chọn cụ thể các cột cần thiết (không lấy tất cả)

---

## Chi tiết: Các cột có sẵn trong kết quả allocate

### Cột từ lifecycle (cohort-level)
- `PRODUCT_TYPE` - Loại sản phẩm
- `RISK_SCORE` - Điểm rủi ro
- `VINTAGE_DATE` - Tháng giải ngân (cohort)
- `MOB` - Months on Book

### Cột từ allocation (kết quả phân bổ)
- `STATE_FORECAST` - Trạng thái dự báo (DPD0, DPD30+, WRITEOFF, ...)
- `EAD_FORECAST` - EAD dự báo
- `ALLOCATION_WEIGHT` - Trọng số phân bổ
- `IS_FORECAST` - 1 (forecast)
- `TARGET_MOB` - MOB được phân bổ (12, 24, ...)
- `MOB_CURRENT` - MOB hiện tại của loan

### Cột từ df_raw (chi tiết hợp đồng) ✅
- `AGREEMENT_ID` - Mã hợp đồng
- `CUSTOMER_ID` - Mã khách hàng
- `DISBURSAL_DATE` - Ngày giải ngân
- `CUTOFF_DATE` - Ngày snapshot
- `PRINCIPLE_OUTSTANDING` - Dư nợ gốc hiện tại
- `STATE_MODEL` - Trạng thái hiện tại
- **... và TẤT CẢ các cột khác từ df_raw**

---

## Ví dụ thực tế

### Ví dụ 1: Xem chi tiết hợp đồng forecast tại MOB 12
```python
# Allocate forecast tại MOB 12
df_loan_forecast = allocate_forecast_to_loans(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=12
)

# Xem chi tiết 10 hợp đồng đầu tiên
print(df_loan_forecast[[
    'AGREEMENT_ID',
    'CUSTOMER_ID',
    'PRODUCT_TYPE',
    'STATE_FORECAST',
    'EAD_FORECAST',
    'TARGET_MOB'
]].head(10))
```

### Ví dụ 2: Lọc hợp đồng có EAD forecast > 100M
```python
df_high_ead = df_loan_forecast[df_loan_forecast['EAD_FORECAST'] > 100_000_000]

print(f"Số hợp đồng có EAD > 100M: {len(df_high_ead):,}")
print(df_high_ead[[
    'AGREEMENT_ID',
    'CUSTOMER_ID',
    'PRODUCT_TYPE',
    'STATE_FORECAST',
    'EAD_FORECAST'
]])
```

### Ví dụ 3: Xuất ra Excel với chi tiết đầy đủ
```python
# Chọn các cột cần xuất
cols_to_export = [
    'AGREEMENT_ID',
    'CUSTOMER_ID',
    'PRODUCT_TYPE',
    'RISK_SCORE',
    'DISBURSAL_DATE',
    'MOB_CURRENT',
    'TARGET_MOB',
    'STATE_FORECAST',
    'EAD_FORECAST',
    'BRANCH_CODE',
    'PRODUCT_NAME',
]

df_loan_forecast[cols_to_export].to_excel(
    'Loan_Forecast_Details_MOB12.xlsx',
    index=False
)
```

### Ví dụ 4: Phân tích theo chi nhánh
```python
# Tổng EAD forecast theo chi nhánh và state
df_branch_summary = df_loan_forecast.groupby(
    ['BRANCH_CODE', 'STATE_FORECAST']
)['EAD_FORECAST'].sum().reset_index()

print(df_branch_summary)
```

---

## Tóm tắt

| Câu hỏi | Trả lời |
|---------|---------|
| **Lấy chi tiết từ bảng nào?** | Từ `df_raw` (bảng loan-level gốc) |
| **Cần merge thêm không?** | ❌ KHÔNG - Đã tự động merge trong `allocate_forecast_to_loans()` |
| **Các cột nào có sẵn?** | ✅ TẤT CẢ các cột từ `df_raw` + cột forecast |
| **Khi nào dùng `enrich_loan_forecast()`?** | Khi cần thêm cột từ bảng khác (không có trong `df_raw`) |

---

## Lưu ý quan trọng

### 1. df_raw phải có đầy đủ thông tin
Đảm bảo `df_raw` đã có các cột bạn cần:
```python
# Kiểm tra các cột có sẵn trong df_raw
print(df_raw.columns.tolist())

# Nếu thiếu cột, cần join từ bảng khác trước khi allocate
df_raw = df_raw.merge(df_customer_info, on='CUSTOMER_ID', how='left')
df_raw = df_raw.merge(df_branch_info, on='BRANCH_CODE', how='left')
```

### 2. Snapshot mới nhất
`allocate_forecast_to_loans()` tự động lấy snapshot mới nhất từ `df_raw`:
```python
# Code trong allocation.py (line 120-125)
latest_cutoff = df_raw[cutoff_col].max()
df_loans_latest = df_raw[df_raw[cutoff_col] == latest_cutoff].copy()
```

### 3. Kiểm tra kết quả
```python
# Kiểm tra số lượng hợp đồng
print(f"Tổng số hợp đồng forecast: {len(df_loan_forecast):,}")

# Kiểm tra các cột có sẵn
print(f"Số cột: {len(df_loan_forecast.columns)}")
print(df_loan_forecast.columns.tolist())

# Kiểm tra missing values
print(df_loan_forecast.isnull().sum())
```

---

## Kết luận

✅ **Bạn KHÔNG CẦN lấy từ bảng khác** - Chi tiết hợp đồng đã có sẵn trong kết quả `allocate_forecast_to_loans()`

✅ **Tất cả các cột từ df_raw** đã được tự động copy vào kết quả

✅ **Chỉ cần dùng `enrich_loan_forecast()`** nếu muốn thêm thông tin từ bảng khác (không có trong df_raw)
