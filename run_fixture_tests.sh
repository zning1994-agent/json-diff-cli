#!/usr/bin/env bash
# Run fixture tests to verify conftest.py works correctly

cd /mnt/user-data/workspace/json-diff-cli

# Run the fixture tests
python -m pytest tests/test_conftest.py -v

# Also run a quick sanity check on other tests
python -m pytest tests/test_differ.py::TestEdgeCases -v
