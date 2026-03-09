# ADC-IMPLEMENTS: <adc-mcp-server-01>
"""
ADC MCP Server — Main server definition.

Registers all tools, resources, and prompts for the ADC framework,
making them available to any MCP-compatible AI client.
"""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .tools import register_tools
from .resources import register_resources
from .prompts import register_prompts

logger = logging.getLogger("adc-mcp")


def create_server() -> Server:
    """Create and configure the ADC MCP server."""
    server = Server("adc")

    register_tools(server)
    register_resources(server)
    register_prompts(server)

    logger.info("ADC MCP server initialized with tools, resources, and prompts")
    return server


async def _run_async():
    """Run the MCP server with stdio transport."""
    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        logger.info("ADC MCP server starting on stdio transport")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run_server():
    """Entry point — run the ADC MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )
    # Suppress noisy loggers on stderr (stdio transport uses stdout)
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    asyncio.run(_run_async())
