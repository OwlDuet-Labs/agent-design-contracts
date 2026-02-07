"""Integration tests for load_library function."""

import pytest
from pathlib import Path

from adc.library_loader import load_library, LibraryMetadata, BridgeType, LanguageType
from adc.library_loader.exceptions import LibraryLoadError


class TestLoadLibrary:
    """Test complete load_library integration."""

    @pytest.fixture
    def simple_lib_path(self):
        """Path to simple Python test library."""
        return Path(__file__).parent / "fixtures" / "simple_python_lib"

    def test_load_python_library(self, simple_lib_path):
        """Test loading Python library returns correct metadata."""
        lib, metadata = load_library(simple_lib_path)

        # Check metadata
        assert isinstance(metadata, LibraryMetadata)
        assert metadata.detected_language == LanguageType.PYTHON
        assert metadata.bridge_type == BridgeType.PYTHON_DIRECT
        assert metadata.supports_signature_verification is True
        assert metadata.supports_type_introspection is True
        assert metadata.supports_docstring_verification is True
        assert metadata.verification_level == "FULL"
        assert metadata.load_time_ms > 0

        # Check library proxy works
        assert hasattr(lib, "create_task")
        result = lib.create_task(title="Test", description="Test task")
        assert result["title"] == "Test"

    def test_load_library_with_expected_language(self, simple_lib_path):
        """Test forcing language detection."""
        lib, metadata = load_library(simple_lib_path, expected_language="python")

        assert metadata.detected_language == LanguageType.PYTHON

    def test_load_library_nonexistent_path_raises_error(self):
        """Test that nonexistent path raises error."""
        with pytest.raises(LibraryLoadError):
            load_library("/nonexistent/path")

    def test_load_time_measured(self, simple_lib_path):
        """Test that load time is measured correctly."""
        lib, metadata = load_library(simple_lib_path)

        # Load time should be reasonable (under 1 second for simple module)
        assert metadata.load_time_ms > 0
        assert metadata.load_time_ms < 1000  # Less than 1 second
