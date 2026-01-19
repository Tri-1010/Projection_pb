"""
Fix missing aggregation steps in Final_Workflow.ipynb
"""
import json
from pathlib import Path

# Read the notebook
notebook_path = Path("notebooks/Final_Workflow.ipynb")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find the cell after lifecycle creation (before allocation)
# We need to add aggregation steps here
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code' and 'df_lifecycle_final = add_del_metrics' in ''.join(cell['source']):
        # Found the lifecycle creation cell
        # Check if next cell is aggregation
        if i + 1 < len(notebook['cells']):
            next_cell = notebook['cells'][i + 1]
            if 'aggregate_to_product' not in ''.join(next_cell.get('source', [])):
                # Need to add aggregation cell
                print(f"✅ Found lifecycle cell at index {i}")
                print(f"   Need to add aggregation cell after it")
                
                # Create new aggregation cell
                new_cell = {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# ============================\n",
                        "# 4️⃣ AGGREGATE TO PRODUCT & PORTFOLIO\n",
                        "# ============================\n",
                        "\n",
                        "# Aggregate to product level\n",
                        "df_product = aggregate_to_product(df_lifecycle_final)\n",
                        "\n",
                        "# Aggregate to portfolio level\n",
                        "df_portfolio = aggregate_products_to_portfolio(\n",
                        "    df_product,\n",
                        "    portfolio_name=\"PORTFOLIO_ALL\"\n",
                        ")\n",
                        "\n",
                        "# Combine product + portfolio\n",
                        "df_del_all = pd.concat([df_product, df_portfolio], ignore_index=True)\n",
                        "\n",
                        "print(f\"\\n✅ Aggregation complete:\")\n",
                        "print(f\"   Product-level: {len(df_product):,} rows\")\n",
                        "print(f\"   Portfolio-level: {len(df_portfolio):,} rows\")\n",
                        "print(f\"   Combined: {len(df_del_all):,} rows\")\n",
                        "\n",
                        "# Create actual_info for all products\n",
                        "actual_info_prod = {}\n",
                        "for (product, score, vintage), data in actual_results.items():\n",
                        "    max_mob = max(data.keys())\n",
                        "    actual_info_prod[(product, vintage)] = max_mob\n",
                        "\n",
                        "# Extend with portfolio\n",
                        "actual_info_all = extend_actual_info_with_portfolio(\n",
                        "    actual_info_prod,\n",
                        "    portfolio_name=\"PORTFOLIO_ALL\"\n",
                        ")\n",
                        "\n",
                        "print(f\"\\n✅ Actual info: {len(actual_info_all):,} cohorts\")\n"
                    ]
                }
                
                # Insert after lifecycle cell
                notebook['cells'].insert(i + 1, new_cell)
                print(f"   ✅ Added aggregation cell at index {i + 1}")
                break
        break

# Update cell numbering in markdown
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source'])
        # Update numbering: 4️⃣ becomes 5️⃣, 5️⃣ becomes 6️⃣
        if '## 4️⃣ ALLOCATE' in source or '## 4️⃣ ALLOCATION' in source:
            cell['source'] = [s.replace('4️⃣', '5️⃣') for s in cell['source']]
            print(f"✅ Updated markdown cell {i}: 4️⃣ → 5️⃣")
        elif '## 5️⃣ EXPORT' in source:
            cell['source'] = [s.replace('5️⃣', '6️⃣') for s in cell['source']]
            print(f"✅ Updated markdown cell {i}: 5️⃣ → 6️⃣")

# Save the updated notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"\n✅ Fixed {notebook_path}")
print("\n📝 Changes made:")
print("   1. Added aggregation cell after lifecycle creation")
print("   2. Creates df_del_all (product + portfolio)")
print("   3. Creates actual_info_all")
print("   4. Updated section numbering")
