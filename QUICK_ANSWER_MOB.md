# ❓ EAD Forecast Được Lấy Tại MOB Mấy?

## 🎯 Câu Trả Lời Nhanh

**TÙY MỤC ĐÍCH SỬ DỤNG!**

### 1. IFRS9 12-Month ECL (Stage 1)
```python
target_mob = current_mob + 12  # Ví dụ: MOB hiện tại 5 → target_mob = 17
```

### 2. IFRS9 Lifetime ECL (Stage 2/3)
```python
target_mob = 36  # Hoặc 48, 60 (maturity của loan)
```

### 3. Collection Planning (3-6 tháng)
```python
target_mob = current_mob + 3  # Hoặc +6
```

### 4. Portfolio Monitoring (xem toàn bộ curve)
```python
target_mob = None  # Lấy tất cả MOB
```

---

## 💻 Code Ví Dụ

### Ví Dụ 1: IFRS9 12-Month ECL

```python
from src.rollrate.allocation import allocate_forecast_to_loans_simple

# Xác định MOB hiện tại
latest_cutoff = df_raw["CUTOFF_DATE"].max()
df_current = df_raw[df_raw["CUTOFF_DATE"] == latest_cutoff]
current_mob_max = df_current["MOB"].max()

print(f"MOB hiện tại: {current_mob_max}")
print(f"Target MOB (12 tháng tới): {current_mob_max + 12}")

# Phân bổ forecast tại MOB = current + 12
df_allocated = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=current_mob_max + 12,  # 🔥 12 tháng tới
    forecast_only=True,
)

print(f"✅ Kết quả: {len(df_allocated):,} loans")
print(f"   EAD forecast tại MOB {current_mob_max + 12}")
```

### Ví Dụ 2: Lifetime ECL (đến maturity)

```python
# Giả sử loan có term 36 tháng
df_allocated = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=36,  # 🔥 Maturity
    forecast_only=True,
)

print(f"✅ Kết quả: {len(df_allocated):,} loans")
print(f"   EAD forecast tại MOB 36 (maturity)")
```

### Ví Dụ 3: Tất Cả MOB (Portfolio Monitoring)

```python
# Lấy tất cả MOB để vẽ vintage curve
df_allocated_all = allocate_forecast_to_loans_simple(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=None,  # 🔥 Tất cả MOB
    forecast_only=True,
)

print(f"✅ Kết quả: {len(df_allocated_all):,} loan-level forecasts")
print(f"   MOB range: {df_allocated_all['TARGET_MOB'].min()} - {df_allocated_all['TARGET_MOB'].max()}")

# Vẽ curve
import matplotlib.pyplot as plt

for vintage in df_allocated_all["VINTAGE_DATE"].unique()[:5]:  # Top 5 vintages
    df_v = df_allocated_all[df_allocated_all["VINTAGE_DATE"] == vintage]
    
    # DEL90 theo MOB
    del90 = (
        df_v[df_v["STATE_FORECAST"].isin(["DPD90+", "WRITEOFF"])]
        .groupby("TARGET_MOB")["EAD_FORECAST"]
        .sum()
    )
    
    plt.plot(del90.index, del90.values, label=str(vintage)[:7])

plt.xlabel("MOB")
plt.ylabel("DEL90 EAD")
plt.legend()
plt.title("Vintage Curves")
plt.show()
```

---

## 📊 Output Columns

Sau khi phân bổ, bạn sẽ có:

```python
df_allocated.columns
```

Output:
```
['AGREEMENT_ID',           # Loan ID
 'PRODUCT_TYPE',           # Sản phẩm
 'RISK_SCORE',             # Risk score
 'VINTAGE_DATE',           # Tháng giải ngân
 'MOB',                    # = TARGET_MOB (MOB được phân bổ)
 'MOB_CURRENT',            # MOB hiện tại của loan
 'STATE_FORECAST',         # State dự báo (DPD0, DPD30+, ...)
 'EAD_FORECAST',           # EAD dự báo
 'IS_FORECAST',            # = 1 (forecast)
 'TARGET_MOB',             # MOB được phân bổ
 ...]
```

**Giải thích:**
- `TARGET_MOB`: MOB mà bạn chọn để phân bổ (12, 24, 36, ...)
- `MOB_CURRENT`: MOB hiện tại của loan (có thể khác TARGET_MOB)
- `EAD_FORECAST`: EAD dự báo tại TARGET_MOB

---

## ⚠️ Lưu Ý Quan Trọng

### 1. MOB Hiện Tại vs Target MOB

```python
# Loan A: giải ngân 1/2023, hiện tại 1/2024
# → MOB_CURRENT = 12

# Nếu target_mob = 24
# → Forecast EAD tại MOB 24 (12 tháng tới)

# Nếu target_mob = 36
# → Forecast EAD tại MOB 36 (24 tháng tới)
```

### 2. Kiểm Tra Max Forecast MOB

```python
# Kiểm tra xem bạn đã forecast đến MOB nào
max_forecast_mob = df_lifecycle_final[
    df_lifecycle_final["IS_FORECAST"] == 1
]["MOB"].max()

print(f"Max forecast MOB: {max_forecast_mob}")

# Nếu target_mob > max_forecast_mob
# → Sẽ không có data để phân bổ
# → Cần forecast thêm hoặc giảm target_mob
```

### 3. Validation

```python
from src.rollrate.allocation import validate_allocation

# Kiểm tra tổng EAD có khớp không
compare = validate_allocation(
    df_allocated=df_allocated,
    df_lifecycle_final=df_lifecycle_final,
)

# Xem kết quả
print(compare["STATUS"].value_counts())
```

---

## 📚 Tài Liệu Chi Tiết

- **Chi tiết đầy đủ:** `docs/MOB_SELECTION_GUIDE.md`
- **Code implementation:** `src/rollrate/allocation.py`
- **Demo notebook:** `notebooks/Allocation_Demo.ipynb`
- **Guide tổng quan:** `guide.md` (Phần 8)

---

## 🆘 Troubleshooting

### Vấn đề: "Không có dữ liệu forecast để phân bổ"

**Nguyên nhân:**
- `target_mob` lớn hơn max forecast MOB
- Hoặc không có forecast rows (IS_FORECAST=1)

**Giải pháp:**
```python
# Kiểm tra
print(df_lifecycle_final["MOB"].max())
print(df_lifecycle_final["IS_FORECAST"].value_counts())

# Giảm target_mob hoặc forecast thêm
```

### Vấn đề: "Tổng EAD không khớp"

**Nguyên nhân:**
- Allocation method không phù hợp
- Hoặc có lỗi trong data

**Giải pháp:**
```python
# Dùng validate_allocation để kiểm tra
compare = validate_allocation(df_allocated, df_lifecycle_final)
errors = compare[compare["STATUS"] != "OK"]
print(errors)
```

---

**Tóm lại:** 
- **IFRS9 12M ECL** → `target_mob = current_mob + 12`
- **IFRS9 Lifetime ECL** → `target_mob = maturity (36, 48, 60)`
- **Portfolio Monitoring** → `target_mob = None`

**Tác giả:** Roll Rate Model Team  
**Cập nhật:** 2025-01-15
