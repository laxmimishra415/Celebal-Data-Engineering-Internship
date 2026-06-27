-- Section A: Basics (SELECT, Primary Keys, Constraints)

-- Q1. Display all columns and rows from the customers table.
SELECT * FROM customers;

-- Q2. Retrieve only the first_name, last_name, and city of all customers.
SELECT first_name, last_name, city FROM customers;

-- Q3. List all unique categories available in the products table.
SELECT DISTINCT category FROM products;

-- Q4. Identify the Primary Key of each table in the schema. Explain why a 
-- Primary Key must be unique and NOT NULL.
-- Answer: customers->customer_id, products->product_id, 
-- orders->order_id, order_items->item_id.
-- A Primary Key must be UNIQUE so every row is identifiable, and NOT NULL 
-- because a missing key breaks identity and any Foreign Key referencing it.

-- Q5. What constraints are applied to the email column in the customers 
-- table? What would happen if you tried to insert a duplicate email?
INSERT INTO customers (customer_id, first_name, last_name, email, city, state, join_date) 
VALUES (999, 'Test', 'User', 'aarav.s@email.com', 'Mumbai', 'Maharashtra', '2024-09-01');
-- Result: IntegrityError - UNIQUE constraint failed: customers.email

-- Q6. Try inserting a product with unit_price = -50. What happens and which 
-- constraint prevents it?
INSERT INTO products (product_id, product_name, category, brand, unit_price, stock_qty) 
VALUES (999, 'Test Product', 'Test', 'TestBrand', -50, 10);
-- Result: IntegrityError - CHECK constraint failed: unit_price > 0