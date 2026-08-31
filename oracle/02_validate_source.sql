SET PAGESIZE 100
SET LINESIZE 220

PROMPT === Oracle source metadata ===
SELECT column_id,
       column_name,
       data_type,
       data_precision,
       data_scale,
       char_length,
       nullable
FROM user_tab_columns
WHERE table_name = 'SALES_ORDERS'
ORDER BY column_id;

PROMPT === DATE values containing a time component ===
SELECT
  SUM(CASE WHEN order_date <> TRUNC(order_date) THEN 1 ELSE 0 END) AS order_date_with_time,
  SUM(CASE WHEN ship_date <> TRUNC(ship_date) THEN 1 ELSE 0 END) AS ship_date_with_time
FROM sales_orders;

PROMPT === NUMBER range and exact aggregate ===
SELECT MIN(unbounded_score) AS min_score,
       MAX(unbounded_score) AS max_score,
       SUM(gross_amount) AS gross_amount_total
FROM sales_orders;

PROMPT === CHAR storage and padding ===
SELECT order_id,
       '"' || legacy_reference || '"' AS displayed_value,
       LENGTH(legacy_reference) AS stored_length,
       LENGTH(RTRIM(legacy_reference)) AS trimmed_length
FROM sales_orders
ORDER BY order_id;

