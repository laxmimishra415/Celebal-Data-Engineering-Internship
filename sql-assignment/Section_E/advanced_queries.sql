-- Section E: Advanced Concepts (CASE, ACID, Transactions)

-- Q24. Write a query using CASE to classify products into price tiers: 
-- 'Budget' -> unit_price < 1000, 'Mid-Range' -> unit_price BETWEEN 1000 AND 
-- 5000, 'Premium' -> unit_price > 5000. Display: product_name, unit_price, 
-- price_tier.
SELECT product_name, unit_price,
CASE 
    WHEN unit_price < 1000 THEN 'Budget'
    WHEN unit_price BETWEEN 1000 AND 5000 THEN 'Mid-Range'
    ELSE 'Premium'
END AS price_tier
FROM products;

-- Q25. Using a CASE statement inside an aggregate function, count how many 
-- orders are 'Delivered' vs 'Not Delivered' (all other statuses) in a 
-- single row.
SELECT 
    SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_count,
    SUM(CASE WHEN status != 'Delivered' THEN 1 ELSE 0 END) AS not_delivered_count
FROM orders;

-- Q26. Explain each letter of ACID: A-Atomicity, C-Consistency, I-Isolation, 
-- D-Durability. Give a real-world example (e.g., bank transfer) showing why 
-- each property is important.
-- Answer:
-- Atomicity: A transaction is all-or-nothing. E.g., debiting Account A and 
-- crediting Account B must both succeed, or neither happens.
-- Consistency: The database moves from one valid state to another. E.g., 
-- total money across all accounts stays the same before and after a transfer.
-- Isolation: Concurrent transactions don't interfere with each other. E.g., 
-- two simultaneous transfers don't corrupt each other's balance calculations.
-- Durability: Once committed, a change persists even after a crash. E.g., 
-- a confirmed transfer survives a server restart.

-- Q27. Write a SQL transaction that does the following atomically: 
-- 1. Insert a new order (order_id=1011, customer_id=102, today's date, 
-- 'Pending', 1098.00) 2. Insert two order items for that order 3. Update 
-- the stock_qty of the purchased products 4. If any step fails, ROLLBACK 
-- the entire transaction. Otherwise, COMMIT.
BEGIN TRANSACTION;

INSERT INTO orders (order_id, customer_id, order_date, status, total_amount)
VALUES (1011, 102, date('now'), 'Pending', 1098.00);

INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_pct)
VALUES (5016, 1011, 202, 1, 799.00, 0);
INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_pct)
VALUES (5017, 1011, 206, 1, 299.00, 0);

UPDATE products SET stock_qty = stock_qty - 1 WHERE product_id = 202;
UPDATE products SET stock_qty = stock_qty - 1 WHERE product_id = 206;

COMMIT;
-- If any step fails, run ROLLBACK; instead of COMMIT;