# Week 7 - Delta Lake MERGE Implementation

## Objective
Perform incremental data processing using Delta Lake MERGE operation on the Superstore dataset.

## Steps Completed
1. Loaded Superstore dataset into a Delta table
2. Cleaned data (removed duplicates, handled nulls)
3. Simulated incremental dataset (10 updates + 5 new customer records)
4. Applied MERGE operation to upsert data
5. Validated results (row counts, duplicate check)
6. Displayed final merged dataset

## Tools Used
Databricks Free Edition, PySpark, Delta Lake

## Output
Notebook: `notebooks/delta_scd_assignment.ipynb`
Screenshots: `screenshots/` folder
