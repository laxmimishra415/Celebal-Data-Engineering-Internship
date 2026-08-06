"""
Part 1: Data Generation
Generates 4 CSV files with realistic but intentionally messy e-commerce data:
- orders.csv
- order_items.csv
- products.csv
- customers.csv

Intentional issues injected:
- 5% of orders have NULL customer_id
- 3% of order_items have negative quantity (returns)
- Some orders have order_date in wrong format (DD-MM-YYYY instead of YYYY-MM-DD HH:MM:SS)
- Some product names have extra spaces / mixed case
- 2% of emails are invalid (missing @ or domain)

Referential integrity: order_items.order_id is always sampled from existing
orders.order_id, so every item legitimately belongs to a real order (the
edge-case tests separately verify what happens if this is ever violated).
"""

import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT_DIR, exist_ok=True)

N_CUSTOMERS = 600
N_PRODUCTS = 150
N_ORDERS = 2000
N_ORDER_ITEMS = 5000

CATEGORIES = {
    "Electronics": ["Mobiles", "Laptops", "Accessories", "Audio"],
    "Clothing": ["Men", "Women", "Kids", "Footwear"],
    "Home": ["Kitchen", "Furniture", "Decor", "Cleaning"],
    "Books": ["Fiction", "Non-Fiction", "Academic", "Comics"],
}

CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]
ORDER_STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
REGION_CODES = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Diya", "Ananya", "Ishaan", "Kabir",
               "Meera", "Riya", "Sai", "Vihaan", "Zara", "Arjun", "Kiara",
               "Rohan", "Priya", "Aman", "Neha", "Karan", "Pooja"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Mishra", "Reddy", "Nair", "Iyer",
              "Singh", "Patel", "Das", "Rao", "Chatterjee", "Kapoor", "Malhotra"]

PRODUCT_ADJ = ["Pro", "Max", "Mini", "Ultra", "Plus", "Lite", "Classic", "Smart"]
PRODUCT_NOUN = {
    "Mobiles": ["Phone", "Smartphone"], "Laptops": ["Laptop", "Notebook"],
    "Accessories": ["Charger", "Cable", "Case", "Earphones"], "Audio": ["Speaker", "Headphone"],
    "Men": ["Shirt", "Jeans", "Jacket"], "Women": ["Dress", "Top", "Saree"],
    "Kids": ["T-Shirt", "Shorts"], "Footwear": ["Sneakers", "Sandals"],
    "Kitchen": ["Mixer", "Cookware Set", "Kettle"], "Furniture": ["Chair", "Table", "Sofa"],
    "Decor": ["Wall Art", "Lamp", "Vase"], "Cleaning": ["Vacuum Cleaner", "Mop"],
    "Fiction": ["Novel", "Story Collection"], "Non-Fiction": ["Biography", "Guide"],
    "Academic": ["Textbook", "Reference Book"], "Comics": ["Comic Pack", "Graphic Novel"],
}


def messy_case(name):
    """Randomly mess up casing/spacing to simulate dirty product names."""
    r = random.random()
    if r < 0.15:
        return f"  {name}  "
    if r < 0.30:
        return name.upper()
    if r < 0.45:
        return name.lower()
    return name


def random_email(name, idx, invalid=False):
    base = name.lower().replace(" ", ".")
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com"])
    if invalid:
        variant = random.choice(["no_at", "no_domain"])
        if variant == "no_at":
            return f"{base}{idx}{domain}"          # missing @
        else:
            return f"{base}{idx}@"                  # missing domain
    return f"{base}{idx}@{domain}"


def random_date(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def generate_customers():
    rows = []
    start = datetime(2022, 1, 1)
    end = datetime(2026, 7, 1)
    for i in range(1, N_CUSTOMERS + 1):
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        name = f"{fname} {lname}"
        invalid_email = random.random() < 0.02
        email = random_email(name, i, invalid=invalid_email)
        reg_date = random_date(start, end).strftime("%Y-%m-%d")
        ctype = random.choices(CUSTOMER_TYPES, weights=[0.6, 0.3, 0.1])[0]
        rows.append([i, name, email, reg_date, ctype])
    path = os.path.join(OUT_DIR, "customers.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "customer_name", "email", "registration_date", "customer_type"])
        w.writerows(rows)
    print(f"customers.csv -> {len(rows)} rows")
    return [r[0] for r in rows]


def generate_products():
    rows = []
    pid = 1
    for category, subcats in CATEGORIES.items():
        for _ in range(N_PRODUCTS // (len(CATEGORIES) * len(subcats)) + 1):
            for subcat in subcats:
                if pid > N_PRODUCTS:
                    break
                noun = random.choice(PRODUCT_NOUN[subcat])
                adj = random.choice(PRODUCT_ADJ)
                base_name = f"{adj} {noun} {random.randint(100,999)}"
                name = messy_case(base_name)
                cost_price = round(random.uniform(50, 50000), 2)
                rows.append([pid, name, category, subcat, cost_price])
                pid += 1
            if pid > N_PRODUCTS:
                break
    path = os.path.join(OUT_DIR, "products.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "product_name", "category", "subcategory", "cost_price"])
        w.writerows(rows)
    print(f"products.csv -> {len(rows)} rows")
    return [r[0] for r in rows]


def generate_orders(customer_ids):
    rows = []
    start = datetime(2024, 1, 1)
    end = datetime(2026, 8, 1)
    for i in range(1, N_ORDERS + 1):
        null_customer = random.random() < 0.05
        cust = "" if null_customer else random.choice(customer_ids)
        dt = random_date(start, end)
        wrong_format = random.random() < 0.10
        if wrong_format:
            order_date = dt.strftime("%d-%m-%Y")  # intentional wrong format
        else:
            order_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        status = random.choices(
            ORDER_STATUSES, weights=[0.15, 0.20, 0.45, 0.10, 0.10]
        )[0]
        region = random.choice(REGION_CODES)
        rows.append([i, cust, order_date, status, region])
    path = os.path.join(OUT_DIR, "orders.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer_id", "order_date", "status", "region_code"])
        w.writerows(rows)
    print(f"orders.csv -> {len(rows)} rows")
    return [r[0] for r in rows]


def generate_order_items(order_ids, product_ids):
    rows = []
    for i in range(1, N_ORDER_ITEMS + 1):
        order_id = random.choice(order_ids)  # guarantees referential integrity
        product_id = random.choice(product_ids)
        is_return = random.random() < 0.03
        quantity = -random.randint(1, 3) if is_return else random.randint(1, 5)
        unit_price = round(random.uniform(100, 20000), 2)
        discount_percent = round(random.uniform(0, 100), 1)
        rows.append([i, order_id, product_id, quantity, unit_price, discount_percent])
    path = os.path.join(OUT_DIR, "order_items.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"])
        w.writerows(rows)
    print(f"order_items.csv -> {len(rows)} rows")


def main():
    customer_ids = generate_customers()
    product_ids = generate_products()
    order_ids = generate_orders(customer_ids)
    generate_order_items(order_ids, product_ids)
    print("\nAll 4 CSV files generated in:", OUT_DIR)


if __name__ == "__main__":
    main()
