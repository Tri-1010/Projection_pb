"""
Ví dụ: Lấy chi tiết hợp đồng sau khi allocate forecast
"""

import pandas as pd
from src.rollrate.allocation import allocate_forecast_to_loans, enrich_loan_forecast

# ============================================================
# Giả sử bạn đã có:
# - df_lifecycle_final: cohort-level forecast
# - df_raw: loan-level raw data
# ============================================================

# ============================================================
# CÁCH 1: Tự động (Khuyến nghị) ✅
# ============================================================
print("=" * 60)
print("CÁCH 1: Lấy chi tiết tự động từ allocate")
print("=" * 60)

# Allocate forecast xuống loan-level
df_loan_forecast = allocate_forecast_to_loans(
    df_lifecycle_final=df_lifecycle_final,
    df_raw=df_raw,
    target_mob=12,  # Phân bổ tại MOB 12
    allocation_method="proportional"
)

# ✅ df_loan_forecast ĐÃ CÓ SẴN tất cả các cột từ df_raw
print(f"\n📊 Kết quả allocate:")
print(f"   - Số hợp đồng: {len(df_loan_forecast):,}")
print(f"   - Số cột: {len(df_loan_forecast.columns)}")
print(f"\n📋 Các cột có sẵn:")
print(df_loan_forecast.columns.tolist())

# Xem chi tiết 5 hợp đồng đầu tiên
print(f"\n📄 Chi tiết 5 hợp đồng đầu tiên:")
print(df_loan_forecast[[
    'AGREEMENT_ID',
    'CUSTOMER_ID',
    'PRODUCT_TYPE',
    'RISK_SCORE',
    'STATE_FORECAST',
    'EAD_FORECAST',
    'TARGET_MOB'
]].head())


# ============================================================
# CÁCH 2: Thêm cột bổ sung (Nếu cần)
# ============================================================
print("\n" + "=" * 60)
print("CÁCH 2: Thêm cột bổ sung từ bảng khác")
print("=" * 60)

# Nếu bạn cần thêm thông tin từ bảng khác
# (Ví dụ: df_customer_info, df_branch_info)

# Bước 1: Merge thông tin bổ sung vào df_raw trước
# df_raw = df_raw.merge(df_customer_info, on='CUSTOMER_ID', how='left')
# df_raw = df_raw.merge(df_branch_info, on='BRANCH_CODE', how='left')

# Bước 2: Hoặc dùng enrich_loan_forecast sau khi allocate
df_loan_forecast_enriched = enrich_loan_forecast(
    df_allocated=df_loan_forecast,
    df_raw=df_raw,
    additional_cols=[
        'CUSTOMER_NAME',
        'CUSTOMER_SEGMENT',
        'BRANCH_NAME',
        'PRODUCT_CATEGORY',
        # ... các cột khác
    ]
)

print(f"\n📊 Kết quả sau khi enrich:")
print(f"   - Số cột: {len(df_loan_forecast_enriched.columns)}")


# ============================================================
# VÍ DỤ SỬ DỤNG
# ============================================================
print("\n" + "=" * 60)
print("VÍ DỤ SỬ DỤNG")
print("=" * 60)

# 1. Lọc hợp đồng có EAD forecast > 100M
df_high_ead = df_loan_forecast[df_loan_forecast['EAD_FORECAST'] > 100_000_000]
print(f"\n1️⃣ Hợp đồng có EAD > 100M: {len(df_high_ead):,}")

# 2. Tổng EAD forecast theo sản phẩm và state
df_product_summary = df_loan_forecast.groupby(
    ['PRODUCT_TYPE', 'STATE_FORECAST']
)['EAD_FORECAST'].sum().reset_index()
print(f"\n2️⃣ Tổng EAD theo sản phẩm và state:")
print(df_product_summary)

# 3. Tổng EAD forecast theo chi nhánh (nếu có cột BRANCH_CODE)
if 'BRANCH_CODE' in df_loan_forecast.columns:
    df_branch_summary = df_loan_forecast.groupby(
        'BRANCH_CODE'
    )['EAD_FORECAST'].sum().reset_index()
    print(f"\n3️⃣ Tổng EAD theo chi nhánh:")
    print(df_branch_summary.head())

# 4. Xuất ra Excel
output_file = 'Loan_Forecast_Details_MOB12.xlsx'
df_loan_forecast.to_excel(output_file, index=False)
print(f"\n4️⃣ Đã xuất ra file: {output_file}")


# ============================================================
# KIỂM TRA KẾT QUẢ
# ============================================================
print("\n" + "=" * 60)
print("KIỂM TRA KẾT QUẢ")
print("=" * 60)

# Kiểm tra missing values
print(f"\n📊 Missing values:")
missing = df_loan_forecast.isnull().sum()
print(missing[missing > 0])

# Kiểm tra tổng EAD
total_ead = df_loan_forecast['EAD_FORECAST'].sum()
print(f"\n💰 Tổng EAD forecast: {total_ead:,.0f}")

# Kiểm tra phân bố state
print(f"\n📊 Phân bố state forecast:")
state_dist = df_loan_forecast.groupby('STATE_FORECAST')['EAD_FORECAST'].agg([
    ('Count', 'count'),
    ('Total_EAD', 'sum'),
    ('Pct', lambda x: x.sum() / total_ead * 100)
])
print(state_dist)


# ============================================================
# TÓM TẮT
# ============================================================
print("\n" + "=" * 60)
print("TÓM TẮT")
print("=" * 60)
print("""
✅ Chi tiết hợp đồng ĐÃ CÓ SẴN trong df_loan_forecast
✅ KHÔNG CẦN merge thêm từ bảng khác
✅ Tất cả các cột từ df_raw đã được tự động copy

📌 Các cột quan trọng:
   - AGREEMENT_ID: Mã hợp đồng
   - CUSTOMER_ID: Mã khách hàng
   - PRODUCT_TYPE: Loại sản phẩm
   - STATE_FORECAST: Trạng thái dự báo
   - EAD_FORECAST: EAD dự báo
   - TARGET_MOB: MOB được phân bổ
   - ... và TẤT CẢ các cột khác từ df_raw

📌 Chỉ dùng enrich_loan_forecast() khi:
   - Cần thêm thông tin từ bảng khác (không có trong df_raw)
   - Muốn chọn cụ thể các cột cần thiết
""")
