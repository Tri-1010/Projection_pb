# 📘 Hướng Dẫn: Thêm Cột Từ Data Gốc Vào Report Allocation

## 🎯 Tổng Quan

Khi phân bổ forecast xuống loan-level, bạn có thể muốn thêm các cột từ data gốc vào report, ví dụ:
- Thông tin khách hàng: `CUSTOMER_ID`, `CUSTOMER_NAME`, `PHONE`, `EMAIL`
- Thông tin hợp đồng: `BRANCH_CODE`, `OFFICER_CODE`, `COLLATERAL_TYPE`
- Thông tin sản phẩm: `TERM`, `INTEREST_RATE`, `LOAN_PURPOSE`

## 📍 Vị Trí Cần Sửa

File: `src/rollrate/allocation_v2_fast.py`

Hàm: `allocate_multi_mob_fast()` (hoặc `allocate_multi_mob_with_scaling_fast()`)

Dòng: ~409-424

---

## 🔧 Cách Thêm Cột

### **Bước 1: Tìm đoạn code `base_cols`**

Mở file `src/rollrate/allocation_v2_fast.py`, tìm đoạn:

```python
# Các cột cần lấy từ df_loans_latest
base_cols = [
    loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
    CFG["mob"], CFG["ead"], CFG["state"]
]

# Thêm DISBURSAL_DATE, DISBURSAL_AMOUNT nếu có
orig_date_col = CFG.get("orig_date", "DISBURSAL_DATE")
disb_amt_col = CFG.get("disb", "DISBURSAL_AMOUNT")

if orig_date_col in df.columns:
    base_cols.append(orig_date_col)
if disb_amt_col in df.columns:
    base_cols.append(disb_amt_col)
```

### **Bước 2: Thêm cột mới vào `base_cols`**

**Cách 1: Thêm trực tiếp vào list**

```python
# Các cột cần lấy từ df_loans_latest
base_cols = [
    loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
    CFG["mob"], CFG["ead"], CFG["state"],
    # ===== THÊM CÁC CỘT MỚI Ở ĐÂY =====
    'CUSTOMER_ID',
    'CUSTOMER_NAME',
    'BRANCH_CODE',
    'OFFICER_CODE',
    'TERM',
    'INTEREST_RATE',
    # ===================================
]
```

**Cách 2: Thêm có điều kiện (nếu cột tồn tại)**

```python
# Thêm DISBURSAL_DATE, DISBURSAL_AMOUNT nếu có
orig_date_col = CFG.get("orig_date", "DISBURSAL_DATE")
disb_amt_col = CFG.get("disb", "DISBURSAL_AMOUNT")

if orig_date_col in df.columns:
    base_cols.append(orig_date_col)
if disb_amt_col in df.columns:
    base_cols.append(disb_amt_col)

# ===== THÊM CÁC CỘT MỚI (CÓ ĐIỀU KIỆN) =====
if 'CUSTOMER_ID' in df.columns:
    base_cols.append('CUSTOMER_ID')
if 'CUSTOMER_NAME' in df.columns:
    base_cols.append('CUSTOMER_NAME')
if 'BRANCH_CODE' in df.columns:
    base_cols.append('BRANCH_CODE')
if 'OFFICER_CODE' in df.columns:
    base_cols.append('OFFICER_CODE')
if 'TERM' in df.columns:
    base_cols.append('TERM')
if 'INTEREST_RATE' in df.columns:
    base_cols.append('INTEREST_RATE')
# ============================================
```

**Cách 3: Thêm nhiều cột cùng lúc**

```python
# ===== THÊM NHIỀU CỘT CÙNG LÚC =====
additional_cols = [
    'CUSTOMER_ID',
    'CUSTOMER_NAME', 
    'BRANCH_CODE',
    'OFFICER_CODE',
    'TERM',
    'INTEREST_RATE',
    'COLLATERAL_TYPE',
    'LOAN_PURPOSE',
    'PHONE',
    'EMAIL',
]

# Chỉ thêm các cột có trong data
for col in additional_cols:
    if col in df.columns:
        base_cols.append(col)
# ====================================
```

### **Bước 3: Lưu file và chạy lại**

Sau khi sửa xong, lưu file và chạy lại notebook:

```python
from src.rollrate.allocation_v2_fast import allocate_multi_mob_with_scaling_fast

df_loan_forecast = allocate_multi_mob_with_scaling_fast(
    df_loans_latest=df_loans_latest,
    df_lifecycle_final=df_lifecycle_final,
    matrices_by_mob=matrices_by_mob,
    target_mobs=[12, 24],
    parent_fallback=parent_fallback,
    include_del30=True,
    include_del90=True,
    seed=42
)

# Kiểm tra các cột mới đã có chưa
print(df_loan_forecast.columns.tolist())
```

---

## 📋 Ví Dụ Cụ Thể

### **Ví Dụ 1: Thêm thông tin khách hàng**

**Trước khi sửa:**
```python
base_cols = [
    loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
    CFG["mob"], CFG["ead"], CFG["state"]
]
```

**Sau khi sửa:**
```python
base_cols = [
    loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
    CFG["mob"], CFG["ead"], CFG["state"],
    'CUSTOMER_ID',      # Thêm mã khách hàng
    'CUSTOMER_NAME',    # Thêm tên khách hàng
    'PHONE',            # Thêm số điện thoại
    'EMAIL',            # Thêm email
]
```

**Kết quả:**
```python
df_loan_forecast.head()
```

| AGREEMENT_ID | CUSTOMER_ID | CUSTOMER_NAME | PHONE | EMAIL | STATE_FORECAST_MOB12 | EAD_FORECAST_MOB12 | DEL90_FLAG_MOB12 |
|--------------|-------------|---------------|-------|-------|----------------------|--------------------|------------------|
| L001 | C001 | Nguyen Van A | 0901234567 | a@email.com | DPD0 | 100M | 0 |
| L002 | C002 | Tran Thi B | 0907654321 | b@email.com | DPD30+ | 50M | 0 |

---

### **Ví Dụ 2: Thêm thông tin chi nhánh và nhân viên**

**Sau khi sửa:**
```python
base_cols = [
    loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
    CFG["mob"], CFG["ead"], CFG["state"],
    'BRANCH_CODE',      # Thêm mã chi nhánh
    'BRANCH_NAME',      # Thêm tên chi nhánh
    'OFFICER_CODE',     # Thêm mã nhân viên
    'OFFICER_NAME',     # Thêm tên nhân viên
]
```

**Use case:** Tạo action list cho từng chi nhánh

```python
# Lọc loans có DEL90 flag = 1 tại MOB 12
high_risk = df_loan_forecast[df_loan_forecast['DEL90_FLAG_MOB12'] == 1]

# Tổng hợp theo chi nhánh
branch_summary = high_risk.groupby('BRANCH_CODE').agg({
    'AGREEMENT_ID': 'count',
    'EAD_DEL90_MOB12': 'sum'
}).rename(columns={
    'AGREEMENT_ID': 'High_Risk_Count',
    'EAD_DEL90_MOB12': 'Total_EAD_DEL90'
})

print(branch_summary)
```

---

### **Ví Dụ 3: Thêm thông tin sản phẩm**

**Sau khi sửa:**
```python
base_cols = [
    loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
    CFG["mob"], CFG["ead"], CFG["state"],
    'TERM',             # Thêm kỳ hạn
    'INTEREST_RATE',    # Thêm lãi suất
    'COLLATERAL_TYPE',  # Thêm loại tài sản đảm bảo
    'LOAN_PURPOSE',     # Thêm mục đích vay
]
```

**Use case:** Phân tích DEL90 theo kỳ hạn

```python
# Phân tích DEL90 rate theo TERM
term_analysis = df_loan_forecast.groupby('TERM').agg({
    'DISBURSAL_AMOUNT': 'sum',
    'EAD_DEL90_MOB12': 'sum'
})

term_analysis['DEL90_RATE'] = (
    term_analysis['EAD_DEL90_MOB12'] / term_analysis['DISBURSAL_AMOUNT'] * 100
)

print(term_analysis)
```

---

## 🔍 Kiểm Tra Kết Quả

Sau khi thêm cột, kiểm tra:

```python
# 1. Xem tất cả các cột
print("Các cột trong df_loan_forecast:")
print(df_loan_forecast.columns.tolist())

# 2. Kiểm tra cột mới có data không
print("\nSample data:")
print(df_loan_forecast[['AGREEMENT_ID', 'CUSTOMER_ID', 'CUSTOMER_NAME', 'BRANCH_CODE']].head())

# 3. Kiểm tra missing values
print("\nMissing values:")
print(df_loan_forecast[['CUSTOMER_ID', 'CUSTOMER_NAME', 'BRANCH_CODE']].isna().sum())

# 4. Kiểm tra số lượng unique values
print("\nUnique values:")
print(f"CUSTOMER_ID: {df_loan_forecast['CUSTOMER_ID'].nunique()}")
print(f"BRANCH_CODE: {df_loan_forecast['BRANCH_CODE'].nunique()}")
```

---

## ⚠️ Lưu Ý Quan Trọng

### 1. **Tên cột phải khớp với data gốc**

```python
# ❌ SAI: Tên cột không tồn tại trong data
base_cols.append('CUSTOMER_FULL_NAME')  # Data có tên là 'CUSTOMER_NAME'

# ✅ ĐÚNG: Kiểm tra trước khi thêm
if 'CUSTOMER_NAME' in df.columns:
    base_cols.append('CUSTOMER_NAME')
```

### 2. **Tránh duplicate columns**

Code đã có xử lý:
```python
# Loại bỏ duplicate columns
base_cols = list(dict.fromkeys(base_cols))
```

Nhưng nếu bạn thêm cột đã có trong list ban đầu, nó sẽ bị duplicate.

### 3. **Cột phải có trong df_loans_latest**

```python
# Code tự động lọc các cột có trong data
loan_info = df[[c for c in base_cols if c in df.columns]].copy()
```

Nếu cột không có trong `df_loans_latest`, nó sẽ bị bỏ qua (không báo lỗi).

### 4. **Không thêm quá nhiều cột**

- Mỗi cột thêm vào sẽ làm tăng kích thước file Excel
- Nếu có > 100 cột, Excel có thể chậm
- Chỉ thêm các cột thực sự cần thiết

---

## 📊 Use Cases Phổ Biến

### **1. Tạo Action List cho Collection Team**

Thêm cột:
```python
base_cols.extend([
    'CUSTOMER_ID',
    'CUSTOMER_NAME',
    'PHONE',
    'EMAIL',
    'BRANCH_CODE',
    'OFFICER_CODE',
])
```

Export:
```python
high_risk = df_loan_forecast[df_loan_forecast['DEL90_FLAG_MOB12'] == 1]
high_risk.to_excel(
    "Collection_Action_List.xlsx",
    columns=['AGREEMENT_ID', 'CUSTOMER_NAME', 'PHONE', 'BRANCH_CODE', 
             'EAD_DEL90_MOB12', 'STATE_FORECAST_MOB12'],
    index=False
)
```

### **2. Báo Cáo Theo Chi Nhánh**

Thêm cột:
```python
base_cols.extend([
    'BRANCH_CODE',
    'BRANCH_NAME',
    'REGION',
])
```

Phân tích:
```python
branch_report = df_loan_forecast.groupby('BRANCH_CODE').agg({
    'AGREEMENT_ID': 'count',
    'DISBURSAL_AMOUNT': 'sum',
    'EAD_DEL90_MOB12': 'sum',
}).rename(columns={'AGREEMENT_ID': 'Loan_Count'})

branch_report['DEL90_RATE'] = (
    branch_report['EAD_DEL90_MOB12'] / branch_report['DISBURSAL_AMOUNT'] * 100
)
```

### **3. Phân Tích Theo Sản Phẩm**

Thêm cột:
```python
base_cols.extend([
    'TERM',
    'INTEREST_RATE',
    'COLLATERAL_TYPE',
    'LOAN_PURPOSE',
])
```

Phân tích:
```python
product_analysis = df_loan_forecast.groupby(['PRODUCT_TYPE', 'TERM']).agg({
    'DISBURSAL_AMOUNT': 'sum',
    'EAD_DEL90_MOB12': 'sum',
})

product_analysis['DEL90_RATE'] = (
    product_analysis['EAD_DEL90_MOB12'] / product_analysis['DISBURSAL_AMOUNT'] * 100
)
```

---

## 🔧 Code Mẫu Hoàn Chỉnh

Đây là code mẫu đã thêm đầy đủ các cột thông dụng:

```python
# Các cột cần lấy từ df_loans_latest
base_cols = [
    loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
    CFG["mob"], CFG["ead"], CFG["state"]
]

# Thêm DISBURSAL_DATE, DISBURSAL_AMOUNT nếu có
orig_date_col = CFG.get("orig_date", "DISBURSAL_DATE")
disb_amt_col = CFG.get("disb", "DISBURSAL_AMOUNT")

if orig_date_col in df.columns:
    base_cols.append(orig_date_col)
if disb_amt_col in df.columns:
    base_cols.append(disb_amt_col)

# ===== THÊM CÁC CỘT BỔ SUNG =====
additional_cols = [
    # Thông tin khách hàng
    'CUSTOMER_ID',
    'CUSTOMER_NAME',
    'PHONE',
    'EMAIL',
    'ID_NUMBER',
    'DATE_OF_BIRTH',
    'GENDER',
    
    # Thông tin chi nhánh & nhân viên
    'BRANCH_CODE',
    'BRANCH_NAME',
    'REGION',
    'OFFICER_CODE',
    'OFFICER_NAME',
    
    # Thông tin sản phẩm
    'TERM',
    'INTEREST_RATE',
    'COLLATERAL_TYPE',
    'COLLATERAL_VALUE',
    'LOAN_PURPOSE',
    'LTV_RATIO',
    
    # Thông tin khác
    'APPROVAL_DATE',
    'FIRST_PAYMENT_DATE',
    'MATURITY_DATE',
]

# Chỉ thêm các cột có trong data
for col in additional_cols:
    if col in df.columns:
        base_cols.append(col)
# ====================================

# Loại bỏ duplicate columns
base_cols = list(dict.fromkeys(base_cols))

loan_info = df[[c for c in base_cols if c in df.columns]].copy()
```

---

## 📚 Tài Liệu Liên Quan

- `src/rollrate/allocation_v2_fast.py`: Code allocation
- `docs/ALLOCATION_DETAILED_EXPLANATION.md`: Giải thích chi tiết allocation
- `notebooks/Final_Workflow.ipynb`: Ví dụ sử dụng

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-16
