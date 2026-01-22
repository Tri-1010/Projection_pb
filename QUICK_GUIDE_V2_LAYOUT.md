# 🚀 Quick Guide: V2 Horizontal Layout

**Version**: 2.0 - Layout ngang để viết công thức Excel  
**Updated**: 2026-01-19

---

## 📊 Layout Mới

### Mỗi Sheet (1 Cohort):

```
Row 1:  Headers
Row 2:  Current MOB | value | C | 30 | 60 | 90 | 120 | 150 | CO | TOTAL
Row 3:  Current Balance | | $ | $ | $ | $ | $ | $ | $ | TOTAL
Row 4:  Number of Loans | | # | # | # | # | # | # | # | TOTAL
Row 5-8: Info (Target MOB, Forecast Steps, etc.)
Row 9:  Empty
Row 10: TM Headers | MOB | From | To C | To 30 | To 60 | ...
Row 11+: TM Data | mob | bucket | % | % | % | ...
```

---

## 💡 Ví Dụ Viết Công Thức

### Forecast 1 Step (MOB 12 → 13):

```excel
# Giả sử:
# - Current balance: row 3, columns C:I
# - TM MOB 12: rows 100-106

# Forecast balance cho bucket C (column C):
=SUMPRODUCT($C$3:$I$3, C100:I100)

# Forecast balance cho bucket 30 (column D):
=SUMPRODUCT($C$3:$I$3, C101:I101)

# Copy công thức sang phải cho các buckets khác
```

### Forecast Multi-Steps:

```excel
# Row 200: MOB 12 → 13
C200: =SUMPRODUCT($C$3:$I$3, C100:I100)

# Row 201: MOB 13 → 14 (dùng balance từ row 200)
C201: =SUMPRODUCT($C200:$I200, C110:I110)

# Row 202: MOB 14 → 15
C202: =SUMPRODUCT($C201:$I201, C120:I120)

# Copy pattern xuống để forecast đến target MOB
```

---

## 🎯 Lợi Ích

✅ **Dễ viết công thức** - Tất cả buckets trên 1 dòng  
✅ **Dễ đọc** - Nhìn ngang thấy ngay distribution  
✅ **Dễ forecast** - Copy công thức xuống để forecast nhiều steps  
✅ **Dễ kiểm tra** - Sum ngang để check total

---

## 🚀 Cách Sử Dụng

### 1. Run Notebook

```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

Click: **Cell → Run All**

### 2. Mở Excel File

File: `cohort_details/Cohort_Forecast_Details_v2_*.xlsx`

### 3. Chọn Sheet

Mỗi sheet = 1 cohort

### 4. Viết Công Thức

- Row 3: Current balance
- Row 10+: Transition matrices
- Dùng SUMPRODUCT để forecast

---

## 📝 Template

```excel
# Forecast balance cho bucket X tại MOB N+1:
=SUMPRODUCT($C$3:$I$3, [TM_row_for_bucket_X])

# Trong đó:
# - $C$3:$I$3 = current balance (hoặc previous forecast)
# - [TM_row_for_bucket_X] = transition probabilities từ tất cả buckets → bucket X
```

---

## ✅ Checklist

- [ ] Current balance ở row 3
- [ ] TM bắt đầu từ row 10
- [ ] Buckets nằm ngang (C, 30, 60, 90, 120, 150, CO)
- [ ] Dùng SUMPRODUCT để forecast
- [ ] Check total = sum của các buckets

---

**Đơn giản và hiệu quả!** 🎉

