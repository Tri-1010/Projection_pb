"""
Export chi tiết các thông số để tính forecast cho specific cohorts
Dùng để gửi cho sếp xem chi tiết cách tính toán
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


def export_cohort_forecast_details(
    cohorts: List[Tuple[str, str, str]],  # [(product, score, vintage_date), ...]
    df_raw: pd.DataFrame,
    matrices_by_mob: Dict,
    k_raw_by_mob: Dict,
    k_smooth_by_mob: Dict,
    alpha_by_mob: Dict,
    target_mob: int,
    output_dir: str = "cohort_details",
):
    """
    Export chi tiết tất cả thông số để tính forecast cho specific cohorts.
    
    Parameters
    ----------
    cohorts : List[Tuple[str, str, str]]
        Danh sách cohorts cần export, mỗi cohort là (product, score, vintage_date)
        Ví dụ: [('X', 'A', '2025-10-01'), ('X', 'B', '2024-10-01')]
    df_raw : pd.DataFrame
        Data gốc
    matrices_by_mob : Dict
        Transition matrices by MOB
    k_raw_by_mob : Dict
        K raw values by MOB
    k_smooth_by_mob : Dict
        K smooth values by MOB
    alpha_by_mob : Dict
        Alpha values by MOB
    target_mob : int
        MOB cần forecast
    output_dir : str
        Thư mục output
    
    Returns
    -------
    str
        Path to Excel file
    """
    
    from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_60P, BUCKETS_90P
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"Cohort_Forecast_Details_{timestamp}.xlsx"
    
    print(f"📊 Exporting forecast details for {len(cohorts)} cohorts...")
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
        })
        
        fmt_title = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'font_color': '#00008B',
        })
        
        fmt_number = workbook.add_format({
            'num_format': '#,##0.0000',
            'border': 1,
        })
        
        fmt_percent = workbook.add_format({
            'num_format': '0.00%',
            'border': 1,
        })
        
        # ============================
        # 1. SUMMARY SHEET
        # ============================
        summary_data = []
        
        for product, score, vintage_date in cohorts:
            vintage_dt = pd.to_datetime(vintage_date)
            
            # Get actual data
            mask = (
                (df_raw['PRODUCT_TYPE'] == product) &
                (df_raw['RISK_SCORE'] == score) &
                (df_raw['VINTAGE_DATE'] == vintage_dt)
            )
            df_cohort = df_raw[mask]
            
            if len(df_cohort) == 0:
                print(f"   ⚠️ No data for cohort: {product}, {score}, {vintage_date}")
                continue
            
            # Get latest MOB
            max_mob = df_cohort['MOB'].max()
            
            # Get latest snapshot
            df_latest = df_cohort[df_cohort['MOB'] == max_mob]
            
            n_loans = df_latest['AGREEMENT_ID'].nunique()
            total_disb = df_cohort[df_cohort['MOB'] == 0]['DISBURSAL_AMOUNT'].sum()
            total_ead = df_latest['PRINCIPLE_OUTSTANDING'].sum()
            
            summary_data.append({
                'Product': product,
                'Risk_Score': score,
                'Vintage_Date': vintage_date,
                'N_Loans': n_loans,
                'Total_Disbursement': total_disb,
                'Current_MOB': max_mob,
                'Current_EAD': total_ead,
                'Target_MOB': target_mob,
                'Forecast_MOBs': target_mob - max_mob,
            })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Format Summary sheet
        worksheet = writer.sheets['Summary']
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:I', 18)
        
        # ============================
        # 2. TRANSITION MATRICES
        # ============================
        for product, score, vintage_date in cohorts:
            sheet_name = f"TM_{product}_{score}"[:31]
            
            # Get transition matrices for this segment
            if product not in matrices_by_mob:
                print(f"   ⚠️ No matrices for product: {product}")
                continue
            
            all_matrices = []
            
            for mob in range(target_mob):
                if mob not in matrices_by_mob[product]:
                    continue
                
                if score not in matrices_by_mob[product][mob]:
                    continue
                
                matrix_data = matrices_by_mob[product][mob][score]
                
                if isinstance(matrix_data, dict) and 'P' in matrix_data:
                    P = matrix_data['P']
                else:
                    P = matrix_data
                
                if isinstance(P, pd.DataFrame):
                    df_matrix = P.copy()
                    df_matrix.insert(0, 'MOB', mob)
                    df_matrix.insert(1, 'From_State', df_matrix.index)
                    df_matrix = df_matrix.reset_index(drop=True)
                    all_matrices.append(df_matrix)
            
            if all_matrices:
                df_all_tm = pd.concat(all_matrices, ignore_index=True)
                df_all_tm.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Format
                worksheet = writer.sheets[sheet_name]
                worksheet.set_column('A:B', 12)
                worksheet.set_column('C:Z', 10)
        
        # ============================
        # 3. K VALUES (RAW & SMOOTH)
        # ============================
        k_data = []
        
        for product, score, vintage_date in cohorts:
            for mob in range(target_mob):
                k_raw = None
                k_smooth = None
                alpha = None
                
                # Get K raw
                if product in k_raw_by_mob:
                    if mob in k_raw_by_mob[product]:
                        if score in k_raw_by_mob[product][mob]:
                            k_raw = k_raw_by_mob[product][mob][score]
                
                # Get K smooth
                if product in k_smooth_by_mob:
                    if mob in k_smooth_by_mob[product]:
                        if score in k_smooth_by_mob[product][mob]:
                            k_smooth = k_smooth_by_mob[product][mob][score]
                
                # Get Alpha
                if product in alpha_by_mob:
                    if mob in alpha_by_mob[product]:
                        if score in alpha_by_mob[product][mob]:
                            alpha = alpha_by_mob[product][mob][score]
                
                k_data.append({
                    'Product': product,
                    'Risk_Score': score,
                    'Vintage_Date': vintage_date,
                    'MOB': mob,
                    'K_Raw': k_raw,
                    'K_Smooth': k_smooth,
                    'Alpha': alpha,
                })
        
        df_k = pd.DataFrame(k_data)
        df_k.to_excel(writer, sheet_name='K_Values', index=False)
        
        # Format K Values sheet
        worksheet = writer.sheets['K_Values']
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:G', 12)
        
        # ============================
        # 4. ACTUAL DATA BY MOB
        # ============================
        for product, score, vintage_date in cohorts:
            sheet_name = f"Actual_{product}_{score}"[:31]
            
            vintage_dt = pd.to_datetime(vintage_date)
            
            mask = (
                (df_raw['PRODUCT_TYPE'] == product) &
                (df_raw['RISK_SCORE'] == score) &
                (df_raw['VINTAGE_DATE'] == vintage_dt)
            )
            df_cohort = df_raw[mask]
            
            if len(df_cohort) == 0:
                continue
            
            # Aggregate by MOB and STATE
            df_agg = df_cohort.groupby(['MOB', 'STATE_MODEL']).agg({
                'AGREEMENT_ID': 'nunique',
                'PRINCIPLE_OUTSTANDING': 'sum',
                'DISBURSAL_AMOUNT': 'sum',
            }).reset_index()
            
            df_agg.columns = ['MOB', 'State', 'N_Loans', 'EAD', 'Disbursement']
            
            # Pivot to wide format
            df_pivot = df_agg.pivot(index='MOB', columns='State', values='EAD').fillna(0)
            df_pivot = df_pivot.reset_index()
            
            # Add DEL metrics
            if set(BUCKETS_30P).intersection(df_pivot.columns):
                df_pivot['DEL30'] = df_pivot[[c for c in BUCKETS_30P if c in df_pivot.columns]].sum(axis=1)
            
            if set(BUCKETS_60P).intersection(df_pivot.columns):
                df_pivot['DEL60'] = df_pivot[[c for c in BUCKETS_60P if c in df_pivot.columns]].sum(axis=1)
            
            if set(BUCKETS_90P).intersection(df_pivot.columns):
                df_pivot['DEL90'] = df_pivot[[c for c in BUCKETS_90P if c in df_pivot.columns]].sum(axis=1)
            
            df_pivot.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Format
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column('A:A', 8)
            worksheet.set_column('B:Z', 12)
        
        # ============================
        # 5. FORECAST CALCULATION STEPS
        # ============================
        calc_data = []
        
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
            
            max_mob = df_cohort['MOB'].max()
            
            # Get current state distribution
            df_latest = df_cohort[df_cohort['MOB'] == max_mob]
            
            state_dist = df_latest.groupby('STATE_MODEL')['PRINCIPLE_OUTSTANDING'].sum()
            total_ead = state_dist.sum()
            
            # Initialize vector
            v_current = pd.Series(0.0, index=BUCKETS_CANON)
            for state in state_dist.index:
                if state in v_current.index:
                    v_current[state] = state_dist[state]
            
            # Forecast step by step
            v = v_current.copy()
            
            for mob in range(max_mob, target_mob):
                # Get transition matrix
                P = None
                if product in matrices_by_mob:
                    if mob in matrices_by_mob[product]:
                        if score in matrices_by_mob[product][mob]:
                            matrix_data = matrices_by_mob[product][mob][score]
                            if isinstance(matrix_data, dict) and 'P' in matrix_data:
                                P = matrix_data['P']
                            else:
                                P = matrix_data
                
                if P is None:
                    print(f"   ⚠️ No matrix for {product}, {score}, MOB {mob}")
                    continue
                
                # Get K
                k = 1.0
                if product in k_smooth_by_mob:
                    if mob in k_smooth_by_mob[product]:
                        if score in k_smooth_by_mob[product][mob]:
                            k = k_smooth_by_mob[product][mob][score]
                
                # Markov forecast
                if isinstance(P, pd.DataFrame):
                    v_markov = v @ P
                else:
                    v_markov = v.copy()
                
                # Apply K
                v_forecast = v_markov * k
                
                # Calculate DEL
                del30 = v_forecast[[s for s in BUCKETS_30P if s in v_forecast.index]].sum()
                del60 = v_forecast[[s for s in BUCKETS_60P if s in v_forecast.index]].sum()
                del90 = v_forecast[[s for s in BUCKETS_90P if s in v_forecast.index]].sum()
                
                total = v_forecast.sum()
                
                calc_data.append({
                    'Product': product,
                    'Risk_Score': score,
                    'Vintage_Date': vintage_date,
                    'From_MOB': mob,
                    'To_MOB': mob + 1,
                    'K': k,
                    'Total_EAD': total,
                    'DEL30': del30,
                    'DEL60': del60,
                    'DEL90': del90,
                    'DEL30_PCT': del30 / total if total > 0 else 0,
                    'DEL60_PCT': del60 / total if total > 0 else 0,
                    'DEL90_PCT': del90 / total if total > 0 else 0,
                })
                
                v = v_forecast.copy()
        
        df_calc = pd.DataFrame(calc_data)
        df_calc.to_excel(writer, sheet_name='Forecast_Steps', index=False)
        
        # Format
        worksheet = writer.sheets['Forecast_Steps']
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:M', 12)
        
        # ============================
        # 6. INSTRUCTIONS
        # ============================
        instructions = [
            ['HƯỚNG DẪN SỬ DỤNG FILE NÀY'],
            [''],
            ['File này chứa tất cả thông số để tính forecast cho các cohorts cụ thể.'],
            [''],
            ['CÁC SHEET:'],
            ['1. Summary: Tổng quan các cohorts'],
            ['2. TM_*: Transition matrices theo segment (Product, Risk_Score)'],
            ['3. K_Values: Giá trị K (raw, smooth) và Alpha theo MOB'],
            ['4. Actual_*: Dữ liệu thực tế theo MOB và State'],
            ['5. Forecast_Steps: Chi tiết từng bước tính forecast'],
            [''],
            ['CÔNG THỨC TÍNH FORECAST:'],
            [''],
            ['Bước 1: Lấy state distribution tại MOB hiện tại'],
            ['  v_current = [EAD_DPD0, EAD_DPD1+, EAD_DPD30+, ...]'],
            [''],
            ['Bước 2: Forecast từng MOB'],
            ['  For mob = current_mob to target_mob:'],
            ['    1. Lấy transition matrix P tại MOB này (từ sheet TM_*)'],
            ['    2. Tính Markov forecast: v_markov = v_current @ P'],
            ['    3. Lấy K tại MOB này (từ sheet K_Values)'],
            ['    4. Apply K: v_forecast = v_markov * K'],
            ['    5. Tính DEL: DEL30 = sum(v_forecast[DPD30+, DPD60+, ...])'],
            ['    6. Update: v_current = v_forecast'],
            [''],
            ['Bước 3: Kết quả cuối cùng tại target_mob'],
            ['  DEL30_PCT = DEL30 / Total_EAD'],
            ['  DEL60_PCT = DEL60 / Total_EAD'],
            ['  DEL90_PCT = DEL90 / Total_EAD'],
            [''],
            ['VÍ DỤ:'],
            ['Cohort: Product=X, Risk_Score=A, Vintage=2024-10'],
            ['Current MOB: 2'],
            ['Target MOB: 12'],
            [''],
            ['MOB 2 → 3:'],
            ['  v_current = [1000, 100, 50, 20, ...]  (từ sheet Actual_*)'],
            ['  P = transition matrix tại MOB 2 (từ sheet TM_*)'],
            ['  v_markov = v_current @ P = [950, 120, 60, 25, ...]'],
            ['  K = 1.05 (từ sheet K_Values)'],
            ['  v_forecast = v_markov * 1.05 = [997.5, 126, 63, 26.25, ...]'],
            ['  DEL30 = 63 + 26.25 + ... = 89.25'],
            ['  DEL30_PCT = 89.25 / 1212.75 = 7.36%'],
            [''],
            ['MOB 3 → 4:'],
            ['  v_current = v_forecast từ bước trước = [997.5, 126, 63, ...]'],
            ['  ... (lặp lại)'],
            [''],
            ['... cho đến MOB 12'],
            [''],
            ['KẾT QUẢ CUỐI CÙNG:'],
            ['Xem sheet "Forecast_Steps" dòng cuối cùng (To_MOB = target_mob)'],
        ]
        
        df_instructions = pd.DataFrame(instructions, columns=['Instructions'])
        df_instructions.to_excel(writer, sheet_name='Instructions', index=False, header=False)
        
        # Format
        worksheet = writer.sheets['Instructions']
        worksheet.set_column('A:A', 100)
        
        # Merge title cell
        worksheet.merge_range('A1:A1', 'HƯỚNG DẪN SỬ DỤNG FILE NÀY', fmt_title)
    
    print(f"✅ Exported to: {filename}")
    print(f"   📊 {len(cohorts)} cohorts")
    print(f"   📄 {len(writer.sheets)} sheets")
    
    return str(filename)


if __name__ == "__main__":
    print("⚠️  Script này cần chạy sau khi đã build model trong notebook")
    print("📝 Hướng dẫn sử dụng:")
    print()
    print("# Trong notebook Final_Workflow copy, sau khi build model:")
    print()
    print("from export_cohort_details import export_cohort_forecast_details")
    print()
    print("# Define cohorts cần export")
    print("cohorts = [")
    print("    ('X', 'A', '2025-10-01'),")
    print("    ('X', 'B', '2024-10-01'),")
    print("    ('T', 'A', '2025-10-01'),")
    print("]")
    print()
    print("# Export")
    print("filename = export_cohort_forecast_details(")
    print("    cohorts=cohorts,")
    print("    df_raw=df_raw,")
    print("    matrices_by_mob=matrices_by_mob,")
    print("    k_raw_by_mob=k_raw_by_mob,")
    print("    k_smooth_by_mob=k_smooth_by_mob,")
    print("    alpha_by_mob=alpha_by_mob,")
    print("    target_mob=TARGET_MOB,")
    print("    output_dir='cohort_details',")
    print(")")
    print()
    print(f"print(f'✅ Exported: {{filename}}')")
