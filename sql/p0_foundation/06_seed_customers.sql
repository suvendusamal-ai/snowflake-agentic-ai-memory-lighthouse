-- ============================================================
-- P0-E1: Deterministic Synthetic Customer Dataset
-- ============================================================

USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;
USE DATABASE ECOM_AGENT_MEMORY_DB;
USE SCHEMA RAW;

-- Idempotent insertion: existing customer IDs are not duplicated.

INSERT INTO RAW.CUSTOMERS (
    CUSTOMER_ID,
    CUSTOMER_NAME,
    EMAIL,
    PHONE,
    CITY,
    STATE,
    COUNTRY,
    CUSTOMER_STATUS,
    CREATED_AT,
    UPDATED_AT
)
SELECT
    'CUST_' || LPAD(TO_VARCHAR(N), 3, '0'),

    CASE
        WHEN N = 1 THEN 'James'
        ELSE 'Customer ' || LPAD(TO_VARCHAR(N), 3, '0')
    END,

    'customer' || LPAD(TO_VARCHAR(N), 3, '0')
        || '@example.com',

    '90000' || LPAD(TO_VARCHAR(N), 5, '0'),

    CASE MOD(N, 5)
        WHEN 0 THEN 'Mumbai'
        WHEN 1 THEN 'Bengaluru'
        WHEN 2 THEN 'Hyderabad'
        WHEN 3 THEN 'Pune'
        ELSE 'Chennai'
    END,

    CASE MOD(N, 5)
        WHEN 0 THEN 'Maharashtra'
        WHEN 1 THEN 'Karnataka'
        WHEN 2 THEN 'Telangana'
        WHEN 3 THEN 'Maharashtra'
        ELSE 'Tamil Nadu'
    END,

    'INDIA',
    'ACTIVE',
    '2026-09-01 09:00:00'::TIMESTAMP_NTZ,
    '2026-09-01 09:00:00'::TIMESTAMP_NTZ

FROM (
    SELECT SEQ4() + 1 AS N
    FROM TABLE(GENERATOR(ROWCOUNT => 100))
) S
WHERE NOT EXISTS (
    SELECT 1
    FROM RAW.CUSTOMERS C
    WHERE C.CUSTOMER_ID =
        'CUST_' || LPAD(TO_VARCHAR(S.N), 3, '0')
);