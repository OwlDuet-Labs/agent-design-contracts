"""
Integration tests for Dart RPC bridge.

Tests MessagePack RPC protocol with Dart subprocess communication.
"""

# ADC-IMPLEMENTS: <rpc-validation-01>

import pytest
from pathlib import Path

from adc.library_loader import (
    load_library,
    BridgeType,
    LanguageType,
    RPCBridge,
    RPCError,
)


@pytest.fixture
def dart_workspace():
    """Path to Dart simple_math test fixture."""
    return Path(__file__).parent / "fixtures" / "dart_simple_math"


def test_dart_language_detection(dart_workspace):
    """Test that Dart language is correctly detected from pubspec.yaml."""
    from adc.library_loader.detection import detect_language

    language, indicators = detect_language(dart_workspace)

    assert language == LanguageType.DART
    assert indicators.get("pubspec.yaml") is True


def test_dart_rpc_bridge_selection(dart_workspace):
    """Test that RPC bridge is selected for Dart workspace with bin/serve.dart."""
    from adc.library_loader import _should_use_rpc_bridge

    assert _should_use_rpc_bridge(dart_workspace, LanguageType.DART) is True


def test_dart_simple_math_via_rpc(dart_workspace):
    """Test loading Dart library via MessagePack RPC bridge."""
    # Skip if Dart is not installed
    import shutil
    if not shutil.which("dart"):
        pytest.skip("Dart runtime not installed")

    # Load library (should auto-detect Dart and use RPC bridge)
    lib, metadata = load_library(dart_workspace)

    # Verify correct bridge type
    assert metadata.detected_language == LanguageType.DART
    assert metadata.bridge_type == BridgeType.RPC
    assert metadata.supports_signature_verification is True
    assert metadata.supports_type_introspection is True
    assert metadata.load_errors == []

    # Test add method
    result = lib.add(a=5, b=3)
    assert result == 8

    # Test multiply method
    result = lib.multiply(a=4, b=7)
    assert result == 28

    # Test divide method
    result = lib.divide(a=10, b=2)
    assert result == 5.0


def test_dart_rpc_error_handling(dart_workspace):
    """Test that RPC errors are properly propagated."""
    import shutil
    if not shutil.which("dart"):
        pytest.skip("Dart runtime not installed")

    lib, _ = load_library(dart_workspace)

    # Test divide by zero error
    with pytest.raises(RPCError) as exc_info:
        lib.divide(a=10, b=0)

    assert "Cannot divide by zero" in str(exc_info.value)


def test_dart_rpc_unknown_method(dart_workspace):
    """Test calling unknown method raises error."""
    import shutil
    if not shutil.which("dart"):
        pytest.skip("Dart runtime not installed")

    lib, _ = load_library(dart_workspace)

    # Call non-existent method
    with pytest.raises(RPCError) as exc_info:
        lib.nonexistent_method(a=1)

    assert "Unknown method" in str(exc_info.value)


def test_rpc_bridge_context_manager():
    """Test RPCBridge context manager cleanup."""
    import shutil
    if not shutil.which("dart"):
        pytest.skip("Dart runtime not installed")

    dart_workspace = Path(__file__).parent / "fixtures" / "dart_simple_math"
    command = ["dart", "run", str(dart_workspace / "bin" / "serve.dart")]

    # Use context manager
    with RPCBridge(command, workspace_path=dart_workspace) as bridge:
        result = bridge.call("add", a=2, b=3)
        assert result == 5

    # Verify process is cleaned up
    assert bridge.process is None


def test_rpc_bridge_manual_cleanup():
    """Test RPCBridge manual close cleanup."""
    import shutil
    if not shutil.which("dart"):
        pytest.skip("Dart runtime not installed")

    dart_workspace = Path(__file__).parent / "fixtures" / "dart_simple_math"
    command = ["dart", "run", str(dart_workspace / "bin" / "serve.dart")]

    bridge = RPCBridge(command, workspace_path=dart_workspace)

    try:
        result = bridge.call("add", a=10, b=20)
        assert result == 30
    finally:
        bridge.close()

    # Verify process is cleaned up
    assert bridge.process is None


def test_rpc_bridge_load_proxy():
    """Test RPCBridge load() creates proxy object."""
    import shutil
    if not shutil.which("dart"):
        pytest.skip("Dart runtime not installed")

    dart_workspace = Path(__file__).parent / "fixtures" / "dart_simple_math"
    command = ["dart", "run", str(dart_workspace / "bin" / "serve.dart")]

    bridge = RPCBridge(command, workspace_path=dart_workspace)

    try:
        proxy = bridge.load()

        # Call methods via proxy
        assert proxy.add(a=7, b=8) == 15
        assert proxy.multiply(a=3, b=4) == 12
    finally:
        bridge.close()


def test_dart_marker_verification(dart_workspace):
    """Test that ADC-IMPLEMENTS markers are found in Dart files."""
    from adc.library_loader.marker_verifier import MarkerVerifier

    verifier = MarkerVerifier(dart_workspace)
    markers = verifier.find_markers([".dart"])

    # Verify markers found
    assert "simple-math-dart" in markers
    assert "simple-math-dart::add" in markers
    assert "simple-math-dart::multiply" in markers
    assert "simple-math-dart::divide" in markers
    assert "rpc-example-01" in markers  # From adc_server.dart


def test_rpc_performance_overhead(dart_workspace):
    """Test that RPC overhead is minimal (<10ms per call)."""
    import shutil
    import time

    if not shutil.which("dart"):
        pytest.skip("Dart runtime not installed")

    lib, metadata = load_library(dart_workspace)

    # Warm up
    for _ in range(5):
        lib.add(a=1, b=1)

    # Measure 100 calls
    start = time.time()
    for i in range(100):
        lib.add(a=i, b=i)
    elapsed = time.time() - start

    avg_time_ms = (elapsed / 100) * 1000

    # Should be well under 10ms per call for local subprocess
    assert avg_time_ms < 10, f"RPC overhead too high: {avg_time_ms:.2f}ms per call"
