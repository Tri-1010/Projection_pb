# 🔄 Workflow: Export Cohorts 2025-10 & 2025-01

## 📊 Visual Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    START: User Request                       │
│  "Export all cohorts for 2025-10 and 2025-01 to send boss" │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              STEP 1: Open Notebook                           │
│  jupyter notebook "notebooks/Final_Workflow copy.ipynb"     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              STEP 2: Run All Cells                           │
│  Cell → Run All (loads data, creates matrices, etc.)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         STEP 3a: Verify (Optional)                           │
│  %run verify_export_ready.py                                │
│  ✅ All checks pass → Continue                              │
│  ❌ Issues found → Fix and retry                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         STEP 3b: Add Export Cell                             │
│  Copy code from export_2025_10_and_2025_01.py              │
│  Paste into new cell                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         STEP 4: Run Export Cell                              │
│  Execute the cell                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         PROCESSING: Export Code Runs                         │
│                                                             │
│  1. Create VINTAGE_DATE (if not exists)                     │
│     ├─ Check if column exists                              │
│     └─ Create from DISBURSAL_DATE using parse_date_column()│
│                                                             │
│  2. Find All Cohorts                                        │
│     ├─ Filter data for 2025-10-01                          │
│     ├─ Group by (PRODUCT_TYPE, RISK_SCORE)                 │
│     ├─ Filter data for 2025-01-01                          │
│     └─ Group by (PRODUCT_TYPE, RISK_SCORE)                 │
│                                                             │
│  3. Export to Excel                                         │
│     ├─ Create Summary sheet                                │
│     ├─ Create TM_* sheets (transition matrices)            │
│     ├─ Create K_Values sheet                               │
│     ├─ Create Actual_* sheets                              │
│     ├─ Create Forecast_Steps sheet                         │
│     └─ Create Instructions sheet                           │
│                                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         OUTPUT: Excel File Created                           │
│  cohort_details/Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx│
│                                                             │
│  Contains:                                                  │
│  ✅ Summary of all cohorts                                  │
│  ✅ Transition matrices by segment                          │
│  ✅ K values (raw, smooth, alpha)                           │
│  ✅ Actual data by segment                                  │
│  ✅ Forecast calculation steps                              │
│  ✅ Instructions for use                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              END: Ready to Send to Boss                      │
│  📄 Excel file with all cohort details                      │
│  🎯 Mission accomplished! 🎉                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Process Flow

### Phase 1: Preparation
```
User Opens Notebook
    ↓
Runs All Cells
    ↓
Variables Created:
    - df_raw (data)
    - matrices_by_mob (transition matrices)
    - k_raw_by_mob (K raw values)
    - k_smooth_by_mob (K smooth values)
    - alpha_by_mob (Alpha values)
    - TARGET_MOBS (target MOB)
```

### Phase 2: Verification (Optional)
```
Run verify_export_ready.py
    ↓
Check 1: Required variables exist? ✅/❌
Check 2: VINTAGE_DATE column exists? ✅/❌
Check 3: Segment columns exist? ✅/❌
Check 4: Target months have data? ✅/❌
Check 5: Export function available? ✅/❌
    ↓
All Pass? → Continue
Any Fail? → Fix issues
```

### Phase 3: Export Execution
```
Run Export Code
    ↓
Step 0: Create VINTAGE_DATE
    ├─ if 'VINTAGE_DATE' not in df_raw.columns:
    │   └─ df_raw['VINTAGE_DATE'] = parse_date_column(df_raw['DISBURSAL_DATE'])
    └─ else:
        └─ df_raw['VINTAGE_DATE'] = pd.to_datetime(df_raw['VINTAGE_DATE'])
    ↓
Step 1: Find Cohorts
    ├─ For month in ['2025-10-01', '2025-01-01']:
    │   ├─ Filter df_raw by VINTAGE_DATE == month
    │   ├─ Group by (PRODUCT_TYPE, RISK_SCORE)
    │   └─ Add to all_cohorts list
    └─ Result: List of (product, score, vintage_date) tuples
    ↓
Step 2: Export
    └─ Call export_cohort_forecast_details()
        ├─ For each cohort:
        │   ├─ Get transition matrices
        │   ├─ Get K values
        │   ├─ Get actual data
        │   └─ Calculate forecast steps
        ├─ Create Excel sheets
        └─ Save file
```

### Phase 4: Output
```
Excel File Created
    ↓
Location: cohort_details/Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx
    ↓
Sheets:
    1. Summary - Overview
    2. TM_* - Transition matrices
    3. K_Values - K parameters
    4. Actual_* - Historical data
    5. Forecast_Steps - Calculations
    6. Instructions - How to use
    ↓
Ready to Send to Boss ✅
```

---

## 🎯 Decision Tree

```
Need to export cohorts?
    │
    ├─ Yes, quickly
    │   └─ Use: QUICK_START_EXPORT_2025.md
    │       └─ 3 steps → Done
    │
    ├─ Yes, but want to understand first
    │   └─ Use: GUIDE_NEXT_STEPS.md
    │       └─ Read → Understand → Export
    │
    ├─ Yes, but got an error
    │   └─ Use: verify_export_ready.py
    │       ├─ All pass → Continue export
    │       └─ Issues found → Check FIX_VINTAGE_DATE_ERROR.md
    │
    ├─ Yes, but need to customize
    │   └─ Use: GUIDE_NEXT_STEPS.md → Customization
    │       └─ Modify code → Export
    │
    └─ Just want to see status
        └─ Use: STATUS_EXPORT_COHORTS.md
            └─ Check what's ready
```

---

## 🔄 Error Handling Flow

```
Run Export Code
    ↓
Error: KeyError 'VINTAGE_DATE'?
    ├─ Yes → Code auto-creates VINTAGE_DATE
    │   └─ Continue execution ✅
    └─ No → Continue
    ↓
Error: No data for month?
    ├─ Yes → Print warning, skip month
    │   └─ Continue with other months
    └─ No → Continue
    ↓
Error: No cohorts found?
    ├─ Yes → Print message, exit gracefully
    │   └─ Check data and target_months
    └─ No → Continue
    ↓
Success → Excel file created ✅
```

---

## 📊 Data Flow

```
Input Data (df_raw)
    ↓
    ├─ DISBURSAL_DATE → parse_date_column() → VINTAGE_DATE
    ├─ PRODUCT_TYPE (segment)
    ├─ RISK_SCORE (segment)
    └─ AGREEMENT_ID (count loans)
    ↓
Filter by VINTAGE_DATE
    ↓
Group by (PRODUCT_TYPE, RISK_SCORE)
    ↓
For each cohort:
    ├─ Get transition matrices (from matrices_by_mob)
    ├─ Get K values (from k_raw_by_mob, k_smooth_by_mob)
    ├─ Get Alpha values (from alpha_by_mob)
    ├─ Get actual data (from df_raw)
    └─ Calculate forecast steps
    ↓
Export to Excel
    ↓
Output: Cohort_Forecast_Details_*.xlsx
```

---

## 🎯 Success Path

```
✅ Open notebook
    ↓
✅ Run all cells
    ↓
✅ (Optional) Verify with verify_export_ready.py
    ↓
✅ Copy export code
    ↓
✅ Run export cell
    ↓
✅ Check output file
    ↓
✅ Send to boss
    ↓
🎉 Success!
```

---

## ⚠️ Common Issues & Solutions

```
Issue: KeyError 'VINTAGE_DATE'
    ↓
Solution: Code auto-creates it
    └─ No action needed ✅

Issue: No data for target month
    ↓
Solution: Check available months
    └─ df_raw['VINTAGE_DATE'].value_counts()
    └─ Change target_months

Issue: Too many cohorts (memory error)
    ↓
Solution: Export separately
    └─ Export 2025-10 first
    └─ Then export 2025-01

Issue: Missing variables
    ↓
Solution: Run all cells first
    └─ Cell → Run All
    └─ Then run export
```

---

## 📚 File Navigation Flow

```
Start
    ↓
Want quick start?
    ├─ Yes → QUICK_START_EXPORT_2025.md
    └─ No → Continue
    ↓
Want complete guide?
    ├─ Yes → GUIDE_NEXT_STEPS.md
    └─ No → Continue
    ↓
Want to check status?
    ├─ Yes → STATUS_EXPORT_COHORTS.md
    └─ No → Continue
    ↓
Got an error?
    ├─ Yes → FIX_VINTAGE_DATE_ERROR.md
    └─ No → Continue
    ↓
Need all files list?
    └─ Yes → INDEX_EXPORT_COHORTS.md
```

---

**This workflow ensures a smooth, error-free export process!** 🚀

