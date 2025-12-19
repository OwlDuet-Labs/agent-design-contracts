"""
Universal Library Loader: Token-Efficient Polyglot Introspection

This package provides a unified Python interface for loading and introspecting
libraries in any programming language with minimal token usage.

Main API:
    load_library(workspace_path) -> (library_proxy, metadata)
"""

# ADC-IMPLEMENTS: <ull-feature-06>

import time
from pathlib import Path
from typing import Any, Optional, Tuple

from .metadata import LibraryMetadata, LanguageType, BridgeType
from .detection import detect_language
from .bridges.python_bridge import PythonBridge
from .bridges.cli_fallback import CliFallbackBridge
from .exceptions import LibraryLoadError, InterfaceConformanceError
from .verification import VerificationResult, SignatureMismatch
from .contract_extractor import ContractInterfaceExtractor, ExpectedInterface
from .verifier import verify_compliance
from .marker_verifier import MarkerVerifier


__all__ = [
    "load_library",
    "LibraryMetadata",
    "LanguageType",
    "BridgeType",
    "VerificationResult",
    "SignatureMismatch",
    "ExpectedInterface",
    "ContractInterfaceExtractor",
    "verify_compliance",
    "MarkerVerifier",
    "LibraryLoadError",
    "InterfaceConformanceError",
]


def load_library(
    workspace_path: str | Path,
    expected_language: Optional[str] = None,
    fail_on_limited_verification: bool = False
) -> Tuple[Any, LibraryMetadata]:
    """
    Load library from any language and return introspectable Python object.

    Args:
        workspace_path: Path to workspace containing library
        expected_language: Force specific language (skip detection)
        fail_on_limited_verification: Raise error if only CLI fallback available

    Returns:
        (library_proxy, metadata)

        library_proxy: Python object with library functions as methods
        metadata: LibraryMetadata with verification capabilities

    Raises:
        LibraryLoadError: If library cannot be loaded
        InterfaceConformanceError: If expected_language doesn't match detected

    Example:
        lib, meta = load_library("./workspace")

        # Use library
        result = lib.create_task(title="foo", description="bar")

        # Check verification capabilities
        if meta.supports_signature_verification:
            import inspect
            sig = inspect.signature(lib.create_task)
            print(f"Signature: {sig}")
    """
    workspace_path = Path(workspace_path)

    # 1. Detect language
    if expected_language:
        detected_language = LanguageType(expected_language)
        indicators_found = {}
    else:
        detected_language, indicators_found = detect_language(workspace_path)

    # 2. Select bridge
    bridge_type, bridge = _select_bridge(detected_language, workspace_path)

    # 3. Load library
    start_time = time.time()
    load_errors = []

    try:
        library_proxy = bridge.load()
        load_time_ms = (time.time() - start_time) * 1000
    except Exception as e:
        load_time_ms = (time.time() - start_time) * 1000
        load_errors = [str(e)]
        raise

    # 4. Create metadata
    metadata = LibraryMetadata(
        workspace_path=str(workspace_path),
        detected_language=detected_language,
        bridge_type=bridge_type,
        language_indicators=indicators_found,
        supports_signature_verification=bridge_type in [
            BridgeType.PYTHON_DIRECT,
            BridgeType.NODEJS_SUBPROCESS,
        ],
        supports_type_introspection=bridge_type in [
            BridgeType.PYTHON_DIRECT,
            BridgeType.NODEJS_SUBPROCESS,
        ],
        supports_docstring_verification=bridge_type == BridgeType.PYTHON_DIRECT,
        load_time_ms=load_time_ms,
        load_errors=load_errors,
    )

    # 5. Fail if limited verification and flag set
    if fail_on_limited_verification and not metadata.supports_signature_verification:
        raise LibraryLoadError(
            f"Library only supports LIMITED verification (CLI fallback)\n"
            f"  Language: {detected_language.value}\n"
            f"  Bridge: {bridge_type.value}\n"
            f"  Fix: Implement Python bindings for full verification\n"
            f"  See: contracts/universal-library-loader/002-phase2-bindings.qmd"
        )

    return library_proxy, metadata


def _select_bridge(language: LanguageType, workspace: Path) -> Tuple[BridgeType, Any]:
    """
    Select appropriate bridge for language.

    Args:
        language: Detected language type
        workspace: Workspace path

    Returns:
        (bridge_type, bridge_instance)
    """
    if language == LanguageType.PYTHON:
        return BridgeType.PYTHON_DIRECT, PythonBridge(workspace)
    elif language == LanguageType.NODEJS:
        # Node.js bridge would go here - using CLI fallback for Phase 1
        return BridgeType.CLI_FALLBACK, CliFallbackBridge(workspace)
    else:
        # CLI fallback for all other languages (Phase 1)
        return BridgeType.CLI_FALLBACK, CliFallbackBridge(workspace)
