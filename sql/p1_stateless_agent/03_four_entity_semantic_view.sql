USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;
USE DATABASE ECOM_AGENT_MEMORY_DB;
USE SCHEMA AGENTS;

CREATE SEMANTIC VIEW IF NOT EXISTS ECOM_STATELESS_FULL_SEMANTIC_VIEW

TABLES (
    customers AS ECOM_AGENT_MEMORY_DB.RAW.CUSTOMERS
        PRIMARY KEY (CUSTOMER_ID),

    orders AS ECOM_AGENT_MEMORY_DB.RAW.ORDERS
        PRIMARY KEY (ORDER_ID),

    shipments AS ECOM_AGENT_MEMORY_DB.RAW.SHIPMENTS
        PRIMARY KEY (SHIPMENT_ID),

    shipment_events AS ECOM_AGENT_MEMORY_DB.RAW.SHIPMENT_EVENTS
        PRIMARY KEY (EVENT_ID)
)

RELATIONSHIPS (
    orders_to_customers AS
        orders (CUSTOMER_ID)
        REFERENCES customers (CUSTOMER_ID),

    shipments_to_orders AS
        shipments (ORDER_ID)
        REFERENCES orders (ORDER_ID),

    events_to_shipments AS
        shipment_events (SHIPMENT_ID)
        REFERENCES shipments (SHIPMENT_ID)
)

FACTS (
    orders.order_amount AS ORDER_AMOUNT
        COMMENT = 'Order monetary value at order grain',

    orders.order_date AS ORDER_DATE
)

DIMENSIONS (
    customers.customer_id AS CUSTOMER_ID,
    customers.customer_name AS CUSTOMER_NAME,
    customers.city AS CITY,
    customers.customer_status AS CUSTOMER_STATUS,

    orders.order_id AS ORDER_ID,
    orders.order_status AS ORDER_STATUS,
    orders.currency AS CURRENCY,
    orders.promised_delivery_date AS PROMISED_DELIVERY_DATE,

    shipments.shipment_id AS SHIPMENT_ID,
    shipments.carrier_name AS CARRIER_NAME,
    shipments.shipment_status AS SHIPMENT_STATUS,
    shipments.expected_delivery_date AS EXPECTED_DELIVERY_DATE,
    shipments.revised_delivery_date AS REVISED_DELIVERY_DATE,
    shipments.delay_reason AS DELAY_REASON,

    shipment_events.event_id AS EVENT_ID,
    shipment_events.event_timestamp AS EVENT_TIMESTAMP,
    shipment_events.event_type AS EVENT_TYPE,
    shipment_events.event_location AS EVENT_LOCATION,
    shipment_events.event_description AS EVENT_DESCRIPTION
)

COMMENT = 'P1 four-entity stateless order and shipment investigation model';