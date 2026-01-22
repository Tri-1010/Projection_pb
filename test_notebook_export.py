"""
Test the export functionality in Final_Workflow copy.ipynb
This script will execute the notebook and check if export works
"""
import subprocess
import sys
import os
from pathlib import Path

print("="*70)
print("🧪 Testing Export Functionality in Final_Workflow copy.ipynb")
print("="*70)

# Check if jupyter is available
try:
    result = subprocess.run(['jupyter', '--version'], capture_output=True, text=True)
    print(f"\n✅ Jupyter installed: {result.stdout.strip()}")
except FileNotFoundError:
    print("\n❌ Jupyter not found. Please install: pip install jupyter")
    sys.exit(1)

# Check if nbconvert is available
try:
    result = subprocess.run(['jupyter', 'nbconvert', '--version'], capture_output=True, text=True)
    print(f"✅ nbconvert installed: {result.stdout.strip()}")
except:
    print("⚠️  nbconvert not found. Installing...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'nbconvert'])

# Check if notebook exists
notebook_path = Path('notebooks/Final_Workflow copy.ipynb')
if not notebook_path.exists():
    print(f"\n❌ Notebook not found: {notebook_path}")
    sys.exit(1)

print(f"\n✅ Notebook found: {notebook_path}")

# Execute notebook
print("\n" + "="*70)
print("🚀 Executing notebook...")
print("="*70)
print("\n⏳ This may take several minutes depending on data size...")
print("   Please wait...\n")

try:
    result = subprocess.run([
        'jupyter', 'nbconvert',
        '--to', 'notebook',
        '--execute',
        '--inplace',
        '--ExecutePreprocessor.timeout=3600',  # 1 hour timeout
        str(notebook_path)
    ], capture_output=True, text=True, timeout=3600)
    
    if result.returncode == 0:
        print("\n" + "="*70)
        print("✅ NOTEBOOK EXECUTED SUCCESSFULLY!")
        print("="*70)
        
        # Check if output file was created
        output_dir = Path('cohort_details')
        if output_dir.exists():
            excel_files = list(output_dir.glob('Cohort_Forecast_Details_*.xlsx'))
            if excel_files:
                latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)
                file_size = latest_file.stat().st_size / (1024 * 1024)  # MB
                
                print(f"\n📄 Output file created:")
                print(f"   File: {latest_file.name}")
                print(f"   Size: {file_size:.2f} MB")
                print(f"   Location: {latest_file}")
                
                print("\n" + "="*70)
                print("🎉 SUCCESS! Export is working perfectly!")
                print("="*70)
                print("\n✅ You can now:")
                print("   1. Open the Excel file to review")
                print("   2. Send it to your boss")
                print("   3. Use the same code for future exports")
            else:
                print("\n⚠️  No output file found in cohort_details/")
                print("   Check notebook output for details")
        else:
            print("\n⚠️  cohort_details/ directory not found")
            print("   Export may not have run")
    else:
        print("\n" + "="*70)
        print("❌ NOTEBOOK EXECUTION FAILED")
        print("="*70)
        print("\nError output:")
        print(result.stderr)
        
        print("\n💡 Troubleshooting:")
        print("   1. Check if all required packages are installed")
        print("   2. Verify data files exist")
        print("   3. Run notebook manually in Jupyter to see detailed errors")
        
except subprocess.TimeoutExpired:
    print("\n⏱️  Execution timeout (> 1 hour)")
    print("   The notebook is taking too long to execute")
    print("   Please run it manually in Jupyter")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Alternative: Run notebook manually")
    print("   1. jupyter notebook")
    print("   2. Open 'Final_Workflow copy.ipynb'")
    print("   3. Cell → Run All")

print("\n" + "="*70)
