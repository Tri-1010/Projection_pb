# ============================================================
#  allocation_v2_optimized.py – Phân bổ forecast TỐI ƯU
#  
#  TỐI ƯU:
#  - Cohort có actual @ target_mob: Lấy thực tế từ df_raw
#  - Cohort chỉ có forecast @ target_mob: Mới allocate
#  
#  => Giảm thời gian chạy, tăng độ chính xác
# ============================================================

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_60P, BUCKETS_90P, parse_date_column

# Import hàm allocate_fast từ allocation_v2_fast
from src.rollrate.allocation_v2_fast import allocate_fast


def allocate_multi_mob_optimized(
    df_raw: pd.DataFrame,
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
    Phân bổ forecast TỐI ƯU tại NHIỀU MOB.
    
    TỐI ƯU:
    - Cohort có actual @ target_mob: Lấy thực tế từ df_raw
    - Cohort chỉ có forecast @ target_mob: Mới allocate
    
    Parameters
    ----------
    df_raw : pd.DataFrame
        Data gốc đầy đủ (có cả actual data)
    df_loans_latest : pd.DataFrame
        Snapshot loans mới nhất
    df_lifecycle_final : pd.DataFrame
        Lifecycle forecast (có cột IS_FORECAST)
    matrices_by_mob : Dict
        Transition matrices
    target_mobs : List[int]
        Các MOB cần forecast
    parent_fallback : Dict
        Fallback matrices
    include_del30 : bool
        Có tính DEL30 không
    include_del90 : bool
        Có tính DEL90 không
    seed : int
        Random seed
    
    Returns
    -------
    pd.DataFrame
        Loan-level forecast với actual + forecast
    """
    
    loan_col = CFG["loan"]
    
    print(f"🎯 Phân bổ forecast TỐI ƯU tại {len(target_mobs)} MOB: {target_mobs}")
    print(f"   📋 CFG mapping:")
    print(f"      loan: {CFG['loan']}")
    print(f"      state: {CFG['state']}")
    print(f"      ead: {CFG['ead']}")
    print(f"      mob: {CFG['mob']}")
    print(f"      orig_date: {CFG.get('orig_date', 'DISBURSAL_DATE')}")
    
    df = df_loans_latest.copy()
    
    if 'VINTAGE_DATE' not in df.columns:
        df['VINTAGE_DATE'] = parse_date_column(df[CFG['orig_date']])
    
    # Các cột cần lấy từ df_loans_latest
    base_cols = [
        loan_col, 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE',
        CFG["mob"], CFG["ead"]
    ]
    
    # Thêm STATE nếu có (không bắt buộc)
    if CFG["state"] in df.columns:
        base_cols.append(CFG["state"])
    
    # Thêm DISBURSAL_DATE, DISBURSAL_AMOUNT nếu có
    orig_date_col = CFG.get("orig_date", "DISBURSAL_DATE")
    disb_amt_col = CFG.get("disb", "DISBURSAL_AMOUNT")
    
    if orig_date_col in df.columns:
        base_cols.append(orig_date_col)
    if disb_amt_col in df.columns:
        base_cols.append(disb_amt_col)
    
    # Loại bỏ duplicate columns
    base_cols = list(dict.fromkeys(base_cols))
    
    loan_info = df[[c for c in base_cols if c in df.columns]].copy()
    
    # Rename columns
    rename_map = {
        CFG["mob"]: 'MOB_CURRENT',
        CFG["ead"]: 'EAD_CURRENT',
    }
    
    # Rename STATE nếu có
    if CFG["state"] in loan_info.columns:
        rename_map[CFG["state"]] = 'STATE_CURRENT'
    
    if orig_date_col in loan_info.columns and orig_date_col != 'DISBURSAL_DATE':
        rename_map[orig_date_col] = 'DISBURSAL_DATE'
    if disb_amt_col in loan_info.columns and disb_amt_col != 'DISBURSAL_AMOUNT':
        rename_map[disb_amt_col] = 'DISBURSAL_AMOUNT'
    
    loan_info = loan_info.rename(columns=rename_map)
    
    for target_mob in target_mobs:
        print(f"\n{'='*50}")
        print(f"📍 MOB {target_mob}")
        
        # ===================================================
        # BƯỚC 1: Phân loại cohorts
        # ===================================================
        print("   Đang phân loại cohorts...")
        
        # Lấy lifecycle @ target_mob
        df_lc = df_lifecycle_final[df_lifecycle_final['MOB'] == target_mob].copy()
        df_lc['VINTAGE_DATE'] = pd.to_datetime(df_lc['VINTAGE_DATE'])
        
        # Phân loại: actual vs forecast
        df_lc_actual = df_lc[df_lc['IS_FORECAST'] == 0].copy()
        df_lc_forecast = df_lc[df_lc['IS_FORECAST'] == 1].copy()
        
        n_cohorts_actual = len(df_lc_actual.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']))
        n_cohorts_forecast = len(df_lc_forecast.groupby(['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']))
        
        print(f"   📊 Cohorts @ MOB {target_mob}:")
        print(f"      Actual: {n_cohorts_actual}")
        print(f"      Forecast: {n_cohorts_forecast}")
        
        # ===================================================
        # BƯỚC 2: Lấy actual data từ df_raw
        # ===================================================
        if n_cohorts_actual > 0:
            print(f"   📥 Lấy actual data từ df_raw...")
            
            # DEBUG: Kiểm tra df_raw có các cột cần thiết không
            print(f"   🔍 DEBUG: Kiểm tra df_raw columns...")
            print(f"      df_raw shape: {df_raw.shape}")
            print(f"      loan_col ({loan_col}): {loan_col in df_raw.columns}")
            print(f"      CFG['state'] ({CFG['state']}): {CFG['state'] in df_raw.columns}")
            print(f"      CFG['ead'] ({CFG['ead']}): {CFG['ead'] in df_raw.columns}")
            print(f"      CFG['mob'] ({CFG['mob']}): {CFG['mob'] in df_raw.columns}")
            
            # Lọc df_raw @ target_mob
            df_raw_target = df_raw[df_raw[CFG['mob']] == target_mob].copy()
            print(f"      df_raw_target shape after filter: {df_raw_target.shape}")
            
            # Kiểm tra sau khi filter
            print(f"      STATE_MODEL in df_raw_target: {CFG['state'] in df_raw_target.columns}")
            
            df_raw_target['VINTAGE_DATE'] = parse_date_column(df_raw_target[CFG['orig_date']])
            
            # Kiểm tra các cột cần thiết có trong df_raw_target không
            required_cols = [loan_col, CFG['state'], CFG['ead'], 'PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']
            missing_cols = [col for col in required_cols if col not in df_raw_target.columns]
            
            if missing_cols:
                print(f"   ⚠️ WARNING: df_raw_target thiếu các cột: {missing_cols}")
                print(f"   ⚠️ Available columns: {df_raw_target.columns.tolist()[:20]}")
                print(f"   ⚠️ Bỏ qua lấy actual data, sẽ allocate cho tất cả")
            else:
                # Lấy danh sách cohorts actual
                actual_cohorts = df_lc_actual[['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']].drop_duplicates()
                
                # Lọc df_raw_target chỉ lấy loans thuộc actual cohorts
                df_raw_actual = df_raw_target.merge(
                    actual_cohorts,
                    on=['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE'],
                    how='inner'
                )
                
                print(f"      df_raw_actual shape: {df_raw_actual.shape}")
                
                if len(df_raw_actual) > 0:
                    # Lấy actual data từ df_raw
                    df_actual_mob = df_raw_actual[[
                        loan_col, CFG['state'], CFG['ead']
                    ]].copy()
                    
                    df_actual_mob = df_actual_mob.rename(columns={
                        CFG['state']: f'STATE_FORECAST_MOB{target_mob}',
                        CFG['ead']: f'EAD_FORECAST_MOB{target_mob}',
                    })
                    
                    # Merge vào loan_info
                    loan_info = loan_info.merge(
                        df_actual_mob,
                        on=loan_col,
                        how='left'
                    )
                    
                    # Tính DEL metrics cho actual
                    if include_del30:
                        mask = loan_info[f'STATE_FORECAST_MOB{target_mob}'].notna()
                        loan_info.loc[mask, f'DEL30_FLAG_MOB{target_mob}'] = (
                            loan_info.loc[mask, f'STATE_FORECAST_MOB{target_mob}'].isin(BUCKETS_30P).astype(int)
                        )
                    if include_del90:
                        mask = loan_info[f'STATE_FORECAST_MOB{target_mob}'].notna()
                        loan_info.loc[mask, f'DEL90_FLAG_MOB{target_mob}'] = (
                            loan_info.loc[mask, f'STATE_FORECAST_MOB{target_mob}'].isin(BUCKETS_90P).astype(int)
                        )
                    
                    # Lấy PROB_DEL từ lifecycle
                    df_del_rates = df_lc_actual[['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']].copy()
                    if 'DEL30_PCT' in df_lc_actual.columns:
                        df_del_rates['DEL30_PCT'] = df_lc_actual['DEL30_PCT']
                    if 'DEL90_PCT' in df_lc_actual.columns:
                        df_del_rates['DEL90_PCT'] = df_lc_actual['DEL90_PCT']
                    
                    # Merge DEL rates (chỉ cho loans có actual data)
                    loan_info_actual_mask = loan_info[f'STATE_FORECAST_MOB{target_mob}'].notna()
                    
                    if loan_info_actual_mask.sum() > 0:
                        loan_info_actual = loan_info[loan_info_actual_mask].merge(
                            df_del_rates,
                            on=['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE'],
                            how='left'
                        )
                        
                        if include_del30 and 'DEL30_PCT' in loan_info_actual.columns:
                            loan_info.loc[loan_info_actual_mask, f'PROB_DEL30_MOB{target_mob}'] = loan_info_actual['DEL30_PCT'].fillna(0).values
                            loan_info.loc[loan_info_actual_mask, f'EAD_DEL30_MOB{target_mob}'] = (
                                loan_info.loc[loan_info_actual_mask, 'DISBURSAL_AMOUNT'].values * 
                                loan_info.loc[loan_info_actual_mask, f'PROB_DEL30_MOB{target_mob}'].values
                            )
                        
                        if include_del90 and 'DEL90_PCT' in loan_info_actual.columns:
                            loan_info.loc[loan_info_actual_mask, f'PROB_DEL90_MOB{target_mob}'] = loan_info_actual['DEL90_PCT'].fillna(0).values
                            loan_info.loc[loan_info_actual_mask, f'EAD_DEL90_MOB{target_mob}'] = (
                                loan_info.loc[loan_info_actual_mask, 'DISBURSAL_AMOUNT'].values * 
                                loan_info.loc[loan_info_actual_mask, f'PROB_DEL90_MOB{target_mob}'].values
                            )
                    
                    print(f"      ✅ Lấy actual cho {len(df_raw_actual):,} loans")
                else:
                    print(f"      ⚠️ Không tìm thấy loans thuộc actual cohorts trong df_raw")
        
        # ===================================================
        # BƯỚC 3: Allocate cho cohorts forecast
        # ===================================================
        if n_cohorts_forecast > 0:
            print(f"   🔨 Allocate cho cohorts forecast...")
            
            # Lọc loans thuộc cohorts forecast
            df_loans_forecast = loan_info.merge(
                df_lc_forecast[['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE']],
                on=['PRODUCT_TYPE', 'RISK_SCORE', 'VINTAGE_DATE'],
                how='inner'
            )
            
            if len(df_loans_forecast) > 0:
                # Allocate
                df_allocated = allocate_fast(
                    df_loans_latest=df_loans_forecast,
                    df_lifecycle_final=df_lifecycle_final,
                    matrices_by_mob=matrices_by_mob,
                    target_mob=target_mob,
                    parent_fallback=parent_fallback,
                    seed=seed,
                )
                
                if not df_allocated.empty:
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
                    
                    # Merge vào loan_info (update cho loans forecast)
                    # Dùng update thay vì merge để không tạo duplicate
                    for col in df_mob.columns:
                        if col != loan_col:
                            if col not in loan_info.columns:
                                loan_info[col] = np.nan
                            loan_info.loc[loan_info[loan_col].isin(df_mob[loan_col]), col] = df_mob.set_index(loan_col)[col]
                    
                    print(f"      ✅ Allocate cho {len(df_loans_forecast):,} loans")
    
    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    print(f"   Total loans: {len(loan_info):,}")
    
    total_disbursal = loan_info['DISBURSAL_AMOUNT'].sum() if 'DISBURSAL_AMOUNT' in loan_info.columns else 0
    total_ead_current = loan_info['EAD_CURRENT'].sum()
    
    print(f"   DISBURSAL_AMOUNT: {total_disbursal:,.0f}")
    print(f"   EAD_CURRENT: {total_ead_current:,.0f}")
    
    for target_mob in target_mobs:
        ead_col = f'EAD_FORECAST_MOB{target_mob}'
        ead_del30_col = f'EAD_DEL30_MOB{target_mob}'
        ead_del90_col = f'EAD_DEL90_MOB{target_mob}'
        
        print(f"\n   MOB {target_mob}:")
        
        if ead_col in loan_info.columns:
            ead_forecast = loan_info[ead_col].sum()
            print(f"      EAD_FORECAST: {ead_forecast:,.0f}")
        
        if ead_del30_col in loan_info.columns and total_disbursal > 0:
            ead_del30 = loan_info[ead_del30_col].sum()
            del30_rate = ead_del30 / total_disbursal * 100
            print(f"      EAD_DEL30: {ead_del30:,.0f} ({del30_rate:.2f}% of DISBURSAL)")
        
        if ead_del90_col in loan_info.columns and total_disbursal > 0:
            ead_del90 = loan_info[ead_del90_col].sum()
            del90_rate = ead_del90 / total_disbursal * 100
            print(f"      EAD_DEL90: {ead_del90:,.0f} ({del90_rate:.2f}% of DISBURSAL)")
    
    return loan_info
