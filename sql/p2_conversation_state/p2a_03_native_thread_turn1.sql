USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;

SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'ECOM_AGENT_MEMORY_DB.AGENTS.ECOM_STATELESS_AGENT',
            $$
            {
              "messages": [
                {
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": "Why is Order 7821 delayed? Use the available order and shipment records."
                    }
                  ]
                }
              ],
              "parent_message_id": 0
            }
            $$,
            TRUE
        )
    ) AS AGENT_RESPONSE;