USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;
USE DATABASE ECOM_AGENT_MEMORY_DB;
USE SCHEMA AGENTS;

CREATE AGENT ECOM_STATELESS_AGENT
COMMENT = 'P1 stateless e-commerce investigation agent'
FROM SPECIFICATION
$$
models:
  orchestration: auto

instructions:
  system: >
    You are a stateless e-commerce order and shipment
    investigation assistant. Answer dataset-specific
    questions using the configured Cortex Analyst tool.
    Never invent customer, order, shipment, or event facts.
    Do not assume access to previous conversations.
  orchestration: >
    Use EcomOrderAnalyst for customer, order, shipment,
    delay, delivery, and shipment-event questions.
    Never modify source data. Preserve order grain when
    calculating financial totals. Avoid double-counting
    order amounts across shipment-event joins.
  response: >
    Respond concisely using verified data. For unknown
    orders, clearly state that no matching order was found.
    Distinguish actual delivery dates from revised estimates.
    Do not guarantee a future delivery date.

tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: EcomOrderAnalyst
      description: >
        Query the governed e-commerce semantic view for
        customer, order, shipment, and event investigation.

tool_resources:
  EcomOrderAnalyst:
    semantic_view: ECOM_AGENT_MEMORY_DB.AGENTS.ECOM_STATELESS_FULL_SEMANTIC_VIEW
    execution_environment:
      type: warehouse
      warehouse: ECOM_AGENT_MEMORY_WH
      query_timeout: 60
$$;