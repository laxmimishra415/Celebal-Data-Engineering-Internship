-- =====================================================================
-- Part 3: SQL Analysis
-- Run against ecommerce.db (created by scripts/load_to_sqlite.py)
-- =====================================================================

-- ---------------------------------------------------------------------
-- BASIC QUERIES
-- ---------------------------------------------------------------------

-- 1. Total revenue per category
SELECT p.category,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- 2. Top 10 customers by total order value
SELECT o.customer_id,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)), 2) AS total_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.customer_id IS NOT NULL
GROUP BY o.customer_id
ORDER BY total_order_value DESC
LIMIT 10;

-- 3. Month-wise order count for the last 12 months
SELECT strftime('%Y-%m', order_date) AS order_month,
       COUNT(*) AS order_count
FROM orders
WHERE order_date >= date((SELECT MAX(order_date) FROM orders), '-12 months')
GROUP BY order_month
ORDER BY order_month;

-- ---------------------------------------------------------------------
-- INTERMEDIATE QUERIES
-- ---------------------------------------------------------------------

-- 4. Customers who placed orders but never had any item delivered
SELECT DISTINCT o.customer_id
FROM orders o
WHERE o.customer_id IS NOT NULL
  AND o.customer_id NOT IN (
      SELECT customer_id FROM orders WHERE status = 'DELIVERED' AND customer_id IS NOT NULL
  );

-- 5. Products that were ordered but had more returns than purchases
SELECT p.product_id, p.product_name,
       SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS total_purchased,
       SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS total_returned
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
HAVING total_returned > total_purchased;

-- 6. Return rate (returned items / total items) per category
SELECT p.category,
       SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS returned_items,
       SUM(ABS(oi.quantity)) AS total_items,
       ROUND(1.0 * SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END)
             / SUM(ABS(oi.quantity)), 4) AS return_rate
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category;

-- ---------------------------------------------------------------------
-- ADVANCED QUERIES (Window Functions, CTEs, Subqueries)
-- ---------------------------------------------------------------------

-- 7. Running totals of revenue per region, ordered by date
WITH daily AS (
    SELECT o.region_code,
           date(o.order_date) AS order_date,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY o.region_code, date(o.order_date)
)
SELECT region_code, order_date,
       ROUND(daily_revenue, 2) AS daily_revenue,
       ROUND(SUM(daily_revenue) OVER (PARTITION BY region_code ORDER BY order_date), 2) AS running_total
FROM daily
ORDER BY region_code, order_date;

-- 8. DENSE_RANK: rank products by total revenue within each category
WITH product_revenue AS (
    SELECT p.category, p.product_name,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS total_revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.category, p.product_name
)
SELECT category, product_name,
       ROUND(total_revenue, 2) AS total_revenue,
       DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category;

-- 9. LAG/LEAD: days between consecutive orders per customer, flag "At Risk"
WITH cust_orders AS (
    SELECT customer_id, order_date,
           LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS previous_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
),
gaps AS (
    SELECT customer_id, order_date, previous_order_date,
           CASE WHEN previous_order_date IS NOT NULL
                THEN julianday(order_date) - julianday(previous_order_date)
                ELSE NULL END AS days_gap
    FROM cust_orders
),
avg_gaps AS (
    SELECT customer_id, AVG(days_gap) AS avg_gap
    FROM gaps
    WHERE days_gap IS NOT NULL
    GROUP BY customer_id
)
SELECT g.customer_id, g.order_date, g.previous_order_date,
       ROUND(g.days_gap, 2) AS days_gap,
       CASE WHEN a.avg_gap > 30 THEN 'At Risk' ELSE 'Normal' END AS risk_flag
FROM gaps g
LEFT JOIN avg_gaps a ON a.customer_id = g.customer_id
ORDER BY g.customer_id, g.order_date;

-- 10. Multi-level CTE: monthly revenue -> High/Medium/Low -> count per month
WITH monthly_revenue AS (
    SELECT o.customer_id, strftime('%Y-%m', o.order_date) AS order_month,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id, order_month
),
categorized AS (
    SELECT customer_id, order_month, revenue,
           CASE WHEN revenue > 10000 THEN 'High'
                WHEN revenue >= 5000 THEN 'Medium'
                ELSE 'Low' END AS revenue_category
    FROM monthly_revenue
)
SELECT order_month, revenue_category, COUNT(DISTINCT customer_id) AS customer_count
FROM categorized
GROUP BY order_month, revenue_category
ORDER BY order_month, revenue_category;

-- 11. NTILE: divide customers into quartiles by lifetime value
WITH customer_value AS (
    SELECT o.customer_id,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS total_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
quartiled AS (
    SELECT customer_id, total_value,
           NTILE(4) OVER (ORDER BY total_value DESC) AS quartile
    FROM customer_value
)
SELECT customer_id, ROUND(total_value, 2) AS total_value, quartile,
       CASE quartile WHEN 1 THEN 'Platinum' WHEN 2 THEN 'Gold'
                     WHEN 3 THEN 'Silver' ELSE 'Bronze' END AS quartile_label
FROM quartiled
ORDER BY total_value DESC;

-- 12. Year-over-year comparison
WITH monthly AS (
    SELECT strftime('%Y', o.order_date) AS year,
           strftime('%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY year, month
)
SELECT curr.year, curr.month,
       ROUND(curr.revenue, 2) AS revenue,
       ROUND(prev.revenue, 2) AS prev_year_revenue,
       CASE WHEN prev.revenue IS NOT NULL AND prev.revenue != 0
            THEN ROUND(100.0 * (curr.revenue - prev.revenue) / prev.revenue, 2)
            ELSE NULL END AS yoy_growth_percent
FROM monthly curr
LEFT JOIN monthly prev
       ON prev.month = curr.month
      AND CAST(prev.year AS INTEGER) = CAST(curr.year AS INTEGER) - 1
ORDER BY curr.year, curr.month;

-- 13. First/last purchased category per customer, flag category_shift
WITH cust_cat AS (
    SELECT o.customer_id, o.order_date, p.category
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.customer_id IS NOT NULL
),
first_last AS (
    SELECT DISTINCT customer_id,
           FIRST_VALUE(category) OVER (
               PARTITION BY customer_id ORDER BY order_date
               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
           ) AS first_category,
           LAST_VALUE(category) OVER (
               PARTITION BY customer_id ORDER BY order_date
               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
           ) AS last_category
    FROM cust_cat
)
SELECT customer_id, first_category, last_category,
       CASE WHEN first_category != last_category THEN 'Yes' ELSE 'No' END AS category_shift
FROM first_last
ORDER BY customer_id;

-- 14. Cumulative distribution: % of revenue from top customers
WITH customer_revenue AS (
    SELECT o.customer_id,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
ranked AS (
    SELECT customer_id, revenue,
           SUM(revenue) OVER (ORDER BY revenue DESC
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue,
           SUM(revenue) OVER () AS grand_total
    FROM customer_revenue
)
SELECT customer_id, ROUND(revenue, 2) AS revenue,
       ROUND(cumulative_revenue, 2) AS cumulative_revenue,
       ROUND(100.0 * cumulative_revenue / grand_total, 2) AS cumulative_percent
FROM ranked
ORDER BY revenue DESC;

-- 15. Complex CTE: cohort analysis by registration month
WITH cohorts AS (
    SELECT customer_id, strftime('%Y-%m', registration_date) AS cohort_month
    FROM customers
),
customer_orders AS (
    SELECT o.customer_id, strftime('%Y-%m', o.order_date) AS order_month
    FROM orders o
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id, order_month
),
cohort_activity AS (
    SELECT c.customer_id, c.cohort_month, co.order_month,
           (CAST(strftime('%Y', co.order_month || '-01') AS INTEGER) * 12 +
            CAST(strftime('%m', co.order_month || '-01') AS INTEGER)) -
           (CAST(strftime('%Y', c.cohort_month || '-01') AS INTEGER) * 12 +
            CAST(strftime('%m', c.cohort_month || '-01') AS INTEGER)) AS month_offset
    FROM cohorts c
    JOIN customer_orders co ON co.customer_id = c.customer_id
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_customers
    FROM cohorts
    GROUP BY cohort_month
)
SELECT ca.cohort_month, ca.month_offset,
       COUNT(DISTINCT ca.customer_id) AS active_customers,
       cs.cohort_customers,
       ROUND(100.0 * COUNT(DISTINCT ca.customer_id) / cs.cohort_customers, 2) AS retention_rate
FROM cohort_activity ca
JOIN cohort_size cs ON cs.cohort_month = ca.cohort_month
WHERE ca.month_offset BETWEEN 0 AND 3
GROUP BY ca.cohort_month, ca.month_offset
ORDER BY ca.cohort_month, ca.month_offset;

-- 16. Self-join: products frequently bought together
SELECT p1.product_name AS product_a, p2.product_name AS product_b,
       COUNT(*) AS times_bought_together
FROM order_items oi1
JOIN order_items oi2 ON oi1.order_id = oi2.order_id AND oi1.product_id < oi2.product_id
JOIN products p1 ON p1.product_id = oi1.product_id
JOIN products p2 ON p2.product_id = oi2.product_id
GROUP BY p1.product_name, p2.product_name
ORDER BY times_bought_together DESC
LIMIT 20;
