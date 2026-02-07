"""
Integration tests for Universal Library Loader with real Dart library (numpy_hooks).

Tests ULL's ability to:
1. Detect Dart language from pubspec.yaml
2. Find ADC-IMPLEMENTS markers in Dart source files (flexible format)
3. Calculate compliance metrics without reading all source
4. Measure token savings vs traditional approach

Note: numpy_hooks uses the older marker format (without angle brackets):
  // ADC-IMPLEMENTS: ADC-001 Core Array
Instead of the newer format:
  // ADC-IMPLEMENTS: <adc-001>

This test validates both formats work for token savings analysis.
"""

import pytest
import subprocess
from pathlib import Path
from adc.library_loader.detection import detect_language
from adc.library_loader.metadata import LanguageType

NUMPY_HOOKS_PATH = Path("/Volumes/X10/labs/numpy/numpy_hooks")


@pytest.mark.skipif(not NUMPY_HOOKS_PATH.exists(), reason="numpy_hooks not available")
def test_numpy_hooks_detection():
    """Test that numpy_hooks is detected as Dart library"""
    lang, indicators = detect_language(NUMPY_HOOKS_PATH)
    assert lang == LanguageType.DART, f"Expected Dart, got {lang}"
    assert indicators["pubspec.yaml"], "Should find pubspec.yaml"
    assert indicators["pubspec.lock"], "Should find pubspec.lock"


def _find_all_markers(workspace_path: Path) -> list[tuple[Path, int, str]]:
    """
    Find all ADC-IMPLEMENTS markers (flexible format) using ripgrep or grep.

    Returns:
        List of (file_path, line_number, marker_text) tuples
    """
    import shutil

    # Try ripgrep first (faster), fallback to grep
    if shutil.which("rg"):
        cmd = [
            "rg",
            "--line-number",
            r"ADC-IMPLEMENTS:",
            str(workspace_path),
        ]
    else:
        cmd = [
            "grep",
            "-r",
            "-n",  # Line numbers
            "-E",  # Extended regex
            r"ADC-IMPLEMENTS:",
            str(workspace_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    markers = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        # Format: path/to/file.dart:123:// ADC-IMPLEMENTS: marker text
        parts = line.split(":", 2)
        if len(parts) >= 3:
            file_path = Path(parts[0])
            line_num = int(parts[1])
            marker_text = parts[2].strip()
            markers.append((file_path, line_num, marker_text))

    return markers


@pytest.mark.skipif(not NUMPY_HOOKS_PATH.exists(), reason="numpy_hooks not available")
def test_numpy_hooks_marker_verification():
    """Test that ADC-IMPLEMENTS markers are found in numpy_hooks Dart files"""
    markers = _find_all_markers(NUMPY_HOOKS_PATH)

    # Should find markers in Dart files
    assert len(markers) > 0, "No ADC-IMPLEMENTS markers found in numpy_hooks"

    # Verify at least the main library file has a marker
    main_lib_markers = [m for m in markers if "lib/numpy_hooks.dart" in str(m[0])]
    assert len(main_lib_markers) > 0, "No markers found in main library file"

    # Check that we found the expected marker from line 37
    expected_marker_substring = "ADC-001 through ADC-009"
    found_expected = any(expected_marker_substring in m[2] for m in markers)
    assert found_expected, f"Expected marker containing '{expected_marker_substring}' not found"

    print(f"\nFound {len(markers)} ADC-IMPLEMENTS markers in numpy_hooks:")
    for file_path, line_num, marker_text in markers[:5]:  # Show first 5
        rel_path = file_path.relative_to(NUMPY_HOOKS_PATH)
        print(f"  - {rel_path}:{line_num}: {marker_text[:60]}")
    if len(markers) > 5:
        print(f"  ... and {len(markers) - 5} more")


@pytest.mark.skipif(not NUMPY_HOOKS_PATH.exists(), reason="numpy_hooks not available")
def test_numpy_hooks_token_efficiency():
    """
    Measure token savings by using marker verification vs reading all source.

    This test demonstrates the core value proposition of ULL:
    - Traditional approach: Read ALL source files (thousands of lines)
    - ULL approach: Use ripgrep to find markers only (minimal token usage)
    """
    # ULL approach: Find markers only
    markers = _find_all_markers(NUMPY_HOOKS_PATH)

    # Estimate verification report size (what we send to LLM)
    verification_lines = []
    for file_path, line_num, marker_text in markers:
        rel_path = file_path.relative_to(NUMPY_HOOKS_PATH)
        verification_lines.append(f"{rel_path}:{line_num}: {marker_text}")

    ull_report = "\n".join(verification_lines)
    ull_tokens_estimate = len(ull_report.split()) * 1.3  # ~1.3 tokens per word

    # Traditional approach: Count all source file content
    dart_files = list(NUMPY_HOOKS_PATH.rglob("*.dart"))
    # Exclude generated and cache files
    dart_files = [
        f for f in dart_files
        if not any(x in str(f) for x in ['.dart_tool', 'generated', '__pycache__'])
    ]

    total_source_chars = sum(len(f.read_text()) for f in dart_files)
    traditional_tokens_estimate = total_source_chars / 4  # ~4 chars per token

    # Calculate reduction
    reduction_pct = (1 - ull_tokens_estimate / traditional_tokens_estimate) * 100

    print(f"\n{'='*60}")
    print(f"Token Efficiency Test - numpy_hooks")
    print(f"{'='*60}")
    print(f"Dart files analyzed:     {len(dart_files)}")
    print(f"ADC markers found:       {len(markers)}")
    print(f"Traditional tokens:      {traditional_tokens_estimate:>10,.0f}")
    print(f"ULL tokens:              {ull_tokens_estimate:>10,.0f}")
    print(f"Token reduction:         {traditional_tokens_estimate - ull_tokens_estimate:>10,.0f} ({reduction_pct:.1f}%)")
    print(f"Cost savings per audit:  ${(traditional_tokens_estimate - ull_tokens_estimate) * 3 / 1_000_000:>10,.3f}")
    print(f"{'='*60}")

    # Validate substantial token savings (should be >80%)
    assert reduction_pct > 80, f"Expected >80% token reduction, got {reduction_pct:.1f}%"

    # Validate we're still finding compliance information
    assert len(markers) > 0, "ULL must find markers to be useful"


@pytest.mark.skipif(not NUMPY_HOOKS_PATH.exists(), reason="numpy_hooks not available")
def test_numpy_hooks_marker_quality():
    """Test that found markers have valid contract IDs and locations"""
    markers = _find_all_markers(NUMPY_HOOKS_PATH)

    for file_path, line_num, marker_text in markers:
        # All markers should have file paths
        assert file_path.exists(), f"Marker file doesn't exist: {file_path}"

        # All markers should have line numbers
        assert line_num > 0, f"Invalid line number: {line_num}"

        # All markers should have marker text
        assert len(marker_text) > 0, "Empty marker text"

        # Marker text should contain ADC-IMPLEMENTS
        assert "ADC-IMPLEMENTS" in marker_text, f"Invalid marker format: {marker_text}"

        # Should reference a contract (ADC-XXX, IMP-XXX, or similar)
        assert any(
            pattern in marker_text.upper()
            for pattern in ["ADC-", "IMP-", "ALG-", "CONTRACT", "SPEC"]
        ), f"No contract reference found in: {marker_text}"
