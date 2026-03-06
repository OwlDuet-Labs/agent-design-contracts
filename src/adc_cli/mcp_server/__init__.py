# ADC-IMPLEMENTS: <adc-mcp-server-01>
"""
ADC MCP Server — Model Context Protocol server for Agent Design Contracts.

Exposes ADC capabilities (tools, resources, prompts) to any MCP-compatible
AI client: Windsurf, Cursor, Claude Desktop, VS Code Continue, etc.
"""

__version__ = "0.11.0"


def main():
    """Entry point for the adc-mcp command."""
    from .server import run_server
    run_server()
