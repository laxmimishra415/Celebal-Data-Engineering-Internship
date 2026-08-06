"""
Runs the entire mini-project pipeline end to end:
  1. Generate raw data (Part 1)
  2. Clean data (Part 2)
  3. Load into SQLite (for Part 3)
  4. Run all 16 SQL analysis queries (Part 3)
  5. Run edge case tests (Part 5)

(Part 4, the CLI tool, is interactive/argument-driven and run separately --
 see README.md)
"""

import subprocess
import sys

STEPS = [
    ("Generating raw CSV data", ["python3", "scripts/generate_data.py"]),
    ("Cleaning data", ["python3", "scripts/clean_data.py"]),
    ("Loading cleaned data into SQLite", ["python3", "scripts/load_to_sqlite.py"]),
    ("Running all SQL analysis queries", ["python3", "scripts/run_queries.py"]),
    ("Running edge case tests", ["python3", "tests/test_edge_cases.py"]),
]

for label, cmd in STEPS:
    print(f"\n{'#'*60}\n# {label}\n{'#'*60}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\nStep failed: {label}")
        sys.exit(1)

print("\nAll steps completed successfully.")
print("Try the CLI tool next:  python3 scripts/cli_report_tool.py --type monthly --start 2025-06-01 --end 2025-06-30")
