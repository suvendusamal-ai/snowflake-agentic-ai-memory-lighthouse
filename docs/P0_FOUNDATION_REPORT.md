# P0 — Snowflake Agentic AI Memory Lighthouse

## 1. Objective

Establish a reproducible Snowflake foundation for demonstrating
the transition from stateless AI agents to governed persistent memory.

P0 provides operational ground truth, memory schemas, procedural
metadata schemas, evaluation schemas, and deterministic test evidence.

No Cortex Agent or memory processing workflow is implemented in P0.

## 2. Snowflake Environment

| Component | Object |
|---|---|
| Database | ECOM_AGENT_MEMORY_DB |
| Warehouse | ECOM_AGENT_MEMORY_WH |
| Owner Role | ECOM_AGENT_MEMORY_OWNER |
| Operational Schema | RAW |
| Memory Schema | MEMORY |
| Procedural Schema | PROCEDURES |
| Evaluation Schema | EVALUATION |
| Reserved Agent Schema | AGENTS |

## 3. Data Architecture

RAW.CUSTOMERS
    |
    | CUSTOMER_ID
    v
RAW.ORDERS
    |
    | ORDER_ID
    v
RAW.SHIPMENTS
    |
    | SHIPMENT_ID
    v
RAW.SHIPMENT_EVENTS

Memory infrastructure:

- MEMORY.CONVERSATION_METADATA
- MEMORY.SESSION_STATE
- MEMORY.EPISODIC_MEMORY
- MEMORY.SEMANTIC_MEMORY
- MEMORY.MEMORY_AUDIT

Procedural infrastructure:

- PROCEDURES.PROCEDURE_CATALOG
- PROCEDURES.PROCEDURE_VERSIONS

Evaluation infrastructure:

- EVALUATION.TEST_CASES
- EVALUATION.TEST_RESULTS

## 4. Validated Dataset

| Table | Records |
|---|---:|
| RAW.CUSTOMERS | 100 |
| RAW.ORDERS | 500 |
| RAW.SHIPMENTS | 500 |
| RAW.SHIPMENT_EVENTS | 2000 |
| Total | 3100 |

All nine memory, procedural and evaluation tables remain empty.

## 5. Primary Lighthouse Scenario

Customer: CUST_001 — James
Order: 7821
Amount: INR 2500
Carrier: BlueDart
Shipment: SHP_7821
Shipment Status: IN_TRANSIT
Original ETA: 2026-10-08
Revised ETA: 2026-10-12
Delay Reason: WEATHER_DELAY
ETA Difference: 4 calendar days

Tracking events:

1. 2026-10-05 09:00 — ORDER_CONFIRMED
2. 2026-10-06 11:00 — DISPATCHED
3. 2026-10-08 08:30 — WEATHER_DELAY
4. 2026-10-09 10:00 — ETA_REVISED

At the fixed reference time 2026-10-11 12:00,
the shipment meets the 48-hour escalation threshold.

Snowflake DATEDIFF('hour') returns 76 hour boundaries.
The precise elapsed duration is 75 hours 30 minutes.

## 6. Validation Evidence

| Milestone | Evidence | Result |
|---|---|---|
| P0-E1 | p0e_02_customer_validation.txt | PASS |
| P0-E2 | p0e_04_order_validation.txt | PASS |
| P0-E3 | p0e_06_shipment_validation.txt | PASS |
| P0-E4 | p0e_08_event_validation.txt | PASS |
| P0-F1 | p0f_01_delayed_order_scenario.txt | PASS |
| P0-F2 | p0f_02_customer_isolation.txt | PASS |
| P0-F3 | p0f_03_operational_exceptions.txt | PASS |
| P0-G1 | p0g_01_foundation_readiness.txt | PASS |

Evidence files are stored under evidence/p0/.

## 7. Governance Boundaries

P0 establishes data ownership relationships and query-level
customer filtering.

P0 does not yet implement:

- Enforced customer isolation for agent identities
- Memory access authorization
- Memory expiration and retention enforcement
- Automated memory promotion or consolidation
- Agent-aware masking
- Procedural memory approval workflows
- Agent evaluations or memory quality scoring
- Cortex Agent execution

Snowflake standard-table primary and foreign key constraints
are informational. Data integrity is validated through SQL tests.

## 8. P1 Handoff

The following prerequisites are available:

- Deterministic operational dataset
- Customer and order ownership relationships
- Shipment event evidence
- Conversation and session-state schemas
- Episodic and semantic memory schemas
- Memory audit schema
- Procedural and evaluation schemas
- Validated business scenarios

P1 implementation must establish its own runtime,
authorization, behavioral and evidence gates.

## 9. Reproducibility

SQL scripts are maintained under sql/p0_foundation/.

Operational seed scripts use deterministic values and
existence checks to avoid duplicate inserts.

Execution requires an appropriately authorized Snowflake
connection and the ECOM_AGENT_MEMORY_OWNER role.

This project uses synthetic customer information only.