# ✅ Update V4: Single Sheet Layout

**Date**: 2026-01-19  
**Version**: 4.0 - Single Sheet  
**Status**: ✅ READY

---

## 🎯 Thay Đổi Chính

### V3 (Cũ)
- ❌ Nhiều sheets (1 sheet per cohort)
- ❌ Khó so sánh giữa các cohorts

### V4 (Mới) ⭐
- ✅ **1 sheet duy nhất** (All_Cohorts)
- ✅ **Mỗi cohort cách nhau 2 dòng trống**
- ✅ **Có đầy đủ**: Current + K + Transition Matrix
- ✅ **Debug info** để check structure

---

## 📊 Layout V4

```
┌─────────────────────────────────────────────────────────────┐
│ COHORT: Product | Score | Vintage_Date                      │
├─────────────────────────────────────────────────────────────┤
│ Current MOB | 12 | C | 30 | 60 | 90 | 120 | 150 | CO | TOTAL│
│ Current Balance | | $$ | $$ | $$ | $$ | $$ | $$ | $$ | TOTAL│
│ Number of Loans | | ## | ## | ## | ## | ## | ## | ## | TOTAL│
├─────────────────────────────────────────────────────────────┤
│ K Values | MOB → | 12 | 13 | 14 | 15 | ... | 36             │
│ K_raw | | 0.95 | 0.94 | 0.93 | ... | 0.85                   │
│ K_smooth | | 0.96 | 0.95 | 0.94 | ... | 0.86                │
│ Alpha | | 0.82 | 0.82 | 0.82 | ... | 0.82                   │
├─────────────────────────────────────────────────────────────┤
│ Transition Matrix | From\To | C | 30 | 60 | 90 | ...        │
│ MOB 0 |                                                      │
│       | C | 95% | 3% | 1% | 0.5% | ...                      │
│       | 30 | 20% | 60% | 15% | 3% | ...                     │
│       | 60 | 10% | 15% | 50% | 20% | ...                    │
│ MOB 1 |                                                      │
│       | C | 96% | 2.5% | 0.8% | 0.4% | ...                  │
│       | 30 | 25% | 55% | 15% | 3% | ...                     │
│ ...                                                          │
├─────────────────────────────────────────────────────────────┤
│ [2 empty rows]                                               │
├─────────────────────────────────────────────────────────────┤
│ COHORT: Next Product | Score | Vintage_Date                 │
│ ...                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Những Gì Đã Sửa

### 1. Single Sheet
- Tất cả cohorts trong 1 sheet "All_Cohorts"
- Không còn nhiều sheets

### 2. Spacing
- Mỗi cohort cách nhau 2 dòng trống
- Dễ phân biệt giữa các cohorts

### 3. Transition Matrix
- Đã fix structure detection
- Hỗ trợ cả 2 formats:
  - `matrices_by_mob[(product, score)][mob]`
  - `matrices_by_mob[mob]`

### 4. Debug Info
- In ra structure của matrices_by_mob
- Dễ debug nếu có vấn đề

---

## 📁 Files Created

1. ✅ `export_cohort_details_v4.py` - Export function v4
2. ✅ `export_2025_10_and_2025_01_v4.py` - Export code v4
3. ✅ `update_notebook_with_v4.py` - Update script
4. ✅ `UPDATE_V4_SINGLE_SHEET.md` - This file

---

## 🚀 Cách Chạy

```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

Click: **Cell → Run All**

---

## 📊 Expected Output

```
============================================================
📊 EXPORT COHORTS V4: 2025-10 và 2025-01
   Layout: 1 sheet, mỗi cohort cách 2 dòng
============================================================

🔍 Debug matrices_by_mob:
   First key: ('X', 'A') (type: <class 'tuple'>)
   Structure: matrices_by_mob[(product, score)][mob] = DataFrame

   [1/33] X_A_2025-10
   [2/33] X_B_2025-10
   ...

✅ Export completed!
   File: cohort_details/Cohort_Forecast_Details_v4_20260119_170000.xlsx
   Sheet: All_Cohorts (single sheet)

============================================================
✅ HOÀN THÀNH!
============================================================
📄 File: cohort_details/Cohort_Forecast_Details_v4_20260119_170000.xlsx
📊 Cohorts: 33

💡 Layout V4:
   - 1 sheet duy nhất (All_Cohorts)
   - Mỗi cohort cách nhau 2 dòng
   - Có đầy đủ: Current + K + Transition Matrix

🎯 Sẵn sàng gửi cho sếp!
============================================================
```

---

## 🎯 Lợi Ích V4

### 1. Dễ So Sánh ✅
- Tất cả cohorts trong 1 sheet
- Scroll xuống để xem cohort tiếp theo

### 2. Dễ Viết Công Thức ✅
- Tất cả data trong 1 sheet
- Có thể reference giữa các cohorts

### 3. Có Đầy Đủ Thông Tin ✅
- Current balance
- K values (K_raw, K_smooth, Alpha)
- Transition matrices

### 4. Debug Friendly ✅
- In ra structure của data
- Dễ phát hiện vấn đề

---

## 💡 Viết Công Thức Excel

### Forecast cho Cohort 1 (bắt đầu từ row 2):

```excel
# Current balance: row 3
# K_smooth: row 7
# TM bắt đầu từ row 11

# Forecast MOB 12 → 13:
# Balance trước K:
=SUMPRODUCT($C$3:$I$3, C11:I11)

# Balance sau K:
=C20 * $D$7  # D7 = K_smooth cho MOB 13
```

### Forecast cho Cohort 2 (tìm row bắt đầu):

```excel
# Cohort 2 bắt đầu sau 2 dòng trống từ cohort 1
# Tìm row header "COHORT:" để xác định vị trí
```

---

## ✅ Verification

```
✅ Import OK
✅ Notebook updated with v4 export code
✅ Single sheet layout
✅ Transition matrices included
```

---

**V4 = Single sheet, đầy đủ thông tin, dễ sử dụng!** 🎉

