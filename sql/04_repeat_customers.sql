-- 04: How many orders does each real customer place? (delivered orders only)
WITH per_customer AS (
  SELECT customer_unique_id, COUNT(*) AS n_orders
  FROM order_base
  WHERE order_status = 'delivered'
  GROUP BY customer_unique_id
)
SELECT CASE WHEN n_orders = 1 THEN '1 order'
            WHEN n_orders = 2 THEN '2 orders'
            ELSE '3+ orders' END AS order_group,
       COUNT(*) AS customers
FROM per_customer
GROUP BY 1
ORDER BY 1
