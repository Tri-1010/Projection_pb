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
