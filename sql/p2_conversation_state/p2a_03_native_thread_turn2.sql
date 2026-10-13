USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;

SELECT
    R:status::VARCHAR AS STATUS,
    R:metadata:thread_id::NUMBER AS THREAD_ID,
    R:metadata:assistant_message_id::NUMBER AS ASSISTANT_MESSAGE_ID,
    R:metadata:user_message_id::NUMBER AS USER_MESSAGE_ID,
    LEFT(TO_VARCHAR(R:content), 4000) AS RESPONSE_CONTENT
FROM (
    SELECT TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'ECOM_AGENT_MEMORY_DB.AGENTS.ECOM_STATELESS_AGENT',
            $$
            {
              "thread_id": 89390720,
              "parent_message_id": 22884004381,
              "messages": [
                {
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": "Who is the carrier for that order? Verify against shipment records."
                    }
                  ]
                }
              ]
            }
            $$,
            FALSE
        )
    ) AS R
);