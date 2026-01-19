# Troubleshooting: Import Error

## ❌ Lỗi Gặp Phải

```
ImportError: cannot import name 'export_lifecycle_with_config_info'
```

## ✅ Đã Sửa

Lỗi này xảy ra do import bị trùng lặp và sai vị trí trong notebook. Đã được sửa bằng script `fix_import_final_workflow.py`.

## 🔍 Nguyên Nhân

Script `update_final_workflow.py` đã thêm import nhưng:
1. ❌ Thêm vào sai vị trí (trong block import từ `src.rollrate.lifecycle`)
2. ❌ Import trùng lặp (2 lần)
3. ❌ Import từ module không có function này

## ✅ Giải Pháp

### Cách 1: Chạy Script Fix (Đã Làm)
```bash
python fix_import_final_workflow.py
```

### Cách 2: Verify Imports
```bash
python verify_notebook_imports.py
```

Nếu thấy:
```
🎉 ALL IMPORTS SUCCESSFUL!
✅ Final_Workflow notebook is ready to run!
```

→ Đã OK!

### Cách 3: Sửa Thủ Công (Nếu Cần)

Mở `notebooks/Final_Workflow.ipynb` và tìm cell import đầu tiên, đảm bảo có dòng này:

```python
from src.rollrate.lifecycle_export_enhanced import export_lifecycle_with_config_info
```

**Vị trí đúng**: Sau các import khác, trước dòng `print("✅ Import thành công")`

**Không được có**: 
- ❌ `export_lifecycle_with_config_info,` trong block `from src.rollrate.lifecycle import (...)`
- ❌ Import trùng lặp

## 📋 Import Cell Đúng

```python
# Setup
import sys
from pathlib import Path
project_root = Path(".").resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime

from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_90P
from src.config import parse_date_column, create_segment_columns, SEGMENT_COLS
from src.data_loader import load_data
from src.rollrate.transition import compute_transition_by_mob
from src.rollrate.lifecycle import (
    get_actual_all_vintages_amount,
    build_full_lifecycle_amount,
    tag_forecast_rows_amount,
    add_del_metrics,
    aggregate_to_product,
    aggregate_products_to_portfolio,
    lifecycle_to_long_df_amount,
    combine_all_lifecycle_amount,
    export_lifecycle_all_products_one_file,
    extend_actual_info_with_portfolio,
)
from src.rollrate.calibration_kmob import (
    fit_k_raw, smooth_k, fit_alpha,
    forecast_all_vintages_partial_step,
)
from src.rollrate.allocation_v2_optimized import allocate_multi_mob_optimized

from src.rollrate.lifecycle_export_enhanced import export_lifecycle_with_config_info

print("✅ Import thành công")
```

## ✅ Kiểm Tra

### Test 1: Import Trực Tiếp
```bash
python -c "from src.rollrate.lifecycle_export_enhanced import export_lifecycle_with_config_info; print('✅ OK')"
```

Kết quả mong đợi:
```
✅ OK
```

### Test 2: Verify All Imports
```bash
python verify_notebook_imports.py
```

Kết quả mong đợi:
```
🎉 ALL IMPORTS SUCCESSFUL!
✅ Final_Workflow notebook is ready to run!
```

### Test 3: Test Function
```bash
python test_enhanced_export.py
```

Kết quả mong đợi:
```
✅ Test successful!
✅ Config_Info sheet found!
```

## 🚀 Chạy Notebook

Sau khi verify imports OK:

```bash
jupyter notebook notebooks/Final_Workflow.ipynb
```

Hoặc trong Jupyter:
1. Kernel → Restart & Run All
2. Chờ chạy xong
3. Kiểm tra file output trong folder `outputs/`
4. Mở file Excel, xem sheet đầu tiên có tên "Config_Info"

## 📝 Checklist

- [x] Chạy `fix_import_final_workflow.py` ✅
- [x] Chạy `verify_notebook_imports.py` ✅
- [x] Test imports thành công ✅
- [ ] Chạy Final_Workflow notebook
- [ ] Kiểm tra file output có Config_Info sheet

## 🔧 Files Liên Quan

- `fix_import_final_workflow.py` - Script fix import
- `verify_notebook_imports.py` - Script verify imports
- `test_enhanced_export.py` - Script test function
- `notebooks/Final_Workflow.ipynb` - Notebook đã fix

## 📞 Nếu Vẫn Lỗi

### Lỗi: Module not found
```
ModuleNotFoundError: No module named 'src.rollrate.lifecycle_export_enhanced'
```

**Giải pháp**:
1. Kiểm tra file tồn tại: `src/rollrate/lifecycle_export_enhanced.py`
2. Kiểm tra đang ở đúng thư mục project root
3. Restart Jupyter kernel

### Lỗi: Function not found
```
ImportError: cannot import name 'export_lifecycle_with_config_info'
```

**Giải pháp**:
1. Kiểm tra function tồn tại trong file
2. Chạy lại: `python verify_notebook_imports.py`
3. Nếu vẫn lỗi, xem file `src/rollrate/lifecycle_export_enhanced.py` có function `export_lifecycle_with_config_info` không

### Lỗi: Syntax error trong notebook
```
SyntaxError: ...
```

**Giải pháp**:
1. Chạy lại: `python fix_import_final_workflow.py`
2. Hoặc sửa thủ công theo mẫu ở trên
3. Restart Jupyter kernel

## ✅ Kết Luận

Lỗi đã được sửa! Notebook sẵn sàng chạy.

**Next steps**:
1. ✅ Imports đã OK
2. ✅ Function đã có
3. ✅ Test đã pass
4. → Chạy Final_Workflow notebook!

---

**Status**: ✅ Resolved  
**Date**: 2026-01-17  
**Fix Script**: `fix_import_final_workflow.py`
