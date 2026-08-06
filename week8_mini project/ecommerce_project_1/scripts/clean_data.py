"""
Part 2: Data Cleaning (pandas)

Functions:
    clean_orders()               -> fixes date formats, handles NULL customer_id
    clean_products()             -> normalizes product names (trim + title case)
    validate_emails()            -> returns list of customer_ids with invalid emails
    check_referential_integrity()-> finds order_items referencing non-existent orders

Running this file end-to-end:
    - reads the raw CSVs from ../data
    - writes cleaned CSVs to ../cleaned_data
    - writes a text report of every issue found to ../cleaned_data/data_quality_report.txt
"""

import os
import re
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
CLEAN_DIR = os.path.join(BASE_DIR, "..", "cleaned_data")
os.makedirs(CLEAN_DIR, exist_ok=True)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_orders(orders_df: pd.DataFrame):
    """
    Fixes order_date formats (handles DD-MM-YYYY as well as YYYY-MM-DD HH:MM:SS)
    and flags/handles NULL customer_id.

    Returns: (cleaned_df, issues_dict)
    """
    df = orders_df.copy()
    issues = {"missing_customer_id": 0, "bad_date_format_fixed": 0, "unparseable_dates": 0}

    # Normalize missing customer_id (empty string / NaN / "NULL" text) -> pd.NA
    df["customer_id"] = df["customer_id"].replace(r"^\s*$", pd.NA, regex=True)
    df["customer_id"] = df["customer_id"].replace("NULL", pd.NA)
    issues["missing_customer_id"] = int(df["customer_id"].isna().sum())

    def parse_date(value):
        value = str(value).strip()
        # Try the correct format first
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return pd.to_datetime(value, format=fmt)
            except ValueError:
                continue
        # Try the known wrong format DD-MM-YYYY
        try:
            dt = pd.to_datetime(value, format="%d-%m-%Y")
            issues["bad_date_format_fixed"] += 1
            return dt
        except ValueError:
            issues["unparseable_dates"] += 1
            return pd.NaT

    df["order_date"] = df["order_date"].apply(parse_date)

    # customer_id kept nullable (Int64) so real IDs stay integers, missing stay NA
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")

    return df, issues


def clean_products(products_df: pd.DataFrame):
    """
    Normalizes product_name: strips leading/trailing whitespace and
    collapses internal double-spaces, then applies title case.

    Returns: (cleaned_df, issues_dict)
    """
    df = products_df.copy()
    original = df["product_name"].copy()

    df["product_name"] = (
        df["product_name"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

    changed = int((original.astype(str).str.strip() != df["product_name"]).sum())
    # more precisely: count rows where raw string differed from cleaned string at all
    changed = int((original.astype(str) != df["product_name"]).sum())
    issues = {"product_names_normalized": changed}
    return df, issues


def validate_emails(customers_df: pd.DataFrame):
    """
    Returns a list of customer_ids whose email fails basic validation
    (missing '@' or missing a domain/dot after the '@').
    """
    invalid_ids = []
    for _, row in customers_df.iterrows():
        email = str(row["email"])
        if not EMAIL_REGEX.match(email):
            invalid_ids.append(row["customer_id"])
    return invalid_ids


def check_referential_integrity(orders_df: pd.DataFrame, order_items_df: pd.DataFrame):
    """
    Returns the subset of order_items rows whose order_id does NOT exist
    in orders.order_id (orphaned rows).
    """
    valid_order_ids = set(orders_df["order_id"])
    orphans = order_items_df[~order_items_df["order_id"].isin(valid_order_ids)]
    return orphans


def main():
    orders = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"), dtype=str)
    order_items = pd.read_csv(os.path.join(DATA_DIR, "order_items.csv"))
    products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))

    orders_clean, order_issues = clean_orders(orders)
    products_clean, product_issues = clean_products(products)
    invalid_email_ids = validate_emails(customers)
    orphan_items = check_referential_integrity(orders_clean.assign(
        order_id=orders_clean["order_id"].astype(int)
    ), order_items)

    # Extra cleaning: negative quantity flagged as a return, not silently dropped
    order_items_clean = order_items.copy()
    order_items_clean["is_return"] = order_items_clean["quantity"] < 0

    # Write cleaned CSVs
    orders_clean.to_csv(os.path.join(CLEAN_DIR, "orders_clean.csv"), index=False)
    products_clean.to_csv(os.path.join(CLEAN_DIR, "products_clean.csv"), index=False)
    order_items_clean.to_csv(os.path.join(CLEAN_DIR, "order_items_clean.csv"), index=False)
    customers.to_csv(os.path.join(CLEAN_DIR, "customers_clean.csv"), index=False)

    report_lines = [
        "DATA QUALITY REPORT",
        "=" * 50,
        f"Orders - missing customer_id: {order_issues['missing_customer_id']}",
        f"Orders - bad date format (DD-MM-YYYY) fixed: {order_issues['bad_date_format_fixed']}",
        f"Orders - unparseable dates: {order_issues['unparseable_dates']}",
        f"Products - names normalized (trim/case): {product_issues['product_names_normalized']}",
        f"Customers - invalid emails found: {len(invalid_email_ids)}",
        f"  Invalid email customer_ids (first 20 shown): {invalid_email_ids[:20]}",
        f"Order_items - negative quantity (returns): {int(order_items_clean['is_return'].sum())}",
        f"Order_items - orphaned rows (order_id not in orders): {len(orphan_items)}",
    ]
    report_path = os.path.join(CLEAN_DIR, "data_quality_report.txt")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    print("\n".join(report_lines))
    print(f"\nCleaned CSVs + report written to: {CLEAN_DIR}")


if __name__ == "__main__":
    main()
