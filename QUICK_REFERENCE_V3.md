# 🚀 Quick Reference: V3 Full Forecast

**Version**: 3.0 - Layout đầy đủ với K values  
**Updated**: 2026-01-19

---

## 📊 Layout

```
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

## 💡 Công Thức Forecast

### 1 Step (MOB 12 → 13):

```excel
# Balance trước K (row 200):
C200: =SUMPRODUCT($C$3:$I$3, C100:I100)

# Balance sau K (row 201):
C201: =C200 * $D$8
```

### Multi-Steps:

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

# Copy pattern xuống...
```

---

## 🎯 Key Points

✅ **Row 3**: Current balance  
✅ **Row 8**: K_smooth values (dùng để nhân)  
✅ **Row 11+**: Transition matrices  

**Formula**:
1. Balance trước K = SUMPRODUCT(previous, TM)
2. Balance sau K = Balance trước K × K_smooth

---

## 🚀 Run

```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

Click: **Cell → Run All**

Output: `cohort_details/Cohort_Forecast_Details_v3_*.xlsx`

---

## 📚 More Info

- **Complete guide**: `GUIDE_V3_FULL_FORECAST.md`
- **Update summary**: `UPDATE_V3_WITH_K_VALUES.md`

---

**Đơn giản và đầy đủ!** 🎉

