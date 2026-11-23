-- 05: Cohort retention. Cohort = month of a customer's first delivered order.
-- month_number = how many months later they ordered again (0 = first order month).
WITH activity AS (
  SELECT customer_unique_id, date_trunc('month', purchased_at) AS order_month
  FROM order_base
  WHERE order_status = 'delivered'
),
first_order AS (
  SELECT customer_unique_id, MIN(order_month) AS cohort_month
  FROM activity
  GROUP BY customer_unique_id
)
SELECT strftime(f.cohort_month, '%Y-%m')                   AS cohort_month,
       date_diff('month', f.cohort_month, a.order_month)   AS month_number,
       COUNT(DISTINCT a.customer_unique_id)                AS customers
FROM first_order f
JOIN activity a ON f.customer_unique_id = a.customer_unique_id
GROUP BY 1, 2
ORDER BY 1, 2
