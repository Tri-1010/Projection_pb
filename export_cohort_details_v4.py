"""
Export chi tiết cohorts - V4
- Tất cả cohorts trong 1 sheet
- Mỗi cohort cách nhau 2 dòng trống
- Layout ngang đầy đủ: Current + K + Transition Matrix
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


def export_cohort_forecast_details_v4(
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
    Export chi tiết cohorts - tất cả trong 1 sheet.
    
    Layout cho mỗi cohort:
    - Row 0: Cohort header
    - Row 1: Current MOB + Buckets
    - Row 2: Current Balance
    - Row 3: Number of Loans
    - Row 4: Empty
    - Row 5: K headers (MOB)
    - Row 6: K_raw values
    - Row 7: K_smooth values
    - Row 8: Alpha values
    - Row 9: Empty
    - Row 10: TM headers
    - Row 11+: TM data (mỗi MOB có nhiều rows cho từng from_bucket)
    - 2 empty rows
    - Next cohort...
    """
    from src.config import CFG, BUCKETS_CANON
    
    # Get column names from config
    state_col = CFG.get("state", "STATE")
    ead_col = CFG.get("ead", "PRINCIPLE_OUTSTANDING")
    loan_col = CFG.get("loan", "AGREEMENT_ID")
    mob_col = CFG.get("mob", "MOB")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"Cohort_Forecast_Details_v4_{timestamp}.xlsx"
    
    print(f"📊 Exporting forecast details (v4 - single sheet)...")
    print(f"   Cohorts: {len(cohorts)}")
    print(f"   Target MOB: {target_mob}")
    print(f"   Output: {filename}")
    
    # Debug: Check matrices_by_mob structure
    print(f"\n🔍 Debug matrices_by_mob:")
    if matrices_by_mob:
        first_product = list(matrices_by_mob.keys())[0]
        print(f"   First product: {first_product}")
        if isinstance(matrices_by_mob[first_product], dict):
            first_mob = list(matrices_by_mob[first_product].keys())[0]
            print(f"   First MOB: {first_mob}")
            if isinstance(matrices_by_mob[first_product][first_mob], dict):
                first_score = list(matrices_by_mob[first_product][first_mob].keys())[0]
                print(f"   First score: {first_score}")
                entry = matrices_by_mob[first_product][first_mob][first_score]
                if isinstance(entry, dict) and 'P' in entry:
                    print(f"   Structure: matrices_by_mob[product][mob][score] = {{'P': DataFrame, ...}}")
                    print(f"   P shape: {entry['P'].shape}")
                else:
                    print(f"   Entry type: {type(entry)}")
    else:
        print(f"   ⚠️  matrices_by_mob is empty!")
    
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        workbook = writer.book
        
        # Formats
        fmt_header = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
        })
        
        fmt_cohort_header = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#002060',
            'font_color': 'white',
            'border': 2,
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
        
        fmt_tm_header = workbook.add_format({
            'bold': True,
            'bg_color': '#FCE4D6',
            'border': 1,
            'align': 'center',
        })
        
        # Create single worksheet
        worksheet = workbook.add_worksheet('All_Cohorts')
        
        buckets = BUCKETS_CANON
        current_row = 0
        
        # ============================
        # EXPORT ALL COHORTS
        # ============================
        
        for cohort_idx, (product, score, vintage_date) in enumerate(cohorts, 1):
            vintage_dt = pd.to_datetime(vintage_date)
            
            print(f"   [{cohort_idx}/{len(cohorts)}] {product}_{score}_{vintage_date[:7]}")
            
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
            
            # ============================
            # ROW 0: COHORT HEADER
            # ============================
            worksheet.write(current_row, 0, f"COHORT: {product} | {score} | {vintage_date}", fmt_cohort_header)
            worksheet.merge_range(current_row, 0, current_row, 10, f"COHORT: {product} | {score} | {vintage_date}", fmt_cohort_header)
            current_row += 1
            
            # ============================
            # ROW 1: CURRENT MOB & BUCKETS
            # ============================
            worksheet.write(current_row, 0, 'Current MOB', fmt_label)
            worksheet.write(current_row, 1, current_mob, fmt_mob)
            
            col = 2
            for bucket in buckets:
                worksheet.write(current_row, col, bucket, fmt_header)
                col += 1
            worksheet.write(current_row, col, 'TOTAL', fmt_header)
            current_row += 1
            
            # ============================
            # ROW 2: CURRENT BALANCE
            # ============================
            worksheet.write(current_row, 0, 'Current Balance', fmt_label)
            worksheet.write(current_row, 1, '', fmt_label)
            
            col = 2
            total_balance = 0
            for bucket in buckets:
                balance = df_current[df_current[state_col] == bucket][ead_col].sum()
                worksheet.write(current_row, col, balance, fmt_number)
                total_balance += balance
                col += 1
            worksheet.write(current_row, col, total_balance, fmt_number)
            current_row += 1
            
            # ============================
            # ROW 3: NUMBER OF LOANS
            # ============================
            worksheet.write(current_row, 0, 'Number of Loans', fmt_label)
            worksheet.write(current_row, 1, '', fmt_label)
            
            col = 2
            total_loans = 0
            for bucket in buckets:
                n_loans = df_current[df_current[state_col] == bucket][loan_col].nunique()
                worksheet.write(current_row, col, n_loans, fmt_number)
                total_loans += n_loans
                col += 1
            worksheet.write(current_row, col, total_loans, fmt_number)
            current_row += 1
            
            # ============================
            # ROW 4: EMPTY
            # ============================
            current_row += 1
            
            # ============================
            # ROW 5-8: K VALUES
            # ============================
            segment_key = (product, score)
            mob_start = current_mob
            mob_end = target_mob
            mob_range = list(range(mob_start, mob_end + 1))
            
            # Detect K structure
            k_raw_dict = None
            k_smooth_dict = None
            
            if k_raw_by_mob:
                first_key = list(k_raw_by_mob.keys())[0]
                if isinstance(first_key, tuple):
                    k_raw_dict = k_raw_by_mob.get(segment_key, {})
                else:
                    k_raw_dict = k_raw_by_mob
            
            if k_smooth_by_mob:
                first_key = list(k_smooth_by_mob.keys())[0]
                if isinstance(first_key, tuple):
                    k_smooth_dict = k_smooth_by_mob.get(segment_key, {})
                else:
                    k_smooth_dict = k_smooth_by_mob
            
            # K headers
            worksheet.write(current_row, 0, 'K Values', fmt_k_header)
            worksheet.write(current_row, 1, 'MOB →', fmt_k_header)
            col = 2
            for mob in mob_range:
                worksheet.write(current_row, col, mob, fmt_mob)
                col += 1
            current_row += 1
            
            # K_raw values
            worksheet.write(current_row, 0, 'K_raw', fmt_k_header)
            worksheet.write(current_row, 1, '', fmt_k_header)
            col = 2
            for mob in mob_range:
                if k_raw_dict and mob in k_raw_dict:
                    worksheet.write(current_row, col, k_raw_dict[mob], fmt_decimal)
                else:
                    worksheet.write(current_row, col, '', fmt_decimal)
                col += 1
            current_row += 1
            
            # K_smooth values
            worksheet.write(current_row, 0, 'K_smooth', fmt_k_header)
            worksheet.write(current_row, 1, '', fmt_k_header)
            col = 2
            for mob in mob_range:
                if k_smooth_dict and mob in k_smooth_dict:
                    worksheet.write(current_row, col, k_smooth_dict[mob], fmt_decimal)
                else:
                    worksheet.write(current_row, col, '', fmt_decimal)
                col += 1
            current_row += 1
            
            # Alpha values
            worksheet.write(current_row, 0, 'Alpha', fmt_k_header)
            worksheet.write(current_row, 1, '', fmt_k_header)
            col = 2
            for mob in mob_range:
                if mob in alpha_by_mob:
                    worksheet.write(current_row, col, alpha_by_mob[mob], fmt_decimal)
                else:
                    worksheet.write(current_row, col, '', fmt_decimal)
                col += 1
            current_row += 1
            
            # ============================
            # ROW: EMPTY
            # ============================
            current_row += 1
            
            # ============================
            # TRANSITION MATRICES
            # ============================
            
            # Structure: matrices_by_mob[product][mob][score] = {"P": DataFrame, ...}
            tm_data_found = False
            
            print(f"      🔍 Looking for TM: product={product}, score={score}")
            
            if matrices_by_mob and product in matrices_by_mob:
                product_matrices = matrices_by_mob[product]
                print(f"      ✅ Found product '{product}' in matrices_by_mob")
                print(f"      📊 Available MOBs: {sorted(product_matrices.keys())[:10]}...")
                
                # Check what scores are available for first MOB
                if product_matrices:
                    first_mob = list(product_matrices.keys())[0]
                    available_scores = list(product_matrices[first_mob].keys())
                    print(f"      📊 Available scores at MOB {first_mob}: {available_scores}")
                    print(f"      🎯 Looking for score: '{score}' (type: {type(score).__name__})")
                
                # TM Header
                worksheet.write(current_row, 0, 'Transition Matrix', fmt_tm_header)
                worksheet.write(current_row, 1, 'From\\To', fmt_tm_header)
                col = 2
                for bucket in buckets:
                    worksheet.write(current_row, col, bucket, fmt_tm_header)
                    col += 1
                current_row += 1
                
                # Write TM for each MOB
                for mob in sorted(product_matrices.keys()):
                    # Try both string and original type for score matching
                    score_str = str(score)
                    
                    # Find matching score key
                    score_key = None
                    if score in product_matrices[mob]:
                        score_key = score
                    elif score_str in product_matrices[mob]:
                        score_key = score_str
                    else:
                        # Try to find a matching score
                        for s in product_matrices[mob].keys():
                            if str(s) == score_str:
                                score_key = s
                                break
                    
                    if score_key is None:
                        continue
                    
                    tm_entry = product_matrices[mob][score_key]
                    
                    # Get the actual transition matrix
                    if isinstance(tm_entry, dict) and 'P' in tm_entry:
                        tm = tm_entry['P']
                    elif isinstance(tm_entry, pd.DataFrame):
                        tm = tm_entry
                    else:
                        print(f"      ⚠️ MOB {mob}: tm_entry is {type(tm_entry).__name__}, not dict or DataFrame")
                        continue
                    
                    if not isinstance(tm, pd.DataFrame):
                        print(f"      ⚠️ MOB {mob}: tm is {type(tm).__name__}, not DataFrame")
                        continue
                    
                    tm_data_found = True
                    
                    # MOB header row
                    worksheet.write(current_row, 0, f'MOB {mob}', fmt_mob)
                    worksheet.write(current_row, 1, '', fmt_mob)
                    current_row += 1
                    
                    # For each "from" bucket
                    for from_bucket in buckets:
                        if from_bucket not in tm.index:
                            continue
                        
                        worksheet.write(current_row, 0, '', fmt_label)
                        worksheet.write(current_row, 1, from_bucket, fmt_label)
                        
                        col = 2
                        for to_bucket in buckets:
                            if to_bucket in tm.columns:
                                prob = tm.loc[from_bucket, to_bucket]
                                if pd.notna(prob):
                                    worksheet.write(current_row, col, prob, fmt_percent)
                                else:
                                    worksheet.write(current_row, col, 0, fmt_percent)
                            else:
                                worksheet.write(current_row, col, 0, fmt_percent)
                            col += 1
                        current_row += 1
                
                if tm_data_found:
                    print(f"      ✅ TM data written successfully")
            else:
                if not matrices_by_mob:
                    print(f"      ❌ matrices_by_mob is empty!")
                else:
                    print(f"      ❌ Product '{product}' not found in matrices_by_mob")
                    print(f"      📊 Available products: {list(matrices_by_mob.keys())}")
            
            if not tm_data_found:
                worksheet.write(current_row, 0, f'⚠️ No transition matrices for {product}/{score}', fmt_label)
                current_row += 1
            
            # ============================
            # 2 EMPTY ROWS BETWEEN COHORTS
            # ============================
            current_row += 2
        
        # ============================
        # COLUMN WIDTHS
        # ============================
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:Z', 12)
        
        # Freeze first row
        worksheet.freeze_panes(1, 0)
    
    print(f"\n✅ Export completed!")
    print(f"   File: {filename}")
    print(f"   Sheet: All_Cohorts (single sheet)")
    
    return str(filename)
