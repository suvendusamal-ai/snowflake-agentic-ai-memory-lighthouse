import streamlit as st

from agent_client import ask_agent, AGENT
from memory.conversation import (
    new_conversation,
    add_message,
    build_agent_messages
)

st.set_page_config(
    page_title="Snowflake Agent Memory Lighthouse",
    page_icon="🧠",
    layout="wide"
)

st.title("Snowflake Agentic AI Memory Lighthouse")

MODES = ["M1 — Stateless", "M2 — Conversation Memory"]

if "memory_mode" not in st.session_state:
    st.session_state.memory_mode = MODES[0]

if "conversations" not in st.session_state:
    st.session_state.conversations = {
        mode: new_conversation() for mode in MODES
    }

if "traces" not in st.session_state:
    st.session_state.traces = {
        mode: None for mode in MODES
    }

with st.sidebar:
    st.header("Agent Configuration")

    mode = st.selectbox(
        "Memory Mode",
        MODES,
        key="memory_mode"
    )

    conversation = st.session_state.conversations[mode]

    st.write("**Agent:** ECOM_STATELESS_AGENT")
    st.write("**Connection:** CoCo_Oct")
    st.write("**Role:** ECOM_AGENT_MEMORY_OWNER")
    st.write("**Conversation ID:**", conversation["conversation_id"])

    if mode == MODES[0]:
        st.write("**Memory:** Stateless")
        st.caption("Previous messages are displayed but never sent.")
    else:
        st.write("**Memory:** Application-managed conversation history")
        st.caption("Previous turns are supplied to Cortex Agent.")

    if st.button("New Conversation", use_container_width=True):
        st.session_state.conversations[mode] = new_conversation()
        st.session_state.traces[mode] = None
        st.rerun()

conversation = st.session_state.conversations[mode]

st.caption(mode)

for message in conversation["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about an ecommerce order...")

if question:
    previous_count = len(conversation["messages"])

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Cortex Agent investigating..."):
            try:
                if mode == MODES[0]:
                    response = ask_agent(question)
                    messages_sent = 1
                    mechanism = "Stateless"
                else:
                    agent_messages = build_agent_messages(
                        conversation, question
                    )
                    response = ask_agent(
                        question,
                        messages=agent_messages
                    )
                    messages_sent = len(agent_messages)
                    mechanism = "Explicit conversation history"

                answer_parts = [
                    item["text"]
                    for item in response.get("content", [])
                    if item.get("type") == "text"
                    and isinstance(item.get("text"), str)
                ]

                answer = "\n\n".join(answer_parts)

                if not answer:
                    answer = "Agent returned no text response."

                st.markdown(answer)

                add_message(conversation, "user", question)
                add_message(conversation, "assistant", answer)

                tools = [
                    item["tool_use"].get("name")
                    for item in response.get("content", [])
                    if item.get("type") == "tool_use"
                ]

                st.session_state.traces[mode] = {
                    "memory_mode": mode,
                    "conversation_id": conversation["conversation_id"],
                    "question": question,
                    "previous_messages_available": previous_count,
                    "previous_messages_sent": (
                        0 if mode == MODES[0] else previous_count
                    ),
                    "messages_sent": messages_sent,
                    "memory_mechanism": mechanism,
                    "agent": AGENT,
                    "tools": tools,
                    "status": response.get("status", "unknown")
                }

            except Exception as exc:
                st.error("Agent invocation failed.")
                st.session_state.traces[mode] = {
                    "memory_mode": mode,
                    "conversation_id": conversation["conversation_id"],
                    "question": question,
                    "status": "error",
                    "error_type": type(exc).__name__
                }

with st.expander("Technical Trace — Last Invocation"):
    trace = st.session_state.traces[mode]

    if trace:
        st.json(trace)
    else:
        st.caption("No agent invocation yet.")