"""
ADC-IMPLEMENTS marker verification via grep.

This module searches for ADC-IMPLEMENTS markers in source code to verify
that contract blocks are properly linked to implementation code.
"""

# ADC-IMPLEMENTS: <ull-feature-05>

import subprocess
from pathlib import Path
from typing import List, Set, Tuple

from .exceptions import LibraryLoadError


class MarkerVerifier:
    """Verify ADC-IMPLEMENTS markers via grep."""

    def __init__(self, workspace_path: Path):
        """
        Initialize marker verifier.

        Args:
            workspace_path: Path to workspace to search for markers
        """
        self.workspace_path = workspace_path

    def find_markers(self, file_extensions: List[str] = None) -> Set[str]:
        """
        Find all ADC-IMPLEMENTS markers in workspace.

        Args:
            file_extensions: File types to search (e.g., [".py", ".js"])
                            If None, search all text files

        Returns:
            Set of block IDs found in markers

        Raises:
            LibraryLoadError: If search times out or fails
        """
        # Try ripgrep first for better performance
        try:
            return self._find_markers_with_rg(file_extensions)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Fallback to grep if ripgrep not available
            return self._find_markers_with_grep(file_extensions)

    def _find_markers_with_rg(self, file_extensions: List[str] = None) -> Set[str]:
        """Find markers using ripgrep (rg) for fast searching."""
        # Pattern: ADC-IMPLEMENTS:\s*<([^>]+)>
        cmd = [
            "rg",
            "--no-heading",
            "--no-filename",
            r"ADC-IMPLEMENTS:\s*<([^>]+)>",
            "--only-matching",
            "--replace", "$1",  # Extract only block ID
            str(self.workspace_path),
        ]

        if file_extensions:
            for ext in file_extensions:
                cmd.extend(["--glob", f"*{ext}"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse output (one block ID per line)
            markers = set(result.stdout.strip().split("\n"))
            markers.discard("")  # Remove empty strings

            return markers
        except subprocess.TimeoutExpired:
            raise LibraryLoadError(
                f"Marker search timed out after 10 seconds\n"
                f"  Workspace: {self.workspace_path}\n"
                f"  Fix: Reduce workspace size or install ripgrep (rg)"
            )

    def _find_markers_with_grep(self, file_extensions: List[str] = None) -> Set[str]:
        """Fallback to grep if ripgrep not available."""
        # Build grep command
        cmd = [
            "grep",
            "-r",
            "-h",  # No filename
            "-o",  # Only matching
            "-E",  # Extended regex
            r"ADC-IMPLEMENTS:\s*<([^>]+)>",
            str(self.workspace_path),
        ]

        # Add file type filters if specified
        if file_extensions:
            # grep uses --include for file patterns
            for ext in file_extensions:
                cmd.extend(["--include", f"*{ext}"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse output - grep returns full match, need to extract block ID
            import re
            pattern = r"ADC-IMPLEMENTS:\s*<([^>]+)>"
            markers = set()

            for line in result.stdout.strip().split("\n"):
                if line:
                    match = re.search(pattern, line)
                    if match:
                        markers.add(match.group(1))

            return markers
        except subprocess.TimeoutExpired:
            raise LibraryLoadError(
                f"Marker search timed out after 10 seconds\n"
                f"  Workspace: {self.workspace_path}\n"
                f"  Fix: Reduce workspace size"
            )
        except FileNotFoundError:
            # No grep available
            raise LibraryLoadError(
                f"Neither ripgrep (rg) nor grep found\n"
                f"  Fix: Install ripgrep or ensure grep is in PATH"
            )

    def verify_coverage(
        self,
        required_block_ids: Set[str],
        found_markers: Set[str]
    ) -> Tuple[bool, Set[str]]:
        """
        Verify that all required contract blocks have markers.

        Args:
            required_block_ids: Set of block IDs from contract
            found_markers: Set of block IDs found in source

        Returns:
            (is_complete, missing_block_ids)
        """
        missing = required_block_ids - found_markers
        return len(missing) == 0, missing
