# 📍 Hướng Dẫn Chọn MOB Cho Phân Bổ Forecast

## ❓ Câu Hỏi: EAD Forecast Được Lấy Tại MOB Mấy?

Đây là câu hỏi **CỰC KỲ QUAN TRỌNG** vì nó quyết định:
- Khoản dự phòng (ECL) bạn tính
- Báo cáo tài chính
- Tuân thủ IFRS9/Basel

---

## 🎯 Các Trường Hợp Sử Dụng

### 1. IFRS9 - 12-Month ECL (Stage 1)

**Mục đích:** Tính ECL cho 12 tháng tới

**Chọn MOB:**
```python
target_mob = 12  # Hoặc MOB_hiện_tại + 12
```

**Ví dụ:**
```python
# Loan hiện tại đang ở MOB 3
# Forecast đến MOB 15 (3 + 12)
df_allocated = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=15,  # MOB 3 + 12 tháng
)
```

**Giải thích:**
- IFRS9 Stage 1 yêu cầu tính ECL cho 12 tháng tới
- Nếu loan đang ở MOB 3, bạn cần forecast đến MOB 15
- EAD forecast tại MOB 15 sẽ được dùng để tính ECL

---

### 2. IFRS9 - Lifetime ECL (Stage 2/3)

**Mục đích:** Tính ECL cho toàn bộ vòng đời còn lại

**Chọn MOB:**
```python
target_mob = None  # Hoặc max_mob (36, 48, 60)
```

**Ví dụ:**
```python
# Loan có term 36 tháng, hiện tại MOB 10
# Forecast đến MOB 36 (maturity)
df_allocated = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=36,  # Maturity
)
```

**Giải thích:**
- Stage 2/3 yêu cầu tính ECL cho toàn bộ vòng đời
- Thường forecast đến maturity (36, 48, 60 tháng)
- Hoặc dùng `target_mob=None` để lấy tất cả MOB forecast

---

### 3. Stress Testing

**Mục đích:** Đánh giá tác động của stress scenario

**Chọn MOB:**
```python
target_mob = 12  # Hoặc 24, 36 tùy scenario
```

**Ví dụ:**
```python
# Stress test: Tác động sau 12 tháng
df_allocated_stress = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_stress,  # Lifecycle với stress k
    df_raw=df_raw,
    target_mob=12,
)

# So sánh với baseline
df_allocated_base = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_base,
    df_raw=df_raw,
    target_mob=12,
)

# Tính impact
impact = df_allocated_stress["EAD_FORECAST"].sum() - df_allocated_base["EAD_FORECAST"].sum()
```

---

### 4. Collection Planning

**Mục đích:** Tạo action list cho collection team

**Chọn MOB:**
```python
target_mob = 3  # Hoặc 6, 12 tùy planning horizon
```

**Ví dụ:**
```python
# Forecast 3 tháng tới để lập kế hoạch collection
df_allocated = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=3,  # 3 tháng tới
)

# Lọc loans dự báo sẽ rơi vào DPD30+
high_risk = df_allocated[
    df_allocated["STATE_FORECAST"].isin(["DPD30+", "DPD60+", "DPD90+"])
]

# Export cho collection team
high_risk.to_excel("Collection_Action_List_3M.xlsx")
```

---

### 5. Portfolio Monitoring

**Mục đích:** Theo dõi xu hướng portfolio

**Chọn MOB:**
```python
target_mob = None  # Lấy tất cả MOB để vẽ curve
```

**Ví dụ:**
```python
# Lấy tất cả MOB forecast
df_allocated_all = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=None,  # Tất cả MOB
)

# Vẽ vintage curve
import matplotlib.pyplot as plt

for vintage in df_allocated_all["VINTAGE_DATE"].unique():
    df_v = df_allocated_all[df_allocated_all["VINTAGE_DATE"] == vintage]
    
    # Tính DEL90 theo MOB
    del90_curve = (
        df_v[df_v["STATE_FORECAST"].isin(["DPD90+", "WRITEOFF"])]
        .groupby("TARGET_MOB")["EAD_FORECAST"]
        .sum()
    )
    
    plt.plot(del90_curve.index, del90_curve.values, label=vintage)

plt.legend()
plt.show()
```

---

## 📊 Bảng Tóm Tắt

| Use Case | Target MOB | Lý Do |
|----------|-----------|-------|
| **IFRS9 Stage 1** | 12 (hoặc current+12) | 12-month ECL |
| **IFRS9 Stage 2/3** | None hoặc max_mob | Lifetime ECL |
| **Stress Testing** | 12, 24, 36 | Theo scenario horizon |
| **Collection Planning** | 3, 6, 12 | Theo planning horizon |
| **Portfolio Monitoring** | None | Xem toàn bộ curve |
| **Regulatory Reporting** | 12, 24 | Theo yêu cầu regulator |

---

## 🔍 Cách Xác Định MOB Phù Hợp

### Bước 1: Xác định mục đích

```python
# Ví dụ: IFRS9 ECL calculation
purpose = "IFRS9_12M_ECL"
```

### Bước 2: Xác định MOB hiện tại của loan

```python
# Lấy MOB hiện tại từ df_raw
latest_cutoff = df_raw["CUTOFF_DATE"].max()
df_current = df_raw[df_raw["CUTOFF_DATE"] == latest_cutoff]

current_mob = df_current.groupby("AGREEMENT_ID")["MOB"].max()
print(f"MOB hiện tại: min={current_mob.min()}, max={current_mob.max()}")
```

### Bước 3: Tính target MOB

```python
if purpose == "IFRS9_12M_ECL":
    # Forecast 12 tháng từ hiện tại
    target_mob = current_mob.max() + 12
    
elif purpose == "IFRS9_LIFETIME_ECL":
    # Forecast đến maturity
    target_mob = 36  # Hoặc 48, 60 tùy product
    
elif purpose == "STRESS_TEST":
    # Theo scenario
    target_mob = 12  # Hoặc 24
    
else:
    # Lấy tất cả
    target_mob = None
```

### Bước 4: Phân bổ

```python
df_allocated = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=target_mob,
)
```

---

## ⚠️ Lưu Ý Quan Trọng

### 1. MOB vs Vintage Age

```python
# ❌ SAI: Nhầm lẫn giữa MOB và vintage age
target_mob = 12  # MOB 12 của loan

# ✅ ĐÚNG: MOB là tuổi của loan kể từ giải ngân
# Nếu loan giải ngân tháng 1/2023, hiện tại là 1/2024
# → MOB hiện tại = 12
# → Forecast 12 tháng tới = MOB 24
```

### 2. Cohort-Level vs Loan-Level MOB

```python
# df_lifecycle_final: MOB là tuổi của cohort
# df_raw: MOB là tuổi của từng loan

# Khi phân bổ:
# - Lấy forecast tại MOB cohort (TARGET_MOB)
# - Assign cho loans trong cohort đó
# - Loan có thể có MOB_CURRENT khác TARGET_MOB
```

### 3. Forecast Horizon

```python
# Nếu bạn chỉ forecast đến MOB 24
# Nhưng target_mob=36
# → Sẽ không có data để phân bổ

# Kiểm tra trước:
max_forecast_mob = df_lifecycle_final[df_lifecycle_final["IS_FORECAST"]==1]["MOB"].max()
print(f"Max forecast MOB: {max_forecast_mob}")

if target_mob > max_forecast_mob:
    print(f"⚠️ target_mob={target_mob} > max_forecast_mob={max_forecast_mob}")
    print(f"   Cần forecast thêm hoặc giảm target_mob")
```

---

## 💡 Best Practices

### 1. IFRS9 ECL Calculation

```python
# Stage 1: 12-month ECL
df_stage1 = df_raw[df_raw["IFRS9_STAGE"] == 1]
current_mob_s1 = df_stage1.groupby("AGREEMENT_ID")["MOB"].max().max()

df_allocated_s1 = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_stage1,
    target_mob=current_mob_s1 + 12,  # 12 tháng tới
)

# Stage 2/3: Lifetime ECL
df_stage23 = df_raw[df_raw["IFRS9_STAGE"].isin([2, 3])]

df_allocated_s23 = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_stage23,
    target_mob=None,  # Toàn bộ lifetime
)

# Combine
df_ecl = pd.concat([df_allocated_s1, df_allocated_s23])
```

### 2. Multiple Horizons

```python
# Tính ECL cho nhiều horizons
horizons = [12, 24, 36]
results = {}

for h in horizons:
    df_alloc = allocate_forecast_to_loans_simple(
        df_lifecycle_final=df_lifecycle_final,
        df_raw=df_raw,
        target_mob=h,
    )
    
    results[f"ECL_{h}M"] = df_alloc["EAD_FORECAST"].sum()

print(results)
# {'ECL_12M': 1234567, 'ECL_24M': 2345678, 'ECL_36M': 3456789}
```

### 3. Validation

```python
# Kiểm tra target_mob có hợp lý không
def validate_target_mob(df_lifecycle, target_mob):
    available_mobs = df_lifecycle["MOB"].unique()
    
    if target_mob not in available_mobs:
        print(f"⚠️ target_mob={target_mob} không có trong lifecycle")
        print(f"   Available MOBs: {sorted(available_mobs)}")
        return False
    
    return True

# Sử dụng
if validate_target_mob(df_lifecycle_final, target_mob=12):
    df_allocated = allocate_forecast_to_loans_simple(...)
```

---

## 📚 Tài Liệu Tham Khảo

- IFRS9 Standard: [Link](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/)
- Basel III: [Link](https://www.bis.org/bcbs/basel3.htm)
- `src/rollrate/allocation.py`: Code implementation
- `notebooks/Allocation_Demo.ipynb`: Examples

---

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15
