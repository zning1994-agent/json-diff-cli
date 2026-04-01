# json-diff-cli

A Python CLI tool for comparing JSON files with colorful terminal output.

## Features

- Deep comparison of nested JSON objects and arrays
- Three change types: additions, deletions, modifications
- Colorful terminal output using rich
- JSON Patch (RFC 6902) format output
- Human-readable statistics summary

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Compare two JSON files
json-diff left.json right.json

# Output as JSON Patch
json-diff left.json right.json --output json-patch

# Summary only
json-diff left.json right.json --output summary
```

## Python API

```python
from json_diff_cli import compare

result = compare("old.json", "new.json")
print(f"Found {result.total_changes} differences")
```

## License

MIT
