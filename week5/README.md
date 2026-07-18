# Week 5 - Spark Data Cleaning Assignment

## Objective
Understand Spark fundamentals and use it to clean, transform, and analyze data using DataFrames.

### About the Dataset
Since no dataset was provided with the assignment, a synthetic sample dataset was generated matching the required columns (`user_id`, `region`, `product_category`, `subscription`, `store_id`, etc.). Duplicates, null values, and inconsistent timestamp formats were intentionally included to realistically demonstrate the cleaning and transformation operations covered in this assignment.

## What was done
- Loaded a sample transactions dataset (620 rows) into a Spark DataFrame with `inferSchema=True`.
- Performed data cleaning: removed duplicate rows, filled/handled null values (`status`, `price`, `email`, `username`).
- Applied filtering conditions (region, age range, subscription type).
- Used aggregation functions (`count`, `sum`, `avg`, `min`, `max`) with `groupBy`.
- Handled inconsistent timestamp formats using `try_to_timestamp` + `coalesce` instead of relying on default schema inference.
- Built a final pipeline: de-duplicate -> fill null prices -> group by `store_id` -> total revenue.
- Answered all 15 assignment questions (Q1-Q15) with theory + working PySpark code inside `notebook/spark_basics.ipynb`.

## What I observed
- `raw_timestamp` had 4 different date/time formats in the raw data - a single `to_timestamp()` call fails on mixed formats, so multiple format attempts with `try_to_timestamp` + `coalesce` were needed (directly ties into Q14's inferSchema risk).
- 20 duplicate rows were found and removed via `dropDuplicates(["user_id", "transaction_date"])`.
- Only 3 out of 8 cities (Mumbai, Delhi, Bangalore) had more than 100 transaction records.
- Filtering age 18-30 + Premium subscription isolated a meaningful high-value customer segment.

## Folder Structure
```
spark-assignment/
├── data/
│   └── dataset.csv          # sample transactions dataset (620 rows, intentionally messy)
├── notebook/
│   └── spark_basics.ipynb   # full solution: Q1-Q15, executed with outputs
├── output/
│   └── results.csv          # final pipeline output (store_id-wise total revenue)
└── README.md
```

## How to run
1. Open `notebook/spark_basics.ipynb` in Jupyter (via Anaconda).
2. Run all cells top to bottom - PySpark session is created automatically.
3. Final output is written to `output/results.csv`.
