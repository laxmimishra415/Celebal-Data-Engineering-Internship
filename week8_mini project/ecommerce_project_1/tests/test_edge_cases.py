"""
Part 5: Edge Case Handling
Test functions verifying how the system behaves under bad/edge-case data.

Run with:  python3 tests/test_edge_cases.py
(plain functions + asserts, no pytest required, but pytest-compatible too)
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from clean_data import check_referential_integrity  # noqa: E402


def test_order_id_not_in_orders():
    """1. What happens when order_items has an order_id not in orders?"""
    orders = pd.DataFrame({"order_id": [1, 2, 3]})
    order_items = pd.DataFrame({
        "item_id": [1, 2, 3],
        "order_id": [1, 2, 999],   # 999 does not exist in orders
        "product_id": [10, 11, 12],
        "quantity": [1, 2, 1],
    })
    orphans = check_referential_integrity(orders, order_items)
    assert len(orphans) == 1
    assert orphans.iloc[0]["order_id"] == 999
    print("PASS: orphaned order_items (order_id not in orders) correctly detected ->",
          list(orphans["item_id"]))


def test_discount_percent_over_100():
    """2. What happens when discount_percent > 100?"""
    order_items = pd.DataFrame({
        "quantity": [2],
        "unit_price": [100.0],
        "discount_percent": [150],   # invalid: >100
    })
    # Revenue formula would go negative, which is not meaningful -> flag it
    invalid_rows = order_items[
        (order_items["discount_percent"] < 0) | (order_items["discount_percent"] > 100)
    ]
    assert len(invalid_rows) == 1
    revenue = order_items["quantity"] * order_items["unit_price"] * (1 - order_items["discount_percent"] / 100)
    assert revenue.iloc[0] < 0, "discount > 100% produces negative revenue, confirming it must be rejected/clamped"
    print("PASS: discount_percent > 100 detected as invalid (would yield negative revenue:",
          round(revenue.iloc[0], 2), ") -> should be clamped to [0, 100] or rejected during cleaning")


def test_zero_quantity():
    """3. What happens when quantity is 0?"""
    order_items = pd.DataFrame({
        "quantity": [0],
        "unit_price": [500.0],
        "discount_percent": [10],
    })
    revenue = order_items["quantity"] * order_items["unit_price"] * (1 - order_items["discount_percent"] / 100)
    assert revenue.iloc[0] == 0
    # Zero quantity is neither a purchase nor a return -- it contributes 0 revenue
    # and should be excluded from "total items" denominators to avoid skewing return rates.
    print("PASS: quantity=0 contributes 0 revenue and is treated as neither purchase nor return")


def test_future_order_date():
    """4. What happens when order_date is in the future?"""
    future_date = datetime.now() + timedelta(days=30)
    orders = pd.DataFrame({
        "order_id": [1],
        "order_date": [future_date],
    })
    today = pd.Timestamp(datetime.now())
    future_orders = orders[pd.to_datetime(orders["order_date"]) > today]
    assert len(future_orders) == 1
    print("PASS: future-dated order detected ->", future_orders.iloc[0]["order_date"],
          "-> should be flagged/excluded from historical reports, not silently included")


def run_all():
    tests = [
        test_order_id_not_in_orders,
        test_discount_percent_over_100,
        test_zero_quantity,
        test_future_order_date,
    ]
    print("Running Part 5 edge case tests...\n")
    for t in tests:
        t()
    print("\nAll edge case tests passed.")


if __name__ == "__main__":
    run_all()
