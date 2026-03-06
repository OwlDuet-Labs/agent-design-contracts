# ADC-IMPLEMENTS: <adc-mcp-setup-tool-01>
"""
Auto-installer for ADC MCP server across all supported AI clients.

Detects installed IDEs/AI apps and writes MCP configuration so the
ADC server is available everywhere: Windsurf, Cursor, Claude Desktop,
VS Code Continue, etc.
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Client detection & config paths
# ---------------------------------------------------------------------------

def _get_client_configs() -> List[Dict]:
    """Return configuration metadata for all supported MCP clients."""
    home = Path.home()
    platform = sys.platform

    clients = [
        {
            "name": "Windsurf",
            "config_path": home / ".codeium" / "windsurf" / "mcp_config.json",
            "detect_paths": [
                home / ".codeium" / "windsurf",
                Path("/Applications/Windsurf.app") if platform == "darwin" else None,
            ],
            "config_key": "mcpServers",
        },
        {
            "name": "Cursor",
            "config_path": home / ".cursor" / "mcp.json",
            "detect_paths": [
                home / ".cursor",
                Path("/Applications/Cursor.app") if platform == "darwin" else None,
            ],
            "config_key": "mcpServers",
        },
        {
            "name": "Claude Desktop",
            "config_path": (
                home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
                if platform == "darwin"
                else home / ".config" / "Claude" / "claude_desktop_config.json"
            ),
            "detect_paths": [
                Path("/Applications/Claude.app") if platform == "darwin" else None,
                home / "Library" / "Application Support" / "Claude" if platform == "darwin" else None,
                home / ".config" / "Claude" if platform != "darwin" else None,
            ],
            "config_key": "mcpServers",
        },
        {
            "name": "VS Code Continue",
            "config_path": home / ".continue" / "config.json",
            "detect_paths": [
                home / ".continue",
            ],
            "config_key": "mcpServers",
        },
    ]

    # Filter out None detect_paths
    for client in clients:
        client["detect_paths"] = [p for p in client["detect_paths"] if p is not None]

    return clients


def _detect_installed_clients() -> List[Dict]:
    """Detect which MCP-compatible clients are installed."""
    installed = []
    for client in _get_client_configs():
        for detect_path in client["detect_paths"]:
            if detect_path.exists():
                installed.append(client)
                break
    return installed


def _find_adc_mcp_command() -> str:
    """Find the adc-mcp command path."""
    # Check if adc-mcp is on PATH
    adc_mcp = shutil.which("adc-mcp")
    if adc_mcp:
        return adc_mcp

    # Check in the current venv
    venv_bin = Path(sys.prefix) / "bin" / "adc-mcp"
    if venv_bin.exists():
        return str(venv_bin)

    # Fallback: use python -m
    return "adc-mcp"


def _build_mcp_entry(command: str) -> Dict:
    """Build the MCP server config entry."""
    # If the command is a full path, use it directly
    if os.path.sep in command or command.startswith("/"):
        return {
            "command": command,
            "args": [],
        }

    # Otherwise, assume it's on PATH
    return {
        "command": command,
        "args": [],
    }


def _write_client_config(client: Dict, mcp_entry: Dict, force: bool = False) -> Tuple[bool, str]:
    """Write MCP config for a specific client. Returns (success, message)."""
    config_path = client["config_path"]
    config_key = client["config_key"]
    client_name = client["name"]

    # Read existing config
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            if not force:
                return False, f"Cannot parse existing config at {config_path}: {e}"
            existing_config = {}

    # Check if ADC is already configured
    mcp_servers = existing_config.get(config_key, {})
    if "adc" in mcp_servers and not force:
        return True, f"Already configured in {client_name} (use --force to overwrite)"

    # Add/update ADC entry
    if config_key not in existing_config:
        existing_config[config_key] = {}
    existing_config[config_key]["adc"] = mcp_entry

    # Write config
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2)
        return True, f"Configured {client_name} at {config_path}"
    except Exception as e:
        return False, f"Failed to write {client_name} config: {e}"


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

def add_setup_mcp_parser(subparsers) -> None:
    """Add the setup-mcp subcommand to the CLI."""
    parser = subparsers.add_parser(
        "setup-mcp",
        help="Configure ADC MCP server for all detected IDEs and AI apps",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing MCP configurations",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_clients",
        help="List detected clients without configuring",
    )
    parser.add_argument(
        "--client",
        help="Configure only a specific client (windsurf, cursor, claude-desktop, continue)",
    )
    parser.set_defaults(func=_handle_setup_mcp)


def _handle_setup_mcp(args) -> bool:
    """Handle the setup-mcp command."""
    # Detect clients
    all_clients = _get_client_configs()
    installed_clients = _detect_installed_clients()

    if args.list_clients:
        print("\nDetected MCP-compatible clients:")
        print("=" * 50)
        for client in all_clients:
            detected = client in installed_clients
            status = "DETECTED" if detected else "not found"
            print(f"  {client['name']:20s} [{status}]")
            print(f"    Config: {client['config_path']}")
        print()
        return True

    # Filter to specific client if requested
    if args.client:
        client_map = {
            "windsurf": "Windsurf",
            "cursor": "Cursor",
            "claude-desktop": "Claude Desktop",
            "claude": "Claude Desktop",
            "continue": "VS Code Continue",
            "vscode": "VS Code Continue",
        }
        target_name = client_map.get(args.client.lower())
        if not target_name:
            print(f"Unknown client: {args.client}")
            print(f"Available: {', '.join(client_map.keys())}")
            return False
        installed_clients = [c for c in all_clients if c["name"] == target_name]

    if not installed_clients:
        print("\nNo MCP-compatible clients detected.")
        print("Supported clients: Windsurf, Cursor, Claude Desktop, VS Code Continue")
        print("\nYou can manually configure by adding to your client's MCP config:")
        print(json.dumps({"mcpServers": {"adc": {"command": "adc-mcp", "args": []}}}, indent=2))
        return False

    # Find adc-mcp command
    command = _find_adc_mcp_command()
    mcp_entry = _build_mcp_entry(command)

    print(f"\nConfiguring ADC MCP server (command: {command})")
    print("=" * 50)

    success_count = 0
    for client in installed_clients:
        ok, message = _write_client_config(client, mcp_entry, force=args.force)
        icon = "OK" if ok else "FAIL"
        print(f"  [{icon}] {message}")
        if ok:
            success_count += 1

    print()
    if success_count > 0:
        print(f"ADC MCP server configured for {success_count} client(s).")
        print()
        print("Next steps:")
        print("  1. Restart your IDE/AI app to load the new MCP server")
        print("  2. The ADC tools, resources, and prompts will be available automatically")
        print()
        print("Available ADC prompts in your AI client:")
        print("  - adc-workflow         (full 5-phase ADC loop)")
        print("  - adc-generate-code    (code generation from contracts)")
        print("  - adc-audit-compliance (compliance auditing)")
        print("  - adc-refine-contracts (contract refinement)")
        print("  - adc-write-contracts  (create contracts from requirements)")
        print("  - adc-evaluate-system  (empirical system evaluation)")
        print("  - adc-initialize       (initialize existing codebase)")
        print("  - adc-manage-release   (PR and release management)")
        print("  - adc-refactor         (coordinated refactoring)")
    else:
        print("No clients were configured. Use --force to overwrite existing configs.")

    return success_count > 0
