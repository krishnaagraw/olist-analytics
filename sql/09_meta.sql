-- 09: Basic facts about the dataset (shown on the dashboard).
SELECT (SELECT COUNT(*) FROM orders)                                AS total_orders,
       (SELECT COUNT(DISTINCT customer_unique_id) FROM customers)   AS total_customers,
       (SELECT COUNT(*) FROM sellers)                               AS total_sellers,
       (SELECT COUNT(*) FROM order_items)                           AS total_items,
       (SELECT strftime(MIN(order_purchase_timestamp), '%Y-%m-%d') FROM orders) AS first_order,
       (SELECT strftime(MAX(order_purchase_timestamp), '%Y-%m-%d') FROM orders) AS last_order
