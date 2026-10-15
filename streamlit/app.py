import re
from uuid import uuid4
import streamlit as st

from agent_client import ask_agent, AGENT
from memory.episodic import (
    register_episodic_conversation,
    save_episodic_memory,
    retrieve_episodic_memories,
    build_episodic_agent_messages,
)
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

MODES = ["M1 — Stateless", "M2 — Conversation Memory", "M3 — Episodic Memory"]

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

    if mode == MODES[2]:
        customer_id = st.selectbox(
            "Demo Customer",
            ["CUST_001", "CUST_002", "CUST_003", "CUST_004", "CUST_005"],
            key="m3_customer_id"
        )
        st.caption("Synthetic customer identity — demonstration only.")

        if st.session_state.get("m3_conversation_customer") != customer_id:
            st.session_state.conversations[mode] = new_conversation()
            st.session_state.traces[mode] = None
            st.session_state.m3_conversation_customer = customer_id

        conversation = st.session_state.conversations[mode]
        register_episodic_conversation(
            customer_id,
            conversation["conversation_id"]
        )

    st.write("**Agent:** ECOM_STATELESS_AGENT")
    st.write("**Connection:** CoCo_Oct")
    st.write("**Role:** ECOM_AGENT_MEMORY_OWNER")
    st.write("**Conversation ID:**", conversation["conversation_id"])

    if mode == MODES[0]:
        st.write("**Memory:** Stateless")
        st.caption("Previous messages are displayed but never sent.")
    elif mode == MODES[1]:
        st.write("**Memory:** Application-managed conversation history")
        st.caption("Previous turns are supplied to Cortex Agent.")
    else:
        st.write("**Memory:** Persistent episodic memory")
        st.caption("Approved historical events are retrieved from Snowflake.")

    if st.button("New Conversation", use_container_width=True):
        new_chat = new_conversation()

        if mode == MODES[2]:
            register_episodic_conversation(
                customer_id,
                new_chat["conversation_id"]
            )

        st.session_state.conversations[mode] = new_chat
        st.session_state.traces[mode] = None
        st.rerun()

conversation = st.session_state.conversations[mode]

st.caption(mode)

for message in conversation["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if mode == MODES[2]:
    with st.expander("Save a Customer-Reported Interaction"):
        st.caption(
            "Only explicitly approved reports are stored. "
            "Saved reports remain unverified historical context."
        )

        with st.form("m3_capture_form", clear_on_submit=True):
            capture_order_id = st.text_input(
                "Order ID",
                placeholder="7821",
            )

            capture_text = st.text_area(
                "What did you report?",
                placeholder=(
                    "I contacted support about a delayed "
                    "delivery for order 7821."
                ),
            )

            capture_approved = st.checkbox(
                "I explicitly approve saving this report "
                "as episodic memory."
            )

            capture_submitted = st.form_submit_button(
                "Save Approved Memory"
            )

        if capture_submitted:
            if not capture_approved:
                st.warning("Explicit approval is required.")
            elif not capture_order_id.strip() or not capture_text.strip():
                st.warning("Order ID and report are required.")
            elif not capture_order_id.strip().isdigit():
                st.warning("Order ID must contain digits only.")
            else:
                try:
                    capture_id = str(uuid4())

                    memory_id = save_episodic_memory(
                        customer_id=customer_id,
                        conversation_id=conversation["conversation_id"],
                        order_id=capture_order_id.strip(),
                        memory_text=capture_text.strip(),
                        source_reference=f"M3_STREAMLIT_{capture_id}",
                        capture_id=capture_id,
                        approved=True,
                    )

                    st.success(
                        f"Approved memory saved. ID: {memory_id}"
                    )

                except Exception as exc:
                    st.error(
                        f"Memory capture failed: {type(exc).__name__}"
                    )

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
                elif mode == MODES[1]:
                    agent_messages = build_agent_messages(
                        conversation, question
                    )
                    response = ask_agent(
                        question,
                        messages=agent_messages
                    )
                    messages_sent = len(agent_messages)
                    mechanism = "Explicit conversation history"
                else:
                    match = re.search(
                        r"\border\s*#?\s*(\d+)\b",
                        question,
                        flags=re.IGNORECASE,
                    )
                    order_id = match.group(1) if match else None

                    memories = (
                        retrieve_episodic_memories(customer_id, order_id)
                        if order_id else []
                    )

                    agent_messages = build_episodic_agent_messages(
                        question, memories
                    )

                    response = ask_agent(
                        question,
                        messages=agent_messages
                    )
                    messages_sent = len(agent_messages)
                    mechanism = "Persistent episodic memory"

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
                        previous_count if mode == MODES[1] else 0
                    ),
                    "messages_sent": messages_sent,
                    "memory_mechanism": mechanism,
                    "episodic_memory_count": (
                        len(memories) if mode == MODES[2] else 0
                    ),
                    "episodic_order_id": (
                        order_id if mode == MODES[2] else None
                    ),
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