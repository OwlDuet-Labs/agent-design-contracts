# ADC-IMPLEMENTS: <adc-mcp-tools-01>
"""
ADC MCP Tools — All tool implementations for the ADC MCP server.

Tools are grouped into:
  - Local tools (no AI required): init, lint, validate, health, config, list/parse/find
  - AI-powered tools: generate, audit, refine
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import TextContent, Tool

# ---------------------------------------------------------------------------
# Cache layer — persistent across tool calls within a server session
# ---------------------------------------------------------------------------

_contract_cache: Dict[str, Dict[str, Any]] = {}  # path -> {mtime, data}
_marker_cache: Dict[str, Dict[str, Any]] = {}    # path -> {mtime, markers}


def _cache_valid(cache: Dict, key: str, path: Path) -> bool:
    """Check if a cache entry is still valid based on file mtime."""
    if key not in cache:
        return False
    try:
        current_mtime = path.stat().st_mtime
        return cache[key].get("mtime") == current_mtime
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Helper: resolve project path
# ---------------------------------------------------------------------------

def _resolve_project(project_path: str) -> Path:
    """Resolve project path, defaulting to cwd."""
    if project_path:
        return Path(project_path).expanduser().resolve()
    return Path.cwd()


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _adc_init(project_path: str = "", force: bool = False) -> Dict[str, Any]:
    """Initialize ADC project structure."""
    project = _resolve_project(project_path)
    created = []

    dirs_to_create = ["contracts", "roles", "src"]
    for d in dirs_to_create:
        target = project / d
        if not target.exists() or force:
            target.mkdir(parents=True, exist_ok=True)
            created.append(str(target.relative_to(project)))

    # Create a starter contract README if missing
    contracts_readme = project / "contracts" / "README.md"
    if not contracts_readme.exists() or force:
        contracts_readme.write_text(
            "# ADC Contracts\n\nPlace your Agent Design Contract `.md` files here.\n",
            encoding="utf-8",
        )
        created.append("contracts/README.md")

    return {
        "status": "success",
        "project_path": str(project),
        "created": created,
        "message": f"ADC structure initialized in {project}" if created else "Already initialized",
    }


def _adc_lint(
    path: str = ".",
    project_path: str = "",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Lint and auto-fix contract files."""
    from ..contract_lint import ContractLinter

    project = _resolve_project(project_path)
    target = project / path if not Path(path).is_absolute() else Path(path)

    config = {"dry_run": dry_run, "backup_originals": False, "verbose": False}
    linter = ContractLinter(config)

    if target.is_file():
        result = linter.lint_contract_file(str(target))
        return {
            "status": "success",
            "summary": f"{'1 fix' if result.get('fixes_applied') else 'No fixes'} applied",
            "total_files": 1,
            "files_updated": 1 if result.get("file_updated") else 0,
            "total_fixes": len(result.get("fixes_applied", [])),
            "details": [result],
        }
    else:
        results = linter.run_contract_lint(str(target))
        return {
            "status": "success",
            "summary": f"{results['total_fixes']} fixes across {results['files_updated']}/{results['files_processed']} files",
            **results,
        }


def _adc_validate(project_path: str = "") -> Dict[str, Any]:
    """Validate contract implementations — check ADC-IMPLEMENTS markers."""
    from ..validation.contract_validator import ContractValidator

    project = _resolve_project(project_path)
    src_dir = str(project / "src")
    contracts_dir = str(project / "contracts")

    if not Path(contracts_dir).exists():
        return {"status": "error", "message": f"No contracts/ directory found in {project}"}
    if not Path(src_dir).exists():
        return {"status": "error", "message": f"No src/ directory found in {project}"}

    validator = ContractValidator(src_dir=src_dir, contracts_dir=contracts_dir)
    return validator.validate_all_contracts()


def _adc_health(project_path: str = "") -> Dict[str, Any]:
    """System health check — providers, config, contracts."""
    project = _resolve_project(project_path)

    health = {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_path": str(project),
        "components": {},
        "recommendations": [],
    }

    # Check contracts directory
    contracts_dir = project / "contracts"
    if contracts_dir.exists():
        contract_files = list(contracts_dir.glob("*.md"))
        health["components"]["contracts"] = {
            "status": "ok",
            "count": len(contract_files),
        }
    else:
        health["components"]["contracts"] = {"status": "missing"}
        health["recommendations"].append("Run adc_init to create project structure")

    # Check source directory
    src_dir = project / "src"
    if src_dir.exists():
        py_files = list(src_dir.rglob("*.py"))
        health["components"]["source"] = {
            "status": "ok",
            "python_files": len(py_files),
        }
    else:
        health["components"]["source"] = {"status": "missing"}

    # Check roles
    roles_dir = project / "roles"
    if roles_dir.exists():
        role_files = list(roles_dir.glob("*.md"))
        health["components"]["roles"] = {
            "status": "ok",
            "count": len(role_files),
        }
    else:
        # Try package-bundled roles
        try:
            from importlib import resources
            adc_package = resources.files("adc")
            roles_pkg = adc_package / "roles"
            role_count = sum(1 for f in roles_pkg.iterdir() if str(f).endswith(".md"))
            health["components"]["roles"] = {
                "status": "ok",
                "count": role_count,
                "source": "package",
            }
        except Exception:
            health["components"]["roles"] = {"status": "missing"}
            health["recommendations"].append("No role definitions found")

    # Check AI providers
    providers_available = []
    for env_var, name in [
        ("ANTHROPIC_API_KEY", "anthropic"),
        ("OPENAI_API_KEY", "openai"),
        ("GOOGLE_API_KEY", "gemini"),
    ]:
        if os.environ.get(env_var):
            providers_available.append(name)

    health["components"]["ai_providers"] = {
        "status": "ok" if providers_available else "warning",
        "available": providers_available,
    }
    if not providers_available:
        health["recommendations"].append(
            "Set at least one API key: ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY"
        )

    # Check config
    config_path = Path.home() / ".adcconfig.json"
    health["components"]["config"] = {
        "status": "ok" if config_path.exists() else "default",
        "path": str(config_path),
    }

    # Overall status
    statuses = [c.get("status", "unknown") for c in health["components"].values()]
    if "missing" in statuses or "error" in statuses:
        health["status"] = "degraded"
    elif "warning" in statuses:
        health["status"] = "warning"

    return health


def _adc_config_show() -> Dict[str, Any]:
    """Show current ADC configuration."""
    from ..config import load_config

    config = load_config()
    return {"status": "success", "config": config}


def _adc_config_set(key: str, value: str) -> Dict[str, Any]:
    """Update ADC configuration."""
    from ..config import update_config

    if "." in key:
        main_key, sub_key = key.split(".", 1)
        if main_key == "task_agents":
            success = update_config(**{f"task_{sub_key}": value})
        elif main_key == "models":
            success = update_config(**{f"model_{sub_key}": value})
        else:
            return {"status": "error", "message": f"Unknown config section: {main_key}"}
    else:
        success = update_config(**{key: value})

    return {
        "status": "success" if success else "error",
        "message": f"Set {key} = {value}" if success else "Failed to update config",
    }


def _adc_list_contracts(project_path: str = "") -> Dict[str, Any]:
    """List all contracts with metadata."""
    project = _resolve_project(project_path)
    contracts_dir = project / "contracts"

    if not contracts_dir.exists():
        return {"status": "error", "message": f"No contracts/ directory in {project}"}

    contracts = []
    for f in sorted(contracts_dir.rglob("*.md")):
        if f.name == "README.md":
            continue
        info = {"file": str(f.relative_to(project)), "name": f.stem}

        # Quick metadata extraction
        try:
            content = f.read_text(encoding="utf-8")
            # Extract YAML front matter fields
            fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if fm_match:
                for line in fm_match.group(1).split("\n"):
                    for field in ("contract_id", "title", "status", "version"):
                        m = re.match(rf'{field}:\s*"?([^"\n]+)"?', line.strip())
                        if m:
                            info[field] = m.group(1).strip()

            # Count design blocks
            blocks = re.findall(r"###\s+\[(\w+):", content)
            info["block_count"] = len(blocks)
            info["block_types"] = list(set(blocks))
        except Exception:
            info["error"] = "Could not parse"

        contracts.append(info)

    return {
        "status": "success",
        "project_path": str(project),
        "count": len(contracts),
        "contracts": contracts,
    }


def _adc_parse_contract(
    file_path: str,
    project_path: str = "",
    detailed: bool = False,
) -> Dict[str, Any]:
    """Parse a contract file into structured block data."""
    project = _resolve_project(project_path)
    target = Path(file_path)
    if not target.is_absolute():
        target = project / file_path

    if not target.exists():
        return {"status": "error", "message": f"File not found: {target}"}

    cache_key = str(target)
    if _cache_valid(_contract_cache, cache_key, target):
        return _contract_cache[cache_key]["data"]

    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:
        return {"status": "error", "message": f"Cannot read {target}: {e}"}

    result: Dict[str, Any] = {
        "status": "success",
        "file": str(target.relative_to(project) if target.is_relative_to(project) else target),
        "metadata": {},
        "blocks": [],
    }

    # Parse YAML front matter
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).split("\n"):
            m = re.match(r"(\w[\w_]*)\s*:\s*(.+)", line.strip())
            if m:
                key = m.group(1)
                val = m.group(2).strip().strip('"')
                result["metadata"][key] = val

    # Parse design blocks
    block_pattern = re.compile(
        r"###\s+\[(\w+):\s*([^\]]+)\]\s*<([^>]+)>"
    )
    blocks_raw = list(block_pattern.finditer(content))

    for i, match in enumerate(blocks_raw):
        block: Dict[str, Any] = {
            "type": match.group(1),
            "name": match.group(2).strip(),
            "id": match.group(3).strip(),
            "line": content[: match.start()].count("\n") + 1,
        }

        # Extract block body (until next block or end)
        start = match.end()
        end = blocks_raw[i + 1].start() if i + 1 < len(blocks_raw) else len(content)
        body = content[start:end].strip()

        # Extract parity section
        parity_match = re.search(
            r"\*\*Parity:\*\*\s*\n((?:[-\s]*\*\*[^*]+\*\*.*\n?)+)", body
        )
        if parity_match:
            parity_lines = parity_match.group(1).strip().split("\n")
            parity = {}
            for pl in parity_lines:
                pm = re.match(r"[-\s]*\*\*([^*]+)\*\*:\s*`?([^`\n]+)`?", pl.strip())
                if pm:
                    parity[pm.group(1).strip()] = pm.group(2).strip()
            block["parity"] = parity

        if detailed:
            block["body"] = body[:2000]  # Cap to avoid huge payloads

        result["blocks"].append(block)

    result["summary"] = {
        "total_blocks": len(result["blocks"]),
        "block_types": list(set(b["type"] for b in result["blocks"])),
        "has_parity": sum(1 for b in result["blocks"] if "parity" in b),
    }

    # Cache result
    try:
        _contract_cache[cache_key] = {
            "mtime": target.stat().st_mtime,
            "data": result,
        }
    except OSError:
        pass

    return result


def _adc_find_markers(
    project_path: str = "",
    src_dir: str = "src",
) -> Dict[str, Any]:
    """Find all ADC-IMPLEMENTS markers in source code."""
    project = _resolve_project(project_path)
    source = project / src_dir

    if not source.exists():
        return {"status": "error", "message": f"Source directory not found: {source}"}

    cache_key = str(source)
    # Simple cache check: if the directory mtime hasn't changed
    # (not perfect but good for quick repeat calls)
    if _cache_valid(_marker_cache, cache_key, source):
        return _marker_cache[cache_key]["data"]

    markers: List[Dict[str, str]] = []
    marker_pattern = re.compile(r"#\s*ADC-IMPLEMENTS:\s*<?([^>\s]+)>?")

    for py_file in sorted(source.rglob("*.py")):
        try:
            lines = py_file.read_text(encoding="utf-8").split("\n")
            for line_num, line in enumerate(lines, 1):
                m = marker_pattern.search(line)
                if m:
                    markers.append({
                        "block_id": m.group(1),
                        "file": str(py_file.relative_to(project)),
                        "line": line_num,
                    })
        except Exception:
            continue

    # Group by block_id
    by_block: Dict[str, List[Dict]] = {}
    for marker in markers:
        bid = marker["block_id"]
        if bid not in by_block:
            by_block[bid] = []
        by_block[bid].append({"file": marker["file"], "line": marker["line"]})

    result = {
        "status": "success",
        "project_path": str(project),
        "total_markers": len(markers),
        "unique_block_ids": len(by_block),
        "markers": markers,
        "by_block_id": by_block,
    }

    try:
        _marker_cache[cache_key] = {
            "mtime": source.stat().st_mtime,
            "data": result,
        }
    except OSError:
        pass

    return result


def _adc_get_role(role_name: str, project_path: str = "") -> Dict[str, Any]:
    """Get a specific agent role definition."""
    project = _resolve_project(project_path)

    # Try project-local roles first
    for roles_dir in [project / "roles", project / "src" / "adc" / "roles"]:
        role_file = roles_dir / f"{role_name}.md"
        if role_file.exists():
            return {
                "status": "success",
                "role_name": role_name,
                "source": str(role_file.relative_to(project)),
                "content": role_file.read_text(encoding="utf-8"),
            }

    # Try package-bundled roles
    try:
        from importlib import resources
        adc_package = resources.files("adc")
        role_res = adc_package / "roles" / f"{role_name}.md"
        if role_res.is_file():
            return {
                "status": "success",
                "role_name": role_name,
                "source": "package",
                "content": role_res.read_text(encoding="utf-8"),
            }
    except Exception:
        pass

    return {
        "status": "error",
        "message": f"Role '{role_name}' not found. Use adc_list_roles to see available roles.",
    }


def _adc_list_roles(project_path: str = "") -> Dict[str, Any]:
    """List all available agent roles."""
    project = _resolve_project(project_path)
    roles: List[Dict[str, str]] = []

    # Project-local roles
    for roles_dir in [project / "roles", project / "src" / "adc" / "roles"]:
        if roles_dir.exists():
            for f in sorted(roles_dir.glob("*.md")):
                roles.append({
                    "name": f.stem,
                    "source": str(f.relative_to(project)),
                })

    # Package-bundled roles (if not already found)
    found_names = {r["name"] for r in roles}
    try:
        from importlib import resources
        adc_package = resources.files("adc")
        roles_pkg = adc_package / "roles"
        for f in roles_pkg.iterdir():
            if str(f).endswith(".md") and Path(str(f)).stem not in found_names:
                roles.append({
                    "name": Path(str(f)).stem,
                    "source": "package",
                })
    except Exception:
        pass

    return {
        "status": "success",
        "count": len(roles),
        "roles": roles,
    }


# ---------------------------------------------------------------------------
# AI-powered tools
# ---------------------------------------------------------------------------

def _adc_generate(
    project_path: str = "",
    agent: str = "",
    model: str = "",
) -> Dict[str, Any]:
    """Generate code from contracts using AI."""
    from ..config import load_config
    from ..providers import call_ai_agent

    project = _resolve_project(project_path)
    config = load_config()

    if not agent:
        agent = config["task_agents"].get("generate", config["default_agent"])

    if not model:
        model = config["models"].get(agent, "")

    # Read code generator role
    role_result = _adc_get_role("code_generator", str(project))
    if role_result["status"] != "success":
        return {"status": "error", "message": "Code generator role not found"}
    system_prompt = role_result["content"]

    # Read contracts
    contracts_dir = project / "contracts"
    if not contracts_dir.exists():
        return {"status": "error", "message": f"No contracts/ directory in {project}"}

    contracts_content = ""
    for cf in sorted(contracts_dir.rglob("*.md")):
        if cf.name == "README.md":
            continue
        try:
            contracts_content += f"\n\n=== {cf.name} ===\n"
            contracts_content += cf.read_text(encoding="utf-8")
        except Exception:
            continue

    if not contracts_content.strip():
        return {"status": "error", "message": "No contract content found"}

    user_prompt = f"Please generate code for these ADC contracts:\n{contracts_content}"
    response = call_ai_agent(agent, system_prompt, user_prompt, model)

    if response.startswith("Error:"):
        return {"status": "error", "message": response}

    return {
        "status": "success",
        "agent": agent,
        "model": model,
        "generated_code": response,
    }


def _adc_audit(
    project_path: str = "",
    agent: str = "",
    model: str = "",
    src_dir: str = "src",
) -> Dict[str, Any]:
    """Audit implementation against contracts using AI."""
    from ..config import load_config
    from ..providers import call_ai_agent

    project = _resolve_project(project_path)
    config = load_config()

    if not agent:
        agent = config["task_agents"].get("audit", config["default_agent"])
    if not model:
        model = config["models"].get(agent, "")

    # Read auditor role
    role_result = _adc_get_role("auditor", str(project))
    if role_result["status"] != "success":
        return {"status": "error", "message": "Auditor role not found"}
    system_prompt = role_result["content"]

    # Read contracts
    contracts_dir = project / "contracts"
    contracts_content = ""
    for cf in sorted(contracts_dir.rglob("*.md")):
        if cf.name == "README.md":
            continue
        try:
            contracts_content += f"\n\n=== CONTRACT: {cf.name} ===\n"
            contracts_content += cf.read_text(encoding="utf-8")
        except Exception:
            continue

    # Read source
    source_path = project / src_dir
    source_content = ""
    for py_file in sorted(source_path.rglob("*.py")):
        try:
            source_content += f"\n\n=== SOURCE: {py_file.relative_to(project)} ===\n"
            source_content += py_file.read_text(encoding="utf-8")
        except Exception:
            continue

    if not contracts_content.strip():
        return {"status": "error", "message": "No contract content found"}
    if not source_content.strip():
        return {"status": "error", "message": "No source content found"}

    user_prompt = f"""Please audit this implementation against the ADC contracts.

CONTRACTS:
{contracts_content}

IMPLEMENTATION:
{source_content}
"""

    response = call_ai_agent(agent, system_prompt, user_prompt, model)

    if response.startswith("Error:"):
        return {"status": "error", "message": response}

    return {
        "status": "success",
        "agent": agent,
        "model": model,
        "audit_report": response,
    }


def _adc_refine(
    contract_file: str,
    project_path: str = "",
    agent: str = "",
    model: str = "",
) -> Dict[str, Any]:
    """Refine a contract using AI."""
    from ..config import load_config
    from ..providers import call_ai_agent

    project = _resolve_project(project_path)
    config = load_config()

    if not agent:
        agent = config["task_agents"].get("refine", config["default_agent"])
    if not model:
        model = config["models"].get(agent, "")

    # Read refiner role
    role_result = _adc_get_role("refiner", str(project))
    if role_result["status"] != "success":
        return {"status": "error", "message": "Refiner role not found"}
    system_prompt = role_result["content"]

    # Read contract
    target = Path(contract_file)
    if not target.is_absolute():
        target = project / contract_file

    if not target.exists():
        return {"status": "error", "message": f"Contract file not found: {target}"}

    contract_content = target.read_text(encoding="utf-8")
    user_prompt = f"Please review and refine this ADC contract:\n\n{contract_content}"

    response = call_ai_agent(agent, system_prompt, user_prompt, model)

    if response.startswith("Error:"):
        return {"status": "error", "message": response}

    return {
        "status": "success",
        "agent": agent,
        "model": model,
        "refined_contract": response,
    }


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    Tool(
        name="adc_init",
        description="Initialize ADC project structure (contracts/, roles/, src/ directories). Use this when starting a new ADC project.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory. Defaults to current working directory.",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force re-creation of existing structure.",
                    "default": False,
                },
            },
        },
    ),
    Tool(
        name="adc_lint",
        description="Lint and auto-fix formatting issues in ADC contract files. Fixes list indentation, section headers, Mermaid syntax, and list spacing.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to file or directory to lint (default: '.' for all contracts).",
                    "default": ".",
                },
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview changes without applying them.",
                    "default": False,
                },
            },
        },
    ),
    Tool(
        name="adc_validate",
        description="Validate ADC contract implementations by checking ADC-IMPLEMENTS markers in source code against contract block IDs. Returns compliance score, missing implementations, and issues. No AI required.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
            },
        },
    ),
    Tool(
        name="adc_health",
        description="Check ADC system health: contracts, source, roles, AI providers, and configuration status.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
            },
        },
    ),
    Tool(
        name="adc_config_show",
        description="Show current ADC configuration (default agent, task agents, models).",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="adc_config_set",
        description="Update ADC configuration. Keys: 'default_agent', 'task_agents.generate', 'task_agents.audit', 'task_agents.refine', 'models.anthropic', 'models.openai', 'models.gemini'.",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Configuration key (e.g., 'default_agent', 'task_agents.generate').",
                },
                "value": {
                    "type": "string",
                    "description": "New value to set.",
                },
            },
            "required": ["key", "value"],
        },
    ),
    Tool(
        name="adc_list_contracts",
        description="List all ADC contracts in a project with metadata (contract_id, title, status, version, block counts). Quick overview of the design landscape.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
            },
        },
    ),
    Tool(
        name="adc_parse_contract",
        description="Parse an ADC contract file into structured data: metadata, design blocks (type, name, ID, parity), and summary. Uses caching for repeated calls.",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the contract file (absolute or relative to project).",
                },
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Include full block body text (up to 2000 chars each).",
                    "default": False,
                },
            },
            "required": ["file_path"],
        },
    ),
    Tool(
        name="adc_find_markers",
        description="Find all ADC-IMPLEMENTS markers in source code. Returns marker locations grouped by block ID. Uses caching for repeated calls. No AI required.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
                "src_dir": {
                    "type": "string",
                    "description": "Source directory to scan (relative to project, default: 'src').",
                    "default": "src",
                },
            },
        },
    ),
    Tool(
        name="adc_get_role",
        description="Get the full content of an ADC agent role definition (e.g., 'auditor', 'code_generator', 'refiner', 'contract_writer', 'system_evaluator', 'pr_orchestrator', 'initializer', 'refactorer', 'simulator').",
        inputSchema={
            "type": "object",
            "properties": {
                "role_name": {
                    "type": "string",
                    "description": "Name of the role (e.g., 'auditor', 'code_generator', 'refiner').",
                },
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
            },
            "required": ["role_name"],
        },
    ),
    Tool(
        name="adc_list_roles",
        description="List all available ADC agent roles with their sources (project-local or package-bundled).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
            },
        },
    ),
    Tool(
        name="adc_generate",
        description="Generate code from ADC contracts using an AI provider. Reads all contracts, applies the code_generator role, and returns generated code. Requires AI API key.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
                "agent": {
                    "type": "string",
                    "description": "AI provider to use: 'anthropic', 'openai', or 'gemini'. Defaults to configured default.",
                    "enum": ["anthropic", "openai", "gemini"],
                },
                "model": {
                    "type": "string",
                    "description": "Specific model override (e.g., 'claude-3-sonnet-20240229', 'gpt-4o').",
                },
            },
        },
    ),
    Tool(
        name="adc_audit",
        description="Audit source code against ADC contracts using an AI provider. Checks compliance, identifies drift, and generates an audit report. Requires AI API key.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
                "agent": {
                    "type": "string",
                    "description": "AI provider: 'anthropic', 'openai', or 'gemini'.",
                    "enum": ["anthropic", "openai", "gemini"],
                },
                "model": {
                    "type": "string",
                    "description": "Specific model override.",
                },
                "src_dir": {
                    "type": "string",
                    "description": "Source directory to audit (default: 'src').",
                    "default": "src",
                },
            },
        },
    ),
    Tool(
        name="adc_refine",
        description="Refine an ADC contract using an AI provider. Analyzes the contract for completeness, consistency, and suggests improvements. Requires AI API key.",
        inputSchema={
            "type": "object",
            "properties": {
                "contract_file": {
                    "type": "string",
                    "description": "Path to the contract file to refine.",
                },
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory.",
                },
                "agent": {
                    "type": "string",
                    "description": "AI provider: 'anthropic', 'openai', or 'gemini'.",
                    "enum": ["anthropic", "openai", "gemini"],
                },
                "model": {
                    "type": "string",
                    "description": "Specific model override.",
                },
            },
            "required": ["contract_file"],
        },
    ),
]

# Dispatch table: tool name -> handler function
_TOOL_HANDLERS = {
    "adc_init": lambda args: _adc_init(
        project_path=args.get("project_path", ""),
        force=args.get("force", False),
    ),
    "adc_lint": lambda args: _adc_lint(
        path=args.get("path", "."),
        project_path=args.get("project_path", ""),
        dry_run=args.get("dry_run", False),
    ),
    "adc_validate": lambda args: _adc_validate(
        project_path=args.get("project_path", ""),
    ),
    "adc_health": lambda args: _adc_health(
        project_path=args.get("project_path", ""),
    ),
    "adc_config_show": lambda args: _adc_config_show(),
    "adc_config_set": lambda args: _adc_config_set(
        key=args["key"],
        value=args["value"],
    ),
    "adc_list_contracts": lambda args: _adc_list_contracts(
        project_path=args.get("project_path", ""),
    ),
    "adc_parse_contract": lambda args: _adc_parse_contract(
        file_path=args["file_path"],
        project_path=args.get("project_path", ""),
        detailed=args.get("detailed", False),
    ),
    "adc_find_markers": lambda args: _adc_find_markers(
        project_path=args.get("project_path", ""),
        src_dir=args.get("src_dir", "src"),
    ),
    "adc_get_role": lambda args: _adc_get_role(
        role_name=args["role_name"],
        project_path=args.get("project_path", ""),
    ),
    "adc_list_roles": lambda args: _adc_list_roles(
        project_path=args.get("project_path", ""),
    ),
    "adc_generate": lambda args: _adc_generate(
        project_path=args.get("project_path", ""),
        agent=args.get("agent", ""),
        model=args.get("model", ""),
    ),
    "adc_audit": lambda args: _adc_audit(
        project_path=args.get("project_path", ""),
        agent=args.get("agent", ""),
        model=args.get("model", ""),
        src_dir=args.get("src_dir", "src"),
    ),
    "adc_refine": lambda args: _adc_refine(
        contract_file=args["contract_file"],
        project_path=args.get("project_path", ""),
        agent=args.get("agent", ""),
        model=args.get("model", ""),
    ),
}


def register_tools(server: Server) -> None:
    """Register all ADC tools with the MCP server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOL_DEFINITIONS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = _TOOL_HANDLERS.get(name)
        if not handler:
            return [TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": f"Unknown tool: {name}"}),
            )]

        try:
            result = handler(arguments or {})
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)}),
            )]
