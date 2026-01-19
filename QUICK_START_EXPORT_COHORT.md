# Quick Start: Export Chi Tiết Forecast Cho Sếp

## 🚀 3 Bước Nhanh

### 1. Mở Final_Workflow copy notebook

```bash
jupyter notebook "notebooks/Final_Workflow copy.ipynb"
```

### 2. Chạy đến hết phần build model

Chạy tất cả cells cho đến hết phần:
- ✅ Load data
- ✅ Build transition matrices  
- ✅ Build lifecycle + calibration

### 3. Add cell mới và chạy

```python
# Copy code từ file: notebook_cell_export_cohort_details.py
# Hoặc copy trực tiếp:

from export_cohort_details import export_cohort_forecast_details

# Define cohorts
cohorts = [
    ('X', 'A', '2025-10-01'),
    ('X', 'B', '2024-10-01'),
]

# Export
filename = export_cohort_forecast_details(
    cohorts=cohorts,
    df_raw=df_raw,
    matrices_by_mob=matrices_by_mob,
    k_raw_by_mob=k_raw_by_mob,
    k_smooth_by_mob=k_smooth_by_mob,
    alpha_by_mob=alpha_by_mob,
    target_mob=24,
    output_dir='cohort_details',
)

print(f'✅ File sẵn sàng: {filename}')
```

---

## 📊 Output

File Excel với 6 sheets:

1. **Summary** - Tổng quan cohorts
2. **TM_[Product]_[Score]** - Transition matrices
3. **K_Values** - K raw, K smooth, Alpha
4. **Actual_[Product]_[Score]** - Dữ liệu thực tế
5. **Forecast_Steps** - Chi tiết từng bước tính
6. **Instructions** - Hướng dẫn đọc file

---

## 💡 Ví Dụ Cohorts

### Chọn cohorts gần đây:
```python
cohorts = [
    ('X', 'A', '2025-10-01'),
    ('X', 'B', '2025-10-01'),
    ('T', 'A', '2025-10-01'),
]
```

### Chọn cohorts để so sánh:
```python
cohorts = [
    # Recent
    ('X', 'A', '2025-10-01'),
    # Older (for comparison)
    ('X', 'A', '2024-10-01'),
]
```

### Chọn nhiều risk scores:
```python
cohorts = [
    ('X', 'A', '2025-10-01'),
    ('X', 'B', '2025-10-01'),
    ('X', 'C', '2025-10-01'),
    ('X', 'D', '2025-10-01'),
]
```

---

## 🎯 Gửi Cho Sếp

File Excel chứa:
- ✅ Dữ liệu thực tế
- ✅ Transition matrices
- ✅ K values
- ✅ Chi tiết từng bước tính toán
- ✅ Kết quả cuối cùng
- ✅ Hướng dẫn đọc file

**Sếp có thể**:
- Xem chi tiết cách tính toán
- Verify từng bước
- Hiểu rõ công thức
- Tự tính lại nếu cần

---

## 📝 Files Liên Quan

- `export_cohort_details.py` - Main function
- `GUIDE_EXPORT_COHORT_DETAILS.md` - Hướng dẫn chi tiết
- `notebook_cell_export_cohort_details.py` - Code mẫu cho notebook

---

**Date**: 2026-01-18  
**Ready to use**: ✅
