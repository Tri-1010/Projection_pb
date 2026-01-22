"""
Update Final_Workflow copy.ipynb with v4 export code (single sheet)
"""
import json

# Read the v4 export code
with open('export_2025_10_and_2025_01_v4.py', 'r', encoding='utf-8') as f:
    export_code = f.read()

# Remove the docstring at the top
lines = export_code.split('\n')
code_lines = []
in_docstring = False
for line in lines:
    if line.strip().startswith('"""'):
        if not in_docstring:
            in_docstring = True
            continue
        else:
            in_docstring = False
            continue
    if not in_docstring:
        code_lines.append(line)

export_code_clean = '\n'.join(code_lines)

# Read notebook
with open('notebooks/Final_Workflow copy.ipynb', 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find and update export cell
updated = False
for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'EXPORT COHORTS' in source or 'export_cohort_forecast_details' in source:
            print("Found export cell, updating to v4...")
            cell['source'] = [line + '\n' for line in export_code_clean.split('\n')]
            cell['outputs'] = []
            cell['execution_count'] = None
            updated = True
            break

if not updated:
    print("Export cell not found, adding new cell...")
    new_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + '\n' for line in export_code_clean.split('\n')]
    }
    notebook['cells'].append(new_cell)

# Save notebook
with open('notebooks/Final_Workflow copy.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"✅ Notebook updated with v4 export code!")
print(f"   Total cells: {len(notebook['cells'])}")
print(f"\n💡 V4 Layout:")
print(f"   - 1 sheet duy nhất (All_Cohorts)")
print(f"   - Mỗi cohort cách nhau 2 dòng")
print(f"   - Có đầy đủ: Current + K + Transition Matrix")
