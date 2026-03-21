# ADC-IMPLEMENTS: <adc-mcp-server-01>
"""
Allow running the MCP server as a module: python -m adc_cli.mcp_server
"""

from .server import run_server

if __name__ == "__main__":
    run_server()
