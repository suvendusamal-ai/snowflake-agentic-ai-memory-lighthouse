"""M5: Read approved and effective operational procedures."""

import json
from datetime import datetime, timezone

import snowflake.connector


CONNECTION = "CoCo_Oct"
ROLE = "ECOM_AGENT_MEMORY_OWNER"
WAREHOUSE = "ECOM_AGENT_MEMORY_WH"

PROCEDURE_ID = "ECOM-DELAY-INVESTIGATION"

CATALOG = "ECOM_AGENT_MEMORY_DB.PROCEDURES.PROCEDURE_CATALOG"
VERSIONS = "ECOM_AGENT_MEMORY_DB.PROCEDURES.PROCEDURE_VERSIONS"


def load_approved_procedure(procedure_id=PROCEDURE_ID):
    """Return exactly one applicable approved procedure, or fail closed."""

    if procedure_id != PROCEDURE_ID:
        raise ValueError("Unsupported procedure")

    conn = snowflake.connector.connect(
        connection_name=CONNECTION,
        role=ROLE,
        warehouse=WAREHOUSE,
    )

    cursor = conn.cursor()

    try:
        cursor.execute("USE SECONDARY ROLES NONE")

        cursor.execute(
            f"""
            SELECT
                c.PROCEDURE_ID,
                c.PROCEDURE_NAME,
                v.PROCEDURE_VERSION_ID,
                v.VERSION_NUMBER,
                v.PROCEDURE_STEPS,
                v.GUARDRAILS,
                v.INPUT_CONTRACT,
                v.OUTPUT_CONTRACT,
                v.APPROVED_BY,
                v.APPROVED_AT
            FROM {CATALOG} c
            JOIN {VERSIONS} v
              ON c.PROCEDURE_ID = v.PROCEDURE_ID
            WHERE c.PROCEDURE_ID = %s
              AND c.BUSINESS_DOMAIN = 'ECOMMERCE'
              AND c.PROCEDURE_STATUS = 'ACTIVE'
              AND v.APPROVAL_STATUS = 'APPROVED'
              AND NULLIF(TRIM(v.APPROVED_BY), '') IS NOT NULL
              AND v.APPROVED_AT IS NOT NULL
              AND v.EFFECTIVE_FROM IS NOT NULL
              AND v.EFFECTIVE_FROM <= CURRENT_TIMESTAMP()
              AND (
                  v.EFFECTIVE_TO IS NULL
                  OR v.EFFECTIVE_TO > CURRENT_TIMESTAMP()
              )
            ORDER BY v.VERSION_NUMBER DESC
            LIMIT 2
            """,
            (procedure_id,),
        )

        rows = cursor.fetchall()

        if len(rows) != 1:
            raise ValueError(
                f"Expected exactly one applicable approved procedure; found {len(rows)}"
            )

        row = rows[0]

        def parse_variant(value):
            if isinstance(value, str):
                return json.loads(value)
            return value

        steps = parse_variant(row[4])
        guardrails = parse_variant(row[5])
        input_contract = parse_variant(row[6])
        output_contract = parse_variant(row[7])

        if not isinstance(steps, list) or len(steps) != 6:
            raise ValueError("Invalid procedure steps")

        if not isinstance(guardrails, dict):
            raise ValueError("Invalid procedure guardrails")

        threshold = guardrails.get("tracking_inactivity_hours")

        if (
            type(threshold) is not int
            or threshold < 1
            or threshold > 168
        ):
            raise ValueError(
                "Invalid approved tracking inactivity threshold"
            )

        if guardrails.get("read_only") is not True:
            raise ValueError("Procedure must be read-only")

        return {
            "procedure_id": row[0],
            "procedure_name": row[1],
            "procedure_version_id": row[2],
            "version": row[3],
            "steps": steps,
            "guardrails": guardrails,
            "input_contract": input_contract,
            "output_contract": output_contract,
            "approved_by": row[8],
            "approved_at": str(row[9]),
        }

    finally:
        cursor.close()
        conn.close()

def evaluate_delayed_order(order_id, procedure):
    """Independently evaluate one order against the approved playbook."""

    if not isinstance(order_id, str) or not order_id.isdigit():
        raise ValueError("Order ID must contain digits only")

    if procedure.get("procedure_id") != PROCEDURE_ID:
        raise ValueError("Unexpected procedure")

    threshold = procedure["guardrails"]["tracking_inactivity_hours"]

    if not isinstance(threshold, int) or threshold <= 0:
        raise ValueError("Invalid tracking threshold")

    conn = snowflake.connector.connect(
        connection_name=CONNECTION,
        role=ROLE,
        warehouse=WAREHOUSE,
    )

    cursor = conn.cursor()

    try:
        cursor.execute("USE SECONDARY ROLES NONE")

        cursor.execute(
            """
            SELECT
                o.ORDER_ID,
                o.ORDER_STATUS,
                o.ACTUAL_DELIVERY_DATE,
                s.SHIPMENT_ID,
                s.SHIPMENT_STATUS,
                s.REVISED_DELIVERY_DATE,
                s.DELAY_REASON,
                MAX(e.EVENT_TIMESTAMP) AS LAST_TRACKING_EVENT,
                DATEDIFF(
                    'hour',
                    MAX(e.EVENT_TIMESTAMP),
                    CURRENT_TIMESTAMP()
                ) AS INACTIVE_HOURS,
                CURRENT_DATE() AS EVALUATION_DATE
            FROM ECOM_AGENT_MEMORY_DB.RAW.ORDERS o
            LEFT JOIN ECOM_AGENT_MEMORY_DB.RAW.SHIPMENTS s
                ON o.ORDER_ID = s.ORDER_ID
            LEFT JOIN ECOM_AGENT_MEMORY_DB.RAW.SHIPMENT_EVENTS e
                ON s.SHIPMENT_ID = e.SHIPMENT_ID
            WHERE o.ORDER_ID = %s
            GROUP BY
                o.ORDER_ID,
                o.ORDER_STATUS,
                o.ACTUAL_DELIVERY_DATE,
                s.SHIPMENT_ID,
                s.SHIPMENT_STATUS,
                s.REVISED_DELIVERY_DATE,
                s.DELAY_REASON
            """,
            (int(order_id),),
        )

        rows = cursor.fetchall()

        if not rows:
            return {
                "order_id": order_id,
                "decision": "UNDETERMINED",
                "reason": "Order not found",
                "procedure_id": procedure["procedure_id"],
                "procedure_version": procedure["version"],
                "inactive_hours": None,
                "threshold_hours": threshold,
            }

        if len(rows) != 1:
            return {
                "order_id": order_id,
                "decision": "UNDETERMINED",
                "reason": "Multiple shipment records require separate assessment",
                "procedure_id": procedure["procedure_id"],
                "procedure_version": procedure["version"],
                "inactive_hours": None,
                "threshold_hours": threshold,
            }

        (
            found_order,
            order_status,
            actual_delivery,
            shipment_id,
            shipment_status,
            revised_eta,
            delay_reason,
            last_event,
            inactive_hours,
            evaluation_date,
        ) = rows[0]

        missed_eta = (
            revised_eta is not None
            and revised_eta < evaluation_date
        )

        inactive_enough = (
            inactive_hours is not None
            and inactive_hours >= threshold
        )

        delivered = (
            actual_delivery is not None
            or order_status == "DELIVERED"
            or shipment_status == "DELIVERED"
        )

        if delivered:
            decision = "NOT_ELIGIBLE"
            reason = "Delivery already recorded"
        elif shipment_id is None or revised_eta is None or last_event is None:
            decision = "UNDETERMINED"
            reason = "Required shipment evidence is missing"
        elif missed_eta and inactive_enough:
            decision = "ELIGIBLE"
            reason = "Missed revised ETA and tracking inactivity threshold met"
        else:
            decision = "NOT_ELIGIBLE"
            reason = "Escalation conditions not both satisfied"

        return {
            "order_id": str(found_order),
            "shipment_id": shipment_id,
            "order_status": order_status,
            "shipment_status": shipment_status,
            "revised_eta": str(revised_eta) if revised_eta else None,
            "last_tracking_event": str(last_event) if last_event else None,
            "inactive_hours": inactive_hours,
            "threshold_hours": threshold,
            "missed_revised_eta": missed_eta,
            "tracking_threshold_met": inactive_enough,
            "decision": decision,
            "reason": reason,
            "procedure_id": procedure["procedure_id"],
            "procedure_version": procedure["version"],
        }

    finally:
        cursor.close()
        conn.close()