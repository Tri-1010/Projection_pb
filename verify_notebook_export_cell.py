"""
Verify that the export cell in Final_Workflow copy.ipynb is correct
"""
import json

print("="*70)
print("🔍 Verifying Export Cell in Final_Workflow copy.ipynb")
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
        if 'EXPORT COHORTS: 2025-10 và 2025-01' in source:
            export_cell = cell
            export_cell_index = i
            break

if export_cell is None:
    print("\n❌ Export cell not found!")
    print("   The export code has not been added to the notebook")
    sys.exit(1)

print(f"   Export cell: Found at position {export_cell_index + 1}")

# Check cell content
source = ''.join(export_cell['source'])

# Required components
checks = {
    'Import statements': 'from export_cohort_details import export_cohort_forecast_details' in source,
    'VINTAGE_DATE creation': 'parse_date_column' in source and 'VINTAGE_DATE' in source,
    'Target months': 'target_months' in source and '2025-10-01' in source and '2025-01-01' in source,
    'Find cohorts': 'all_cohorts' in source and 'groupby' in source,
    'Alpha conversion': 'alpha_by_mob' in source and 'if \'alpha\' in globals()' in source,
    'Export call': 'export_cohort_forecast_details(' in source,
    'Success message': 'HOÀN THÀNH' in source or 'Done' in source,
}

print("\n✅ Checking export cell components:")
all_passed = True
for check_name, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"   {status} {check_name}")
    if not passed:
        all_passed = False

# Check for key fixes
print("\n🔧 Checking fixes:")

fixes = {
    'VINTAGE_DATE auto-creation': (
        'if \'VINTAGE_DATE\' not in df_raw.columns' in source and
        'parse_date_column(df_raw[\'DISBURSAL_DATE\'])' in source
    ),
    'Alpha auto-conversion': (
        'if \'alpha_by_mob\' not in globals()' in source and
        'alpha_by_mob = {mob: alpha for mob in k_raw_by_mob.keys()}' in source
    ),
}

for fix_name, passed in fixes.items():
    status = "✅" if passed else "❌"
    print(f"   {status} {fix_name}")
    if not passed:
        all_passed = False

# Summary
print("\n" + "="*70)
if all_passed:
    print("✅ ALL CHECKS PASSED!")
    print("="*70)
    print("\n🎉 The export cell is correctly configured!")
    print("\n📝 Next steps:")
    print("   1. Open notebook: jupyter notebook 'notebooks/Final_Workflow copy.ipynb'")
    print("   2. Run all cells: Cell → Run All")
    print("   3. Wait for completion")
    print("   4. Check output in cohort_details/ folder")
    print("\n💡 Expected output:")
    print("   - File: cohort_details/Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx")
    print("   - Message: 'Created alpha_by_mob from single alpha value'")
    print("   - Message: 'HOÀN THÀNH!'")
else:
    print("⚠️  SOME CHECKS FAILED")
    print("="*70)
    print("\n❌ The export cell may not work correctly")
    print("\n💡 Solution:")
    print("   Run: python add_export_cell_to_notebook_v2.py")
    print("   This will update the cell with the correct code")

print("\n" + "="*70)

# Show preview of export cell
print("\n📄 Export cell preview (first 20 lines):")
print("-"*70)
lines = source.split('\n')
for i, line in enumerate(lines[:20], 1):
    print(f"{i:3d} | {line}")
if len(lines) > 20:
    print(f"... ({len(lines) - 20} more lines)")
print("-"*70)
