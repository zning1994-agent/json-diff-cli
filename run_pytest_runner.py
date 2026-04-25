#!/usr/bin/env python3
"""Run pytest and show results."""
import subprocess
import sys

result = subprocess.run(
    ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
    cwd="/mnt/user-data/workspace/json-diff-cli",
    capture_output=True,
    text=True
)
print(result.stdout[-8000:] if len(result.stdout) > 8000 else result.stdout)
if result.stderr:
    print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
print("\n=== EXIT CODE:", result.returncode, "===")
