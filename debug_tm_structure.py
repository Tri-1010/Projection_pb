"""
Debug script to check matrices_by_mob structure
Run this in the notebook after compute_transition_by_mob
"""

def debug_matrices_structure(matrices_by_mob):
    """
    Print detailed structure of matrices_by_mob
    """
    print("=" * 60)
    print("🔍 DEBUG: matrices_by_mob structure")
    print("=" * 60)
    
    if not matrices_by_mob:
        print("❌ matrices_by_mob is empty!")
        return
    
    print(f"\n📊 Top-level keys (products): {list(matrices_by_mob.keys())}")
    print(f"   Type of keys: {type(list(matrices_by_mob.keys())[0])}")
    
    for product in list(matrices_by_mob.keys())[:2]:  # First 2 products
        print(f"\n📦 Product: '{product}'")
        product_data = matrices_by_mob[product]
        
        if isinstance(product_data, dict):
            print(f"   MOBs available: {sorted(product_data.keys())[:10]}...")
            print(f"   Type of MOB keys: {type(list(product_data.keys())[0])}")
            
            # Check first MOB
            first_mob = list(product_data.keys())[0]
            mob_data = product_data[first_mob]
            
            print(f"\n   📊 MOB {first_mob}:")
            if isinstance(mob_data, dict):
                print(f"      Scores available: {list(mob_data.keys())}")
                print(f"      Type of score keys: {type(list(mob_data.keys())[0])}")
                
                # Check first score
                first_score = list(mob_data.keys())[0]
                score_data = mob_data[first_score]
                
                print(f"\n      📊 Score '{first_score}':")
                if isinstance(score_data, dict):
                    print(f"         Keys: {list(score_data.keys())}")
                    if 'P' in score_data:
                        P = score_data['P']
                        print(f"         P type: {type(P)}")
                        if hasattr(P, 'shape'):
                            print(f"         P shape: {P.shape}")
                            print(f"         P index: {list(P.index)[:5]}...")
                            print(f"         P columns: {list(P.columns)[:5]}...")
                else:
                    print(f"         Type: {type(score_data)}")
            else:
                print(f"      Type: {type(mob_data)}")
        else:
            print(f"   Type: {type(product_data)}")
    
    print("\n" + "=" * 60)
    print("✅ Debug complete")
    print("=" * 60)


# Usage in notebook:
# from debug_tm_structure import debug_matrices_structure
# debug_matrices_structure(matrices_by_mob)
