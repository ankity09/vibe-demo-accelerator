# Genie Space

Databricks Genie enables natural language queries over Delta Lake tables without writing SQL.
Users ask questions in plain English and Genie generates and executes the appropriate query.

## What it does
- Translates natural language questions into SQL against your Delta Lake tables
- Maintains conversation context for follow-up questions
- Supports custom instructions to tune responses to your domain vocabulary
- Used as a sub-agent inside MAS to give the AI read access to analytics data

## Prerequisites
- SQL Warehouse (Genie executes queries through it)
- Delta Lake tables already populated (run `notebooks/02_generate_data.py` first)
- Unity Catalog access granted to the app service principal

## Setup
1. Create a Genie Space via the REST API (see Gotcha #10 in CLAUDE.md for the exact steps)
2. Attach your Delta Lake tables using `serialized_space` format (NOT `table_identifiers`)
3. Grant `CAN_RUN` to the app SP and `account users` group
4. Add `GENIE_SPACE_ID` to `app.yaml`
5. Wire as a `genie-space` sub-agent in your MAS config

## Connection to the Demo
The Genie Space is the primary data retrieval layer for the AI Chat page.
When a user asks "show me this week's top risk items", MAS routes the query to Genie
which executes the right SQL and returns structured results.
