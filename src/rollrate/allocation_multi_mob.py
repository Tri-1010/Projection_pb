# ============================================================
#  allocation_multi_mob.py – Phân bổ nhiều MOB + tính DEL metrics
# ============================================================

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Dict

from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_60P, BUCKETS_90P


def allocate_multi_mob_with_del_metrics(
    df_lifecycle_final: pd.DataFrame,
    df_raw: pd.DataFrame,
    target_mobs: List[int] = [12, 24],
    allocation_method: str = "simple",
    include_del30: bool = True,
    include_del60: bool = False,
    include_del90: bool = True,
) -> pd.DataFrame:
    """
    Phân bổ forecast tại NHIỀU MOB và tính DEL30/DEL90 cho mỗi loan.
    
    Use Case:
        - IFRS9: Cần ECL tại MOB 12 và MOB 24
        - Reporting: Cần DEL30, DEL90 tại nhiều horizons
        - Stress testing: So sánh nhiều scenarios
    
    Parameters
    ----------
    df_lifecycle_final : DataFrame
        Cohort-level forecast (PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE, MOB, states...)
    
    df_raw : DataFrame
        Loan-level data (AGREEMENT_ID, PRODUCT_TYPE, RISK_SCORE, DISBURSAL_DATE, ...)
    
    target_mobs : List[int]
        Danh sách MOB cần phân bổ. Ví dụ: [12, 24]
    
    allocation_method : str
        - "simple": Mỗi loan 1 state (Monte Carlo sampling)
        - "proportional": Mỗi loan nhiều states theo tỷ lệ
    
    include_del30 : bool
        Có tính DEL30 không
    
    include_del60 : bool
        Có tính DEL60 không
    
    include_del90 : bool
        Có tính DEL90 không
    
    Returns
    -------
    DataFrame
        Loan-level forecast với format:
            - AGREEMENT_ID
            - PRODUCT_TYPE, RISK_SCORE, VINTAGE_DATE
            - MOB_CURRENT (MOB hiện tại)
            
            # Forecast tại MOB 12
            - STATE_FORECAST_MOB12
            - EAD_FORECAST_MOB12
            - DEL30_FLAG_MOB12 (0/1)
            - DEL90_FLAG_MOB12 (0/1)
            
            # Forecast tại MOB 24
            - STATE_FORECAST_MOB24
            - EAD_FORECAST_MOB24
            - DEL30_FLAG_MOB24 (0/1)
            - DEL90_FLAG_MOB24 (0/1)
            
            # [Các cột khác từ df_raw]
    """
    
    from src.rollrate.allocation import allocate_forecast_to_loans_simple
    
    loan_col = CFG["loan"]
    orig_col = CFG["orig_date"]
    mob_col = CFG["mob"]
    ead_col = CFG["ead"]
    cutoff_col = CFG["cutoff"]
    
    print(f"🎯 Phân bổ forecast tại {len(target_mobs)} MOB: {target_mobs}")
    
    # ===================================================
    # 1️⃣ Lấy loan-level info (snapshot mới nhất)
    # ===================================================
    df_loans = df_raw.copy()
    df_loans[orig_col] = pd.to_datetime(df_loans[orig_col])
    df_loans["VINTAGE_DATE"] = df_loans[orig_col]
    
    latest_cutoff = df_loans[cutoff_col].max()
    df_loans_latest = df_loans[df_loans[cutoff_col] == latest_cutoff].copy()
    
    # Lấy thông tin cơ bản của mỗi loan
    loan_info = df_loans_latest[[
        loan_col, "PRODUCT_TYPE", "RISK_SCORE", "VINTAGE_DATE", mob_col, ead_col
    ]].copy()
    
    loan_info = loan_info.rename(columns={
        mob_col: "MOB_CURRENT",
        ead_col: "EAD_CURRENT"
    })
    
    # ===================================================
    # 2️⃣ Loop qua từng target MOB
    # ===================================================
    results_by_mob = {}
    
    for target_mob in target_mobs:
        print(f"\n📍 Phân bổ tại MOB {target_mob}...")
        
        # Phân bổ forecast tại MOB này
        df_allocated = allocate_forecast_to_loans_simple(
            df_lifecycle_final=df_lifecycle_final,
            df_raw=df_raw,
            target_mob=target_mob,
            forecast_only=True,
        )
        
        if df_allocated.empty:
            print(f"⚠️ Không có forecast tại MOB {target_mob}")
            continue
        
        # Tính DEL flags
        df_allocated = _add_del_flags(
            df_allocated,
            include_del30=include_del30,
            include_del60=include_del60,
            include_del90=include_del90,
        )
        
        # Chỉ giữ các cột cần thiết
        cols_to_keep = [
            loan_col,
            "STATE_FORECAST",
            "EAD_FORECAST",
        ]
        
        if include_del30:
            cols_to_keep.append("DEL30_FLAG")
        if include_del60:
            cols_to_keep.append("DEL60_FLAG")
        if include_del90:
            cols_to_keep.append("DEL90_FLAG")
        
        df_mob = df_allocated[cols_to_keep].copy()
        
        # Rename columns với suffix _MOBXX
        rename_map = {
            "STATE_FORECAST": f"STATE_FORECAST_MOB{target_mob}",
            "EAD_FORECAST": f"EAD_FORECAST_MOB{target_mob}",
        }
        
        if include_del30:
            rename_map["DEL30_FLAG"] = f"DEL30_FLAG_MOB{target_mob}"
        if include_del60:
            rename_map["DEL60_FLAG"] = f"DEL60_FLAG_MOB{target_mob}"
        if include_del90:
            rename_map["DEL90_FLAG"] = f"DEL90_FLAG_MOB{target_mob}"
        
        df_mob = df_mob.rename(columns=rename_map)
        
        results_by_mob[target_mob] = df_mob
        
        print(f"   ✅ {len(df_mob):,} loans")
    
    # ===================================================
    # 3️⃣ Merge tất cả MOB vào 1 DataFrame
    # ===================================================
    if not results_by_mob:
        print("⚠️ Không có kết quả phân bổ.")
        return pd.DataFrame()
    
    # Start với loan_info
    df_result = loan_info.copy()
    
    # Merge từng MOB
    for target_mob, df_mob in results_by_mob.items():
        df_result = df_result.merge(
            df_mob,
            on=loan_col,
            how="left"
        )
    
    # ===================================================
    # 4️⃣ Tính summary metrics
    # ===================================================
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for target_mob in target_mobs:
        state_col = f"STATE_FORECAST_MOB{target_mob}"
        
        if state_col not in df_result.columns:
            continue
        
        print(f"\n🔹 MOB {target_mob}:")
        print(f"   Total loans: {df_result[state_col].notna().sum():,}")
        
        if include_del30:
            del30_col = f"DEL30_FLAG_MOB{target_mob}"
            if del30_col in df_result.columns:
                del30_count = df_result[del30_col].sum()
                del30_pct = del30_count / len(df_result) * 100
                print(f"   DEL30+: {del30_count:,} loans ({del30_pct:.2f}%)")
        
        if include_del90:
            del90_col = f"DEL90_FLAG_MOB{target_mob}"
            if del90_col in df_result.columns:
                del90_count = df_result[del90_col].sum()
                del90_pct = del90_count / len(df_result) * 100
                print(f"   DEL90+: {del90_count:,} loans ({del90_pct:.2f}%)")
    
    print("\n" + "="*60)
    print(f"✅ Hoàn tất: {len(df_result):,} loans với forecast tại {len(target_mobs)} MOB")
    print("="*60)
    
    return df_result


def _add_del_flags(
    df_allocated: pd.DataFrame,
    include_del30: bool = True,
    include_del60: bool = False,
    include_del90: bool = True,
) -> pd.DataFrame:
    """
    Thêm DEL flags (0/1) dựa trên STATE_FORECAST.
    
    Logic:
        - DEL30_FLAG = 1 nếu STATE_FORECAST in BUCKETS_30P
        - DEL60_FLAG = 1 nếu STATE_FORECAST in BUCKETS_60P
        - DEL90_FLAG = 1 nếu STATE_FORECAST in BUCKETS_90P
    """
    
    df = df_allocated.copy()
    
    if "STATE_FORECAST" not in df.columns:
        return df
    
    if include_del30:
        df["DEL30_FLAG"] = df["STATE_FORECAST"].isin(BUCKETS_30P).astype(int)
    
    if include_del60:
        df["DEL60_FLAG"] = df["STATE_FORECAST"].isin(BUCKETS_60P).astype(int)
    
    if include_del90:
        df["DEL90_FLAG"] = df["STATE_FORECAST"].isin(BUCKETS_90P).astype(int)
    
    return df


def compare_del_across_mobs(
    df_multi_mob: pd.DataFrame,
    target_mobs: List[int] = [12, 24],
    metric: str = "DEL90",
) -> pd.DataFrame:
    """
    So sánh DEL metrics giữa các MOB.
    
    Parameters
    ----------
    df_multi_mob : DataFrame
        Output từ allocate_multi_mob_with_del_metrics()
    
    target_mobs : List[int]
        Danh sách MOB để so sánh
    
    metric : str
        "DEL30" hoặc "DEL90"
    
    Returns
    -------
    DataFrame
        Bảng so sánh:
            - AGREEMENT_ID
            - DEL30_FLAG_MOB12, DEL30_FLAG_MOB24
            - MIGRATION (ví dụ: "0→1", "1→1", "0→0")
    """
    
    loan_col = CFG["loan"]
    
    df = df_multi_mob.copy()
    
    # Lấy các cột DEL flag
    flag_cols = [f"{metric}_FLAG_MOB{mob}" for mob in target_mobs]
    
    # Kiểm tra cột có tồn tại không
    missing = [c for c in flag_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Thiếu các cột: {missing}")
    
    # Tạo migration label
    if len(target_mobs) == 2:
        mob1, mob2 = target_mobs
        col1 = f"{metric}_FLAG_MOB{mob1}"
        col2 = f"{metric}_FLAG_MOB{mob2}"
        
        df["MIGRATION"] = (
            df[col1].astype(str) + "→" + df[col2].astype(str)
        )
        
        # Summary
        print(f"\n📊 {metric} Migration (MOB {mob1} → MOB {mob2}):")
        print(df["MIGRATION"].value_counts().sort_index())
        
        # Tính tỷ lệ
        total = len(df)
        for mig in ["0→0", "0→1", "1→0", "1→1"]:
            count = (df["MIGRATION"] == mig).sum()
            pct = count / total * 100
            print(f"   {mig}: {count:,} loans ({pct:.2f}%)")
    
    return df[[loan_col] + flag_cols + ["MIGRATION"]]


def export_multi_mob_to_excel(
    df_multi_mob: pd.DataFrame,
    filename: str = "outputs/Loan_Forecast_Multi_MOB.xlsx",
    target_mobs: List[int] = [12, 24],
) -> None:
    """
    Export kết quả multi-MOB ra Excel với nhiều sheets.
    Tự động chia nhỏ nếu data > 1M rows.
    
    Sheets:
        1. All_Loans: Tất cả loans với forecast tại các MOB
        2. DEL30_MOB12: Loans có DEL30=1 tại MOB 12
        3. DEL30_MOB24: Loans có DEL30=1 tại MOB 24
        4. DEL90_MOB12: Loans có DEL90=1 tại MOB 12
        5. DEL90_MOB24: Loans có DEL90=1 tại MOB 24
        6. Summary: Tổng hợp số liệu
    """
    from src.config import EXCEL_MAX_ROWS
    
    loan_col = CFG["loan"]
    n_rows = len(df_multi_mob)
    
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        
        # Sheet 1: All loans (chia nhỏ nếu cần)
        if n_rows <= EXCEL_MAX_ROWS:
            df_multi_mob.to_excel(writer, sheet_name="All_Loans", index=False)
        else:
            n_sheets = (n_rows // EXCEL_MAX_ROWS) + 1
            print(f"   ⚠️ Data có {n_rows:,} rows > {EXCEL_MAX_ROWS:,}, chia thành {n_sheets} sheets")
            for i in range(n_sheets):
                start_idx = i * EXCEL_MAX_ROWS
                end_idx = min((i + 1) * EXCEL_MAX_ROWS, n_rows)
                sheet_name = f"All_Loans_{i+1}"
                df_multi_mob.iloc[start_idx:end_idx].to_excel(
                    writer, sheet_name=sheet_name, index=False
                )
        
        # Sheet 2-5: DEL30/DEL90 per MOB
        for mob in target_mobs:
            for metric in ["DEL30", "DEL90"]:
                flag_col = f"{metric}_FLAG_MOB{mob}"
                
                if flag_col not in df_multi_mob.columns:
                    continue
                
                df_del = df_multi_mob[df_multi_mob[flag_col] == 1].copy()
                
                if df_del.empty:
                    continue
                
                sheet_name = f"{metric}_MOB{mob}"
                
                # Chia nhỏ nếu cần
                if len(df_del) <= EXCEL_MAX_ROWS:
                    df_del.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    n_del_sheets = (len(df_del) // EXCEL_MAX_ROWS) + 1
                    for j in range(n_del_sheets):
                        s = j * EXCEL_MAX_ROWS
                        e = min((j + 1) * EXCEL_MAX_ROWS, len(df_del))
                        df_del.iloc[s:e].to_excel(
                            writer, sheet_name=f"{sheet_name}_{j+1}", index=False
                        )
        
        # Sheet 6: Summary
        summary_rows = []
        
        for mob in target_mobs:
            row = {"MOB": mob}
            
            # Total loans
            state_col = f"STATE_FORECAST_MOB{mob}"
            if state_col in df_multi_mob.columns:
                row["Total_Loans"] = df_multi_mob[state_col].notna().sum()
            
            # DEL30
            del30_col = f"DEL30_FLAG_MOB{mob}"
            if del30_col in df_multi_mob.columns:
                row["DEL30_Count"] = df_multi_mob[del30_col].sum()
                row["DEL30_Pct"] = row["DEL30_Count"] / row["Total_Loans"] * 100
            
            # DEL90
            del90_col = f"DEL90_FLAG_MOB{mob}"
            if del90_col in df_multi_mob.columns:
                row["DEL90_Count"] = df_multi_mob[del90_col].sum()
                row["DEL90_Pct"] = row["DEL90_Count"] / row["Total_Loans"] * 100
            
            summary_rows.append(row)
        
        df_summary = pd.DataFrame(summary_rows)
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
    
    print(f"\n✅ Exported to {filename}")


def pivot_del_by_product_mob(
    df_multi_mob: pd.DataFrame,
    target_mobs: List[int] = [12, 24],
    metric: str = "DEL90",
) -> pd.DataFrame:
    """
    Pivot table: DEL metrics theo PRODUCT_TYPE × MOB.
    
    Returns
    -------
    DataFrame
        Pivot table:
            index = PRODUCT_TYPE
            columns = MOB (12, 24, ...)
            values = DEL90_Pct
    """
    
    rows = []
    
    for mob in target_mobs:
        flag_col = f"{metric}_FLAG_MOB{mob}"
        
        if flag_col not in df_multi_mob.columns:
            continue
        
        # Tính % theo product
        product_del = (
            df_multi_mob.groupby("PRODUCT_TYPE")[flag_col]
            .agg(["sum", "count"])
            .reset_index()
        )
        
        product_del["Pct"] = product_del["sum"] / product_del["count"] * 100
        product_del["MOB"] = mob
        
        rows.append(product_del[["PRODUCT_TYPE", "MOB", "Pct"]])
    
    if not rows:
        return pd.DataFrame()
    
    df_long = pd.concat(rows, ignore_index=True)
    
    # Pivot
    df_pivot = df_long.pivot(
        index="PRODUCT_TYPE",
        columns="MOB",
        values="Pct"
    )
    
    # Rename columns
    df_pivot.columns = [f"MOB{int(c)}" for c in df_pivot.columns]
    
    return df_pivot
