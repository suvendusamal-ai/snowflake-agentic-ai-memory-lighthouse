-- ============================================================
-- P0-F2: Customer Ownership and Isolation Ground Truth
-- ============================================================

USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;
USE DATABASE ECOM_AGENT_MEMORY_DB;

-- TEST ISO-01:
-- James can resolve his own order through customer-scoped SQL.

SELECT
    'ISO-01' AS TEST_ID,
    COUNT(*) AS MATCHING_RECORDS,
    IFF(COUNT(*) = 1, 'PASS', 'FAIL') AS TEST_STATUS
FROM RAW.ORDERS
WHERE CUSTOMER_ID = 'CUST_001'
  AND ORDER_ID = 7821;

-- TEST ISO-02:
-- Another customer must not resolve James's order
-- when the query uses the other customer's ID.

SELECT
    'ISO-02' AS TEST_ID,
    COUNT(*) AS MATCHING_RECORDS,
    IFF(COUNT(*) = 0, 'PASS', 'FAIL') AS TEST_STATUS
FROM RAW.ORDERS
WHERE CUSTOMER_ID = 'CUST_002'
  AND ORDER_ID = 7821;

-- TEST ISO-03:
-- All order references resolve to existing customers.

SELECT
    'ISO-03' AS TEST_ID,
    COUNT(*) AS ORPHAN_RECORDS,
    IFF(COUNT(*) = 0, 'PASS', 'FAIL') AS TEST_STATUS
FROM RAW.ORDERS O
LEFT JOIN RAW.CUSTOMERS C
    ON O.CUSTOMER_ID = C.CUSTOMER_ID
WHERE C.CUSTOMER_ID IS NULL;

-- TEST ISO-04:
-- Each order ID has exactly one owning customer.

WITH OWNERSHIP AS (
    SELECT
        ORDER_ID,
        COUNT(*) AS ROW_COUNT,
        COUNT(DISTINCT CUSTOMER_ID) AS OWNER_COUNT
    FROM RAW.ORDERS
    GROUP BY ORDER_ID
)
SELECT
    'ISO-04' AS TEST_ID,
    COUNT_IF(
        ROW_COUNT <> 1 OR OWNER_COUNT <> 1
    ) AS INVALID_OWNERSHIP_RECORDS,
    IFF(
        COUNT_IF(ROW_COUNT <> 1 OR OWNER_COUNT <> 1) = 0,
        'PASS',
        'FAIL'
    ) AS TEST_STATUS
FROM OWNERSHIP;

-- TEST ISO-05:
-- Customer-scoped join cannot return another customer's
-- shipment or tracking events for order 7821.

SELECT
    'ISO-05' AS TEST_ID,
    COUNT(*) AS EXPOSED_EVENTS,
    IFF(COUNT(*) = 0, 'PASS', 'FAIL') AS TEST_STATUS
FROM RAW.SHIPMENT_EVENTS E
JOIN RAW.SHIPMENTS S
    ON E.SHIPMENT_ID = S.SHIPMENT_ID
JOIN RAW.ORDERS O
    ON S.ORDER_ID = O.ORDER_ID
WHERE O.CUSTOMER_ID = 'CUST_002'
  AND O.ORDER_ID = 7821;