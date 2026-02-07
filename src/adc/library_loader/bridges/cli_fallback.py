"""
CLI fallback bridge for Universal Library Loader.

This bridge provides limited verification capabilities for compiled languages
by executing CLI commands. Used for Go, Rust, Java, C++ in Phase 1.
"""

# ADC-IMPLEMENTS: <ull-feature-04>

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from ..exceptions import LibraryLoadError, InterfaceConformanceError


# Documentation of limitations
CLI_VERIFICATION_LIMITATIONS = """
CLI Fallback Bridge Limitations:

✅ CAN VERIFY:
- Command exists and is executable
- Basic output format
- Help text presence
- Exit codes

❌ CANNOT VERIFY:
- Type signatures
- Parameter annotations
- Return types
- Docstring compliance

RECOMMENDATION: Implement Python bindings for full verification.
See Phase 2 contracts for Go/Rust/Java binding generation.
"""


class CliFallbackBridge:
    """CLI-based verification for compiled languages (Phase 1)."""

    def __init__(self, workspace_path: Path):
        """
        Initialize CLI fallback bridge.

        Args:
            workspace_path: Path to workspace containing CLI executable
        """
        self.workspace_path = workspace_path
        self.cli_executable = None

    def _detect_cli_executable(self) -> Path:
        """
        Find CLI executable in workspace.

        Returns:
            Path to executable file

        Raises:
            LibraryLoadError: If no executable found
        """
        # Common locations for compiled executables
        search_dirs = [
            self.workspace_path / "bin",
            self.workspace_path / "build",
            self.workspace_path / "target" / "release",  # Rust
            self.workspace_path / "target" / "debug",    # Rust debug
            self.workspace_path / "dist",
            self.workspace_path,  # Check root directory too
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Find executable files
            for file in search_dir.iterdir():
                if file.is_file():
                    # Check if executable (Unix permission bit)
                    try:
                        if file.stat().st_mode & 0o111:  # Executable bit
                            # Skip common non-CLI executables
                            if file.suffix not in [".so", ".dylib", ".dll", ".a"]:
                                return file
                    except OSError:
                        continue

        searched_paths = ", ".join(str(d) for d in search_dirs if d.exists())
        raise LibraryLoadError(
            f"No CLI executable found in {self.workspace_path}\n"
            f"  Searched: {searched_paths}\n"
            f"  Fix: Build your project first, or implement Python bindings\n"
            f"  Phase 2: See contracts/universal-library-loader/002-phase2-bindings.qmd"
        )

    def verify_commands_exist(self, required_commands: List[str]) -> Dict[str, bool]:
        """
        Verify that required CLI commands exist.

        This is LIMITED verification - we can only check if commands exist,
        not their signatures or types.

        Args:
            required_commands: List of command names to verify

        Returns:
            Dictionary mapping command names to existence boolean
        """
        if self.cli_executable is None:
            self.cli_executable = self._detect_cli_executable()

        results = {}

        for command in required_commands:
            try:
                # Try running: <executable> <command> --help
                result = subprocess.run(
                    [str(self.cli_executable), command, "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                # Command exists if exit code is 0 or help text present
                results[command] = (
                    result.returncode == 0
                    or "usage" in result.stdout.lower()
                    or "help" in result.stdout.lower()
                )
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                results[command] = False

        return results

    def load(self) -> Any:
        """
        Create proxy for CLI execution.

        Note: This does NOT provide signature verification.
        Use only for basic command existence checks.

        Returns:
            Proxy object for calling CLI commands

        Raises:
            LibraryLoadError: If executable cannot be found
        """
        self.cli_executable = self._detect_cli_executable()

        bridge = self

        class CliProxy:
            """Proxy object that forwards calls to CLI executable."""

            def __getattr__(self, name):
                """
                Create callable for any attribute access.

                Args:
                    name: Command name

                Returns:
                    Callable that executes the CLI command
                """
                def call_command(*args, **kwargs):
                    """
                    Execute CLI command.

                    Args:
                        *args: Positional arguments (passed as-is)
                        **kwargs: Keyword arguments (converted to --key value)

                    Returns:
                        stdout from command

                    Raises:
                        InterfaceConformanceError: If command fails
                    """
                    # Build command line
                    cli_args = [str(bridge.cli_executable), name]

                    # Add positional args
                    cli_args.extend(str(arg) for arg in args)

                    # Add keyword args as --key value
                    for k, v in kwargs.items():
                        # Convert underscores to hyphens (Python convention)
                        key = k.replace("_", "-")
                        cli_args.extend([f"--{key}", str(v)])

                    # Execute command
                    try:
                        result = subprocess.run(
                            cli_args,
                            capture_output=True,
                            text=True,
                            cwd=str(bridge.workspace_path),
                            timeout=30,
                        )

                        if result.returncode != 0:
                            raise InterfaceConformanceError(
                                f"CLI command failed: {name}\n"
                                f"  Command: {' '.join(cli_args)}\n"
                                f"  Exit code: {result.returncode}\n"
                                f"  Error: {result.stderr}"
                            )

                        return result.stdout
                    except subprocess.TimeoutExpired:
                        raise InterfaceConformanceError(
                            f"CLI command timed out after 30 seconds: {name}\n"
                            f"  Command: {' '.join(cli_args)}"
                        )

                return call_command

        return CliProxy()

    def get_limitations(self) -> str:
        """
        Get documentation about CLI bridge limitations.

        Returns:
            Formatted string describing verification limitations
        """
        return CLI_VERIFICATION_LIMITATIONS
