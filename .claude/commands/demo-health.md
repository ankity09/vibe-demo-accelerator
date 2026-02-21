# /demo-health — Health Check & Diagnostics

Run a comprehensive health check on the deployed demo app and diagnose any issues.

## Steps

1. **Read `demo-config.yaml`** or `CLAUDE.md` Project Identity to get the app name, profile, and URLs.

2. **Check app status:**
   ```bash
   databricks apps get <app-name> --profile=<profile>
   ```
   - Is the app in RUNNING state?
   - Are resources registered? (Look for `resources` array in response)
   - Note the app URL and SP client ID.

3. **Hit the health endpoint:**
   Use WebFetch on `https://<app-url>/api/health` to check status.
   - If 401/empty response: This is normal from CLI — Databricks Apps require browser OAuth. Tell the user to open the URL in their browser instead.

4. **Diagnose failures using this table:**

   | Check | Fails When | Fix |
   |-------|-----------|-----|
   | `sdk` | App SP not authenticated | Redeploy the app |
   | `sql_warehouse` | Warehouse resource not registered or SP lacks CAN_USE | Register resource via API + grant CAN_USE + redeploy |
   | `lakebase` | PGHOST not set (resource not registered) or Lakebase instance not running | Register database resource via API + redeploy; check instance status |
   | All zeros on dashboard | Delta Lake tables don't exist | Run `notebooks/02_generate_data.py` |
   | Agent Workflows empty | Lakebase `workflows` table empty or doesn't exist | Apply `core_schema.sql` + run `notebooks/03_seed_lakebase.py` |
   | Chat returns 403 | MAS endpoint resource not registered or SP lacks CAN_QUERY | Register mas-endpoint resource + redeploy |
   | Chat returns empty | MAS tile ID wrong in app.yaml | Verify MAS_TILE_ID is first 8 chars of the tile UUID |

5. **If issues found**, offer to fix them automatically:
   - Missing resources → register via API + redeploy
   - Missing data → run the appropriate notebook
   - Missing permissions → grant via CLI

6. **Report:**
   ```
   Health Check Results
   ━━━━━━━━━━━━━━━━━━━
   App:        <name> (<status>)
   URL:        <url>
   SDK:        <pass/fail>
   Warehouse:  <pass/fail>
   Lakebase:   <pass/fail>

   Resources registered: <yes/no>
   Delta tables exist:   <yes/no>
   Lakebase tables exist: <yes/no>

   Issues found: <N>
   <list of issues and fixes applied>
   ```
