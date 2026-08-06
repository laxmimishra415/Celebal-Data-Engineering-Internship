"""
Part 4: Python + SQL Integration
A command-line reporting tool. No external libraries except sqlite3.

Usage (interactive):
    python3 cli_report_tool.py

Usage (non-interactive, for testing/automation):
    python3 cli_report_tool.py --type monthly --start 2025-01-01 --end 2025-01-31
"""

import argparse
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "ecommerce.db")

REVENUE_EXPR = "oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)"


def get_period_dates(report_type):
    today = datetime.now()
    if report_type == "daily":
        start = today - timedelta(days=1)
    elif report_type == "weekly":
        start = today - timedelta(weeks=1)
    elif report_type == "monthly":
        start = today - timedelta(days=30)
    else:
        raise ValueError("report_type must be daily, weekly, or monthly")
    return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def summary_for_range(conn, start_date, end_date):
    cur = conn.cursor()

    cur.execute(f"""
        SELECT COUNT(DISTINCT o.order_id),
               COALESCE(SUM({REVENUE_EXPR}), 0),
               COUNT(DISTINCT o.customer_id)
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE date(o.order_date) BETWEEN date(?) AND date(?)
    """, (start_date, end_date))
    total_orders, total_revenue, unique_customers = cur.fetchone()

    cur.execute(f"""
        SELECT p.product_name, SUM({REVENUE_EXPR}) AS rev
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE date(o.order_date) BETWEEN date(?) AND date(?)
        GROUP BY p.product_name
        ORDER BY rev DESC
        LIMIT 3
    """, (start_date, end_date))
    top_products = cur.fetchall()

    return {
        "total_orders": total_orders or 0,
        "total_revenue": round(total_revenue or 0, 2),
        "unique_customers": unique_customers or 0,
        "top_products": top_products,
    }


def previous_period(start_date, end_date):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    span = (end_dt - start_dt).days + 1
    prev_end = start_dt - timedelta(days=1)
    prev_start = prev_end - timedelta(days=span - 1)
    return prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d")


def pct_change(current, previous):
    if previous == 0:
        return None
    return round(100 * (current - previous) / previous, 2)


def print_report(report_type, start_date, end_date, conn):
    current = summary_for_range(conn, start_date, end_date)
    prev_start, prev_end = previous_period(start_date, end_date)
    previous = summary_for_range(conn, prev_start, prev_end)

    print(f"\n{'='*55}")
    print(f"{report_type.upper()} REPORT: {start_date} to {end_date}")
    print(f"{'='*55}")
    print(f"Total Orders     : {current['total_orders']}")
    print(f"Total Revenue    : {current['total_revenue']}")
    print(f"Unique Customers : {current['unique_customers']}")
    print("\nTop 3 Products:")
    if current["top_products"]:
        for name, rev in current["top_products"]:
            print(f"  - {name}: {round(rev, 2)}")
    else:
        print("  (no sales in this period)")

    print(f"\nComparison with previous period ({prev_start} to {prev_end}):")
    for key, label in [("total_orders", "Orders"), ("total_revenue", "Revenue"),
                        ("unique_customers", "Customers")]:
        change = pct_change(current[key], previous[key])
        change_str = f"{change:+.2f}%" if change is not None else "N/A (no prior data)"
        print(f"  {label}: {previous[key]} -> {current[key]}  ({change_str})")
    print(f"{'='*55}\n")


def main():
    parser = argparse.ArgumentParser(description="E-commerce reporting CLI tool")
    parser.add_argument("--type", choices=["daily", "weekly", "monthly"], help="Report type")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (overrides --type default)")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    if args.type and not args.start:
        report_type = args.type
        start_date, end_date = get_period_dates(report_type)
    elif args.start and args.end:
        report_type = args.type or "custom"
        start_date, end_date = args.start, args.end
    else:
        # Interactive mode
        report_type = input("Report type (daily/weekly/monthly): ").strip().lower()
        while report_type not in ("daily", "weekly", "monthly"):
            report_type = input("Please enter daily, weekly, or monthly: ").strip().lower()
        use_custom = input("Enter custom date range? (y/n): ").strip().lower()
        if use_custom == "y":
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            end_date = input("End date (YYYY-MM-DD): ").strip()
        else:
            start_date, end_date = get_period_dates(report_type)

    print_report(report_type, start_date, end_date, conn)
    conn.close()


if __name__ == "__main__":
    main()
