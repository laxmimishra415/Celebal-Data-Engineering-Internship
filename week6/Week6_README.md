# Week 6 - Spark Assignment (PySpark)

## Objective
Understand Spark architecture and perform efficient data processing using transformations, filtering, schema handling, and optimized file formats (CSV vs Parquet).

## What's covered
- Spark architecture: Driver, Cluster Manager, Executors
- Lazy evaluation & DAG (lineage graph)
- Reading data with schema handling (CSV, Parquet)
- DataFrame transformations: select, filter, rename, cast, add column
- Wide transformations & performance concepts (predicate pushdown)
- CSV vs Parquet performance comparison
- Transformations vs Actions
- Client mode vs Cluster mode
- Building a read → transform → filter → write pipeline
- Best practices for large datasets (`.show()` vs `.collect()`)

## Files
- `Week6_Spark_Assignment.ipynb` — full notebook with explanations (Q1–Q15) and PySpark code
- `data/source.csv`, `data/source.parquet` — synthetic dataset used for the assignment
- `screenshots/` — LMS submission + execution output screenshots

## Tech Stack
Python, PySpark, Jupyter Notebook (Anaconda)

## Author
Laxmi Mishra — Data Engineering Intern, Celebal Technologies
