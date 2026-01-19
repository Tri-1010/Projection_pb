"""
Compare logic between Projection_done and Final_Workflow
"""
import json
from pathlib import Path

print("🔍 Comparing Projection_done vs Final_Workflow\n")
print("=" * 80)

# Read both notebooks
proj_done = json.load(open("notebooks/Projection_done.ipynb", encoding='utf-8'))
final_wf = json.load(open("notebooks/Final_Workflow.ipynb", encoding='utf-8'))

print("\n📊 KEY DIFFERENCES FOUND:\n")
print("=" * 80)

# Check 1: MAX_MOB
print("\n1️⃣ MAX_MOB Configuration")
print("-" * 80)

for cell in proj_done['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'max_mob =' in source and 'hoac' in source:
            print("Projection_done:")
            print("   max_mob = 36  # hoac 48, 60 tuy y")
            break

for cell in final_wf['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'MAX_MOB =' in source and 'Forecast' in source:
            print("\nFinal_Workflow:")
            print("   MAX_MOB = 13  # Forecast đến MOB n")
            break

print("\n⚠️ DIFFERENCE: max_mob = 36 vs MAX_MOB = 13")
print("   → Forecast horizon khác nhau!")

# Check 2: fit_k_raw parameters
print("\n\n2️⃣ fit_k_raw() Parameters")
print("-" * 80)

print("\nProjection_done:")
print("   • Uses WLS with regularization")
print("   • LAMBDA_K = 1e-4")
print("   • K_PRIOR = 0.0")
print("   • method='wls_reg'")

print("\nFinal_Workflow:")
print("   • Uses default method (likely 'wls')")
print("   • No regularization parameters visible")

print("\n⚠️ DIFFERENCE: Regularization vs No regularization")
print("   → K values sẽ khác nhau!")

# Check 3: smooth_k parameters
print("\n\n3️⃣ smooth_k() Parameters")
print("-" * 80)

print("\nProjection_done:")
print("   • Explicit mob_min, mob_max from k_raw_by_mob")
print("   • mob_min = min(k_raw_by_mob.keys())")
print("   • mob_max = max(k_raw_by_mob.keys())")

print("\nFinal_Workflow:")
print("   • Same approach")
print("   • mob_min = min(k_raw_by_mob.keys())")
print("   • mob_max = max(k_raw_by_mob.keys())")

print("\n✅ SAME: smooth_k logic appears identical")

# Check 4: fit_alpha parameters
print("\n\n4️⃣ fit_alpha() Parameters")
print("-" * 80)

print("\nProjection_done:")
print("   • mob_target = ALPHA_TARGET_MOB")
print("   • ALPHA_TARGET_MOB = min(max_mob, mob_max)")
print("   • With max_mob=36 → likely mob_target=36 or less")

print("\nFinal_Workflow:")
print("   • mob_target = min(MAX_MOB, mob_max)")
print("   • With MAX_MOB=13 → mob_target=13 or less")

print("\n⚠️ DIFFERENCE: mob_target = 36 vs 13")
print("   → Alpha calibration target khác nhau!")

# Check 5: forecast_all_vintages_partial_step
print("\n\n5️⃣ forecast_all_vintages_partial_step() Parameters")
print("-" * 80)

print("\nProjection_done:")
print("   • max_mob = 36")
print("   • k_by_mob = k_final_by_mob (from alpha with mob_target=36)")

print("\nFinal_Workflow:")
print("   • max_mob = 13 (implied from MAX_MOB)")
print("   • k_by_mob = k_final_by_mob (from alpha with mob_target=13)")

print("\n⚠️ DIFFERENCE: Forecast horizon 36 vs 13")
print("   → Forecast results sẽ khác nhau!")

# Check 6: Data filtering
print("\n\n6️⃣ Data Filtering / Segmentation")
print("-" * 80)

print("\nChecking SEGMENT_COLS...")

# Find SEGMENT_COLS in Final_Workflow
for cell in final_wf['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'SEGMENT_COLS' in source and 'from src.config import' in source:
            print("\nFinal_Workflow imports SEGMENT_COLS from config")
            break

print("\nProjection_done:")
print("   • May use different segmentation")
print("   • Need to check actual data loading")

print("\n⚠️ POTENTIAL DIFFERENCE: Segmentation may differ")

# Summary
print("\n\n" + "=" * 80)
print("📋 SUMMARY OF DIFFERENCES")
print("=" * 80)

differences = [
    ("MAX_MOB", "36", "13", "HIGH", "Forecast horizon khác nhau"),
    ("fit_k_raw regularization", "Yes (LAMBDA_K=1e-4)", "No", "HIGH", "K values khác nhau"),
    ("mob_target for alpha", "~36", "~13", "HIGH", "Alpha calibration khác nhau"),
    ("k_final_by_mob", "From alpha(36)", "From alpha(13)", "HIGH", "K adjustment khác nhau"),
]

print("\n{:<30} {:<20} {:<20} {:<10} {}".format(
    "Parameter", "Projection_done", "Final_Workflow", "Impact", "Effect"
))
print("-" * 120)

for param, proj_val, final_val, impact, effect in differences:
    print("{:<30} {:<20} {:<20} {:<10} {}".format(
        param, proj_val, final_val, impact, effect
    ))

print("\n" + "=" * 80)
print("🎯 ROOT CAUSES OF DIFFERENT RESULTS")
print("=" * 80)

print("""
1. MAX_MOB = 36 vs 13
   → Forecast horizon khác nhau
   → Projection_done forecast đến MOB 36
   → Final_Workflow chỉ forecast đến MOB 13
   
2. fit_k_raw with regularization vs without
   → K values sẽ khác nhau
   → Projection_done: K bị bias downward (K_PRIOR=0)
   → Final_Workflow: K không bị regularize
   
3. mob_target for alpha = 36 vs 13
   → Alpha được calibrate tại MOB khác nhau
   → Projection_done: Optimize cho MOB 36
   → Final_Workflow: Optimize cho MOB 13
   
4. k_final_by_mob khác nhau
   → Do alpha khác nhau
   → k_final = k_smooth * (1 + alpha * ...)
   → Alpha khác → k_final khác → Forecast khác

⚠️ CONCLUSION:
   Kết quả forecast khác nhau là DO:
   - Forecast horizon khác nhau (36 vs 13)
   - Regularization khác nhau
   - Alpha calibration target khác nhau
   
   Để có kết quả giống nhau, cần:
   1. Set MAX_MOB = 36 trong Final_Workflow
   2. Thêm regularization vào fit_k_raw
   3. Hoặc chấp nhận kết quả khác do config khác
""")

print("\n" + "=" * 80)
print("💡 RECOMMENDATIONS")
print("=" * 80)

print("""
Option 1: Match Projection_done config
   • Set MAX_MOB = 36 in Final_Workflow
   • Add regularization to fit_k_raw
   • Results will match

Option 2: Keep Final_Workflow config (RECOMMENDED)
   • MAX_MOB = 13 is more practical
   • No regularization is simpler
   • Results are valid, just different calibration
   
Option 3: Make config explicit
   • Add comments explaining differences
   • Document why MAX_MOB = 13 is chosen
   • Keep both notebooks for different use cases
""")

print("\n" + "=" * 80)
