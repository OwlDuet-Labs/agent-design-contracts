---
contract_id: "adc-mcp-server-adc-004"
title: "ADC MCP Server — Universal IDE Integration"
author: "OwlDuet-Labs"
status: "active"
version: 1.0
created_date: "2026-03-06"
last_updated: "2026-03-06"
---

### [Rationale: MCP Server Rationale] <adc-mcp-rationale-01>
The ADC framework was originally tightly coupled to Claude Code via `.claude/agents/` and `.claude/commands/` directories. This limits adoption to a single IDE. An MCP (Model Context Protocol) server exposes all ADC capabilities — tools, resources, and role-based prompts — as a universal interface that any MCP-compatible AI client can consume: Windsurf, Cursor, Claude Desktop, VS Code Continue, and future clients. This enables seamless cross-IDE ADC workflows and significantly reduces token usage by moving deterministic operations (validation, marker scanning, contract parsing) out of the LLM context into efficient tool calls with server-side caching.

### [Implementation: MCP Server Architecture] <adc-mcp-impl-01>
The MCP server is implemented as a new subpackage `src/adc_cli/mcp_server/` within the existing ADC CLI package. It uses the official Python MCP SDK (`mcp>=1.0.0`) with stdio transport for local operation. The server reuses existing ADC core logic from `commands.py`, `providers.py`, `contract_lint.py`, and `validation/` modules. It is installed as a pip entry point (`adc-mcp`) and auto-configured for detected clients via `adc setup-mcp`.

**Parity:**
- **Implementation Scope:** `src/adc_cli/mcp_server/`
- **Configuration Scope:** `pyproject.toml` (entry points, dependencies)
- **Tests:** `tests/test_mcp_server.py`

### [Tool: ADC MCP Server] <adc-mcp-server-01>
The MCP server process that hosts all ADC tools, resources, and prompts over stdio transport.

**Interface:**
- **Transport:** stdio (JSON-RPC)
- **Entry Point:** `adc-mcp` command or `python -m adc_cli.mcp_server`
- **Capabilities:** Tools (14), Resources (dynamic), Prompts (9)

**Parity:**
- **Implementation Scope:** `src/adc_cli/mcp_server/server.py`

### [Feature: MCP Tools] <adc-mcp-tools-01>
14 tools exposed via MCP, split into local (no AI) and AI-powered categories.

**Local Tools (no API key required):**
- `adc_init` — Initialize ADC project structure
- `adc_lint` — Lint and auto-fix contract files
- `adc_validate` — Check ADC-IMPLEMENTS markers against contracts
- `adc_health` — System health check
- `adc_config_show` / `adc_config_set` — Configuration management
- `adc_list_contracts` — List contracts with metadata
- `adc_parse_contract` — Parse contract into structured blocks (cached)
- `adc_find_markers` — Find ADC-IMPLEMENTS markers in source (cached)
- `adc_get_role` / `adc_list_roles` — Role definition access

**AI-Powered Tools (require API key):**
- `adc_generate` — Generate code from contracts
- `adc_audit` — AI-powered compliance audit
- `adc_refine` — AI-powered contract refinement

**Parity:**
- **Implementation Scope:** `src/adc_cli/mcp_server/tools.py`

### [Feature: MCP Resources] <adc-mcp-resources-01>
Static and dynamic data exposed as MCP resources for on-demand fetching.

- `adc://schema` — Complete ADC schema v1.0
- `adc://config` — Current ADC configuration
- `adc://roles/{name}` — Individual role definitions (dynamically listed)

**Parity:**
- **Implementation Scope:** `src/adc_cli/mcp_server/resources.py`

### [Feature: MCP Prompts] <adc-mcp-prompts-01>
9 role-based prompt templates that convert Claude Code agents into universal MCP prompts.

- `adc-workflow` — Full 5-phase ADC loop orchestration
- `adc-generate-code` — Code generation with code_generator role
- `adc-audit-compliance` — Compliance audit with auditor role
- `adc-refine-contracts` — Contract refinement with refiner role
- `adc-write-contracts` — Contract creation with contract_writer role + schema
- `adc-evaluate-system` — Empirical evaluation with system_evaluator role
- `adc-initialize` — Codebase initialization with initializer role + schema
- `adc-manage-release` — Release management with pr_orchestrator role
- `adc-refactor` — Coordinated refactoring with refactorer role

**Parity:**
- **Implementation Scope:** `src/adc_cli/mcp_server/prompts.py`

### [Tool: MCP Setup Installer] <adc-mcp-setup-tool-01>
CLI command `adc setup-mcp` that auto-detects installed MCP clients and writes configuration.

**Supported Clients:**
- Windsurf (`~/.codeium/windsurf/mcp_config.json`)
- Cursor (`~/.cursor/mcp.json`)
- Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)
- VS Code Continue (`~/.continue/config.json`)

**Parity:**
- **Implementation Scope:** `src/adc_cli/command_modules/setup_mcp_command.py`

### [Algorithm: Server-Side Caching] <adc-mcp-cache-01>
The MCP server maintains in-memory caches for parsed contracts and marker scans, keyed by file path and validated against file mtime. This avoids re-reading and re-parsing files on repeat tool calls within the same server session.

**Cache Strategy:**
1. On first call: parse file, store result + mtime
2. On subsequent calls: compare stored mtime with current; return cached if match
3. On file change: mtime mismatch → invalidate and re-parse

**Parity:**
- **Implementation Scope:** `src/adc_cli/mcp_server/tools.py` (`_contract_cache`, `_marker_cache`)

### [Constraint: Token Efficiency] <adc-mcp-constraint-01>
The MCP server is designed to minimize LLM token usage:
- Tool definitions add ~2,100 tokens to system prompt (fixed cost)
- Local tools return compact JSON instead of requiring the AI to read raw files
- Caching eliminates redundant file reads across tool calls
- Prompts load only the specific role needed, not all agents
- `detailed` parameter on `adc_parse_contract` controls payload size
