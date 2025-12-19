"""
Bridge implementations for different programming languages.

This package contains bridge adapters that provide a unified Python interface
for loading and introspecting libraries in different languages.
"""

from .python_bridge import PythonBridge
from .cli_fallback import CliFallbackBridge

__all__ = ["PythonBridge", "CliFallbackBridge"]
