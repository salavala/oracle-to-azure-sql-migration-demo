SET NOCOUNT ON;

PRINT '=== Azure SQL target metadata ===';
SELECT
    c.column_id,
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable
FROM sys.columns AS c
JOIN sys.types AS t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID(N'dbo.sales_orders')
ORDER BY c.column_id;

PRINT '=== Row-count check ===';
SELECT COUNT_BIG(*) AS target_row_count
FROM dbo.sales_orders;

PRINT '=== DATE semantics ===';
SELECT
    order_id,
    order_date,
    ship_date,
    CASE
        WHEN CONVERT(time(0), order_date) <> '00:00:00' THEN 1
        ELSE 0
    END AS order_date_retained_time
FROM dbo.sales_orders
ORDER BY order_id;

PRINT '=== Exact NUMBER aggregate ===';
SELECT
    MIN(unbounded_score) AS min_score,
    MAX(unbounded_score) AS max_score,
    SUM(gross_amount) AS gross_amount_total
FROM dbo.sales_orders;

PRINT '=== CHAR/VARCHAR semantics ===';
SELECT
    order_id,
    CONCAT('"', legacy_reference, '"') AS displayed_value,
    DATALENGTH(legacy_reference) AS stored_bytes,
    LEN(legacy_reference) AS length_without_trailing_spaces
FROM dbo.sales_orders
ORDER BY order_id;

PRINT '=== Acceptance gate ===';
IF (SELECT COUNT_BIG(*) FROM dbo.sales_orders) <> 4
    THROW 51000, 'Expected four migrated rows.', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.sales_orders
    WHERE order_date IS NULL
       OR gross_amount IS NULL
       OR status_code IS NULL
)
    THROW 51001, 'Required values were lost during migration.', 1;

IF (SELECT SUM(gross_amount) FROM dbo.sales_orders) <> CAST(10000000124958.65 AS decimal(15,2))
    THROW 51002, 'Exact NUMBER aggregate does not match the Oracle source.', 1;

PRINT 'Validation passed.';

