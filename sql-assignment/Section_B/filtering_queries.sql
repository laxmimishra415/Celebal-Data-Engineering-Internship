-- Section B: Filtering & Optimization (WHERE, Indexes)

-- Q7. Retrieve all orders with status = 'Delivered'.
SELECT * FROM orders WHERE status = 'Delivered';

-- Q8. Find all products in the 'Electronics' category with a unit_price 
-- greater than ₹2000.
SELECT * FROM products 
WHERE category = 'Electronics' AND unit_price > 2000;

-- Q9. List all customers who joined in the year 2024 and belong to the 
-- state 'Maharashtra'.
SELECT * FROM customers 
WHERE strftime('%Y', join_date) = '2024' AND state = 'Maharashtra';

-- Q10. Find all orders placed between '2024-08-10' and '2024-08-25' 
-- (inclusive) that are NOT cancelled.
SELECT * FROM orders 
WHERE order_date BETWEEN '2024-08-10' AND '2024-08-25' 
AND status != 'Cancelled';

-- Q11. Explain what the index idx_orders_date does. How would it improve 
-- the performance of a query that filters orders by order_date? Write a 
-- sample query that would benefit from this index.
-- Answer: idx_orders_date is an index built on the order_date column. 
-- Without it, SQLite performs a full table scan to find matches. With the 
-- index, SQLite uses a sorted B-tree structure to jump directly to matching 
-- rows, significantly speeding up date-based filters as the table grows.
SELECT * FROM orders WHERE order_date = '2024-08-15';

-- Q12. If you run: SELECT * FROM customers WHERE YEAR(join_date) = 2024; 
-- — would the index on join_date be used? Explain why or why not, and 
-- rewrite the query to be index-friendly (SARGable).
-- Answer: No, the index would NOT be used. Wrapping a column in a function 
-- (e.g., YEAR() or strftime()) forces the database to evaluate that function 
-- on every row, making the query non-SARGable and forcing a full table scan.
-- Index-friendly (SARGable) rewrite:
SELECT * FROM customers 
WHERE join_date >= '2024-01-01' AND join_date < '2025-01-01';