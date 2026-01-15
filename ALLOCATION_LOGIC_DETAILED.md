# 📘 Hướng dẫn chi tiết: Logic Allocation (Phân bổ forecast xuống loan-level)

## 🎯 Mục đích

Document này giải thích **CHI TIẾT** logic phân bổ forecast từ cohort-level xuống loan-level, bao gồm:
1. Input data (dữ liệu đầu vào)
2. Logic tính toán từng bước
3. Output data (dữ liệu đầu ra)
4. Validation (kiểm tra kết quả)
5. Ví dụ minh họa cụ thể

---

## 📊 Tổng quan

### Vấn đề cần giải quyết

**Input:** Forecast ở cohort-level (Product × Risk × Vintage × MOB)
```
PRODUCT | RISK | VINTAGE   | MOB | DPD0 | DPD30+ | WRITEOFF | PREPAY | Total
--------|------|-----------|-----|------|--------|----------|--------|------
SALPIL  | LOW  | 2024-01   | 12  | 600  | 150    | 0        | 0      | 750
```

**Output:** Forecast ở loan-level (từng hợp đồng)
```
AGREEMENT_ID | PRODUCT | RISK | VINTAGE   | MOB_CURRENT | EAD_CURRENT | STATE_FORECAST | EAD_FORECAST
-------------|---------|------|-----------|-------------|-------------|----------------|-------------
LOAN_001     | SALPIL  | LOW  | 2024-01   | 1           | 100         | DPD0           | 75
LOAN_002     | SALPIL  | LOW  | 2024-01   | 1           | 100         | DPD30+         | 75
...
```

### Câu hỏi quan trọng

1. **Làm sao phân bổ EAD từ cohort xuống từng loan?**
   - Tổng EAD cohort = 750
   - Tổng EAD current của 10 loans = 1,000
   - → Mỗi loan nhận bao nhiêu EAD forecast?

2. **Làm sao assign state cho từng loan?**
   - Cohort có 600 DPD0, 150 DPD30+
   - 10 loans → loan nào DPD0, loan nào DPD30+?

3. **Tại sao EAD_FORECAST < EAD_CURRENT?**
   - Do prepayment, writeoff, amortization

---

## 🔢 Logic chi tiết: `allocate_forecast_to_loans_simple()`

### Bước 1: Chuẩn bị dữ liệu

#### ⚠️ Quan trọng: EAD_CURRENT từ snapshot mới nhất

**EAD_CURRENT được lấy từ CUTOFF_DATE gần nhất:**

```python
# Lấy snapshot mới nhất
latest_cutoff = df_raw['CUTOFF_DATE'].max()
df_loans_latest = df_raw[df_raw['CUTOFF_DATE'] == latest_cutoff]

# EAD_CURRENT = PRINCIPLE_OUTSTANDING tại snapshot mới nhất
# MOB_CURRENT = MOB tại snapshot mới nhất
```

**Ví dụ:**
```
Loan LOAN_001 có 3 snapshots:
- 2024-10-31: MOB=1, EAD=100
- 2024-11-30: MOB=2, EAD=98
- 2024-12-31: MOB=3, EAD=95 ← Lấy từ đây

→ EAD_CURRENT = 95 (không phải 100 hay 98)
→ MOB_CURRENT = 3 (không phải 1 hay 2)
```

**Tại sao?**
- Phản ánh tình trạng hiện tại
- Tránh duplicate loans (1 loan chỉ xuất hiện 1 lần)
- Consistency với lifecycle forecast

**Xem chi tiết:** `CLARIFICATION_EAD_CURRENT_MOB.md`

---

#### Input 1: Lifecycle forecast (cohort-level)

```python
df_lifecycle_final = pd.DataFrame([{
    'PRODUCT_TYPE': 'SALPIL',
    'RISK_SCORE': 'LOW',
    'VINTAGE_DATE': '2024-01-01',
    'MOB': 12,
    'DPD0': 600,
    'DPD1+': 0,
    'DPD30+': 150,
    'DPD60+': 0,
    'DPD90+': 0,
    'DPD120+': 0,
    'DPD180+': 0,
    'WRITEOFF': 0,
    'PREPAY': 0,
    'SOLDOUT': 0,
    'IS_FORECAST': 1
}])
```

**Giải thích:**
- Cohort: SALPIL × LOW × 2024-01
- Forecast tại MOB 12
- Tổng EAD forecast = 600 + 150 = **750**
- Phân bổ state:
  - DPD0: 600 (80%)
  - DPD30+: 150 (20%)

#### Input 2: Loan-level data (df_raw)

```python
df_raw = pd.DataFrame([
    {'AGREEMENT_ID': 'LOAN_001', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW', 
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 1, 'PRINCIPLE_OUTSTANDING': 100, 
     'STATE_MODEL': 'DPD0', 'CUTOFF_DATE': '2024-01-31'},
    {'AGREEMENT_ID': 'LOAN_002', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW', 
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 1, 'PRINCIPLE_OUTSTANDING': 100, 
     'STATE_MODEL': 'DPD0', 'CUTOFF_DATE': '2024-01-31'},
    # ... 8 loans nữa
])
```

**Giải thích:**
- 10 loans trong cohort SALPIL × LOW × 2024-01
- Mỗi loan có EAD hiện tại = 100
- Tổng EAD current = 10 × 100 = **1,000**
- MOB hiện tại = 1 (mới giải ngân)

---

### Bước 2: Tính phân phối state (xác suất)

```python
# Tổng EAD forecast từ lifecycle
total_ead_forecast = row_lc[BUCKETS_CANON].sum()  # = 750

# Phân phối state (xác suất)
state_probs = {
    'DPD0': 600 / 750 = 0.80 (80%),
    'DPD30+': 150 / 750 = 0.20 (20%)
}
```

**Giải thích:**
- Xác suất loan rơi vào DPD0 = 80%
- Xác suất loan rơi vào DPD30+ = 20%
- Tổng xác suất = 100%

---

### Bước 3: Lấy loans trong cohort

```python
# Lọc loans thuộc cohort này
mask = (
    (df_loans_latest["PRODUCT_TYPE"] == 'SALPIL') &
    (df_loans_latest["RISK_SCORE"] == 'LOW') &
    (df_loans_latest["VINTAGE_DATE"] == '2024-01-01')
)

df_cohort_loans = df_loans_latest[mask].copy()
# → 10 loans
```

**Giải thích:**
- Lấy tất cả loans thuộc cohort SALPIL × LOW × 2024-01
- Kết quả: 10 loans

---

### Bước 4: Tính tổng EAD current của cohort

```python
total_ead_current = df_cohort_loans['PRINCIPLE_OUTSTANDING'].sum()
# = 100 + 100 + ... + 100 = 1,000
```

**Giải thích:**
- Tổng EAD hiện tại của 10 loans = 1,000

---

### Bước 5: Tính tỷ lệ EAD (EAD ratio)

```python
ead_ratio = total_ead_forecast / total_ead_current
# = 750 / 1,000 = 0.75
```

**Giải thích:**
- EAD forecast = 75% của EAD current
- Giảm 25% do prepayment/writeoff/amortization
- **Đây là tỷ lệ quan trọng nhất!**

---

### Bước 6: Assign state cho từng loan (Monte Carlo sampling)

```python
# Danh sách states và xác suất
states_list = ['DPD0', 'DPD30+']
probs_list = [0.80, 0.20]

# Random sampling với seed cố định (reproducible)
np.random.seed(42)
assigned_states = np.random.choice(
    states_list,
    size=10,  # 10 loans
    p=probs_list
)

# Kết quả (ví dụ):
# ['DPD0', 'DPD0', 'DPD30+', 'DPD0', 'DPD0', 
#  'DPD0', 'DPD0', 'DPD30+', 'DPD0', 'DPD0']
```

**Giải thích:**
- Dùng Monte Carlo sampling để assign state
- Xác suất: 80% DPD0, 20% DPD30+
- Kết quả: ~8 loans DPD0, ~2 loans DPD30+
- Seed cố định → kết quả reproducible

---

### Bước 7: Tính EAD_FORECAST cho từng loan

```python
# Công thức:
# EAD_FORECAST_loan = EAD_CURRENT_loan × ead_ratio

df_cohort_loans["EAD_FORECAST"] = df_cohort_loans['PRINCIPLE_OUTSTANDING'] * ead_ratio

# Kết quả:
# LOAN_001: EAD_FORECAST = 100 × 0.75 = 75
# LOAN_002: EAD_FORECAST = 100 × 0.75 = 75
# ...
# LOAN_010: EAD_FORECAST = 100 × 0.75 = 75
```

**Giải thích:**
- Mỗi loan giảm EAD theo cùng tỷ lệ (0.75)
- EAD_FORECAST = 75 < EAD_CURRENT = 100 ✅
- Tổng EAD_FORECAST = 10 × 75 = 750 ✅ (khớp với lifecycle)

---

### Bước 8: Kết quả cuối cùng

```python
df_result = pd.DataFrame([
    {'AGREEMENT_ID': 'LOAN_001', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'VINTAGE_DATE': '2024-01-01', 'MOB': 12, 'MOB_CURRENT': 1,
     'STATE_FORECAST': 'DPD0', 'EAD_CURRENT': 100, 'EAD_FORECAST': 75,
     'IS_FORECAST': 1, 'TARGET_MOB': 12},
    
    {'AGREEMENT_ID': 'LOAN_002', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'VINTAGE_DATE': '2024-01-01', 'MOB': 12, 'MOB_CURRENT': 1,
     'STATE_FORECAST': 'DPD0', 'EAD_CURRENT': 100, 'EAD_FORECAST': 75,
     'IS_FORECAST': 1, 'TARGET_MOB': 12},
    
    {'AGREEMENT_ID': 'LOAN_003', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'VINTAGE_DATE': '2024-01-01', 'MOB': 12, 'MOB_CURRENT': 1,
     'STATE_FORECAST': 'DPD30+', 'EAD_CURRENT': 100, 'EAD_FORECAST': 75,
     'IS_FORECAST': 1, 'TARGET_MOB': 12},
    
    # ... 7 loans nữa
])
```

---

## ✅ Validation (Kiểm tra kết quả)

### Check 1: Tổng EAD khớp với lifecycle

```python
# Tổng EAD từ lifecycle (cohort-level)
total_ead_lifecycle = df_lifecycle[BUCKETS_CANON].sum().sum()
# = 600 + 150 = 750

# Tổng EAD từ allocation (loan-level)
total_ead_allocated = df_result["EAD_FORECAST"].sum()
# = 75 × 10 = 750

# Chênh lệch
diff = abs(total_ead_lifecycle - total_ead_allocated)
# = 0

# ✅ PASS: Tổng EAD khớp
```

### Check 2: EAD_FORECAST < EAD_CURRENT

```python
# Kiểm tra từng loan
for _, row in df_result.iterrows():
    assert row['EAD_FORECAST'] <= row['EAD_CURRENT']

# ✅ PASS: Tất cả loans có EAD_FORECAST <= EAD_CURRENT
```

### Check 3: Phân bổ state đúng tỷ lệ

```python
# Đếm số loans theo state
state_counts = df_result['STATE_FORECAST'].value_counts()
# DPD0: 8 loans (80%)
# DPD30+: 2 loans (20%)

# ✅ PASS: Phân bổ state đúng tỷ lệ (±10% do sampling)
```

---

## 📐 Công thức tổng quát

### Công thức 1: EAD Ratio

```
ead_ratio = Total_EAD_Forecast_Cohort / Total_EAD_Current_Cohort
```

**Ví dụ:**
```
ead_ratio = 750 / 1,000 = 0.75
```

### Công thức 2: EAD_FORECAST per loan

```
EAD_FORECAST_loan = EAD_CURRENT_loan × ead_ratio
```

**Ví dụ:**
```
EAD_FORECAST_loan = 100 × 0.75 = 75
```

### Công thức 3: State probability

```
P(state) = EAD_state / Total_EAD_Forecast
```

**Ví dụ:**
```
P(DPD0) = 600 / 750 = 0.80
P(DPD30+) = 150 / 750 = 0.20
```

---

## 🔍 Ví dụ minh họa đầy đủ

### Scenario: 3 cohorts, 30 loans

#### Cohort 1: SALPIL × LOW × 2024-01

**Lifecycle forecast @ MOB 12:**
```
DPD0: 600, DPD30+: 150
Total: 750
```

**Loans (10 loans):**
```
LOAN_001 ~ LOAN_010: EAD_CURRENT = 100 each
Total EAD_CURRENT: 1,000
```

**Calculation:**
```
ead_ratio = 750 / 1,000 = 0.75
EAD_FORECAST per loan = 100 × 0.75 = 75

State assignment (80% DPD0, 20% DPD30+):
- LOAN_001: DPD0, EAD_FORECAST = 75
- LOAN_002: DPD0, EAD_FORECAST = 75
- LOAN_003: DPD30+, EAD_FORECAST = 75
- ...
```

#### Cohort 2: SALPIL × HIGH × 2024-01

**Lifecycle forecast @ MOB 12:**
```
DPD0: 400, DPD30+: 200, DPD90+: 100
Total: 700
```

**Loans (10 loans):**
```
LOAN_011 ~ LOAN_020: EAD_CURRENT = 100 each
Total EAD_CURRENT: 1,000
```

**Calculation:**
```
ead_ratio = 700 / 1,000 = 0.70
EAD_FORECAST per loan = 100 × 0.70 = 70

State assignment (57% DPD0, 29% DPD30+, 14% DPD90+):
- LOAN_011: DPD0, EAD_FORECAST = 70
- LOAN_012: DPD0, EAD_FORECAST = 70
- LOAN_013: DPD30+, EAD_FORECAST = 70
- LOAN_014: DPD90+, EAD_FORECAST = 70
- ...
```

#### Cohort 3: CARD × LOW × 2024-02

**Lifecycle forecast @ MOB 12:**
```
DPD0: 800, DPD30+: 100
Total: 900
```

**Loans (10 loans):**
```
LOAN_021 ~ LOAN_030: EAD_CURRENT = 100 each
Total EAD_CURRENT: 1,000
```

**Calculation:**
```
ead_ratio = 900 / 1,000 = 0.90
EAD_FORECAST per loan = 100 × 0.90 = 90

State assignment (89% DPD0, 11% DPD30+):
- LOAN_021: DPD0, EAD_FORECAST = 90
- LOAN_022: DPD0, EAD_FORECAST = 90
- LOAN_023: DPD30+, EAD_FORECAST = 90
- ...
```

### Tổng kết 3 cohorts

```
Total EAD_CURRENT: 3,000
Total EAD_FORECAST: 750 + 700 + 900 = 2,350
Overall reduction: (3,000 - 2,350) / 3,000 = 21.67%
```

---

## 🎯 Các trường hợp đặc biệt

### Trường hợp 1: EAD_FORECAST = EAD_CURRENT

**Khi nào xảy ra?**
- Không có prepayment
- Không có writeoff
- Không có amortization
- Lifecycle forecast = EAD current

**Ví dụ:**
```
Lifecycle: DPD0: 1,000, Total: 1,000
Loans: 10 loans × 100 = 1,000
ead_ratio = 1,000 / 1,000 = 1.0
EAD_FORECAST = 100 × 1.0 = 100 (= EAD_CURRENT)
```

**Hợp lệ?** ✅ Có, trong trường hợp đặc biệt này

### Trường hợp 2: EAD_FORECAST rất nhỏ

**Khi nào xảy ra?**
- Nhiều prepayment
- Nhiều writeoff
- Cohort gần hết vòng đời

**Ví dụ:**
```
Lifecycle: DPD0: 100, PREPAY: 0, WRITEOFF: 0, Total: 100
Loans: 10 loans × 100 = 1,000
ead_ratio = 100 / 1,000 = 0.10
EAD_FORECAST = 100 × 0.10 = 10 (giảm 90%)
```

**Hợp lệ?** ✅ Có, nếu cohort gần hết vòng đời

### Trường hợp 3: Không có loans trong cohort

**Khi nào xảy ra?**
- Cohort mới (chưa giải ngân)
- Cohort đã hết (tất cả đã prepay/writeoff)

**Xử lý:**
```python
if df_cohort_loans.empty:
    continue  # Bỏ qua cohort này
```

### Trường hợp 4: Loans có EAD khác nhau

**Ví dụ:**
```
LOAN_001: EAD_CURRENT = 50
LOAN_002: EAD_CURRENT = 150
LOAN_003: EAD_CURRENT = 200
Total: 400

Lifecycle: Total = 300
ead_ratio = 300 / 400 = 0.75

EAD_FORECAST:
LOAN_001: 50 × 0.75 = 37.5
LOAN_002: 150 × 0.75 = 112.5
LOAN_003: 200 × 0.75 = 150.0
Total: 300 ✅
```

**Giải thích:** Mỗi loan giảm theo cùng tỷ lệ, nhưng EAD_FORECAST khác nhau do EAD_CURRENT khác nhau.

---

## 🔄 So sánh 2 phương pháp allocation

### Method 1: Simple (Monte Carlo)

**File:** `allocate_forecast_to_loans_simple()`

**Logic:**
- Mỗi loan → 1 state duy nhất
- Assign state bằng Monte Carlo sampling
- EAD_FORECAST = EAD_CURRENT × ead_ratio

**Ưu điểm:**
- Đơn giản, dễ hiểu
- Nhanh (1 dòng per loan)
- Phù hợp cho reporting

**Nhược điểm:**
- Không phản ánh uncertainty
- Mỗi loan chỉ có 1 scenario

**Output:**
```
LOAN_001 | DPD0   | EAD_FORECAST = 75
LOAN_002 | DPD0   | EAD_FORECAST = 75
LOAN_003 | DPD30+ | EAD_FORECAST = 75
```

### Method 2: Proportional (Multiple states)

**File:** `allocate_forecast_to_loans()`

**Logic:**
- Mỗi loan → nhiều states (theo tỷ lệ)
- Phân bổ EAD theo weight
- EAD_FORECAST = sum(EAD_state × weight)

**Ưu điểm:**
- Phản ánh uncertainty
- Nhiều scenarios per loan
- Phù hợp cho risk analysis

**Nhược điểm:**
- Phức tạp hơn
- Chậm hơn (nhiều dòng per loan)

**Output:**
```
LOAN_001 | DPD0   | EAD_FORECAST = 60 (80% × 75)
LOAN_001 | DPD30+ | EAD_FORECAST = 15 (20% × 75)
LOAN_002 | DPD0   | EAD_FORECAST = 60
LOAN_002 | DPD30+ | EAD_FORECAST = 15
```

---

## 📊 Validation checklist

Sau khi chạy allocation, kiểm tra:

### ✅ Check 1: Tổng EAD khớp
```python
assert abs(total_ead_lifecycle - total_ead_allocated) / total_ead_lifecycle < 0.0001
```

### ✅ Check 2: EAD_FORECAST <= EAD_CURRENT
```python
assert (df_result['EAD_FORECAST'] <= df_result['EAD_CURRENT']).all()
```

### ✅ Check 3: Không có missing values
```python
assert df_result['EAD_FORECAST'].notna().all()
assert df_result['STATE_FORECAST'].notna().all()
```

### ✅ Check 4: State distribution hợp lý
```python
state_dist = df_result['STATE_FORECAST'].value_counts(normalize=True)
# So sánh với lifecycle distribution
```

### ✅ Check 5: Số lượng loans đúng
```python
assert len(df_result) == len(df_cohort_loans)
```

---

## 🐛 Troubleshooting

### Vấn đề 1: EAD_FORECAST = EAD_CURRENT

**Nguyên nhân:** Code cũ (đã fix)
```python
# SAI ❌
df_cohort_loans["EAD_FORECAST"] = df_cohort_loans[ead_col]
```

**Giải pháp:** Dùng code mới
```python
# ĐÚNG ✅
ead_ratio = total_ead_forecast / total_ead_current
df_cohort_loans["EAD_FORECAST"] = df_cohort_loans[ead_col] * ead_ratio
```

### Vấn đề 2: Tổng EAD không khớp

**Nguyên nhân:**
- Missing loans trong cohort
- Sai vintage date
- Sai product/risk mapping

**Giải pháp:**
```python
# Kiểm tra số loans trong cohort
print(f"Loans in cohort: {len(df_cohort_loans)}")
print(f"Expected loans: {expected_count}")

# Kiểm tra vintage date
print(df_cohort_loans['VINTAGE_DATE'].unique())
```

### Vấn đề 3: State distribution sai

**Nguyên nhân:**
- Random seed khác nhau
- Lifecycle data sai

**Giải pháp:**
```python
# Fix random seed
np.random.seed(42)

# Kiểm tra lifecycle distribution
print(df_lifecycle[BUCKETS_CANON] / df_lifecycle[BUCKETS_CANON].sum(axis=1))
```

---

## 📚 Tài liệu liên quan

- **FIX_EAD_FORECAST_LOGIC.md** - Chi tiết về fix EAD_FORECAST
- **test_ead_forecast_fix.py** - Test script
- **QUICK_GUIDE_MULTI_MOB.md** - Hướng dẫn nhanh multi-MOB
- **GUIDE_LAY_CHI_TIET_HOP_DONG.md** - Hướng dẫn lấy chi tiết hợp đồng

---

## 🎓 Tóm tắt

### Logic cốt lõi (3 bước)

1. **Tính ead_ratio:**
   ```
   ead_ratio = Total_EAD_Forecast / Total_EAD_Current
   ```

2. **Assign state (Monte Carlo):**
   ```
   state_probs = {state: EAD_state / Total_EAD_Forecast}
   assigned_states = np.random.choice(states, p=probs)
   ```

3. **Tính EAD_FORECAST:**
   ```
   EAD_FORECAST = EAD_CURRENT × ead_ratio
   ```

### Điểm quan trọng

✅ **EAD_FORECAST < EAD_CURRENT** (thường xuyên)  
✅ **Tổng EAD khớp** với lifecycle  
✅ **State distribution** theo xác suất từ lifecycle  
✅ **Reproducible** (seed cố định)  

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15  
**Version:** 2.0 (sau fix EAD_FORECAST)
