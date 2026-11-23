-- 01: Main summary table (one row per month x state).
-- The dashboard filters on this, so it stores SUMS (not averages).
-- Rates are calculated in the app as sum / sum, which stays correct after filtering.
-- Revenue excludes canceled and unavailable orders.
SELECT ym,
       state,
       COUNT(*)                                   AS orders,
       SUM(revenue)                               AS revenue,
       SUM(freight)                               AS freight,
       SUM(is_delivered)                          AS delivered_orders,
       SUM(CASE WHEN is_delivered = 1 AND is_late = 1 THEN 1 ELSE 0 END) AS late_orders,
       SUM(review_score)                          AS review_sum,
       COUNT(review_score)                        AS review_n
FROM order_base
WHERE order_status NOT IN ('canceled', 'unavailable')
GROUP BY ym, state
ORDER BY ym, state
