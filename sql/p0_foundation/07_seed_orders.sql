-- ============================================================
-- P0-E2: Deterministic Synthetic Orders
-- Target: 500 orders
-- Primary scenario: James / Order 7821
-- ============================================================

USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;
USE DATABASE ECOM_AGENT_MEMORY_DB;
USE SCHEMA RAW;

INSERT INTO RAW.ORDERS (
    ORDER_ID,
    CUSTOMER_ID,
    ORDER_DATE,
    ORDER_AMOUNT,
    CURRENCY,
    ORDER_STATUS,
    PROMISED_DELIVERY_DATE,
    ACTUAL_DELIVERY_DATE,
    CREATED_AT,
    UPDATED_AT
)
SELECT
    S.ORDER_ID,
    S.CUSTOMER_ID,
    S.ORDER_DATE,
    S.ORDER_AMOUNT,
    'INR',
    S.ORDER_STATUS,
    S.PROMISED_DELIVERY_DATE,
    S.ACTUAL_DELIVERY_DATE,
    S.ORDER_DATE,
    '2026-10-10 12:00:00'::TIMESTAMP_NTZ
FROM (
    SELECT
        7820 + N AS ORDER_ID,

        'CUST_' ||
            LPAD(
                TO_VARCHAR(
                    CASE
                        WHEN N = 1 THEN 1
                        ELSE MOD(N - 1, 100) + 1
                    END
                ),
                3,
                '0'
            ) AS CUSTOMER_ID,

        DATEADD(
            'day',
            MOD(N - 1, 25),
            '2026-09-01 10:00:00'::TIMESTAMP_NTZ
        ) AS ORDER_DATE,

        CASE
            WHEN N = 1 THEN 2500.00
            ELSE (500 + MOD(N * 137, 9500))::NUMBER(12,2)
        END AS ORDER_AMOUNT,

        CASE
            WHEN N = 1 THEN 'SHIPPED'
            WHEN MOD(N, 20) = 0 THEN 'CANCELLED'
            WHEN MOD(N, 17) = 0 THEN 'LOST'
            WHEN MOD(N, 7) = 0 THEN 'DELAYED'
            WHEN MOD(N, 3) = 0 THEN 'SHIPPED'
            ELSE 'DELIVERED'
        END AS ORDER_STATUS,

        CASE
            WHEN N = 1 THEN '2026-10-08'::DATE
            ELSE DATEADD(
                'day',
                5 + MOD(N, 5),
                DATEADD(
                    'day',
                    MOD(N - 1, 25),
                    '2026-09-01'::DATE
                )
            )
        END AS PROMISED_DELIVERY_DATE,

        CASE
            WHEN N = 1 THEN NULL
            WHEN MOD(N, 20) = 0 THEN NULL
            WHEN MOD(N, 17) = 0 THEN NULL
            WHEN MOD(N, 7) = 0 THEN NULL
            WHEN MOD(N, 3) = 0 THEN NULL
            ELSE DATEADD(
                'day',
                4 + MOD(N, 4),
                DATEADD(
                    'day',
                    MOD(N - 1, 25),
                    '2026-09-01'::DATE
                )
            )
        END AS ACTUAL_DELIVERY_DATE

    FROM (
        SELECT
            ROW_NUMBER() OVER (ORDER BY SEQ4()) AS N
        FROM TABLE(GENERATOR(ROWCOUNT => 500))
    )
) S
WHERE NOT EXISTS (
    SELECT 1
    FROM RAW.ORDERS O
    WHERE O.ORDER_ID = S.ORDER_ID
);