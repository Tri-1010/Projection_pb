# 📘 Làm rõ: EAD_CURRENT và MOB_CURRENT

## ❓ Câu hỏi

**"EAD hiện tại được tính từ MOB gần nhất đúng không?"**

## ✅ Trả lời

**Đúng, nhưng cần làm rõ 2 khái niệm:**

1. **CUTOFF_DATE** (Ngày snapshot) - Thời điểm chụp dữ liệu
2. **MOB_CURRENT** (MOB hiện tại) - Tuổi của loan tại thời điểm snapshot

---

## 🔍 Chi tiết

### 1. EAD_CURRENT được lấy từ đâu?

**Code:**
```python
# Lấy snapshot mới nhất
latest_cutoff = df_loans[cutoff_col].max()
df_loans_latest = df_loans[df_loans[cutoff_col] == latest_cutoff].copy()

# EAD_CURRENT = PRINCIPLE_OUTSTANDING tại snapshot mới nhất
loan_info = df_loans_latest[[
    'AGREEMENT_ID', 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE', 
    'MOB', 'PRINCIPLE_OUTSTANDING'
]].copy()

loan_info = loan_info.rename(columns={
    'MOB': 'MOB_CURRENT',
    'PRINCIPLE_OUTSTANDING': 'EAD_CURRENT'
})
```

**Giải thích:**
- `latest_cutoff` = CUTOFF_DATE mới nhất (ví dụ: 2024-12-31)
- `EAD_CURRENT` = PRINCIPLE_OUTSTANDING tại ngày 2024-12-31
- `MOB_CURRENT` = MOB của loan tại ngày 2024-12-31

---

### 2. Ví dụ cụ thể

#### Scenario: Loan LOAN_001

**Data trong df_raw:**

| AGREEMENT_ID | CUTOFF_DATE | MOB | PRINCIPLE_OUTSTANDING | STATE_MODEL |
|--------------|-------------|-----|----------------------|-------------|
| LOAN_001     | 2024-10-31  | 1   | 100                  | DPD0        |
| LOAN_001     | 2024-11-30  | 2   | 98                   | DPD0        |
| LOAN_001     | 2024-12-31  | 3   | 95                   | DPD0        |

**Khi chạy allocation:**

```python
latest_cutoff = df_raw['CUTOFF_DATE'].max()
# = 2024-12-31

df_loans_latest = df_raw[df_raw['CUTOFF_DATE'] == '2024-12-31']
# → Chỉ lấy dòng cuối cùng

# Kết quả:
# AGREEMENT_ID: LOAN_001
# MOB_CURRENT: 3
# EAD_CURRENT: 95
# STATE_CURRENT: DPD0
```

**Giải thích:**
- EAD_CURRENT = 95 (không phải 100 hay 98)
- MOB_CURRENT = 3 (không phải 1 hay 2)
- Lấy từ snapshot **mới nhất** (2024-12-31)

---

### 3. Tại sao lấy snapshot mới nhất?

#### Lý do 1: Dữ liệu mới nhất phản ánh tình trạng hiện tại

```
Loan LOAN_001:
- Tháng 10: EAD = 100, MOB = 1
- Tháng 11: EAD = 98, MOB = 2
- Tháng 12: EAD = 95, MOB = 3 ← Tình trạng hiện tại

→ Dùng EAD = 95 để forecast
```

#### Lý do 2: Tránh duplicate loans

Nếu không filter theo latest_cutoff:
```
LOAN_001 xuất hiện 3 lần (3 tháng)
→ Tổng EAD = 100 + 98 + 95 = 293 ❌ SAI!

Đúng phải là: EAD = 95 ✅
```

#### Lý do 3: Consistency với lifecycle

Lifecycle forecast bắt đầu từ MOB hiện tại:
```
MOB_CURRENT = 3
Forecast: MOB 4, 5, 6, ..., 12, 24, 36
```

---

## 📊 Workflow đầy đủ

### Bước 1: Lấy snapshot mới nhất

```python
# Input: df_raw với nhiều snapshots
df_raw = pd.DataFrame([
    {'AGREEMENT_ID': 'LOAN_001', 'CUTOFF_DATE': '2024-10-31', 'MOB': 1, 'PRINCIPLE_OUTSTANDING': 100},
    {'AGREEMENT_ID': 'LOAN_001', 'CUTOFF_DATE': '2024-11-30', 'MOB': 2, 'PRINCIPLE_OUTSTANDING': 98},
    {'AGREEMENT_ID': 'LOAN_001', 'CUTOFF_DATE': '2024-12-31', 'MOB': 3, 'PRINCIPLE_OUTSTANDING': 95},
    {'AGREEMENT_ID': 'LOAN_002', 'CUTOFF_DATE': '2024-10-31', 'MOB': 1, 'PRINCIPLE_OUTSTANDING': 200},
    {'AGREEMENT_ID': 'LOAN_002', 'CUTOFF_DATE': '2024-11-30', 'MOB': 2, 'PRINCIPLE_OUTSTANDING': 195},
    {'AGREEMENT_ID': 'LOAN_002', 'CUTOFF_DATE': '2024-12-31', 'MOB': 3, 'PRINCIPLE_OUTSTANDING': 190},
])

# Lấy snapshot mới nhất
latest_cutoff = df_raw['CUTOFF_DATE'].max()  # = '2024-12-31'
df_loans_latest = df_raw[df_raw['CUTOFF_DATE'] == latest_cutoff]

# Kết quả:
# LOAN_001: MOB = 3, EAD = 95
# LOAN_002: MOB = 3, EAD = 190
```

### Bước 2: Tính EAD_FORECAST

```python
# Lifecycle forecast @ MOB 12
# Cohort: SALPIL × LOW × 2024-10
# Total_EAD_Forecast = 750

# Loans trong cohort (tại snapshot mới nhất):
# LOAN_001: EAD_CURRENT = 95, MOB_CURRENT = 3
# LOAN_002: EAD_CURRENT = 190, MOB_CURRENT = 3
# Total_EAD_CURRENT = 285

# Tính ead_ratio
ead_ratio = 750 / 285 = 2.63

# Tính EAD_FORECAST
LOAN_001: EAD_FORECAST = 95 × 2.63 = 250
LOAN_002: EAD_FORECAST = 190 × 2.63 = 500
Total: 750 ✅
```

**Lưu ý:** Trong ví dụ này, EAD_FORECAST > EAD_CURRENT vì cohort đang tăng trưởng (ví dụ: credit card limit tăng). Thông thường EAD_FORECAST < EAD_CURRENT do prepayment/writeoff.

---

## 🎯 Các trường hợp đặc biệt

### Trường hợp 1: Loans có MOB khác nhau tại cùng snapshot

```
Snapshot: 2024-12-31

LOAN_001: MOB = 3, EAD = 95  (giải ngân tháng 10)
LOAN_002: MOB = 2, EAD = 190 (giải ngân tháng 11)
LOAN_003: MOB = 1, EAD = 300 (giải ngân tháng 12)
```

**Xử lý:**
- Tất cả đều thuộc cùng snapshot (2024-12-31)
- Nhưng thuộc **khác vintage** (tháng giải ngân khác nhau)
- Allocation sẽ group theo vintage riêng biệt

### Trường hợp 2: Loan mới giải ngân (MOB = 0 hoặc 1)

```
LOAN_004: MOB_CURRENT = 1, EAD_CURRENT = 500
Forecast @ MOB 12: EAD_FORECAST = 375
```

**Hợp lệ:** Loan mới vẫn được forecast đến MOB 12, 24, ...

### Trường hợp 3: Loan gần hết vòng đời (MOB = 35)

```
LOAN_005: MOB_CURRENT = 35, EAD_CURRENT = 50
Forecast @ MOB 36: EAD_FORECAST = 10
```

**Hợp lệ:** Loan gần hết vòng đời, EAD giảm mạnh

---

## 📐 Công thức tổng quát

### Công thức 1: Lấy snapshot mới nhất

```
latest_cutoff = max(CUTOFF_DATE)
df_loans_latest = df_raw[CUTOFF_DATE == latest_cutoff]
```

### Công thức 2: EAD_CURRENT

```
EAD_CURRENT = PRINCIPLE_OUTSTANDING tại latest_cutoff
```

### Công thức 3: MOB_CURRENT

```
MOB_CURRENT = MOB tại latest_cutoff
```

### Công thức 4: EAD_FORECAST

```
ead_ratio = Total_EAD_Forecast_Cohort / Total_EAD_CURRENT_Cohort
EAD_FORECAST = EAD_CURRENT × ead_ratio
```

---

## ✅ Validation

### Check 1: Không có duplicate loans

```python
# Kiểm tra
assert df_loans_latest['AGREEMENT_ID'].duplicated().sum() == 0

# Nếu có duplicate → Có vấn đề với data
```

### Check 2: Tất cả loans có cùng CUTOFF_DATE

```python
# Kiểm tra
assert df_loans_latest['CUTOFF_DATE'].nunique() == 1

# Nếu > 1 → Logic lấy snapshot sai
```

### Check 3: MOB_CURRENT hợp lý

```python
# Kiểm tra
assert (df_loans_latest['MOB'] >= 0).all()
assert (df_loans_latest['MOB'] <= 60).all()  # Tùy business

# Nếu MOB âm hoặc quá lớn → Data issue
```

---

## 🐛 Troubleshooting

### Vấn đề 1: "Tổng EAD không khớp"

**Nguyên nhân:** Có thể do không lấy đúng snapshot mới nhất

**Giải pháp:**
```python
# Kiểm tra
print(f"Latest cutoff: {df_raw['CUTOFF_DATE'].max()}")
print(f"Number of loans at latest cutoff: {len(df_loans_latest)}")

# So sánh với expected
print(f"Total loans in df_raw: {df_raw['AGREEMENT_ID'].nunique()}")
```

### Vấn đề 2: "Có loans bị thiếu"

**Nguyên nhân:** Một số loans không có data tại snapshot mới nhất

**Giải pháp:**
```python
# Tìm loans bị thiếu
all_loans = df_raw['AGREEMENT_ID'].unique()
loans_at_latest = df_loans_latest['AGREEMENT_ID'].unique()
missing_loans = set(all_loans) - set(loans_at_latest)

print(f"Missing loans: {missing_loans}")

# Kiểm tra tại sao thiếu
for loan in missing_loans:
    loan_data = df_raw[df_raw['AGREEMENT_ID'] == loan]
    print(f"{loan}: Last cutoff = {loan_data['CUTOFF_DATE'].max()}")
```

### Vấn đề 3: "MOB_CURRENT không đúng"

**Nguyên nhân:** Tính MOB sai trong data pipeline

**Giải pháp:**
```python
# Kiểm tra MOB
df_check = df_loans_latest.copy()
df_check['DISBURSAL_DATE'] = pd.to_datetime(df_check['DISBURSAL_DATE'])
df_check['CUTOFF_DATE'] = pd.to_datetime(df_check['CUTOFF_DATE'])

# Tính MOB lại
df_check['MOB_CALCULATED'] = (
    (df_check['CUTOFF_DATE'].dt.year - df_check['DISBURSAL_DATE'].dt.year) * 12 +
    (df_check['CUTOFF_DATE'].dt.month - df_check['DISBURSAL_DATE'].dt.month)
)

# So sánh
df_check['MOB_DIFF'] = df_check['MOB'] - df_check['MOB_CALCULATED']
print(df_check[df_check['MOB_DIFF'] != 0])
```

---

## 📚 Tóm tắt

### Câu trả lời ngắn gọn:

**Có, EAD_CURRENT được lấy từ snapshot mới nhất (CUTOFF_DATE gần nhất).**

### Chi tiết:

1. **Snapshot mới nhất:**
   ```
   latest_cutoff = max(CUTOFF_DATE)
   ```

2. **EAD_CURRENT:**
   ```
   EAD_CURRENT = PRINCIPLE_OUTSTANDING tại latest_cutoff
   ```

3. **MOB_CURRENT:**
   ```
   MOB_CURRENT = MOB tại latest_cutoff
   ```

4. **Tại sao?**
   - Phản ánh tình trạng hiện tại
   - Tránh duplicate loans
   - Consistency với lifecycle forecast

### Ví dụ:

```
Loan LOAN_001:
- Tháng 10: EAD = 100, MOB = 1
- Tháng 11: EAD = 98, MOB = 2
- Tháng 12: EAD = 95, MOB = 3 ← Lấy từ đây

→ EAD_CURRENT = 95
→ MOB_CURRENT = 3
```

---

## 📖 Tài liệu liên quan

- **ALLOCATION_LOGIC_DETAILED.md** - Logic allocation chi tiết
- **FIX_EAD_FORECAST_LOGIC.md** - Fix EAD_FORECAST
- **src/rollrate/allocation.py** - Implementation (line 117-118)
- **src/rollrate/allocation_multi_mob.py** - Implementation (line 95-96)

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15  
**Version:** 1.0
