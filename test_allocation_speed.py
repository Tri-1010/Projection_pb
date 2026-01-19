"""
Test và so sánh tốc độ các hàm allocation
"""
import time
import pandas as pd
from pathlib import Path

# Import các hàm allocation
from src.rollrate.allocation_v2_fast import allocate_multi_mob_fast
from src.rollrate.allocation_v2_ultra_fast import allocate_multi_mob_ultra_fast
from src.rollrate.allocation_v2_optimized import allocate_multi_mob_optimized


def test_allocation_speed(
    df_raw,
    df_loans_latest,
    df_lifecycle_final,
    matrices_by_mob,
    target_mobs,
    parent_fallback,
):
    """
    Test tốc độ của 3 versions allocation.
    
    Returns
    -------
    dict
        Kết quả benchmark với thời gian và speedup
    """
    
    results = {}
    
    print("="*60)
    print("🧪 BENCHMARK: So Sánh Tốc Độ Allocation")
    print("="*60)
    print(f"📊 Data: {len(df_loans_latest):,} loans")
    print(f"🎯 Target MOBs: {target_mobs}")
    print()
    
    # ============================
    # 1. Test v2_optimized (current)
    # ============================
    print("1️⃣ Testing v2_optimized (current)...")
    start = time.time()
    
    df_opt = allocate_multi_mob_optimized(
        df_raw=df_raw,
        df_loans_latest=df_loans_latest,
        df_lifecycle_final=df_lifecycle_final,
        matrices_by_mob=matrices_by_mob,
        target_mobs=target_mobs,
        parent_fallback=parent_fallback,
    )
    
    time_opt = time.time() - start
    results['v2_optimized'] = {
        'time_seconds': time_opt,
        'time_minutes': time_opt / 60,
        'df': df_opt,
    }
    
    print(f"   ✅ Hoàn thành: {time_opt:.1f}s ({time_opt/60:.2f} phút)")
    print(f"   📊 Output: {len(df_opt):,} rows")
    print()
    
    # ============================
    # 2. Test v2_fast
    # ============================
    print("2️⃣ Testing v2_fast...")
    start = time.time()
    
    df_fast = allocate_multi_mob_fast(
        df_loans_latest=df_loans_latest,
        df_lifecycle_final=df_lifecycle_final,
        matrices_by_mob=matrices_by_mob,
        target_mobs=target_mobs,
        parent_fallback=parent_fallback,
    )
    
    time_fast = time.time() - start
    results['v2_fast'] = {
        'time_seconds': time_fast,
        'time_minutes': time_fast / 60,
        'df': df_fast,
    }
    
    print(f"   ✅ Hoàn thành: {time_fast:.1f}s ({time_fast/60:.2f} phút)")
    print(f"   📊 Output: {len(df_fast):,} rows")
    print()
    
    # ============================
    # 3. Test v2_ultra_fast
    # ============================
    print("3️⃣ Testing v2_ultra_fast...")
    start = time.time()
    
    df_ultra = allocate_multi_mob_ultra_fast(
        df_loans_latest=df_loans_latest,
        df_lifecycle_final=df_lifecycle_final,
        matrices_by_mob=matrices_by_mob,
        target_mobs=target_mobs,
        parent_fallback=parent_fallback,
    )
    
    time_ultra = time.time() - start
    results['v2_ultra_fast'] = {
        'time_seconds': time_ultra,
        'time_minutes': time_ultra / 60,
        'df': df_ultra,
    }
    
    print(f"   ✅ Hoàn thành: {time_ultra:.1f}s ({time_ultra/60:.2f} phút)")
    print(f"   📊 Output: {len(df_ultra):,} rows")
    print()
    
    # ============================
    # 4. So sánh
    # ============================
    print("="*60)
    print("📊 KẾT QUẢ SO SÁNH")
    print("="*60)
    
    print(f"\n⏱️  Thời Gian:")
    print(f"   v2_optimized:  {time_opt:>8.1f}s ({time_opt/60:>6.2f} phút)")
    print(f"   v2_fast:       {time_fast:>8.1f}s ({time_fast/60:>6.2f} phút)")
    print(f"   v2_ultra_fast: {time_ultra:>8.1f}s ({time_ultra/60:>6.2f} phút)")
    
    print(f"\n🚀 Speedup (so với v2_optimized):")
    print(f"   v2_fast:       {time_opt/time_fast:>6.2f}x")
    print(f"   v2_ultra_fast: {time_opt/time_ultra:>6.2f}x")
    
    print(f"\n🚀 Speedup (v2_ultra_fast so với v2_fast):")
    print(f"   {time_fast/time_ultra:>6.2f}x")
    
    # ============================
    # 5. Verify output consistency
    # ============================
    print(f"\n✅ Kiểm Tra Output:")
    
    # Check số lượng rows
    if len(df_opt) == len(df_fast) == len(df_ultra):
        print(f"   ✅ Số rows giống nhau: {len(df_opt):,}")
    else:
        print(f"   ⚠️  Số rows khác nhau:")
        print(f"      v2_optimized:  {len(df_opt):,}")
        print(f"      v2_fast:       {len(df_fast):,}")
        print(f"      v2_ultra_fast: {len(df_ultra):,}")
    
    # Check columns
    cols_opt = set(df_opt.columns)
    cols_fast = set(df_fast.columns)
    cols_ultra = set(df_ultra.columns)
    
    if cols_opt == cols_fast == cols_ultra:
        print(f"   ✅ Columns giống nhau: {len(cols_opt)} columns")
    else:
        print(f"   ⚠️  Columns khác nhau:")
        print(f"      v2_optimized:  {len(cols_opt)}")
        print(f"      v2_fast:       {len(cols_fast)}")
        print(f"      v2_ultra_fast: {len(cols_ultra)}")
    
    # ============================
    # 6. Recommendation
    # ============================
    print(f"\n💡 KHUYẾN NGHỊ:")
    
    fastest = min(results.items(), key=lambda x: x[1]['time_seconds'])
    print(f"   🏆 Nhanh nhất: {fastest[0]} ({fastest[1]['time_minutes']:.2f} phút)")
    
    if fastest[0] == 'v2_ultra_fast':
        speedup = time_opt / time_ultra
        print(f"   🚀 Nhanh hơn current {speedup:.1f}x")
        print(f"   ✅ Nên chuyển sang v2_ultra_fast để tăng tốc độ!")
    elif fastest[0] == 'v2_fast':
        speedup = time_opt / time_fast
        print(f"   🚀 Nhanh hơn current {speedup:.1f}x")
        print(f"   ✅ Nên chuyển sang v2_fast!")
    else:
        print(f"   ✅ Current (v2_optimized) đã là tốt nhất!")
    
    print("="*60)
    
    return results


def compare_output_quality(df1, df2, name1="v1", name2="v2"):
    """
    So sánh chất lượng output giữa 2 versions.
    """
    print(f"\n🔍 So Sánh Output: {name1} vs {name2}")
    print("="*60)
    
    # Check DEL metrics
    for col in ['EAD_DEL30', 'EAD_DEL60', 'EAD_DEL90']:
        if col in df1.columns and col in df2.columns:
            sum1 = df1[col].sum()
            sum2 = df2[col].sum()
            diff_pct = abs(sum1 - sum2) / sum1 * 100 if sum1 > 0 else 0
            
            print(f"\n{col}:")
            print(f"   {name1}: {sum1:,.2f}")
            print(f"   {name2}: {sum2:,.2f}")
            print(f"   Diff:  {diff_pct:.2f}%")
            
            if diff_pct < 0.1:
                print(f"   ✅ Giống nhau (diff < 0.1%)")
            elif diff_pct < 1.0:
                print(f"   ⚠️  Khác nhau nhẹ (diff < 1%)")
            else:
                print(f"   ❌ Khác nhau nhiều (diff >= 1%)")
    
    print("="*60)


if __name__ == "__main__":
    print("⚠️  Script này cần chạy sau khi đã load data trong notebook")
    print("📝 Hướng dẫn sử dụng:")
    print()
    print("# Trong notebook Final_Workflow, sau khi load data:")
    print()
    print("from test_allocation_speed import test_allocation_speed, compare_output_quality")
    print()
    print("results = test_allocation_speed(")
    print("    df_raw=df_raw,")
    print("    df_loans_latest=df_loans_latest,")
    print("    df_lifecycle_final=df_lifecycle_final,")
    print("    matrices_by_mob=matrices_by_mob,")
    print("    target_mobs=TARGET_MOBS,")
    print("    parent_fallback=parent_fallback,")
    print(")")
    print()
    print("# So sánh output")
    print("compare_output_quality(")
    print("    results['v2_optimized']['df'],")
    print("    results['v2_ultra_fast']['df'],")
    print("    'v2_optimized',")
    print("    'v2_ultra_fast'")
    print(")")
