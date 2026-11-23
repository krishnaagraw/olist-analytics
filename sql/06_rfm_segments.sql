-- 06: RFM segmentation (Recency, Frequency, Monetary).
-- Almost every customer ordered once, so frequency cannot be split into 5 equal groups.
-- Instead: anyone with 2+ orders is a "Repeat buyer"; one-time buyers are split by recency and spend.
WITH pay AS (
  SELECT order_id, SUM(payment_value) AS order_value
  FROM order_payments
  GROUP BY order_id
),
base AS (
  SELECT ob.customer_unique_id,
         date_diff('day', MAX(ob.purchased_at),
                   (SELECT MAX(order_purchase_timestamp) FROM orders)) AS recency_days,
         COUNT(*)            AS frequency,
         SUM(pay.order_value) AS monetary
  FROM order_base ob
  JOIN pay ON ob.order_id = pay.order_id
  WHERE ob.order_status = 'delivered'
  GROUP BY ob.customer_unique_id
),
scored AS (
  SELECT *,
         NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,  -- 5 = bought most recently
         NTILE(5) OVER (ORDER BY monetary)          AS m_score   -- 5 = spent the most
  FROM base
),
labeled AS (
  SELECT *,
         CASE WHEN frequency >= 2                  THEN 'Repeat buyers'
              WHEN r_score >= 4 AND m_score >= 4   THEN 'Recent big spenders'
              WHEN r_score <= 2 AND m_score >= 4   THEN 'At-risk big spenders'
              WHEN r_score <= 2                    THEN 'Lapsed one-time buyers'
              ELSE                                      'Regular one-time buyers' END AS segment
  FROM scored
)
SELECT segment,
       COUNT(*)                   AS customers,
       ROUND(AVG(monetary), 2)    AS avg_spend,
       ROUND(SUM(monetary), 2)    AS total_spend
FROM labeled
GROUP BY segment
ORDER BY total_spend DESC
