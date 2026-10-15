# M4 — Semantic Memory: Test Evidence

## Scope

Snowflake Agentic AI Memory Lighthouse; unified Streamlit interface, shared ecommerce Cortex Agent, Snowflake-backed customer-scoped semantic preferences. Synthetic demo customers only.

## Evidence index

| Evidence | Observation | Result |
|---|---|---|
| `T1_approved_capture.png` | CUST_001 explicitly approved saving `NOTIFICATION_CHANNEL=EMAIL`; Streamlit returned a memory ID. | PASS |
| `T2_cross_conversation_recall.png` | New conversation: agent recalled EMAIL; trace shows `semantic_memory_count=1`, `previous_messages_sent=0`, status `completed`. | PASS |
| `T3_versioned_update.png` | CUST_001 approved EMAIL → SMS update; Streamlit returned a new memory ID. The active label in this immediate post-submit screenshot still reflects pre-refresh EMAIL. | PASS (write confirmation) |
| `T4_updated_preference_recall.png` | New conversation: active preference SMS (v2); agent recalled SMS; trace shows one semantic memory and no previous messages sent. | PASS |
| `T5_revocation_abstention.png` | After revocation and new conversation, no active preference; agent did not recall revoked value; trace shows zero semantic memories. | PASS |
| `T6_customer_002_capture.png` | CUST_002 explicitly approved saving SMS. | PASS |
| `T6_customer_isolation.png` | Switching to CUST_001: no active preference; trace shows zero semantic memories, empty preference keys, and no previous messages sent. | PASS (application filtering) |

## Backend validation (executed separately)

- Explicit approval required for capture, update, and revocation.
- Capture sequential retry returned the original memory ID; one CREATE audit record observed.
- Update produced versioned history; only the latest active value was retrieved.
- Revocation marked the active record REVOKED and excluded it from retrieval.
- Revocation sequential retry returned the existing memory ID; Snowflake verification showed 2 total versions, 0 active, 1 revoked, latest version 2, and exactly 1 matching REVOKE audit event for the tested operation.

## Regression evidence

Separate Streamlit screenshots in the project conversation confirmed:
- M1: stateless order 7821 lookup, zero prior messages sent.
- M2: follow-up recalled order 7821 with two prior messages sent.
- M3: order 7821 customer-reported interaction retrieved; trace showed four episodic memories and zero prior messages sent.

## Constraints / limitations

- Demo customer IDs are selected in the UI and **not authenticated identities**. Customer-ID filtering is not an authorization boundary; production use requires verified identity, access controls, and isolation testing.
- Sequential idempotency was tested; concurrency-safe exactly-once behavior was **not** established.
- Stored customer statements/preferences are customer-reported, not independently verified operational facts.
- Screenshots evidence UI behavior and agent traces; they do not independently establish all database invariants.
- The immediate post-submit active label may reflect pre-submit state until Streamlit reruns; subsequent new-conversation tests confirmed updated state.

## Reproduction

1. Run Streamlit from project root: `python -m streamlit run .\streamlit\app.py`.
2. Select M4 and synthetic customer CUST_001; explicitly approve and save EMAIL.
3. Start a new conversation; ask for the saved notification channel; inspect trace.
4. Approve update to SMS; start a new conversation; verify SMS (v2).
5. Approve revoke; start a new conversation; verify no active preference.
6. Save SMS for CUST_002; switch to CUST_001; verify no cross-customer recall.
7. Run representative M1–M3 regression tests.

No real customer data should be used in this demonstration.
