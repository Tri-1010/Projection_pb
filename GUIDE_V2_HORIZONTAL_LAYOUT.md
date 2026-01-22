# 📊 Guide: V2 Horizontal Layout

**Version**: 2.0  
**Date**: 2026-01-19  
**Layout**: Horizontal (ngang) để viết công thức Excel

---

## 🎯 Thay Đổi Chính

### Version 1 (Cũ)
- Layout dọc (vertical)
- Khó viết công thức Excel

### Version 2 (Mới) ⭐
- **Layout ngang (horizontal)**
- **Dễ viết công thức Excel tính ngang**
- Current balance ở row 2-4
- Transition matrices bắt đầu từ row 10

---

## 📋 Layout Chi Tiết

### Mỗi Sheet (1 Cohort)

```
Row 1:  [Headers] Cohort Info | Product_Score_Vintage
Row 2:  [Current MOB] | MOB_value | C | 30 | 60 | 90 | 120 | 150 | CO | TOTAL
Row 3:  [Current Balance] | | balance_C | balance_30 | ... | TOTAL
Row 4:  [Number of Loans] | | loans_C | loans_30 | ... | TOTAL
Row 5:  [Target MOB] | target_value
Row 6:  [Forecast Steps] | steps
Row 7:  [Total Disbursement] | amount
Row 8:  [Vintage Date] | date
Row 9:  [Empty]
Row 10: [Headers] MOB | From Bucket | To C | To 30 | To 60 | ... (TM headers)
Row 11+: [TM Data] mob | from_bucket | prob_to_C | prob_to_30 | ...
```

---

## 💡 Ví Dụ Cụ Thể

### Sheet: X_A_2025-10

```
Row 1:  Cohort Info | X | A | 2025-10-01
Row 2:  Current MOB | 12 | C | 30 | 60 | 90 | 120 | 150 | CO | TOTAL
Row 3:  Current Balance | | 1,000,000 | 500,000 | 200,000 | 100,000 | 50,000 | 30,000 | 20,000 | 1,900,000
Row 4:  Number of Loans | | 100 | 50 | 20 | 10 | 5 | 3 | 2 | 190
Row 5:  Target MOB | 36
Row 6:  Forecast Steps | 24
Row 7:  Total Disbursement | 2,500,000
Row 8:  Vintage Date | 2025-10-01
Row 9:  
Row 10: MOB | From Bucket | To C | To 30 | To 60 | To 90 | To 120 | To 150 | To CO
Row 11: 0 | C | 95.00% | 3.00% | 1.00% | 0.50% | 0.30% | 0.10% | 0.10%
Row 12: 0 | 30 | 20.00% | 60.00% | 15.00% | 3.00% | 1.00% | 0.50% | 0.50%
Row 13: 0 | 60 | 10.00% | 15.00% | 50.00% | 20.00% | 3.00% | 1.00% | 1.00%
...
Row 20: 1 | C | 96.00% | 2.50% | 0.80% | 0.40% | 0.20% | 0.05% | 0.05%
Row 21: 1 | 30 | 25.00% | 55.00% | 15.00% | 3.00% | 1.00% | 0.50% | 0.50%
...
```

---

## 📝 Viết Công Thức Excel

### Ví Dụ 1: Forecast Balance từ Current

**Giả sử**:
- Current balance ở row 3, columns C-I (C=col 3, 30=col 4, ...)
- Transition matrix MOB 12 ở rows 100-106
- Muốn forecast balance cho MOB 13

**Công thức** (ở row 200):

```excel
# Balance forecast cho bucket C (col 3) tại MOB 13
=C3*C100 + D3*C101 + E3*C102 + F3*C103 + G3*C104 + H3*C105 + I3*C106

# Balance forecast cho bucket 30 (col 4) tại MOB 13
=C3*D100 + D3*D101 + E3*D102 + F3*D103 + G3*D104 + H3*D105 + I3*D106

# Tương tự cho các buckets khác...
```

**Hoặc dùng SUMPRODUCT**:

```excel
# Balance forecast cho bucket C
=SUMPRODUCT($C3:$I3, C100:I100)

# Balance forecast cho bucket 30
=SUMPRODUCT($C3:$I3, C101:I101)
```

### Ví Dụ 2: Forecast Multi-Step

**Forecast từ MOB 12 → MOB 13 → MOB 14**:

```excel
# Step 1: MOB 12 → MOB 13 (ở row 200)
C200: =SUMPRODUCT($C3:$I3, C100:I100)  # Bucket C
D200: =SUMPRODUCT($C3:$I3, C101:I101)  # Bucket 30
... (tương tự cho các buckets khác)

# Step 2: MOB 13 → MOB 14 (ở row 201)
C201: =SUMPRODUCT($C200:$I200, C110:I110)  # Bucket C (dùng TM của MOB 13)
D201: =SUMPRODUCT($C200:$I200, C111:I111)  # Bucket 30
... (tương tự)
```

---

## 🎯 Lợi Ích Layout Ngang

### 1. Dễ Viết Công Thức
- Tất cả buckets nằm trên 1 dòng
- Dùng SUMPRODUCT dễ dàng
- Copy công thức xuống dưới để forecast nhiều steps

### 2. Dễ Đọc
- Nhìn ngang thấy ngay balance/loans theo buckets
- Transition matrix rõ ràng: from bucket → to buckets

### 3. Dễ Kiểm Tra
- Sum ngang để check total
- So sánh giữa các MOBs dễ dàng

### 4. Dễ Mở Rộng
- Thêm forecast steps chỉ cần copy công thức
- Thêm scenarios dễ dàng

---

## 📊 So Sánh V1 vs V2

| Feature | V1 (Vertical) | V2 (Horizontal) ⭐ |
|---------|---------------|-------------------|
| Current balance | Nhiều rows | 1 row (row 3) |
| Transition matrix | Nhiều sheets | 1 sheet, từ row 10 |
| Viết công thức | Khó | Dễ (SUMPRODUCT) |
| Đọc data | Khó | Dễ |
| Forecast steps | Phức tạp | Đơn giản (copy down) |

---

## 🚀 Cách Sử Dụng

### 1. Export Data

Chạy code trong notebook:
```python
# Code đã được update trong cell 18
# Chỉ cần run cell đó
```

### 2. Mở Excel File

File: `cohort_details/Cohort_Forecast_Details_v2_YYYYMMDD_HHMMSS.xlsx`

### 3. Chọn Sheet Cohort

Mỗi sheet = 1 cohort (Product_Score_Vintage)

### 4. Viết Công Thức Forecast

**Bước 1**: Tìm current balance (row 3)  
**Bước 2**: Tìm transition matrix cho MOB tiếp theo (từ row 10)  
**Bước 3**: Viết công thức SUMPRODUCT  
**Bước 4**: Copy xuống để forecast nhiều steps

---

## 💡 Tips

### Tip 1: Freeze Panes
- Freeze đã được set tại row 10, column B
- Scroll xuống vẫn thấy headers
- Scroll sang phải vẫn thấy MOB và From Bucket

### Tip 2: Named Ranges
Tạo named ranges để công thức dễ đọc:
```excel
CurrentBalance = $C$3:$I$3
TM_MOB12_C = $C$100:$I$100
TM_MOB12_30 = $C$101:$I$101
```

Công thức trở thành:
```excel
=SUMPRODUCT(CurrentBalance, TM_MOB12_C)
```

### Tip 3: Data Validation
Thêm dropdown để chọn MOB:
```excel
MOB_List = 0, 1, 2, ..., 36
```

### Tip 4: Conditional Formatting
Highlight cells theo giá trị:
- Balance > threshold → màu đỏ
- Probability < 50% → màu vàng

---

## 📝 Template Công Thức

### Template 1: Forecast 1 Step

```excel
# Ở row 200 (forecast MOB 13 từ MOB 12)
# Giả sử current balance ở row 3, TM MOB 12 bắt đầu từ row 100

C200: =SUMPRODUCT($C$3:$I$3, C100:I100)
D200: =SUMPRODUCT($C$3:$I$3, C101:I101)
E200: =SUMPRODUCT($C$3:$I$3, C102:I102)
F200: =SUMPRODUCT($C$3:$I$3, C103:I103)
G200: =SUMPRODUCT($C$3:$I$3, C104:I104)
H200: =SUMPRODUCT($C$3:$I$3, C105:I105)
I200: =SUMPRODUCT($C$3:$I$3, C106:I106)
J200: =SUM(C200:I200)  # Total
```

### Template 2: Forecast Multi-Steps

```excel
# Row 200: MOB 12 → 13
C200: =SUMPRODUCT($C$3:$I$3, C100:I100)
...

# Row 201: MOB 13 → 14 (dùng TM của MOB 13, giả sử bắt đầu từ row 110)
C201: =SUMPRODUCT($C200:$I200, C110:I110)
...

# Row 202: MOB 14 → 15 (dùng TM của MOB 14, giả sử bắt đầu từ row 120)
C202: =SUMPRODUCT($C201:$I201, C120:I120)
...

# Copy pattern xuống để forecast đến target MOB
```

---

## ✅ Checklist

Khi viết công thức:
- [ ] Đã xác định current balance row (row 3)
- [ ] Đã tìm transition matrix rows (từ row 10)
- [ ] Đã check MOB đúng
- [ ] Đã check from/to buckets đúng
- [ ] Công thức SUMPRODUCT đúng range
- [ ] Total = sum của các buckets
- [ ] Copy công thức đúng (absolute/relative refs)

---

## 🎉 Kết Luận

**V2 Layout** giúp bạn:
- ✅ Viết công thức Excel dễ dàng
- ✅ Forecast nhanh chóng
- ✅ Kiểm tra kết quả dễ dàng
- ✅ Mở rộng scenarios linh hoạt

**Sẵn sàng để gửi cho sếp!** 🚀

