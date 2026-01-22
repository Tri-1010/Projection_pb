# 📊 Hướng Dẫn Tính Forecast Trong Excel

## Tổng Quan

File Excel export chứa tất cả thông số cần thiết để tính forecast cho mỗi cohort:
- **Current Balance**: Dư nợ hiện tại theo từng bucket
- **K Values**: Hệ số điều chỉnh (K_raw, K_smooth, Alpha)
- **Transition Matrix**: Ma trận chuyển đổi trạng thái

---

## 📋 Cấu Trúc File Excel

Mỗi cohort có layout như sau:

| Row | Nội dung |
|-----|----------|
| 0 | **COHORT HEADER**: Product \| Score \| Vintage |
| 1 | Current MOB + Bucket headers (DPD0, DPD1+, DPD30+, ...) |
| 2 | **Current Balance** theo từng bucket |
| 3 | Number of Loans |
| 4 | (trống) |
| 5 | K Values header + MOB columns |
| 6 | **K_raw** values |
| 7 | **K_smooth** values |
| 8 | **Alpha** values |
| 9 | (trống) |
| 10 | Transition Matrix header |
| 11+ | **TM data** cho từng MOB |

---

## 🧮 Công Thức Tính Forecast

### Bước 1: Hiểu Transition Matrix

Ma trận transition (TM) cho biết xác suất chuyển từ bucket này sang bucket khác trong 1 tháng.

```
Ví dụ TM tại MOB 3:
           DPD0    DPD1+   DPD30+  DPD60+  ...
DPD0       85%     10%     3%      1%      ...
DPD1+      20%     50%     25%     3%      ...
DPD30+     5%      10%     40%     35%     ...
...
```

**Đọc theo hàng**: Từ DPD0, có 85% ở lại DPD0, 10% chuyển sang DPD1+, 3% sang DPD30+...

### Bước 2: Công Thức Forecast 1 Tháng

```
Balance_next = Balance_current × TM × K_smooth
```

**Trong Excel:**

Giả sử:
- Current Balance ở row 2, columns C:I (DPD0 đến DPD180+)
- TM cho MOB hiện tại ở rows 12:18, columns C:I
- K_smooth ở row 7

```excel
=MMULT(C2:I2, C12:I18) * C7
```

### Bước 3: Forecast Nhiều Tháng (Rolling)

Để forecast từ MOB hiện tại đến target MOB:

```
MOB_n+1 = MOB_n × TM(n) × K_smooth(n)
MOB_n+2 = MOB_n+1 × TM(n+1) × K_smooth(n+1)
...
```

---

## 📝 Hướng Dẫn Chi Tiết Trong Excel

### Ví Dụ Cụ Thể

Giả sử cohort có:
- Current MOB = 3
- Target MOB = 24
- Current Balance: DPD0=1,000,000 | DPD1+=200,000 | DPD30+=50,000 | ...

#### Sheet Setup

1. **Tạo bảng Forecast** bên dưới data của cohort:

| Row | A | B | C | D | E | F | G | H | I |
|-----|---|---|---|---|---|---|---|---|---|
| 20 | **Forecast** | MOB | DPD0 | DPD1+ | DPD30+ | DPD60+ | DPD90+ | DPD120+ | DPD180+ |
| 21 | | 3 | =C2 | =D2 | =E2 | =F2 | =G2 | =H2 | =I2 |
| 22 | | 4 | (formula) | ... | ... | ... | ... | ... | ... |
| 23 | | 5 | (formula) | ... | ... | ... | ... | ... | ... |
| ... | | ... | ... | ... | ... | ... | ... | ... | ... |

#### Công Thức Excel Chi Tiết

**Bước 1: Copy Current Balance (Row 21)**
```excel
C21 = C2  (Current DPD0)
D21 = D2  (Current DPD1+)
...
```

**Bước 2: Forecast MOB 4 (Row 22)**

Cần tìm TM cho MOB 3→4 trong data. Giả sử TM MOB 3 ở rows 12:18.

```excel
C22 = SUMPRODUCT($C21:$I21, C12:C18) * INDEX($C$7:$Z$7, 1, B22-$B$21+1)
```

Hoặc đơn giản hơn:
```excel
C22 = (C21*C12 + D21*C13 + E21*C14 + F21*C15 + G21*C16 + H21*C17 + I21*C18) * K_smooth_MOB4
```

**Bước 3: Copy công thức xuống các MOB tiếp theo**

---

## 🎯 Công Thức Đơn Giản Hóa

### Nếu K_smooth ≈ 1 (không điều chỉnh)

```excel
Balance_DPD0_next = Balance_DPD0_current * TM[DPD0→DPD0] 
                  + Balance_DPD1+_current * TM[DPD1+→DPD0]
                  + Balance_DPD30+_current * TM[DPD30+→DPD0]
                  + ...
```

### Công Thức SUMPRODUCT

```excel
=SUMPRODUCT(CurrentBalanceRow, TMColumn_for_target_bucket)
```

---

## 📊 Tính DEL30+ và DEL90+

Sau khi có forecast balance cho từng bucket:

```excel
DEL30+ = DPD30+ + DPD60+ + DPD90+ + DPD120+ + DPD180+ + WRITEOFF
DEL90+ = DPD90+ + DPD120+ + DPD180+ + WRITEOFF
```

**DEL Rate:**
```excel
DEL30+_Rate = DEL30+ / DISB_TOTAL
DEL90+_Rate = DEL90+ / DISB_TOTAL
```

---

## 🔧 Template Excel

### Tạo Sheet "Calculation"

```
| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Cohort | MOB | DPD0 | DPD1+ | DPD30+ | DPD60+ | DPD90+ | DPD120+ | DPD180+ | TOTAL |
| X_A_2025-10 | 3 | 1000000 | 200000 | 50000 | 20000 | 10000 | 5000 | 2000 | =SUM(C2:I2) |
| | 4 | =forecast | ... | ... | ... | ... | ... | ... | =SUM(C3:I3) |
| | 5 | =forecast | ... | ... | ... | ... | ... | ... | =SUM(C4:I4) |
```

---

## ⚠️ Lưu Ý Quan Trọng

1. **TM thay đổi theo MOB**: Mỗi MOB có TM riêng, cần dùng đúng TM cho từng bước forecast

2. **K_smooth điều chỉnh**: K_smooth thường gần 1, nhưng có thể khác nhau theo MOB

3. **Absorbing States**: PREPAY, WRITEOFF, SOLDOUT là trạng thái hấp thụ (không chuyển đi đâu)

4. **Kiểm tra tổng hàng TM = 100%**: Mỗi hàng trong TM phải cộng lại = 1 (100%)

---

## 📈 Ví Dụ Hoàn Chỉnh

### Input:
- Current MOB: 3
- Current Balance: [1,000,000, 200,000, 50,000, 20,000, 10,000, 5,000, 2,000]
- K_smooth(MOB 4): 1.02

### TM MOB 3:
```
        DPD0   DPD1+  DPD30+ DPD60+ DPD90+ DPD120+ DPD180+
DPD0    0.85   0.10   0.03   0.01   0.005  0.003   0.002
DPD1+   0.20   0.50   0.25   0.03   0.01   0.005   0.005
DPD30+  0.05   0.10   0.40   0.35   0.05   0.03    0.02
...
```

### Calculation:
```
DPD0_MOB4 = (1,000,000 × 0.85 + 200,000 × 0.20 + 50,000 × 0.05 + ...) × 1.02
          = (850,000 + 40,000 + 2,500 + ...) × 1.02
          ≈ 910,550
```

---

## 🚀 Quick Start

1. Mở file Excel export
2. Tìm cohort cần tính
3. Copy Current Balance vào sheet mới
4. Áp dụng công thức SUMPRODUCT với TM tương ứng
5. Nhân với K_smooth
6. Lặp lại cho các MOB tiếp theo

---

**Chúc bạn thành công!** 🎉
