"""
Verify all imports in Final_Workflow notebook work correctly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(".").resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("🔍 Verifying imports from Final_Workflow notebook...\n")

try:
    print("1. Testing basic imports...")
    import pandas as pd
    import numpy as np
    from datetime import datetime
    print("   ✅ Basic imports OK")
    
    print("\n2. Testing config imports...")
    from src.config import CFG, BUCKETS_CANON, BUCKETS_30P, BUCKETS_90P
    from src.config import parse_date_column, create_segment_columns, SEGMENT_COLS
    print("   ✅ Config imports OK")
    
    print("\n3. Testing data loader...")
    from src.data_loader import load_data
    print("   ✅ Data loader OK")
    
    print("\n4. Testing rollrate modules...")
    from src.rollrate.transition import compute_transition_by_mob
    print("   ✅ Transition module OK")
    
    print("\n5. Testing lifecycle imports...")
    from src.rollrate.lifecycle import (
        get_actual_all_vintages_amount,
        build_full_lifecycle_amount,
        tag_forecast_rows_amount,
        add_del_metrics,
        aggregate_to_product,
        aggregate_products_to_portfolio,
        lifecycle_to_long_df_amount,
        combine_all_lifecycle_amount,
        export_lifecycle_all_products_one_file,
        extend_actual_info_with_portfolio,
    )
    print("   ✅ Lifecycle imports OK")
    
    print("\n6. Testing calibration imports...")
    from src.rollrate.calibration_kmob import (
        fit_k_raw, smooth_k, fit_alpha,
        forecast_all_vintages_partial_step,
    )
    print("   ✅ Calibration imports OK")
    
    print("\n7. Testing allocation imports...")
    from src.rollrate.allocation_v2_optimized import allocate_multi_mob_optimized
    print("   ✅ Allocation imports OK")
    
    print("\n8. Testing NEW enhanced export import...")
    from src.rollrate.lifecycle_export_enhanced import export_lifecycle_with_config_info
    print("   ✅ Enhanced export import OK")
    
    print("\n" + "="*60)
    print("🎉 ALL IMPORTS SUCCESSFUL!")
    print("="*60)
    print("\n✅ Final_Workflow notebook is ready to run!")
    print("\nNext steps:")
    print("1. Open Jupyter: jupyter notebook notebooks/Final_Workflow.ipynb")
    print("2. Run all cells")
    print("3. Check output file for Config_Info sheet")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're in the project root directory")
    print("2. Check if all required files exist")
    print("3. Verify Python path is correct")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
