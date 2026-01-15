# 🎯 Quick Guide: Phân Bổ Forecast Tại MOB 12 & 24 + DEL30/DEL90

## ❓ Bạn Cần Gì?

Phân bổ forecast tại **2 MOB (12 và 24)** với **DEL30 và DEL90** cho mỗi loan.

---

## 💻 Code Nhanh Nhất (1 Function Duy Nhất)

```python
from src.rollrate.allocation_multi_mob import allocate_multi_mob_with_del_metrics

# 🔥 1 function duy nhất
df_result = allocate_multi_mob_with_del_metrics(
    df_lifecycle_final=df_lifecycle_final,  # Cohort-level forecast
    df_raw=df_raw,                          # Loan-level data
    target_mobs=[12, 24],                   # 🎯 MOB 12 và 24
    allocation_method="simple",
    include_del30=True,                     # ✅ Tính DEL30
    include_del60=False,
    include_del90=True,                     # ✅ Tính DEL90
)

print(f"✅ Kết quả: {len(df_result):,} loans")
```

---

## 📊 Output Format

```python
df_result.columns
```

Output:
```
['AGREEMENT_ID',              # Loan ID
 'PRODUCT_TYPE',              # Sản phẩm
 'RISK_SCORE',                # Risk score
 'VINTAGE_DATE',              # Tháng giải ngân
 'MOB_CURRENT',               # MOB hiện tại
 'EAD_CURRENT',               # EAD hiện tại
 
 # === Forecast tại MOB 12 ===
 'STATE_FORECAST_MOB12',      # State dự báo (DPD0, DPD30+, ...)
 'EAD_FORECAST_MOB12',        # EAD dự báo
 'DEL30_FLAG_MOB12',          # 0/1 (1 = DEL30+)
 'DEL90_FLAG_MOB12',          # 0/1 (1 = DEL90+)
 
 # === Forecast tại MOB 24 ===
 'STATE_FORECAST_MOB24',      # State dự báo
 'EAD_FORECAST_MOB24',        # EAD dự báo
 'DEL30_FLAG_MOB24',          # 0/1
 'DEL90_FLAG_MOB24',          # 0/1
]
```

**Giải thích:**
- Mỗi loan có **1 dòng duy nhất**
- Có forecast tại **2 MOB** (12 và 24)
- Có **DEL flags** (0/1) cho mỗi MOB

**⚠️ Quan trọng về EAD_FORECAST:**
- `EAD_FORECAST < EAD_CURRENT` (thường xuyên)
- Giảm do: prepayment, writeoff, amortization
- Công thức: `EAD_FORECAST = EAD_CURRENT × (Total_EAD_Forecast / Total_EAD_Current)`
- Xem chi tiết: `ALLOCATION_LOGIC_DETAILED.md`

**Ví dụ:**
```
LOAN_001:
  EAD_CURRENT = 100
  EAD_FORECAST_MOB12 = 75  (giảm 25%)
  EAD_FORECAST_MOB24 = 60  (giảm 40%)
```

---

## 🔍 Phân Tích Nhanh

### 1. Tổng Số Loans Có DEL90=1

```python
# Tại MOB 12
del90_mob12 = df_result["DEL90_FLAG_MOB12"].sum()
print(f"DEL90+ tại MOB 12: {del90_mob12:,} loans")

# Tại MOB 24
del90_mob24 = df_result["DEL90_FLAG_MOB24"].sum()
print(f"DEL90+ tại MOB 24: {del90_mob24:,} loans")
```

### 2. Migration: DEL90 (MOB 12 → 24)

```python
from src.rollrate.allocation_multi_mob import compare_del_across_mobs

df_migration = compare_del_across_mobs(
    df_multi_mob=df_result,
    target_mobs=[12, 24],
    metric="DEL90"
)

# Output:
# 📊 DEL90 Migration (MOB 12 → MOB 24):
#    0→0: 8,500 loans (85.0%)  # Không có DEL90 ở cả 2 MOB
#    0→1: 800 loans (8.0%)     # Deteriorate
#    1→0: 200 loans (2.0%)     # Improve
#    1→1: 500 loans (5.0%)     # Vẫn DEL90
```

### 3. Lọc Loans Theo Tiêu Chí

```python
# Loans dự báo DEL90+ tại MOB 12
high_risk = df_result[df_result["DEL90_FLAG_MOB12"] == 1]
print(f"High risk: {len(high_risk):,} loans")

# Loans deteriorate (0→1)
deteriorate = df_result[
    (df_result["DEL90_FLAG_MOB12"] == 0) &
    (df_result["DEL90_FLAG_MOB24"] == 1)
]
print(f"Deteriorate: {len(deteriorate):,} loans")

# Loans improve (1→0)
improve = df_result[
    (df_result["DEL90_FLAG_MOB12"] == 1) &
    (df_result["DEL90_FLAG_MOB24"] == 0)
]
print(f"Improve: {len(improve):,} loans")
```

---

## 📈 Pivot Table: DEL90% Theo Product × MOB

```python
from src.rollrate.allocation_multi_mob import pivot_del_by_product_mob

df_pivot = pivot_del_by_product_mob(
    df_multi_mob=df_result,
    target_mobs=[12, 24],
    metric="DEL90"
)

print(df_pivot)
```

Output:
```
              MOB12  MOB24
PRODUCT_TYPE              
CDLPIL         3.5%   5.2%
TWLPIL         4.2%   6.8%
SPLPIL         2.8%   4.1%
```

---

## 💾 Export Ra Excel

```python
from src.rollrate.allocation_multi_mob import export_multi_mob_to_excel

export_multi_mob_to_excel(
    df_multi_mob=df_result,
    filename="outputs/Loan_Forecast_MOB12_MOB24.xlsx",
    target_mobs=[12, 24]
)
```

**Sheets trong Excel:**
1. `All_Loans`: Tất cả loans
2. `DEL30_MOB12`: Loans có DEL30=1 tại MOB 12
3. `DEL30_MOB24`: Loans có DEL30=1 tại MOB 24
4. `DEL90_MOB12`: Loans có DEL90=1 tại MOB 12
5. `DEL90_MOB24`: Loans có DEL90=1 tại MOB 24
6. `Summary`: Tổng hợp số liệu

---

## 🎯 Use Cases

### 1. IFRS9 ECL Calculation

```python
# Tính ECL dựa trên DEL90
LGD = 0.45
DISCOUNT_RATE = 0.10

# ECL tại MOB 12 (12-month ECL)
df_result["ECL_MOB12"] = (
    df_result["EAD_FORECAST_MOB12"] *
    df_result["DEL90_FLAG_MOB12"] *
    LGD /
    ((1 + DISCOUNT_RATE) ** 1)  # Discount 12 tháng
)

# ECL tại MOB 24
df_result["ECL_MOB24"] = (
    df_result["EAD_FORECAST_MOB24"] *
    df_result["DEL90_FLAG_MOB24"] *
    LGD /
    ((1 + DISCOUNT_RATE) ** 2)  # Discount 24 tháng
)

# Tổng ECL
print(f"Total ECL (MOB 12): {df_result['ECL_MOB12'].sum():,.0f}")
print(f"Total ECL (MOB 24): {df_result['ECL_MOB24'].sum():,.0f}")
```

### 2. Collection Planning

```python
# Tạo action list cho collection team
# Loans dự báo sẽ rơi vào DEL30+ tại MOB 12
action_list = df_result[
    df_result["DEL30_FLAG_MOB12"] == 1
].copy()

# Sort theo EAD (ưu tiên loans có EAD cao)
action_list = action_list.sort_values("EAD_FORECAST_MOB12", ascending=False)

# Export
action_list.to_excel(
    "outputs/Collection_Action_List_MOB12.xlsx",
    columns=[
        "AGREEMENT_ID",
        "CUSTOMER_NAME",
        "BRANCH_CODE",
        "STATE_FORECAST_MOB12",
        "EAD_FORECAST_MOB12",
        "PHONE_NUMBER"
    ],
    index=False
)
```

### 3. Stress Testing

```python
# So sánh baseline vs stress scenario
df_baseline = allocate_multi_mob_with_del_metrics(
    df_lifecycle_final=df_lifecycle_baseline,
    df_raw=df_raw,
    target_mobs=[12, 24],
    include_del90=True
)

df_stress = allocate_multi_mob_with_del_metrics(
    df_lifecycle_final=df_lifecycle_stress,
    df_raw=df_raw,
    target_mobs=[12, 24],
    include_del90=True
)

# So sánh DEL90
print("Baseline DEL90 (MOB 12):", df_baseline["DEL90_FLAG_MOB12"].mean())
print("Stress DEL90 (MOB 12):", df_stress["DEL90_FLAG_MOB12"].mean())

# Impact
impact = (
    df_stress["DEL90_FLAG_MOB12"].sum() -
    df_baseline["DEL90_FLAG_MOB12"].sum()
)
print(f"Impact: +{impact:,} loans")
```

---

## 📚 Tài Liệu Chi Tiết

- **Code implementation:** `src/rollrate/allocation_multi_mob.py`
- **Demo notebook:** `notebooks/Multi_MOB_Demo.ipynb`
- **Guide tổng quan:** `guide.md`

---

## ⚠️ Lưu Ý

### 1. EAD_FORECAST Logic (Quan Trọng!)

**EAD_FORECAST thường nhỏ hơn EAD_CURRENT:**

```python
# Kiểm tra
print(f"EAD_CURRENT (avg): {df_result['EAD_CURRENT'].mean():,.2f}")
print(f"EAD_FORECAST_MOB12 (avg): {df_result['EAD_FORECAST_MOB12'].mean():,.2f}")
print(f"EAD_FORECAST_MOB24 (avg): {df_result['EAD_FORECAST_MOB24'].mean():,.2f}")

# Reduction
reduction_mob12 = (1 - df_result['EAD_FORECAST_MOB12'].sum() / df_result['EAD_CURRENT'].sum()) * 100
reduction_mob24 = (1 - df_result['EAD_FORECAST_MOB24'].sum() / df_result['EAD_CURRENT'].sum()) * 100

print(f"Reduction @ MOB 12: {reduction_mob12:.2f}%")
print(f"Reduction @ MOB 24: {reduction_mob24:.2f}%")
```

**Tại sao giảm?**
- Prepayment (trả trước)
- Writeoff (xóa nợ)
- Natural amortization (trả nợ theo kỳ hạn)

**Công thức:**
```
ead_ratio = Total_EAD_Forecast_Cohort / Total_EAD_Current_Cohort
EAD_FORECAST_loan = EAD_CURRENT_loan × ead_ratio
```

**Xem chi tiết:** `ALLOCATION_LOGIC_DETAILED.md`

### 2. Kiểm Tra Max Forecast MOB

```python
# Kiểm tra xem bạn đã forecast đến MOB nào
max_forecast_mob = df_lifecycle_final[
    df_lifecycle_final["IS_FORECAST"] == 1
]["MOB"].max()

print(f"Max forecast MOB: {max_forecast_mob}")

# Nếu max_forecast_mob < 24
# → Cần forecast thêm hoặc giảm target_mobs
```

### 3. DEL Flags Logic

```python
# DEL30_FLAG = 1 nếu STATE_FORECAST in ["DPD30+", "DPD60+", "DPD90+", "DPD120+", "DPD180+", "WRITEOFF"]
# DEL90_FLAG = 1 nếu STATE_FORECAST in ["DPD90+", "DPD120+", "DPD180+", "WRITEOFF"]
```

### 4. Allocation Method

- `"simple"`: Mỗi loan 1 state (Monte Carlo sampling) - **Khuyến nghị**
- `"proportional"`: Mỗi loan nhiều states theo tỷ lệ - Phức tạp hơn

---

## 🆘 Troubleshooting

### Vấn đề: "Không có dữ liệu forecast để phân bổ"

**Giải pháp:**
```python
# Kiểm tra
print(df_lifecycle_final["MOB"].max())
print(df_lifecycle_final["IS_FORECAST"].value_counts())

# Nếu max MOB < 24 → Cần forecast thêm
```

### Vấn đề: "Thiếu cột DEL30_FLAG_MOB12"

**Giải pháp:**
```python
# Đảm bảo include_del30=True
df_result = allocate_multi_mob_with_del_metrics(
    ...,
    include_del30=True,  # ✅
)
```

---

**Tóm lại:**
- **1 function** → Phân bổ tại nhiều MOB + tính DEL flags
- **1 dòng per loan** → Dễ phân tích
- **Export Excel** → Nhiều sheets tiện lợi

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15
