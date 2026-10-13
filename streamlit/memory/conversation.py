"""M2: Application-managed conversation context."""

from uuid import uuid4


def new_conversation():
    return {
        "conversation_id": str(uuid4()),
        "messages": []
    }


def add_message(conversation, role, text):
    if role not in ("user", "assistant"):
        raise ValueError("Unsupported conversation role")

    conversation["messages"].append({
        "role": role,
        "content": text
    })


def build_agent_messages(conversation, question):
    """Build a DATA_AGENT_RUN request from conversation history."""

    messages = []

    for message in conversation["messages"]:
        messages.append({
            "role": message["role"],
            "content": [
                {
                    "type": "text",
                    "text": message["content"]
                }
            ]
        })

    messages.append({
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": question
            }
        ]
    })

    return messages