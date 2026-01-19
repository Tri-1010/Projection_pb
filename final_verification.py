"""
Final verification - Check if notebook will run without errors
"""
import json
from pathlib import Path

print("🔍 Final Verification of Final_Workflow.ipynb\n")
print("=" * 60)

# Read notebook
notebook_path = Path("notebooks/Final_Workflow.ipynb")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Check critical variables for export cell
print("CHECKING CRITICAL VARIABLES FOR EXPORT")
print("=" * 60)

variables_to_check = {
    'df_del_all': False,
    'actual_info_all': False,
    'df_loan_forecast': False,
    'df_raw': False,
    # config_params is created in export cell itself, so we don't check it
}

export_cell_index = None

for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    
    source = ''.join(cell['source'])
    
    # Check if this is the export cell
    if 'export_lifecycle_with_config_info' in source and 'df_del_all' in source:
        export_cell_index = i
        print(f"\n📍 Export cell found at index {i}\n")
        continue
    
    # Track variable definitions before export cell
    if export_cell_index is None:
        for var in variables_to_check:
            if f'{var} =' in source or f'{var}=' in source:
                variables_to_check[var] = True
                print(f"✅ Cell {i}: Defines {var}")

print("\n" + "=" * 60)
print("VERIFICATION RESULTS")
print("=" * 60)

all_ok = True
for var, defined in variables_to_check.items():
    if defined:
        print(f"✅ {var:20s} - Defined before export")
    else:
        print(f"❌ {var:20s} - NOT defined before export")
        all_ok = False

print("\n" + "=" * 60)
print("CHECKING IMPORTS")
print("=" * 60)

critical_imports = [
    'export_lifecycle_with_config_info',
    'export_loan_forecast_excel',
    'aggregate_to_product',
    'aggregate_products_to_portfolio',
    'extend_actual_info_with_portfolio',
]

imports_found = {imp: False for imp in critical_imports}

for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        for imp in critical_imports:
            if imp in source and ('import' in source or 'from' in source):
                imports_found[imp] = True

for imp, found in imports_found.items():
    if found:
        print(f"✅ {imp}")
    else:
        print(f"❌ {imp} - NOT imported")
        all_ok = False

print("\n" + "=" * 60)
print("FINAL STATUS")
print("=" * 60)

if all_ok:
    print("\n🎉 NOTEBOOK IS READY TO RUN!")
    print("\n✅ All critical variables are defined")
    print("✅ All critical imports are present")
    print("✅ Export cell should work without errors")
    print("\n📝 Next steps:")
    print("   1. jupyter notebook notebooks/Final_Workflow.ipynb")
    print("   2. Run all cells")
    print("   3. Check outputs/ folder for results")
else:
    print("\n❌ NOTEBOOK HAS ISSUES!")
    print("\n⚠️ Please fix the issues above before running")
    
    # Provide specific fixes
    if not variables_to_check['df_del_all'] or not variables_to_check['actual_info_all']:
        print("\n💡 Fix: Run fix_missing_aggregation.py again")
    
    if not imports_found['export_lifecycle_with_config_info']:
        print("\n💡 Fix: Run fix_import_final_workflow.py again")

print("\n" + "=" * 60)
