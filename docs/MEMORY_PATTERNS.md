# Five agent-memory patterns: a Snowflake e-commerce lighthouse

> **Architecture boundary:** M1–M5 are **application-managed patterns**, not five native Snowflake Cortex Agent memory products. All five use the same deployed Cortex Agent, with a different request context prepared by Python.

| Pattern | Business question | Actual source | Request context | Lifetime | Demonstrated control |
|---|---|---|---|---|---|
| M1 Stateless | Where is order 7821? | Current question | One user message | Request | No prior chat sent |
| M2 Conversation | Who is delivering it? | Streamlit session state | Prior turns plus question | Active session | Mode/conversation isolation |
| M3 Episodic | Did I report this delay? | `MEMORY.EPISODIC_MEMORY` | Customer/order-scoped, approved historical report | Durable | Approval, audit, active/expiry filtering |
| M4 Semantic | What notification channel do I prefer? | `MEMORY.SEMANTIC_MEMORY` | Current active preference | Durable until superseded/revoked/expired | Approval, versioning, revocation, audit |
| M5 Procedural | Should this delayed order be escalated? | `PROCEDURES.PROCEDURE_CATALOG` + `PROCEDURE_VERSIONS` | Approved/effective playbook | Durable/versioned | Approval filtering; independent SQL policy check |

## The distinction most teams miss

- **M2** remembers what was said **in this session**.
- **M3** recalls **a historical event** across conversations. In this demo it is a *customer-reported, unverified* complaint, not a confirmed operational event.
- **M4** recalls **the currently approved structured fact** across conversations, e.g. `NOTIFICATION_CHANNEL=SMS (v2)` after superseding EMAIL (v1). Revocation excludes the fact from future retrieval.
- **M5** retrieves **how to investigate**. It is an approved business playbook, not a learned agent skill or permission to issue refunds.

## Runtime sequence

1. User selects M1–M5 in `streamlit/app.py`.
2. Python builds context: no history (M1), session turns (M2), SQL-retrieved historical report (M3), active preference (M4), or approved playbook (M5).
3. `streamlit/agent_client.py` calls `SNOWFLAKE.CORTEX.DATA_AGENT_RUN` for `ECOM_AGENT_MEMORY_DB.AGENTS.ECOM_STATELESS_AGENT` (the *existing physical name*; **Shared Cortex Agent** is its logical diagram label).
4. The agent can invoke Cortex Analyst over `ECOM_STATELESS_FULL_SEMANTIC_VIEW` and synthetic operational data.
5. For M5 only, `evaluate_delayed_order()` independently reads the order/shipment/tracking data and calculates eligibility using the approved procedure threshold. Streamlit shows this decision **separately** from the generated agent answer.

## M5 decision contract

- `ELIGIBLE` only when revised ETA is missed **and** tracking inactivity meets the active approved threshold.
- `NOT_ELIGIBLE` when already delivered or both conditions are not satisfied.
- `UNDETERMINED` when the order is missing, multiple shipment records need assessment, or required evidence is absent.
- The previously demonstrated active v1 uses a **48-hour** tracking inactivity threshold. Draft v2 uses **24 hours** and must not be described as active unless its approval/effective state is independently rechecked.
- The evaluator is application-side SQL, **not** a Snowflake privilege-enforcement test and **not** an agent-issued operational action.

## Governance and honest limitations

- M3/M4 memory capture requires explicit demo approval and uses audit records; retrieved customer reports are not independently verified.
- Demo customer IDs are selectable in the UI. **Filtering is not authentication or tenant isolation**; production requires verified identity, authorization, and isolation tests.
- Sequential retry/idempotency evidence does not establish concurrency-safe exactly-once behavior.
- M2 is not durable across app restarts. M3 requires an explicit order ID in the current question; it is not similarity-based retrieval. M4 is structured key/value retrieval, not vector RAG.
- No demonstration establishes database-enforced read-only access, Restricted Session Scope, full telemetry, or automatic memory extraction from free-form chat.
- No real customer data should be used.

## Demo prompts

| Mode | Action / prompt | Expected illustration |
|---|---|---|
| M1 | `Where is order 7821?` then `Who is delivering it?` | First grounded; second needs clarification |
| M2 | Same two questions in one conversation | Follow-up resolves order 7821 |
| M3 | Approve a complaint for order 7821; start new conversation; ask `What did I report about order 7821?` | Historical report retrieved as unverified context |
| M4 | Save EMAIL, update to SMS, then revoke, starting a new conversation between steps | Active v1 → active v2 → no active preference |
| M5 | `Investigate delayed order 7821 and assess escalation` | Approved playbook + separate SQL eligibility result |

See `architecture/L0_linkedin_reference.png` and `architecture/L1_technical_reference.png`.
