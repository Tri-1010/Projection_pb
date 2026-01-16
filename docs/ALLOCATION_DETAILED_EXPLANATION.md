# 📘 Giải Thích Chi Tiết: Phân Bổ Forecast Xuống Loan-Level

## 🎯 Tổng Quan

**Mục tiêu:** Từ forecast ở cohort-level (PRODUCT_TYPE × RISK_SCORE × VINTAGE_DATE × MOB), phân bổ ngược xuống từng hợp đồng cụ thể.

**Input:**
- `df_lifecycle_final`: Forecast ở cohort-level (tổng hợp)
- `df_loans_latest`: Danh sách hợp đồng hiện tại (loan-level)
- `matrices_by_mob`: Ma trận chuyển trạng thái
- `target_mob`: MOB cần forecast (ví dụ: 12, 24)

**Output:**
- DataFrame với mỗi hợp đồng có:
  - `STATE_FORECAST_MOB{X}`: Trạng thái dự báo
  - `EAD_FORECAST_MOB{X}`: Dư nợ dự báo
  - `PROB_DEL30_MOB{X}`: Xác suất DEL30+
  - `EAD_DEL30_MOB{X}`: Dư nợ dự kiến thuộc DEL30+
  - `DEL30_FLAG_MOB{X}`: Flag 0/1

---

## 📊 Ví Dụ Minh Họa

### Input Data

**1. df_lifecycle_final (Cohort-level forecast @ MOB 12):**

| PRODUCT_TYPE | RISK_SCORE | VINTAGE_DATE | MOB | DPD0 | DPD30+ | DPD90+ | DEL30_PCT | DEL90_PCT |
|--------------|------------|--------------|-----|------|--------|--------|-----------|-----------|
| PL | A | 2024-01 | 12 | 800M | 150M | 50M | 15% | 5% |
| PL | B | 2024-01 | 12 | 600M | 300M | 100M | 30% | 10% |
| CC | A | 2024-01 | 12 | 900M | 80M | 20M | 8% | 2% |

**Giải thích:**
- Cohort (PL, A, 2024-01) tại MOB 12:
  - Tổng dư nợ: 800M (DPD0) + 150M (DPD30+) + 50M (DPD90+) = 1,000M
  - DEL30_PCT = 15% (tỉ lệ dư nợ thuộc nhóm DPD30+)
  - DEL90_PCT = 5% (tỉ lệ dư nợ thuộc nhóm DPD90+)

**2. df_loans_latest (Loan-level hiện tại @ MOB 3):**

| AGREEMENT_ID | PRODUCT_TYPE | RISK_SCORE | VINTAGE_DATE | MOB_CURRENT | STATE_CURRENT | EAD_CURRENT | DISBURSAL_AMOUNT |
|--------------|--------------|------------|--------------|-------------|---------------|-------------|------------------|
| L001 | PL | A | 2024-01 | 3 | DPD0 | 100M | 100M |
| L002 | PL | A | 2024-01 | 3 | DPD0 | 200M | 200M |
| L003 | PL | A | 2024-01 | 3 | DPD30+ | 50M | 50M |
| L004 | PL | B | 2024-01 | 3 | DPD0 | 150M | 150M |
| L005 | CC | A | 2024-01 | 3 | DPD0 | 300M | 300M |

**Giải thích:**
- 3 loans (L001, L002, L003) thuộc cohort (PL, A, 2024-01)
- Hiện tại đang ở MOB 3
- Cần forecast đến MOB 12 (9 tháng nữa)

---

## 🔄 Quy Trình Phân Bổ (4 Bước)

### **BƯỚC 1: Tính Combined Transition Matrix**

**Mục đích:** Tính xác suất chuyển trạng thái từ MOB_CURRENT → TARGET_MOB

**Logic:**
```
Combined_Matrix = P(MOB=3→4) × P(MOB=4→5) × ... × P(MOB=11→12)
```

**Ví dụ với loan L001:**
- Cohort: (PL, A, 2024-01)
- MOB_CURRENT: 3
- TARGET_MOB: 12
- STATE_CURRENT: DPD0

**Lấy ma trận:**
```python
# Lấy từ matrices_by_mob
P_3to4 = matrices_by_mob["PL"][3]["A"]["P"]  # Ma trận MOB 3→4
P_4to5 = matrices_by_mob["PL"][4]["A"]["P"]  # Ma trận MOB 4→5
...
P_11to12 = matrices_by_mob["PL"][11]["A"]["P"]  # Ma trận MOB 11→12

# Nhân chuỗi ma trận
Combined = P_3to4 @ P_4to5 @ ... @ P_11to12
```

**Kết quả Combined Matrix (ví dụ):**

|  | DPD0 | DPD30+ | DPD90+ | PREPAY | WRITEOFF |
|--|------|--------|--------|--------|----------|
| **DPD0** | 0.70 | 0.15 | 0.05 | 0.08 | 0.02 |
| **DPD30+** | 0.10 | 0.50 | 0.30 | 0.05 | 0.05 |
| **DPD90+** | 0.00 | 0.00 | 0.60 | 0.00 | 0.40 |

**Giải thích:**
- Loan L001 hiện tại ở DPD0
- Xác suất tại MOB 12:
  - DPD0: 70%
  - DPD30+: 15%
  - DPD90+: 5%
  - PREPAY: 8%
  - WRITEOFF: 2%

**Code:**
```python
# Vector ban đầu (loan L001 ở DPD0)
init_vec = [1.0, 0, 0, 0, 0]  # [DPD0, DPD30+, DPD90+, PREPAY, WRITEOFF]

# Nhân với combined matrix
final_probs = init_vec @ Combined
# => [0.70, 0.15, 0.05, 0.08, 0.02]
```

---

### **BƯỚC 2: Lấy DEL Rates từ Lifecycle**

**Mục đích:** Lấy tỉ lệ DEL30%, DEL90% từ lifecycle forecast (cohort-level)

**Logic:**
```
PROB_DEL30 = DEL30_PCT từ lifecycle (KHÔNG tính từ transition matrix)
PROB_DEL90 = DEL90_PCT từ lifecycle
```

**Tại sao KHÔNG dùng transition matrix?**
- Transition matrix cho xác suất riêng từng loan (phụ thuộc STATE_CURRENT)
- Lifecycle đã tính sẵn tỉ lệ DEL cho TOÀN COHORT
- Nếu dùng transition matrix → tổng sẽ không khớp với lifecycle

**Ví dụ:**

**Lifecycle forecast @ MOB 12:**
| PRODUCT_TYPE | RISK_SCORE | VINTAGE_DATE | DEL30_PCT | DEL90_PCT |
|--------------|------------|--------------|-----------|-----------|
| PL | A | 2024-01 | 15% | 5% |

**Merge vào loans:**
| AGREEMENT_ID | PRODUCT_TYPE | RISK_SCORE | VINTAGE_DATE | DISBURSAL_AMOUNT | PROB_DEL30 | PROB_DEL90 |
|--------------|--------------|------------|--------------|------------------|------------|------------|
| L001 | PL | A | 2024-01 | 100M | **15%** | **5%** |
| L002 | PL | A | 2024-01 | 200M | **15%** | **5%** |
| L003 | PL | A | 2024-01 | 50M | **15%** | **5%** |

**Giải thích:**
- Tất cả loans trong cùng cohort (PL, A, 2024-01) có cùng PROB_DEL30 = 15%
- PROB_DEL30 = DEL30_PCT từ lifecycle (không phụ thuộc STATE_CURRENT)

**Tính EAD_DEL:**
```
EAD_DEL30 = DISBURSAL_AMOUNT × PROB_DEL30
EAD_DEL90 = DISBURSAL_AMOUNT × PROB_DEL90
```

| AGREEMENT_ID | DISBURSAL_AMOUNT | PROB_DEL30 | EAD_DEL30 | PROB_DEL90 | EAD_DEL90 |
|--------------|------------------|------------|-----------|------------|-----------|
| L001 | 100M | 15% | **15M** | 5% | **5M** |
| L002 | 200M | 15% | **30M** | 5% | **10M** |
| L003 | 50M | 15% | **7.5M** | 5% | **2.5M** |
| **Tổng** | **350M** | - | **52.5M** | - | **17.5M** |

**Validation:**
```
DEL30_rate = Total_EAD_DEL30 / Total_DISBURSAL
           = 52.5M / 350M
           = 15% ✅ (khớp với lifecycle)
```

**Code:**
```python
# Merge DEL rates từ lifecycle
df_del_rates = df_lifecycle_final[
    df_lifecycle_final['MOB'] == target_mob
][['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE', 'DEL30_PCT', 'DEL90_PCT']]

df = df.merge(
    df_del_rates,
    on=['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE'],
    how='left'
)

# PROB_DEL30 = DEL30_PCT từ lifecycle
df['PROB_DEL30'] = df['DEL30_PCT']
df['PROB_DEL90'] = df['DEL90_PCT']

# EAD_DEL = DISBURSAL_AMOUNT × PROB_DEL
df['EAD_DEL30'] = df['DISBURSAL_AMOUNT'] * df['PROB_DEL30']
df['EAD_DEL90'] = df['DISBURSAL_AMOUNT'] * df['PROB_DEL90']
```

---

### **BƯỚC 3: Sample STATE_FORECAST**

**Mục đích:** Assign trạng thái dự báo cho từng loan dựa trên xác suất từ BƯỚC 1

**Logic:**
```
STATE_FORECAST = random.choice(states, p=final_probs)
```

**Ví dụ với loan L001:**
- Xác suất từ BƯỚC 1: [DPD0: 70%, DPD30+: 15%, DPD90+: 5%, PREPAY: 8%, WRITEOFF: 2%]
- Random sampling → giả sử kết quả: **DPD0**

**Ví dụ với loan L002:**
- Xác suất giống L001 (cùng cohort, cùng STATE_CURRENT)
- Random sampling → giả sử kết quả: **DPD30+**

**Kết quả sau sampling:**

| AGREEMENT_ID | STATE_CURRENT | STATE_FORECAST | DEL30_FLAG | DEL90_FLAG |
|--------------|---------------|----------------|------------|------------|
| L001 | DPD0 | **DPD0** | 0 | 0 |
| L002 | DPD0 | **DPD30+** | 1 | 0 |
| L003 | DPD30+ | **DPD90+** | 1 | 1 |

**Giải thích:**
- DEL30_FLAG = 1 nếu STATE_FORECAST ∈ {DPD30+, DPD60+, DPD90+, ...}
- DEL90_FLAG = 1 nếu STATE_FORECAST ∈ {DPD90+, DPD120+, ...}

**Code:**
```python
def sample_state(probs):
    if probs.sum() == 0:
        return 'DPD0'
    probs = probs / probs.sum()
    return np.random.choice(BUCKETS_CANON, p=probs)

df['STATE_FORECAST'] = [sample_state(p) for p in probs_arr]

# DEL flags
df['DEL30_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_30P).astype(int)
df['DEL90_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_90P).astype(int)
```

---

### **BƯỚC 4: Phân Bổ EAD_FORECAST**

**Mục đích:** Tính dư nợ dự báo cho từng loan sao cho tổng khớp với lifecycle

**Logic:**
```
Với mỗi cohort (PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE):
    Với mỗi state (DPD0, DPD30+, ...):
        EAD_lifecycle_state = lifecycle[state]  # Tổng dư nợ của state từ lifecycle
        EAD_current_state = sum(EAD_CURRENT của loans có STATE_FORECAST = state)
        
        ratio = EAD_lifecycle_state / EAD_current_state
        
        Với mỗi loan có STATE_FORECAST = state:
            EAD_FORECAST = EAD_CURRENT × ratio
```

**Ví dụ với cohort (PL, A, 2024-01):**

**Lifecycle @ MOB 12:**
| State | EAD từ lifecycle |
|-------|------------------|
| DPD0 | 800M |
| DPD30+ | 150M |
| DPD90+ | 50M |

**Loans sau sampling (BƯỚC 3):**
| AGREEMENT_ID | STATE_FORECAST | EAD_CURRENT |
|--------------|----------------|-------------|
| L001 | DPD0 | 100M |
| L002 | DPD30+ | 200M |
| L003 | DPD90+ | 50M |

**Tính ratio cho từng state:**

**State DPD0:**
```
EAD_lifecycle_DPD0 = 800M
EAD_current_DPD0 = 100M (chỉ có L001)
ratio_DPD0 = 800M / 100M = 8.0

=> EAD_FORECAST(L001) = 100M × 8.0 = 800M
```

**State DPD30+:**
```
EAD_lifecycle_DPD30+ = 150M
EAD_current_DPD30+ = 200M (chỉ có L002)
ratio_DPD30+ = 150M / 200M = 0.75

=> EAD_FORECAST(L002) = 200M × 0.75 = 150M
```

**State DPD90+:**
```
EAD_lifecycle_DPD90+ = 50M
EAD_current_DPD90+ = 50M (chỉ có L003)
ratio_DPD90+ = 50M / 50M = 1.0

=> EAD_FORECAST(L003) = 50M × 1.0 = 50M
```

**Kết quả cuối cùng:**

| AGREEMENT_ID | STATE_CURRENT | EAD_CURRENT | STATE_FORECAST | EAD_FORECAST | PROB_DEL30 | EAD_DEL30 | DEL30_FLAG |
|--------------|---------------|-------------|----------------|--------------|------------|-----------|------------|
| L001 | DPD0 | 100M | DPD0 | **800M** | 15% | 15M | 0 |
| L002 | DPD0 | 200M | DPD30+ | **150M** | 15% | 30M | 1 |
| L003 | DPD30+ | 50M | DPD90+ | **50M** | 15% | 7.5M | 1 |
| **Tổng** | - | **350M** | - | **1,000M** | - | **52.5M** | - |

**Validation:**
```
✅ Tổng EAD_FORECAST = 1,000M (khớp với lifecycle: 800M + 150M + 50M)
✅ Tổng EAD_DEL30 / DISBURSAL = 52.5M / 350M = 15% (khớp với DEL30_PCT)
```

**Code:**
```python
for (product, score, vintage), grp in df.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']):
    # Lấy lifecycle row
    lc_row = df_lifecycle_final[
        (df_lifecycle_final['PRODUCT_TYPE'] == product) &
        (df_lifecycle_final['RISK_SCORE'] == score) &
        (df_lifecycle_final['VINTAGE_DATE'] == vintage) &
        (df_lifecycle_final['MOB'] == target_mob)
    ].iloc[0]
    
    # Với mỗi state
    for state in BUCKETS_CANON:
        ead_lifecycle_state = lc_row[state]  # Tổng EAD từ lifecycle
        
        # Loans có STATE_FORECAST = state
        state_mask = (
            (df['PRODUCT_TYPE'] == product) &
            (df['RISK_SCORE'] == score) &
            (df['VINTAGE_DATE'] == vintage) &
            (df['STATE_FORECAST'] == state)
        )
        
        ead_current_state = df.loc[state_mask, 'EAD_CURRENT'].sum()
        
        if ead_current_state > 0:
            ratio = ead_lifecycle_state / ead_current_state
            ratio = min(ratio, 1.0)  # Cap tại 1.0
            
            df.loc[state_mask, 'EAD_FORECAST'] = df.loc[state_mask, 'EAD_CURRENT'] * ratio
```

---

## 🔍 Điểm Quan Trọng

### 1. **PROB_DEL vs DEL_FLAG**

| Metric | Nguồn | Ý nghĩa | Giá trị |
|--------|-------|---------|---------|
| **PROB_DEL30** | Lifecycle (cohort-level) | Xác suất cohort thuộc DEL30+ | Giống nhau cho tất cả loans trong cohort |
| **DEL30_FLAG** | STATE_FORECAST (loan-level) | Loan có thuộc DEL30+ không | 0 hoặc 1 (khác nhau giữa các loans) |

**Ví dụ:**
- Cohort có PROB_DEL30 = 15%
- Loan L001: DEL30_FLAG = 0 (STATE_FORECAST = DPD0)
- Loan L002: DEL30_FLAG = 1 (STATE_FORECAST = DPD30+)
- Loan L003: DEL30_FLAG = 1 (STATE_FORECAST = DPD90+)

### 2. **EAD_DEL vs EAD_FORECAST**

| Metric | Công thức | Ý nghĩa |
|--------|-----------|---------|
| **EAD_DEL30** | DISBURSAL_AMOUNT × PROB_DEL30 | Dư nợ dự kiến thuộc nhóm DEL30+ (theo lifecycle) |
| **EAD_FORECAST** | EAD_CURRENT × ratio | Dư nợ dự báo còn lại tại MOB target |

**Validation:**
```
Tổng EAD_DEL30 / Tổng DISBURSAL = DEL30_PCT từ lifecycle ✅
```

### 3. **Tại Sao Cần Cả 2 Metrics?**

**EAD_DEL30 (từ lifecycle):**
- Dùng để tính ECL, dự phòng
- Ổn định, không phụ thuộc random sampling
- Khớp chính xác với lifecycle forecast

**STATE_FORECAST + DEL30_FLAG (từ sampling):**
- Dùng để phân tích chi tiết từng loan
- Tạo action list cho collection team
- Có yếu tố random (mỗi lần chạy khác nhau)

---

## 📋 Tóm Tắt Workflow

```
INPUT:
├── df_lifecycle_final (cohort-level forecast)
│   └── (PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB) → EAD per state, DEL%
└── df_loans_latest (loan-level current)
    └── (AGREEMENT_ID, PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB_CURRENT, STATE_CURRENT, EAD_CURRENT)

BƯỚC 1: Tính Combined Transition Matrix
├── Lấy matrices_by_mob[product][mob][score]
├── Nhân chuỗi: P(MOB_CURRENT→MOB_CURRENT+1) × ... × P(TARGET_MOB-1→TARGET_MOB)
└── Kết quả: final_probs per loan (xác suất cho mỗi state)

BƯỚC 2: Lấy DEL Rates từ Lifecycle
├── Merge lifecycle theo (PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE)
├── PROB_DEL30 = DEL30_PCT từ lifecycle (giống nhau cho tất cả loans trong cohort)
└── EAD_DEL30 = DISBURSAL_AMOUNT × PROB_DEL30

BƯỚC 3: Sample STATE_FORECAST
├── Random sampling theo final_probs từ BƯỚC 1
├── STATE_FORECAST = random.choice(states, p=final_probs)
└── DEL30_FLAG = 1 nếu STATE_FORECAST ∈ BUCKETS_30P

BƯỚC 4: Phân Bổ EAD_FORECAST
├── Groupby (PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE)
├── Với mỗi state: ratio = EAD_lifecycle_state / EAD_current_state
└── EAD_FORECAST = EAD_CURRENT × ratio

OUTPUT:
└── DataFrame với mỗi loan có:
    ├── STATE_FORECAST_MOB{X}: Trạng thái dự báo (sampled)
    ├── EAD_FORECAST_MOB{X}: Dư nợ dự báo (scaled)
    ├── PROB_DEL30_MOB{X}: Xác suất DEL30+ (từ lifecycle)
    ├── EAD_DEL30_MOB{X}: Dư nợ dự kiến thuộc DEL30+ (DISBURSAL × PROB)
    └── DEL30_FLAG_MOB{X}: Flag 0/1 (từ STATE_FORECAST)
```

---

## ✅ Validation Checklist

Sau khi allocation, kiểm tra:

```python
# 1. Tổng EAD_FORECAST khớp với lifecycle
total_ead_forecast = df_result['EAD_FORECAST'].sum()
total_ead_lifecycle = df_lifecycle_final[
    df_lifecycle_final['MOB'] == target_mob
][BUCKETS_CANON].sum(axis=1).sum()

assert abs(total_ead_forecast - total_ead_lifecycle) / total_ead_lifecycle < 0.01  # < 1% error

# 2. DEL30 rate khớp với lifecycle
total_disbursal = df_result['DISBURSAL_AMOUNT'].sum()
total_ead_del30 = df_result['EAD_DEL30'].sum()
del30_rate_calc = total_ead_del30 / total_disbursal

del30_rate_lifecycle = df_lifecycle_final[
    df_lifecycle_final['MOB'] == target_mob
]['DEL30_PCT'].mean()

assert abs(del30_rate_calc - del30_rate_lifecycle) < 0.001  # < 0.1% error

# 3. Số loans không đổi
assert len(df_result) == len(df_loans_latest)

# 4. Không có missing values
assert df_result['STATE_FORECAST'].notna().all()
assert df_result['EAD_FORECAST'].notna().all()
```

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-16
