# ✅ Đã cập nhật: Tài liệu chi tiết về Allocation Logic

## 📚 Files đã tạo/cập nhật

### 1. ✅ `ALLOCATION_LOGIC_DETAILED.md` (NEW)

**Nội dung:** Hướng dẫn chi tiết về logic allocation với:

#### 📊 Tổng quan
- Vấn đề cần giải quyết
- Input/Output data
- 3 câu hỏi quan trọng

#### 🔢 Logic chi tiết (8 bước)
1. **Chuẩn bị dữ liệu** - Input lifecycle & loans
2. **Tính phân phối state** - Xác suất từ lifecycle
3. **Lấy loans trong cohort** - Filter theo product/risk/vintage
4. **Tính tổng EAD current** - Sum EAD của loans
5. **Tính tỷ lệ EAD (ead_ratio)** - `Total_EAD_Forecast / Total_EAD_Current`
6. **Assign state** - Monte Carlo sampling
7. **Tính EAD_FORECAST** - `EAD_CURRENT × ead_ratio`
8. **Kết quả cuối cùng** - DataFrame với forecast

#### 📐 Công thức tổng quát
```
ead_ratio = Total_EAD_Forecast_Cohort / Total_EAD_Current_Cohort
EAD_FORECAST_loan = EAD_CURRENT_loan × ead_ratio
P(state) = EAD_state / Total_EAD_Forecast
```

#### 🔍 Ví dụ minh họa
- **Scenario 1:** 1 cohort, 10 loans
- **Scenario 2:** 3 cohorts, 30 loans
- Tính toán từng bước chi tiết

#### 🎯 Các trường hợp đặc biệt
1. EAD_FORECAST = EAD_CURRENT (không có prepay/writeoff)
2. EAD_FORECAST rất nhỏ (nhiều prepay/writeoff)
3. Không có loans trong cohort
4. Loans có EAD khác nhau

#### 🔄 So sánh 2 phương pháp
- **Simple (Monte Carlo):** 1 state per loan
- **Proportional:** Multiple states per loan

#### ✅ Validation checklist
- Tổng EAD khớp
- EAD_FORECAST <= EAD_CURRENT
- Không có missing values
- State distribution hợp lý
- Số lượng loans đúng

#### 🐛 Troubleshooting
- EAD_FORECAST = EAD_CURRENT (đã fix)
- Tổng EAD không khớp
- State distribution sai

### 2. ✅ `QUICK_GUIDE_MULTI_MOB.md` (UPDATED)

**Thêm section mới:**

#### Section 1: Giải thích EAD_FORECAST trong Output Format
```
⚠️ Quan trọng về EAD_FORECAST:
- EAD_FORECAST < EAD_CURRENT (thường xuyên)
- Giảm do: prepayment, writeoff, amortization
- Công thức: EAD_FORECAST = EAD_CURRENT × (Total_EAD_Forecast / Total_EAD_Current)
```

#### Section 2: Lưu ý về EAD_FORECAST Logic
```python
# Kiểm tra reduction
reduction_mob12 = (1 - df_result['EAD_FORECAST_MOB12'].sum() / df_result['EAD_CURRENT'].sum()) * 100
reduction_mob24 = (1 - df_result['EAD_FORECAST_MOB24'].sum() / df_result['EAD_CURRENT'].sum()) * 100

print(f"Reduction @ MOB 12: {reduction_mob12:.2f}%")
print(f"Reduction @ MOB 24: {reduction_mob24:.2f}%")
```

**Tại sao giảm?**
- Prepayment (trả trước)
- Writeoff (xóa nợ)
- Natural amortization (trả nợ theo kỳ hạn)

---

## 📊 Nội dung chi tiết

### Điểm quan trọng nhất

#### 1. EAD_FORECAST Logic

**Công thức cốt lõi:**
```
ead_ratio = Total_EAD_Forecast_Cohort / Total_EAD_Current_Cohort
EAD_FORECAST_loan = EAD_CURRENT_loan × ead_ratio
```

**Ví dụ cụ thể:**
```
Cohort:
  Total_EAD_Forecast = 750 (DPD0: 600, DPD30+: 150)
  
Loans (10 loans):
  Total_EAD_Current = 1,000 (mỗi loan 100)

Calculation:
  ead_ratio = 750 / 1,000 = 0.75
  
Result:
  LOAN_001: EAD_FORECAST = 100 × 0.75 = 75
  LOAN_002: EAD_FORECAST = 100 × 0.75 = 75
  ...
  Total: 750 ✅ (khớp với lifecycle)
```

#### 2. State Assignment (Monte Carlo)

**Logic:**
```python
# Xác suất từ lifecycle
state_probs = {
    'DPD0': 600 / 750 = 0.80 (80%),
    'DPD30+': 150 / 750 = 0.20 (20%)
}

# Random sampling
np.random.seed(42)  # Reproducible
assigned_states = np.random.choice(
    ['DPD0', 'DPD30+'],
    size=10,
    p=[0.80, 0.20]
)

# Kết quả: ~8 loans DPD0, ~2 loans DPD30+
```

#### 3. Validation

**3 checks quan trọng:**

1. **Tổng EAD khớp:**
   ```
   Total_EAD_Lifecycle = 750
   Total_EAD_Allocated = 75 × 10 = 750 ✅
   ```

2. **EAD_FORECAST <= EAD_CURRENT:**
   ```
   LOAN_001: 75 <= 100 ✅
   LOAN_002: 75 <= 100 ✅
   ...
   ```

3. **State distribution đúng:**
   ```
   DPD0: 8 loans (80%) ✅
   DPD30+: 2 loans (20%) ✅
   ```

---

## 🎯 Use Cases

### 1. Kiểm tra logic allocation

```python
# Đọc tài liệu
# File: ALLOCATION_LOGIC_DETAILED.md

# Chạy test
python test_ead_forecast_fix.py

# Kết quả:
# ✅ PASSED: All EAD_FORECAST <= EAD_CURRENT
# ✅ PASSED: Total EAD matches (< 0.01% diff)
```

### 2. Debug khi EAD_FORECAST = EAD_CURRENT

```python
# Kiểm tra ead_ratio
print(f"ead_ratio: {total_ead_forecast / total_ead_current}")

# Nếu = 1.0 → Không có prepay/writeoff
# Nếu < 1.0 → Có prepay/writeoff (bình thường)
```

### 3. Phân tích reduction theo cohort

```python
# Group by cohort
df_cohort_analysis = df_result.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']).agg({
    'EAD_CURRENT': 'sum',
    'EAD_FORECAST_MOB12': 'sum',
    'EAD_FORECAST_MOB24': 'sum'
})

df_cohort_analysis['REDUCTION_MOB12'] = (
    1 - df_cohort_analysis['EAD_FORECAST_MOB12'] / df_cohort_analysis['EAD_CURRENT']
) * 100

df_cohort_analysis['REDUCTION_MOB24'] = (
    1 - df_cohort_analysis['EAD_FORECAST_MOB24'] / df_cohort_analysis['EAD_CURRENT']
) * 100

print(df_cohort_analysis)
```

---

## 📚 Cấu trúc tài liệu

```
ALLOCATION_LOGIC_DETAILED.md (NEW)
├── 1. Tổng quan
│   ├── Vấn đề cần giải quyết
│   └── 3 câu hỏi quan trọng
│
├── 2. Logic chi tiết (8 bước)
│   ├── Bước 1: Chuẩn bị dữ liệu
│   ├── Bước 2: Tính phân phối state
│   ├── Bước 3: Lấy loans trong cohort
│   ├── Bước 4: Tính tổng EAD current
│   ├── Bước 5: Tính ead_ratio ⭐
│   ├── Bước 6: Assign state (Monte Carlo)
│   ├── Bước 7: Tính EAD_FORECAST ⭐
│   └── Bước 8: Kết quả cuối cùng
│
├── 3. Công thức tổng quát
│   ├── ead_ratio
│   ├── EAD_FORECAST per loan
│   └── State probability
│
├── 4. Ví dụ minh họa
│   ├── Scenario 1: 1 cohort, 10 loans
│   └── Scenario 2: 3 cohorts, 30 loans
│
├── 5. Trường hợp đặc biệt
│   ├── EAD_FORECAST = EAD_CURRENT
│   ├── EAD_FORECAST rất nhỏ
│   ├── Không có loans
│   └── Loans có EAD khác nhau
│
├── 6. So sánh 2 phương pháp
│   ├── Simple (Monte Carlo)
│   └── Proportional
│
├── 7. Validation checklist
│   ├── Tổng EAD khớp
│   ├── EAD_FORECAST <= EAD_CURRENT
│   ├── Không có missing
│   ├── State distribution
│   └── Số lượng loans
│
└── 8. Troubleshooting
    ├── EAD_FORECAST = EAD_CURRENT
    ├── Tổng EAD không khớp
    └── State distribution sai
```

---

## 🎓 Điểm mấu chốt

### 3 công thức quan trọng nhất:

1. **ead_ratio:**
   ```
   ead_ratio = Total_EAD_Forecast / Total_EAD_Current
   ```

2. **EAD_FORECAST:**
   ```
   EAD_FORECAST = EAD_CURRENT × ead_ratio
   ```

3. **State probability:**
   ```
   P(state) = EAD_state / Total_EAD_Forecast
   ```

### Tại sao EAD_FORECAST < EAD_CURRENT?

1. **Prepayment** - Khách hàng trả trước
2. **Writeoff** - Xóa nợ
3. **Amortization** - Trả nợ theo kỳ hạn

### Validation quan trọng:

✅ Tổng EAD khớp với lifecycle  
✅ EAD_FORECAST <= EAD_CURRENT  
✅ State distribution đúng tỷ lệ  

---

## 📁 Files liên quan

1. ✅ `ALLOCATION_LOGIC_DETAILED.md` - Hướng dẫn chi tiết (NEW)
2. ✅ `QUICK_GUIDE_MULTI_MOB.md` - Quick guide (UPDATED)
3. ✅ `FIX_EAD_FORECAST_LOGIC.md` - Chi tiết về fix
4. ✅ `test_ead_forecast_fix.py` - Test script
5. ✅ `src/rollrate/allocation.py` - Implementation

---

## 🚀 Git Status

✅ **Đã commit và push**

```bash
Commit: 39d8055
Message: "Add detailed allocation logic documentation"
Branch: main
Remote: https://github.com/Tri-1010/Projection_pb.git
```

---

## 🎯 Next Steps

Bây giờ bạn có thể:

1. **Đọc tài liệu chi tiết:**
   ```bash
   cat ALLOCATION_LOGIC_DETAILED.md
   ```

2. **Kiểm tra logic:**
   ```bash
   python test_ead_forecast_fix.py
   ```

3. **Re-run Complete_Workflow:**
   ```bash
   jupyter notebook notebooks/Complete_Workflow.ipynb
   ```

4. **Verify kết quả:**
   ```python
   # Kiểm tra EAD_FORECAST < EAD_CURRENT
   print(df_loan_forecast[['EAD_CURRENT', 'EAD_FORECAST_MOB12', 'EAD_FORECAST_MOB24']].head())
   ```

---

**Tóm tắt:** Đã tạo tài liệu chi tiết 700+ dòng giải thích logic allocation từng bước, bao gồm công thức, ví dụ, validation, và troubleshooting. Bạn có thể kiểm tra lại logic một cách chi tiết! 🎉
