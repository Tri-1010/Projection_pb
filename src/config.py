from pathlib import Path
import pandas as pd


# ===== Resolve project root from this file path (stable across notebooks/scripts) =====
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../RR_model
OUT_ROOT     = PROJECT_ROOT / "outputs"

# Data source defaults to parquet for offline runs
DATA_SOURCE  = "parquet"  # options: "parquet" | "oracle"
PARQUET_DIR  = PROJECT_ROOT / "data" / "parquet"       # <-- FIXED: absolute path
PARQUET_FILE = None  # or "rollrate_base.parquet" if bạn dùng 1 file duy nhất

EXCEL_FILE   = PROJECT_ROOT / "data" / "rollrate_input.xlsx"   # 👈 đường dẫn mặc định nếu dùng Excel
EXCEL_SHEET  = "Data"    
# === COLUMNS CONFIG & others giữ nguyên ===

# ===========================
# A. Date Format Config
# ===========================
# Nếu DISBURSAL_DATE, CUTOFF_DATE là định dạng YYYYMM (int hoặc string)
# thì set DATE_FORMAT = "YYYYMM"
# Nếu là datetime thì set DATE_FORMAT = "datetime"
DATE_FORMAT = "YYYYMM"  # "YYYYMM" hoặc "datetime"


def parse_date(value):
    """
    Parse date từ nhiều định dạng khác nhau.
    - YYYYMM (int/string): 202501 -> 2025-01-01
    - datetime: giữ nguyên
    - string date: parse bình thường
    """
    if pd.isna(value):
        return pd.NaT
    
    # Nếu là int hoặc string dạng YYYYMM
    if isinstance(value, (int, float)):
        value = int(value)
        if 190001 <= value <= 209912:  # YYYYMM range
            year = value // 100
            month = value % 100
            return pd.Timestamp(year=year, month=month, day=1)
    
    # Nếu là string
    if isinstance(value, str):
        value = value.strip()
        # YYYYMM format
        if len(value) == 6 and value.isdigit():
            year = int(value[:4])
            month = int(value[4:6])
            return pd.Timestamp(year=year, month=month, day=1)
        # YYYY-MM format
        if len(value) == 7 and value[4] == '-':
            return pd.Timestamp(value + '-01')
    
    # Fallback: dùng pd.to_datetime
    try:
        return pd.to_datetime(value)
    except:
        return pd.NaT


def parse_date_column(series):
    """Parse toàn bộ column date."""
    return series.apply(parse_date)

# ===========================
# B. Model parameters
# ===========================
MIN_OBS = 100         # Số quan sát tối thiểu
MIN_EAD = 1e2         # Tổng dư nợ tối thiểu để build transition
BUCKETS_30P = ["DPD30+", "DPD60+", "DPD90+", "DPD120+", "DPD180+", "WRITEOFF"]
BUCKETS_60P = ["DPD60+", "DPD90+", "DPD120+", "DPD180+", "WRITEOFF"]
BUCKETS_90P = ["DPD90+", "DPD120+", "DPD180+", "WRITEOFF"]
# === COLUMNS CONFIG ===
CFG = dict(
    loan="AGREEMENT_ID",
    mob="MOB",
    state="STATE_MODEL",
    orig_date="DISBURSAL_DATE",
    ead="PRINCIPLE_OUTSTANDING",
    disb="DISBURSAL_AMOUNT",
    cutoff="CUTOFF_DATE",
)

# === SEGMENTATION CONFIG ===
# Các cột dùng để phân nhóm (segment) khi tính transition matrix và forecast
# Thay đổi list này để thêm/bớt segment dimensions
# Lưu ý: Code sử dụng 2 cột cố định: PRODUCT_TYPE và RISK_SCORE
# - PRODUCT_TYPE: giữ nguyên từ data
# - RISK_SCORE: sẽ được tạo tự động từ các cột trong SEGMENT_COLS (trừ PRODUCT_TYPE)
#
# Ví dụ:
# - SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE"] => giữ nguyên RISK_SCORE từ data
# - SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE", "GENDER"] => RISK_SCORE = "RISK_SCORE_GENDER"
# - SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE", "GENDER", "LA_GROUP"] => RISK_SCORE = "RISK_SCORE_GENDER_LA_GROUP"
SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE"]  # Mặc định: giữ nguyên RISK_SCORE từ data

def get_cohort_cols():
    """Trả về list columns để định nghĩa 1 cohort: SEGMENT_COLS + VINTAGE_DATE"""
    return ["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE"]

def get_cohort_mob_cols():
    """Trả về list columns để định nghĩa 1 cohort tại 1 MOB"""
    return ["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE", "MOB"]

def create_segment_columns(df):
    """
    Tạo cột PRODUCT_TYPE và RISK_SCORE từ SEGMENT_COLS.
    
    Logic:
    - Nếu SEGMENT_COLS = ["PRODUCT_TYPE", "RISK_SCORE"]: giữ nguyên
    - Nếu SEGMENT_COLS = ["PRODUCT_TYPE", "GRADE", "GENDER", "LA_GROUP"]:
      + PRODUCT_TYPE: giữ nguyên
      + RISK_SCORE = "GRADE_GENDER_LA_GROUP" (ghép các giá trị)
    
    Returns:
        DataFrame với cột PRODUCT_TYPE và RISK_SCORE đã được chuẩn hóa
    """
    df = df.copy()
    
    # Lấy các cột segment (trừ PRODUCT_TYPE)
    other_cols = [c for c in SEGMENT_COLS if c != "PRODUCT_TYPE"]
    
    if not other_cols:
        # Không có cột nào khác, tạo RISK_SCORE mặc định
        if "RISK_SCORE" not in df.columns:
            df["RISK_SCORE"] = "ALL"
    elif other_cols == ["RISK_SCORE"]:
        # Chỉ có RISK_SCORE, giữ nguyên
        df["RISK_SCORE"] = df["RISK_SCORE"].astype(str)
    else:
        # Ghép nhiều cột thành RISK_SCORE
        # Kiểm tra các cột có tồn tại không
        missing_cols = [c for c in other_cols if c not in df.columns]
        if missing_cols:
            raise KeyError(f"SEGMENT_COLS chứa các cột không tồn tại trong data: {missing_cols}")
        
        # Ghép các cột thành RISK_SCORE
        df["RISK_SCORE"] = df[other_cols].astype(str).agg("_".join, axis=1)
        print(f"   ✅ Tạo RISK_SCORE từ {other_cols}: {df['RISK_SCORE'].nunique()} unique values")
    
    # Đảm bảo PRODUCT_TYPE là string
    if "PRODUCT_TYPE" in df.columns:
        df["PRODUCT_TYPE"] = df["PRODUCT_TYPE"].astype(str)
    
    return df

SEGMENT_MAP = {
    "RISK_SCORE": ["LOW", "MEDIUM", "HIGH"],
    "PRODUCT_TYPE": ["PL", "CC"],
}


# === SMOOTHING CONFIG ===
ALPHA_SMOOTH = 0.5

# === STATE DEFINITIONS ===
BUCKETS_CANON = [
    "DPD0", "DPD1+", "DPD30+", "DPD60+", "DPD90+", "DPD120+", "DPD180+",
    "PREPAY", "WRITEOFF", "SOLDOUT"
]

#ABSORBING_BASE = ["WRITEOFF", "PREPAY", "SOLDOUT"]
ABSORBING_BASE = ["DPD90+", "WRITEOFF", "PREPAY", "SOLDOUT"] # PD model

DEFAULT = {"DPD90+"}

# === MODEL CONFIG ===
WEIGHT_METHOD = "exp"
#WEIGHT_METHOD = None
ROLL_WINDOW = 20
CFG["ROLL_WINDOW"] = ROLL_WINDOW
DECAY_LAMBDA = 0.5 ** (1/20)
CFG["DECAY_LAMBDA"] = DECAY_LAMBDA
# === MACRO & COLLX ADJUSTMENT CONFIG (optional, not wired by default) ===
MACRO_INDICATORS = {
    "GDP_GROWTH": {"weight": -0.3},
    "UNEMPLOYMENT_RATE": {"weight": +0.5},
    "CPI": {"weight": +0.2},
    "POLICY_RATE": {"weight": +0.3},
}
COLLX_CONFIG = {
    "COLLX_INDEX": {
        "weight": -0.4,
        "ref_value": 1.0,
        "min_adj": -0.3,
        "max_adj": +0.3,
    }
}
ADJUST_METHOD = "multiplicative"
MACRO_LAG = 1
MACRO_SOURCE = "sql/macro_data.sql"
COLLX_SOURCE = "sql/collx_index.sql"
