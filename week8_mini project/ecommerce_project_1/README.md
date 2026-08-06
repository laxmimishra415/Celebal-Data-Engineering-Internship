# E-Commerce Order Analytics System
**Celebal Technologies — Data Engineering Internship — Week 8 Mini Project**

End-to-end analytics system covering data generation, cleaning, SQL analysis,
a CLI reporting tool, and edge-case testing — built entirely with Python and
SQLite (local environment, no cloud dependency).

## Project Structure

```
ecommerce_project/
├── data/                     # Raw generated CSVs (Part 1)
│   ├── orders.csv
│   ├── order_items.csv
│   ├── products.csv
│   └── customers.csv
├── cleaned_data/              # Cleaned CSVs + data quality report (Part 2)
│   ├── orders_clean.csv
│   ├── order_items_clean.csv
│   ├── products_clean.csv
│   ├── customers_clean.csv
│   └── data_quality_report.txt
├── scripts/
│   ├── generate_data.py       # Part 1: data generation
│   ├── clean_data.py          # Part 2: cleaning functions
│   ├── load_to_sqlite.py      # loads cleaned CSVs into ecommerce.db
│   ├── run_queries.py         # runs & verifies all Part 3 SQL queries
│   └── cli_report_tool.py     # Part 4: command-line reporting tool
├── sql/
│   ├── analysis_queries.sql   # Part 3: all 16 queries (basic -> advanced)
│   └── query_results.txt      # sample output of every query
├── tests/
│   └── test_edge_cases.py     # Part 5: 4 edge case tests
├── ecommerce.db                # SQLite database (generated)
├── run_all.py                  # runs the full pipeline in one go
└── README.md
```

## How to Run

Requires Python 3 with `pandas` installed (`pip install pandas`).

### Full pipeline (recommended)
```bash
python3 run_all.py
```
This generates data, cleans it, loads it into SQLite, runs all 16 SQL
queries, and runs the edge-case tests — in that order.

### Individual steps
```bash
python3 scripts/generate_data.py        # Part 1
python3 scripts/clean_data.py            # Part 2
python3 scripts/load_to_sqlite.py        # prep for Part 3
python3 scripts/run_queries.py           # Part 3 (executes sql/analysis_queries.sql)
python3 scripts/cli_report_tool.py       # Part 4 (interactive)
python3 tests/test_edge_cases.py         # Part 5
```

### CLI tool usage
```bash
# Interactive
python3 scripts/cli_report_tool.py

# Non-interactive
python3 scripts/cli_report_tool.py --type monthly --start 2025-06-01 --end 2025-06-30
```

## Design Notes

- **Referential integrity**: `order_items.order_id` is always sampled from
  existing `orders.order_id` values during generation, so the base dataset
  is clean by construction. `check_referential_integrity()` and the edge
  case tests verify the *detection logic* using deliberately broken
  synthetic examples.
- **Negative quantity** in `order_items` represents returns and is kept
  (not dropped) — it naturally reduces revenue in the revenue formula and
  is used directly in the return-rate queries.
- **Missing `customer_id`**: kept as `NULL`/`NaN` rather than dropped, so
  orders aren't silently lost; queries explicitly filter these out where a
  valid customer is required (e.g. top-10 customers).
- **Bad date formats** (`DD-MM-YYYY`): `clean_orders()` tries the correct
  format first, falls back to the known bad format, and only marks a row
  "unparseable" if neither works.

## Data Quality Summary (last run)

See `cleaned_data/data_quality_report.txt` for exact numbers from the most
recent run — typically ~5% missing customer_id, ~10% bad date formats,
~3% negative quantities, ~2% invalid emails, and 0 orphaned order_items
(by construction).
