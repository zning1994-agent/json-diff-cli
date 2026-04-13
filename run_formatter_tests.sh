#!/usr/bin/env bash
# Quick test to verify formatter tests work

cd /mnt/user-data/workspace/json-diff-cli

# Run formatter tests
python -m pytest tests/test_formatter.py -v 2>&1 | head -80
