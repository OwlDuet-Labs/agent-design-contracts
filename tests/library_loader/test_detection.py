"""Tests for language detection."""

import pytest
from pathlib import Path
import tempfile
import shutil

from adc.library_loader.detection import detect_language, LANGUAGE_INDICATORS
from adc.library_loader.metadata import LanguageType
from adc.library_loader.exceptions import LibraryLoadError


class TestLanguageDetection:
    """Test language detection functionality."""

    def test_detect_python_with_setup_py(self, tmp_path):
        """Test Python detection via setup.py."""
        (tmp_path / "setup.py").write_text("from setuptools import setup")

        language, indicators = detect_language(tmp_path)

        assert language == LanguageType.PYTHON
        assert indicators["setup.py"] is True

    def test_detect_python_with_pyproject_toml(self, tmp_path):
        """Test Python detection via pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        language, indicators = detect_language(tmp_path)

        assert language == LanguageType.PYTHON
        assert indicators["pyproject.toml"] is True

    def test_detect_nodejs_with_package_json(self, tmp_path):
        """Test Node.js detection via package.json."""
        (tmp_path / "package.json").write_text('{"name": "test"}')

        language, indicators = detect_language(tmp_path)

        assert language == LanguageType.NODEJS
        assert indicators["package.json"] is True

    def test_detect_rust_with_cargo_toml(self, tmp_path):
        """Test Rust detection via Cargo.toml."""
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "test"')

        language, indicators = detect_language(tmp_path)

        assert language == LanguageType.RUST
        assert indicators["Cargo.toml"] is True

    def test_detect_go_with_go_mod(self, tmp_path):
        """Test Go detection via go.mod."""
        (tmp_path / "go.mod").write_text('module test')

        language, indicators = detect_language(tmp_path)

        assert language == LanguageType.GO
        assert indicators["go.mod"] is True

    def test_polyglot_project_prefers_highest_score(self, tmp_path):
        """Test that polyglot projects prefer language with most indicators."""
        # Create Python indicators
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        (tmp_path / "requirements.txt").write_text("requests")

        # Create single Node.js indicator
        (tmp_path / "package.json").write_text('{"name": "test"}')

        language, indicators = detect_language(tmp_path)

        # Should prefer Python (3 indicators) over Node.js (1 indicator)
        assert language == LanguageType.PYTHON

    def test_no_indicators_raises_error(self, tmp_path):
        """Test that missing indicators raises LibraryLoadError."""
        with pytest.raises(LibraryLoadError) as exc_info:
            detect_language(tmp_path)

        assert "Unable to detect library language" in str(exc_info.value)
        assert "Fix: Ensure workspace contains language indicator file" in str(exc_info.value)

    def test_nonexistent_path_raises_error(self):
        """Test that nonexistent path raises LibraryLoadError."""
        nonexistent = Path("/nonexistent/path/that/does/not/exist")

        with pytest.raises(LibraryLoadError) as exc_info:
            detect_language(nonexistent)

        assert "does not exist" in str(exc_info.value)

    def test_file_instead_of_directory_raises_error(self, tmp_path):
        """Test that file path (not directory) raises LibraryLoadError."""
        file_path = tmp_path / "somefile.txt"
        file_path.write_text("content")

        with pytest.raises(LibraryLoadError) as exc_info:
            detect_language(file_path)

        assert "not a directory" in str(exc_info.value)
