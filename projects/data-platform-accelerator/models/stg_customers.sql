SELECT DISTINCT customer_id, name, country, CAST(signup_date AS DATE) AS signup_date
FROM raw_customers
