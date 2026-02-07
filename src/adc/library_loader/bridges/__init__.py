"""
Bridge implementations for different programming languages.

This package contains bridge adapters that provide a unified Python interface
for loading and introspecting libraries in different languages.
"""

from .python_bridge import PythonBridge
from .cli_fallback import CliFallbackBridge

# RPC bridge is optional (requires msgpack)
try:
    from .rpc_bridge import RPCBridge, RPCError, RPCTimeoutError
    HAS_RPC = True
except ImportError:
    HAS_RPC = False
    RPCBridge = None
    RPCError = None
    RPCTimeoutError = None

__all__ = [
    "PythonBridge",
    "CliFallbackBridge",
    "RPCBridge",
    "RPCError",
    "RPCTimeoutError",
    "HAS_RPC",
]
