# P2-B — Conversation State Contract

**Project:** Snowflake Agentic AI Memory Lighthouse  
**Milestone:** P2-B-01D  
**Status:** PROPOSED — awaiting architectural approval; no Snowflake DDL executed  
**Baseline:** P0/P1/P2-A complete; native Cortex Agent thread continuity demonstrated.

## 1. Purpose and scope

Define the application-managed contract for a conversation that uses Snowflake Cortex Agent native thread state. The contract is the basis for P2-B-02 through P2-B-06. It does **not** claim that Snowflake native threads provide application ownership enforcement, transactional exactly-once execution, or guaranteed retention.

In scope: identity, ownership, thread mapping, lifecycle, latest committed assistant message pointer, authorization, idempotency and failure outcomes, concurrency expectations, minimal audit evidence. Out of scope: full transcript replication, episodic/semantic/procedural memory implementation (P3–P5), UI, and exhaustive testing.

## 2. Verified baseline versus design proposals

### Verified from local discovery
- `ECOM_AGENT_MEMORY_DB.MEMORY.CONVERSATION_METADATA` exists with `CONVERSATION_ID VARCHAR(64) NOT NULL`, `CUSTOMER_ID VARCHAR(30) NOT NULL`, `AGENT_ID VARCHAR(100)`, `CHANNEL`, `CONVERSATION_STATUS DEFAULT 'ACTIVE'`, `STARTED_AT`, `ENDED_AT`, `METADATA VARIANT`, `CREATED_AT`, `UPDATED_AT`.
- `MEMORY.SESSION_STATE` exists with `STATE_VERSION`, which is **not** a conversation-level version.
- `MEMORY.MEMORY_AUDIT` exists with actor, operation, status, and before/after metadata.
- Primary and foreign keys are declared; on Snowflake standard tables, such constraints are generally informational rather than enforcement mechanisms.
- P2-A validated native thread continuation, inspection, and behavioral isolation. Native thread authorization, retention and failure/retry guarantees have not been established.

### Proposed design decisions (not yet implemented)
- Extend the existing `CONVERSATION_METADATA` table rather than create a second registry.
- Treat the authenticated application principal (`OWNER_ID`) separately from business `CUSTOMER_ID`.
- Maintain native thread/message identifiers as server-side internal references.
- Route all state mutations through a trusted conversation service with explicit authorization and conflict handling.

## 3. Logical record contract

| Field | Logical type | Requirement / invariant |
|---|---|---|
| `CONVERSATION_ID` | VARCHAR(64) | Required, immutable application-generated opaque ID; uniqueness must be enforced by the write path, not assumed from standard-table PK |
| `CUSTOMER_ID` | VARCHAR(30) | Required legacy business customer reference; access to customer data requires separate entitlement checks |
| `OWNER_ID` | VARCHAR(128) | Required authenticated principal; derived from verified identity, never accepted as authoritative from a client payload |
| `AGENT_ID` | VARCHAR(100) | Existing optional legacy identifier, retained for compatibility |
| `AGENT_FQN` | VARCHAR(255) | Required allowlisted fully qualified Cortex Agent identifier |
| `THREAD_ID` | NUMBER(38,0) nullable | Native thread identifier; assigned only after verified association; never an authorization token |
| `LAST_ASSISTANT_MESSAGE_ID` | NUMBER(38,0) nullable | Last assistant message confirmed by the application as successfully committed |
| `CONVERSATION_STATUS` | VARCHAR(30) | Required logical lifecycle state; see Section 4 |
| `VERSION` | NUMBER(38,0) | Required nonnegative application-level revision, advanced on successful state mutation; alone does not ensure safe concurrency |
| `EXPIRES_AT` | TIMESTAMP_NTZ nullable | Optional application expiry; not a claim about native thread retention or deletion |
| `CHANNEL` | VARCHAR(30) nullable | Existing application channel |
| `STARTED_AT`, `ENDED_AT` | TIMESTAMP_NTZ | Existing lifecycle timestamps; `ENDED_AT` set for terminal state |
| `METADATA` | VARIANT nullable | Existing extension field; non-sensitive diagnostics only, never secrets or unbounded transcript copies |
| `CREATED_AT`, `UPDATED_AT` | TIMESTAMP_NTZ | Creation and last committed update timestamps |

Physical column additions, defaults, and migration/backfill strategy are **deferred** until P2-B-03. A nullable `OWNER_ID` during a migration must never mean that an unowned legacy record is accessible; access must fail closed until ownership is explicitly established.

## 4. Lifecycle contract

**Logical states:** `CREATING`, `ACTIVE`, `CLOSED`, `EXPIRED`, `FAILED`.

| From | Event | To | Condition |
|---|---|---|---|
| No record | Authorized create | `CREATING` | Valid principal, agent allowlist, and customer entitlement |
| `CREATING` | Thread association confirmed | `ACTIVE` | Thread mapping persisted successfully |
| `CREATING` | Definitive unrecoverable setup failure | `FAILED` | Evidence establishes failure, not merely a timeout |
| `ACTIVE` | Authorized continuation committed | `ACTIVE` | Response and pointer validated; version advances |
| `ACTIVE` | Authorized close | `CLOSED` | Subsequent continuations denied |
| `CREATING` / `ACTIVE` | Application expiry | `EXPIRED` | Expiry enforced by service; physical cleanup is separate |
| `ACTIVE` | Definitive unrecoverable state corruption | `FAILED` | Explicitly audited and operator-actionable |

Terminal states (`CLOSED`, `EXPIRED`, `FAILED`) do not accept continuation. Any recovery/reopen behavior requires a separate, reviewed contract; none is assumed in P2-B.

**Uncertain outcomes:** A native agent-call timeout, a lost response, or a failed registry update after an agent response is **not** proof of failure. Keep the conversation in a recoverable/blocked operation condition and reconcile before allowing a new continuation; do not blindly replay the same call.

## 5. API-level operation contract

### Create conversation
Input: authenticated identity context, authorized `CUSTOMER_ID`, allowlisted `AGENT_FQN`, optional channel, request idempotency key. Output: opaque `CONVERSATION_ID`, logical status, and only public metadata. The service associates a native thread before making the conversation available as `ACTIVE`. The exact native thread creation/association behavior is to be verified in P2-B-04.

### Continue conversation
Input: authenticated identity context, `CONVERSATION_ID`, user message, idempotency key, optional expected revision. The service loads the registry record, verifies owner and customer entitlements, checks status/expiry, resolves server-side native thread and parent assistant pointer, and invokes the agent. It validates the returned thread and assistant message IDs before committing a new pointer and version. Do not return raw internal thread IDs to untrusted clients.

### Close conversation
Input: authenticated identity context, `CONVERSATION_ID`, idempotency key. Owner check and valid transition required. Close updates the application lifecycle; it does not imply deletion of Snowflake-native thread messages.

### Read conversation metadata
Input: authenticated identity context, `CONVERSATION_ID`. Output: authorized public metadata only. Native transcript retrieval, if exposed later, requires independent authorization and safe content handling.

## 6. Identity, authorization, and isolation

1. Authenticate the caller outside the agent prompt; derive `OWNER_ID` from trusted identity claims.
2. Verify conversation ownership **before** native thread lookup, message inspection, or agent invocation.
3. Verify the caller may access the associated business customer; ownership alone does not grant arbitrary customer-data access.
4. Use an allowlisted agent; reject caller-supplied agent FQNs that are not authorized.
5. Deny missing, malformed, unowned, expired, closed, and failed conversations without disclosing existence across principals.
6. App-layer checks are a **proposed control**, not proven Snowflake database-level isolation. P2-B-02 must document actual role/service boundaries and execute a cross-user negative test.
7. The agent's business-data permissions must be scoped separately from conversation registry permissions.

## 7. Concurrency, idempotency, and recovery

- `VERSION` is a logical compare-and-update token, **not** sufficient by itself to claim atomic compare-and-swap on a Snowflake standard table.
- Require a concrete serialized or otherwise proven atomic write mechanism before enabling concurrent continuations. Candidate mechanisms and Snowflake transaction behavior are assessed in P2-B-05; no mechanism is claimed validated now.
- Track an application-generated operation/idempotency key and operation state (`PENDING`, `SUCCEEDED`, `FAILED`, `UNKNOWN`) in a dedicated operation ledger **if testing shows it is needed**. Avoid hiding operational state only in unstructured `METADATA`.
- Duplicate request keys must not trigger an additional native agent invocation after a committed success; identical keys with different request payloads must be rejected.
- For an uncertain agent outcome, block conflicting continuation and reconcile native state/registry pointer where supported; escalate when reconciliation cannot establish a safe parent pointer.
- If an agent response succeeds but registry persistence fails, never claim the application pointer was committed. Record the discrepancy and reconcile before retry.
- Native thread ID reuse, native message ordering, and provider idempotency semantics remain unverified and must not be assumed.

## 8. Audit and observability

Use `MEMORY.MEMORY_AUDIT` where its schema supports meaningful, safe operation evidence: conversation ID, actor, operation, outcome, timestamp, reason, and bounded before/after state. Avoid raw user messages, assistant outputs, credentials, or sensitive customer data in audit records. If this table cannot express operation idempotency and uncertain outcomes safely, propose a narrowly scoped supplemental operation ledger at P2-B-05.

## 9. Moderate acceptance tests

| Milestone | Minimal evidence |
|---|---|
| P2-B-01 | Contract review: schema compatibility and invariants; no DDL |
| P2-B-02 | Authorized access, cross-owner denial, missing/invalid identity denial |
| P2-B-03 | Registry create/read, duplicate prevention, persisted native mapping |
| P2-B-04 | Create/continue/close, invalid continuation denial |
| P2-B-05 | Duplicate request behavior, one concurrency conflict, one uncertain-outcome/recovery path |
| P2-B-06 | Audit record, end-to-end run, compact regression against P2-A |

**Testing principle:** Representative happy path + meaningful negative/security test + targeted failure/recovery test where applicable. Do not expand into exhaustive native feature diagnostics unless an acceptance criterion fails.

## 10. Open decisions and approval gate

1. Confirm `OWNER_ID` namespace (e.g., stable application subject) and its relationship to `CUSTOMER_ID`.
2. Confirm the physical migration/backfill approach for existing P0 metadata rows (currently reported empty at discovery).
3. Validate actual Snowflake-native thread association, response IDs, and failure behavior before implementation claims.
4. Choose and demonstrate a safe uniqueness/concurrency enforcement strategy before production-oriented guarantees.
5. Decide whether a dedicated operation ledger is required based on representative reliability tests.

**Approval requested:** Accept reuse of `MEMORY.CONVERSATION_METADATA` and the logical contract above as the design baseline. Approval authorizes P2-B-02 design and testing, **not** immediate schema changes or claims of production readiness.
