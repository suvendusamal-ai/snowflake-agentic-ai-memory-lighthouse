-- ============================================================
-- P0-C: Snowflake Agentic AI Memory Lighthouse
-- Infrastructure provisioning
-- Connection: CoCo_Oct
-- ============================================================

-- 1. Create dedicated project owner role
USE ROLE USERADMIN;

CREATE ROLE IF NOT EXISTS ECOM_AGENT_MEMORY_OWNER
  COMMENT = 'Object owner role for Agentic AI Memory Lighthouse';

-- 2. Assign project role to SYSADMIN hierarchy
USE ROLE SECURITYADMIN;

GRANT ROLE ECOM_AGENT_MEMORY_OWNER TO ROLE SYSADMIN;
GRANT ROLE ECOM_AGENT_MEMORY_OWNER TO USER SUVENDU;

-- 3. Provision database and warehouse
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS ECOM_AGENT_MEMORY_DB
  DATA_RETENTION_TIME_IN_DAYS = 1
  COMMENT = 'Synthetic e-commerce data and governed agent memory';

CREATE WAREHOUSE IF NOT EXISTS ECOM_AGENT_MEMORY_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Dedicated compute for Agentic AI Memory Lighthouse';

-- 4. Grant database and warehouse ownership to project role
GRANT OWNERSHIP ON DATABASE ECOM_AGENT_MEMORY_DB
  TO ROLE ECOM_AGENT_MEMORY_OWNER
  COPY CURRENT GRANTS;

GRANT OWNERSHIP ON WAREHOUSE ECOM_AGENT_MEMORY_WH
  TO ROLE ECOM_AGENT_MEMORY_OWNER
  COPY CURRENT GRANTS;

-- 5. Create schemas under project owner role
USE ROLE ECOM_AGENT_MEMORY_OWNER;

USE DATABASE ECOM_AGENT_MEMORY_DB;

CREATE SCHEMA IF NOT EXISTS RAW
  WITH MANAGED ACCESS
  COMMENT = 'Synthetic operational e-commerce data';

CREATE SCHEMA IF NOT EXISTS MEMORY
  WITH MANAGED ACCESS
  COMMENT = 'Persistent agent memory foundation';

CREATE SCHEMA IF NOT EXISTS PROCEDURES
  WITH MANAGED ACCESS
  COMMENT = 'Versioned procedural memory metadata';

CREATE SCHEMA IF NOT EXISTS EVALUATION
  WITH MANAGED ACCESS
  COMMENT = 'Agent memory evaluation framework';

CREATE SCHEMA IF NOT EXISTS AGENTS
  WITH MANAGED ACCESS
  COMMENT = 'Future Snowflake Cortex Agent objects';

-- No Cortex Agents are created in P0.
