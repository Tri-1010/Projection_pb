# 📊 Guide: V3 Full Forecast Layout

**Version**: 3.0 - Layout đầy đủ với K values  
**Date**: 2026-01-19  
**Purpose**: Có đủ thông tin để tính forecast hoàn chỉnh

---

## 🎯 Layout V3 - Đầy Đủ

### Mỗi Sheet (1 Cohort):

```
Row 1:  [Headers] Cohort Info
Row 2:  [Current MOB] | MOB | C | 30 | 60 | 90 | 120 | 150 | CO | TOTAL
Row 3:  [Current Balance] | | $$ | $$ | $$ | $$ | $$ | $$ | $$ | TOTAL
Row 4:  [Number of Loans] | | ## | ## | ## | ## | ## | ## | ## | TOTAL
Row 5:  [Empty]
Row 6:  [K_raw] | MOB → | 12 | 13 | 14 | 15 | ... | 36
Row 7:  [K_raw values] | | 0.95 | 0.94 | 0.93 | ... | 0.85
Row 8:  [K_smooth values] | | 0.96 | 0.95 | 0.94 | ... | 0.86
Row 9:  [Alpha values] | | 0.82 | 0.82 | 0.82 | ... | 0.82
Row 10: [Empty]
Row 11: [TM Headers] MOB | From | To C | To 30 | To 60 | ...
Row 12+: [TM Data] mob | bucket | % | % | % | ...
```

---

## 💡 Công Thức Forecast Đầy Đủ

### Bước 1: Forecast Balance (Chưa Có K)

**Forecast từ MOB 12 → MOB 13** (chưa nhân K):

```excel
# Ở row 200 (forecast balance trước khi nhân K)
# Giả sử: Current balance ở row 3, TM MOB 12 bắt đầu từ row 100

# Bucket C (column C):
C200: =SUMPRODUCT($C$3:$I$3, C100:I100)

# Bucket 30 (column D):
D200: =SUMPRODUCT($C$3:$I$3, C101:I101)

# Bucket 60 (column E):
E200: =SUMPRODUCT($C$3:$I$3, C102:I102)

# ... tương tự cho các buckets khác

# Total:
J200: =SUM(C200:I200)
```

### Bước 2: Nhân Với K (Final Forecast)

**Forecast cuối cùng = Balance × K_smooth** (hoặc K_final):

```excel
# Ở row 201 (forecast cuối cùng sau khi nhân K)
# Giả sử: K_smooth cho MOB 13 ở cell D8 (column D = MOB 13)

# Bucket C:
C201: =C200 * $D$8

# Bucket 30:
D201: =D200 * $D$8

# Bucket 60:
E201: =E200 * $D$8

# ... tương tự cho các buckets khác

# Total:
J201: =SUM(C201:I201)
```

### Bước 3: Forecast Multi-Steps

**Forecast từ MOB 12 → 13 → 14 → ... → 36**:

```excel
# ===== MOB 12 → 13 =====
# Row 200: Balance trước K
C200: =SUMPRODUCT($C$3:$I$3, C100:I100)
D200: =SUMPRODUCT($C$3:$I$3, C101:I101)
...

# Row 201: Balance sau K (MOB 13)
C201: =C200 * $D$8  # D8 = K_smooth cho MOB 13
D201: =D200 * $D$8
...

# ===== MOB 13 → 14 =====
# Row 202: Balance trước K (dùng TM MOB 13, giả sử từ row 110)
C202: =SUMPRODUCT($C201:$I201, C110:I110)
D202: =SUMPRODUCT($C201:$I201, C111:I111)
...

# Row 203: Balance sau K (MOB 14)
C203: =C202 * $E$8  # E8 = K_smooth cho MOB 14
D203: =D202 * $E$8
...

# ===== MOB 14 → 15 =====
# Row 204: Balance trước K
C204: =SUMPRODUCT($C203:$I203, C120:I120)
...

# Row 205: Balance sau K (MOB 15)
C205: =C204 * $F$8  # F8 = K_smooth cho MOB 15
...

# Tiếp tục pattern cho đến target MOB
```

---

## 🎯 Công Thức Tổng Quát

### Template Forecast 1 Step:

```excel
# Step N: MOB m → m+1

# Row X: Balance trước K
C[X]: =SUMPRODUCT($C[prev]:$I[prev], C[TM_start]:I[TM_start])
D[X]: =SUMPRODUCT($C[prev]:$I[prev], C[TM_start+1]:I[TM_start+1])
E[X]: =SUMPRODUCT($C[prev]:$I[prev], C[TM_start+2]:I[TM_start+2])
F[X]: =SUMPRODUCT($C[prev]:$I[prev], C[TM_start+3]:I[TM_start+3])
G[X]: =SUMPRODUCT($C[prev]:$I[prev], C[TM_start+4]:I[TM_start+4])
H[X]: =SUMPRODUCT($C[prev]:$I[prev], C[TM_start+5]:I[TM_start+5])
I[X]: =SUMPRODUCT($C[prev]:$I[prev], C[TM_start+6]:I[TM_start+6])
J[X]: =SUM(C[X]:I[X])

# Row X+1: Balance sau K
C[X+1]: =C[X] * $[K_col]$8
D[X+1]: =D[X] * $[K_col]$8
E[X+1]: =E[X] * $[K_col]$8
F[X+1]: =F[X] * $[K_col]$8
G[X+1]: =G[X] * $[K_col]$8
H[X+1]: =H[X] * $[K_col]$8
I[X+1]: =I[X] * $[K_col]$8
J[X+1]: =SUM(C[X+1]:I[X+1])

# Trong đó:
# [prev] = row của balance trước đó (row 3 cho step đầu, hoặc row X-1 cho steps sau)
# [TM_start] = row bắt đầu của TM cho MOB hiện tại
# [K_col] = column của K cho MOB tiếp theo (D cho MOB 13, E cho MOB 14, ...)
```

---

## 📝 Ví Dụ Cụ Thể

### Scenario: Forecast từ MOB 12 → 36

**Giả sử**:
- Current MOB: 12 (row 2, cell B2)
- Current balance: row 3, columns C:I
- K_smooth: row 8, columns C:Z (C=MOB 12, D=MOB 13, ...)
- TM MOB 12: rows 100-106
- TM MOB 13: rows 110-116
- TM MOB 14: rows 120-126
- ... (mỗi MOB cách nhau 10 rows)

**Công thức**:

```excel
# ===== MOB 12 → 13 =====
# Row 200: Balance trước K
C200: =SUMPRODUCT($C$3:$I$3, C100:I100)
D200: =SUMPRODUCT($C$3:$I$3, C101:I101)
E200: =SUMPRODUCT($C$3:$I$3, C102:I102)
F200: =SUMPRODUCT($C$3:$I$3, C103:I103)
G200: =SUMPRODUCT($C$3:$I$3, C104:I104)
H200: =SUMPRODUCT($C$3:$I$3, C105:I105)
I200: =SUMPRODUCT($C$3:$I$3, C106:I106)
J200: =SUM(C200:I200)

# Row 201: Balance sau K (MOB 13)
C201: =C200*$D$8
D201: =D200*$D$8
E201: =E200*$D$8
F201: =F200*$D$8
G201: =G200*$D$8
H201: =H200*$D$8
I201: =I200*$D$8
J201: =SUM(C201:I201)

# ===== MOB 13 → 14 =====
# Row 202: Balance trước K
C202: =SUMPRODUCT($C201:$I201, C110:I110)
D202: =SUMPRODUCT($C201:$I201, C111:I111)
E202: =SUMPRODUCT($C201:$I201, C112:I112)
F202: =SUMPRODUCT($C201:$I201, C113:I113)
G202: =SUMPRODUCT($C201:$I201, C114:I114)
H202: =SUMPRODUCT($C201:$I201, C115:I115)
I202: =SUMPRODUCT($C201:$I201, C116:I116)
J202: =SUM(C202:I202)

# Row 203: Balance sau K (MOB 14)
C203: =C202*$E$8
D203: =D202*$E$8
E203: =E202*$E$8
F203: =F202*$E$8
G203: =G202*$E$8
H203: =H202*$E$8
I203: =I202*$E$8
J203: =SUM(C203:I203)

# Tiếp tục pattern...
```

---

## 🔧 Tips & Tricks

### Tip 1: Named Ranges

Tạo named ranges để công thức dễ đọc:

```excel
CurrentBalance = $C$3:$I$3
K_Smooth_Row = $C$8:$Z$8
TM_MOB12_C = $C$100:$I$100
TM_MOB12_30 = $C$101:$I$101
```

Công thức trở thành:

```excel
C200: =SUMPRODUCT(CurrentBalance, TM_MOB12_C)
C201: =C200 * INDEX(K_Smooth_Row, 1, 2)  # Column 2 = MOB 13
```

### Tip 2: Dynamic K Lookup

Dùng INDEX để lookup K động:

```excel
# Giả sử MOB hiện tại ở cell A200
# K_smooth cho MOB tiếp theo:
=INDEX($C$8:$Z$8, 1, A200-11)  # 11 = offset (nếu column C = MOB 12)
```

### Tip 3: Macro để Generate Công Thức

Viết VBA macro để tự động generate công thức cho tất cả steps:

```vba
Sub GenerateForecast()
    Dim startRow As Long
    Dim currentMOB As Long
    Dim targetMOB As Long
    Dim step As Long
    
    startRow = 200
    currentMOB = Range("B2").Value  ' Current MOB
    targetMOB = 36
    
    For step = 0 To (targetMOB - currentMOB - 1)
        ' Generate formulas for this step
        ' ...
    Next step
End Sub
```

### Tip 4: Validation

Thêm validation để check:

```excel
# Check: Total balance không âm
=IF(J201<0, "ERROR: Negative balance", "OK")

# Check: K trong khoảng hợp lý (0.5 - 1.0)
=IF(OR(D8<0.5, D8>1), "WARNING: K out of range", "OK")

# Check: TM sum = 100%
=IF(ABS(SUM(C100:I100)-1)>0.01, "ERROR: TM not sum to 100%", "OK")
```

---

## 📊 So Sánh Các Versions

| Feature | V1 | V2 | V3 ⭐ |
|---------|----|----|------|
| Current balance | ✅ | ✅ | ✅ |
| Transition matrices | ✅ | ✅ | ✅ |
| K values | ❌ | ❌ | ✅ |
| Layout ngang | ❌ | ✅ | ✅ |
| Forecast đầy đủ | ❌ | ⚠️ | ✅ |

**V3 = Complete solution!** 🎉

---

## ✅ Checklist Viết Công Thức

Khi viết công thức forecast:

- [ ] Đã xác định current balance row (row 3)
- [ ] Đã xác định K_smooth row (row 8)
- [ ] Đã tìm TM rows cho từng MOB
- [ ] Đã viết công thức balance trước K
- [ ] Đã viết công thức balance sau K
- [ ] Đã check K column đúng cho từng MOB
- [ ] Đã validate: total = sum của buckets
- [ ] Đã validate: balance không âm
- [ ] Đã validate: K trong khoảng hợp lý

---

## 🎯 Kết Luận

**V3 Layout** cung cấp:
- ✅ Current balance (row 3)
- ✅ K values (rows 6-9)
- ✅ Transition matrices (row 11+)
- ✅ Tất cả thông tin để forecast đầy đủ

**Công thức forecast**:
1. Balance trước K = SUMPRODUCT(previous_balance, TM)
2. Balance sau K = Balance trước K × K_smooth
3. Repeat cho đến target MOB

**Sẵn sàng để tính forecast chính xác!** 🚀

