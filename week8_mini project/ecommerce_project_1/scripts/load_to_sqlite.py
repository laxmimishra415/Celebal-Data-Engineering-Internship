"""
Loads the cleaned CSVs into a local SQLite database (ecommerce.db)
so Part 3 SQL queries can run against it.
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CLEAN_DIR = os.path.join(BASE_DIR, "..", "cleaned_data")
DB_PATH = os.path.join(BASE_DIR, "..", "ecommerce.db")


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)

    orders = pd.read_csv(os.path.join(CLEAN_DIR, "orders_clean.csv"))
    order_items = pd.read_csv(os.path.join(CLEAN_DIR, "order_items_clean.csv"))
    products = pd.read_csv(os.path.join(CLEAN_DIR, "products_clean.csv"))
    customers = pd.read_csv(os.path.join(CLEAN_DIR, "customers_clean.csv"))

    orders.to_sql("orders", conn, if_exists="replace", index=False)
    order_items.to_sql("order_items", conn, if_exists="replace", index=False)
    products.to_sql("products", conn, if_exists="replace", index=False)
    customers.to_sql("customers", conn, if_exists="replace", index=False)

    conn.execute("CREATE INDEX idx_oi_order_id ON order_items(order_id)")
    conn.execute("CREATE INDEX idx_oi_product_id ON order_items(product_id)")
    conn.execute("CREATE INDEX idx_orders_customer_id ON orders(customer_id)")
    conn.commit()

    print("Loaded tables into", DB_PATH)
    for table in ["orders", "order_items", "products", "customers"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows")

    conn.close()


if __name__ == "__main__":
    main()
