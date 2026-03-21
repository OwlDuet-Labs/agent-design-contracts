# ADC-IMPLEMENTS: <adc-mcp-prompts-01>
"""
ADC MCP Prompts — Role-based prompt templates for any MCP client.

Converts the Claude Code–specific agent definitions (src/adc/claude/agents/)
into universal MCP prompts that Windsurf, Cursor, Claude Desktop, etc. can use.

Each prompt loads the corresponding role definition and provides it as a
system message, so the AI client can assume any ADC role natively.
"""

from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
)


def _load_role_content(role_name: str) -> str:
    """Load a role definition from project or package."""
    # Project-local roles
    for roles_dir in [Path.cwd() / "roles", Path.cwd() / "src" / "adc" / "roles"]:
        role_file = roles_dir / f"{role_name}.md"
        if role_file.exists():
            return role_file.read_text(encoding="utf-8")

    # Package-bundled roles
    try:
        from importlib import resources
        adc_package = resources.files("adc")
        role_res = adc_package / "roles" / f"{role_name}.md"
        if role_res.is_file():
            return role_res.read_text(encoding="utf-8")
    except Exception:
        pass

    return ""


def _load_agent_content(agent_filename: str) -> str:
    """Load a Claude agent definition from project or package."""
    # Project-local agents
    for agents_dir in [
        Path.cwd() / "src" / "adc" / "claude" / "agents",
        Path.cwd() / ".claude" / "agents",
    ]:
        agent_file = agents_dir / agent_filename
        if agent_file.exists():
            content = agent_file.read_text(encoding="utf-8")
            # Strip YAML frontmatter (Claude Code-specific metadata)
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    content = content[end + 3:].strip()
            return content

    # Package-bundled agents
    try:
        from importlib import resources
        adc_package = resources.files("adc")
        agent_res = adc_package / "claude" / "agents" / agent_filename
        if agent_res.is_file():
            content = agent_res.read_text(encoding="utf-8")
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    content = content[end + 3:].strip()
            return content
    except Exception:
        pass

    return ""


def _load_schema_content() -> str:
    """Load the ADC schema."""
    try:
        from importlib import resources
        adc_package = resources.files("adc")
        schema_res = adc_package / "schema" / "adc-schema.md"
        if schema_res.is_file():
            return schema_res.read_text(encoding="utf-8")
    except Exception:
        pass

    schema_path = Path.cwd() / "adc-schema.md"
    if schema_path.exists():
        return schema_path.read_text(encoding="utf-8")

    return ""


def _build_prompt_content(
    role_name: str,
    agent_filename: str,
    task_description: str,
    include_schema: bool = False,
) -> str:
    """Build a complete prompt by combining role + agent instructions."""
    parts = []

    # Role definition (core behavioral instructions)
    role_content = _load_role_content(role_name)
    if role_content:
        parts.append(role_content)

    # Agent-specific workflow instructions
    agent_content = _load_agent_content(agent_filename)
    if agent_content:
        parts.append(agent_content)

    # Schema reference (for contract-writing and refinement tasks)
    if include_schema:
        schema = _load_schema_content()
        if schema:
            parts.append(f"\n---\n\n## ADC Schema Reference\n\n{schema}")

    if not parts:
        return f"You are an ADC agent performing: {task_description}. No role definition files found — use your best judgment following ADC principles."

    # Add MCP-specific tool usage guidance
    parts.append(
        "\n---\n\n"
        "## Available ADC Tools\n\n"
        "You have access to ADC MCP tools. Use them to gather context efficiently:\n"
        "- `adc_list_contracts` — discover all contracts in the project\n"
        "- `adc_parse_contract` — parse a contract into structured blocks\n"
        "- `adc_find_markers` — find ADC-IMPLEMENTS markers in source code\n"
        "- `adc_validate` — check contract-implementation compliance\n"
        "- `adc_lint` — fix contract formatting issues\n"
        "- `adc_health` — check system health\n"
        "- `adc_get_role` — load a specific role definition\n\n"
        "Prefer using these tools over manually reading files — they return "
        "structured data and use caching for efficiency.\n"
    )

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Prompt definitions
# ---------------------------------------------------------------------------

PROMPT_DEFINITIONS = [
    Prompt(
        name="adc-workflow",
        description=(
            "Run the complete ADC workflow loop (5 phases): "
            "Refine → Audit → Generate → Evaluate → Release. "
            "Use this to orchestrate the full ADC development cycle."
        ),
        arguments=[
            PromptArgument(
                name="task",
                description="What to build or which phase to focus on (e.g., 'implement user auth', 'adc-test: weather app').",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
    Prompt(
        name="adc-generate-code",
        description=(
            "Generate Python code from ADC contracts. "
            "Assumes the Code Generator role: creates implementations with "
            "ADC-IMPLEMENTS markers, functional patterns, and proper structure."
        ),
        arguments=[
            PromptArgument(
                name="task",
                description="What to generate (e.g., 'implement contracts/adc-001.md', 'scaffold the data pipeline').",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
    Prompt(
        name="adc-audit-compliance",
        description=(
            "Audit source code against ADC contracts. "
            "Assumes the Auditor role: checks parity, detects drift, "
            "identifies anti-patterns, and generates structured reports."
        ),
        arguments=[
            PromptArgument(
                name="task",
                description="Audit scope (e.g., 'audit all contracts', 'audit contracts/adc-001.md').",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
    Prompt(
        name="adc-refine-contracts",
        description=(
            "Analyze and improve ADC contract quality. "
            "Assumes the Refiner role: checks completeness, consistency, "
            "feasibility, and suggests improvements."
        ),
        arguments=[
            PromptArgument(
                name="task",
                description="What to refine (e.g., 'refine all contracts', 'improve contracts/adc-002.md').",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
    Prompt(
        name="adc-write-contracts",
        description=(
            "Create new ADC contracts from requirements or user stories. "
            "Assumes the Contract Writer role: translates high-level descriptions "
            "into formal ADC contracts following the schema."
        ),
        arguments=[
            PromptArgument(
                name="requirements",
                description="Requirements, user stories, or system description to convert into ADC contracts.",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
    Prompt(
        name="adc-evaluate-system",
        description=(
            "Empirically evaluate a system through actual interfaces. "
            "Assumes the System Evaluator role: runs real tests, measures "
            "performance, reports failures first. No hallucinated results."
        ),
        arguments=[
            PromptArgument(
                name="task",
                description="What to evaluate (e.g., 'test authentication with 100 attempts', 'benchmark API endpoints').",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
    Prompt(
        name="adc-initialize",
        description=(
            "Initialize an existing codebase with ADC contracts. "
            "Assumes the Initializer role: analyzes existing code, creates "
            "contracts, and adds ADC-IMPLEMENTS markers without modifying functional code."
        ),
        arguments=[
            PromptArgument(
                name="task",
                description="Initialization scope (e.g., 'initialize this project', 'create contracts for src/auth/').",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
    Prompt(
        name="adc-manage-release",
        description=(
            "Manage version control, PRs, and releases. "
            "Assumes the PR Orchestrator role: detects version changes, "
            "generates PRs, manages semantic versioning."
        ),
        arguments=[
            PromptArgument(
                name="task",
                description="Release task (e.g., 'prepare v2.0 release', 'create PR for feature branch').",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
    Prompt(
        name="adc-refactor",
        description=(
            "Orchestrate refactoring through temporary contracts. "
            "Assumes the Refactorer role: coordinates updates to existing "
            "component contracts during refactoring work."
        ),
        arguments=[
            PromptArgument(
                name="task",
                description="Refactoring scope (e.g., 'consolidate authentication modules', 'refactor data pipeline').",
                required=True,
            ),
            PromptArgument(
                name="project_path",
                description="Absolute path to the project directory.",
                required=False,
            ),
        ],
    ),
]

# Mapping: prompt name -> (role_name, agent_filename, include_schema)
_PROMPT_CONFIG = {
    "adc-workflow": ("system_evaluator", "adc-workflow-orchestrator.md", False),
    "adc-generate-code": ("code_generator", "adc-code-generator.md", False),
    "adc-audit-compliance": ("auditor", "adc-compliance-auditor.md", False),
    "adc-refine-contracts": ("refiner", "adc-contract-refiner.md", False),
    "adc-write-contracts": ("contract_writer", "adc-contract-writer.md", True),
    "adc-evaluate-system": ("system_evaluator", "adc-system-evaluator.md", False),
    "adc-initialize": ("initializer", "adc-initializer.md", True),
    "adc-manage-release": ("pr_orchestrator", "adc-pr-orchestrator.md", False),
    "adc-refactor": ("refactorer", "adc-refactorer.md", False),
}


def register_prompts(server: Server) -> None:
    """Register all ADC prompts with the MCP server."""

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return PROMPT_DEFINITIONS

    @server.get_prompt()
    async def get_prompt(name: str, arguments: Optional[dict] = None) -> GetPromptResult:
        args = arguments or {}

        config = _PROMPT_CONFIG.get(name)
        if not config:
            return GetPromptResult(
                description=f"Unknown prompt: {name}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"Error: Unknown ADC prompt '{name}'. Available: {', '.join(_PROMPT_CONFIG.keys())}",
                        ),
                    )
                ],
            )

        role_name, agent_filename, include_schema = config

        # Build the system prompt from role + agent definitions
        system_content = _build_prompt_content(
            role_name=role_name,
            agent_filename=agent_filename,
            task_description=name,
            include_schema=include_schema,
        )

        # Build the user message from arguments
        task = args.get("task") or args.get("requirements") or "Please proceed with the ADC workflow."
        project_path = args.get("project_path", "")

        user_message = task
        if project_path:
            user_message += f"\n\nProject path: {project_path}"

        # Find the matching prompt definition for the description
        prompt_def = next((p for p in PROMPT_DEFINITIONS if p.name == name), None)
        description = prompt_def.description if prompt_def else name

        return GetPromptResult(
            description=description,
            messages=[
                PromptMessage(
                    role="assistant",
                    content=TextContent(type="text", text=system_content),
                ),
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=user_message),
                ),
            ],
        )
