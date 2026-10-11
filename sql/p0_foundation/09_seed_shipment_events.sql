-- ============================================================
-- P0-E4: Deterministic Shipment Event Timeline
-- Target: 500 shipments x 4 events = 2,000 events
-- ============================================================

USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;
USE DATABASE ECOM_AGENT_MEMORY_DB;
USE SCHEMA RAW;

INSERT INTO RAW.SHIPMENT_EVENTS (
    EVENT_ID,
    SHIPMENT_ID,
    EVENT_TIMESTAMP,
    EVENT_TYPE,
    EVENT_LOCATION,
    EVENT_DESCRIPTION,
    EVENT_METADATA,
    CREATED_AT
)
WITH EVENT_SEQUENCE AS (
    SELECT 1 AS EVENT_NO
    UNION ALL SELECT 2
    UNION ALL SELECT 3
    UNION ALL SELECT 4
),
BASE AS (
    SELECT
        S.SHIPMENT_ID,
        S.ORDER_ID,
        S.CARRIER_NAME,
        S.SHIPMENT_STATUS,
        S.DELAY_REASON,
        S.REVISED_DELIVERY_DATE,
        O.ORDER_DATE,
        E.EVENT_NO
    FROM RAW.SHIPMENTS S
    JOIN RAW.ORDERS O
      ON S.ORDER_ID = O.ORDER_ID
    CROSS JOIN EVENT_SEQUENCE E
),
EVENT_DATA AS (
    SELECT
        'EVT_' || TO_VARCHAR(ORDER_ID) || '_' ||
            TO_VARCHAR(EVENT_NO) AS EVENT_ID,

        SHIPMENT_ID,

        CASE
            WHEN ORDER_ID = 7821 THEN
                CASE EVENT_NO
                    WHEN 1 THEN '2026-10-05 09:00:00'::TIMESTAMP_NTZ
                    WHEN 2 THEN '2026-10-06 11:00:00'::TIMESTAMP_NTZ
                    WHEN 3 THEN '2026-10-08 08:30:00'::TIMESTAMP_NTZ
                    ELSE '2026-10-09 10:00:00'::TIMESTAMP_NTZ
                END
            ELSE DATEADD(
                'hour',
                (EVENT_NO - 1) * 24,
                ORDER_DATE
            )
        END AS EVENT_TIMESTAMP,

        CASE
            WHEN ORDER_ID = 7821 THEN
                CASE EVENT_NO
                    WHEN 1 THEN 'ORDER_CONFIRMED'
                    WHEN 2 THEN 'DISPATCHED'
                    WHEN 3 THEN 'WEATHER_DELAY'
                    ELSE 'ETA_REVISED'
                END

            WHEN SHIPMENT_STATUS = 'NOT_DISPATCHED' THEN
                CASE EVENT_NO
                    WHEN 1 THEN 'ORDER_CONFIRMED'
                    WHEN 2 THEN 'CANCELLATION_REQUESTED'
                    WHEN 3 THEN 'CANCELLATION_APPROVED'
                    ELSE 'ORDER_CANCELLED'
                END

            WHEN SHIPMENT_STATUS = 'DELIVERED' THEN
                CASE EVENT_NO
                    WHEN 1 THEN 'ORDER_CONFIRMED'
                    WHEN 2 THEN 'DISPATCHED'
                    WHEN 3 THEN 'OUT_FOR_DELIVERY'
                    ELSE 'DELIVERED'
                END

            WHEN SHIPMENT_STATUS = 'LOST' THEN
                CASE EVENT_NO
                    WHEN 1 THEN 'ORDER_CONFIRMED'
                    WHEN 2 THEN 'DISPATCHED'
                    WHEN 3 THEN 'TRACKING_EXCEPTION'
                    ELSE 'PACKAGE_LOST'
                END

            WHEN SHIPMENT_STATUS = 'DELAYED' THEN
                CASE EVENT_NO
                    WHEN 1 THEN 'ORDER_CONFIRMED'
                    WHEN 2 THEN 'DISPATCHED'
                    WHEN 3 THEN 'DELIVERY_EXCEPTION'
                    ELSE 'ETA_REVISED'
                END

            ELSE
                CASE EVENT_NO
                    WHEN 1 THEN 'ORDER_CONFIRMED'
                    WHEN 2 THEN 'DISPATCHED'
                    WHEN 3 THEN 'IN_TRANSIT'
                    ELSE 'ARRIVED_AT_HUB'
                END
        END AS EVENT_TYPE,

        CASE
            WHEN ORDER_ID = 7821 THEN 'Bengaluru'
            WHEN MOD(ORDER_ID, 3) = 0 THEN 'Mumbai'
            WHEN MOD(ORDER_ID, 3) = 1 THEN 'Hyderabad'
            ELSE 'Chennai'
        END AS EVENT_LOCATION,

        EVENT_NO
    FROM BASE
)
SELECT
    E.EVENT_ID,
    E.SHIPMENT_ID,
    E.EVENT_TIMESTAMP,
    E.EVENT_TYPE,
    E.EVENT_LOCATION,

    CASE
        WHEN E.EVENT_ID = 'EVT_7821_3'
            THEN 'Weather disruption delayed shipment delivery.'
        WHEN E.EVENT_ID = 'EVT_7821_4'
            THEN 'Delivery ETA revised to 2026-10-12.'
        ELSE REPLACE(E.EVENT_TYPE, '_', ' ')
            || ' event recorded for shipment '
            || E.SHIPMENT_ID || '.'
    END AS EVENT_DESCRIPTION,

    OBJECT_CONSTRUCT(
        'event_sequence', E.EVENT_NO,
        'source_system', 'SYNTHETIC_ECOM_TRACKING',
        'data_classification', 'SYNTHETIC'
    ) AS EVENT_METADATA,

    E.EVENT_TIMESTAMP AS CREATED_AT

FROM EVENT_DATA E
WHERE NOT EXISTS (
    SELECT 1
    FROM RAW.SHIPMENT_EVENTS X
    WHERE X.EVENT_ID = E.EVENT_ID
);