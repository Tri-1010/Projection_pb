"""
Fix import issue in Final_Workflow.ipynb
"""
import json
from pathlib import Path

# Read the notebook
notebook_path = Path("notebooks/Final_Workflow.ipynb")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find the import cell and fix it
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code' and 'from src.rollrate.lifecycle import' in ''.join(cell['source']):
        source_lines = cell['source']
        
        # Remove the wrong import line
        new_source = []
        for line in source_lines:
            # Skip the wrong import line
            if 'export_lifecycle_with_config_info,' in line and 'from src.rollrate.lifecycle import' in ''.join(source_lines[:source_lines.index(line)+1]):
                continue
            # Skip duplicate import
            if 'from src.rollrate.lifecycle_export_enhanced import export_lifecycle_with_config_info' in line:
                continue
            new_source.append(line)
        
        # Add correct import at the end, before print statement
        final_source = []
        for j, line in enumerate(new_source):
            if 'print(' in line and 'Import' in line:
                # Add import before print
                final_source.append('from src.rollrate.lifecycle_export_enhanced import export_lifecycle_with_config_info\n')
                final_source.append('\n')
            final_source.append(line)
        
        cell['source'] = final_source
        print(f"✅ Fixed import cell (cell {i})")
        print(f"   Removed duplicate/wrong imports")
        print(f"   Added correct import before print statement")
        break

# Save the updated notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"\n✅ Fixed {notebook_path}")
print("\n📝 Changes:")
print("   1. Removed wrong import from src.rollrate.lifecycle")
print("   2. Removed duplicate import")
print("   3. Added correct import from src.rollrate.lifecycle_export_enhanced")
