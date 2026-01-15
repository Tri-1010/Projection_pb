# ============================================================
#  allocation_v2.py – Phân bổ forecast dựa trên Transition Matrix
#  
#  FIX: Logic cũ (random sampling) không xét STATE_CURRENT
#       Logic mới dùng transition matrix để tính xác suất đúng
# ============================================================

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_60P, BUCKETS_90P


def allocate_with_transition_matrix(
    df_loans_latest: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mob: int,
    parent_fallback: Dict = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Phân bổ forecast dựa trên transition matrix.
    
    ⚠️ FIX: Logic cũ (random sampling) không xét STATE_CURRENT của loan.
    Logic mới dùng transition matrix để tính xác suất chuyển state đúng.
    
    Logic:
    1. Với mỗi loan, lấy STATE_CURRENT và MOB_CURRENT
    2. Áp dụng transition matrix từ MOB_CURRENT đến TARGET_MOB
    3. Tính xác suất state tại TARGET_MOB
    4. Assign state theo xác suất
    
    Ví dụ:
        LOAN_001 (DPD0, MOB=11) → TARGET_MOB=12:
        - 1 step: Dùng matrix MOB 11→12
        - P(DPD0) = 95%, P(DPD30+) = 4%, P(WRITEOFF) = 1%
        - Hầu như chắc chắn DPD0 ✅
        
        LOAN_002 (DPD30+, MOB=11) → TARGET_MOB=12:
        - 1 step: Dùng matrix MOB 11→12
        - P(DPD0) = 10%, P(DPD30+) = 70%, P(WRITEOFF) = 20%
        - Hầu như chắc chắn DPD30+ hoặc xấu hơn ✅
    
    Parameters
    ----------
    df_loans_latest : DataFrame
        Loan-level data với các cột:
        - AGREEMENT_ID
        - PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE
        - STATE_MODEL (state hiện tại)
        - MOB (MOB hiện tại)
        - PRINCIPLE_OUTSTANDING (EAD hiện tại)
    
    matrices_by_mob : dict
        Transition matrices theo MOB:
        {
            (product, score, mob): {
                from_state: {to_state: probability}
            }
        }
    
    target_mob : int
        MOB cần forecast (ví dụ: 12, 24)
    
    parent_fallback : dict
        Fallback matrix nếu không có matrix cho MOB cụ thể
    
    seed : int
        Random seed để reproducible
    
    Returns
    -------
    DataFrame
        Loan-level forecast với các cột:
        - AGREEMENT_ID
        - PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE
        - STATE_CURRENT, MOB_CURRENT, EAD_CURRENT
        - STATE_FORECAST, EAD_FORECAST
        - TARGET_MOB
        - STATE_PROBS (dict xác suất các state)
    """
    
    loan_col = CFG["loan"]
    state_col = CFG["state"]
    mob_col = CFG["mob"]
    ead_col = CFG["ead"]
    
    np.random.seed(seed)
    
    results = []
    
    print(f"📍 Phân bổ forecast tại MOB = {target_mob} (dùng transition matrix)")
    print(f"   Số loans: {len(df_loans_latest):,}")
    
    for idx, loan in df_loans_latest.iterrows():
        loan_id = loan[loan_col]
        product = loan['PRODUCT_TYPE']
        score = loan['RISK_SCORE']
        vintage = loan['VINTAGE_DATE']
        state_current = loan[state_col]
        mob_current = int(loan[mob_col])
        ead_current = float(loan[ead_col])
        
        # Số bước cần forecast
        steps = target_mob - mob_current
        
        if steps <= 0:
            # Loan đã qua target_mob → Giữ nguyên state
            state_forecast = state_current
            state_probs = {state_current: 1.0}
        else:
            # Bắt đầu từ state hiện tại với xác suất 100%
            state_probs = {state_current: 1.0}
            
            # Áp dụng transition matrix steps lần
            for step in range(steps):
                mob_step = mob_current + step
                
                # Lấy matrix cho (product, score, mob)
                # Cấu trúc: matrices_by_mob[product][mob][score]["P"]
                matrix = None
                
                if product in matrices_by_mob:
                    if mob_step in matrices_by_mob[product]:
                        if score in matrices_by_mob[product][mob_step]:
                            matrix_data = matrices_by_mob[product][mob_step][score]
                            if isinstance(matrix_data, dict) and "P" in matrix_data:
                                # matrix_data["P"] là DataFrame, cần convert sang dict
                                P_df = matrix_data["P"]
                                matrix = P_df.to_dict(orient='index')
                
                # Fallback: dùng parent_fallback
                if matrix is None and parent_fallback:
                    # parent_fallback có cấu trúc: {(product, score): DataFrame}
                    parent_key = (product, score)
                    if parent_key in parent_fallback:
                        P_df = parent_fallback[parent_key]
                        if isinstance(P_df, pd.DataFrame):
                            matrix = P_df.to_dict(orient='index')
                
                # Fallback: dùng identity matrix (giữ nguyên state)
                if matrix is None:
                    continue
                
                # Nhân ma trận xác suất
                new_probs = {st: 0.0 for st in BUCKETS_CANON}
                
                for from_state, prob in state_probs.items():
                    if prob <= 0:
                        continue
                    
                    # Lấy transition probabilities từ from_state
                    trans_probs = matrix.get(from_state, {})
                    
                    if not trans_probs:
                        # Không có transition → giữ nguyên state
                        new_probs[from_state] = new_probs.get(from_state, 0) + prob
                        continue
                    
                    for to_state, trans_prob in trans_probs.items():
                        if to_state in new_probs:
                            new_probs[to_state] += prob * trans_prob
                
                # Normalize
                total = sum(new_probs.values())
                if total > 0:
                    state_probs = {k: v/total for k, v in new_probs.items() if v > 0}
                else:
                    # Fallback: giữ nguyên state
                    state_probs = {state_current: 1.0}
            
            # Assign state theo xác suất
            if state_probs:
                states = list(state_probs.keys())
                probs = list(state_probs.values())
                state_forecast = np.random.choice(states, p=probs)
            else:
                state_forecast = state_current
        
        # Tính EAD forecast
        # EAD giảm theo xác suất PREPAY + WRITEOFF + SOLDOUT (absorbing states)
        absorbing_prob = (
            state_probs.get('PREPAY', 0) +
            state_probs.get('WRITEOFF', 0) +
            state_probs.get('SOLDOUT', 0)
        )
        ead_forecast = ead_current * (1 - absorbing_prob)
        
        results.append({
            loan_col: loan_id,
            'PRODUCT_TYPE': product,
            'RISK_SCORE': score,
            'VINTAGE_DATE': vintage,
            'STATE_CURRENT': state_current,
            'MOB_CURRENT': mob_current,
            'EAD_CURRENT': ead_current,
            'STATE_FORECAST': state_forecast,
            'EAD_FORECAST': ead_forecast,
            'TARGET_MOB': target_mob,
            'IS_FORECAST': 1,
            'STATE_PROBS': state_probs,  # Lưu xác suất để debug
        })
    
    df_result = pd.DataFrame(results)
    
    # Validation
    print(f"\n✅ Phân bổ hoàn tất:")
    print(f"   Số loans: {len(df_result):,}")
    
    # Thống kê state transition
    if not df_result.empty:
        same_state = (df_result['STATE_CURRENT'] == df_result['STATE_FORECAST']).sum()
        diff_state = len(df_result) - same_state
        print(f"   Giữ nguyên state: {same_state:,} ({same_state/len(df_result)*100:.1f}%)")
        print(f"   Chuyển state: {diff_state:,} ({diff_state/len(df_result)*100:.1f}%)")
        
        # Thống kê DEL
        if 'STATE_FORECAST' in df_result.columns:
            del30_count = df_result['STATE_FORECAST'].isin(BUCKETS_30P).sum()
            del90_count = df_result['STATE_FORECAST'].isin(BUCKETS_90P).sum()
            print(f"   DEL30+ forecast: {del30_count:,} ({del30_count/len(df_result)*100:.2f}%)")
            print(f"   DEL90+ forecast: {del90_count:,} ({del90_count/len(df_result)*100:.2f}%)")
    
    return df_result


def allocate_multi_mob_v2(
    df_loans_latest: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mobs: List[int] = [12, 24],
    parent_fallback: Dict = None,
    include_del30: bool = True,
    include_del60: bool = False,
    include_del90: bool = True,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Phân bổ forecast tại NHIỀU MOB dùng transition matrix.
    
    Parameters
    ----------
    df_loans_latest : DataFrame
        Loan-level data (snapshot mới nhất)
    matrices_by_mob : dict
        Transition matrices theo MOB
    target_mobs : list
        Danh sách MOB cần forecast
    parent_fallback : dict
        Fallback matrix
    include_del30, include_del60, include_del90 : bool
        Có tính DEL flags không
    seed : int
        Random seed
    
    Returns
    -------
    DataFrame
        Loan-level forecast với format:
        - AGREEMENT_ID
        - PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE
        - MOB_CURRENT, EAD_CURRENT, STATE_CURRENT
        - STATE_FORECAST_MOB12, EAD_FORECAST_MOB12, DEL30_FLAG_MOB12, DEL90_FLAG_MOB12
        - STATE_FORECAST_MOB24, EAD_FORECAST_MOB24, DEL30_FLAG_MOB24, DEL90_FLAG_MOB24
    """
    
    loan_col = CFG["loan"]
    
    print(f"🎯 Phân bổ forecast tại {len(target_mobs)} MOB: {target_mobs}")
    print(f"   (Dùng transition matrix - logic mới)")
    
    # Lấy thông tin cơ bản của mỗi loan
    loan_info = df_loans_latest[[
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
        CFG["mob"], CFG["ead"], CFG["state"]
    ]].copy()
    
    loan_info = loan_info.rename(columns={
        CFG["mob"]: 'MOB_CURRENT',
        CFG["ead"]: 'EAD_CURRENT',
        CFG["state"]: 'STATE_CURRENT',
    })
    
    # Loop qua từng target MOB
    results_by_mob = {}
    
    for target_mob in target_mobs:
        print(f"\n📍 Phân bổ tại MOB {target_mob}...")
        
        df_allocated = allocate_with_transition_matrix(
            df_loans_latest=df_loans_latest,
            matrices_by_mob=matrices_by_mob,
            target_mob=target_mob,
            parent_fallback=parent_fallback,
            seed=seed,
        )
        
        if df_allocated.empty:
            print(f"⚠️ Không có kết quả tại MOB {target_mob}")
            continue
        
        # Tính DEL flags
        df_allocated = _add_del_flags_v2(
            df_allocated,
            include_del30=include_del30,
            include_del60=include_del60,
            include_del90=include_del90,
        )
        
        # Chỉ giữ các cột cần thiết
        cols_to_keep = [
            loan_col,
            'STATE_FORECAST',
            'EAD_FORECAST',
        ]
        
        if include_del30:
            cols_to_keep.append('DEL30_FLAG')
        if include_del60:
            cols_to_keep.append('DEL60_FLAG')
        if include_del90:
            cols_to_keep.append('DEL90_FLAG')
        
        df_mob = df_allocated[cols_to_keep].copy()
        
        # Rename columns với suffix _MOBXX
        rename_map = {
            'STATE_FORECAST': f'STATE_FORECAST_MOB{target_mob}',
            'EAD_FORECAST': f'EAD_FORECAST_MOB{target_mob}',
        }
        
        if include_del30:
            rename_map['DEL30_FLAG'] = f'DEL30_FLAG_MOB{target_mob}'
        if include_del60:
            rename_map['DEL60_FLAG'] = f'DEL60_FLAG_MOB{target_mob}'
        if include_del90:
            rename_map['DEL90_FLAG'] = f'DEL90_FLAG_MOB{target_mob}'
        
        df_mob = df_mob.rename(columns=rename_map)
        
        results_by_mob[target_mob] = df_mob
    
    # Merge tất cả MOB vào 1 DataFrame
    if not results_by_mob:
        print("⚠️ Không có kết quả phân bổ.")
        return pd.DataFrame()
    
    df_result = loan_info.copy()
    
    for target_mob, df_mob in results_by_mob.items():
        df_result = df_result.merge(
            df_mob,
            on=loan_col,
            how='left'
        )
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for target_mob in target_mobs:
        state_col = f'STATE_FORECAST_MOB{target_mob}'
        del90_col = f'DEL90_FLAG_MOB{target_mob}'
        
        if state_col not in df_result.columns:
            continue
        
        print(f"\n📍 MOB {target_mob}:")
        print(f"   State distribution:")
        state_dist = df_result[state_col].value_counts()
        for state, count in state_dist.items():
            pct = count / len(df_result) * 100
            print(f"      {state}: {count:,} ({pct:.2f}%)")
        
        if del90_col in df_result.columns:
            del90_count = df_result[del90_col].sum()
            del90_pct = del90_count / len(df_result) * 100
            print(f"   DEL90+: {del90_count:,} ({del90_pct:.2f}%)")
    
    return df_result


def _add_del_flags_v2(
    df: pd.DataFrame,
    include_del30: bool = True,
    include_del60: bool = False,
    include_del90: bool = True,
) -> pd.DataFrame:
    """Thêm DEL flags dựa trên STATE_FORECAST."""
    
    df = df.copy()
    
    if include_del30:
        df['DEL30_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_30P).astype(int)
    
    if include_del60:
        df['DEL60_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_60P).astype(int)
    
    if include_del90:
        df['DEL90_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_90P).astype(int)
    
    return df


# ============================================================
# Utility functions
# ============================================================

def compare_allocation_methods(
    df_loans_latest: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mob: int = 12,
    parent_fallback: Dict = None,
) -> pd.DataFrame:
    """
    So sánh kết quả giữa 2 phương pháp allocation:
    1. Random sampling (cũ)
    2. Transition matrix (mới)
    
    Returns
    -------
    DataFrame
        So sánh DEL rates giữa 2 phương pháp
    """
    
    from src.rollrate.allocation import allocate_forecast_to_loans_simple
    
    print("="*60)
    print("SO SÁNH 2 PHƯƠNG PHÁP ALLOCATION")
    print("="*60)
    
    # Method 1: Random sampling (cũ)
    print("\n1️⃣ Random Sampling (cũ):")
    df_random = allocate_forecast_to_loans_simple(
        df_lifecycle_final=df_lifecycle_final,
        df_raw=df_loans_latest,
        target_mob=target_mob,
    )
    
    # Method 2: Transition matrix (mới)
    print("\n2️⃣ Transition Matrix (mới):")
    df_transition = allocate_with_transition_matrix(
        df_loans_latest=df_loans_latest,
        matrices_by_mob=matrices_by_mob,
        target_mob=target_mob,
        parent_fallback=parent_fallback,
    )
    
    # So sánh
    print("\n" + "="*60)
    print("📊 SO SÁNH KẾT QUẢ")
    print("="*60)
    
    if not df_random.empty and not df_transition.empty:
        # DEL30 rate
        del30_random = df_random['STATE_FORECAST'].isin(BUCKETS_30P).mean() * 100
        del30_transition = df_transition['STATE_FORECAST'].isin(BUCKETS_30P).mean() * 100
        
        # DEL90 rate
        del90_random = df_random['STATE_FORECAST'].isin(BUCKETS_90P).mean() * 100
        del90_transition = df_transition['STATE_FORECAST'].isin(BUCKETS_90P).mean() * 100
        
        print(f"\n📍 DEL30+ rate @ MOB {target_mob}:")
        print(f"   Random sampling: {del30_random:.2f}%")
        print(f"   Transition matrix: {del30_transition:.2f}%")
        
        print(f"\n📍 DEL90+ rate @ MOB {target_mob}:")
        print(f"   Random sampling: {del90_random:.2f}%")
        print(f"   Transition matrix: {del90_transition:.2f}%")
        
        # So sánh theo STATE_CURRENT
        print(f"\n📍 DEL90+ rate theo STATE_CURRENT:")
        
        for state in ['DPD0', 'DPD30+', 'DPD90+']:
            mask_random = df_random['STATE_CURRENT'] == state if 'STATE_CURRENT' in df_random.columns else pd.Series([False]*len(df_random))
            mask_transition = df_transition['STATE_CURRENT'] == state
            
            if mask_transition.sum() > 0:
                del90_r = df_random.loc[mask_random, 'STATE_FORECAST'].isin(BUCKETS_90P).mean() * 100 if mask_random.sum() > 0 else 0
                del90_t = df_transition.loc[mask_transition, 'STATE_FORECAST'].isin(BUCKETS_90P).mean() * 100
                
                print(f"   {state}:")
                print(f"      Random: {del90_r:.2f}%")
                print(f"      Transition: {del90_t:.2f}%")
    
    return {
        'random': df_random,
        'transition': df_transition,
    }


# ============================================================
# SCALING: Điều chỉnh allocation để match với lifecycle (calibrated)
# ============================================================

def scale_allocation_to_lifecycle(
    df_allocated: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    target_mob: int,
) -> pd.DataFrame:
    """
    Scale EAD_FORECAST từ allocation để match với lifecycle (đã calibrated).
    
    Vấn đề:
        - Lifecycle forecast đã apply calibration (k per MOB)
        - Allocation dùng transition matrix gốc (chưa calibrated)
        - → Tổng EAD theo state từ allocation ≠ lifecycle
    
    Giải pháp:
        - Tính scaling factor cho mỗi (product, score, vintage, state)
        - Scale EAD_FORECAST để match với lifecycle
    
    Parameters
    ----------
    df_allocated : DataFrame
        Kết quả từ allocate_with_transition_matrix()
    df_lifecycle_final : DataFrame
        Lifecycle forecast đã calibrated
    target_mob : int
        MOB đang xét
    
    Returns
    -------
    DataFrame
        df_allocated với cột EAD_FORECAST_SCALED
    """
    
    df = df_allocated.copy()
    
    print(f"\n🔧 Scaling allocation to match lifecycle @ MOB {target_mob}...")
    
    # Lọc lifecycle tại target_mob
    df_lc = df_lifecycle_final[df_lifecycle_final['MOB'] == target_mob].copy()
    
    if df_lc.empty:
        print(f"⚠️ Không có lifecycle data tại MOB {target_mob}")
        df['EAD_FORECAST_SCALED'] = df['EAD_FORECAST']
        df['SCALING_FACTOR'] = 1.0
        return df
    
    # Tính scaling factor cho mỗi cohort × state
    scaling_factors = {}
    
    for _, row_lc in df_lc.iterrows():
        product = row_lc['PRODUCT_TYPE']
        score = row_lc['RISK_SCORE']
        vintage = row_lc['VINTAGE_DATE']
        
        # EAD theo state từ lifecycle (đã calibrated)
        for state in BUCKETS_CANON:
            ead_lifecycle = row_lc.get(state, 0)
            if pd.isna(ead_lifecycle):
                ead_lifecycle = 0
            
            # EAD theo state từ allocation
            mask = (
                (df['PRODUCT_TYPE'] == product) &
                (df['RISK_SCORE'] == score) &
                (df['VINTAGE_DATE'] == vintage) &
                (df['STATE_FORECAST'] == state)
            )
            ead_allocated = df.loc[mask, 'EAD_FORECAST'].sum()
            
            # Tính scaling factor
            if ead_allocated > 0:
                factor = ead_lifecycle / ead_allocated
            else:
                factor = 1.0
            
            scaling_factors[(product, score, vintage, state)] = factor
    
    # Apply scaling
    def get_scaling_factor(row):
        key = (row['PRODUCT_TYPE'], row['RISK_SCORE'], row['VINTAGE_DATE'], row['STATE_FORECAST'])
        return scaling_factors.get(key, 1.0)
    
    df['SCALING_FACTOR'] = df.apply(get_scaling_factor, axis=1)
    df['EAD_FORECAST_SCALED'] = df['EAD_FORECAST'] * df['SCALING_FACTOR']
    
    # Validation
    total_ead_allocated = df['EAD_FORECAST'].sum()
    total_ead_scaled = df['EAD_FORECAST_SCALED'].sum()
    total_ead_lifecycle = df_lc[BUCKETS_CANON].sum().sum()
    
    print(f"   EAD allocated (raw): {total_ead_allocated:,.0f}")
    print(f"   EAD scaled: {total_ead_scaled:,.0f}")
    print(f"   EAD lifecycle: {total_ead_lifecycle:,.0f}")
    
    diff_pct = abs(total_ead_scaled - total_ead_lifecycle) / total_ead_lifecycle * 100 if total_ead_lifecycle > 0 else 0
    if diff_pct < 1:
        print(f"   ✅ Match! (diff = {diff_pct:.2f}%)")
    else:
        print(f"   ⚠️ Mismatch (diff = {diff_pct:.2f}%)")
    
    return df


def allocate_with_calibration_scaling(
    df_loans_latest: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mob: int,
    parent_fallback: Dict = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Allocation với scaling từ lifecycle (đã calibrated).
    
    Workflow:
    1. Dùng transition matrix để assign STATE_FORECAST
    2. Scale EAD_FORECAST để match với lifecycle
    
    Parameters
    ----------
    df_loans_latest : DataFrame
        Loan-level data
    df_lifecycle_final : DataFrame
        Lifecycle forecast đã calibrated
    matrices_by_mob : dict
        Transition matrices
    target_mob : int
        MOB cần forecast
    parent_fallback : dict
        Fallback matrix
    seed : int
        Random seed
    
    Returns
    -------
    DataFrame
        Loan-level forecast với EAD_FORECAST_SCALED
    """
    
    # Bước 1: Allocation với transition matrix
    df_allocated = allocate_with_transition_matrix(
        df_loans_latest=df_loans_latest,
        matrices_by_mob=matrices_by_mob,
        target_mob=target_mob,
        parent_fallback=parent_fallback,
        seed=seed,
    )
    
    if df_allocated.empty:
        return df_allocated
    
    # Bước 2: Scale để match với lifecycle
    df_scaled = scale_allocation_to_lifecycle(
        df_allocated=df_allocated,
        df_lifecycle_final=df_lifecycle_final,
        target_mob=target_mob,
    )
    
    return df_scaled


def allocate_multi_mob_with_scaling(
    df_loans_latest: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mobs: List[int] = [12, 24],
    parent_fallback: Dict = None,
    include_del30: bool = True,
    include_del60: bool = False,
    include_del90: bool = True,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Phân bổ forecast tại NHIỀU MOB với scaling từ lifecycle.
    
    Parameters
    ----------
    df_loans_latest : DataFrame
        Loan-level data (snapshot mới nhất)
    df_lifecycle_final : DataFrame
        Lifecycle forecast đã calibrated
    matrices_by_mob : dict
        Transition matrices theo MOB
    target_mobs : list
        Danh sách MOB cần forecast
    parent_fallback : dict
        Fallback matrix
    include_del30, include_del60, include_del90 : bool
        Có tính DEL flags không
    seed : int
        Random seed
    
    Returns
    -------
    DataFrame
        Loan-level forecast với format:
        - AGREEMENT_ID
        - PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE
        - MOB_CURRENT, EAD_CURRENT, STATE_CURRENT
        - STATE_FORECAST_MOB12, EAD_FORECAST_MOB12, EAD_SCALED_MOB12, DEL30_FLAG_MOB12, DEL90_FLAG_MOB12
        - STATE_FORECAST_MOB24, EAD_FORECAST_MOB24, EAD_SCALED_MOB24, DEL30_FLAG_MOB24, DEL90_FLAG_MOB24
    """
    
    loan_col = CFG["loan"]
    
    print(f"🎯 Phân bổ forecast tại {len(target_mobs)} MOB: {target_mobs}")
    print(f"   (Dùng transition matrix + scaling từ lifecycle)")
    
    # Lấy thông tin cơ bản của mỗi loan
    loan_info = df_loans_latest[[
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
        CFG["mob"], CFG["ead"], CFG["state"]
    ]].copy()
    
    loan_info = loan_info.rename(columns={
        CFG["mob"]: 'MOB_CURRENT',
        CFG["ead"]: 'EAD_CURRENT',
        CFG["state"]: 'STATE_CURRENT',
    })
    
    # Loop qua từng target MOB
    results_by_mob = {}
    
    for target_mob in target_mobs:
        print(f"\n{'='*60}")
        print(f"📍 Phân bổ tại MOB {target_mob}...")
        print(f"{'='*60}")
        
        df_allocated = allocate_with_calibration_scaling(
            df_loans_latest=df_loans_latest,
            df_lifecycle_final=df_lifecycle_final,
            matrices_by_mob=matrices_by_mob,
            target_mob=target_mob,
            parent_fallback=parent_fallback,
            seed=seed,
        )
        
        if df_allocated.empty:
            print(f"⚠️ Không có kết quả tại MOB {target_mob}")
            continue
        
        # Tính DEL flags
        df_allocated = _add_del_flags_v2(
            df_allocated,
            include_del30=include_del30,
            include_del60=include_del60,
            include_del90=include_del90,
        )
        
        # Chỉ giữ các cột cần thiết
        cols_to_keep = [
            loan_col,
            'STATE_FORECAST',
            'EAD_FORECAST',
            'EAD_FORECAST_SCALED',
            'SCALING_FACTOR',
        ]
        
        if include_del30:
            cols_to_keep.append('DEL30_FLAG')
        if include_del60:
            cols_to_keep.append('DEL60_FLAG')
        if include_del90:
            cols_to_keep.append('DEL90_FLAG')
        
        df_mob = df_allocated[cols_to_keep].copy()
        
        # Rename columns với suffix _MOBXX
        rename_map = {
            'STATE_FORECAST': f'STATE_FORECAST_MOB{target_mob}',
            'EAD_FORECAST': f'EAD_FORECAST_MOB{target_mob}',
            'EAD_FORECAST_SCALED': f'EAD_SCALED_MOB{target_mob}',
            'SCALING_FACTOR': f'SCALING_FACTOR_MOB{target_mob}',
        }
        
        if include_del30:
            rename_map['DEL30_FLAG'] = f'DEL30_FLAG_MOB{target_mob}'
        if include_del60:
            rename_map['DEL60_FLAG'] = f'DEL60_FLAG_MOB{target_mob}'
        if include_del90:
            rename_map['DEL90_FLAG'] = f'DEL90_FLAG_MOB{target_mob}'
        
        df_mob = df_mob.rename(columns=rename_map)
        
        results_by_mob[target_mob] = df_mob
    
    # Merge tất cả MOB vào 1 DataFrame
    if not results_by_mob:
        print("⚠️ Không có kết quả phân bổ.")
        return pd.DataFrame()
    
    df_result = loan_info.copy()
    
    for target_mob, df_mob in results_by_mob.items():
        df_result = df_result.merge(
            df_mob,
            on=loan_col,
            how='left'
        )
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for target_mob in target_mobs:
        state_col = f'STATE_FORECAST_MOB{target_mob}'
        del90_col = f'DEL90_FLAG_MOB{target_mob}'
        ead_col = f'EAD_FORECAST_MOB{target_mob}'
        ead_scaled_col = f'EAD_SCALED_MOB{target_mob}'
        
        if state_col not in df_result.columns:
            continue
        
        print(f"\n📍 MOB {target_mob}:")
        
        # EAD comparison
        if ead_col in df_result.columns and ead_scaled_col in df_result.columns:
            ead_raw = df_result[ead_col].sum()
            ead_scaled = df_result[ead_scaled_col].sum()
            print(f"   EAD (raw): {ead_raw:,.0f}")
            print(f"   EAD (scaled): {ead_scaled:,.0f}")
        
        # DEL rates
        if del90_col in df_result.columns:
            del90_count = df_result[del90_col].sum()
            del90_pct = del90_count / len(df_result) * 100
            print(f"   DEL90+: {del90_count:,} ({del90_pct:.2f}%)")
    
    return df_result


# ============================================================
# BACKTEST: So sánh forecast với actual
# ============================================================

def backtest_allocation(
    df_allocated: pd.DataFrame,
    df_actual: pd.DataFrame,
    target_mob: int,
    state_col_forecast: str = 'STATE_FORECAST',
    state_col_actual: str = None,
) -> pd.DataFrame:
    """
    Backtest: So sánh STATE_FORECAST với STATE_ACTUAL.
    
    Parameters
    ----------
    df_allocated : DataFrame
        Kết quả allocation với STATE_FORECAST
    df_actual : DataFrame
        Dữ liệu actual tại target_mob
    target_mob : int
        MOB đang xét
    state_col_forecast : str
        Tên cột state forecast
    state_col_actual : str
        Tên cột state actual (mặc định: STATE_MODEL)
    
    Returns
    -------
    DataFrame
        Confusion matrix và metrics
    """
    
    loan_col = CFG["loan"]
    if state_col_actual is None:
        state_col_actual = CFG["state"]
    
    print(f"\n{'='*60}")
    print(f"📊 BACKTEST @ MOB {target_mob}")
    print(f"{'='*60}")
    
    # Merge forecast với actual
    df_forecast = df_allocated[[loan_col, state_col_forecast]].copy()
    df_forecast = df_forecast.rename(columns={state_col_forecast: 'STATE_FORECAST'})
    
    # Lọc actual tại target_mob
    df_act = df_actual[df_actual[CFG["mob"]] == target_mob].copy()
    df_act = df_act[[loan_col, state_col_actual]].copy()
    df_act = df_act.rename(columns={state_col_actual: 'STATE_ACTUAL'})
    
    # Merge
    df_compare = df_forecast.merge(df_act, on=loan_col, how='inner')
    
    if df_compare.empty:
        print("⚠️ Không có dữ liệu để backtest")
        return pd.DataFrame()
    
    print(f"   Số loans so sánh: {len(df_compare):,}")
    
    # Accuracy
    correct = (df_compare['STATE_FORECAST'] == df_compare['STATE_ACTUAL']).sum()
    accuracy = correct / len(df_compare) * 100
    print(f"   Accuracy (exact match): {accuracy:.2f}%")
    
    # DEL30 accuracy
    df_compare['DEL30_FORECAST'] = df_compare['STATE_FORECAST'].isin(BUCKETS_30P).astype(int)
    df_compare['DEL30_ACTUAL'] = df_compare['STATE_ACTUAL'].isin(BUCKETS_30P).astype(int)
    
    del30_correct = (df_compare['DEL30_FORECAST'] == df_compare['DEL30_ACTUAL']).sum()
    del30_accuracy = del30_correct / len(df_compare) * 100
    print(f"   DEL30 accuracy: {del30_accuracy:.2f}%")
    
    # DEL90 accuracy
    df_compare['DEL90_FORECAST'] = df_compare['STATE_FORECAST'].isin(BUCKETS_90P).astype(int)
    df_compare['DEL90_ACTUAL'] = df_compare['STATE_ACTUAL'].isin(BUCKETS_90P).astype(int)
    
    del90_correct = (df_compare['DEL90_FORECAST'] == df_compare['DEL90_ACTUAL']).sum()
    del90_accuracy = del90_correct / len(df_compare) * 100
    print(f"   DEL90 accuracy: {del90_accuracy:.2f}%")
    
    # Confusion matrix for DEL90
    print(f"\n📊 DEL90 Confusion Matrix:")
    
    tp = ((df_compare['DEL90_FORECAST'] == 1) & (df_compare['DEL90_ACTUAL'] == 1)).sum()
    fp = ((df_compare['DEL90_FORECAST'] == 1) & (df_compare['DEL90_ACTUAL'] == 0)).sum()
    fn = ((df_compare['DEL90_FORECAST'] == 0) & (df_compare['DEL90_ACTUAL'] == 1)).sum()
    tn = ((df_compare['DEL90_FORECAST'] == 0) & (df_compare['DEL90_ACTUAL'] == 0)).sum()
    
    print(f"                    Actual")
    print(f"                    DEL90=1    DEL90=0")
    print(f"   Forecast DEL90=1   {tp:>6,}    {fp:>6,}  (TP, FP)")
    print(f"   Forecast DEL90=0   {fn:>6,}    {tn:>6,}  (FN, TN)")
    
    # Metrics
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n📊 DEL90 Metrics:")
    print(f"   Precision: {precision:.2f}%")
    print(f"   Recall: {recall:.2f}%")
    print(f"   F1 Score: {f1:.2f}%")
    
    # Forecast vs Actual rates
    del90_forecast_rate = df_compare['DEL90_FORECAST'].mean() * 100
    del90_actual_rate = df_compare['DEL90_ACTUAL'].mean() * 100
    
    print(f"\n📊 DEL90 Rates:")
    print(f"   Forecast: {del90_forecast_rate:.2f}%")
    print(f"   Actual: {del90_actual_rate:.2f}%")
    print(f"   Diff: {del90_forecast_rate - del90_actual_rate:+.2f}%")
    
    return df_compare


def backtest_allocation_by_cohort(
    df_allocated: pd.DataFrame,
    df_actual: pd.DataFrame,
    target_mob: int,
    state_col_forecast: str = 'STATE_FORECAST',
) -> pd.DataFrame:
    """
    Backtest theo từng cohort (Product × Risk × Vintage).
    
    Returns
    -------
    DataFrame
        Metrics theo cohort
    """
    
    loan_col = CFG["loan"]
    state_col_actual = CFG["state"]
    
    print(f"\n{'='*60}")
    print(f"📊 BACKTEST BY COHORT @ MOB {target_mob}")
    print(f"{'='*60}")
    
    # Merge forecast với actual
    df_forecast = df_allocated[[
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE', state_col_forecast
    ]].copy()
    df_forecast = df_forecast.rename(columns={state_col_forecast: 'STATE_FORECAST'})
    
    # Lọc actual tại target_mob
    df_act = df_actual[df_actual[CFG["mob"]] == target_mob].copy()
    df_act = df_act[[loan_col, state_col_actual]].copy()
    df_act = df_act.rename(columns={state_col_actual: 'STATE_ACTUAL'})
    
    # Merge
    df_compare = df_forecast.merge(df_act, on=loan_col, how='inner')
    
    if df_compare.empty:
        print("⚠️ Không có dữ liệu để backtest")
        return pd.DataFrame()
    
    # Tính DEL flags
    df_compare['DEL90_FORECAST'] = df_compare['STATE_FORECAST'].isin(BUCKETS_90P).astype(int)
    df_compare['DEL90_ACTUAL'] = df_compare['STATE_ACTUAL'].isin(BUCKETS_90P).astype(int)
    
    # Group by cohort
    results = []
    
    for (product, score, vintage), grp in df_compare.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']):
        n_loans = len(grp)
        
        # DEL90 rates
        del90_forecast = grp['DEL90_FORECAST'].mean() * 100
        del90_actual = grp['DEL90_ACTUAL'].mean() * 100
        
        # Accuracy
        del90_correct = (grp['DEL90_FORECAST'] == grp['DEL90_ACTUAL']).sum()
        del90_accuracy = del90_correct / n_loans * 100
        
        results.append({
            'PRODUCT_TYPE': product,
            'RISK_SCORE': score,
            'VINTAGE_DATE': vintage,
            'N_LOANS': n_loans,
            'DEL90_FORECAST': del90_forecast,
            'DEL90_ACTUAL': del90_actual,
            'DEL90_DIFF': del90_forecast - del90_actual,
            'DEL90_ACCURACY': del90_accuracy,
        })
    
    df_results = pd.DataFrame(results)
    
    # Summary
    print(f"\n📊 Summary by cohort:")
    print(df_results.to_string(index=False))
    
    # Overall metrics
    print(f"\n📊 Overall:")
    print(f"   Mean DEL90 Forecast: {df_results['DEL90_FORECAST'].mean():.2f}%")
    print(f"   Mean DEL90 Actual: {df_results['DEL90_ACTUAL'].mean():.2f}%")
    print(f"   Mean DEL90 Diff: {df_results['DEL90_DIFF'].mean():+.2f}%")
    print(f"   Mean DEL90 Accuracy: {df_results['DEL90_ACCURACY'].mean():.2f}%")
    
    return df_results


def backtest_ead(
    df_allocated: pd.DataFrame,
    df_actual: pd.DataFrame,
    target_mob: int,
    ead_col_forecast: str = 'EAD_FORECAST_SCALED',
) -> pd.DataFrame:
    """
    Backtest EAD: So sánh EAD_FORECAST với EAD_ACTUAL.
    
    Parameters
    ----------
    df_allocated : DataFrame
        Kết quả allocation với EAD_FORECAST
    df_actual : DataFrame
        Dữ liệu actual tại target_mob
    target_mob : int
        MOB đang xét
    ead_col_forecast : str
        Tên cột EAD forecast
    
    Returns
    -------
    DataFrame
        Comparison metrics
    """
    
    loan_col = CFG["loan"]
    ead_col_actual = CFG["ead"]
    
    print(f"\n{'='*60}")
    print(f"📊 BACKTEST EAD @ MOB {target_mob}")
    print(f"{'='*60}")
    
    # Merge forecast với actual
    df_forecast = df_allocated[[loan_col, ead_col_forecast]].copy()
    df_forecast = df_forecast.rename(columns={ead_col_forecast: 'EAD_FORECAST'})
    
    # Lọc actual tại target_mob
    df_act = df_actual[df_actual[CFG["mob"]] == target_mob].copy()
    df_act = df_act[[loan_col, ead_col_actual]].copy()
    df_act = df_act.rename(columns={ead_col_actual: 'EAD_ACTUAL'})
    
    # Merge
    df_compare = df_forecast.merge(df_act, on=loan_col, how='inner')
    
    if df_compare.empty:
        print("⚠️ Không có dữ liệu để backtest")
        return pd.DataFrame()
    
    print(f"   Số loans so sánh: {len(df_compare):,}")
    
    # Total EAD
    total_forecast = df_compare['EAD_FORECAST'].sum()
    total_actual = df_compare['EAD_ACTUAL'].sum()
    
    print(f"\n📊 Total EAD:")
    print(f"   Forecast: {total_forecast:,.0f}")
    print(f"   Actual: {total_actual:,.0f}")
    print(f"   Diff: {total_forecast - total_actual:+,.0f} ({(total_forecast/total_actual - 1)*100:+.2f}%)")
    
    # Mean Absolute Error
    df_compare['ABS_ERROR'] = (df_compare['EAD_FORECAST'] - df_compare['EAD_ACTUAL']).abs()
    mae = df_compare['ABS_ERROR'].mean()
    
    # Mean Absolute Percentage Error
    df_compare['APE'] = df_compare['ABS_ERROR'] / df_compare['EAD_ACTUAL'].replace(0, np.nan) * 100
    mape = df_compare['APE'].mean()
    
    print(f"\n📊 Error Metrics:")
    print(f"   MAE: {mae:,.2f}")
    print(f"   MAPE: {mape:.2f}%")
    
    # R-squared
    ss_res = ((df_compare['EAD_FORECAST'] - df_compare['EAD_ACTUAL']) ** 2).sum()
    ss_tot = ((df_compare['EAD_ACTUAL'] - df_compare['EAD_ACTUAL'].mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    print(f"   R²: {r2:.4f}")
    
    return df_compare
