"""
Comprehensive verification of Final_Workflow notebook
"""
import json
from pathlib import Path

print("🔍 Verifying Final_Workflow.ipynb...\n")

# Read notebook
notebook_path = Path("notebooks/Final_Workflow.ipynb")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Track variables
variables_defined = set()
variables_used = set()
issues = []

print("=" * 60)
print("CHECKING VARIABLE DEFINITIONS AND USAGE")
print("=" * 60)

for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    
    source = ''.join(cell['source'])
    
    # Skip empty cells
    if not source.strip():
        continue
    
    # Track variable definitions
    if 'df_raw =' in source or 'df_raw=' in source:
        variables_defined.add('df_raw')
        print(f"✅ Cell {i}: Defines df_raw")
    
    if 'df_lifecycle_final =' in source or 'df_lifecycle_final=' in source:
        variables_defined.add('df_lifecycle_final')
        print(f"✅ Cell {i}: Defines df_lifecycle_final")
    
    if 'df_del_all =' in source or 'df_del_all=' in source:
        variables_defined.add('df_del_all')
        print(f"✅ Cell {i}: Defines df_del_all")
    
    if 'actual_info_all =' in source or 'actual_info_all=' in source:
        variables_defined.add('actual_info_all')
        print(f"✅ Cell {i}: Defines actual_info_all")
    
    if 'df_loan_forecast =' in source or 'df_loan_forecast=' in source:
        variables_defined.add('df_loan_forecast')
        print(f"✅ Cell {i}: Defines df_loan_forecast")
    
    if 'matrices_by_mob =' in source or 'matrices_by_mob=' in source:
        variables_defined.add('matrices_by_mob')
        print(f"✅ Cell {i}: Defines matrices_by_mob")
    
    if 'actual_results =' in source or 'actual_results=' in source:
        variables_defined.add('actual_results')
        print(f"✅ Cell {i}: Defines actual_results")
    
    if 'forecast_calibrated =' in source or 'forecast_calibrated=' in source:
        variables_defined.add('forecast_calibrated')
        print(f"✅ Cell {i}: Defines forecast_calibrated")
    
    if 'df_loans_latest =' in source or 'df_loans_latest=' in source:
        variables_defined.add('df_loans_latest')
        print(f"✅ Cell {i}: Defines df_loans_latest")
    
    # Track variable usage (excluding definitions)
    for var in ['df_raw', 'df_lifecycle_final', 'df_del_all', 'actual_info_all', 
                'df_loan_forecast', 'matrices_by_mob', 'actual_results', 
                'forecast_calibrated', 'df_loans_latest']:
        # Check if variable is used (not just defined)
        if var in source and f'{var} =' not in source and f'{var}=' not in source:
            variables_used.add(var)
            # Check if it's defined before use
            if var not in variables_defined:
                issues.append(f"❌ Cell {i}: Uses '{var}' before it's defined")
                print(f"❌ Cell {i}: Uses '{var}' before it's defined")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print("\n✅ Variables Defined:")
for var in sorted(variables_defined):
    print(f"   • {var}")

print("\n📊 Variables Used:")
for var in sorted(variables_used):
    print(f"   • {var}")

print("\n🔍 Checking Required Variables for Export:")
required_for_export = ['df_del_all', 'actual_info_all', 'df_loan_forecast', 'df_raw']
missing = []
for var in required_for_export:
    if var in variables_defined:
        print(f"   ✅ {var}")
    else:
        print(f"   ❌ {var} - NOT DEFINED")
        missing.append(var)

if issues:
    print("\n" + "=" * 60)
    print("⚠️ ISSUES FOUND")
    print("=" * 60)
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n" + "=" * 60)
    print("✅ NO ISSUES FOUND")
    print("=" * 60)

if missing:
    print("\n" + "=" * 60)
    print("❌ MISSING REQUIRED VARIABLES")
    print("=" * 60)
    for var in missing:
        print(f"   • {var}")
    print("\n⚠️ Export cell will fail!")
else:
    print("\n🎉 All required variables are defined!")
    print("✅ Notebook should run without errors!")

# Check imports
print("\n" + "=" * 60)
print("CHECKING IMPORTS")
print("=" * 60)

required_imports = [
    'export_lifecycle_with_config_info',
    'aggregate_to_product',
    'aggregate_products_to_portfolio',
    'extend_actual_info_with_portfolio',
    'combine_all_lifecycle_amount',
    'add_del_metrics',
]

for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        for imp in required_imports:
            if imp in source and 'import' in source:
                print(f"✅ {imp}")
                required_imports.remove(imp)
                break

if required_imports:
    print("\n⚠️ Missing imports:")
    for imp in required_imports:
        print(f"   ❌ {imp}")
else:
    print("\n✅ All required imports found!")

print("\n" + "=" * 60)
print("FINAL STATUS")
print("=" * 60)

if not issues and not missing and not required_imports:
    print("✅ NOTEBOOK IS READY TO RUN!")
    print("   No issues found.")
    print("   All variables defined.")
    print("   All imports present.")
else:
    print("❌ NOTEBOOK HAS ISSUES!")
    if issues:
        print(f"   • {len(issues)} variable usage issues")
    if missing:
        print(f"   • {len(missing)} missing required variables")
    if required_imports:
        print(f"   • {len(required_imports)} missing imports")
