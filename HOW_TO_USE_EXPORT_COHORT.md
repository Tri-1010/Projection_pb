# Cách Sử Dụng Export Cohort Details

## ✅ Đã Hoàn Thành

Cell export đã được thêm vào notebook **Final_Workflow copy.ipynb**!

---

## 🚀 Cách Chạy

### Bước 1: Mở notebook

```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

### Bước 2: Chạy tất cả cells từ đầu đến cuối

Click: **Cell → Run All**

Hoặc chạy từng cell cho đến cell cuối cùng (cell mới thêm).

### Bước 3: Xem kết quả

Cell cuối cùng sẽ:
1. ✅ Verify cohorts có tồn tại không
2. ✅ Export file Excel chi tiết
3. ✅ Show preview kết quả

---

## 📝 Tùy Chỉnh Cohorts

Mở cell cuối cùng và sửa danh sách cohorts:

```python
# Mặc định (đã có trong cell)
cohorts = [
    ('C', 'A_F_40M+_None', '2025-10-01'),
    ('C', 'B_F_40M+_None', '2025-10-01'),
    ('C', 'A_F_40M+_None', '2024-10-01'),
    ('C', 'B_F_40M+_None', '2024-10-01'),
    ('S', 'A_F_40M+_None', '2025-10-01'),
    ('S', 'B_F_40M+_None', '2025-10-01'),
]
```

### Cách tìm RISK_SCORE đúng

Chạy cell này để xem các RISK_SCORE có sẵn:

```python
# Xem unique RISK_SCORE
print("Available RISK_SCORE:")
print(df_raw['RISK_SCORE'].unique()[:20])  # Show 20 đầu tiên

# Xem theo Product
for product in df_raw['PRODUCT_TYPE'].unique():
    print(f"\nProduct {product}:")
    scores = df_raw[df_raw['PRODUCT_TYPE'] == product]['RISK_SCORE'].unique()
    print(f"  {len(scores)} risk scores")
    print(f"  Examples: {scores[:5].tolist()}")
```

### Cách tìm Vintage Date đúng

```python
# Xem các vintages gần đây
recent_vintages = df_raw.groupby('VINTAGE_DATE')['AGREEMENT_ID'].nunique().sort_index(ascending=False).head(10)
print("Recent vintages:")
print(recent_vintages)
```

### Ví dụ tùy chỉnh

```python
# Chỉ export 2 cohorts
cohorts = [
    ('C', 'A_F_40M+_None', '2025-10-01'),
    ('S', 'B_M_25M-_None', '2024-10-01'),
]

# Export nhiều cohorts cùng product
cohorts = [
    ('C', 'A_F_40M+_None', '2025-10-01'),
    ('C', 'A_F_40M+_None', '2025-09-01'),
    ('C', 'A_F_40M+_None', '2025-08-01'),
]

# Export nhiều risk scores
cohorts = [
    ('C', 'A_F_40M+_None', '2025-10-01'),
    ('C', 'B_F_40M+_None', '2025-10-01'),
    ('C', 'C_F_40M+_None', '2025-10-01'),
    ('C', 'D_F_40M+_None', '2025-10-01'),
]
```

---

## 📊 Output

### File Location

```
cohort_details/Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx
```

### Sheets trong file

1. **Summary** - Tổng quan cohorts
   - N loans, Disbursement, Current MOB, Target MOB

2. **TM_[Product]_[Score]** - Transition matrices
   - Tất cả matrices từ MOB 0 đến target_mob

3. **K_Values** - K và Alpha values
   - K_Raw, K_Smooth, Alpha theo MOB

4. **Actual_[Product]_[Score]** - Dữ liệu thực tế
   - EAD theo state và MOB

5. **Forecast_Steps** - Chi tiết tính toán
   - Từng bước forecast từ current_mob đến target_mob
   - **Dòng cuối cùng = Kết quả cuối cùng!**

6. **Instructions** - Hướng dẫn đọc file

---

## 🎯 Gửi Cho Sếp

File Excel chứa đầy đủ:
- ✅ Dữ liệu thực tế
- ✅ Transition matrices
- ✅ K values
- ✅ Chi tiết từng bước tính toán
- ✅ Công thức và hướng dẫn

**Sếp có thể**:
- Xem chi tiết cách tính
- Verify từng bước
- Tự tính lại nếu cần

---

## 🔍 Troubleshooting

### Lỗi: "No data for cohort"

**Nguyên nhân**: RISK_SCORE hoặc Vintage_Date không đúng

**Giải pháp**: Chạy cell để xem available values:

```python
# Check available combinations
df_check = df_raw.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']).size().reset_index(name='count')
df_check = df_check.sort_values('count', ascending=False)
print(df_check.head(20))
```

### Lỗi: "NameError: name 'k_raw_by_mob' is not defined"

**Nguyên nhân**: Chưa chạy cells build model

**Giải pháp**: Chạy lại tất cả cells từ đầu (Cell → Run All)

### Lỗi: "ModuleNotFoundError: No module named 'export_cohort_details'"

**Nguyên nhân**: File export_cohort_details.py không ở đúng vị trí

**Giải pháp**: Đảm bảo file `export_cohort_details.py` ở thư mục gốc project

---

## 💡 Tips

### 1. Chọn cohorts có volume lớn

```python
# Tìm cohorts có nhiều loans nhất
top_cohorts = df_raw.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE'])['AGREEMENT_ID'].nunique()
top_cohorts = top_cohorts.sort_values(ascending=False).head(10)
print(top_cohorts)
```

### 2. Chọn cohorts gần đây

```python
# Lấy vintages trong 6 tháng gần đây
recent_date = df_raw['VINTAGE_DATE'].max()
six_months_ago = recent_date - pd.DateOffset(months=6)

df_recent = df_raw[df_raw['VINTAGE_DATE'] >= six_months_ago]
recent_cohorts = df_recent.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE'])['AGREEMENT_ID'].nunique()
print(recent_cohorts.sort_values(ascending=False).head(10))
```

### 3. Export theo từng Product

```python
# Product C only
cohorts_c = [
    ('C', score, '2025-10-01')
    for score in df_raw[df_raw['PRODUCT_TYPE'] == 'C']['RISK_SCORE'].unique()[:5]
]

# Product S only
cohorts_s = [
    ('S', score, '2025-10-01')
    for score in df_raw[df_raw['PRODUCT_TYPE'] == 'S']['RISK_SCORE'].unique()[:5]
]
```

---

## 📚 Files Liên Quan

- `export_cohort_details.py` - Main function
- `GUIDE_EXPORT_COHORT_DETAILS.md` - Hướng dẫn chi tiết
- `QUICK_START_EXPORT_COHORT.md` - Quick start guide
- `add_export_cell_to_notebook.py` - Script đã dùng để add cell

---

**Date**: 2026-01-18  
**Status**: ✅ Ready to use  
**Notebook**: Final_Workflow copy.ipynb (18 cells)
