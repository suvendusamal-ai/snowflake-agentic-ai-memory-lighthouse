USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;

SELECT TRY_PARSE_JSON(
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
                  "text": "Why is Order 7821 delayed?"
                }
              ]
            },
            {
              "role": "assistant",
              "content": [
                {
                  "type": "text",
                  "text": "We were discussing Order 7821 and its shipment delay."
                }
              ]
            },
            {
              "role": "user",
              "content": [
                {
                  "type": "text",
                  "text": "Who is the carrier for that order? Verify using the available records."
                }
              ]
            }
          ]
        }
        $$
    )
) AS AGENT_RESPONSE;