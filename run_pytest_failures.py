#!/usr/bin/env python3
"""Run pytest and capture all failing test details."""
import subprocess
import sys

print("Running pytest to identify failing tests...")
print("=" * 80)

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=line", "--no-header"],
    cwd="/mnt/user-data/workspace/json-diff-cli",
    capture_output=True,
    text=True
)

# Print full output
print(result.stdout)

# Parse and count failures
lines = result.stdout.split('\n')
failures = []
errors = []
for line in lines:
    if 'FAILED' in line:
        failures.append(line.strip())
    elif 'ERROR' in line and 'test_' in line:
        errors.append(line.strip())

print("\n" + "=" * 80)
print(f"SUMMARY: {len(failures)} failures, {len(errors)} errors")
print("=" * 80)

if failures:
    print("\nFAILING TESTS:")
    for f in failures:
        print(f"  - {f}")

if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  - {e}")

print(f"\nExit code: {result.returncode}")
