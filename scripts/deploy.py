#!/usr/bin/env python3
"""
Vibe Demo Accelerator — Deployment Orchestrator

Handles everything DABs can't do natively: Lakebase provisioning, resource
registration, permission grants, and health verification.

Usage:
    python scripts/deploy.py --target <target> [--step <step>...] [--profile <profile>] [--dry-run]

Steps (run in order by default):
    config      Load target config and validate
    template    Generate app/app.yaml from target variables
    lakebase    Create Lakebase instance + database + apply schemas
    data        Run setup notebooks (placeholder — prints instructions)
    ai          Create Genie Space (placeholder — prints instructions)
    deploy      Run databricks bundle deploy
    resources   Register app resources via API + redeploy
    permissions Grant CAN_USE, CAN_QUERY, catalog/schema permissions
    verify      Check /api/health endpoint

Options:
    --target    Target name from databricks.yml (required)
    --step      Run specific step(s) only. Can repeat: --step lakebase --step deploy
    --profile   Override Databricks CLI profile (defaults to target workspace)
    --dry-run   Print what would be done without executing
    --skip-dabs Skip DABs deploy, use direct CLI deploy instead
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("\033[31mERROR:\033[0m pyyaml is required. Run: pip install -r scripts/requirements.txt")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

ALL_STEPS = [
    "config",
    "template",
    "lakebase",
    "data",
    "ai",
    "deploy",
    "resources",
    "permissions",
    "verify",
]

# Variables that MUST be set (not empty, not TODO, not CHANGEME)
REQUIRED_VARIABLES = [
    "warehouse_id",
    "catalog",
    "schema",
    "demo_name",
    "demo_customer",
    "app_name",
    "lakebase_instance",
    "lakebase_database",
]

# Variables that are optional (set later during AI layer setup)
OPTIONAL_VARIABLES = [
    "mas_tile_id",
    "genie_space_id",
    "ka_tile_id",
]

PLACEHOLDER_VALUES = {"TODO", "CHANGEME", "REPLACE_ME", "todo", "changeme", "replace_me", ""}

# Polling configuration
LAKEBASE_POLL_INTERVAL = 15  # seconds
LAKEBASE_POLL_TIMEOUT = 600  # 10 minutes
APP_POLL_INTERVAL = 10  # seconds
APP_POLL_TIMEOUT = 300  # 5 minutes

# Project root — scripts/ is one level below
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════════════════════════
# ANSI color helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _green(text: str) -> str:
    return f"\033[32m{text}\033[0m"


def _yellow(text: str) -> str:
    return f"\033[33m{text}\033[0m"


def _red(text: str) -> str:
    return f"\033[31m{text}\033[0m"


def _cyan(text: str) -> str:
    return f"\033[36m{text}\033[0m"


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def _dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


# ═══════════════════════════════════════════════════════════════════════════════
# Output helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _header(step: str, title: str) -> None:
    """Print a prominent step header."""
    print()
    print(f"  {_bold(_cyan(f'[{step.upper()}]'))}  {_bold(title)}")
    print(f"  {'─' * 60}")


def _info(msg: str) -> None:
    print(f"  {_dim('>')} {msg}")


def _success(msg: str) -> None:
    print(f"  {_green('✓')} {msg}")


def _warn(msg: str) -> None:
    print(f"  {_yellow('!')} {msg}")


def _error(msg: str) -> None:
    print(f"  {_red('✗')} {msg}")


def _cmd_display(cmd: list[str]) -> str:
    """Format a command list for display, quoting args with spaces."""
    parts = []
    for arg in cmd:
        if " " in arg or "{" in arg:
            parts.append(f'"{arg}"')
        else:
            parts.append(arg)
    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI runner
# ═══════════════════════════════════════════════════════════════════════════════

class CLIError(Exception):
    """Raised when a CLI command fails."""

    def __init__(self, cmd: list[str], returncode: int, stderr: str, stdout: str = ""):
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout
        super().__init__(f"Command failed (exit {returncode}): {_cmd_display(cmd)}")


def _run_cli(
    cmd: list[str],
    *,
    dry_run: bool = False,
    capture_json: bool = False,
    ignore_errors: bool = False,
    timeout: int = 300,
    stdin_data: Optional[str] = None,
) -> Optional[dict | list | str]:
    """
    Execute a CLI command via subprocess.

    Args:
        cmd: Command and arguments as a list.
        dry_run: If True, print the command but don't execute.
        capture_json: If True, parse stdout as JSON and return it.
        ignore_errors: If True, return None on failure instead of raising.
        timeout: Timeout in seconds.
        stdin_data: Optional string to pipe to stdin.

    Returns:
        Parsed JSON (dict/list) if capture_json, raw stdout string otherwise,
        or None if dry_run or on ignored error.
    """
    display = _cmd_display(cmd)

    if dry_run:
        print(f"  {_dim('$')} {_dim(display)}")
        return None

    _info(f"$ {display}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=stdin_data,
        )
    except FileNotFoundError:
        if ignore_errors:
            _warn(f"Command not found: {cmd[0]}")
            return None
        _error(f"Command not found: {cmd[0]}")
        _error("Is the Databricks CLI installed? Run: brew install databricks")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        if ignore_errors:
            _warn(f"Command timed out after {timeout}s")
            return None
        _error(f"Command timed out after {timeout}s: {display}")
        sys.exit(1)

    if result.returncode != 0:
        if ignore_errors:
            _warn(f"Command failed (exit {result.returncode}), continuing...")
            if result.stderr.strip():
                for line in result.stderr.strip().split("\n")[:5]:
                    _warn(f"  {line}")
            return None
        raise CLIError(cmd, result.returncode, result.stderr.strip(), result.stdout.strip())

    stdout = result.stdout.strip()
    if capture_json and stdout:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            if ignore_errors:
                _warn("Failed to parse JSON output")
                return None
            _error(f"Expected JSON output but got:\n{stdout[:500]}")
            sys.exit(1)

    return stdout


# ═══════════════════════════════════════════════════════════════════════════════
# Config loading
# ═══════════════════════════════════════════════════════════════════════════════

def _load_config(target: str, profile_override: Optional[str] = None) -> dict[str, Any]:
    """
    Load and resolve target configuration from databricks.yml.

    Reads databricks.yml at the project root, merges default variables with
    target-specific overrides, validates required variables, and returns a
    fully resolved config dict.

    Returns:
        {
            "target": str,
            "profile": str,
            "workspace_host": str,
            "variables": {str: str},
            "available_targets": [str],
        }
    """
    bundle_path = PROJECT_ROOT / "databricks.yml"

    if not bundle_path.exists():
        _error(f"databricks.yml not found at {bundle_path}")
        _error("This script must be run from the project root.")
        _info("Expected location: <project>/databricks.yml")
        _info("")
        _info("If you haven't set up DABs yet, create databricks.yml with:")
        _info("  databricks bundle init")
        sys.exit(1)

    with open(bundle_path) as f:
        bundle = yaml.safe_load(f)

    if not bundle:
        _error("databricks.yml is empty or invalid YAML")
        sys.exit(1)

    # Also load any included target files
    targets_section = bundle.get("targets", {})

    # Load target files from targets/ directory.
    # Each file has format: targets: { <name>: { workspace: ..., variables: ... } }
    # DABs merges these via the `include: ./targets/*.yml` directive.
    # Here we replicate that merge for the Python loader.
    targets_dir = PROJECT_ROOT / "targets"
    if targets_dir.is_dir():
        for target_file in targets_dir.glob("*.yml"):
            with open(target_file) as f:
                target_data = yaml.safe_load(f)
            if not target_data:
                continue
            # Unwrap the `targets:` key (matches DABs include format)
            file_targets = target_data.get("targets", target_data)
            if isinstance(file_targets, dict):
                for name, cfg in file_targets.items():
                    if name not in targets_section:
                        targets_section[name] = cfg

    available_targets = list(targets_section.keys())

    if target not in targets_section:
        _error(f"Target '{target}' not found in databricks.yml")
        if available_targets:
            _info(f"Available targets: {', '.join(available_targets)}")
        else:
            _info("No targets defined. Add a [targets] section to databricks.yml")
        sys.exit(1)

    target_config = targets_section[target]

    # Resolve variables: defaults from bundle root, overridden by target
    default_vars = {}
    if "variables" in bundle:
        for var_name, var_def in bundle["variables"].items():
            if isinstance(var_def, dict):
                default_vars[var_name] = str(var_def.get("default", ""))
            else:
                default_vars[var_name] = str(var_def) if var_def is not None else ""

    target_vars = {}
    if "variables" in target_config:
        for var_name, var_val in target_config["variables"].items():
            if isinstance(var_val, dict):
                target_vars[var_name] = str(var_val.get("default", var_val.get("value", "")))
            else:
                target_vars[var_name] = str(var_val) if var_val is not None else ""

    # Merge: target overrides defaults
    variables = {**default_vars, **target_vars}

    # Determine profile
    profile = profile_override
    if not profile:
        profile = target_config.get("profile", "")
    if not profile:
        profile = target_config.get("workspace", {}).get("profile", "")
    if not profile:
        profile = bundle.get("workspace", {}).get("profile", "")

    # Determine workspace host
    workspace_host = target_config.get("workspace", {}).get("host", "")
    if not workspace_host:
        workspace_host = bundle.get("workspace", {}).get("host", "")

    return {
        "target": target,
        "profile": profile,
        "workspace_host": workspace_host,
        "variables": variables,
        "available_targets": available_targets,
    }


def _validate_config(config: dict[str, Any]) -> list[str]:
    """
    Validate that all required variables are set and not placeholders.

    Returns a list of error messages (empty = valid).
    """
    errors = []
    variables = config["variables"]

    for var_name in REQUIRED_VARIABLES:
        value = variables.get(var_name, "")
        if value in PLACEHOLDER_VALUES or "CHANGEME" in value.upper() or "TODO" in value.upper():
            errors.append(f"  Variable '{var_name}' is not set (current: '{value or '(empty)'}')")

    if not config["profile"]:
        errors.append("  No CLI profile configured. Use --profile or set profile in target config.")

    return errors


def _get_var(config: dict, name: str, default: str = "") -> str:
    """Get a resolved variable from config."""
    return config["variables"].get(name, default)


# ═══════════════════════════════════════════════════════════════════════════════
# Step: config
# ═══════════════════════════════════════════════════════════════════════════════

def _step_config(config: dict, dry_run: bool) -> None:
    """Load and validate target configuration."""
    _header("config", "Loading target configuration")

    _info(f"Target:    {config['target']}")
    _info(f"Profile:   {config['profile'] or '(not set)'}")
    _info(f"Workspace: {config['workspace_host'] or '(not set)'}")
    _info(f"Variables: {len(config['variables'])} defined")

    # Print resolved variables
    print()
    for name, value in sorted(config["variables"].items()):
        is_placeholder = value in PLACEHOLDER_VALUES
        display_val = value or "(empty)"
        if is_placeholder:
            print(f"    {name}: {_yellow(display_val)}")
        else:
            print(f"    {name}: {_green(display_val)}")

    # Validate
    print()
    errors = _validate_config(config)
    if errors:
        _warn("Validation warnings (some steps may fail):")
        for err in errors:
            print(f"    {_yellow(err)}")
    else:
        _success("All required variables are set")


# ═══════════════════════════════════════════════════════════════════════════════
# Step: template
# ═══════════════════════════════════════════════════════════════════════════════

def _step_template(config: dict, dry_run: bool) -> None:
    """Generate app/app.yaml from target variables."""
    _header("template", "Generating app/app.yaml")

    v = config["variables"]
    warehouse_id = v.get("warehouse_id", "TODO")
    catalog = v.get("catalog", "TODO")
    schema = v.get("schema", "TODO")
    mas_tile_id = v.get("mas_tile_id", "TODO")
    genie_space_id = v.get("genie_space_id", "TODO")
    ka_tile_id = v.get("ka_tile_id", "TODO")
    demo_name = v.get("demo_name", "TODO")
    demo_customer = v.get("demo_customer", "TODO")
    lakebase_instance = v.get("lakebase_instance", "TODO")
    lakebase_database = v.get("lakebase_database", "TODO")

    # Build MAS endpoint name (first 8 chars of tile ID)
    mas_endpoint_name = f"mas-{mas_tile_id[:8]}-endpoint" if mas_tile_id and mas_tile_id != "TODO" else "mas-TODO-endpoint"

    app_yaml_content = textwrap.dedent(f"""\
        command:
          - uvicorn
          - backend.main:app
          - --host
          - 0.0.0.0
          - --port
          - 8000

        env:
          - name: DATABRICKS_WAREHOUSE_ID
            value: "{warehouse_id}"
          - name: CATALOG
            value: "{catalog}"
          - name: SCHEMA
            value: "{schema}"
          - name: MAS_TILE_ID
            value: "{mas_tile_id}"
          - name: GENIE_SPACE_ID
            value: "{genie_space_id}"
          - name: KA_TILE_ID
            value: "{ka_tile_id}"
          - name: DEMO_NAME
            value: "{demo_name}"
          - name: DEMO_CUSTOMER
            value: "{demo_customer}"

        resources:
          - name: sql-warehouse
            sql_warehouse:
              id: "{warehouse_id}"
              permission: CAN_USE
          - name: mas-endpoint
            serving_endpoint:
              name: "{mas_endpoint_name}"
              permission: CAN_QUERY
          - name: database
            database:
              instance_name: "{lakebase_instance}"
              database_name: "{lakebase_database}"
              permission: CAN_CONNECT_AND_CREATE
    """)

    app_yaml_path = PROJECT_ROOT / "app" / "app.yaml"

    if dry_run:
        _info(f"Would write {app_yaml_path}")
        _info("Content preview:")
        for line in app_yaml_content.strip().split("\n")[:10]:
            print(f"      {_dim(line)}")
        _info("  ...")
        return

    app_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(app_yaml_path, "w") as f:
        f.write(app_yaml_content)

    _success(f"Generated {app_yaml_path}")

    # Count TODOs remaining
    todo_count = app_yaml_content.count("TODO")
    if todo_count > 0:
        _warn(f"{todo_count} TODO placeholders remain — set variables in databricks.yml")
    else:
        _success("All placeholders resolved")


# ═══════════════════════════════════════════════════════════════════════════════
# Step: lakebase
# ═══════════════════════════════════════════════════════════════════════════════

def _step_lakebase(config: dict, dry_run: bool) -> None:
    """Create Lakebase instance, database, and apply schemas."""
    _header("lakebase", "Provisioning Lakebase")

    profile = config["profile"]
    instance = _get_var(config, "lakebase_instance")
    database = _get_var(config, "lakebase_database")

    if not instance or instance in PLACEHOLDER_VALUES:
        _error("lakebase_instance variable is not set")
        sys.exit(1)

    if not database or database in PLACEHOLDER_VALUES:
        _error("lakebase_database variable is not set")
        sys.exit(1)

    # Validate instance name uses hyphens (Gotcha #5)
    if "_" in instance:
        _error(f"Lakebase instance name '{instance}' contains underscores.")
        _error("Instance names MUST use hyphens, not underscores (Gotcha #5).")
        _info(f"Suggested fix: {instance.replace('_', '-')}")
        sys.exit(1)

    # ── Check if instance exists ──
    _info(f"Checking if instance '{instance}' exists...")

    instance_data = _run_cli(
        ["databricks", "database", "get-database-instance", instance, f"--profile={profile}", "-o", "json"],
        dry_run=dry_run,
        capture_json=True,
        ignore_errors=True,
    )

    if dry_run:
        _info("Would check instance state and create if needed")
    elif instance_data and isinstance(instance_data, dict):
        state = instance_data.get("state", "UNKNOWN")
        _info(f"Instance exists, state: {state}")

        if state == "AVAILABLE":
            _success(f"Instance '{instance}' is AVAILABLE")
        elif state in ("STARTING", "CREATING"):
            _info("Instance is starting, waiting for AVAILABLE state...")
            _poll_lakebase_instance(instance, profile)
        else:
            _warn(f"Instance state is '{state}' — may need manual intervention")
    else:
        # Instance doesn't exist — create it
        _info(f"Creating Lakebase instance '{instance}' (capacity: CU_1)...")
        _info("This typically takes 4-6 minutes.")

        _run_cli(
            ["databricks", "database", "create-database-instance", instance,
             "--capacity", "CU_1", f"--profile={profile}"],
            dry_run=dry_run,
        )

        if not dry_run:
            _poll_lakebase_instance(instance, profile)

    # ── Check if database exists ──
    _info(f"Checking if database '{database}' exists...")

    if dry_run:
        _info(f"Would create database '{database}' if it doesn't exist")
    else:
        # Try to connect to the database — if it fails, create it
        check_result = _run_cli(
            ["databricks", "psql", instance, f"--profile={profile}", "--",
             "-d", database, "-c", "SELECT 1;"],
            dry_run=dry_run,
            ignore_errors=True,
        )

        if check_result is None:
            _info(f"Creating database '{database}'...")
            _run_cli(
                ["databricks", "psql", instance, f"--profile={profile}", "--",
                 "-c", f"CREATE DATABASE {database};"],
                dry_run=dry_run,
                ignore_errors=True,  # Ignore if database already exists
            )
            _success(f"Database '{database}' created")
        else:
            _success(f"Database '{database}' already exists")

    # ── Apply schemas ──
    core_schema_path = PROJECT_ROOT / "lakebase" / "core_schema.sql"
    domain_schema_path = PROJECT_ROOT / "lakebase" / "domain_schema.sql"

    if core_schema_path.exists():
        _info("Applying core_schema.sql...")
        _run_cli(
            ["databricks", "psql", instance, f"--profile={profile}", "--",
             "-d", database, "-f", str(core_schema_path)],
            dry_run=dry_run,
        )
        if not dry_run:
            _success("core_schema.sql applied")
    else:
        _warn(f"core_schema.sql not found at {core_schema_path}")

    if domain_schema_path.exists():
        # Check if domain_schema.sql has actual content (not just comments)
        with open(domain_schema_path) as f:
            content = f.read()
        # Strip comments and whitespace to check for real SQL
        stripped = re.sub(r'--[^\n]*', '', content)
        stripped = stripped.strip()
        if stripped:
            _info("Applying domain_schema.sql...")
            _run_cli(
                ["databricks", "psql", instance, f"--profile={profile}", "--",
                 "-d", database, "-f", str(domain_schema_path)],
                dry_run=dry_run,
            )
            if not dry_run:
                _success("domain_schema.sql applied")
        else:
            _info("domain_schema.sql has no active SQL — skipping")
    else:
        _info("No domain_schema.sql found — skipping")

    # ── Summary ──
    print()
    _success(f"Lakebase ready: instance={instance}, database={database}")


def _poll_lakebase_instance(instance: str, profile: str) -> None:
    """
    Poll a Lakebase instance until it reaches AVAILABLE state.

    IMPORTANT: Check for AVAILABLE, NOT RUNNING (Gotcha #33).
    """
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > LAKEBASE_POLL_TIMEOUT:
            _error(f"Timed out waiting for instance '{instance}' after {LAKEBASE_POLL_TIMEOUT}s")
            _info("Check manually: databricks database get-database-instance "
                  f"{instance} --profile={profile} -o json")
            sys.exit(1)

        data = _run_cli(
            ["databricks", "database", "get-database-instance", instance,
             f"--profile={profile}", "-o", "json"],
            capture_json=True,
            ignore_errors=True,
        )

        if data and isinstance(data, dict):
            state = data.get("state", "UNKNOWN")
            _info(f"Instance state: {state} ({int(elapsed)}s elapsed)")

            if state == "AVAILABLE":
                _success(f"Instance '{instance}' is AVAILABLE")
                return
            elif state in ("FAILED", "DELETED", "ERROR"):
                _error(f"Instance entered terminal state: {state}")
                _info(f"Full response: {json.dumps(data, indent=2)[:500]}")
                sys.exit(1)
        else:
            _warn(f"Could not check instance state ({int(elapsed)}s elapsed)")

        time.sleep(LAKEBASE_POLL_INTERVAL)


# ═══════════════════════════════════════════════════════════════════════════════
# Step: data
# ═══════════════════════════════════════════════════════════════════════════════

def _step_data(config: dict, dry_run: bool) -> None:
    """Print instructions for running data setup notebooks."""
    _header("data", "Data Setup Notebooks")

    catalog = _get_var(config, "catalog")
    schema = _get_var(config, "schema")
    workspace_host = config.get("workspace_host", "")

    notebooks_dir = PROJECT_ROOT / "notebooks"
    notebooks = sorted(notebooks_dir.glob("*.py")) + sorted(notebooks_dir.glob("*.sql"))

    if not notebooks:
        _warn("No notebooks found in notebooks/ directory")
        return

    # Check if notebooks are customized (not just TODOs)
    customized = False
    for nb in notebooks:
        with open(nb) as f:
            content = f.read()
        if "TODO_CATALOG" not in content and "TODO_SCHEMA" not in content:
            customized = True
            break

    if not customized:
        _warn("Notebooks not yet customized -- skip this step for now.")
        _info(f"Update CATALOG and SCHEMA values in notebooks/ to:")
        _info(f"  CATALOG = \"{catalog}\"")
        _info(f"  SCHEMA  = \"{schema}\"")
        return

    _info("The following notebooks should be run in the workspace notebook UI:")
    _info("(Serverless runtimes have auth issues with programmatic execution)")
    print()

    for i, nb in enumerate(notebooks, 1):
        rel_path = nb.relative_to(PROJECT_ROOT)
        print(f"    {_bold(f'{i}.')} {rel_path}")

    print()

    if workspace_host:
        _info(f"Workspace: {workspace_host}")
    _info("Run them in order using the notebook UI.")
    _info("Make sure to set CATALOG and SCHEMA before running:")
    _info(f"  CATALOG = \"{catalog}\"")
    _info(f"  SCHEMA  = \"{schema}\"")


# ═══════════════════════════════════════════════════════════════════════════════
# Step: ai
# ═══════════════════════════════════════════════════════════════════════════════

def _step_ai(config: dict, dry_run: bool) -> None:
    """Print instructions for creating Genie Space, MAS, and KA."""
    _header("ai", "AI Layer Setup")

    profile = config["profile"]
    catalog = _get_var(config, "catalog")
    schema = _get_var(config, "schema")
    warehouse_id = _get_var(config, "warehouse_id")
    demo_name = _get_var(config, "demo_name")

    _info("The AI layer requires interactive setup. Follow these steps:")
    print()

    # ── Genie Space ──
    print(f"  {_bold('1. Create Genie Space')}")
    print()
    print(f"     # Create blank space:")
    print(f"     databricks api post /api/2.0/genie/spaces --json '{{")
    print(f'       "serialized_space": "{{\\"version\\": 2}}",')
    print(f'       "warehouse_id": "{warehouse_id}"')
    print(f"     }}' --profile={profile}")
    print()
    print(f"     # PATCH title:")
    print(f"     databricks api patch /api/2.0/genie/spaces/<space_id> --json '{{")
    print(f'       "title": "{demo_name} Data Space"')
    print(f"     }}' --profile={profile}")
    print()
    print(f"     # PATCH tables (sorted, dotted identifiers in serialized_space):")
    print(f"     databricks api patch /api/2.0/genie/spaces/<space_id> --json '{{")
    print(f'       "serialized_space": "{{\\"version\\":2,\\"data_sources\\":'
          f'{{\\"tables\\":[{{\\"identifier\\":\\"{catalog}.{schema}.<table1>\\"}}'
          f',{{\\"identifier\\":\\"{catalog}.{schema}.<table2>\\"}}]}}}}"')
    print(f"     }}' --profile={profile}")
    print()
    print(f"     # Grant CAN_RUN (endpoint is /genie/<id>, NOT /genie/spaces/<id>):")
    print(f"     databricks api patch /api/2.0/permissions/genie/<space_id> --json '{{")
    print(f'       "access_control_list": [{{"group_name": "users", "permission_level": "CAN_RUN"}}]')
    print(f"     }}' --profile={profile}")
    print()

    # ── MAS ──
    print(f"  {_bold('2. Create Multi-Agent Supervisor (MAS)')}")
    print()
    print(f"     # Create via POST (without MCP agents — add those via PATCH):")
    print(f"     databricks api post /api/2.0/multi-agent-supervisors --json '{{")
    print(f'       "name": "{demo_name} Advisor",')
    print(f'       "agents": [')
    print(f'         {{"agent_type": "genie-space", "genie_space": {{"id": "<space_id>"}}, '
          f'"name": "{demo_name.lower().replace(" ", "-")}-data", '
          f'"description": "Query {demo_name} data"}}')
    print(f"       ]")
    print(f"     }}' --profile={profile}")
    print()
    print(f"     # Discover MAS tile ID:")
    print(f"     databricks api get /api/2.0/serving-endpoints --profile={profile} | \\")
    print(f"       jq '.endpoints[] | select(.name | startswith(\"mas-\")) | .tile_endpoint_metadata.tile_id'")
    print()

    # ── Knowledge Assistant ──
    print(f"  {_bold('3. Create Knowledge Assistant (optional)')}")
    print()
    print(f"     # Create via workspace UI or API")
    print(f"     # Add as sub-agent to MAS via PATCH")
    print()

    # ── Update config ──
    print(f"  {_bold('4. Update your target config')}")
    print()
    print(f"     After creating Genie Space and MAS, update databricks.yml:")
    print(f"       genie_space_id: <space_id>")
    print(f"       mas_tile_id: <first 8 chars of tile UUID>")
    print(f"       ka_tile_id: <knowledge assistant ID>")
    print()
    print(f"     Then re-run: python scripts/deploy.py --target {config['target']} --step template")


# ═══════════════════════════════════════════════════════════════════════════════
# Step: deploy
# ═══════════════════════════════════════════════════════════════════════════════

def _step_deploy(config: dict, dry_run: bool, skip_dabs: bool = False) -> None:
    """Deploy the app via DABs or direct CLI."""
    _header("deploy", "Deploying Application")

    profile = config["profile"]
    target = config["target"]
    app_name = _get_var(config, "app_name")

    if not app_name or app_name in PLACEHOLDER_VALUES:
        _error("app_name variable is not set")
        sys.exit(1)

    if skip_dabs:
        _deploy_direct_cli(config, dry_run)
    else:
        _deploy_dabs(config, dry_run)

    # Wait for app to be RUNNING
    if not dry_run:
        _poll_app_running(app_name, profile)


def _deploy_dabs(config: dict, dry_run: bool) -> None:
    """Deploy via Databricks Asset Bundles."""
    target = config["target"]

    _info(f"Deploying via DABs (target: {target})")

    try:
        _run_cli(
            ["databricks", "bundle", "deploy", "--target", target],
            dry_run=dry_run,
            timeout=600,
        )
        if not dry_run:
            _success("DABs deploy complete")
    except CLIError as e:
        if "not found" in e.stderr.lower() or "no such" in e.stderr.lower():
            _warn("DABs not available or bundle not configured")
            _info("Falling back to direct CLI deploy...")
            _deploy_direct_cli(config, dry_run)
        else:
            _error(f"DABs deploy failed:\n{e.stderr}")
            sys.exit(1)


def _deploy_direct_cli(config: dict, dry_run: bool) -> None:
    """Deploy via direct Databricks CLI (sync + deploy)."""
    profile = config["profile"]
    app_name = _get_var(config, "app_name")
    workspace_email = _get_var(config, "workspace_email", "")

    if not workspace_email:
        # Try to get current user email
        _info("Getting current user email...")
        user_data = _run_cli(
            ["databricks", "current-user", "me", f"--profile={profile}", "-o", "json"],
            dry_run=dry_run,
            capture_json=True,
            ignore_errors=True,
        )
        if user_data and isinstance(user_data, dict):
            workspace_email = user_data.get("userName", "")
        if not workspace_email:
            _error("Could not determine workspace email. Set workspace_email variable or use --profile.")
            sys.exit(1)

    workspace_path = f"/Workspace/Users/{workspace_email}/demos/{app_name}/app"

    _info(f"Syncing app code to {workspace_path}")
    app_dir = PROJECT_ROOT / "app"

    _run_cli(
        ["databricks", "sync", str(app_dir), workspace_path,
         f"--profile={profile}", "--watch=false"],
        dry_run=dry_run,
        timeout=120,
    )

    if not dry_run:
        _success("Code synced")

    # Create app (ignore error if it already exists)
    _info(f"Creating app '{app_name}' (if it doesn't exist)...")
    _run_cli(
        ["databricks", "apps", "create", app_name, f"--profile={profile}"],
        dry_run=dry_run,
        ignore_errors=True,
    )

    # Deploy
    _info(f"Deploying app '{app_name}'...")
    _run_cli(
        ["databricks", "apps", "deploy", app_name,
         "--source-code-path", workspace_path,
         f"--profile={profile}"],
        dry_run=dry_run,
        timeout=300,
    )

    if not dry_run:
        _success(f"App '{app_name}' deployed")


def _poll_app_running(app_name: str, profile: str) -> None:
    """Poll until the app reaches RUNNING state."""
    _info(f"Waiting for app '{app_name}' to reach RUNNING state...")
    start = time.time()

    while True:
        elapsed = time.time() - start
        if elapsed > APP_POLL_TIMEOUT:
            _warn(f"Timed out waiting for app after {APP_POLL_TIMEOUT}s")
            _info("Check manually: databricks apps get "
                  f"{app_name} --profile={profile} -o json")
            return

        data = _run_cli(
            ["databricks", "apps", "get", app_name, f"--profile={profile}", "-o", "json"],
            capture_json=True,
            ignore_errors=True,
        )

        if data and isinstance(data, dict):
            # App status can be in different fields depending on CLI version
            status = data.get("status", {})
            if isinstance(status, dict):
                state = status.get("state", "UNKNOWN")
            else:
                state = str(status) if status else "UNKNOWN"

            # Also check compute_status or active_deployment
            if state == "UNKNOWN":
                active = data.get("active_deployment", {})
                if isinstance(active, dict):
                    deploy_status = active.get("status", {})
                    if isinstance(deploy_status, dict):
                        state = deploy_status.get("state", "UNKNOWN")

            _info(f"App state: {state} ({int(elapsed)}s elapsed)")

            if state in ("RUNNING", "SUCCEEDED"):
                _success(f"App '{app_name}' is running")
                return
            elif state in ("FAILED", "ERROR", "CRASHED"):
                _error(f"App entered terminal state: {state}")
                app_url = data.get("url", "")
                if app_url:
                    _info(f"Check logs at: {app_url}/logz")
                sys.exit(1)

        time.sleep(APP_POLL_INTERVAL)


# ═══════════════════════════════════════════════════════════════════════════════
# Step: resources
# ═══════════════════════════════════════════════════════════════════════════════

def _step_resources(config: dict, dry_run: bool, skip_dabs: bool = False) -> None:
    """
    Register app resources via API and redeploy.

    CRITICAL: `databricks apps deploy` clears resources (Gotcha #45).
    Resources MUST be registered after deploy, then app must be redeployed
    so that PGHOST/PGPORT/PGDATABASE/PGUSER env vars are injected (Gotcha #23).
    """
    _header("resources", "Registering App Resources")

    profile = config["profile"]
    app_name = _get_var(config, "app_name")
    warehouse_id = _get_var(config, "warehouse_id")
    mas_tile_id = _get_var(config, "mas_tile_id")
    lakebase_instance = _get_var(config, "lakebase_instance")
    lakebase_database = _get_var(config, "lakebase_database")

    if not app_name or app_name in PLACEHOLDER_VALUES:
        _error("app_name variable is not set")
        sys.exit(1)

    # Build resources array — always include warehouse and database
    resources = []

    if warehouse_id and warehouse_id not in PLACEHOLDER_VALUES:
        resources.append({
            "name": "sql-warehouse",
            "sql_warehouse": {
                "id": warehouse_id,
                "permission": "CAN_USE",
            },
        })
    else:
        _warn("warehouse_id not set — skipping sql-warehouse resource")

    # MAS endpoint (optional — may not be set up yet)
    if mas_tile_id and mas_tile_id not in PLACEHOLDER_VALUES:
        mas_endpoint_name = f"mas-{mas_tile_id[:8]}-endpoint"
        resources.append({
            "name": "mas-endpoint",
            "serving_endpoint": {
                "name": mas_endpoint_name,
                "permission": "CAN_QUERY",
            },
        })
    else:
        _info("mas_tile_id not set — skipping MAS endpoint resource (set it after AI layer setup)")

    # Database resource — always include
    if lakebase_instance and lakebase_instance not in PLACEHOLDER_VALUES:
        resources.append({
            "name": "database",
            "database": {
                "instance_name": lakebase_instance,
                "database_name": lakebase_database,
                "permission": "CAN_CONNECT_AND_CREATE",
            },
        })
    else:
        _warn("lakebase_instance not set — skipping database resource")

    if not resources:
        _error("No resources to register. Set warehouse_id and lakebase_instance at minimum.")
        sys.exit(1)

    _info(f"Registering {len(resources)} resource(s):")
    for res in resources:
        _info(f"  - {res['name']}")

    # Register via databricks apps update
    payload = json.dumps({"resources": resources})

    _run_cli(
        ["databricks", "apps", "update", app_name, "--json", payload, f"--profile={profile}"],
        dry_run=dry_run,
    )

    if not dry_run:
        _success("Resources registered")

    # REDEPLOY — PGHOST is only injected at deploy time (Gotcha #23)
    _warn("Redeploying to inject PGHOST/PGPORT/PGDATABASE/PGUSER env vars...")

    if skip_dabs:
        # Get the workspace path for direct deploy
        workspace_email = _get_var(config, "workspace_email", "")
        if not workspace_email:
            user_data = _run_cli(
                ["databricks", "current-user", "me", f"--profile={profile}", "-o", "json"],
                dry_run=dry_run,
                capture_json=True,
                ignore_errors=True,
            )
            if user_data and isinstance(user_data, dict):
                workspace_email = user_data.get("userName", "")

        if workspace_email:
            workspace_path = f"/Workspace/Users/{workspace_email}/demos/{app_name}/app"
            _run_cli(
                ["databricks", "apps", "deploy", app_name,
                 "--source-code-path", workspace_path,
                 f"--profile={profile}"],
                dry_run=dry_run,
                timeout=300,
            )
        else:
            _warn("Could not determine workspace path for redeploy.")
            _info(f"Run manually: databricks apps deploy {app_name} --source-code-path <path> --profile={profile}")
    else:
        _run_cli(
            ["databricks", "bundle", "deploy", "--target", config["target"]],
            dry_run=dry_run,
            timeout=600,
            ignore_errors=True,
        )

    if not dry_run:
        _success("Redeployed with resource env vars")
        _poll_app_running(app_name, profile)


# ═══════════════════════════════════════════════════════════════════════════════
# Step: permissions
# ═══════════════════════════════════════════════════════════════════════════════

def _step_permissions(config: dict, dry_run: bool) -> None:
    """Grant all required permissions to the app service principal."""
    _header("permissions", "Granting Permissions")

    profile = config["profile"]
    app_name = _get_var(config, "app_name")
    catalog = _get_var(config, "catalog")
    schema = _get_var(config, "schema")
    warehouse_id = _get_var(config, "warehouse_id")
    mas_tile_id = _get_var(config, "mas_tile_id")
    lakebase_instance = _get_var(config, "lakebase_instance")
    lakebase_database = _get_var(config, "lakebase_database")

    if not app_name or app_name in PLACEHOLDER_VALUES:
        _error("app_name variable is not set")
        sys.exit(1)

    # ── Get app SP client ID ──
    _info("Getting app service principal client ID...")
    app_data = _run_cli(
        ["databricks", "apps", "get", app_name, f"--profile={profile}", "-o", "json"],
        dry_run=dry_run,
        capture_json=True,
    )

    sp_client_id = None
    if app_data and isinstance(app_data, dict):
        sp_client_id = app_data.get("service_principal_client_id", "")

    if dry_run:
        sp_client_id = "<SP_CLIENT_ID>"
        _info(f"Would retrieve SP client ID from app '{app_name}'")

    if not sp_client_id:
        _error(f"Could not get service_principal_client_id from app '{app_name}'")
        _info("Is the app created and deployed?")
        sys.exit(1)

    _info(f"App SP client ID: {sp_client_id}")
    print()

    # ── Grant catalog/schema permissions via SQL ──
    if catalog and catalog not in PLACEHOLDER_VALUES and schema and schema not in PLACEHOLDER_VALUES:
        _info("Granting Unity Catalog permissions...")

        grants = [
            f"GRANT USE CATALOG ON CATALOG {catalog} TO `{sp_client_id}`",
            f"GRANT USE SCHEMA ON SCHEMA {catalog}.{schema} TO `{sp_client_id}`",
            f"GRANT SELECT ON SCHEMA {catalog}.{schema} TO `{sp_client_id}`",
        ]

        for grant_sql in grants:
            _run_cli(
                ["databricks", "api", "post", "/api/2.0/sql/statements", "--json",
                 json.dumps({
                     "warehouse_id": warehouse_id,
                     "statement": grant_sql,
                     "wait_timeout": "30s",
                 }),
                 f"--profile={profile}"],
                dry_run=dry_run,
                ignore_errors=True,
            )

        if not dry_run:
            _success("Catalog/schema permissions granted")
    else:
        _warn("catalog/schema not set — skipping UC permission grants")

    # ── Grant CAN_USE on SQL warehouse ──
    if warehouse_id and warehouse_id not in PLACEHOLDER_VALUES:
        _info("Granting CAN_USE on SQL warehouse...")
        _run_cli(
            ["databricks", "api", "patch",
             f"/api/2.0/permissions/sql/warehouses/{warehouse_id}",
             "--json", json.dumps({
                 "access_control_list": [{
                     "service_principal_name": sp_client_id,
                     "permission_level": "CAN_USE",
                 }],
             }),
             f"--profile={profile}"],
            dry_run=dry_run,
            ignore_errors=True,
        )
        if not dry_run:
            _success("SQL warehouse CAN_USE granted")
    else:
        _warn("warehouse_id not set — skipping warehouse permission grant")

    # ── Grant CAN_QUERY on MAS endpoint ──
    if mas_tile_id and mas_tile_id not in PLACEHOLDER_VALUES:
        _info("Granting CAN_QUERY on MAS serving endpoint...")
        _info("Looking up endpoint UUID (Gotcha #25 — must use UUID, not name)...")

        # Get all serving endpoints to find the MAS one
        endpoints_data = _run_cli(
            ["databricks", "api", "get", "/api/2.0/serving-endpoints",
             f"--profile={profile}"],
            dry_run=dry_run,
            capture_json=True,
            ignore_errors=True,
        )

        endpoint_uuid = None
        mas_endpoint_name = f"mas-{mas_tile_id[:8]}-endpoint"

        if endpoints_data and isinstance(endpoints_data, dict):
            for ep in endpoints_data.get("endpoints", []):
                if ep.get("name") == mas_endpoint_name:
                    endpoint_uuid = ep.get("id")
                    break

        if endpoint_uuid:
            _run_cli(
                ["databricks", "api", "patch",
                 f"/api/2.0/permissions/serving-endpoints/{endpoint_uuid}",
                 "--json", json.dumps({
                     "access_control_list": [{
                         "service_principal_name": sp_client_id,
                         "permission_level": "CAN_QUERY",
                     }],
                 }),
                 f"--profile={profile}"],
                dry_run=dry_run,
                ignore_errors=True,
            )
            if not dry_run:
                _success(f"CAN_QUERY granted on endpoint {mas_endpoint_name} (UUID: {endpoint_uuid})")
        elif dry_run:
            _info(f"Would grant CAN_QUERY on endpoint '{mas_endpoint_name}'")
        else:
            _warn(f"Could not find endpoint '{mas_endpoint_name}' — grant CAN_QUERY manually")
            _info("Ensure the MAS is deployed and the endpoint name matches.")
    else:
        _info("mas_tile_id not set — skipping MAS endpoint permission (set after AI layer setup)")

    # ── Grant Lakebase table access ──
    if (lakebase_instance and lakebase_instance not in PLACEHOLDER_VALUES
            and lakebase_database and lakebase_database not in PLACEHOLDER_VALUES):
        _info("Granting Lakebase table access to app SP...")
        _info("(Requires app resource registration + redeploy first — Gotcha #35)")

        lakebase_grants_sql = f"""
GRANT ALL ON ALL TABLES IN SCHEMA public TO "{sp_client_id}";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{sp_client_id}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{sp_client_id}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{sp_client_id}";
"""
        _run_cli(
            ["databricks", "psql", lakebase_instance, f"--profile={profile}", "--",
             "-d", lakebase_database, "-c", lakebase_grants_sql],
            dry_run=dry_run,
            ignore_errors=True,
        )
        if not dry_run:
            _success("Lakebase table permissions granted")
    else:
        _warn("lakebase_instance/database not set — skipping Lakebase grants")

    # ── Summary ──
    print()
    _success(f"Permissions configured for SP: {sp_client_id}")
    _info("Save this SP client ID for reference.")


# ═══════════════════════════════════════════════════════════════════════════════
# Step: verify
# ═══════════════════════════════════════════════════════════════════════════════

def _step_verify(config: dict, dry_run: bool) -> None:
    """Verify the deployed app by checking health endpoint."""
    _header("verify", "Verifying Deployment")

    profile = config["profile"]
    app_name = _get_var(config, "app_name")

    if not app_name or app_name in PLACEHOLDER_VALUES:
        _error("app_name variable is not set")
        sys.exit(1)

    # Get app URL
    app_data = _run_cli(
        ["databricks", "apps", "get", app_name, f"--profile={profile}", "-o", "json"],
        dry_run=dry_run,
        capture_json=True,
    )

    app_url = ""
    if app_data and isinstance(app_data, dict):
        app_url = app_data.get("url", "")

    if dry_run:
        app_url = "https://<app-name>.aws.databricksapps.com"

    if app_url:
        _success(f"App URL: {app_url}")
    else:
        _warn("Could not determine app URL")
        _info(f"Check: databricks apps get {app_name} --profile={profile} -o json")

    print()
    _info("Open in browser (OAuth required) and check /api/health")
    _info("")
    if app_url:
        _info(f"  App:    {app_url}")
        _info(f"  Health: {app_url}/api/health")
        _info(f"  Logs:   {app_url}/logz")
    _info("")
    _info("Expected health response:")
    _info('  {"status": "healthy", "checks": {"sdk": "ok", "sql_warehouse": "ok", "lakebase": "ok"}}')
    print()
    _info("If health shows 'degraded', check:")
    _info("  sdk:           App SP can authenticate (usually means resource registration issue)")
    _info("  sql_warehouse: CAN_USE granted + warehouse resource registered")
    _info("  lakebase:      Database resource registered + redeployed + SP granted table access")


# ═══════════════════════════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

def _print_summary(completed_steps: list[str], skipped_steps: list[str], failed_step: Optional[str]) -> None:
    """Print a summary of what was done."""
    print()
    print(f"  {'═' * 60}")
    print(f"  {_bold('DEPLOYMENT SUMMARY')}")
    print(f"  {'═' * 60}")

    if completed_steps:
        for step in completed_steps:
            print(f"    {_green('done')}  {step}")

    if skipped_steps:
        for step in skipped_steps:
            print(f"    {_dim('skip')}  {step}")

    if failed_step:
        print(f"    {_red('FAIL')}  {failed_step}")

    print(f"  {'═' * 60}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vibe Demo Accelerator — Deployment Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Steps (run in order by default):
              config      Load target config and validate
              template    Generate app/app.yaml from target variables
              lakebase    Create Lakebase instance + database + apply schemas
              data        Run setup notebooks (prints instructions)
              ai          Create Genie Space + MAS (prints instructions)
              deploy      Run databricks bundle deploy
              resources   Register app resources via API + redeploy
              permissions Grant CAN_USE, CAN_QUERY, catalog/schema permissions
              verify      Check /api/health endpoint

            Examples:
              # Full deploy to dev target:
              python scripts/deploy.py --target dev

              # Just provision Lakebase:
              python scripts/deploy.py --target dev --step lakebase

              # Deploy + register resources (after code changes):
              python scripts/deploy.py --target dev --step deploy --step resources

              # Dry run to see what would happen:
              python scripts/deploy.py --target dev --dry-run

              # Use direct CLI instead of DABs:
              python scripts/deploy.py --target dev --skip-dabs
        """),
    )

    parser.add_argument(
        "--target", "-t",
        required=True,
        help="Target name from databricks.yml (e.g., dev, staging, prod)",
    )
    parser.add_argument(
        "--step", "-s",
        action="append",
        choices=ALL_STEPS,
        help="Run specific step(s) only. Can repeat: --step lakebase --step deploy",
    )
    parser.add_argument(
        "--profile", "-p",
        help="Override Databricks CLI profile (defaults to target config)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print what would be done without executing",
    )
    parser.add_argument(
        "--skip-dabs",
        action="store_true",
        help="Skip DABs, use direct CLI deploy instead",
    )

    args = parser.parse_args()

    # ── Banner ──
    print()
    print(f"  {_bold('Vibe Demo Accelerator — Deploy')}")
    if args.dry_run:
        print(f"  {_yellow('DRY RUN — no changes will be made')}")
    print()

    # ── Determine steps to run ──
    steps_to_run = args.step if args.step else ALL_STEPS

    # Always run config first (even if not explicitly requested)
    if "config" not in steps_to_run and steps_to_run != ALL_STEPS:
        steps_to_run = ["config"] + list(steps_to_run)

    # ── Load config ──
    config = _load_config(args.target, args.profile)

    # ── Execute steps ──
    step_dispatch = {
        "config":      lambda: _step_config(config, args.dry_run),
        "template":    lambda: _step_template(config, args.dry_run),
        "lakebase":    lambda: _step_lakebase(config, args.dry_run),
        "data":        lambda: _step_data(config, args.dry_run),
        "ai":          lambda: _step_ai(config, args.dry_run),
        "deploy":      lambda: _step_deploy(config, args.dry_run, args.skip_dabs),
        "resources":   lambda: _step_resources(config, args.dry_run, args.skip_dabs),
        "permissions": lambda: _step_permissions(config, args.dry_run),
        "verify":      lambda: _step_verify(config, args.dry_run),
    }

    completed = []
    skipped = []
    failed = None

    for step in steps_to_run:
        if step not in step_dispatch:
            _warn(f"Unknown step: {step}")
            skipped.append(step)
            continue

        try:
            step_dispatch[step]()
            completed.append(step)
        except CLIError as e:
            _error(str(e))
            if e.stderr:
                print()
                for line in e.stderr.split("\n")[:10]:
                    print(f"    {_red(line)}")
                print()
            if e.stdout:
                for line in e.stdout.split("\n")[:5]:
                    print(f"    {_dim(line)}")
            failed = step
            break
        except SystemExit:
            failed = step
            break
        except KeyboardInterrupt:
            print()
            _warn("Interrupted by user")
            failed = step
            break
        except Exception as e:
            _error(f"Unexpected error in step '{step}': {e}")
            failed = step
            break

    # Mark remaining steps as skipped
    if failed:
        idx = steps_to_run.index(failed) if failed in steps_to_run else len(steps_to_run)
        for remaining_step in steps_to_run[idx + 1:]:
            skipped.append(remaining_step)

    _print_summary(completed, skipped, failed)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
