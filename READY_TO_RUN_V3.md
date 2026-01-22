# ✅ READY TO RUN: V3 Full Layout

**Date**: 2026-01-19  
**Version**: 3.0 - Đầy đủ với K values  
**Status**: ✅ VERIFIED & READY

---

## ✅ Verification Complete

```
======================================================================
✅ ALL CHECKS PASSED - V3 IS READY!
======================================================================

🎉 Notebook has V3 export code with K values!

📝 V3 Layout includes:
   - Row 2-4: Current balance & loans (ngang)
   - Row 6-9: K_raw, K_smooth, Alpha (ngang)
   - Row 11+: Transition matrices (ngang)
```

---

## 🚀 Cách Chạy (2 Bước)

### Bước 1: Mở Notebook

```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

### Bước 2: Run All Cells

Click: **Cell → Run All**

Hoặc: **Kernel → Restart & Run All**

---

## 📊 Output Mong Đợi

### Console Output:

```
============================================================
📊 EXPORT COHORTS V3: 2025-10 và 2025-01
   Layout: Ngang đầy đủ (Current + K + TM)
============================================================
✅ VINTAGE_DATE created

2025-10-01:
  Cohorts: 15
  Loans: 12,345

2025-01-01:
  Cohorts: 18
  Loans: 15,678

============================================================
✅ Total cohorts: 33
============================================================

📤 Exporting 33 cohorts (v3 full layout)...
   ℹ️  Created alpha_by_mob from single alpha value: 0.8234
📊 Exporting forecast details (v3 - full horizontal layout)...
   Cohorts: 33
   Target MOB: 36
   [1/33] X_A_2025-10
   [2/33] X_B_2025-10
   ...

✅ Export completed!
   File: cohort_details/Cohort_Forecast_Details_v3_20260119_160000.xlsx

============================================================
✅ HOÀN THÀNH!
============================================================
📄 File: cohort_details/Cohort_Forecast_Details_v3_20260119_160000.xlsx
📊 Cohorts: 33

💡 Layout đầy đủ:
   - Row 2-4: Current balance & loans (ngang)
   - Row 6-9: K_raw, K_smooth, Alpha (ngang)
   - Row 11+: Transition matrices (ngang)
   → Có đủ thông tin để tính forecast!

🎯 Sẵn sàng gửi cho sếp!
============================================================
```

### Excel File:

**Location**: `cohort_details/Cohort_Forecast_Details_v3_YYYYMMDD_HHMMSS.xlsx`

**Mỗi Sheet** (1 cohort):

```
Row 1:  Cohort Info
Row 2:  Current MOB | 12 | C | 30 | 60 | 90 | 120 | 150 | CO
Row 3:  Current Balance | | $$ | $$ | $$ | $$ | $$ | $$ | $$
Row 4:  Number of Loans | | ## | ## | ## | ## | ## | ## | ##

Row 6:  K_raw | MOB → | 12 | 13 | 14 | 15 | ... | 36
Row 7:  K_raw values | | 0.95 | 0.94 | 0.93 | ... | 0.85
Row 8:  K_smooth values | | 0.96 | 0.95 | 0.94 | ... | 0.86
Row 9:  Alpha values | | 0.82 | 0.82 | 0.82 | ... | 0.82

Row 11: MOB | From | To C | To 30 | To 60 | ...
Row 12+: mob | bucket | % | % | % | ...
```

---

## 💡 Viết Công Thức Excel

### Forecast 1 Step (MOB 12 → 13):

```excel
# Balance trước K (row 200):
C200: =SUMPRODUCT($C$3:$I$3, C100:I100)
D200: =SUMPRODUCT($C$3:$I$3, C101:I101)
...

# Balance sau K (row 201):
C201: =C200 * $D$8  # D8 = K_smooth cho MOB 13
D201: =D200 * $D$8
...
```

### Forecast Multi-Steps:

```excel
# MOB 12 → 13
C200: =SUMPRODUCT($C$3:$I$3, C100:I100)
C201: =C200 * $D$8

# MOB 13 → 14
C202: =SUMPRODUCT($C201:$I201, C110:I110)
C203: =C202 * $E$8

# MOB 14 → 15
C204: =SUMPRODUCT($C203:$I203, C120:I120)
C205: =C204 * $F$8

# Copy pattern xuống đến target MOB...
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `QUICK_REFERENCE_V3.md` | Quick reference ⭐ |
| `GUIDE_V3_FULL_FORECAST.md` | Complete guide with formulas |
| `UPDATE_V3_WITH_K_VALUES.md` | Update summary |
| `READY_TO_RUN_V3.md` | This file |

---

## ⏱️ Expected Time

- **Small dataset** (< 100k loans): 5-10 phút
- **Medium dataset** (100k-500k loans): 10-30 phút
- **Large dataset** (> 500k loans): 30-60 phút

---

## ✅ Checklist

Trước khi chạy:
- [x] Notebook đã có V3 code (verified ✅)
- [ ] Jupyter đã được cài đặt
- [ ] Đã mở notebook
- [ ] Sẵn sàng chờ execution hoàn thành

Sau khi chạy:
- [ ] Không có errors
- [ ] Excel file được tạo trong `cohort_details/`
- [ ] File có tên `Cohort_Forecast_Details_v3_*.xlsx`
- [ ] Mở file và check:
  - [ ] Row 3: Current balance có data
  - [ ] Row 8: K_smooth có values
  - [ ] Row 11+: Transition matrices có data
- [ ] Viết công thức Excel để forecast
- [ ] Gửi cho sếp 🎉

---

## 🎯 Key Points

✅ **Row 3**: Current balance - điểm bắt đầu  
✅ **Row 8**: K_smooth values - hệ số điều chỉnh  
✅ **Row 11+**: Transition matrices - xác suất chuyển đổi  

**Formula**:
```
Final Forecast = (Previous Balance × TM) × K_smooth
```

---

## 🆘 Nếu Có Lỗi

### Error: ImportError export_cohort_details_v3
**Solution**: File `export_cohort_details_v3.py` phải ở cùng thư mục với notebook

### Error: KeyError 'VINTAGE_DATE'
**Solution**: Code tự động tạo, không nên xảy ra. Check DISBURSAL_DATE column exists

### Error: NameError 'alpha_by_mob'
**Solution**: Code tự động convert, không nên xảy ra. Check previous cells ran successfully

### Error: No data for month
**Solution**: Tháng đó không có data. Change `target_months` trong code

---

## 🎉 Summary

**Notebook**: ✅ Updated with V3  
**Layout**: ✅ Full horizontal with K values  
**Ready**: ✅ Verified and ready to run  

**Just run it!** 🚀

---

**Good luck!** 🎉

