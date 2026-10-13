import json
import snowflake.connector

AGENT = "ECOM_AGENT_MEMORY_DB.AGENTS.ECOM_STATELESS_AGENT"


def ask_agent(question):
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": question}]
            }
        ]
    }

    conn = snowflake.connector.connect(
        connection_name="CoCo_Oct",
        role="ECOM_AGENT_MEMORY_OWNER",
        warehouse="ECOM_AGENT_MEMORY_WH"
    )

    try:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(%s, %s)",
                (AGENT, json.dumps(payload))
            )
            result = cursor.fetchone()[0]
            return json.loads(result) if isinstance(result, str) else result
        finally:
            cursor.close()
    finally:
        conn.close()


if __name__ == "__main__":
    response = ask_agent("Where is order 7821?")
    print(json.dumps(response, indent=2, ensure_ascii=True))