ALTER SESSION SET CURRENT_SCHEMA = MIGRATION_DEMO;

BEGIN
  EXECUTE IMMEDIATE 'DROP TABLE sales_orders PURGE';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -942 THEN
      RAISE;
    END IF;
END;
/

CREATE TABLE sales_orders (
  order_id         NUMBER(12,0)    NOT NULL,
  customer_id      NUMBER(10,0)    NOT NULL,
  order_date       DATE            NOT NULL,
  ship_date        DATE,
  gross_amount     NUMBER(15,2)    NOT NULL,
  discount_rate    NUMBER(5,4)     NOT NULL,
  quantity         NUMBER(5,0)     NOT NULL,
  status_code      CHAR(1)         NOT NULL,
  country_code     CHAR(2)         NOT NULL,
  legacy_reference CHAR(12)        NOT NULL,
  unbounded_score  NUMBER,
  description      VARCHAR2(100),
  CONSTRAINT pk_sales_orders PRIMARY KEY (order_id),
  CONSTRAINT ck_sales_orders_status CHECK (status_code IN ('N', 'P', 'S', 'C'))
);

INSERT INTO sales_orders VALUES (
  100000000001, 2000000001,
  TO_DATE('2026-07-09 09:15:31', 'YYYY-MM-DD HH24:MI:SS'),
  TO_DATE('2026-07-10 00:00:00', 'YYYY-MM-DD HH24:MI:SS'),
  125000.75, 0.0750, 25, 'S', 'US', 'LEGACY-001',
  98.765432, 'DATE retains time; shipment date intentionally drops time'
);

INSERT INTO sales_orders VALUES (
  100000000002, 2000000002,
  TO_DATE('2026-08-24 14:05:07', 'YYYY-MM-DD HH24:MI:SS'),
  NULL,
  9999999999999.99, 0.0000, 1, 'N', 'GB', 'PADDED',
  0.000001, 'Maximum NUMBER(15,2) value and right-padded CHAR value'
);

INSERT INTO sales_orders VALUES (
  100000000003, 2000000003,
  TO_DATE('2024-02-29 23:59:59', 'YYYY-MM-DD HH24:MI:SS'),
  TO_DATE('2024-03-01 16:45:00', 'YYYY-MM-DD HH24:MI:SS'),
  -42.10, 0.1255, 32767, 'C', 'CA', 'LEAP-DAY',
  -123456.654321, 'Leap-day and negative decimal test'
);

INSERT INTO sales_orders VALUES (
  100000000004, 2147483647,
  TO_DATE('1900-01-01 00:00:00', 'YYYY-MM-DD HH24:MI:SS'),
  TO_DATE('1900-01-02 12:30:00', 'YYYY-MM-DD HH24:MI:SS'),
  0.01, 0.9999, 99999, 'P', 'DE', 'FIXED-WIDTH',
  NULL, 'Boundary values for integer and nullable unconstrained NUMBER'
);

COMMIT;

PROMPT Created MIGRATION_DEMO.SALES_ORDERS with four edge-case rows.

