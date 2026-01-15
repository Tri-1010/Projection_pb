"""
Test script để so sánh 2 phương pháp allocation:
1. Random sampling (cũ) - KHÔNG xét STATE_CURRENT
2. Transition matrix (mới) - XÉT STATE_CURRENT
"""

import pandas as pd
import numpy as np
from src.config import BUCKETS_CANON, BUCKETS_30P, BUCKETS_90P

# ============================================================
# Tạo sample data
# ============================================================

print("=" * 70)
print("TEST: SO SÁNH 2 PHƯƠNG PHÁP ALLOCATION")
print("=" * 70)

# 1. Tạo transition matrix giả lập
# Matrix cho MOB 11→12
transition_matrix = pd.DataFrame({
    'DPD0': [0.95, 0.10, 0.05, 0.00],
    'DPD1+': [0.03, 0.80, 0.10, 0.00],
    'DPD30+': [0.01, 0.05, 0.75, 0.00],
    'DPD90+': [0.00, 0.02, 0.05, 0.80],
    'WRITEOFF': [0.01, 0.03, 0.05, 0.15],
    'PREPAY': [0.00, 0.00, 0.00, 0.05],
}, index=['DPD0', 'DPD1+', 'DPD30+', 'DPD90+'])

# Thêm các cột còn thiếu
for col in BUCKETS_CANON:
    if col not in transition_matrix.columns:
        transition_matrix[col] = 0.0

# Thêm các rows còn thiếu
for row in BUCKETS_CANON:
    if row not in transition_matrix.index:
        transition_matrix.loc[row] = 0.0
        transition_matrix.loc[row, row] = 1.0  # Absorbing state

# Normalize rows
transition_matrix = transition_matrix.div(transition_matrix.sum(axis=1), axis=0).fillna(0)

print("\n1️⃣ Transition Matrix (MOB 11→12):")
print(transition_matrix[['DPD0', 'DPD30+', 'DPD90+', 'WRITEOFF', 'PREPAY']].round(2))

# 2. Tạo matrices_by_mob
matrices_by_mob = {
    'SALPIL': {
        11: {
            'LOW': {
                'P': transition_matrix,
                'is_fallback': False,
            }
        }
    }
}

# 3. Tạo parent_fallback
parent_fallback = {
    ('SALPIL', 'LOW'): transition_matrix,
}

# 4. Tạo loan-level data
# 10 loans với STATE_CURRENT khác nhau
loans = [
    # 5 loans đang DPD0
    {'AGREEMENT_ID': 'LOAN_001', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD0', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    {'AGREEMENT_ID': 'LOAN_002', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD0', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    {'AGREEMENT_ID': 'LOAN_003', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD0', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    {'AGREEMENT_ID': 'LOAN_004', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD0', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    {'AGREEMENT_ID': 'LOAN_005', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD0', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    
    # 3 loans đang DPD30+
    {'AGREEMENT_ID': 'LOAN_006', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD30+', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    {'AGREEMENT_ID': 'LOAN_007', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD30+', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    {'AGREEMENT_ID': 'LOAN_008', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD30+', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    
    # 2 loans đang DPD90+
    {'AGREEMENT_ID': 'LOAN_009', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD90+', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
    {'AGREEMENT_ID': 'LOAN_010', 'PRODUCT_TYPE': 'SALPIL', 'RISK_SCORE': 'LOW',
     'DISBURSAL_DATE': '2024-01-01', 'MOB': 11, 'PRINCIPLE_OUTSTANDING': 100,
     'STATE_MODEL': 'DPD90+', 'CUTOFF_DATE': '2024-12-31', 'VINTAGE_DATE': '2024-01-01'},
]

df_loans = pd.DataFrame(loans)
df_loans['DISBURSAL_DATE'] = pd.to_datetime(df_loans['DISBURSAL_DATE'])
df_loans['CUTOFF_DATE'] = pd.to_datetime(df_loans['CUTOFF_DATE'])
df_loans['VINTAGE_DATE'] = pd.to_datetime(df_loans['VINTAGE_DATE'])

print("\n2️⃣ Loan-level data:")
print(f"   Tổng số loans: {len(df_loans)}")
print(f"   DPD0: {(df_loans['STATE_MODEL'] == 'DPD0').sum()} loans")
print(f"   DPD30+: {(df_loans['STATE_MODEL'] == 'DPD30+').sum()} loans")
print(f"   DPD90+: {(df_loans['STATE_MODEL'] == 'DPD90+').sum()} loans")

# ============================================================
# Test Method 2: Transition Matrix (mới)
# ============================================================

print("\n" + "=" * 70)
print("3️⃣ TEST: TRANSITION MATRIX METHOD (MỚI)")
print("=" * 70)

from src.rollrate.allocation_v2 import allocate_with_transition_matrix

df_transition = allocate_with_transition_matrix(
    df_loans_latest=df_loans,
    matrices_by_mob=matrices_by_mob,
    target_mob=12,
    parent_fallback=parent_fallback,
    seed=42,
)

print("\n📊 Kết quả Transition Matrix:")
print(df_transition[['AGREEMENT_ID', 'STATE_CURRENT', 'STATE_FORECAST', 'EAD_FORECAST']].to_string())

# Phân tích theo STATE_CURRENT
print("\n📊 Phân tích theo STATE_CURRENT:")

for state in ['DPD0', 'DPD30+', 'DPD90+']:
    mask = df_transition['STATE_CURRENT'] == state
    if mask.sum() > 0:
        subset = df_transition[mask]
        del30_rate = subset['STATE_FORECAST'].isin(BUCKETS_30P).mean() * 100
        del90_rate = subset['STATE_FORECAST'].isin(BUCKETS_90P).mean() * 100
        
        print(f"\n   {state} ({mask.sum()} loans):")
        print(f"      → DEL30+ forecast: {del30_rate:.1f}%")
        print(f"      → DEL90+ forecast: {del90_rate:.1f}%")
        print(f"      → State distribution:")
        for s, c in subset['STATE_FORECAST'].value_counts().items():
            print(f"         {s}: {c} ({c/mask.sum()*100:.1f}%)")

# ============================================================
# Kỳ vọng
# ============================================================

print("\n" + "=" * 70)
print("4️⃣ KỲ VỌNG (dựa trên transition matrix)")
print("=" * 70)

print("""
Dựa trên transition matrix:

1. Loans đang DPD0 (5 loans):
   - 95% → DPD0 (khoảng 4-5 loans)
   - 3% → DPD1+
   - 1% → DPD30+
   - 1% → WRITEOFF
   → DEL30+ rate ≈ 2% (rất thấp)
   → DEL90+ rate ≈ 1% (rất thấp)

2. Loans đang DPD30+ (3 loans):
   - 75% → DPD30+ (khoảng 2-3 loans)
   - 5% → DPD90+
   - 5% → WRITEOFF
   → DEL30+ rate ≈ 85% (cao)
   → DEL90+ rate ≈ 10% (trung bình)

3. Loans đang DPD90+ (2 loans):
   - 80% → DPD90+ (khoảng 1-2 loans)
   - 15% → WRITEOFF
   → DEL30+ rate ≈ 95% (rất cao)
   → DEL90+ rate ≈ 95% (rất cao)

⚠️ Logic cũ (random sampling) sẽ cho kết quả SAI:
   - Tất cả loans có cùng xác suất DEL30+/DEL90+
   - Không phân biệt STATE_CURRENT
""")

# ============================================================
# Validation
# ============================================================

print("\n" + "=" * 70)
print("5️⃣ VALIDATION")
print("=" * 70)

# Check 1: Loans DPD0 có DEL30+ rate thấp
dpd0_loans = df_transition[df_transition['STATE_CURRENT'] == 'DPD0']
dpd0_del30_rate = dpd0_loans['STATE_FORECAST'].isin(BUCKETS_30P).mean() * 100

if dpd0_del30_rate < 20:
    print(f"✅ PASS: Loans DPD0 có DEL30+ rate thấp ({dpd0_del30_rate:.1f}% < 20%)")
else:
    print(f"❌ FAIL: Loans DPD0 có DEL30+ rate cao ({dpd0_del30_rate:.1f}% >= 20%)")

# Check 2: Loans DPD30+ có DEL30+ rate cao
dpd30_loans = df_transition[df_transition['STATE_CURRENT'] == 'DPD30+']
dpd30_del30_rate = dpd30_loans['STATE_FORECAST'].isin(BUCKETS_30P).mean() * 100

if dpd30_del30_rate > 50:
    print(f"✅ PASS: Loans DPD30+ có DEL30+ rate cao ({dpd30_del30_rate:.1f}% > 50%)")
else:
    print(f"❌ FAIL: Loans DPD30+ có DEL30+ rate thấp ({dpd30_del30_rate:.1f}% <= 50%)")

# Check 3: Loans DPD90+ có DEL90+ rate cao
dpd90_loans = df_transition[df_transition['STATE_CURRENT'] == 'DPD90+']
dpd90_del90_rate = dpd90_loans['STATE_FORECAST'].isin(BUCKETS_90P).mean() * 100

if dpd90_del90_rate > 50:
    print(f"✅ PASS: Loans DPD90+ có DEL90+ rate cao ({dpd90_del90_rate:.1f}% > 50%)")
else:
    print(f"❌ FAIL: Loans DPD90+ có DEL90+ rate thấp ({dpd90_del90_rate:.1f}% <= 50%)")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
