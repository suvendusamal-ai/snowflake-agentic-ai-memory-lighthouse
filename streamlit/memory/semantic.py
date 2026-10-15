"""M4: Approved, customer-scoped semantic preference capture and retrieval."""

from uuid import uuid4

import snowflake.connector


CONNECTION = "CoCo_Oct"
ROLE = "ECOM_AGENT_MEMORY_OWNER"
WAREHOUSE = "ECOM_AGENT_MEMORY_WH"

MEMORY_TABLE = "ECOM_AGENT_MEMORY_DB.MEMORY.SEMANTIC_MEMORY"
CONVERSATION_TABLE = "ECOM_AGENT_MEMORY_DB.MEMORY.CONVERSATION_METADATA"
AUDIT_TABLE = "ECOM_AGENT_MEMORY_DB.MEMORY.MEMORY_AUDIT"

ALLOWED_PREFERENCES = {
    "NOTIFICATION_CHANNEL": {"EMAIL", "SMS"},
}


def save_semantic_preference(
    customer_id,
    conversation_id,
    preference_key,
    preference_value,
    capture_id,
    approved=False,
):
    """Save one approved customer preference with an audit record."""

    if not approved:
        raise ValueError("Explicit memory approval is required")

    for value in (
        customer_id,
        conversation_id,
        preference_key,
        preference_value,
        capture_id,
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("All capture fields must be nonempty strings")

    if preference_key not in ALLOWED_PREFERENCES:
        raise ValueError("Unsupported preference key")

    if preference_value not in ALLOWED_PREFERENCES[preference_key]:
        raise ValueError("Unsupported preference value")

    conn = snowflake.connector.connect(
        connection_name=CONNECTION,
        role=ROLE,
        warehouse=WAREHOUSE,
    )
    cursor = conn.cursor()

    try:
        cursor.execute("USE SECONDARY ROLES NONE")
        cursor.execute("BEGIN TRANSACTION")

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {CONVERSATION_TABLE}
            WHERE CONVERSATION_ID = %s
              AND CUSTOMER_ID = %s
            """,
            (conversation_id, customer_id),
        )
        if cursor.fetchone()[0] != 1:
            raise ValueError("Conversation ownership validation failed")

        source_reference = f"M4_STREAMLIT_{capture_id}"
        if len(source_reference) > 200:
            raise ValueError("Capture ID exceeds supported length")

        cursor.execute(
            f"""
            SELECT MEMORY_ID, FACT_KEY, FACT_VALUE::VARCHAR
            FROM {MEMORY_TABLE}
            WHERE CUSTOMER_ID = %s
              AND SOURCE_REFERENCE = %s
            LIMIT 2
            """,
            (customer_id, source_reference),
        )
        existing = cursor.fetchall()
        if len(existing) > 1:
            raise ValueError("Duplicate capture records detected")
        if existing:
            memory_id, old_key, old_value = existing[0]
            if old_key != preference_key or old_value != preference_value:
                raise ValueError("Conflicting capture ID reuse")
            conn.commit()
            return memory_id

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {MEMORY_TABLE}
            WHERE CUSTOMER_ID = %s
              AND FACT_KEY = %s
              AND MEMORY_STATUS = 'ACTIVE'
            """,
            (customer_id, preference_key),
        )
        if cursor.fetchone()[0] != 0:
            raise ValueError(
                "Active preference already exists; use update operation"
            )

        memory_id = str(uuid4())
        audit_id = str(uuid4())

        cursor.execute(
            f"""
            INSERT INTO {MEMORY_TABLE}
            (
                MEMORY_ID, CUSTOMER_ID, FACT_CATEGORY,
                FACT_KEY, FACT_VALUE, FACT_TEXT,
                SOURCE_REFERENCE, MEMORY_VERSION, MEMORY_STATUS
            )
            SELECT
                %s, %s, 'DELIVERY_PREFERENCE',
                %s, TO_VARIANT(%s),
                %s, %s, 1, 'ACTIVE'
            """,
            (
                memory_id,
                customer_id,
                preference_key,
                preference_value,
                f"Customer prefers {preference_value} delivery notifications",
                source_reference,
            ),
        )

        cursor.execute(
            f"""
            INSERT INTO {AUDIT_TABLE}
            (
                AUDIT_ID, MEMORY_ID, CUSTOMER_ID,
                MEMORY_TYPE, OPERATION_TYPE,
                ACTOR_TYPE, ACTOR_ID, CONVERSATION_ID,
                OPERATION_REASON, AFTER_VALUE,
                OPERATION_STATUS
            )
            SELECT
                %s, %s, %s,
                'SEMANTIC', 'CREATE',
                'APPLICATION', %s, %s,
                'Explicitly approved customer preference',
                OBJECT_CONSTRUCT(
                    'preference_key', %s,
                    'preference_value', %s,
                    'capture_id', %s,
                    'verification_status', 'CUSTOMER_REPORTED'
                ),
                'SUCCESS'
            """,
            (
                audit_id,
                memory_id,
                customer_id,
                customer_id,
                conversation_id,
                preference_key,
                preference_value,
                capture_id,
            ),
        )

        conn.commit()
        return memory_id

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def retrieve_semantic_preferences(customer_id, preference_key=None):
    """Retrieve active, valid preferences belonging to one customer."""

    if not isinstance(customer_id, str) or not customer_id.strip():
        raise ValueError("Valid customer ID is required")

    if preference_key is not None and preference_key not in ALLOWED_PREFERENCES:
        raise ValueError("Unsupported preference key")

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
                MEMORY_ID,
                FACT_KEY,
                FACT_VALUE::VARCHAR,
                FACT_TEXT,
                MEMORY_VERSION
            FROM {MEMORY_TABLE}
            WHERE CUSTOMER_ID = %s
              AND MEMORY_STATUS = 'ACTIVE'
              AND VALID_FROM <= CURRENT_TIMESTAMP()
              AND (VALID_TO IS NULL OR VALID_TO > CURRENT_TIMESTAMP())
              AND (EXPIRES_AT IS NULL OR EXPIRES_AT > CURRENT_TIMESTAMP())
              AND (%s IS NULL OR FACT_KEY = %s)
            ORDER BY MEMORY_VERSION DESC, CREATED_AT DESC
            """,
            (customer_id, preference_key, preference_key),
        )
        rows = cursor.fetchall()
        return [
            {
                "memory_id": row[0],
                "preference_key": row[1],
                "preference_value": row[2],
                "fact_text": row[3],
                "memory_version": row[4],
            }
            for row in rows
        ]
    finally:
        cursor.close()
        conn.close()


def update_semantic_preference(
    customer_id,
    conversation_id,
    preference_key,
    new_preference_value,
    update_id,
    approved=False,
):
    """Supersede an active preference and audit an approved new version."""

    if not approved:
        raise ValueError("Explicit memory approval is required")

    for value in (
        customer_id,
        conversation_id,
        preference_key,
        new_preference_value,
        update_id,
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("All update fields must be nonempty strings")

    if preference_key not in ALLOWED_PREFERENCES:
        raise ValueError("Unsupported preference key")
    if new_preference_value not in ALLOWED_PREFERENCES[preference_key]:
        raise ValueError("Unsupported preference value")

    source_reference = f"M4_UPDATE_{update_id}"
    if len(source_reference) > 200:
        raise ValueError("Update ID exceeds supported length")

    conn = snowflake.connector.connect(
        connection_name=CONNECTION,
        role=ROLE,
        warehouse=WAREHOUSE,
    )
    cursor = conn.cursor()
    try:
        cursor.execute("USE SECONDARY ROLES NONE")
        cursor.execute("BEGIN TRANSACTION")

        cursor.execute(
            f"""
            SELECT COUNT(*) FROM {CONVERSATION_TABLE}
            WHERE CONVERSATION_ID = %s AND CUSTOMER_ID = %s
            """,
            (conversation_id, customer_id),
        )
        if cursor.fetchone()[0] != 1:
            raise ValueError("Conversation ownership validation failed")

        # A sequential retry must return the same version, without a new audit.
        cursor.execute(
            f"""
            SELECT MEMORY_ID, FACT_KEY, FACT_VALUE::VARCHAR
            FROM {MEMORY_TABLE}
            WHERE CUSTOMER_ID = %s AND SOURCE_REFERENCE = %s
            LIMIT 2
            """,
            (customer_id, source_reference),
        )
        prior_attempt = cursor.fetchall()
        if len(prior_attempt) > 1:
            raise ValueError("Duplicate update records detected")
        if prior_attempt:
            memory_id, old_key, old_value = prior_attempt[0]
            if old_key != preference_key or old_value != new_preference_value:
                raise ValueError("Conflicting update ID reuse")
            conn.commit()
            return memory_id

        cursor.execute(
            f"""
            SELECT MEMORY_ID, FACT_VALUE::VARCHAR, MEMORY_VERSION
            FROM {MEMORY_TABLE}
            WHERE CUSTOMER_ID = %s
              AND FACT_KEY = %s
              AND MEMORY_STATUS = 'ACTIVE'
              AND VALID_FROM <= CURRENT_TIMESTAMP()
              AND (VALID_TO IS NULL OR VALID_TO > CURRENT_TIMESTAMP())
              AND (EXPIRES_AT IS NULL OR EXPIRES_AT > CURRENT_TIMESTAMP())
            LIMIT 2
            """,
            (customer_id, preference_key),
        )
        active = cursor.fetchall()
        if len(active) != 1:
            raise ValueError("Expected exactly one active preference")
        old_memory_id, old_value, old_version = active[0]
        if old_value == new_preference_value:
            raise ValueError("New preference must differ from active value")

        cursor.execute(
            f"""
            UPDATE {MEMORY_TABLE}
            SET MEMORY_STATUS = 'SUPERSEDED',
                VALID_TO = CURRENT_TIMESTAMP(),
                UPDATED_AT = CURRENT_TIMESTAMP()
            WHERE MEMORY_ID = %s
              AND CUSTOMER_ID = %s
              AND FACT_KEY = %s
              AND MEMORY_STATUS = 'ACTIVE'
            """,
            (old_memory_id, customer_id, preference_key),
        )
        if cursor.rowcount != 1:
            raise ValueError("Preference changed before update completed")

        new_memory_id = str(uuid4())
        cursor.execute(
            f"""
            INSERT INTO {MEMORY_TABLE}
            (
                MEMORY_ID, CUSTOMER_ID, FACT_CATEGORY,
                FACT_KEY, FACT_VALUE, FACT_TEXT,
                SOURCE_REFERENCE, MEMORY_VERSION, MEMORY_STATUS
            )
            SELECT %s, %s, 'DELIVERY_PREFERENCE',
                   %s, TO_VARIANT(%s), %s, %s, %s, 'ACTIVE'
            """,
            (
                new_memory_id,
                customer_id,
                preference_key,
                new_preference_value,
                f"Customer prefers {new_preference_value} delivery notifications",
                source_reference,
                old_version + 1,
            ),
        )

        cursor.execute(
            f"""
            INSERT INTO {AUDIT_TABLE}
            (
                AUDIT_ID, MEMORY_ID, CUSTOMER_ID, MEMORY_TYPE,
                OPERATION_TYPE, ACTOR_TYPE, ACTOR_ID,
                CONVERSATION_ID, OPERATION_REASON,
                BEFORE_VALUE, AFTER_VALUE, OPERATION_STATUS
            )
            SELECT %s, %s, %s, 'SEMANTIC',
                   'UPDATE', 'APPLICATION', %s,
                   %s, 'Explicitly approved preference update',
                   OBJECT_CONSTRUCT('memory_id', %s, 'preference_value', %s,
                                    'memory_version', %s),
                   OBJECT_CONSTRUCT('memory_id', %s, 'preference_key', %s,
                                    'preference_value', %s, 'memory_version', %s,
                                    'update_id', %s,
                                    'verification_status', 'CUSTOMER_REPORTED'),
                   'SUCCESS'
            """,
            (
                str(uuid4()), new_memory_id, customer_id, customer_id,
                conversation_id, old_memory_id, old_value, old_version,
                new_memory_id, preference_key, new_preference_value,
                old_version + 1, update_id,
            ),
        )
        conn.commit()
        return new_memory_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def revoke_semantic_preference(
    customer_id,
    conversation_id,
    preference_key,
    revoke_id,
    approved=False,
):
    """Revoke an active preference, retaining history and an audit trail.

    Sequential retries with the same revoke_id return the same memory ID.
    This does not provide concurrency-safe exactly-once guarantees.
    """
    if not approved:
        raise ValueError("Explicit memory approval is required")

    for value in (customer_id, conversation_id, preference_key, revoke_id):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("All revocation fields must be nonempty strings")
    if preference_key not in ALLOWED_PREFERENCES:
        raise ValueError("Unsupported preference key")

    conn = snowflake.connector.connect(
        connection_name=CONNECTION, role=ROLE, warehouse=WAREHOUSE
    )
    cursor = conn.cursor()
    try:
        cursor.execute("USE SECONDARY ROLES NONE")
        cursor.execute("BEGIN TRANSACTION")

        cursor.execute(
            f"""SELECT COUNT(*) FROM {CONVERSATION_TABLE}
                WHERE CONVERSATION_ID = %s AND CUSTOMER_ID = %s""",
            (conversation_id, customer_id),
        )
        if cursor.fetchone()[0] != 1:
            raise ValueError("Conversation ownership validation failed")

        # Check an existing successful revocation before checking active state.
        cursor.execute(
            f"""SELECT MEMORY_ID, AFTER_VALUE:preference_key::VARCHAR
                FROM {AUDIT_TABLE}
                WHERE CUSTOMER_ID = %s AND MEMORY_TYPE = 'SEMANTIC'
                  AND OPERATION_TYPE = 'REVOKE'
                  AND OPERATION_STATUS = 'SUCCESS'
                  AND AFTER_VALUE:revoke_id::VARCHAR = %s
                LIMIT 2""",
            (customer_id, revoke_id),
        )
        prior = cursor.fetchall()
        if len(prior) > 1:
            raise ValueError("Duplicate revocation audit records detected")
        if prior:
            memory_id, old_key = prior[0]
            if old_key != preference_key:
                raise ValueError("Conflicting revocation ID reuse")
            conn.commit()
            return memory_id

        cursor.execute(
            f"""SELECT MEMORY_ID, FACT_VALUE::VARCHAR, MEMORY_VERSION
                FROM {MEMORY_TABLE}
                WHERE CUSTOMER_ID = %s AND FACT_KEY = %s
                  AND MEMORY_STATUS = 'ACTIVE'
                  AND VALID_FROM <= CURRENT_TIMESTAMP()
                  AND (VALID_TO IS NULL OR VALID_TO > CURRENT_TIMESTAMP())
                  AND (EXPIRES_AT IS NULL OR EXPIRES_AT > CURRENT_TIMESTAMP())
                LIMIT 2""",
            (customer_id, preference_key),
        )
        active = cursor.fetchall()
        if len(active) != 1:
            raise ValueError("Expected exactly one active preference")
        memory_id, old_value, version = active[0]

        cursor.execute(
            f"""UPDATE {MEMORY_TABLE}
                SET MEMORY_STATUS = 'REVOKED',
                    VALID_TO = CURRENT_TIMESTAMP(),
                    UPDATED_AT = CURRENT_TIMESTAMP()
                WHERE MEMORY_ID = %s AND CUSTOMER_ID = %s
                  AND FACT_KEY = %s AND MEMORY_STATUS = 'ACTIVE'""",
            (memory_id, customer_id, preference_key),
        )
        if cursor.rowcount != 1:
            raise ValueError("Preference changed before revocation completed")

        cursor.execute(
            f"""INSERT INTO {AUDIT_TABLE}
                (AUDIT_ID, MEMORY_ID, CUSTOMER_ID, MEMORY_TYPE,
                 OPERATION_TYPE, ACTOR_TYPE, ACTOR_ID,
                 CONVERSATION_ID, OPERATION_REASON,
                 BEFORE_VALUE, AFTER_VALUE, OPERATION_STATUS)
                SELECT %s, %s, %s, 'SEMANTIC',
                       'REVOKE', 'APPLICATION', %s, %s,
                       'Explicitly approved preference revocation',
                       OBJECT_CONSTRUCT('memory_id', %s,
                                        'preference_key', %s,
                                        'preference_value', %s,
                                        'memory_version', %s,
                                        'memory_status', 'ACTIVE'),
                       OBJECT_CONSTRUCT('memory_id', %s,
                                        'preference_key', %s,
                                        'memory_version', %s,
                                        'memory_status', 'REVOKED',
                                        'revoke_id', %s),
                       'SUCCESS'""",
            (str(uuid4()), memory_id, customer_id, customer_id,
             conversation_id, memory_id, preference_key, old_value,
             version, memory_id, preference_key, version, revoke_id),
        )
        conn.commit()
        return memory_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
