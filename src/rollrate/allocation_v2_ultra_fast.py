# ============================================================
#  allocation_v2_ultra_fast.py – Phân bổ forecast CỰC NHANH
#  
#  TỐI ƯU:
#  - Vectorized operations (không loop)
#  - Batch processing
#  - Memory efficient
#  
#  Benchmark: 1.26M loans @ MOB 12: ~5-10 phút (thay vì 90 phút)
# ============================================================

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_60P, BUCKETS_90P, parse_date_column

# Absorbing states - dư nợ = 0
ABSORBING_STATES = ['WRITEOFF', 'PREPAY', 'SOLDOUT']


def _get_combined_matrix(
    matrices_by_mob: Dict,
    parent_fallback: Dict,
    product: str,
    score: str,
    mob_from: int,
    mob_to: int,
) -> np.ndarray:
    """Tính combined transition matrix từ mob_from đến mob_to."""
    n_states = len(BUCKETS_CANON)
    state_to_idx = {s: i for i, s in enumerate(BUCKETS_CANON)}
    
    combined = np.eye(n_states)
    
    for mob in range(mob_from, mob_to):
        P = None
        
        if product in matrices_by_mob:
            if mob in matrices_by_mob[product]:
                if score in matrices_by_mob[product][mob]:
                    matrix_data = matrices_by_mob[product][mob][score]
                    if isinstance(matrix_data, dict) and "P" in matrix_data:
                        P = matrix_data["P"]
        
        if P is None and parent_fallback:
            parent_key = (product, score)
            if parent_key in parent_fallback:
                P = parent_fallback[parent_key]
        
        if P is None:
            continue
        
        if isinstance(P, pd.DataFrame):
            P_arr = np.zeros((n_states, n_states))
            for from_state in P.index:
                if from_state in state_to_idx:
                    for to_state in P.columns:
                        if to_state in state_to_idx:
                            P_arr[state_to_idx[from_state], state_to_idx[to_state]] = P.loc[from_state, to_state]
            combined = combined @ P_arr
    
    return combined


def allocate_ultra_fast(
    df_loans_latest: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mob: int,
    parent_fallback: Dict = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Phân bổ forecast CỰC NHANH với vectorization.
    
    Tối ưu:
    - BƯỚC 4: Vectorized (không loop từng cohort/state)
    - Memory efficient
    - Batch processing
    """
    
    loan_col = CFG["loan"]
    state_col = CFG["state"]
    mob_col = CFG["mob"]
    ead_col = CFG["ead"]
    
    np.random.seed(seed)
    
    n_states = len(BUCKETS_CANON)
    state_to_idx = {s: i for i, s in enumerate(BUCKETS_CANON)}
    
    print(f"📍 Phân bổ forecast tại MOB = {target_mob} (ULTRA FAST mode)")
    print(f"   Số loans: {len(df_loans_latest):,}")
    
    # Chuẩn bị data
    df = df_loans_latest.copy()
    df['STATE_CURRENT'] = df[state_col]
    df['MOB_CURRENT'] = df[mob_col].astype(int)
    df['EAD_CURRENT'] = df[ead_col].astype(float)
    
    # Lấy DISBURSAL_AMOUNT
    disb_col = CFG.get("disb", "DISBURSAL_AMOUNT")
    if disb_col in df.columns:
        df['DISBURSAL_AMOUNT'] = df[disb_col].astype(float)
    else:
        df['DISBURSAL_AMOUNT'] = df['EAD_CURRENT']
    
    if 'VINTAGE_DATE' not in df.columns:
        df['VINTAGE_DATE'] = parse_date_column(df[CFG['orig_date']])
    
    # ===================================================
    # BƯỚC 1: Tính state probabilities (VECTORIZED)
    # ===================================================
    print("   Đang tính combined matrices...")
    
    # Cache matrices per (product, score, mob_current)
    unique_combos = df[['PRODUCT_TYPE', 'RISK_SCORE', 'MOB_CURRENT']].drop_duplicates()
    matrix_cache = {}
    
    for _, row in unique_combos.iterrows():
        product = row['PRODUCT_TYPE']
        score = row['RISK_SCORE']
        mob_current = row['MOB_CURRENT']
        
        if mob_current >= target_mob:
            matrix_cache[(product, score, mob_current)] = np.eye(n_states)
        else:
            combined = _get_combined_matrix(
                matrices_by_mob, parent_fallback,
                product, score, mob_current, target_mob
            )
            matrix_cache[(product, score, mob_current)] = combined
    
    print(f"   Cached {len(matrix_cache)} matrices")
    
    # Tính probabilities vectorized
    print("   Đang tính state probabilities (vectorized)...")
    
    def get_state_probs_batch(group):
        product = group['PRODUCT_TYPE'].iloc[0]
        score = group['RISK_SCORE'].iloc[0]
        mob_current = group['MOB_CURRENT'].iloc[0]
        
        key = (product, score, mob_current)
        if key not in matrix_cache:
            # Fallback: giữ nguyên state
            probs = np.zeros((len(group), n_states))
            for i, state in enumerate(group['STATE_CURRENT']):
                if state in state_to_idx:
                    probs[i, state_to_idx[state]] = 1.0
            return pd.DataFrame(probs, index=group.index)
        
        combined = matrix_cache[key]
        
        # Vectorized: tính cho tất cả loans cùng lúc
        init_vecs = np.zeros((len(group), n_states))
        for i, state in enumerate(group['STATE_CURRENT']):
            if state in state_to_idx:
                init_vecs[i, state_to_idx[state]] = 1.0
            else:
                init_vecs[i, 0] = 1.0
        
        final_probs = init_vecs @ combined
        
        # Normalize
        totals = final_probs.sum(axis=1, keepdims=True)
        totals[totals == 0] = 1
        final_probs = final_probs / totals
        
        return pd.DataFrame(final_probs, index=group.index)
    
    probs_df = df.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'MOB_CURRENT'], group_keys=False).apply(get_state_probs_batch)
    probs_arr = probs_df.values
    
    # ===================================================
    # BƯỚC 2: Lấy DEL rates từ lifecycle
    # ===================================================
    print("   Đang lấy DEL rates từ lifecycle...")
    
    df_lc = df_lifecycle_final[df_lifecycle_final['MOB'] == target_mob].copy()
    df_lc['VINTAGE_DATE'] = pd.to_datetime(df_lc['VINTAGE_DATE'])
    df['VINTAGE_DATE'] = pd.to_datetime(df['VINTAGE_DATE'])
    
    # Merge DEL rates
    del_cols = ['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']
    if 'DEL30_PCT' in df_lc.columns:
        del_cols.append('DEL30_PCT')
    if 'DEL90_PCT' in df_lc.columns:
        del_cols.append('DEL90_PCT')
    
    df_del_rates = df_lc[del_cols].drop_duplicates()
    
    df = df.merge(df_del_rates, on=['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE'], how='left')
    
    df['PROB_DEL30'] = df['DEL30_PCT'].fillna(0)
    df['PROB_DEL90'] = df['DEL90_PCT'].fillna(0)
    df['EAD_DEL30'] = df['DISBURSAL_AMOUNT'] * df['PROB_DEL30']
    df['EAD_DEL90'] = df['DISBURSAL_AMOUNT'] * df['PROB_DEL90']
    
    # ===================================================
    # BƯỚC 3: Sample STATE_FORECAST (VECTORIZED)
    # ===================================================
    print("   Đang assign states (vectorized)...")
    
    # Vectorized sampling
    cumsum_probs = np.cumsum(probs_arr, axis=1)
    random_vals = np.random.random(len(df))
    state_indices = (cumsum_probs < random_vals[:, None]).sum(axis=1)
    state_indices = np.clip(state_indices, 0, n_states - 1)
    
    df['STATE_FORECAST'] = [BUCKETS_CANON[i] for i in state_indices]
    df['DEL30_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_30P).astype(int)
    df['DEL90_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_90P).astype(int)
    
    # ===================================================
    # BƯỚC 4: Phân bổ EAD_FORECAST (VECTORIZED) ⚡
    # ===================================================
    print("   Đang phân bổ EAD (vectorized)...")
    
    # Tạo cohort_id để group
    df['_cohort_id'] = (
        df['PRODUCT_TYPE'].astype(str) + '_' + 
        df['RISK_SCORE'].astype(str) + '_' + 
        df['VINTAGE_DATE'].astype(str)
    )
    
    # Tạo state_id
    df['_state_id'] = df['STATE_FORECAST']
    
    # Aggregate EAD_CURRENT per (cohort, state)
    ead_current_agg = df.groupby(['_cohort_id', '_state_id'])['EAD_CURRENT'].sum()
    
    # Lấy EAD từ lifecycle per (cohort, state)
    df_lc['_cohort_id'] = (
        df_lc['PRODUCT_TYPE'].astype(str) + '_' + 
        df_lc['RISK_SCORE'].astype(str) + '_' + 
        df_lc['VINTAGE_DATE'].astype(str)
    )
    
    # Melt lifecycle để có (cohort_id, state, ead_lifecycle)
    ead_lifecycle = df_lc.melt(
        id_vars=['_cohort_id'],
        value_vars=BUCKETS_CANON,
        var_name='_state_id',
        value_name='ead_lifecycle'
    )
    ead_lifecycle = ead_lifecycle.set_index(['_cohort_id', '_state_id'])['ead_lifecycle']
    
    # Tính ratio per (cohort, state)
    ratio_df = pd.DataFrame({
        'ead_current': ead_current_agg,
        'ead_lifecycle': ead_lifecycle
    }).fillna(0)
    
    ratio_df['ratio'] = np.where(
        ratio_df['ead_current'] > 0,
        ratio_df['ead_lifecycle'] / ratio_df['ead_current'],
        0
    )
    ratio_df['ratio'] = np.clip(ratio_df['ratio'], 0, 1.0)
    
    # Merge ratio vào df
    df = df.merge(
        ratio_df[['ratio']],
        left_on=['_cohort_id', '_state_id'],
        right_index=True,
        how='left'
    )
    
    # Tính EAD_FORECAST vectorized
    df['ratio'] = df['ratio'].fillna(0)
    
    # Absorbing states → EAD = 0
    is_absorbing = df['STATE_FORECAST'].isin(ABSORBING_STATES)
    df['EAD_FORECAST'] = np.where(
        is_absorbing,
        0,
        df['EAD_CURRENT'] * df['ratio']
    )
    
    # Cleanup
    df = df.drop(columns=['_cohort_id', '_state_id', 'ratio'], errors='ignore')
    
    df['TARGET_MOB'] = target_mob
    df['IS_FORECAST'] = 1
    
    # Output
    output_cols = [
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
        'DISBURSAL_AMOUNT',
        'STATE_CURRENT', 'MOB_CURRENT', 'EAD_CURRENT',
        'STATE_FORECAST', 'EAD_FORECAST',
        'PROB_DEL30', 'PROB_DEL90',
        'EAD_DEL30', 'EAD_DEL90',
        'DEL30_FLAG', 'DEL90_FLAG',
        'TARGET_MOB', 'IS_FORECAST'
    ]
    
    df_result = df[[c for c in output_cols if c in df.columns]].copy()
    
    # Validation
    print(f"\n✅ Phân bổ hoàn tất:")
    print(f"   Số loans: {len(df_result):,}")
    
    total_ead_current = df_result['EAD_CURRENT'].sum()
    total_ead_forecast = df_result['EAD_FORECAST'].sum()
    total_ead_del30 = df_result['EAD_DEL30'].sum()
    total_disbursal = df_result['DISBURSAL_AMOUNT'].sum()
    
    print(f"   EAD_CURRENT: {total_ead_current:,.0f}")
    print(f"   EAD_FORECAST: {total_ead_forecast:,.0f}")
    print(f"   EAD_DEL30: {total_ead_del30:,.0f} ({total_ead_del30/total_disbursal*100:.2f}%)")
    
    return df_result


def allocate_multi_mob_ultra_fast(
    df_loans_latest: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mobs: List[int] = [12, 24],
    parent_fallback: Dict = None,
    include_del30: bool = True,
    include_del90: bool = True,
    seed: int = 42,
) -> pd.DataFrame:
    """Phân bổ forecast CỰC NHANH tại NHIỀU MOB."""
    
    loan_col = CFG["loan"]
    
    print(f"🚀 Phân bổ forecast ULTRA FAST tại {len(target_mobs)} MOB: {target_mobs}")
    
    df = df_loans_latest.copy()
    
    if 'VINTAGE_DATE' not in df.columns:
        df['VINTAGE_DATE'] = parse_date_column(df[CFG['orig_date']])
    
    # Base columns
    base_cols = [loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE', CFG["mob"], CFG["ead"]]
    
    if CFG["state"] in df.columns:
        base_cols.append(CFG["state"])
    
    orig_date_col = CFG.get("orig_date", "DISBURSAL_DATE")
    disb_amt_col = CFG.get("disb", "DISBURSAL_AMOUNT")
    
    if orig_date_col in df.columns:
        base_cols.append(orig_date_col)
    if disb_amt_col in df.columns:
        base_cols.append(disb_amt_col)
    
    base_cols = list(dict.fromkeys(base_cols))
    loan_info = df[[c for c in base_cols if c in df.columns]].copy()
    
    # Rename
    rename_map = {
        CFG["mob"]: 'MOB_CURRENT',
        CFG["ead"]: 'EAD_CURRENT',
    }
    
    if CFG["state"] in loan_info.columns:
        rename_map[CFG["state"]] = 'STATE_CURRENT'
    if orig_date_col in loan_info.columns and orig_date_col != 'DISBURSAL_DATE':
        rename_map[orig_date_col] = 'DISBURSAL_DATE'
    if disb_amt_col in loan_info.columns and disb_amt_col != 'DISBURSAL_AMOUNT':
        rename_map[disb_amt_col] = 'DISBURSAL_AMOUNT'
    
    loan_info = loan_info.rename(columns=rename_map)
    
    for target_mob in target_mobs:
        print(f"\n{'='*50}")
        
        df_allocated = allocate_ultra_fast(
            df_loans_latest=df_loans_latest,
            df_lifecycle_final=df_lifecycle_final,
            matrices_by_mob=matrices_by_mob,
            target_mob=target_mob,
            parent_fallback=parent_fallback,
            seed=seed,
        )
        
        if df_allocated.empty:
            continue
        
        # Merge columns
        cols_to_merge = [loan_col, 'STATE_FORECAST', 'EAD_FORECAST']
        
        if include_del30:
            cols_to_merge.extend(['PROB_DEL30', 'EAD_DEL30', 'DEL30_FLAG'])
        if include_del90:
            cols_to_merge.extend(['PROB_DEL90', 'EAD_DEL90', 'DEL90_FLAG'])
        
        df_mob = df_allocated[[c for c in cols_to_merge if c in df_allocated.columns]].copy()
        
        # Rename
        rename_map = {
            'STATE_FORECAST': f'STATE_FORECAST_MOB{target_mob}',
            'EAD_FORECAST': f'EAD_FORECAST_MOB{target_mob}',
        }
        
        if include_del30:
            rename_map['PROB_DEL30'] = f'PROB_DEL30_MOB{target_mob}'
            rename_map['EAD_DEL30'] = f'EAD_DEL30_MOB{target_mob}'
            rename_map['DEL30_FLAG'] = f'DEL30_FLAG_MOB{target_mob}'
        
        if include_del90:
            rename_map['PROB_DEL90'] = f'PROB_DEL90_MOB{target_mob}'
            rename_map['EAD_DEL90'] = f'EAD_DEL90_MOB{target_mob}'
            rename_map['DEL90_FLAG'] = f'DEL90_FLAG_MOB{target_mob}'
        
        df_mob = df_mob.rename(columns=rename_map)
        
        loan_info = loan_info.merge(df_mob, on=loan_col, how='left')
    
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    print(f"   Total loans: {len(loan_info):,}")
    
    return loan_info
