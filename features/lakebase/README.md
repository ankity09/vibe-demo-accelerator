# Lakebase

Lakebase is Databricks' serverless PostgreSQL-compatible OLTP database, designed for real-time
transactional workloads alongside Delta Lake analytics. It is the write layer for agent actions.

## What it does
- Provides a fully managed PostgreSQL 16-compatible database with no cluster management
- Stores operational state: notes, agent actions, workflows, and domain-specific OLTP records
- Integrates with MAS via the Lakebase MCP Server (33 MCP tools for CRUD and DDL)
- Scales to zero when idle; auto-warms on first connection

## Prerequisites
- Lakebase instance created and in `AVAILABLE` state (not `RUNNING` — see Gotcha #33)
- Database created within the instance
- Core and domain schemas applied via `databricks psql`
- App resources registered via `databricks apps update` and redeployed (Gotcha #8)

## Setup
1. Create instance: `databricks database create-database-instance <name> --capacity CU_1`
2. Create database: `databricks psql <instance> -- -c "CREATE DATABASE <db>;"`
3. Apply schemas: `databricks psql <instance> -- -d <db> -f lakebase/core_schema.sql`
4. Register as app resource, redeploy to inject PGHOST/PGPORT/PGDATABASE/PGUSER
5. Grant SP access AFTER redeploy (SP role only exists after resource registration)

## Connection to the Demo
Lakebase is the operational backbone of every demo. The Agent Workflows page reads from the
`workflows` and `agent_actions` tables. The AI Chat page writes new records when the agent
creates work orders, flags risks, or logs decisions — making the demo feel like a live system.
