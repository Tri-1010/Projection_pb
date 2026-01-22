"""
Verify that notebook has V3 export code with K values
"""
import json

print("="*70)
print("🔍 Verifying V3 Export Cell in Final_Workflow copy.ipynb")
print("="*70)

# Read notebook
with open('notebooks/Final_Workflow copy.ipynb', 'r', encoding='utf-8') as f:
    notebook = json.load(f)

print(f"\n📊 Notebook info:")
print(f"   Total cells: {len(notebook['cells'])}")

# Find export cell
export_cell = None
export_cell_index = None

for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'EXPORT COHORTS' in source or 'export_cohort_forecast_details' in source:
            export_cell = cell
            export_cell_index = i
            break

if export_cell is None:
    print("\n❌ Export cell not found!")
    exit(1)

print(f"   Export cell: Found at position {export_cell_index + 1}")

# Check cell content
source = ''.join(export_cell['source'])

# Check version
if 'export_cohort_forecast_details_v3' in source:
    version = "V3"
    print(f"   Version: ✅ V3 (Full layout with K values)")
elif 'export_cohort_forecast_details_v2' in source:
    version = "V2"
    print(f"   Version: ⚠️  V2 (Missing K values)")
elif 'export_cohort_forecast_details' in source:
    version = "V1"
    print(f"   Version: ⚠️  V1 (Old version)")
else:
    version = "Unknown"
    print(f"   Version: ❌ Unknown")

# Required components for V3
checks = {
    'Import v3 function': 'from export_cohort_details_v3 import export_cohort_forecast_details_v3' in source,
    'VINTAGE_DATE creation': 'parse_date_column' in source and 'VINTAGE_DATE' in source,
    'Target months': 'target_months' in source and '2025-10-01' in source and '2025-01-01' in source,
    'Find cohorts': 'all_cohorts' in source and 'groupby' in source,
    'Alpha conversion': 'alpha_by_mob' in source and 'if \'alpha\' in globals()' in source,
    'V3 export call': 'export_cohort_forecast_details_v3(' in source,
    'Success message': 'HOÀN THÀNH' in source or 'Done' in source,
}

print("\n✅ Checking V3 export cell components:")
all_passed = True
for check_name, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"   {status} {check_name}")
    if not passed:
        all_passed = False

# Check for V3 specific features
print("\n🔧 Checking V3 specific features:")

v3_features = {
    'K values mentioned': 'K_raw, K_smooth, Alpha' in source or 'K values' in source,
    'Full layout message': 'full layout' in source.lower() or 'đầy đủ' in source,
    'V3 in output filename': 'v3' in source.lower(),
}

for feature_name, passed in v3_features.items():
    status = "✅" if passed else "⚠️ "
    print(f"   {status} {feature_name}")
    if not passed:
        all_passed = False

# Summary
print("\n" + "="*70)
if all_passed and version == "V3":
    print("✅ ALL CHECKS PASSED - V3 IS READY!")
    print("="*70)
    print("\n🎉 Notebook has V3 export code with K values!")
    print("\n📝 V3 Layout includes:")
    print("   - Row 2-4: Current balance & loans (ngang)")
    print("   - Row 6-9: K_raw, K_smooth, Alpha (ngang)")
    print("   - Row 11+: Transition matrices (ngang)")
    print("\n💡 Next steps:")
    print("   1. Open notebook: jupyter notebook 'notebooks/Final_Workflow copy.ipynb'")
    print("   2. Run all cells: Cell → Run All")
    print("   3. Check output: cohort_details/Cohort_Forecast_Details_v3_*.xlsx")
    print("   4. Write Excel formulas using K values from row 8")
else:
    print("⚠️  SOME CHECKS FAILED OR NOT V3")
    print("="*70)
    if version != "V3":
        print(f"\n❌ Current version: {version}")
        print("   Expected: V3")
        print("\n💡 Solution:")
        print("   Run: python update_notebook_with_v3.py")
    else:
        print("\n❌ Some components missing")
        print("\n💡 Solution:")
        print("   Run: python update_notebook_with_v3.py")

print("\n" + "="*70)

# Show preview of export cell
print("\n📄 Export cell preview (first 30 lines):")
print("-"*70)
lines = source.split('\n')
for i, line in enumerate(lines[:30], 1):
    print(f"{i:3d} | {line}")
if len(lines) > 30:
    print(f"... ({len(lines) - 30} more lines)")
print("-"*70)
