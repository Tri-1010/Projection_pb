# RR_Model_v3 — Roll Rate / Markov Chain (Full Package)

**Ngôn ngữ / Languages:** [Tiếng Việt](#tiếng-việt) | [English](#english)

---

## Tiếng Việt

### 🎯 Mục tiêu
Bộ công cụ mô hình **Roll Rate / Markov Chain** để:
- Tính ma trận chuyển trạng thái DPD (theo số hợp đồng & số dư)
- Dự báo phân phối rủi ro 12-36 tháng tới cho từng *subproduct*
- Calibration: điều chỉnh dự báo sát với thực tế
- Allocation: phân bổ forecast xuống loan-level
- Backtest: kiểm định ổn định ma trận & roll-forward validation
- Xuất báo cáo Excel theo *subproduct* và sheet Summary cho toàn danh mục

### 🗂️ Cấu trúc
```
RR_Model_v3/
├── README.md
├── src/
│   ├── config.py              # ⭐ Cấu hình chính (SEGMENT_COLS, CFG, ...)
│   ├── db.py
│   ├── data_loader.py
│   └── rollrate/
│        ├── transition.py     # Ma trận chuyển trạng thái
│        ├── lifecycle.py      # Build lifecycle actual + forecast
│        ├── calibration_kmob.py  # Calibration per MOB (WLS)
│        ├── allocation_v2_fast.py  # ⭐ Phân bổ xuống loan-level
│        ├── allocation_multi_mob.py
│        └── ...
├── notebooks/
│   ├── Final_Workflow.ipynb   # ⭐ Notebook gọn nhẹ (khuyên dùng)
│   └── Complete_Workflow.ipynb  # Notebook đầy đủ với visualization
└── docs/
    └── MOB_SELECTION_GUIDE.md
```

### ⚙️ Cấu hình (`src/config.py`)

```python
# === SEGMENTATION CONFIG ===
# Thay đổi SEGMENT_COLS để thêm/bớt segment dimensions
# Code sử dụng 2 cột cố định: PRODUCT_TYPE và RISK_SCORE
# - PRODUCT_TYPE: giữ nguyên từ data
# - RISK_SCORE: tự động tạo từ các cột trong SEGMENT_COLS (trừ PRODUCT_TYPE)
#
# Ví dụ:
# - SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE"] => giữ nguyên RISK_SCORE từ data
# - SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE", "GENDER"] => RISK_SCORE = "RISK_SCORE_GENDER"
# - SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE", "GENDER", "LA_GROUP"] => RISK_SCORE = "RISK_SCORE_GENDER_LA_GROUP"
SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE"]

# Hàm tạo segment columns
from src.config import create_segment_columns
df_raw = create_segment_columns(df_raw)  # Tự động tạo RISK_SCORE từ SEGMENT_COLS
```

### 🚀 Cách chạy nhanh

1. Cài đặt thư viện:
   ```bash
   pip install pandas numpy matplotlib seaborn openpyxl xlsxwriter cvxpy
   ```

2. Đặt file parquet vào thư mục data

3. Mở notebook:
   ```bash
   jupyter notebook notebooks/Final_Workflow.ipynb
   ```

4. Cấu hình trong notebook:
   ```python
   DATA_PATH = 'path/to/your/parquet'  # Thay đổi path
   MAX_MOB = 36  # Forecast đến MOB nào
   TARGET_MOBS = [12, 24]  # Allocate tại MOB nào
   ```

5. Chạy từng cell → outputs sẽ được tạo tại `./outputs/`

### 🧩 Thành phần chính

| Module | Chức năng |
|--------|-----------|
| `config.py` | Cấu hình chính: SEGMENT_COLS, CFG, parse_date, create_segment_columns |
| `transition.py` | Tính ma trận Markov (contract/amount) |
| `lifecycle.py` | Build lifecycle actual + forecast, add DEL metrics |
| `calibration_kmob.py` | Calibration per MOB với WLS method |
| `allocation_v2_fast.py` | Phân bổ forecast xuống loan-level (fast) |
| `data_loader.py` | Load data từ Parquet/Oracle |

### 📊 Output

1. **Lifecycle Excel**: Forecast theo cohort với heatmap actual/forecast
2. **Loan Forecast Excel**: Chi tiết từng hợp đồng với STATE_FORECAST, EAD_FORECAST, DEL flags

### 📚 Tài liệu

- `guide.md`: Hướng dẫn chi tiết về Calibration
- `docs/MOB_SELECTION_GUIDE.md`: Hướng dẫn chọn MOB cho allocation

---

## English

### 🎯 Purpose
A **Roll Rate / Markov Chain** toolkit to:
- Estimate DPD transition matrices (by contract & amount)
- Forecast 12-36 month risk distribution by subproduct
- Calibration: adjust forecast to match actual
- Allocation: allocate forecast to loan-level
- Backtest: matrix stability & roll‑forward validation
- Export Excel reports per subproduct + portfolio Summary sheet

### 🚀 Quickstart

1. Install deps:
   ```bash
   pip install pandas numpy matplotlib seaborn openpyxl xlsxwriter cvxpy
   ```

2. Open the notebook:
   ```bash
   jupyter notebook notebooks/Final_Workflow.ipynb
   ```

3. Configure:
   ```python
   DATA_PATH = 'path/to/your/parquet'
   MAX_MOB = 36
   TARGET_MOBS = [12, 24]
   ```

4. Run cells → outputs land in `./outputs/`

### ⚙️ Dynamic Segmentation

```python
# In src/config.py
SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE"]  # Default

# To add more segments:
SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE", "GENDER", "LA_GROUP"]
# => RISK_SCORE will be auto-generated as "RISK_SCORE_GENDER_LA_GROUP"

# In notebook:
from src.config import create_segment_columns
df_raw = create_segment_columns(df_raw)
```
