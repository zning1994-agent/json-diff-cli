#!/bin/bash
cd /mnt/user-data/workspace/json-diff-cli
source .venv/bin/activate 2>/dev/null || true
python -m pytest tests/ -v --tb=short 2>&1 | head -200
