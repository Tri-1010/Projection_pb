"""
Export chi tiết cohorts với layout ngang đầy đủ (v3)
- Row 2-4: Current balance và MOB (ngang)
- Row 6-8: K values (K_raw, K_smooth, Alpha) (ngang)
- Row 10+: Transition matrices (ngang)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


def export_cohort_forecast_details_v3(
    cohorts: List[Tuple[str, str, str]],
    df_raw: pd.DataFrame,
    matrices_by_mob: Dict,
    k_raw_by_mob: Dict,
    k_smooth_by_mob: Dict,
    alpha_by_mob: Dict,
    target_mob: int,
    output_dir: str = "cohort_details",
):
    """
    Export chi tiết cohorts với layout ngang đầy đủ để viết công thức Excel.
    
    Layout:
    - Row 1: Headers
    - Row 2: Current MOB và buckets (ngang)
    - Row 3: Current balance (ngang)
    - Row 4: Number of loans (ngang)
    - Row 5: Empty
    - Row 6: K_raw by MOB (ngang)
    - Row 7: K_smooth by MOB (ngang)
    - Row 8: Alpha by MOB (ngang)
    - Row 9: Empty
    - Row 10+: Transition matrices (ngang)
    """
    from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_60P, BUCKETS_90P
    
    # Get column names from config
    state_col = CFG.get("state", "STATE")
    ead_col = CFG.get("ead", "PRINCIPLE_OUTSTANDING")
    loan_col = CFG.get("loan", "AGREEMENT_ID")
    mob_col = CFG.get("mob", "MOB")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"Cohort_Forecast_Details_v3_{timestamp}.xlsx"
    
    print(f"📊 Exporting forecast details (v3 - full horizontal layout)...")
    print(f"   Cohorts: {len(cohorts)}")
    print(f"   Target MOB: {target_mob}")
    print(f"   Output: {filename}")
    
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        workbook = writer.book
        
        # Formats
        fmt_header = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        
        fmt_label = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'align': 'left',
        })
        
        fmt_number = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
            'align': 'right',
        })
        
        fmt_percent = workbook.add_format({
            'num_format': '0.00%',
            'border': 1,
            'align': 'right',
        })
        
        fmt_decimal = workbook.add_format({
            'num_format': '0.0000',
            'border': 1,
            'align': 'right',
        })
        
        fmt_mob = workbook.add_format({
            'bold': True,
            'bg_color': '#FFF2CC',
            'border': 1,
            'align': 'center',
        })
        
        fmt_k_header = workbook.add_format({
            'bold': True,
            'bg_color': '#E2EFDA',
            'border': 1,
            'align': 'left',
        })
        
        # ============================
        # EXPORT EACH COHORT
        # ============================
        
        for cohort_idx, (product, score, vintage_date) in enumerate(cohorts, 1):
            vintage_dt = pd.to_datetime(vintage_date)
            
            # Sheet name
            sheet_name = f"{product}_{score}_{vintage_date[:7]}"[:31]
            
            print(f"   [{cohort_idx}/{len(cohorts)}] {sheet_name}")
            
            # Get cohort data
            mask = (
                (df_raw['PRODUCT_TYPE'] == product) &
                (df_raw['RISK_SCORE'] == score) &
                (df_raw['VINTAGE_DATE'] == vintage_dt)
            )
            df_cohort = df_raw[mask].copy()
            
            if len(df_cohort) == 0:
                print(f"      ⚠️  No data")
                continue
            
            # Get current MOB (latest)
            current_mob = df_cohort[mob_col].max()
            df_current = df_cohort[df_cohort[mob_col] == current_mob]
            
            # Create worksheet
            worksheet = workbook.add_worksheet(sheet_name)
            
            # ============================
            # ROW 1: HEADERS
            # ============================
            row = 0
            worksheet.write(row, 0, 'Cohort Info', fmt_header)
            worksheet.write(row, 1, f"{product} | {score} | {vintage_date}", fmt_label)
            
            # ============================
            # ROW 2: CURRENT MOB & BUCKETS (NGANG)
            # ============================
            row = 1
            
            # Label
            worksheet.write(row, 0, 'Current MOB', fmt_label)
            worksheet.write(row, 1, current_mob, fmt_mob)
            
            # Buckets (ngang)
            buckets = BUCKETS_CANON
            col = 2
            
            # Headers for buckets
            for bucket in buckets:
                worksheet.write(row, col, bucket, fmt_header)
                col += 1
            
            # Total column
            worksheet.write(row, col, 'TOTAL', fmt_header)
            
            # ============================
            # ROW 3: CURRENT BALANCE (NGANG)
            # ============================
            row = 2
            
            worksheet.write(row, 0, 'Current Balance', fmt_label)
            worksheet.write(row, 1, '', fmt_label)
            
            # Calculate balance by bucket
            col = 2
            total_balance = 0
            
            for bucket in buckets:
                balance = df_current[df_current[state_col] == bucket][ead_col].sum()
                worksheet.write(row, col, balance, fmt_number)
                total_balance += balance
                col += 1
            
            # Total
            worksheet.write(row, col, total_balance, fmt_number)
            
            # ============================
            # ROW 4: NUMBER OF LOANS (NGANG)
            # ============================
            row = 3
            
            worksheet.write(row, 0, 'Number of Loans', fmt_label)
            worksheet.write(row, 1, '', fmt_label)
            
            col = 2
            total_loans = 0
            
            for bucket in buckets:
                n_loans = df_current[df_current[state_col] == bucket][loan_col].nunique()
                worksheet.write(row, col, n_loans, fmt_number)
                total_loans += n_loans
                col += 1
            
            # Total
            worksheet.write(row, col, total_loans, fmt_number)
            
            # ============================
            # ROW 5: EMPTY
            # ============================
            row = 4
            
            # ============================
            # ROW 6-9: K VALUES (NGANG)
            # ============================
            
            # Get segment key
            segment_key = (product, score)
            
            # Determine MOB range for K values
            mob_start = current_mob
            mob_end = target_mob
            mob_range = list(range(mob_start, mob_end + 1))
            
            # Check K structure (with or without segment key)
            k_raw_dict = None
            k_smooth_dict = None
            
            # Check if k_raw_by_mob has segment keys
            if k_raw_by_mob:
                first_key = list(k_raw_by_mob.keys())[0]
                if isinstance(first_key, tuple):
                    # Structure: k_raw_by_mob[segment_key][mob]
                    k_raw_dict = k_raw_by_mob.get(segment_key, {})
                else:
                    # Structure: k_raw_by_mob[mob]
                    k_raw_dict = k_raw_by_mob
            
            # Check if k_smooth_by_mob has segment keys
            if k_smooth_by_mob:
                first_key = list(k_smooth_by_mob.keys())[0]
                if isinstance(first_key, tuple):
                    # Structure: k_smooth_by_mob[segment_key][mob]
                    k_smooth_dict = k_smooth_by_mob.get(segment_key, {})
                else:
                    # Structure: k_smooth_by_mob[mob]
                    k_smooth_dict = k_smooth_by_mob
            
            # ROW 6: K_RAW HEADER
            row = 5
            worksheet.write(row, 0, 'K_raw', fmt_k_header)
            worksheet.write(row, 1, 'MOB →', fmt_k_header)
            
            col = 2
            for mob in mob_range:
                worksheet.write(row, col, mob, fmt_mob)
                col += 1
            
            # ROW 7: K_RAW VALUES
            row = 6
            worksheet.write(row, 0, 'K_raw values', fmt_k_header)
            worksheet.write(row, 1, '', fmt_k_header)
            
            col = 2
            for mob in mob_range:
                if k_raw_dict and mob in k_raw_dict:
                    k_val = k_raw_dict[mob]
                    worksheet.write(row, col, k_val, fmt_decimal)
                else:
                    worksheet.write(row, col, '', fmt_decimal)
                col += 1
            
            # ROW 8: K_SMOOTH VALUES
            row = 7
            worksheet.write(row, 0, 'K_smooth values', fmt_k_header)
            worksheet.write(row, 1, '', fmt_k_header)
            
            col = 2
            for mob in mob_range:
                if k_smooth_dict and mob in k_smooth_dict:
                    k_val = k_smooth_dict[mob]
                    worksheet.write(row, col, k_val, fmt_decimal)
                else:
                    worksheet.write(row, col, '', fmt_decimal)
                col += 1
            
            # ROW 9: ALPHA VALUES
            row = 8
            worksheet.write(row, 0, 'Alpha values', fmt_k_header)
            worksheet.write(row, 1, '', fmt_k_header)
            
            col = 2
            for mob in mob_range:
                if mob in alpha_by_mob:
                    alpha_val = alpha_by_mob[mob]
                    worksheet.write(row, col, alpha_val, fmt_decimal)
                else:
                    worksheet.write(row, col, '', fmt_decimal)
                col += 1
            
            # ============================
            # ROW 10: EMPTY
            # ============================
            row = 9
            
            # ============================
            # ROW 11+: TRANSITION MATRICES (NGANG)
            # ============================
            row = 10
            
            # Header row
            worksheet.write(row, 0, 'MOB', fmt_header)
            worksheet.write(row, 1, 'From Bucket', fmt_header)
            
            col = 2
            for bucket in buckets:
                worksheet.write(row, col, f"To {bucket}", fmt_header)
                col += 1
            
            if segment_key not in matrices_by_mob:
                print(f"      ⚠️  No transition matrices for segment")
                continue
            
            # Write transition matrices for each MOB
            row = 11
            
            for mob in sorted(matrices_by_mob[segment_key].keys()):
                tm = matrices_by_mob[segment_key][mob]
                
                # For each "from" bucket
                for from_bucket in buckets:
                    if from_bucket not in tm.index:
                        continue
                    
                    # MOB column
                    worksheet.write(row, 0, mob, fmt_mob)
                    
                    # From bucket column
                    worksheet.write(row, 1, from_bucket, fmt_label)
                    
                    # Transition probabilities (ngang)
                    col = 2
                    for to_bucket in buckets:
                        if to_bucket in tm.columns:
                            prob = tm.loc[from_bucket, to_bucket]
                            worksheet.write(row, col, prob, fmt_percent)
                        else:
                            worksheet.write(row, col, 0, fmt_percent)
                        col += 1
                    
                    row += 1
            
            # ============================
            # COLUMN WIDTHS
            # ============================
            worksheet.set_column('A:A', 18)  # Labels
            worksheet.set_column('B:B', 15)  # MOB / From Bucket
            worksheet.set_column('C:Z', 12)  # Buckets / Values
            
            # Freeze panes (freeze first 2 columns and first 11 rows)
            worksheet.freeze_panes(11, 2)
        
        # ============================
        # SUMMARY SHEET
        # ============================
        summary_data = []
        
        for product, score, vintage_date in cohorts:
            vintage_dt = pd.to_datetime(vintage_date)
            
            mask = (
                (df_raw['PRODUCT_TYPE'] == product) &
                (df_raw['RISK_SCORE'] == score) &
                (df_raw['VINTAGE_DATE'] == vintage_dt)
            )
            df_cohort = df_raw[mask]
            
            if len(df_cohort) == 0:
                continue
            
            current_mob = df_cohort[mob_col].max()
            df_current = df_cohort[df_cohort[mob_col] == current_mob]
            
            n_loans = df_current[loan_col].nunique()
            total_disb = df_cohort[df_cohort[mob_col] == 0]['DISBURSAL_AMOUNT'].sum()
            total_ead = df_current[ead_col].sum()
            
            summary_data.append({
                'Product': product,
                'Risk_Score': score,
                'Vintage_Date': vintage_date,
                'N_Loans': n_loans,
                'Total_Disbursement': total_disb,
                'Current_MOB': current_mob,
                'Current_EAD': total_ead,
                'Target_MOB': target_mob,
                'Forecast_Steps': target_mob - current_mob,
            })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        worksheet = writer.sheets['Summary']
        worksheet.set_column('A:C', 15)
        worksheet.set_column('D:I', 18)
    
    print(f"\n✅ Export completed!")
    print(f"   File: {filename}")
    
    return str(filename)
