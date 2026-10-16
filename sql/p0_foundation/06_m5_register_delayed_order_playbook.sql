-- M5-B.02: Synthetic approved delayed-order investigation playbook.
-- Demonstration policy only; not a real carrier policy.

USE ROLE ECOM_AGENT_MEMORY_OWNER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE ECOM_AGENT_MEMORY_WH;
USE DATABASE ECOM_AGENT_MEMORY_DB;
USE SCHEMA PROCEDURES;

BEGIN TRANSACTION;

INSERT INTO PROCEDURE_CATALOG (
    PROCEDURE_ID,
    PROCEDURE_NAME,
    BUSINESS_DOMAIN,
    PROCEDURE_PURPOSE,
    PROCEDURE_OWNER,
    PROCEDURE_STATUS
)
SELECT
    'ECOM-DELAY-INVESTIGATION',
    'Delayed Order Investigation',
    'ECOMMERCE',
    'Evidence-based investigation and escalation recommendation for delayed shipments',
    'SYNTHETIC_ECOM_OPERATIONS',
    'ACTIVE'
WHERE NOT EXISTS (
    SELECT 1
    FROM PROCEDURE_CATALOG
    WHERE PROCEDURE_ID = 'ECOM-DELAY-INVESTIGATION'
);

INSERT INTO PROCEDURE_VERSIONS (
    PROCEDURE_VERSION_ID,
    PROCEDURE_ID,
    VERSION_NUMBER,
    PROCEDURE_STEPS,
    GUARDRAILS,
    INPUT_CONTRACT,
    OUTPUT_CONTRACT,
    APPROVAL_STATUS,
    APPROVED_BY,
    APPROVED_AT,
    EFFECTIVE_FROM
)
SELECT
    'ECOM-DELAY-INVESTIGATION-V1',
    'ECOM-DELAY-INVESTIGATION',
    1,
    PARSE_JSON('[
      {"step_id":"S1","action":"Verify order existence, order status and associated shipments"},
      {"step_id":"S2","action":"Compare promised delivery and revised ETA with investigation date"},
      {"step_id":"S3","action":"Examine delay reason and latest chronological tracking events"},
      {"step_id":"S4","action":"Recommend carrier investigation only when revised ETA is missed AND tracking inactivity is at least 48 hours; otherwise report insufficient evidence or no escalation"},
      {"step_id":"S5","action":"Enforce restrictions on refunds, compensation, reshipment and delivery promises"},
      {"step_id":"S6","action":"Report verified findings, missing evidence, decision, next action and procedure version"}
    ]'),
    PARSE_JSON('{
      "policy_type":"SYNTHETIC_DEMONSTRATION",
      "tracking_inactivity_hours":48,
      "escalation_requires":["REVISED_ETA_MISSED","TRACKING_INACTIVE_48_HOURS"],
      "read_only":true,
      "prohibited_actions":["ISSUE_REFUND","ISSUE_COMPENSATION","CREATE_RESHIPMENT","PROMISE_DELIVERY_DATE"],
      "missing_evidence_behavior":"UNDETERMINED"
    }'),
    PARSE_JSON('{"required":["order_id"],"order_id_type":"NUMBER"}'),
    PARSE_JSON('{
      "required":["order_id","verified_facts","missing_evidence","escalation_decision","recommended_next_action","procedure_version","step_evidence"],
      "escalation_decisions":["ELIGIBLE","NOT_ELIGIBLE","UNDETERMINED"]
    }'),
    'APPROVED',
    'SYNTHETIC_DEMO_APPROVER',
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP()
WHERE NOT EXISTS (
    SELECT 1
    FROM PROCEDURE_VERSIONS
    WHERE PROCEDURE_ID = 'ECOM-DELAY-INVESTIGATION'
      AND VERSION_NUMBER = 1
);

COMMIT;

SELECT
    C.PROCEDURE_ID,
    C.PROCEDURE_STATUS,
    V.VERSION_NUMBER,
    V.APPROVAL_STATUS,
    V.APPROVED_BY,
    V.GUARDRAILS:tracking_inactivity_hours::NUMBER AS INACTIVITY_HOURS,
    ARRAY_SIZE(V.PROCEDURE_STEPS) AS STEP_COUNT
FROM PROCEDURE_CATALOG C
JOIN PROCEDURE_VERSIONS V
    ON C.PROCEDURE_ID = V.PROCEDURE_ID
WHERE C.PROCEDURE_ID = 'ECOM-DELAY-INVESTIGATION'
ORDER BY V.VERSION_NUMBER;
