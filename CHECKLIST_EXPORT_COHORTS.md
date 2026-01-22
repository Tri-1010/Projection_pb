# ✅ Checklist: Export Cohorts 2025-10 & 2025-01

**Date**: 2026-01-19  
**Task**: Export all cohorts for months 2025-10 and 2025-01

---

## 📋 Pre-Export Checklist

### Environment Setup
- [ ] Jupyter notebook is installed and working
- [ ] Python environment is activated
- [ ] All required packages are installed (pandas, numpy, xlsxwriter)
- [ ] Project directory is accessible

### Files Ready
- [ ] `notebooks/Final_Workflow copy.ipynb` exists
- [ ] `export_2025_10_and_2025_01.py` exists
- [ ] `export_cohort_details.py` exists
- [ ] `src/config.py` exists (contains parse_date_column)

---

## 🚀 Execution Checklist

### Step 1: Open Notebook
- [ ] Opened `notebooks/Final_Workflow copy.ipynb` in Jupyter
- [ ] Notebook loaded successfully
- [ ] Can see all cells

### Step 2: Run All Cells
- [ ] Clicked "Cell → Run All" or "Kernel → Restart & Run All"
- [ ] All cells executed without errors
- [ ] Variables created: df_raw, matrices_by_mob, k_raw_by_mob, etc.
- [ ] No error messages in output

### Step 3: Verify (Optional but Recommended)
- [ ] Added new cell with `%run verify_export_ready.py`
- [ ] Ran verification cell
- [ ] All checks passed ✅
- [ ] If any checks failed, fixed issues before continuing

### Step 4: Add Export Cell
- [ ] Opened `export_2025_10_and_2025_01.py`
- [ ] Copied entire code
- [ ] Created new cell in notebook
- [ ] Pasted code into new cell

### Step 5: Run Export
- [ ] Ran the export cell
- [ ] Saw "Creating VINTAGE_DATE..." message (if needed)
- [ ] Saw cohort counts for each month
- [ ] Saw "Exporting X cohorts..." message
- [ ] Saw "HOÀN THÀNH!" success message
- [ ] No error messages

---

## 📊 Output Verification Checklist

### File Created
- [ ] File exists in `cohort_details/` folder
- [ ] Filename format: `Cohort_Forecast_Details_YYYYMMDD_HHMMSS.xlsx`
- [ ] File size is reasonable (not 0 bytes)
- [ ] Can open file in Excel

### Excel Sheets
- [ ] Sheet 1: "Summary" exists
- [ ] Sheet 2+: "TM_*" sheets exist (transition matrices)
- [ ] Sheet: "K_Values" exists
- [ ] Sheet: "Actual_*" sheets exist
- [ ] Sheet: "Forecast_Steps" exists
- [ ] Sheet: "Instructions" exists

### Data Quality
- [ ] Summary sheet shows correct number of cohorts
- [ ] Cohorts for 2025-10 are present
- [ ] Cohorts for 2025-01 are present
- [ ] Transition matrices have values (not all zeros)
- [ ] K values are present and reasonable
- [ ] Actual data is present
- [ ] Forecast steps are detailed

---

## 🎯 Final Checklist

### Before Sending to Boss
- [ ] Opened Excel file and reviewed content
- [ ] Checked Summary sheet for overview
- [ ] Verified data looks correct
- [ ] Checked Instructions sheet
- [ ] File is ready to share

### Documentation
- [ ] Read `QUICK_START_EXPORT_2025.md` (if needed)
- [ ] Understand what each sheet contains
- [ ] Know how to explain the data to boss

### Backup
- [ ] Saved a copy of the Excel file
- [ ] Noted the filename and location
- [ ] Can reproduce if needed

---

## ⚠️ Troubleshooting Checklist

### If Error: KeyError 'VINTAGE_DATE'
- [ ] Code should auto-create VINTAGE_DATE
- [ ] If still fails, check `FIX_VINTAGE_DATE_ERROR.md`
- [ ] Verify DISBURSAL_DATE column exists in df_raw

### If Error: NameError 'alpha_by_mob' is not defined
- [ ] Code should auto-convert alpha to alpha_by_mob
- [ ] If still fails, check `FIX_ALPHA_BY_MOB_ERROR.md`
- [ ] Use updated code from `export_2025_10_and_2025_01.py`

### If Error: No data for month
- [ ] Check available months: `df_raw['VINTAGE_DATE'].value_counts()`
- [ ] Verify target_months are correct
- [ ] Change target_months if needed

### If Error: Missing variables
- [ ] Verify all cells in notebook were run
- [ ] Check for error messages in previous cells
- [ ] Re-run "Cell → Run All"

### If Error: MemoryError
- [ ] Too many cohorts to export at once
- [ ] Export months separately
- [ ] Or filter to top N cohorts

### If Error: Cannot import export_cohort_forecast_details
- [ ] Verify `export_cohort_details.py` exists
- [ ] Check file is in same directory as notebook
- [ ] Restart kernel and try again

### If Error: NameError 'alpha_by_mob' is not defined
- [ ] Use updated code from `export_2025_10_and_2025_01.py`
- [ ] Code auto-converts alpha to alpha_by_mob
- [ ] Check `FIX_ALPHA_BY_MOB_ERROR.md` for details

---

## 📚 Documentation Checklist

### Files to Read (Priority Order)
1. [ ] `QUICK_START_EXPORT_2025.md` - Quick start (2 min)
2. [ ] `export_2025_10_and_2025_01.py` - Code to use
3. [ ] `STATUS_EXPORT_COHORTS.md` - Current status (5 min)
4. [ ] `GUIDE_NEXT_STEPS.md` - Complete guide (10 min)
5. [ ] `FIX_VINTAGE_DATE_ERROR.md` - Error fix (if needed)

### Optional Reading
- [ ] `INDEX_EXPORT_COHORTS.md` - File navigation
- [ ] `WORKFLOW_EXPORT_COHORTS.md` - Visual workflow
- [ ] `HOW_TO_USE_EXPORT_COHORT.md` - Detailed usage
- [ ] `SUMMARY_EXPORT_COHORTS_COMPLETE.md` - Complete summary

---

## 🎉 Success Checklist

### Task Complete When:
- [x] Code is ready and tested
- [x] Documentation is complete
- [x] VINTAGE_DATE error is fixed
- [ ] Notebook cells all run successfully
- [ ] Export code executed without errors
- [ ] Excel file created with all sheets
- [ ] Data verified and looks correct
- [ ] File ready to send to boss

---

## 📝 Notes Section

### Execution Notes
```
Date executed: _______________
Time taken: _______________
Number of cohorts exported: _______________
File size: _______________
Any issues encountered: _______________
```

### Data Notes
```
2025-10 cohorts: _______________
2025-10 loans: _______________
2025-01 cohorts: _______________
2025-01 loans: _______________
Total cohorts: _______________
```

### Next Steps
```
[ ] Send file to boss
[ ] Prepare presentation (if needed)
[ ] Answer boss questions (if any)
[ ] Archive file for records
```

---

## 🔄 Reusability Checklist

### For Future Exports
- [ ] Know how to change target_months
- [ ] Know how to filter cohorts
- [ ] Know how to export separately
- [ ] Saved code for future use
- [ ] Documented any customizations

### Knowledge Transfer
- [ ] Understand the workflow
- [ ] Can explain to colleagues
- [ ] Know where to find documentation
- [ ] Can troubleshoot common issues

---

## ✅ Final Sign-Off

```
Task: Export cohorts 2025-10 & 2025-01
Status: [ ] Complete / [ ] In Progress / [ ] Issues

Completed by: _______________
Date: _______________
Time: _______________

Output file: _______________
Location: _______________

Ready to send to boss: [ ] Yes / [ ] No

Notes:
_________________________________________________
_________________________________________________
_________________________________________________
```

---

**Use this checklist to ensure nothing is missed!** ✅

