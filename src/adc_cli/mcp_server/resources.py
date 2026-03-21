# ADC-IMPLEMENTS: <adc-mcp-resources-01>
"""
ADC MCP Resources — Static and dynamic data exposed to MCP clients.

Resources allow AI clients to read ADC reference material (schema, roles, config)
without consuming tool calls. Clients fetch resources on-demand.
"""

import json
from pathlib import Path

from mcp.server import Server
from mcp.types import Resource, TextResourceContents


def _read_schema() -> str:
    """Read the ADC schema from package or project."""
    # Try package-bundled schema
    try:
        from importlib import resources
        adc_package = resources.files("adc")
        schema_res = adc_package / "schema" / "adc-schema.md"
        if schema_res.is_file():
            return schema_res.read_text(encoding="utf-8")
    except Exception:
        pass

    # Try well-known project location
    for candidate in [
        Path.cwd() / "adc-schema.md",
        Path.home() / ".claude" / "schema" / "adc-schema.md",
    ]:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")

    return "# ADC Schema\n\nSchema file not found. Install the ADC package or place adc-schema.md in your project root."


def _read_role(role_name: str) -> str:
    """Read a role definition."""
    # Try project-local roles
    for roles_dir in [Path.cwd() / "roles", Path.cwd() / "src" / "adc" / "roles"]:
        role_file = roles_dir / f"{role_name}.md"
        if role_file.exists():
            return role_file.read_text(encoding="utf-8")

    # Try package-bundled roles
    try:
        from importlib import resources
        adc_package = resources.files("adc")
        role_res = adc_package / "roles" / f"{role_name}.md"
        if role_res.is_file():
            return role_res.read_text(encoding="utf-8")
    except Exception:
        pass

    return f"# {role_name}\n\nRole definition not found."


def _list_role_names() -> list[str]:
    """Get all available role names."""
    names = set()

    for roles_dir in [Path.cwd() / "roles", Path.cwd() / "src" / "adc" / "roles"]:
        if roles_dir.exists():
            for f in roles_dir.glob("*.md"):
                names.add(f.stem)

    try:
        from importlib import resources
        adc_package = resources.files("adc")
        roles_pkg = adc_package / "roles"
        for f in roles_pkg.iterdir():
            if str(f).endswith(".md"):
                names.add(Path(str(f)).stem)
    except Exception:
        pass

    return sorted(names)


def _read_config() -> str:
    """Read ADC configuration as JSON."""
    config_path = Path.home() / ".adcconfig.json"
    if config_path.exists():
        return config_path.read_text(encoding="utf-8")

    return json.dumps({
        "default_agent": "anthropic",
        "task_agents": {
            "generate": "anthropic",
            "audit": "anthropic",
            "refine": "gemini",
        },
        "models": {
            "anthropic": "claude-3-sonnet-20240229",
            "openai": "gpt-4o",
            "gemini": "gemini-1.5-pro-latest",
        },
    }, indent=2)


# ---------------------------------------------------------------------------
# All static resources
# ---------------------------------------------------------------------------

STATIC_RESOURCES = [
    Resource(
        uri="adc://schema",
        name="ADC Schema",
        description="The complete Agent Design Contract schema v1.0 — block types, format, parity sections, and ADC-IMPLEMENTS markers.",
        mimeType="text/markdown",
    ),
    Resource(
        uri="adc://config",
        name="ADC Configuration",
        description="Current ADC configuration (default agent, task agents, models).",
        mimeType="application/json",
    ),
]


def register_resources(server: Server) -> None:
    """Register all ADC resources with the MCP server."""

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        resources_list = list(STATIC_RESOURCES)

        # Add role resources dynamically
        for role_name in _list_role_names():
            resources_list.append(Resource(
                uri=f"adc://roles/{role_name}",
                name=f"ADC Role: {role_name}",
                description=f"Role definition for the ADC {role_name.replace('_', ' ')} agent.",
                mimeType="text/markdown",
            ))

        return resources_list

    @server.read_resource()
    async def read_resource(uri: str) -> list[TextResourceContents]:
        uri_str = str(uri)

        if uri_str == "adc://schema":
            return [TextResourceContents(
                uri=uri_str,
                mimeType="text/markdown",
                text=_read_schema(),
            )]

        if uri_str == "adc://config":
            return [TextResourceContents(
                uri=uri_str,
                mimeType="application/json",
                text=_read_config(),
            )]

        if uri_str.startswith("adc://roles/"):
            role_name = uri_str.replace("adc://roles/", "")
            return [TextResourceContents(
                uri=uri_str,
                mimeType="text/markdown",
                text=_read_role(role_name),
            )]

        return [TextResourceContents(
            uri=uri_str,
            mimeType="text/plain",
            text=f"Unknown resource: {uri_str}",
        )]
