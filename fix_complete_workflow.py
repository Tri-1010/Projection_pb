#!/usr/bin/env python3
"""
Fix Complete_Workflow.ipynb - Section 5 (Apply Calibration)
"""

import json

# Load notebook
with open("notebooks/Complete_Workflow.ipynb", "r", encoding="utf-8") as f:
    notebook = json.load(f)

# Find and replace Section 5 cells
# Cell index for "Apply Calibration" section

# Remove old cells from index 16 to 18 (Section 5)
# Then insert new corrected cells

# Find the index of Section 5
section_5_idx = None
for i, cell in enumerate(notebook["cells"]):
    if cell["cell_type"] == "markdown" and "5️⃣ APPLY CALIBRATION" in "".join(cell["source"]):
        section_5_idx = i
        break

if section_5_idx is None:
    print("❌ Cannot find Section 5")
    exit(1)

print(f"Found Section 5 at index {section_5_idx}")

# Remove old cells (Section 5 has 2 code cells after the markdown)
del notebook["cells"][section_5_idx + 1:section_5_idx + 3]

# Insert new corrected cells
new_cells = []

# Cell 1: Apply calibration (CORRECTED)
new_cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "print(\"🔨 Applying calibration...\")\n",
        "\n",
        "# Forecast với k_final (calibrated)\n",
        "forecast_calibrated = forecast_all_vintages_partial_step(\n",
        "    actual_results=actual_results,\n",
        "    matrices_by_mob=matrices_by_mob,\n",
        "    parent_fallback=parent_fallback,\n",
        "    max_mob=max_mob,\n",
        "    k_by_mob=k_final_by_mob,\n",
        "    states=states,\n",
        ")\n",
        "\n",
        "# Convert to DataFrame\n",
        "from src.rollrate.lifecycle import (\n",
        "    lifecycle_to_long_df_amount,\n",
        "    combine_all_lifecycle_amount,\n",
        ")\n",
        "\n",
        "# ✅ FIX: Combine actual + forecast TRƯỚC KHI convert to DataFrame\n",
        "lifecycle_combined = combine_all_lifecycle_amount(\n",
        "    actual=actual_results,\n",
        "    forecast=forecast_calibrated\n",
        ")\n",
        "\n",
        "# Convert to long format\n",
        "df_lifecycle_final = lifecycle_to_long_df_amount(lifecycle_combined)\n",
        "\n",
        "# Tag forecast rows\n",
        "df_lifecycle_final = tag_forecast_rows_amount(df_lifecycle_final, df_raw)\n",
        "\n",
        "# Add DEL metrics\n",
        "df_lifecycle_final = add_del_metrics(df_lifecycle_final, df_raw)\n",
        "\n",
        "print(f\"\\n✅ Lifecycle final (calibrated):\")\n",
        "print(f\"   Total rows: {len(df_lifecycle_final):,}\")\n",
        "print(f\"   Actual rows: {(df_lifecycle_final['IS_FORECAST']==0).sum():,}\")\n",
        "print(f\"   Forecast rows (calibrated): {(df_lifecycle_final['IS_FORECAST']==1).sum():,}\")\n",
        "print(f\"   MOB range: {df_lifecycle_final['MOB'].min()} → {df_lifecycle_final['MOB'].max()}\")\n",
        "\n",
        "# ✅ Kiểm tra forecast có data không\n",
        "df_fc_check = df_lifecycle_final[df_lifecycle_final['IS_FORECAST'] == 1]\n",
        "if df_fc_check.empty:\n",
        "    print(\"\\n⚠️ WARNING: Không có forecast rows!\")\n",
        "else:\n",
        "    print(f\"\\n✅ Forecast check:\")\n",
        "    print(f\"   Forecast MOB range: {df_fc_check['MOB'].min()} → {df_fc_check['MOB'].max()}\")\n",
        "    print(f\"   Sample forecast EAD: {df_fc_check[BUCKETS_CANON].sum(axis=1).sum():,.0f}\")"
    ]
})

# Cell 2: Aggregate (unchanged but with better checks)
new_cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "print(\"🔨 Aggregating to product level...\")\n",
        "\n",
        "# ✅ Kiểm tra trước khi aggregate\n",
        "print(f\"\\nBefore aggregate:\")\n",
        "print(f\"   Total rows: {len(df_lifecycle_final):,}\")\n",
        "print(f\"   Actual: {(df_lifecycle_final['IS_FORECAST']==0).sum():,}\")\n",
        "print(f\"   Forecast: {(df_lifecycle_final['IS_FORECAST']==1).sum():,}\")\n",
        "\n",
        "# Aggregate to product\n",
        "df_product = aggregate_to_product(df_lifecycle_final)\n",
        "\n",
        "# ✅ Kiểm tra sau aggregate\n",
        "print(f\"\\nAfter aggregate to product:\")\n",
        "print(f\"   Total rows: {len(df_product):,}\")\n",
        "if 'IS_FORECAST' in df_product.columns:\n",
        "    print(f\"   Actual: {(df_product['IS_FORECAST']==0).sum():,}\")\n",
        "    print(f\"   Forecast: {(df_product['IS_FORECAST']==1).sum():,}\")\n",
        "\n",
        "# Aggregate to portfolio\n",
        "df_portfolio = aggregate_products_to_portfolio(\n",
        "    df_product,\n",
        "    portfolio_name=\"PORTFOLIO_ALL\"\n",
        ")\n",
        "\n",
        "# Combine\n",
        "df_del_all = pd.concat([df_product, df_portfolio], ignore_index=True)\n",
        "\n",
        "print(f\"\\n✅ Aggregation complete:\")\n",
        "print(f\"   Product-level: {len(df_product):,} rows\")\n",
        "print(f\"   Portfolio-level: {len(df_portfolio):,} rows\")\n",
        "print(f\"   Combined: {len(df_del_all):,} rows\")\n",
        "\n",
        "# ✅ Final check\n",
        "if 'IS_FORECAST' in df_del_all.columns:\n",
        "    fc_count = (df_del_all['IS_FORECAST']==1).sum()\n",
        "    if fc_count == 0:\n",
        "        print(\"\\n⚠️ WARNING: df_del_all không có forecast rows!\")\n",
        "        print(\"   Có thể do aggregate_to_product() không preserve IS_FORECAST\")\n",
        "    else:\n",
        "        print(f\"\\n✅ df_del_all có {fc_count:,} forecast rows\")"
    ]
})

# Insert new cells
for i, cell in enumerate(new_cells):
    notebook["cells"].insert(section_5_idx + 1 + i, cell)

# Save
with open("notebooks/Complete_Workflow.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print("✅ Fixed Section 5 in Complete_Workflow.ipynb")
print("   - Corrected combine_all_lifecycle_amount() usage")
print("   - Added validation checks for forecast rows")
