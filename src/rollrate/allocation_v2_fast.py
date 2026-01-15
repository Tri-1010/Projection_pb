# ============================================================
#  allocation_v2_fast.py – Phân bổ forecast NHANH (vectorized)
#  
#  OUTPUT:
#  - STATE_FORECAST: State dự báo (sampled từ xác suất)
#  - EAD_FORECAST: Dư nợ dự báo còn lại
#  - PROB_DEL30: Xác suất loan sẽ ở DEL30+ tại MOB đó
#  - PROB_DEL90: Xác suất loan sẽ ở DEL90+ tại MOB đó
#  - EAD_DEL30: Dư nợ dự kiến thuộc nhóm DEL30+ = EAD_CURRENT × PROB_DEL30
#  - EAD_DEL90: Dư nợ dự kiến thuộc nhóm DEL90+ = EAD_CURRENT × PROB_DEL90
# ============================================================

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_60P, BUCKETS_90P

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


def allocate_fast(
    df_loans_latest: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    matrices_by_mob: Dict,
    target_mob: int,
    parent_fallback: Dict = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Phân bổ forecast NHANH.
    
    OUTPUT columns:
    - STATE_FORECAST: State dự báo (sampled)
    - EAD_FORECAST: Dư nợ dự báo còn lại
    - PROB_DEL30: Xác suất ở DEL30+
    - PROB_DEL90: Xác suất ở DEL90+
    - EAD_DEL30: EAD_CURRENT × PROB_DEL30 (dư nợ dự kiến thuộc DEL30+)
    - EAD_DEL90: EAD_CURRENT × PROB_DEL90 (dư nợ dự kiến thuộc DEL90+)
    """
    
    loan_col = CFG["loan"]
    state_col = CFG["state"]
    mob_col = CFG["mob"]
    ead_col = CFG["ead"]
    
    np.random.seed(seed)
    
    n_states = len(BUCKETS_CANON)
    state_to_idx = {s: i for i, s in enumerate(BUCKETS_CANON)}
    
    # Index của các states thuộc DEL30+, DEL90+
    del30_idx = [state_to_idx[s] for s in BUCKETS_30P if s in state_to_idx]
    del90_idx = [state_to_idx[s] for s in BUCKETS_90P if s in state_to_idx]
    
    print(f"📍 Phân bổ forecast tại MOB = {target_mob} (FAST mode)")
    print(f"   Số loans: {len(df_loans_latest):,}")
    
    # Chuẩn bị data
    df = df_loans_latest.copy()
    df['STATE_CURRENT'] = df[state_col]
    df['MOB_CURRENT'] = df[mob_col].astype(int)
    df['EAD_CURRENT'] = df[ead_col].astype(float)
    
    if 'VINTAGE_DATE' not in df.columns:
        df['VINTAGE_DATE'] = df[CFG['orig_date']].apply(lambda x: x.replace(day=1))
    
    # ===================================================
    # BƯỚC 1: Tính state probabilities từ transition matrix
    # ===================================================
    print("   Đang tính combined matrices...")
    matrix_cache = {}
    
    unique_combos = df.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'MOB_CURRENT']).size().reset_index()[['PRODUCT_TYPE', 'RISK_SCORE', 'MOB_CURRENT']]
    
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
    
    print(f"   Cached {len(matrix_cache)} combined matrices")
    print("   Đang tính state probabilities...")
    
    def get_state_probs(row):
        product = row['PRODUCT_TYPE']
        score = row['RISK_SCORE']
        mob_current = row['MOB_CURRENT']
        state_current = row['STATE_CURRENT']
        
        key = (product, score, mob_current)
        if key not in matrix_cache:
            probs = np.zeros(n_states)
            if state_current in state_to_idx:
                probs[state_to_idx[state_current]] = 1.0
            return probs
        
        combined = matrix_cache[key]
        
        init_vec = np.zeros(n_states)
        if state_current in state_to_idx:
            init_vec[state_to_idx[state_current]] = 1.0
        else:
            init_vec[0] = 1.0
        
        final_probs = init_vec @ combined
        
        total = final_probs.sum()
        if total > 0:
            final_probs = final_probs / total
        
        return final_probs
    
    probs_list = df.apply(get_state_probs, axis=1).tolist()
    probs_arr = np.array(probs_list)
    
    # ===================================================
    # BƯỚC 2: Tính PROB_DEL30, PROB_DEL90
    # ===================================================
    print("   Đang tính xác suất DEL...")
    
    # PROB_DEL30 = sum(prob[state] for state in BUCKETS_30P)
    df['PROB_DEL30'] = probs_arr[:, del30_idx].sum(axis=1) if del30_idx else 0
    df['PROB_DEL90'] = probs_arr[:, del90_idx].sum(axis=1) if del90_idx else 0
    
    # EAD_DEL30 = EAD_CURRENT × PROB_DEL30
    df['EAD_DEL30'] = df['EAD_CURRENT'] * df['PROB_DEL30']
    df['EAD_DEL90'] = df['EAD_CURRENT'] * df['PROB_DEL90']
    
    # ===================================================
    # BƯỚC 3: Sample STATE_FORECAST
    # ===================================================
    print("   Đang assign states...")
    
    def sample_state(probs):
        if probs.sum() == 0:
            return 'DPD0'
        probs = probs / probs.sum()
        return np.random.choice(BUCKETS_CANON, p=probs)
    
    df['STATE_FORECAST'] = [sample_state(p) for p in probs_arr]
    
    # DEL flags (0/1) dựa trên STATE_FORECAST
    df['DEL30_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_30P).astype(int)
    df['DEL90_FLAG'] = df['STATE_FORECAST'].isin(BUCKETS_90P).astype(int)
    
    # ===================================================
    # BƯỚC 4: Phân bổ EAD_FORECAST theo STATE_FORECAST
    # ===================================================
    print("   Đang phân bổ EAD theo state...")
    
    df_lc = df_lifecycle_final[df_lifecycle_final['MOB'] == target_mob].copy()
    
    df['EAD_FORECAST'] = 0.0
    
    for (product, score, vintage), grp in df.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']):
        lc_mask = (
            (df_lc['PRODUCT_TYPE'] == product) &
            (df_lc['RISK_SCORE'] == score) &
            (df_lc['VINTAGE_DATE'] == vintage)
        )
        lc_row = df_lc[lc_mask]
        
        if lc_row.empty:
            continue
        
        lc_row = lc_row.iloc[0]
        total_ead_current = grp['EAD_CURRENT'].sum()
        
        if total_ead_current <= 0:
            continue
        
        for state in BUCKETS_CANON:
            ead_lifecycle_state = lc_row.get(state, 0)
            if pd.isna(ead_lifecycle_state):
                ead_lifecycle_state = 0
            
            state_mask = (
                (df['PRODUCT_TYPE'] == product) &
                (df['RISK_SCORE'] == score) &
                (df['VINTAGE_DATE'] == vintage) &
                (df['STATE_FORECAST'] == state)
            )
            
            if state_mask.sum() == 0:
                continue
            
            ead_current_state = df.loc[state_mask, 'EAD_CURRENT'].sum()
            
            if ead_current_state <= 0:
                continue
            
            if state in ABSORBING_STATES:
                df.loc[state_mask, 'EAD_FORECAST'] = 0
            else:
                ratio = ead_lifecycle_state / ead_current_state
                ratio = min(ratio, 1.0)
                df.loc[state_mask, 'EAD_FORECAST'] = df.loc[state_mask, 'EAD_CURRENT'] * ratio
    
    df['TARGET_MOB'] = target_mob
    df['IS_FORECAST'] = 1
    
    # Output columns
    output_cols = [
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
        'STATE_CURRENT', 'MOB_CURRENT', 'EAD_CURRENT',
        'STATE_FORECAST', 'EAD_FORECAST',
        'PROB_DEL30', 'PROB_DEL90',
        'EAD_DEL30', 'EAD_DEL90',
        'DEL30_FLAG', 'DEL90_FLAG',
        'TARGET_MOB', 'IS_FORECAST'
    ]
    
    df_result = df[[c for c in output_cols if c in df.columns]].copy()
    
    # ===================================================
    # VALIDATION
    # ===================================================
    print(f"\n✅ Phân bổ hoàn tất:")
    print(f"   Số loans: {len(df_result):,}")
    
    total_ead_current = df_result['EAD_CURRENT'].sum()
    total_ead_forecast = df_result['EAD_FORECAST'].sum()
    total_ead_del30 = df_result['EAD_DEL30'].sum()
    total_ead_del90 = df_result['EAD_DEL90'].sum()
    
    print(f"\n   EAD Summary:")
    print(f"      EAD_CURRENT: {total_ead_current:,.0f}")
    print(f"      EAD_FORECAST: {total_ead_forecast:,.0f} (giảm {(1-total_ead_forecast/total_ead_current)*100:.2f}%)")
    print(f"      EAD_DEL30: {total_ead_del30:,.0f} ({total_ead_del30/total_ead_current*100:.2f}% of current)")
    print(f"      EAD_DEL90: {total_ead_del90:,.0f} ({total_ead_del90/total_ead_current*100:.2f}% of current)")
    
    print(f"\n   DEL Probability (avg):")
    print(f"      PROB_DEL30: {df_result['PROB_DEL30'].mean()*100:.2f}%")
    print(f"      PROB_DEL90: {df_result['PROB_DEL90'].mean()*100:.2f}%")
    
    return df_result


def allocate_multi_mob_fast(
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
    Phân bổ forecast tại NHIỀU MOB.
    
    OUTPUT columns per MOB:
    - STATE_FORECAST_MOB{X}: State dự báo
    - EAD_FORECAST_MOB{X}: Dư nợ dự báo còn lại
    - PROB_DEL30_MOB{X}: Xác suất ở DEL30+
    - PROB_DEL90_MOB{X}: Xác suất ở DEL90+
    - EAD_DEL30_MOB{X}: Dư nợ dự kiến thuộc DEL30+
    - EAD_DEL90_MOB{X}: Dư nợ dự kiến thuộc DEL90+
    - DEL30_FLAG_MOB{X}: 1 nếu STATE_FORECAST ∈ DEL30+
    - DEL90_FLAG_MOB{X}: 1 nếu STATE_FORECAST ∈ DEL90+
    """
    
    loan_col = CFG["loan"]
    
    print(f"🎯 Phân bổ forecast tại {len(target_mobs)} MOB: {target_mobs}")
    
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
        
        df_allocated = allocate_fast(
            df_loans_latest=df_loans_latest,
            df_lifecycle_final=df_lifecycle_final,
            matrices_by_mob=matrices_by_mob,
            target_mob=target_mob,
            parent_fallback=parent_fallback,
            seed=seed,
        )
        
        if df_allocated.empty:
            continue
        
        # Columns to merge
        cols_to_merge = [loan_col, 'STATE_FORECAST', 'EAD_FORECAST']
        
        if include_del30:
            cols_to_merge.extend(['PROB_DEL30', 'EAD_DEL30', 'DEL30_FLAG'])
        if include_del90:
            cols_to_merge.extend(['PROB_DEL90', 'EAD_DEL90', 'DEL90_FLAG'])
        
        df_mob = df_allocated[[c for c in cols_to_merge if c in df_allocated.columns]].copy()
        
        # Rename với suffix _MOB{X}
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
    
    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    print(f"   Total loans: {len(loan_info):,}")
    print(f"   EAD_CURRENT: {loan_info['EAD_CURRENT'].sum():,.0f}")
    
    for target_mob in target_mobs:
        ead_col = f'EAD_FORECAST_MOB{target_mob}'
        ead_del30_col = f'EAD_DEL30_MOB{target_mob}'
        ead_del90_col = f'EAD_DEL90_MOB{target_mob}'
        prob_del30_col = f'PROB_DEL30_MOB{target_mob}'
        prob_del90_col = f'PROB_DEL90_MOB{target_mob}'
        
        print(f"\n   MOB {target_mob}:")
        
        if ead_col in loan_info.columns:
            ead_forecast = loan_info[ead_col].sum()
            print(f"      EAD_FORECAST: {ead_forecast:,.0f}")
        
        if ead_del30_col in loan_info.columns:
            ead_del30 = loan_info[ead_del30_col].sum()
            print(f"      EAD_DEL30: {ead_del30:,.0f}")
        
        if ead_del90_col in loan_info.columns:
            ead_del90 = loan_info[ead_del90_col].sum()
            print(f"      EAD_DEL90: {ead_del90:,.0f}")
        
        if prob_del30_col in loan_info.columns:
            avg_prob_del30 = loan_info[prob_del30_col].mean() * 100
            print(f"      Avg PROB_DEL30: {avg_prob_del30:.2f}%")
        
        if prob_del90_col in loan_info.columns:
            avg_prob_del90 = loan_info[prob_del90_col].mean() * 100
            print(f"      Avg PROB_DEL90: {avg_prob_del90:.2f}%")
    
    return loan_info


# Alias
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
    """Alias cho allocate_multi_mob_fast."""
    return allocate_multi_mob_fast(
        df_loans_latest=df_loans_latest,
        df_lifecycle_final=df_lifecycle_final,
        matrices_by_mob=matrices_by_mob,
        target_mobs=target_mobs,
        parent_fallback=parent_fallback,
        include_del30=include_del30,
        include_del90=include_del90,
        seed=seed,
    )
