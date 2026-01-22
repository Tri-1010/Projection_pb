"""
Check structure of k_raw_by_mob and k_smooth_by_mob to understand the correct format
"""

# This is a test script to understand the structure
# Run this in the notebook after loading data to see the structure

print("="*70)
print("Checking K structure")
print("="*70)

# Check k_raw_by_mob structure
if 'k_raw_by_mob' in globals():
    print("\n1. k_raw_by_mob structure:")
    print(f"   Type: {type(k_raw_by_mob)}")
    
    if isinstance(k_raw_by_mob, dict):
        print(f"   Keys (first 5): {list(k_raw_by_mob.keys())[:5]}")
        
        # Check first key
        first_key = list(k_raw_by_mob.keys())[0]
        print(f"   First key: {first_key}")
        print(f"   First key type: {type(first_key)}")
        print(f"   First value type: {type(k_raw_by_mob[first_key])}")
        
        # If first key is tuple (segment), show structure
        if isinstance(first_key, tuple):
            print(f"   → Structure: dict[segment_key][mob] = k_value")
            print(f"   → segment_key = (product, score)")
            segment_key = first_key
            if isinstance(k_raw_by_mob[segment_key], dict):
                mobs = list(k_raw_by_mob[segment_key].keys())[:5]
                print(f"   → MOBs for {segment_key}: {mobs}")
        # If first key is int (MOB), show structure
        elif isinstance(first_key, int):
            print(f"   → Structure: dict[mob] = k_value")
            print(f"   → No segment key, just MOB")
else:
    print("\n❌ k_raw_by_mob not found")

# Check k_smooth_by_mob structure
if 'k_smooth_by_mob' in globals():
    print("\n2. k_smooth_by_mob structure:")
    print(f"   Type: {type(k_smooth_by_mob)}")
    
    if isinstance(k_smooth_by_mob, dict):
        print(f"   Keys (first 5): {list(k_smooth_by_mob.keys())[:5]}")
        
        first_key = list(k_smooth_by_mob.keys())[0]
        print(f"   First key: {first_key}")
        print(f"   First key type: {type(first_key)}")
else:
    print("\n❌ k_smooth_by_mob not found")

# Check alpha_by_mob structure
if 'alpha_by_mob' in globals():
    print("\n3. alpha_by_mob structure:")
    print(f"   Type: {type(alpha_by_mob)}")
    
    if isinstance(alpha_by_mob, dict):
        print(f"   Keys (first 5): {list(alpha_by_mob.keys())[:5]}")
        
        first_key = list(alpha_by_mob.keys())[0]
        print(f"   First key: {first_key}")
        print(f"   First key type: {type(first_key)}")
        print(f"   First value: {alpha_by_mob[first_key]}")
else:
    print("\n❌ alpha_by_mob not found")

print("\n" + "="*70)
