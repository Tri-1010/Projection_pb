"""
Script to update Final_Workflow.ipynb with enhanced export function
"""
import json
from pathlib import Path

# Read the notebook
notebook_path = Path("notebooks/Final_Workflow.ipynb")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find the import cell (cell 0) and add the new import
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code' and 'from src.rollrate.lifecycle import' in ''.join(cell['source']):
        # Add import for the new function
        source_lines = cell['source']
        
        # Find the line with export_lifecycle_all_products_one_file
        for j, line in enumerate(source_lines):
            if 'export_lifecycle_all_products_one_file' in line:
                # Add the new import after this line
                source_lines.insert(j + 1, '    export_lifecycle_with_config_info,\n')
                break
        
        # Also add import for the module
        if 'from src.rollrate.lifecycle_export_enhanced import' not in ''.join(source_lines):
            # Add at the end before print statement
            for j, line in enumerate(source_lines):
                if 'print(' in line:
                    source_lines.insert(j, 'from src.rollrate.lifecycle_export_enhanced import export_lifecycle_with_config_info\n')
                    break
        
        cell['source'] = source_lines
        print(f"✅ Updated import cell (cell {i})")
        break

# Find the export cell and update it
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code' and 'print("💾 Exporting...")' in ''.join(cell['source']):
        # This is the export cell
        new_source = [
            'print("💾 Exporting...")\n',
            '\n',
            'output_dir = Path("outputs")\n',
            'output_dir.mkdir(exist_ok=True)\n',
            '\n',
            'timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")\n',
            '\n',
            '# ============================\n',
            '# 1. Lifecycle với Config Info\n',
            '# ============================\n',
            '\n',
            '# Chuẩn bị config params\n',
            'config_params = {\n',
            '    "DATA_PATH": DATA_PATH,\n',
            '    "MAX_MOB": MAX_MOB,\n',
            '    "TARGET_MOBS": TARGET_MOBS,\n',
            '    "SEGMENT_COLS": SEGMENT_COLS,\n',
            '    "MIN_OBS": CFG.get("MIN_OBS", 100),\n',
            '    "MIN_EAD": CFG.get("MIN_EAD", 100),\n',
            '    "WEIGHT_METHOD": CFG.get("WEIGHT_METHOD", "exp"),\n',
            '    "ROLL_WINDOW": CFG.get("ROLL_WINDOW", 20),\n',
            '    "DECAY_LAMBDA": CFG.get("DECAY_LAMBDA", 0.97),\n',
            '}\n',
            '\n',
            'lifecycle_file = output_dir / f"Lifecycle_All_Products_{timestamp}.xlsx"\n',
            'export_lifecycle_with_config_info(\n',
            '    df_del_all, \n',
            '    actual_info_all, \n',
            '    df_raw,\n',
            '    config_params,\n',
            '    str(lifecycle_file)\n',
            ')\n',
            'print(f"   ✅ {lifecycle_file}")\n',
            '\n',
            '# ============================\n',
            '# 2. Loan forecast (tự động chia sheet nếu > 1M rows)\n',
            '# ============================\n',
            'from src.config import export_loan_forecast_excel\n',
            '\n',
            'loan_file = output_dir / f"Loan_Forecast_{timestamp}.xlsx"\n',
            'export_loan_forecast_excel(\n',
            '    df_loan_forecast, \n',
            '    loan_file, \n',
            '    target_mobs=TARGET_MOBS,\n',
            '    include_del_sheets=True\n',
            ')\n',
            'print(f"   ✅ {loan_file}")\n',
            '\n',
            'print("\\n🎉 DONE!")\n',
        ]
        
        cell['source'] = new_source
        print(f"✅ Updated export cell (cell {i})")
        break

# Save the updated notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"\n✅ Updated {notebook_path}")
print("\n📝 Changes made:")
print("   1. Added import for export_lifecycle_with_config_info")
print("   2. Updated export cell to use new function with config_params")
print("   3. Renamed output file to Lifecycle_All_Products_*.xlsx")
