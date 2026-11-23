-- 03: Do late deliveries get worse reviews?
SELECT CASE WHEN is_late = 0      THEN '1. On time'
            WHEN delay_days <= 7  THEN '2. Late (up to 7 days)'
            ELSE                       '3. Late (8+ days)' END AS delivery_group,
       COUNT(*)                     AS orders,
       ROUND(AVG(review_score), 2)  AS avg_review
FROM order_base
WHERE is_delivered = 1 AND review_score IS NOT NULL
GROUP BY 1
ORDER BY 1
