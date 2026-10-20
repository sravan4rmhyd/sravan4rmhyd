-- Gold model: revenue per customer (dbt-style: one SELECT per file, named after the file)
SELECT c.customer_id, c.name, c.country,
       COUNT(o.order_id) AS orders,
       ROUND(SUM(o.amount), 2) AS revenue
FROM stg_customers c
LEFT JOIN stg_orders o USING (customer_id)
GROUP BY ALL
