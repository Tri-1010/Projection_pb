"""
Test ảnh hưởng của seed parameter lên kết quả allocation
"""
import numpy as np
import pandas as pd
from src.rollrate.allocation_v2_fast import allocate_multi_mob_fast


def test_seed_impact(
    df_loans_latest,
    df_lifecycle_final,
    matrices_by_mob,
    target_mobs,
    parent_fallback,
    seeds=[42, 100, 200, 300, 500],
):
    """
    Test ảnh hưởng của seed lên kết quả allocation.
    
    Parameters
    ----------
    seeds : list
        Danh sách seeds để test
    
    Returns
    -------
    pd.DataFrame
        Kết quả so sánh giữa các seeds
    """
    
    print("="*60)
    print("🧪 TEST: Ảnh Hưởng Của seed Parameter")
    print("="*60)
    print(f"📊 Data: {len(df_loans_latest):,} loans")
    print(f"🎯 Target MOBs: {target_mobs}")
    print(f"🎲 Seeds to test: {seeds}")
    print()
    
    results = []
    dfs = {}
    
    for seed in seeds:
        print(f"Testing seed={seed}...")
        
        df_result = allocate_multi_mob_fast(
            df_loans_latest=df_loans_latest,
            df_lifecycle_final=df_lifecycle_final,
            matrices_by_mob=matrices_by_mob,
            target_mobs=target_mobs,
            parent_fallback=parent_fallback,
            seed=seed,  # ← Thay đổi seed
        )
        
        # Tính metrics
        total_disb = df_result['DISBURSAL_AMOUNT'].sum()
        
        if 'EAD_DEL30' in df_result.columns:
            del30_rate = df_result['EAD_DEL30'].sum() / total_disb if total_disb > 0 else 0
        else:
            del30_rate = None
        
        if 'EAD_DEL60' in df_result.columns:
            del60_rate = df_result['EAD_DEL60'].sum() / total_disb if total_disb > 0 else 0
        else:
            del60_rate = None
        
        if 'EAD_DEL90' in df_result.columns:
            del90_rate = df_result['EAD_DEL90'].sum() / total_disb if total_disb > 0 else 0
        else:
            del90_rate = None
        
        # State distribution
        state_dist = df_result['STATE_FORECAST'].value_counts(normalize=True).to_dict()
        
        results.append({
            'seed': seed,
            'n_loans': len(df_result),
            'total_disb': total_disb,
            'DEL30_rate': del30_rate,
            'DEL60_rate': del60_rate,
            'DEL90_rate': del90_rate,
            'state_dist': state_dist,
        })
        
        dfs[seed] = df_result
        
        print(f"   ✅ DEL30: {del30_rate*100:.3f}%, DEL90: {del90_rate*100:.3f}%")
        print()
    
    # ============================
    # So sánh kết quả
    # ============================
    print("="*60)
    print("📊 SO SÁNH KẾT QUẢ")
    print("="*60)
    
    df_compare = pd.DataFrame(results)
    
    print("\n📈 DEL Rates:")
    print(df_compare[['seed', 'DEL30_rate', 'DEL60_rate', 'DEL90_rate']])
    
    # Tính std dev
    if 'DEL30_rate' in df_compare.columns and df_compare['DEL30_rate'].notna().any():
        std_del30 = df_compare['DEL30_rate'].std()
        mean_del30 = df_compare['DEL30_rate'].mean()
        print(f"\nDEL30 Statistics:")
        print(f"   Mean:   {mean_del30*100:.4f}%")
        print(f"   Std:    {std_del30*100:.4f}%")
        print(f"   CV:     {std_del30/mean_del30*100:.2f}%")
    
    if 'DEL90_rate' in df_compare.columns and df_compare['DEL90_rate'].notna().any():
        std_del90 = df_compare['DEL90_rate'].std()
        mean_del90 = df_compare['DEL90_rate'].mean()
        print(f"\nDEL90 Statistics:")
        print(f"   Mean:   {mean_del90*100:.4f}%")
        print(f"   Std:    {std_del90*100:.4f}%")
        print(f"   CV:     {std_del90/mean_del90*100:.2f}%")
    
    # So sánh state distribution
    print("\n📊 State Distribution (seed=42 vs seed=100):")
    if 42 in dfs and 100 in dfs:
        dist_42 = dfs[42]['STATE_FORECAST'].value_counts(normalize=True)
        dist_100 = dfs[100]['STATE_FORECAST'].value_counts(normalize=True)
        
        df_dist = pd.DataFrame({
            'seed=42': dist_42,
            'seed=100': dist_100,
        }).fillna(0)
        df_dist['diff'] = (df_dist['seed=100'] - df_dist['seed=42']) * 100
        
        print(df_dist)
    
    # ============================
    # Kết luận
    # ============================
    print("\n" + "="*60)
    print("🎓 KẾT LUẬN")
    print("="*60)
    
    if 'DEL90_rate' in df_compare.columns and df_compare['DEL90_rate'].notna().any():
        max_diff = df_compare['DEL90_rate'].max() - df_compare['DEL90_rate'].min()
        print(f"\n📊 DEL90 Range: {max_diff*100:.4f}%")
        
        if max_diff < 0.0001:  # < 0.01%
            print("   ✅ Sai số RẤT NHỎ (< 0.01%)")
            print("   ✅ seed KHÔNG ảnh hưởng đến kết quả")
            print("   ✅ Có thể dùng seed BẤT KỲ")
        elif max_diff < 0.001:  # < 0.1%
            print("   ✅ Sai số NHỎ (< 0.1%)")
            print("   ✅ seed ảnh hưởng NEGLIGIBLE")
            print("   ✅ Nên dùng seed CỐ ĐỊNH (42) để reproducible")
        else:
            print("   ⚠️  Sai số LỚN (>= 0.1%)")
            print("   ⚠️  Cần kiểm tra lại logic")
    
    print("\n💡 KHUYẾN NGHỊ:")
    print("   ✅ Giữ nguyên seed=42 (default)")
    print("   ✅ Reproducible và dễ debug")
    print("   ✅ Không cần thay đổi")
    
    print("="*60)
    
    return df_compare, dfs


def compare_individual_loans(df1, df2, n_samples=10):
    """
    So sánh STATE_FORECAST của individual loans giữa 2 seeds.
    """
    print("\n🔍 So Sánh Individual Loans (seed=42 vs seed=100)")
    print("="*60)
    
    # Merge 2 dataframes
    loan_col = 'AGREEMENT_ID'
    
    df_merged = df1[[loan_col, 'STATE_FORECAST', 'EAD_FORECAST']].merge(
        df2[[loan_col, 'STATE_FORECAST', 'EAD_FORECAST']],
        on=loan_col,
        suffixes=('_42', '_100')
    )
    
    # Đếm số loans có state khác nhau
    n_diff = (df_merged['STATE_FORECAST_42'] != df_merged['STATE_FORECAST_100']).sum()
    pct_diff = n_diff / len(df_merged) * 100
    
    print(f"\n📊 Tổng số loans: {len(df_merged):,}")
    print(f"📊 Loans có STATE khác nhau: {n_diff:,} ({pct_diff:.2f}%)")
    print(f"📊 Loans có STATE giống nhau: {len(df_merged)-n_diff:,} ({100-pct_diff:.2f}%)")
    
    # Sample một số loans khác nhau
    df_diff = df_merged[df_merged['STATE_FORECAST_42'] != df_merged['STATE_FORECAST_100']]
    
    if len(df_diff) > 0:
        print(f"\n📋 Sample {min(n_samples, len(df_diff))} loans có STATE khác nhau:")
        print(df_diff.head(n_samples))
    
    # So sánh EAD
    ead_diff = (df_merged['EAD_FORECAST_42'] - df_merged['EAD_FORECAST_100']).abs()
    print(f"\n📊 EAD Difference:")
    print(f"   Mean:   {ead_diff.mean():.6f}")
    print(f"   Median: {ead_diff.median():.6f}")
    print(f"   Max:    {ead_diff.max():.6f}")
    
    print("="*60)


if __name__ == "__main__":
    print("⚠️  Script này cần chạy sau khi đã load data trong notebook")
    print("📝 Hướng dẫn sử dụng:")
    print()
    print("# Trong notebook Final_Workflow, sau khi load data:")
    print()
    print("from test_seed_impact import test_seed_impact, compare_individual_loans")
    print()
    print("# Test nhiều seeds")
    print("df_compare, dfs = test_seed_impact(")
    print("    df_loans_latest=df_loans_latest,")
    print("    df_lifecycle_final=df_lifecycle_final,")
    print("    matrices_by_mob=matrices_by_mob,")
    print("    target_mobs=TARGET_MOBS,")
    print("    parent_fallback=parent_fallback,")
    print("    seeds=[42, 100, 200, 300, 500],")
    print(")")
    print()
    print("# So sánh individual loans")
    print("compare_individual_loans(dfs[42], dfs[100])")
