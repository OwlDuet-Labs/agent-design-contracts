"""Tests for Python bridge."""

import pytest
from pathlib import Path

from adc.library_loader.bridges.python_bridge import PythonBridge
from adc.library_loader.exceptions import LibraryLoadError, InterfaceConformanceError


class TestPythonBridge:
    """Test Python bridge functionality."""

    @pytest.fixture
    def simple_lib_path(self):
        """Path to simple Python test library."""
        return Path(__file__).parent / "fixtures" / "simple_python_lib"

    def test_load_simple_library(self, simple_lib_path):
        """Test loading a simple Python library."""
        bridge = PythonBridge(simple_lib_path)
        lib = bridge.load()

        # Verify functions are accessible
        assert hasattr(lib, "create_task")
        assert hasattr(lib, "list_tasks")
        assert hasattr(lib, "complete_task")

        # Verify functions are callable
        assert callable(lib.create_task)
        assert callable(lib.list_tasks)
        assert callable(lib.complete_task)

    def test_call_loaded_functions(self, simple_lib_path):
        """Test calling functions from loaded library."""
        bridge = PythonBridge(simple_lib_path)
        lib = bridge.load()

        # Test create_task
        result = lib.create_task(title="Test", description="Test task")
        assert result["title"] == "Test"
        assert result["description"] == "Test task"
        assert "id" in result

        # Test list_tasks
        tasks = lib.list_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) > 0

        # Test complete_task
        completed = lib.complete_task(task_id="task-1")
        assert completed["id"] == "task-1"
        assert completed["completed"] is True

    def test_get_signature(self, simple_lib_path):
        """Test signature introspection."""
        bridge = PythonBridge(simple_lib_path)
        bridge.load()

        # Get signature for create_task
        sig = bridge.get_signature("create_task")

        # Verify parameters
        assert "title" in sig.parameters
        assert "description" in sig.parameters

        # Verify parameter annotations
        assert sig.parameters["title"].annotation == str
        assert sig.parameters["description"].annotation == str

    def test_get_signature_for_missing_function_raises_error(self, simple_lib_path):
        """Test that getting signature for missing function raises error."""
        bridge = PythonBridge(simple_lib_path)
        bridge.load()

        with pytest.raises(InterfaceConformanceError) as exc_info:
            bridge.get_signature("nonexistent_function")

        assert "not found" in str(exc_info.value)

    def test_verify_signature_matching(self, simple_lib_path):
        """Test signature verification for matching signatures."""
        bridge = PythonBridge(simple_lib_path)
        bridge.load()

        matches, mismatches = bridge.verify_signature(
            "create_task",
            expected_params={"title": str, "description": str},
            expected_return=dict
        )

        assert matches is True
        assert len(mismatches) == 0

    def test_verify_signature_missing_parameter(self, simple_lib_path):
        """Test signature verification detects missing parameters."""
        bridge = PythonBridge(simple_lib_path)
        bridge.load()

        matches, mismatches = bridge.verify_signature(
            "create_task",
            expected_params={"title": str, "description": str, "priority": int},
            expected_return=dict
        )

        assert matches is False
        assert any("Missing parameter 'priority'" in m for m in mismatches)

    def test_get_docstring(self, simple_lib_path):
        """Test docstring extraction."""
        bridge = PythonBridge(simple_lib_path)
        bridge.load()

        docstring = bridge.get_docstring("create_task")

        assert docstring is not None
        assert "Create a new task" in docstring
        assert "Args:" in docstring
        assert "Returns:" in docstring

    def test_load_nonexistent_module_raises_error(self, tmp_path):
        """Test that loading nonexistent module raises error."""
        # Create empty directory with no Python module
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        bridge = PythonBridge(empty_dir)

        with pytest.raises(LibraryLoadError) as exc_info:
            bridge.load()

        assert "Unable to detect Python module name" in str(exc_info.value)
