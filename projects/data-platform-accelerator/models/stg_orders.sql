SELECT order_id, customer_id, CAST(amount AS DOUBLE) AS amount, CAST(order_date AS DATE) AS order_date
FROM raw_orders
