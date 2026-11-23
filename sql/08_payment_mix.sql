-- 08: How do customers pay?
SELECT p.payment_type,
       COUNT(DISTINCT p.order_id)              AS orders,
       SUM(p.payment_value)                    AS total_value,
       ROUND(AVG(p.payment_installments), 2)   AS avg_installments
FROM order_payments p
JOIN order_base ob ON p.order_id = ob.order_id
WHERE ob.order_status NOT IN ('canceled', 'unavailable')
  AND p.payment_type <> 'not_defined'
GROUP BY p.payment_type
ORDER BY total_value DESC
