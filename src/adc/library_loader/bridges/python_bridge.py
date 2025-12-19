"""
Python direct import bridge for Universal Library Loader.

This bridge loads Python libraries directly using importlib and provides
full signature introspection using the inspect module.
"""

# ADC-IMPLEMENTS: <ull-feature-02>

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..exceptions import LibraryLoadError, InterfaceConformanceError


class PythonBridge:
    """Direct Python library loading with full introspection."""

    def __init__(self, workspace_path: Path):
        """
        Initialize Python bridge.

        Args:
            workspace_path: Path to Python workspace
        """
        self.workspace_path = workspace_path
        self.module = None
        self.module_name = None

    def _detect_module_name(self) -> str:
        """
        Detect main module name from setup.py, pyproject.toml, or directory structure.

        Returns:
            Module name to import

        Raises:
            LibraryLoadError: If module name cannot be detected
        """
        # Strategy 1: Parse pyproject.toml
        pyproject_path = self.workspace_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                # Python 3.11+ has tomllib built-in, Python 3.10 needs tomli
                try:
                    import tomllib
                except ImportError:
                    import tomli as tomllib

                with open(pyproject_path, "rb") as f:
                    config = tomllib.load(f)
                    # Try to find package name
                    if "project" in config and "name" in config["project"]:
                        return config["project"]["name"].replace("-", "_")
                    if "tool" in config and "poetry" in config["tool"]:
                        if "name" in config["tool"]["poetry"]:
                            return config["tool"]["poetry"]["name"].replace("-", "_")
            except Exception:
                pass  # Fall through to next strategy

        # Strategy 2: Look for setup.py
        setup_py = self.workspace_path / "setup.py"
        if setup_py.exists():
            try:
                import re
                content = setup_py.read_text()
                # Look for name= parameter in setup()
                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1).replace("-", "_")
            except Exception:
                pass

        # Strategy 3: Find src/ directory with __init__.py
        src_dir = self.workspace_path / "src"
        if src_dir.exists():
            for item in src_dir.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    return item.name

        # Strategy 4: Find any directory with __init__.py at workspace root
        for item in self.workspace_path.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                # Skip common non-package directories
                if item.name not in ["tests", "test", "docs", "examples", "scripts"]:
                    return item.name

        raise LibraryLoadError(
            f"Unable to detect Python module name in {self.workspace_path}\n"
            f"  Checked: pyproject.toml, setup.py, src/ directory, root directory\n"
            f"  Fix: Ensure workspace has pyproject.toml, setup.py, or module with __init__.py"
        )

    def load(self) -> Any:
        """
        Load Python module and return importable object.

        Returns:
            Module proxy object with library functions

        Raises:
            LibraryLoadError: If module cannot be imported
        """
        # Detect module name
        self.module_name = self._detect_module_name()

        # Check if workspace itself is the module (has __init__.py directly)
        is_direct_module = (self.workspace_path / "__init__.py").exists()

        if is_direct_module:
            # Workspace directory IS the module - add parent to sys.path
            parent_path = str(self.workspace_path.parent)
            module_name = self.workspace_path.name
            paths_to_try = [parent_path]
        else:
            # Standard package structure - try src/ then workspace root
            workspace_str = str(self.workspace_path)
            src_path = str(self.workspace_path / "src")
            paths_to_try = [src_path, workspace_str]
            module_name = self.module_name

        # Add paths to sys.path
        for path in paths_to_try:
            if path not in sys.path:
                sys.path.insert(0, path)

        try:
            # Try to import the module
            self.module = importlib.import_module(module_name)
            return self._create_proxy(self.module)
        except ImportError as e:
            raise LibraryLoadError(
                f"Failed to import Python module '{module_name}'\n"
                f"  Workspace: {self.workspace_path}\n"
                f"  Error: {e}\n"
                f"  Fix: Ensure module is importable (check __init__.py and dependencies)"
            )
        finally:
            # Clean up sys.path to avoid pollution
            for path in paths_to_try:
                if path in sys.path:
                    sys.path.remove(path)

    def _create_proxy(self, module: Any) -> Any:
        """
        Create proxy object with all public module functions.

        Args:
            module: Imported Python module

        Returns:
            Proxy object with module functions as attributes
        """
        class ModuleProxy:
            """Proxy object that exposes module functions."""
            pass

        proxy = ModuleProxy()
        proxy.__module_ref__ = module  # Store reference for introspection

        # Copy all public functions and classes to proxy
        for name in dir(module):
            if not name.startswith('_'):
                attr = getattr(module, name)
                setattr(proxy, name, attr)

        return proxy

    def get_signature(self, function_name: str) -> inspect.Signature:
        """
        Get function signature for verification.

        Args:
            function_name: Name of function to inspect

        Returns:
            Function signature object

        Raises:
            InterfaceConformanceError: If function not found
        """
        if self.module is None:
            raise LibraryLoadError("Module not loaded - call load() first")

        func = getattr(self.module, function_name, None)
        if func is None:
            raise InterfaceConformanceError(
                f"Function '{function_name}' not found in module '{self.module_name}'"
            )

        if not callable(func):
            raise InterfaceConformanceError(
                f"'{function_name}' is not callable in module '{self.module_name}'"
            )

        return inspect.signature(func)

    def verify_signature(
        self,
        function_name: str,
        expected_params: Dict[str, type],
        expected_return: type
    ) -> Tuple[bool, List[str]]:
        """
        Verify function signature matches expected contract.

        Args:
            function_name: Name of function to verify
            expected_params: Expected parameters {name: type}
            expected_return: Expected return type

        Returns:
            (matches, mismatch_details)
        """
        try:
            sig = self.get_signature(function_name)
        except InterfaceConformanceError as e:
            return False, [str(e)]

        mismatches = []

        # Check parameters
        for param_name, param_type in expected_params.items():
            if param_name not in sig.parameters:
                mismatches.append(f"Missing parameter '{param_name}'")
            else:
                param = sig.parameters[param_name]
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation != param_type:
                        mismatches.append(
                            f"Parameter '{param_name}' type mismatch: "
                            f"expected {param_type}, found {param.annotation}"
                        )

        # Check return type
        if sig.return_annotation != inspect.Signature.empty:
            if sig.return_annotation != expected_return:
                mismatches.append(
                    f"Return type mismatch: "
                    f"expected {expected_return}, found {sig.return_annotation}"
                )

        return len(mismatches) == 0, mismatches

    def get_docstring(self, function_name: str) -> str:
        """
        Get function docstring.

        Args:
            function_name: Name of function

        Returns:
            Docstring content or empty string if no docstring

        Raises:
            InterfaceConformanceError: If function not found
        """
        if self.module is None:
            raise LibraryLoadError("Module not loaded - call load() first")

        func = getattr(self.module, function_name, None)
        if func is None:
            raise InterfaceConformanceError(
                f"Function '{function_name}' not found in module '{self.module_name}'"
            )

        return inspect.getdoc(func) or ""
