# ============================================================
#  allocation_v2_fast.py – Phân bổ forecast NHANH (vectorized)
#  
#  Tối ưu: Thay vì loop từng loan, dùng groupby + vectorized ops
# ============================================================

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_60P, BUCKETS_90P


def _get_combined_matrix(
    matrices_by_mob: Dict,
    parent_fallback: Dict,
    product: str,
    score: str,
    mob_from: int,
    mob_to: int,
) -> np.ndarray:
    """
    Tính combined transition matrix từ mob_from đến mob_to.
    Trả về numpy array (n_states x n_states).
    """
    n_states = len(BUCKETS_CANON)
    state_to_idx = {s: i for i, s in enumerate(BUCKETS_CANON)}
    
    # Identity matrix
    combined = np.eye(n_states)
    
    for mob in range(mob_from, mob_to):
        # Lấy matrix tại MOB này
        P = None
        
        if product in matrices_by_mob:
            if mob in matrices_by_mob[product]:
                if score in matrices_by_mob[product][mob]:
                    matrix_data = matrices_by_mob[product][mob][score]
                    if isinstance(matrix_data, dict) and "P" in matrix_data:
                        P = matrix_data["P"]
        
        # Fallback
        if P is None and parent_fallback:
            parent_key = (product, score)
            if parent_key in parent_fallback:
                P = parent_fallback[parent_key]
        
        if P is None:
            continue
        
        # Convert DataFrame to numpy array
        if isinstance(P, pd.DataFrame):
            P_arr = np.zeros((n_states, n_states))
            for from_state in P.index:
                if from_state in state_to_idx:
                    for to_state in P.columns:
                        if to_state in state_to_idx:
                            P_arr[state_to_idx[from_state], state_to_idx[to_state]] = P.loc[from_state, to_state]
            
            # Nhân ma trận
            combined = combined @ P_arr
    
    return combined


def allocate_fast(
    df_loans_latest: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mob: int,
    parent_fallback: Dict = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Phân bổ forecast NHANH bằng vectorized operations.
    
    Thay vì loop từng loan, group theo (product, score, state, mob)
    và apply transition matrix một lần cho cả group.
    """
    
    loan_col = CFG["loan"]
    state_col = CFG["state"]
    mob_col = CFG["mob"]
    ead_col = CFG["ead"]
    
    np.random.seed(seed)
    
    n_states = len(BUCKETS_CANON)
    state_to_idx = {s: i for i, s in enumerate(BUCKETS_CANON)}
    idx_to_state = {i: s for s, i in state_to_idx.items()}
    
    print(f"📍 Phân bổ forecast tại MOB = {target_mob} (FAST mode)")
    print(f"   Số loans: {len(df_loans_latest):,}")
    
    # Chuẩn bị data
    df = df_loans_latest.copy()
    df['STATE_CURRENT'] = df[state_col]
    df['MOB_CURRENT'] = df[mob_col].astype(int)
    df['EAD_CURRENT'] = df[ead_col].astype(float)
    
    # Thêm VINTAGE_DATE nếu chưa có
    if 'VINTAGE_DATE' not in df.columns:
        df['VINTAGE_DATE'] = df[CFG['orig_date']].apply(lambda x: x.replace(day=1))
    
    # Cache combined matrices
    print("   Đang tính combined matrices...")
    matrix_cache = {}
    
    # Lấy unique combinations
    unique_combos = df.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'MOB_CURRENT']).size().reset_index()[['PRODUCT_TYPE', 'RISK_SCORE', 'MOB_CURRENT']]
    
    for _, row in unique_combos.iterrows():
        product = row['PRODUCT_TYPE']
        score = row['RISK_SCORE']
        mob_current = row['MOB_CURRENT']
        
        if mob_current >= target_mob:
            # Không cần forecast
            matrix_cache[(product, score, mob_current)] = np.eye(n_states)
        else:
            combined = _get_combined_matrix(
                matrices_by_mob, parent_fallback,
                product, score, mob_current, target_mob
            )
            matrix_cache[(product, score, mob_current)] = combined
    
    print(f"   Cached {len(matrix_cache)} combined matrices")
    
    # Tính state probabilities cho mỗi loan
    print("   Đang tính state probabilities...")
    
    def get_state_probs(row):
        """Lấy probability vector cho loan."""
        product = row['PRODUCT_TYPE']
        score = row['RISK_SCORE']
        mob_current = row['MOB_CURRENT']
        state_current = row['STATE_CURRENT']
        
        # Lấy combined matrix
        key = (product, score, mob_current)
        if key not in matrix_cache:
            # Fallback: giữ nguyên state
            probs = np.zeros(n_states)
            if state_current in state_to_idx:
                probs[state_to_idx[state_current]] = 1.0
            return probs
        
        combined = matrix_cache[key]
        
        # Initial state vector
        init_vec = np.zeros(n_states)
        if state_current in state_to_idx:
            init_vec[state_to_idx[state_current]] = 1.0
        else:
            init_vec[0] = 1.0  # Default to DPD0
        
        # Final probabilities
        final_probs = init_vec @ combined
        
        # Normalize
        total = final_probs.sum()
        if total > 0:
            final_probs = final_probs / total
        
        return final_probs
    
    # Apply vectorized (vẫn cần apply nhưng nhanh hơn nhiều)
    probs_list = df.apply(get_state_probs, axis=1).tolist()
    probs_arr = np.array(probs_list)
    
    print("   Đang assign states...")
    
    # Sample states theo probabilities
    def sample_state(probs):
        """Sample state từ probability vector."""
        if probs.sum() == 0:
            return 'DPD0'
        # Normalize
        probs = probs / probs.sum()
        return np.random.choice(BUCKETS_CANON, p=probs)
    
    df['STATE_FORECAST'] = [sample_state(p) for p in probs_arr]
    
    # Tính EAD forecast
    # Absorbing states: PREPAY, WRITEOFF, SOLDOUT
    absorbing_idx = [state_to_idx.get(s, -1) for s in ['PREPAY', 'WRITEOFF', 'SOLDOUT']]
    absorbing_idx = [i for i in absorbing_idx if i >= 0]
    
    absorbing_probs = probs_arr[:, absorbing_idx].sum(axis=1) if absorbing_idx else np.zeros(len(df))
    df['EAD_FORECAST'] = df['EAD_CURRENT'] * (1 - absorbing_probs)
    
    # Lưu state probs (optional, có thể bỏ để tiết kiệm memory)
    # df['STATE_PROBS'] = [dict(zip(BUCKETS_CANON, p)) for p in probs_arr]
    
    df['TARGET_MOB'] = target_mob
    df['IS_FORECAST'] = 1
    
    # Select output columns
    output_cols = [
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
        'STATE_CURRENT', 'MOB_CURRENT', 'EAD_CURRENT',
        'STATE_FORECAST', 'EAD_FORECAST', 'TARGET_MOB', 'IS_FORECAST'
    ]
    
    df_result = df[[c for c in output_cols if c in df.columns]].copy()
    
    # Stats
    print(f"\n✅ Phân bổ hoàn tất:")
    print(f"   Số loans: {len(df_result):,}")
    
    same_state = (df_result['STATE_CURRENT'] == df_result['STATE_FORECAST']).sum()
    print(f"   Giữ nguyên state: {same_state:,} ({same_state/len(df_result)*100:.1f}%)")
    
    del30_count = df_result['STATE_FORECAST'].isin(BUCKETS_30P).sum()
    del90_count = df_result['STATE_FORECAST'].isin(BUCKETS_90P).sum()
    print(f"   DEL30+ forecast: {del30_count:,} ({del30_count/len(df_result)*100:.2f}%)")
    print(f"   DEL90+ forecast: {del90_count:,} ({del90_count/len(df_result)*100:.2f}%)")
    
    return df_result


def allocate_multi_mob_fast(
    df_loans_latest: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mobs: List[int] = [12, 24],
    parent_fallback: Dict = None,
    include_del30: bool = True,
    include_del90: bool = True,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Phân bổ forecast tại NHIỀU MOB (FAST mode).
    """
    
    loan_col = CFG["loan"]
    
    print(f"🎯 Phân bổ forecast tại {len(target_mobs)} MOB: {target_mobs}")
    print(f"   (FAST mode - vectorized)")
    
    # Lấy thông tin cơ bản
    df = df_loans_latest.copy()
    
    # Thêm VINTAGE_DATE nếu chưa có
    if 'VINTAGE_DATE' not in df.columns:
        df['VINTAGE_DATE'] = df[CFG['orig_date']].apply(lambda x: x.replace(day=1))
    
    loan_info = df[[
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
        CFG["mob"], CFG["ead"], CFG["state"]
    ]].copy()
    
    loan_info = loan_info.rename(columns={
        CFG["mob"]: 'MOB_CURRENT',
        CFG["ead"]: 'EAD_CURRENT',
        CFG["state"]: 'STATE_CURRENT',
    })
    
    # Loop qua từng MOB
    for target_mob in target_mobs:
        print(f"\n{'='*50}")
        
        df_allocated = allocate_fast(
            df_loans_latest=df_loans_latest,
            matrices_by_mob=matrices_by_mob,
            target_mob=target_mob,
            parent_fallback=parent_fallback,
            seed=seed,
        )
        
        if df_allocated.empty:
            continue
        
        # Merge kết quả
        df_mob = df_allocated[[loan_col, 'STATE_FORECAST', 'EAD_FORECAST']].copy()
        df_mob = df_mob.rename(columns={
            'STATE_FORECAST': f'STATE_FORECAST_MOB{target_mob}',
            'EAD_FORECAST': f'EAD_FORECAST_MOB{target_mob}',
        })
        
        # Add DEL flags
        if include_del30:
            df_mob[f'DEL30_FLAG_MOB{target_mob}'] = df_allocated['STATE_FORECAST'].isin(BUCKETS_30P).astype(int).values
        if include_del90:
            df_mob[f'DEL90_FLAG_MOB{target_mob}'] = df_allocated['STATE_FORECAST'].isin(BUCKETS_90P).astype(int).values
        
        loan_info = loan_info.merge(df_mob, on=loan_col, how='left')
    
    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    for target_mob in target_mobs:
        del90_col = f'DEL90_FLAG_MOB{target_mob}'
        if del90_col in loan_info.columns:
            del90_count = loan_info[del90_col].sum()
            del90_pct = del90_count / len(loan_info) * 100
            print(f"   MOB {target_mob}: DEL90+ = {del90_count:,} ({del90_pct:.2f}%)")
    
    return loan_info


def allocate_multi_mob_with_scaling_fast(
    df_loans_latest: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mobs: List[int] = [12, 24],
    parent_fallback: Dict = None,
    include_del30: bool = True,
    include_del90: bool = True,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Phân bổ forecast với scaling (FAST mode).
    """
    
    loan_col = CFG["loan"]
    
    print(f"🎯 Phân bổ forecast tại {len(target_mobs)} MOB: {target_mobs}")
    print(f"   (FAST mode + scaling)")
    
    # Lấy thông tin cơ bản
    df = df_loans_latest.copy()
    
    if 'VINTAGE_DATE' not in df.columns:
        df['VINTAGE_DATE'] = df[CFG['orig_date']].apply(lambda x: x.replace(day=1))
    
    loan_info = df[[
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
        CFG["mob"], CFG["ead"], CFG["state"]
    ]].copy()
    
    loan_info = loan_info.rename(columns={
        CFG["mob"]: 'MOB_CURRENT',
        CFG["ead"]: 'EAD_CURRENT',
        CFG["state"]: 'STATE_CURRENT',
    })
    
    for target_mob in target_mobs:
        print(f"\n{'='*50}")
        
        # Allocation
        df_allocated = allocate_fast(
            df_loans_latest=df_loans_latest,
            matrices_by_mob=matrices_by_mob,
            target_mob=target_mob,
            parent_fallback=parent_fallback,
            seed=seed,
        )
        
        if df_allocated.empty:
            continue
        
        # Scaling
        print("   Đang scale EAD...")
        df_lc = df_lifecycle_final[df_lifecycle_final['MOB'] == target_mob].copy()
        
        if not df_lc.empty:
            # Tính scaling factor per cohort × state
            scaling_factors = {}
            
            for _, row_lc in df_lc.iterrows():
                product = row_lc['PRODUCT_TYPE']
                score = row_lc['RISK_SCORE']
                vintage = row_lc['VINTAGE_DATE']
                
                for state in BUCKETS_CANON:
                    ead_lifecycle = row_lc.get(state, 0)
                    if pd.isna(ead_lifecycle):
                        ead_lifecycle = 0
                    
                    mask = (
                        (df_allocated['PRODUCT_TYPE'] == product) &
                        (df_allocated['RISK_SCORE'] == score) &
                        (df_allocated['VINTAGE_DATE'] == vintage) &
                        (df_allocated['STATE_FORECAST'] == state)
                    )
                    ead_allocated = df_allocated.loc[mask, 'EAD_FORECAST'].sum()
                    
                    factor = ead_lifecycle / ead_allocated if ead_allocated > 0 else 1.0
                    scaling_factors[(product, score, vintage, state)] = factor
            
            # Apply scaling
            def get_factor(row):
                key = (row['PRODUCT_TYPE'], row['RISK_SCORE'], row['VINTAGE_DATE'], row['STATE_FORECAST'])
                return scaling_factors.get(key, 1.0)
            
            df_allocated['SCALING_FACTOR'] = df_allocated.apply(get_factor, axis=1)
            df_allocated['EAD_FORECAST_SCALED'] = df_allocated['EAD_FORECAST'] * df_allocated['SCALING_FACTOR']
        else:
            df_allocated['SCALING_FACTOR'] = 1.0
            df_allocated['EAD_FORECAST_SCALED'] = df_allocated['EAD_FORECAST']
        
        # Merge
        df_mob = df_allocated[[loan_col, 'STATE_FORECAST', 'EAD_FORECAST', 'EAD_FORECAST_SCALED', 'SCALING_FACTOR']].copy()
        df_mob = df_mob.rename(columns={
            'STATE_FORECAST': f'STATE_FORECAST_MOB{target_mob}',
            'EAD_FORECAST': f'EAD_FORECAST_MOB{target_mob}',
            'EAD_FORECAST_SCALED': f'EAD_SCALED_MOB{target_mob}',
            'SCALING_FACTOR': f'SCALING_FACTOR_MOB{target_mob}',
        })
        
        if include_del30:
            df_mob[f'DEL30_FLAG_MOB{target_mob}'] = df_allocated['STATE_FORECAST'].isin(BUCKETS_30P).astype(int).values
        if include_del90:
            df_mob[f'DEL90_FLAG_MOB{target_mob}'] = df_allocated['STATE_FORECAST'].isin(BUCKETS_90P).astype(int).values
        
        loan_info = loan_info.merge(df_mob, on=loan_col, how='left')
    
    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    for target_mob in target_mobs:
        del90_col = f'DEL90_FLAG_MOB{target_mob}'
        ead_col = f'EAD_FORECAST_MOB{target_mob}'
        ead_scaled_col = f'EAD_SCALED_MOB{target_mob}'
        
        if del90_col in loan_info.columns:
            del90_count = loan_info[del90_col].sum()
            del90_pct = del90_count / len(loan_info) * 100
            print(f"   MOB {target_mob}:")
            print(f"      DEL90+: {del90_count:,} ({del90_pct:.2f}%)")
            
            if ead_col in loan_info.columns and ead_scaled_col in loan_info.columns:
                ead_raw = loan_info[ead_col].sum()
                ead_scaled = loan_info[ead_scaled_col].sum()
                print(f"      EAD raw: {ead_raw:,.0f}")
                print(f"      EAD scaled: {ead_scaled:,.0f}")
    
    return loan_info
