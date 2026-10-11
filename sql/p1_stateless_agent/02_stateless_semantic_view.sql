USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;
USE DATABASE ECOM_AGENT_MEMORY_DB;
USE SCHEMA AGENTS;

CREATE SEMANTIC VIEW IF NOT EXISTS ECOM_STATELESS_SEMANTIC_VIEW

TABLES (
    orders AS ECOM_AGENT_MEMORY_DB.RAW.ORDERS
        PRIMARY KEY (ORDER_ID),

    shipments AS ECOM_AGENT_MEMORY_DB.RAW.SHIPMENTS
        PRIMARY KEY (SHIPMENT_ID)
)

RELATIONSHIPS (
    order_shipments AS
        shipments (ORDER_ID)
        REFERENCES orders (ORDER_ID)
)

FACTS (
    orders.order_amount AS ORDER_AMOUNT
        COMMENT = 'Monetary amount of the order',

    orders.order_date AS ORDER_DATE
        COMMENT = 'Timestamp when the order was placed'
)

DIMENSIONS (
    orders.order_id AS ORDER_ID,
    orders.customer_id AS CUSTOMER_ID,
    orders.order_status AS ORDER_STATUS,
    orders.currency AS CURRENCY,
    orders.promised_delivery_date AS PROMISED_DELIVERY_DATE,

    shipments.shipment_id AS SHIPMENT_ID,
    shipments.carrier_name AS CARRIER_NAME,
    shipments.shipment_status AS SHIPMENT_STATUS,
    shipments.expected_delivery_date AS EXPECTED_DELIVERY_DATE,
    shipments.revised_delivery_date AS REVISED_DELIVERY_DATE,
    shipments.delay_reason AS DELAY_REASON
)

COMMENT = 'P1 stateless e-commerce order tracking semantic view';
