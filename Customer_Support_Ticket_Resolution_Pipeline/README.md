# Customer Support Ticket Resolution Pipeline

## Overview
A PySpark data pipeline built on Databricks that processes customer support ticket data 
from a 2-day Customer Support Efficiency Review. Raw CSV data (simulated ADLS Gen2 source) 
is cleaned, validated, transformed, and aggregated using a **Bronze → Silver → Gold** 
medallion architecture to answer 4 key business questions for leadership.

## Tech Stack
- Databricks (PySpark, DataFrame API)
- Python (regex, UDFs)

## Business Questions Answered
1. Ticket resolution rates across the team hierarchy (TL01–TL08)
2. Per-agent performance comparison: Day 1 vs Day 2
3. Compliance with the 15-minute resolution quality threshold
4. Agents who carried over unresolved work from Day 1 to Day 2

## Business Rules Implemented
| Rule | Description |
|------|-------------|
| R1 | Resolution time text (`Xh Xm Xs`) converted to total decimal minutes |
| R2 | Rounding: seconds ≥ 30 → round up to next minute |
| R3 | Successful resolution = status "Resolved" AND time > 15 minutes |
| R4 | Scope filter: only agents under TL01–TL08 included |
| R5 | Drop rows with null/blank ticket_id, agent_id, or resolution_time |
| R6 | Day 2 carry-over: agents who succeeded Day 1 excluded from Day 2 |

## Pipeline Architecture
- **Bronze** — Raw ingestion, Day marker added, no business logic
- **Silver** — Null handling, time conversion, scope filtering, quality threshold
- **Gold** — Carry-over rule applied, aggregated into 4 business-question outputs

## Files
- `Customer_Support_Ticket_Resolution_Pipeline.py` — source notebook (Databricks export)
- `Customer_Support_Ticket_Resolution_Pipeline.ipynb` — Jupyter-compatible notebook

## Notes
Sample data was synthetically generated (no live ADLS Gen2 access), with intentional edge 
cases — nulls, rushed tickets, out-of-scope agents, malformed time strings — to properly 
test every business rule. See the notebook's "Assumptions & Known Limitations" section for details.
