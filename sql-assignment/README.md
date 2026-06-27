\# Week 2 — E-Commerce Sales Database (SQL Assignment)



\## Objective

Analyze an e-commerce sales dataset using SQL — covering filtering, 

aggregation, joins, and transaction management — to extract business 

insights from a relational database of customers, products, orders, 

and order items.



\## Database Used

SQLite (accessed via Python's `sqlite3` library inside a Jupyter Notebook).



\## Schema

4 tables with Primary Keys, Foreign Keys, CHECK constraints, and indexes:

\- \*\*customers\*\* — customer\_id (PK), name, email (UNIQUE), city, state, join\_date

\- \*\*products\*\* — product\_id (PK), name, category, brand, unit\_price, stock\_qty

\- \*\*orders\*\* — order\_id (PK), customer\_id (FK), order\_date, status, total\_amount

\- \*\*order\_items\*\* — item\_id (PK), order\_id (FK), product\_id (FK), quantity, unit\_price, discount\_pct



\## Folder Structure

