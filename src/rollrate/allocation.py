# ============================================================
#  allocation.py – Phân bổ ngược forecast từ cohort xuống loan
# ============================================================

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, Literal

from src.config import CFG, BUCKETS_CANON


def allocate_forecast_to_loans(
    df_lifecycle_final: pd.DataFrame,
    df_raw: pd.DataFrame,
    allocation_method: Literal["proportional", "risk_weighted", "equal"] = "proportional",
    forecast_only: bool = True,
    target_mob: int | None = None,
) -> pd.DataFrame:
    """
    Phân bổ ngược kết quả forecast từ cohort-level xuống loan-level.
    
    Logic:
        - df_lifecycle_final: cohort-level forecast (PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB)
        - df_raw: loan-level data (có AGREEMENT_ID, PRODUCT_TYPE, RISK_SCORE, DISBURSAL_DATE, MOB, STATE_MODEL, EAD)
        - Với mỗi cohort tại MOB forecast, phân bổ EAD theo state xuống từng loan
    
    ⚠️ QUAN TRỌNG - EAD FORECAST TẠI MOB NÀO?
        - Nếu target_mob=None: phân bổ TẤT CẢ các MOB forecast (mỗi loan có nhiều dòng theo MOB)
        - Nếu target_mob=12: chỉ phân bổ forecast tại MOB=12 (thường dùng cho IFRS9)
        - Nếu target_mob=24: chỉ phân bổ forecast tại MOB=24
        
        Ví dụ:
            - IFRS9 ECL: dùng target_mob=12 (12-month ECL)
            - Lifetime ECL: dùng target_mob=None hoặc max_mob
            - Stress test: dùng target_mob cụ thể (12, 24, 36)
    
    Parameters
    ----------
    df_lifecycle_final : DataFrame
        Cohort-level forecast với các cột:
            - PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB
            - DPD0, DPD1+, DPD30+, ..., WRITEOFF, PREPAY, SOLDOUT (EAD theo state)
            - IS_FORECAST (0=actual, 1=forecast)
    
    df_raw : DataFrame
        Loan-level data với các cột:
            - AGREEMENT_ID, PRODUCT_TYPE, RISK_SCORE, DISBURSAL_DATE, MOB, CUTOFF_DATE
            - STATE_MODEL, PRINCIPLE_OUTSTANDING (EAD hiện tại)
    
    allocation_method : str
        - "proportional": phân bổ theo tỷ lệ EAD hiện tại của loan trong cohort
        - "risk_weighted": phân bổ theo risk score (loan rủi ro cao nhận nhiều hơn ở bucket xấu)
        - "equal": phân bổ đều cho tất cả loan trong cohort
    
    forecast_only : bool
        - True: chỉ phân bổ các MOB forecast (IS_FORECAST=1)
        - False: phân bổ cả actual và forecast
    
    target_mob : int, optional
        - None: phân bổ tất cả MOB forecast
        - 12: chỉ phân bổ MOB=12 (IFRS9 12-month ECL)
        - 24, 36, ...: phân bổ MOB cụ thể
    
    Returns
    -------
    DataFrame
        Loan-level forecast với các cột:
            - AGREEMENT_ID, PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB
            - STATE_FORECAST (state dự báo)
            - EAD_FORECAST (EAD dự báo)
            - ALLOCATION_WEIGHT (trọng số phân bổ)
            - IS_FORECAST
            - TARGET_MOB (MOB được phân bổ)
            - [các cột khác từ df_raw: customer info, product info, ...]
    """
    
    loan_col = CFG["loan"]
    orig_col = CFG["orig_date"]
    mob_col = CFG["mob"]
    state_col = CFG["state"]
    ead_col = CFG["ead"]
    cutoff_col = CFG["cutoff"]
    
    # ===================================================
    # 1️⃣ Chuẩn bị df_lifecycle_final
    # ===================================================
    df_lc = df_lifecycle_final.copy()
    
    # Lọc forecast rows nếu cần
    if forecast_only and "IS_FORECAST" in df_lc.columns:
        df_lc = df_lc[df_lc["IS_FORECAST"] == 1].copy()
    
    # 🔥 Lọc theo target_mob nếu có
    if target_mob is not None:
        df_lc = df_lc[df_lc["MOB"] == target_mob].copy()
        print(f"📍 Phân bổ forecast tại MOB = {target_mob}")
    else:
        print(f"📍 Phân bổ forecast cho TẤT CẢ MOB ({df_lc['MOB'].min()}-{df_lc['MOB'].max()})")
    
    if df_lc.empty:
        print("⚠️ Không có dữ liệu forecast để phân bổ.")
        return pd.DataFrame()
    
    # Chuẩn hóa VINTAGE_DATE
    df_lc["VINTAGE_DATE"] = pd.to_datetime(df_lc["VINTAGE_DATE"])
    
    # ===================================================
    # 2️⃣ Chuẩn bị df_raw (loan-level)
    # ===================================================
    df_loans = df_raw.copy()
    df_loans[orig_col] = pd.to_datetime(df_loans[orig_col])
    df_loans["VINTAGE_DATE"] = df_loans[orig_col]
    
    # Lấy snapshot mới nhất của mỗi loan
    latest_cutoff = df_loans[cutoff_col].max()
    df_loans_latest = df_loans[df_loans[cutoff_col] == latest_cutoff].copy()
    
    # ===================================================
    # 3️⃣ Tính allocation weight cho mỗi loan trong cohort
    # ===================================================
    if allocation_method == "proportional":
        # Weight = EAD hiện tại / tổng EAD cohort
        cohort_ead = (
            df_loans_latest.groupby(["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE"])[ead_col]
            .sum()
            .rename("COHORT_EAD")
            .reset_index()
        )
        
        df_loans_latest = df_loans_latest.merge(
            cohort_ead,
            on=["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE"],
            how="left"
        )
        
        df_loans_latest["ALLOCATION_WEIGHT"] = (
            df_loans_latest[ead_col] / df_loans_latest["COHORT_EAD"]
        ).fillna(0)
    
    elif allocation_method == "equal":
        # Weight = 1 / số loan trong cohort
        cohort_count = (
            df_loans_latest.groupby(["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE"])[loan_col]
            .count()
            .rename("COHORT_COUNT")
            .reset_index()
        )
        
        df_loans_latest = df_loans_latest.merge(
            cohort_count,
            on=["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE"],
            how="left"
        )
        
        df_loans_latest["ALLOCATION_WEIGHT"] = 1.0 / df_loans_latest["COHORT_COUNT"]
    
    elif allocation_method == "risk_weighted":
        # Weight phức tạp hơn: loan ở state xấu hơn nhận nhiều EAD hơn ở bucket xấu
        # Đơn giản hóa: dùng proportional + risk adjustment
        print("⚠️ risk_weighted chưa implement đầy đủ, fallback về proportional.")
        allocation_method = "proportional"
        
        cohort_ead = (
            df_loans_latest.groupby(["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE"])[ead_col]
            .sum()
            .rename("COHORT_EAD")
            .reset_index()
        )
        
        df_loans_latest = df_loans_latest.merge(
            cohort_ead,
            on=["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE"],
            how="left"
        )
        
        df_loans_latest["ALLOCATION_WEIGHT"] = (
            df_loans_latest[ead_col] / df_loans_latest["COHORT_EAD"]
        ).fillna(0)
    
    else:
        raise ValueError(f"Unknown allocation_method: {allocation_method}")
    
    # ===================================================
    # 4️⃣ Loop qua từng cohort × MOB forecast
    # ===================================================
    results = []
    
    for _, row_lc in df_lc.iterrows():
        product = row_lc["PRODUCT_TYPE"]
        score = row_lc["RISK_SCORE"]
        vintage = row_lc["VINTAGE_DATE"]
        mob = int(row_lc["MOB"])
        
        # Lấy EAD theo state từ lifecycle
        ead_by_state = {}
        for st in BUCKETS_CANON:
            if st in row_lc.index:
                ead_by_state[st] = float(row_lc[st])
        
        total_ead_cohort = sum(ead_by_state.values())
        
        if total_ead_cohort <= 0:
            continue
        
        # Lấy các loan trong cohort này
        mask = (
            (df_loans_latest["PRODUCT_TYPE"] == product) &
            (df_loans_latest["RISK_SCORE"] == score) &
            (df_loans_latest["VINTAGE_DATE"] == vintage)
        )
        
        df_cohort_loans = df_loans_latest[mask].copy()
        
        if df_cohort_loans.empty:
            continue
        
        # ===================================================
        # 5️⃣ Phân bổ EAD theo state xuống từng loan
        # ===================================================
        # Strategy: Mỗi loan sẽ được assign vào 1 state dựa trên:
        #   - State hiện tại của loan
        #   - Xác suất chuyển state (từ transition matrix)
        #   - Allocation weight
        
        # Đơn giản hóa: Phân bổ theo tỷ lệ EAD
        # Loan có EAD cao hơn sẽ nhận nhiều EAD hơn
        
        for st in BUCKETS_CANON:
            ead_state = ead_by_state.get(st, 0.0)
            
            if ead_state <= 0:
                continue
            
            # Phân bổ EAD_state xuống các loan theo weight
            for _, loan_row in df_cohort_loans.iterrows():
                weight = loan_row["ALLOCATION_WEIGHT"]
                ead_allocated = ead_state * weight
                
                if ead_allocated <= 0:
                    continue
                
                result_row = {
                    loan_col: loan_row[loan_col],
                    "PRODUCT_TYPE": product,
                    "RISK_SCORE": score,
                    "VINTAGE_DATE": vintage,
                    "MOB": mob,
                    "MOB_CURRENT": int(loan_row[mob_col]),  # MOB hiện tại của loan
                    "STATE_FORECAST": st,
                    "EAD_FORECAST": ead_allocated,
                    "ALLOCATION_WEIGHT": weight,
                    "IS_FORECAST": 1,
                    "ALLOCATION_METHOD": allocation_method,
                    "TARGET_MOB": mob,  # MOB được phân bổ
                }
                
                # Thêm các cột khác từ df_raw (customer info, product info, ...)
                for col in df_loans_latest.columns:
                    if col not in result_row and col != ead_col:
                        result_row[col] = loan_row[col]
                
                results.append(result_row)
    
    # ===================================================
    # 6️⃣ Tạo DataFrame kết quả
    # ===================================================
    df_result = pd.DataFrame(results)
    
    if df_result.empty:
        print("⚠️ Không có kết quả phân bổ.")
        return pd.DataFrame()
    
    # ===================================================
    # 7️⃣ Validation: Kiểm tra tổng EAD
    # ===================================================
    print("✅ Phân bổ hoàn tất. Kiểm tra tổng EAD...")
    
    # Tổng EAD từ lifecycle (cohort-level)
    total_ead_lifecycle = df_lc[BUCKETS_CANON].sum().sum()
    
    # Tổng EAD từ allocation (loan-level)
    total_ead_allocated = df_result["EAD_FORECAST"].sum()
    
    diff = abs(total_ead_lifecycle - total_ead_allocated)
    diff_pct = diff / total_ead_lifecycle * 100 if total_ead_lifecycle > 0 else 0
    
    print(f"  - Tổng EAD lifecycle: {total_ead_lifecycle:,.0f}")
    print(f"  - Tổng EAD allocated: {total_ead_allocated:,.0f}")
    print(f"  - Chênh lệch: {diff:,.0f} ({diff_pct:.4f}%)")
    
    if diff_pct > 0.01:
        print(f"⚠️ Chênh lệch > 0.01%, cần kiểm tra lại logic phân bổ.")
    else:
        print("✅ Tổng EAD khớp (chênh lệch < 0.01%).")
    
    return df_result


def allocate_forecast_to_loans_simple(
    df_lifecycle_final: pd.DataFrame,
    df_raw: pd.DataFrame,
    forecast_only: bool = True,
    target_mob: int | None = None,
) -> pd.DataFrame:
    """
    Phiên bản đơn giản: Mỗi loan chỉ được assign vào 1 state duy nhất.
    
    Logic:
        - Với mỗi cohort × MOB, tính phân phối state (% EAD theo state)
        - Assign loan vào state theo xác suất (Monte Carlo sampling)
        - Đảm bảo tổng EAD khớp với lifecycle
    
    ⚠️ QUAN TRỌNG - EAD FORECAST TẠI MOB NÀO?
        - Nếu target_mob=None: phân bổ TẤT CẢ các MOB forecast
        - Nếu target_mob=12: chỉ phân bổ forecast tại MOB=12 (IFRS9 12-month ECL)
        - Nếu target_mob=24: chỉ phân bổ forecast tại MOB=24
        
        📌 Khuyến nghị:
            - IFRS9 Stage 1 (12-month ECL): target_mob=12
            - IFRS9 Stage 2/3 (Lifetime ECL): target_mob=None hoặc max_mob
            - Stress testing: target_mob theo scenario
    
    Parameters
    ----------
    df_lifecycle_final : DataFrame
        Long lifecycle (PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB, các bucket DPD*, WRITEOFF,...)
    df_raw : DataFrame
        Loan-level raw data
    forecast_only : bool
        True: chỉ phân bổ forecast rows
    target_mob : int, optional
        MOB cụ thể để phân bổ (None = tất cả MOB)
    
    Returns
    -------
    DataFrame
        Loan-level forecast với 1 state duy nhất cho mỗi loan:
            - AGREEMENT_ID, PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB
            - STATE_FORECAST (1 state duy nhất)
            - EAD_FORECAST (= EAD hiện tại của loan)
            - IS_FORECAST
            - TARGET_MOB (MOB được phân bổ)
    """
    
    loan_col = CFG["loan"]
    orig_col = CFG["orig_date"]
    mob_col = CFG["mob"]
    state_col = CFG["state"]
    ead_col = CFG["ead"]
    cutoff_col = CFG["cutoff"]
    
    # ===================================================
    # 1️⃣ Chuẩn bị data
    # ===================================================
    df_lc = df_lifecycle_final.copy()
    
    if forecast_only and "IS_FORECAST" in df_lc.columns:
        df_lc = df_lc[df_lc["IS_FORECAST"] == 1].copy()
    
    # 🔥 Lọc theo target_mob nếu có
    if target_mob is not None:
        df_lc = df_lc[df_lc["MOB"] == target_mob].copy()
        print(f"📍 Phân bổ forecast tại MOB = {target_mob}")
    else:
        print(f"📍 Phân bổ forecast cho TẤT CẢ MOB ({df_lc['MOB'].min()}-{df_lc['MOB'].max()})")
    
    if df_lc.empty:
        print("⚠️ Không có dữ liệu forecast để phân bổ.")
        return pd.DataFrame()
    
    df_lc["VINTAGE_DATE"] = pd.to_datetime(df_lc["VINTAGE_DATE"])
    
    df_loans = df_raw.copy()
    df_loans[orig_col] = pd.to_datetime(df_loans[orig_col])
    df_loans["VINTAGE_DATE"] = df_loans[orig_col]
    
    latest_cutoff = df_loans[cutoff_col].max()
    df_loans_latest = df_loans[df_loans[cutoff_col] == latest_cutoff].copy()
    
    # ===================================================
    # 2️⃣ Tính tổng EAD cho mỗi cohort × MOB (để tính phân phối state)
    # ===================================================
    df_lc["TOTAL_EAD"] = df_lc[BUCKETS_CANON].sum(axis=1)
    
    # ===================================================
    # 3️⃣ Assign state cho từng loan
    # ===================================================
    results = []
    
    for _, row_lc in df_lc.iterrows():
        product = row_lc["PRODUCT_TYPE"]
        score = row_lc["RISK_SCORE"]
        vintage = row_lc["VINTAGE_DATE"]
        mob = int(row_lc["MOB"])
        
        # 🔥 Tổng EAD forecast từ lifecycle (tất cả states)
        total_ead_forecast = row_lc[BUCKETS_CANON].sum()
        
        if total_ead_forecast <= 0:
            continue
        
        # Phân phối state (xác suất)
        state_probs = {st: row_lc[st] / total_ead_forecast for st in BUCKETS_CANON}
        state_probs = {k: v for k, v in state_probs.items() if pd.notna(v) and v > 0}
        
        if not state_probs:
            continue
        
        # Normalize
        total_prob = sum(state_probs.values())
        state_probs = {k: v / total_prob for k, v in state_probs.items()}
        
        # Lấy các loan trong cohort
        mask = (
            (df_loans_latest["PRODUCT_TYPE"] == product) &
            (df_loans_latest["RISK_SCORE"] == score) &
            (df_loans_latest["VINTAGE_DATE"] == vintage)
        )
        
        df_cohort_loans = df_loans_latest[mask].copy()
        
        if df_cohort_loans.empty:
            continue
        
        # 🔥 Tổng EAD hiện tại của cohort
        total_ead_current = df_cohort_loans[ead_col].sum()
        
        if total_ead_current <= 0:
            continue
        
        # Assign state cho từng loan bằng sampling
        states_list = list(state_probs.keys())
        probs_list = list(state_probs.values())
        
        np.random.seed(42)  # Reproducible
        assigned_states = np.random.choice(
            states_list,
            size=len(df_cohort_loans),
            p=probs_list
        )
        
        df_cohort_loans["STATE_FORECAST"] = assigned_states
        df_cohort_loans["MOB"] = mob
        df_cohort_loans["MOB_CURRENT"] = df_cohort_loans[mob_col]  # MOB hiện tại
        df_cohort_loans["IS_FORECAST"] = 1
        
        # 🔥 FIX: EAD_FORECAST phải tính theo tỷ lệ từ lifecycle forecast
        # EAD_FORECAST_loan = EAD_CURRENT_loan * (Total_EAD_Forecast / Total_EAD_Current)
        ead_ratio = total_ead_forecast / total_ead_current
        df_cohort_loans["EAD_FORECAST"] = df_cohort_loans[ead_col] * ead_ratio
        
        df_cohort_loans["TARGET_MOB"] = mob  # MOB được phân bổ
        
        results.append(df_cohort_loans)
    
    # ===================================================
    # 4️⃣ Kết quả
    # ===================================================
    if not results:
        print("⚠️ Không có kết quả phân bổ.")
        return pd.DataFrame()
    
    df_result = pd.concat(results, ignore_index=True)
    
    # ===================================================
    # 5️⃣ Validation: Kiểm tra tổng EAD
    # ===================================================
    print("\n✅ Phân bổ hoàn tất. Kiểm tra tổng EAD...")
    
    # Tổng EAD từ lifecycle (cohort-level)
    total_ead_lifecycle = df_lc[BUCKETS_CANON].sum().sum()
    
    # Tổng EAD từ allocation (loan-level)
    total_ead_allocated = df_result["EAD_FORECAST"].sum()
    
    diff = abs(total_ead_lifecycle - total_ead_allocated)
    diff_pct = diff / total_ead_lifecycle * 100 if total_ead_lifecycle > 0 else 0
    
    print(f"  - Tổng EAD lifecycle: {total_ead_lifecycle:,.0f}")
    print(f"  - Tổng EAD allocated: {total_ead_allocated:,.0f}")
    print(f"  - Chênh lệch: {diff:,.0f} ({diff_pct:.4f}%)")
    
    if diff_pct > 0.01:
        print(f"⚠️ Chênh lệch > 0.01%, có thể do làm tròn hoặc missing loans.")
    else:
        print("✅ Tổng EAD khớp (chênh lệch < 0.01%).")
    
    print(f"\n📊 Kết quả: {len(df_result):,} loan-level forecasts.")
    
    return df_result


def validate_allocation(
    df_allocated: pd.DataFrame,
    df_lifecycle_final: pd.DataFrame,
    group_cols: list = None,
) -> pd.DataFrame:
    """
    Kiểm tra tổng EAD sau phân bổ có khớp với lifecycle không.
    
    Parameters
    ----------
    df_allocated : DataFrame
        Loan-level allocation result
    df_lifecycle_final : DataFrame
        Cohort-level lifecycle
    group_cols : list
        Các cột để group (mặc định: PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB)
    
    Returns
    -------
    DataFrame
        Bảng so sánh tổng EAD:
            - PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB
            - EAD_LIFECYCLE (từ lifecycle)
            - EAD_ALLOCATED (từ allocation)
            - DIFF (chênh lệch)
            - DIFF_PCT (% chênh lệch)
    """
    
    if group_cols is None:
        group_cols = ["PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE", "MOB"]
    
    # Tổng EAD từ lifecycle
    df_lc = df_lifecycle_final.copy()
    df_lc["EAD_LIFECYCLE"] = df_lc[BUCKETS_CANON].sum(axis=1)
    
    lc_summary = df_lc[group_cols + ["EAD_LIFECYCLE"]]
    
    # Tổng EAD từ allocation
    alloc_summary = (
        df_allocated.groupby(group_cols)["EAD_FORECAST"]
        .sum()
        .rename("EAD_ALLOCATED")
        .reset_index()
    )
    
    # Merge
    compare = lc_summary.merge(alloc_summary, on=group_cols, how="outer")
    
    compare["DIFF"] = compare["EAD_ALLOCATED"] - compare["EAD_LIFECYCLE"]
    compare["DIFF_PCT"] = (
        compare["DIFF"] / compare["EAD_LIFECYCLE"] * 100
    ).fillna(0)
    
    # Highlight lỗi lớn
    compare["STATUS"] = "OK"
    compare.loc[abs(compare["DIFF_PCT"]) > 0.1, "STATUS"] = "WARNING"
    compare.loc[abs(compare["DIFF_PCT"]) > 1.0, "STATUS"] = "ERROR"
    
    print("\n📊 Validation Summary:")
    print(compare["STATUS"].value_counts())
    
    errors = compare[compare["STATUS"] == "ERROR"]
    if not errors.empty:
        print(f"\n⚠️ Có {len(errors)} cohorts có lỗi lớn (>1%):")
        print(errors[group_cols + ["DIFF_PCT"]].head(10))
    
    return compare


# ============================================================
# Helper: Enrich loan-level forecast với thông tin bổ sung
# ============================================================

def enrich_loan_forecast(
    df_allocated: pd.DataFrame,
    df_raw: pd.DataFrame,
    additional_cols: list = None,
) -> pd.DataFrame:
    """
    Thêm thông tin bổ sung vào loan-level forecast từ df_raw.
    
    Parameters
    ----------
    df_allocated : DataFrame
        Loan-level allocation result
    df_raw : DataFrame
        Raw loan-level data với các cột bổ sung
    additional_cols : list
        Các cột cần thêm (ví dụ: CUSTOMER_ID, BRANCH_CODE, PRODUCT_NAME, ...)
    
    Returns
    -------
    DataFrame
        df_allocated + additional columns
    """
    
    loan_col = CFG["loan"]
    cutoff_col = CFG["cutoff"]
    
    if additional_cols is None:
        # Mặc định: lấy tất cả cột không phải numeric
        additional_cols = [
            col for col in df_raw.columns
            if col not in df_allocated.columns
            and df_raw[col].dtype == "object"
        ]
    
    # Lấy snapshot mới nhất
    latest_cutoff = df_raw[cutoff_col].max()
    df_info = df_raw[df_raw[cutoff_col] == latest_cutoff].copy()
    
    # Chỉ giữ các cột cần thiết
    cols_to_merge = [loan_col] + [c for c in additional_cols if c in df_info.columns]
    df_info = df_info[cols_to_merge].drop_duplicates(subset=[loan_col])
    
    # Merge
    df_result = df_allocated.merge(df_info, on=loan_col, how="left")
    
    print(f"✅ Enriched với {len(additional_cols)} cột bổ sung.")
    
    return df_result
