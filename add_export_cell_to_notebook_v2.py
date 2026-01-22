"""
Add export cohort cell to Final_Workflow copy.ipynb
"""
import json

# Read the export code
with open('export_2025_10_and_2025_01.py', 'r', encoding='utf-8') as f:
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
    if not in_docstring and line.strip():
        code_lines.append(line)

export_code_clean = '\n'.join(code_lines)

# Read notebook
with open('notebooks/Final_Workflow copy.ipynb', 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Check if export cell already exists
has_export_cell = False
for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'EXPORT COHORTS: 2025-10 và 2025-01' in source or 'export_cohort_forecast_details' in source:
            has_export_cell = True
            print("Export cell already exists, updating it...")
            cell['source'] = [line + '\n' for line in export_code_clean.split('\n')]
            cell['outputs'] = []
            cell['execution_count'] = None
            break

# If no export cell exists, add new one
if not has_export_cell:
    print("Adding new export cell...")
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

print(f"✅ Notebook updated!")
print(f"   Total cells: {len(notebook['cells'])}")
print(f"   Export cell: {'Updated' if has_export_cell else 'Added'}")
