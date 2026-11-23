-- 07: Revenue and average review per seller (delivered orders). Used for the Pareto chart.
SELECT oi.seller_id,
       s.seller_state                     AS state,
       SUM(oi.price)                      AS revenue,
       COUNT(DISTINCT oi.order_id)        AS orders,
       ROUND(AVG(ob.review_score), 2)     AS avg_review
FROM order_items oi
JOIN sellers s     ON oi.seller_id = s.seller_id
JOIN order_base ob ON oi.order_id = ob.order_id
WHERE ob.order_status = 'delivered'
GROUP BY oi.seller_id, s.seller_state
ORDER BY revenue DESC
