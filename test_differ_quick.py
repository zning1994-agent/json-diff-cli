#!/usr/bin/env python
"""Quick test to verify differ.py matches test expectations."""

import sys
sys.path.insert(0, '/mnt/user-data/workspace/json-diff-cli/src')

from json_diff_cli.differ import compare, DiffResult

# Test 1: compare() accepts dict data
print("Test 1: compare() accepts dict data...")
left_data = {"name": "Alice"}
right_data = {"name": "Bob"}
result = compare(left_data, right_data)
print(f"  Result type: {type(result)}")
print(f"  isinstance DiffResult: {isinstance(result, DiffResult)}")

# Test 2: summary has total_changes
print("\nTest 2: summary has total_changes...")
print(f"  summary keys: {list(result.summary.keys())}")
print(f"  total_changes: {result.summary.get('total_changes', 'MISSING')}")

# Test 3: has_changes() method
print("\nTest 3: has_changes() method...")
print(f"  has_changes() exists: {hasattr(result, 'has_changes')}")
print(f"  has_changes() callable: {callable(result.has_changes) if hasattr(result, 'has_changes') else False}")
try:
    hc = result.has_changes()
    print(f"  has_changes() result: {hc}")
except Exception as e:
    print(f"  has_changes() error: {e}")

# Test 4: modifications with old_value/new_value
print("\nTest 4: modifications with old_value/new_value...")
left = {"name": "Alice"}
right = {"name": "Bob"}
result = compare(left, right)
print(f"  modifications: {result.modifications}")
if "name" in result.modifications:
    print(f"  old_value: {result.modifications['name'].get('old_value')}")
    print(f"  new_value: {result.modifications['name'].get('new_value')}")

# Test 5: get_changed_paths() method
print("\nTest 5: get_changed_paths() method...")
left = {"a": 1, "b": 2}
right = {"a": 99, "c": 3}
result = compare(left, right)
print(f"  get_changed_paths() exists: {hasattr(result, 'get_changed_paths')}")
try:
    paths = result.get_changed_paths()
    print(f"  changed paths: {paths}")
except Exception as e:
    print(f"  get_changed_paths() error: {e}")

print("\nDone!")
