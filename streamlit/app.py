import streamlit as st
from agent_client import ask_agent, AGENT

st.set_page_config(
    page_title="Snowflake Agent Memory Lighthouse",
    page_icon="🧠",
    layout="wide"
)

st.title("Snowflake Agentic AI Memory Lighthouse")
st.caption("M1 — Stateless Cortex Agent")

with st.sidebar:
    st.header("Agent Configuration")
    st.write("**Memory mode:** Stateless")
    st.write("**Agent:** ECOM_STATELESS_AGENT")
    st.write("**Connection:** CoCo_Oct")
    st.write("**Role:** ECOM_AGENT_MEMORY_OWNER")
    st.write("**Memory mechanism:** None")
    st.write("**Conversation continuity:** Disabled")

    if st.button("New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_trace = None
        st.rerun()

    st.divider()
    st.info(
        "Previous messages are displayed in Streamlit, "
        "but are never sent to the Cortex Agent."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_trace" not in st.session_state:
    st.session_state.last_trace = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about an ecommerce order...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Cortex Agent investigating..."):
            try:
                response = ask_agent(question)

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

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

                tools = [
                    item["tool_use"].get("name")
                    for item in response.get("content", [])
                    if item.get("type") == "tool_use"
                ]

                st.session_state.last_trace = {
                    "question": question,
                    "agent": AGENT,
                    "messages_sent": 1,
                    "previous_messages_sent": 0,
                    "thread_id": None,
                    "tools": tools,
                    "status": response.get("status", "unknown")
                }

            except Exception as exc:
                st.error("Agent invocation failed.")
                st.session_state.last_trace = {
                    "question": question,
                    "status": "error",
                    "error_type": type(exc).__name__
                }

with st.expander("Technical Trace — Last Invocation"):
    if st.session_state.last_trace:
        st.json(st.session_state.last_trace)
    else:
        st.caption("No agent invocation yet.")