/*
Run only if the custom-mapping assessment approved CHAR(12) -> varchar(12)
and post-migration validation shows retained Oracle padding.
*/
SET XACT_ABORT ON;
BEGIN TRANSACTION;

SELECT order_id,
       CONCAT('"', legacy_reference, '"') AS before_value,
       DATALENGTH(legacy_reference) AS before_bytes
FROM dbo.sales_orders
ORDER BY order_id;

UPDATE dbo.sales_orders
SET legacy_reference = RTRIM(legacy_reference)
WHERE legacy_reference <> RTRIM(legacy_reference);

SELECT order_id,
       CONCAT('"', legacy_reference, '"') AS after_value,
       DATALENGTH(legacy_reference) AS after_bytes
FROM dbo.sales_orders
ORDER BY order_id;

COMMIT TRANSACTION;

