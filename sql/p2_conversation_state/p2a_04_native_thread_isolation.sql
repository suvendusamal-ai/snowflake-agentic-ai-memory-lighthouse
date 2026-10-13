USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;

SELECT
    R:status::VARCHAR AS STATUS,
    R:metadata:thread_id::NUMBER AS THREAD_ID,
    R:metadata:assistant_message_id::NUMBER AS ASSISTANT_MESSAGE_ID,
    R:metadata:user_message_id::NUMBER AS USER_MESSAGE_ID,
    (
        SELECT LISTAGG(F.VALUE:text::VARCHAR, ' ')
            WITHIN GROUP (ORDER BY F.INDEX)
        FROM TABLE(FLATTEN(INPUT => R:content)) F
        WHERE F.VALUE:type::VARCHAR = 'text'
    ) AS ASSISTANT_ANSWER
FROM (
    SELECT TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'ECOM_AGENT_MEMORY_DB.AGENTS.ECOM_STATELESS_AGENT',
            $$
            {
              "parent_message_id": 0,
              "messages": [
                {
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": "Which order number were we discussing previously? Do not guess. If no earlier order is available in this conversation, say so."
                    }
                  ]
                }
              ]
            }
            $$,
            TRUE
        )
    ) AS R
);