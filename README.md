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
