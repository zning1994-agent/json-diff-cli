#!/usr/bin/env bash
# Run differ tests to verify the fix

cd /mnt/user-data/workspace/json-diff-cli

# Run differ tests
python -m pytest tests/test_differ.py -v 2>&1 | head -100
