# Snowflake Agentic AI Memory Lighthouse

## Objective
Demonstrate the progression from stateless Snowflake Cortex
Agents to governed enterprise long-term agent memory.

## Technology
- Snowflake Cortex Agents
- Snowflake SQL
- Snowflake CLI
- Python
- Streamlit
- Git

## Implementation Roadmap
- P0: Environment and synthetic e-commerce foundation
- P1: Stateless agent
- P2: Conversation history and session state
- P3: Episodic memory
- P4: Semantic memory
- P5: Procedural memory
- P6: Governance and lifecycle
- P7: Enterprise evaluation
- P8: Publication

## Environment
Connection: CoCo_Oct
Database: ECOM_AGENT_MEMORY_DB
Warehouse: ECOM_AGENT_MEMORY_WH

## Current Status
P0: COMPLETE - Foundation validated

## Security
Only synthetic data is permitted.
Credentials and private keys must never be committed.


## P1 - Stateless Cortex Agent

Status: FUNCTIONALLY VALIDATED

The P1 implementation establishes a Snowflake Cortex Agent
using Cortex Analyst and a governed four-entity semantic view.

Validated capabilities:

- Order and shipment investigation
- Grounded responses
- Unknown-order abstention
- Independent-request statelessness

Persistent agent memory is intentionally excluded from P1.

Documentation:
[Implementation Report](docs/P1_STATELESS_AGENT_REPORT.md)

Evidence:
[Evidence Manifest](evidence/p1_stateless_agent/P1_EVIDENCE_MANIFEST.md)

Next milestone: P2 - Conversation State.

## M1 - Stateless Cortex Agent with Streamlit

### Business Scenario
An ecommerce customer asks about an order and then asks
follow-up questions. M1 demonstrates that a stateless agent
cannot automatically resolve references to earlier messages.

### Architecture
Streamlit Chat UI
  -> Python Agent Client
  -> Snowflake Cortex Agent
  -> Cortex Analyst
  -> Semantic View
  -> Ecommerce Data

### Snowflake Components
- Agent: ECOM_AGENT_MEMORY_DB.AGENTS.ECOM_STATELESS_AGENT
- Tool: EcomOrderAnalyst
- Semantic View: ECOM_STATELESS_FULL_SEMANTIC_VIEW
- Warehouse: ECOM_AGENT_MEMORY_WH

### Run Locally
Prerequisites: Python, Snowflake Connector, Streamlit,
and a configured Snowflake connection named CoCo_Oct.

From the repository root:

    python -m streamlit run .\streamlit\app.py

### Stateless Memory Demonstration

| Test | Question | Observed Behavior | Result |
|---|---|---|---|
| T1 | Where is order 7821? | Grounded shipment response | PASS |
| T2 | Who is delivering it? | Requested order clarification | PASS |
| T3 | Who is delivering order 7821? | Identified BlueDart | PASS |
| T4 | New conversation: What is its ETA? | No inherited order context | PASS |

### Memory Mechanism
- Streamlit retains chat history for display.
- Each Cortex Agent request contains only the current question.
- Previous conversation messages are not transmitted.
- No conversation thread identifier is supplied.
- No persistent agent memory is retrieved.

### Architectural Takeaway
Chat history displayed in a user interface is not equivalent
to agent memory. Stateless behavior is controlled by the
application's request construction.

### Evidence
See evidence/m1_stateless/ for demonstration screenshots.

### Limitations
- No conversational continuity.
- Ambiguous follow-up questions require clarification.
- No persistent session, episodic, or semantic memory.
- Demonstration uses synthetic ecommerce data.
