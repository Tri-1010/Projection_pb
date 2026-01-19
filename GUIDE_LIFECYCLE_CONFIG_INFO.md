# Hướng Dẫn: Lifecycle_All_Products với Config Info Sheet

## 📋 Tổng Quan

File `Lifecycle_All_Products.xlsx` đã được nâng cấp với sheet **Config_Info** chứa đầy đủ thông tin cấu hình và metadata để có thể tái tạo lại kết quả.

## 🎯 Mục Đích

Sheet **Config_Info** giúp bạn:
- ✅ Lưu trữ đầy đủ thông số cấu hình model
- ✅ Ghi nhận thông tin tổng quan về dữ liệu đầu vào
- ✅ Theo dõi metadata quan trọng để audit và validation
- ✅ Dễ dàng tái tạo lại kết quả với cùng cấu hình

## 📊 Nội Dung Config_Info Sheet

### 1. Model Configuration
Chứa các thông số cấu hình model:
- **Data Path**: Đường dẫn đến dữ liệu nguồn
- **Max MOB**: MOB tối đa được forecast
- **Target MOBs**: Các MOB được chọn để allocate
- **Segment Columns**: Các cột dùng để phân nhóm (segmentation)
- **Min Observations**: Số quan sát tối thiểu
- **Min EAD**: Tổng dư nợ tối thiểu
- **Weight Method**: Phương pháp tính trọng số (exp, linear, uniform)
- **Roll Window**: Cửa sổ rolling cho transition matrix
- **Decay Lambda**: Hệ số decay cho exponential weighting

### 2. Input Data Summary
Thông tin tổng quan về dữ liệu đầu vào:
- **Total Rows**: Tổng số dòng dữ liệu
- **Total Loans**: Tổng số hợp đồng
- **Products**: Danh sách sản phẩm
- **Cutoff Date Range**: Khoảng thời gian cutoff
- **Disbursal Date Range**: Khoảng thời gian giải ngân
- **Total EAD**: Tổng dư nợ
- **Total Disbursement**: Tổng giải ngân
- **Risk Score Groups**: Số lượng nhóm risk score

### 3. Output Summary
Thông tin về kết quả output:
- **Total Cohorts**: Tổng số cohort
- **Vintage Range**: Khoảng thời gian vintage
- **Max MOB in Output**: MOB tối đa trong output
- **Actual Data Points**: Số điểm dữ liệu actual
- **Forecast Data Points**: Số điểm dữ liệu forecast

## 🔧 Cách Sử Dụng

### Trong Final_Workflow.ipynb

Code đã được cập nhật tự động:

```python
# Chuẩn bị config params
config_params = {
    "DATA_PATH": DATA_PATH,
    "MAX_MOB": MAX_MOB,
    "TARGET_MOBS": TARGET_MOBS,
    "SEGMENT_COLS": SEGMENT_COLS,
    "MIN_OBS": CFG.get("MIN_OBS", 100),
    "MIN_EAD": CFG.get("MIN_EAD", 100),
    "WEIGHT_METHOD": CFG.get("WEIGHT_METHOD", "exp"),
    "ROLL_WINDOW": CFG.get("ROLL_WINDOW", 20),
    "DECAY_LAMBDA": CFG.get("DECAY_LAMBDA", 0.97),
}

# Export với Config Info
lifecycle_file = output_dir / f"Lifecycle_All_Products_{timestamp}.xlsx"
export_lifecycle_with_config_info(
    df_del_all, 
    actual_info_all, 
    df_raw,
    config_params,
    str(lifecycle_file)
)
```

### Sử Dụng Trực Tiếp

```python
from src.rollrate.lifecycle_export_enhanced import export_lifecycle_with_config_info

config_params = {
    'DATA_PATH': 'path/to/data',
    'MAX_MOB': 13,
    'TARGET_MOBS': [12],
    'SEGMENT_COLS': ['PRODUCT_TYPE', 'RISK_SCORE'],
    # ... các params khác
}

export_lifecycle_with_config_info(
    df_del_prod=df_lifecycle,
    actual_info=actual_info_dict,
    df_raw=df_raw_data,
    config_params=config_params,
    filename="Lifecycle_All_Products.xlsx"
)
```

## 📁 Cấu Trúc File Output

```
Lifecycle_All_Products_YYYYMMDD_HHMMSS.xlsx
├── Config_Info          ← Sheet mới: Thông tin cấu hình
├── Portfolio_DEL30      ← (nếu có)
├── Portfolio_DEL60
├── Portfolio_DEL90
├── C_DEL30             ← Product C
├── C_DEL60
├── C_DEL90
├── S_DEL30             ← Product S
├── S_DEL60
├── S_DEL90
└── ...
```

## 🎨 Format và Styling

Sheet **Config_Info** có format đẹp mắt:
- ✅ Header màu xanh đậm với icon
- ✅ Parameter names có background màu xanh nhạt
- ✅ Timestamp ở đầu sheet
- ✅ Note hướng dẫn ở cuối sheet
- ✅ Auto-sized columns
- ✅ No gridlines

## 🔍 Use Cases

### 1. Audit và Validation
Khi cần kiểm tra lại kết quả, mở sheet Config_Info để xem:
- Dữ liệu nguồn nào được sử dụng?
- Thông số model là gì?
- Khoảng thời gian dữ liệu?

### 2. Tái Tạo Kết Quả
Nếu cần chạy lại với cùng cấu hình:
1. Mở sheet Config_Info
2. Copy các thông số
3. Set lại trong notebook
4. Chạy lại workflow

### 3. So Sánh Các Runs
So sánh Config_Info của nhiều file để thấy sự khác biệt:
- Thay đổi về data range
- Thay đổi về thông số model
- Thay đổi về segmentation

### 4. Documentation
Gửi file cho stakeholders với đầy đủ context:
- Không cần giải thích thêm về cấu hình
- Tất cả thông tin đã có trong file
- Dễ dàng review và approve

## 📝 Lưu Ý

1. **Timestamp**: Mỗi lần export sẽ có timestamp riêng trong filename và trong sheet
2. **Sheet Order**: Config_Info luôn ở vị trí đầu tiên, Portfolio sheets ở vị trí thứ hai
3. **Backward Compatible**: Các sheet Product × Metric vẫn giữ nguyên format cũ
4. **Performance**: Việc thêm Config_Info sheet không ảnh hưởng đến performance

## 🚀 Nâng Cấp So Với Phiên Bản Cũ

| Feature | Phiên Bản Cũ | Phiên Bản Mới |
|---------|--------------|---------------|
| Config Info | ❌ Không có | ✅ Sheet riêng |
| Metadata | ❌ Không có | ✅ Đầy đủ |
| Data Summary | ❌ Không có | ✅ Tự động tính |
| Reproducibility | ⚠️ Khó | ✅ Dễ dàng |
| Audit Trail | ⚠️ Thiếu | ✅ Đầy đủ |

## 🔗 Files Liên Quan

- `src/rollrate/lifecycle_export_enhanced.py`: Function export mới
- `notebooks/Final_Workflow.ipynb`: Notebook đã được cập nhật
- `test_enhanced_export.py`: Script test function

## ❓ FAQ

**Q: Config_Info sheet có bắt buộc không?**
A: Không, bạn vẫn có thể dùng function cũ `export_lifecycle_all_products_one_file` nếu không cần Config_Info.

**Q: Có thể customize nội dung Config_Info không?**
A: Có, bạn có thể thêm/bớt parameters trong `config_params` dict.

**Q: File có nặng hơn không?**
A: Không đáng kể, Config_Info sheet chỉ thêm vài KB.

**Q: Có thể export Config_Info riêng không?**
A: Hiện tại chưa, nhưng bạn có thể copy sheet này sang file khác.

## 📞 Support

Nếu có vấn đề hoặc câu hỏi, vui lòng:
1. Kiểm tra file test: `python test_enhanced_export.py`
2. Xem log output để debug
3. Kiểm tra config_params có đầy đủ không

---

**Version**: 1.0  
**Last Updated**: 2026-01-17  
**Author**: Kiro AI Assistant
