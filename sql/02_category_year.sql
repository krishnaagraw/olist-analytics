-- 02: Revenue and freight per product category per year.
-- Categories with no English name keep the Portuguese name; missing ones become 'unknown'.
SELECT strftime(o.order_purchase_timestamp, '%Y') AS year,
       COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       SUM(oi.price)                 AS revenue,
       SUM(oi.freight_value)         AS freight,
       COUNT(DISTINCT oi.order_id)   AS orders,
       COUNT(*)                      AS items
FROM order_items oi
JOIN orders o   ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY 1, 2
ORDER BY 1, revenue DESC
