"""
Debug script để kiểm tra structure của matrices_by_mob
Chạy trong notebook sau khi đã load data
"""

print("="*70)
print("🔍 DEBUG: Checking matrices_by_mob structure")
print("="*70)

if 'matrices_by_mob' not in globals():
    print("❌ matrices_by_mob not found!")
else:
    print(f"\n1. Type: {type(matrices_by_mob)}")
    print(f"2. Length: {len(matrices_by_mob)}")
    
    if len(matrices_by_mob) > 0:
        print(f"\n3. All keys:")
        for i, key in enumerate(matrices_by_mob.keys()):
            print(f"   [{i}] {key} (type: {type(key)})")
            if i >= 10:
                print(f"   ... and {len(matrices_by_mob) - 10} more")
                break
        
        # Check first key
        first_key = list(matrices_by_mob.keys())[0]
        first_value = matrices_by_mob[first_key]
        
        print(f"\n4. First key: {first_key}")
        print(f"5. First value type: {type(first_value)}")
        
        if isinstance(first_value, dict):
            print(f"6. First value is a dict with {len(first_value)} keys:")
            for j, (k, v) in enumerate(first_value.items()):
                print(f"   [{j}] key={k}, value type={type(v)}")
                if isinstance(v, pd.DataFrame):
                    print(f"       DataFrame shape: {v.shape}")
                    print(f"       Index: {list(v.index)[:5]}...")
                    print(f"       Columns: {list(v.columns)[:5]}...")
                if j >= 3:
                    print(f"   ... and {len(first_value) - 3} more")
                    break
        elif isinstance(first_value, pd.DataFrame):
            print(f"6. First value is a DataFrame:")
            print(f"   Shape: {first_value.shape}")
            print(f"   Index: {list(first_value.index)}")
            print(f"   Columns: {list(first_value.columns)}")
            print(f"\n   Sample data:")
            print(first_value.head())
        else:
            print(f"6. First value: {first_value}")
    else:
        print("⚠️ matrices_by_mob is empty!")

print("\n" + "="*70)
print("🔍 Checking parent_fallback (if exists)")
print("="*70)

if 'parent_fallback' in globals():
    print(f"\n1. Type: {type(parent_fallback)}")
    print(f"2. Length: {len(parent_fallback)}")
    
    if len(parent_fallback) > 0:
        print(f"\n3. First 5 keys:")
        for i, key in enumerate(list(parent_fallback.keys())[:5]):
            print(f"   [{i}] {key}")
        
        first_key = list(parent_fallback.keys())[0]
        first_value = parent_fallback[first_key]
        
        print(f"\n4. First key: {first_key}")
        print(f"5. First value type: {type(first_value)}")
        
        if isinstance(first_value, pd.DataFrame):
            print(f"6. DataFrame shape: {first_value.shape}")
            print(f"   Index: {list(first_value.index)[:5]}...")
            print(f"   Columns: {list(first_value.columns)[:5]}...")
else:
    print("parent_fallback not found")

print("\n" + "="*70)
