-- 00: Base views used by every other query.
-- KEY IDEA: payments, reviews and items have MANY rows per order.
-- We add each one up (or average it) PER ORDER first, then join.
-- Joining them raw would count the same order several times (double-counting).

CREATE OR REPLACE VIEW review_per_order AS
SELECT order_id, AVG(review_score) AS review_score
FROM order_reviews
GROUP BY order_id;

CREATE OR REPLACE VIEW items_per_order AS
SELECT order_id,
       SUM(price)         AS revenue,
       SUM(freight_value) AS freight,
       COUNT(*)           AS items
FROM order_items
GROUP BY order_id;

-- One row per order. Customer analysis uses customer_unique_id because
-- customer_id changes with every order in this dataset.
CREATE OR REPLACE VIEW order_base AS
SELECT o.order_id,
       c.customer_unique_id,
       c.customer_state AS state,
       o.order_status,
       o.order_purchase_timestamp AS purchased_at,
       strftime(o.order_purchase_timestamp, '%Y-%m') AS ym,
       it.revenue,
       it.freight,
       CASE WHEN o.order_status = 'delivered'
                 AND o.order_delivered_customer_date IS NOT NULL THEN 1 ELSE 0 END AS is_delivered,
       CASE WHEN CAST(o.order_delivered_customer_date AS DATE)
                 > CAST(o.order_estimated_delivery_date AS DATE) THEN 1 ELSE 0 END AS is_late,
       date_diff('day', CAST(o.order_estimated_delivery_date AS DATE),
                        CAST(o.order_delivered_customer_date AS DATE)) AS delay_days,
       date_diff('day', CAST(o.order_purchase_timestamp AS DATE),
                        CAST(o.order_delivered_customer_date AS DATE)) AS delivery_days,
       r.review_score
FROM orders o
JOIN customers c        ON o.customer_id = c.customer_id
JOIN items_per_order it ON o.order_id = it.order_id
LEFT JOIN review_per_order r ON o.order_id = r.order_id;
