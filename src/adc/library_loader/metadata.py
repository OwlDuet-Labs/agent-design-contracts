"""
Library metadata models for Universal Library Loader.

This module defines the data structures for tracking loaded library information
and verification capabilities across different programming languages.
"""

# ADC-IMPLEMENTS: <ull-model-01>

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LanguageType(str, Enum):
    """Detected language types."""
    PYTHON = "python"
    NODEJS = "nodejs"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CPP = "cpp"
    UNKNOWN = "unknown"


class BridgeType(str, Enum):
    """Bridge implementation types."""
    PYTHON_DIRECT = "python_direct"
    NODEJS_SUBPROCESS = "nodejs_subprocess"
    CLI_FALLBACK = "cli_fallback"
    GO_CTYPES = "go_ctypes"  # Phase 2
    RUST_PYO3 = "rust_pyo3"  # Phase 2
    JAVA_JNI = "java_jni"  # Phase 2


@dataclass
class LibraryMetadata:
    """Metadata about loaded library."""

    workspace_path: str
    detected_language: LanguageType
    bridge_type: BridgeType

    # Language indicators found
    language_indicators: dict[str, bool]  # {"setup.py": True, "package.json": False, ...}

    # Verification capabilities
    supports_signature_verification: bool
    supports_type_introspection: bool
    supports_docstring_verification: bool

    # Performance metrics
    load_time_ms: float

    # Error tracking
    load_errors: list[str]  # Empty if successful

    @property
    def verification_level(self) -> str:
        """Human-readable verification capability level."""
        if self.supports_signature_verification:
            return "FULL"  # Python, Node.js, Phase 2 bindings
        elif self.bridge_type == BridgeType.CLI_FALLBACK:
            return "LIMITED"  # CLI only, no signature verification
        else:
            return "UNKNOWN"
