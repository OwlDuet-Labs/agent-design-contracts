"""
Contract interface extractor for Universal Library Loader.

This module parses ADC contracts to extract expected interface specifications
for verification purposes.
"""

# ADC-IMPLEMENTS: <ull-tool-01>

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set

from .exceptions import LibraryLoadError


@dataclass
class FunctionSignature:
    """Expected function signature from contract."""
    name: str
    parameters: Dict[str, type]  # {param_name: param_type}
    return_type: type
    is_required: bool


@dataclass
class ExpectedInterface:
    """Expected interface extracted from ADC contract."""

    contract_id: str

    # Functions and their signatures
    required_functions: Dict[str, FunctionSignature]

    # Block IDs that must have ADC-IMPLEMENTS markers
    required_block_ids: Set[str]

    # Optional: expected docstrings
    expected_docstrings: Dict[str, str]


class ContractInterfaceExtractor:
    """Extract expected interface from ADC contract."""

    def extract(self, contract_path: Path) -> ExpectedInterface:
        """
        Parse contract and extract interface specification.

        Looks for:
        - [APIEndpoint] blocks with function signatures
        - [Feature] blocks with method specifications
        - [DataModel] blocks for type definitions
        - Block IDs for marker verification

        Args:
            contract_path: Path to ADC contract file

        Returns:
            Expected interface specification

        Raises:
            LibraryLoadError: If contract cannot be parsed
        """
        if not contract_path.exists():
            raise LibraryLoadError(
                f"Contract file not found: {contract_path}\n"
                f"  Fix: Ensure contract path is correct"
            )

        contract_text = contract_path.read_text()

        # Extract contract ID from YAML front matter
        contract_id = self._extract_contract_id(contract_text)

        # Extract block IDs for marker verification
        required_block_ids = self._extract_block_ids(contract_text)

        # Extract function signatures (simplified for Phase 1)
        # Full signature parsing would require more sophisticated AST parsing
        required_functions = self._extract_functions(contract_text)

        return ExpectedInterface(
            contract_id=contract_id,
            required_functions=required_functions,
            required_block_ids=required_block_ids,
            expected_docstrings={},
        )

    def _extract_contract_id(self, contract_text: str) -> str:
        """
        Extract contract_id from YAML front matter.

        Args:
            contract_text: Full contract content

        Returns:
            Contract ID string

        Raises:
            LibraryLoadError: If contract ID not found
        """
        # Parse YAML between --- markers
        yaml_match = re.search(r'^---\n(.*?)\n---', contract_text, re.DOTALL | re.MULTILINE)
        if yaml_match:
            yaml_text = yaml_match.group(1)
            id_match = re.search(r'contract_id:\s*(.+)', yaml_text)
            if id_match:
                return id_match.group(1).strip()

        raise LibraryLoadError(
            f"Could not find contract_id in contract YAML front matter\n"
            f"  Fix: Ensure contract has YAML front matter with contract_id field"
        )

    def _extract_block_ids(self, contract_text: str) -> Set[str]:
        """
        Extract all block IDs from contract.

        Block IDs appear in headers like: ## [Section] <block-id>

        Args:
            contract_text: Full contract content

        Returns:
            Set of block IDs
        """
        # Pattern: <block-id> at end of section headers
        pattern = r'<([a-zA-Z0-9_-]+)>'
        matches = re.findall(pattern, contract_text)
        return set(matches)

    def _extract_functions(self, contract_text: str) -> Dict[str, FunctionSignature]:
        """
        Extract function signatures from contract blocks.

        This is a simplified implementation for Phase 1. A complete implementation
        would use AST parsing to extract full type information.

        Args:
            contract_text: Full contract content

        Returns:
            Dictionary of function signatures
        """
        functions = {}

        # Look for Python function definitions in code blocks
        # Pattern: def function_name(param: type, ...) -> return_type:
        code_blocks = re.findall(r'```python\n(.*?)\n```', contract_text, re.DOTALL)

        for block in code_blocks:
            # Find function definitions
            func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            func_matches = re.finditer(func_pattern, block)

            for match in func_matches:
                func_name = match.group(1)
                # For now, just mark as required without detailed signature parsing
                # Full signature parsing would require ast module
                functions[func_name] = FunctionSignature(
                    name=func_name,
                    parameters={},  # Simplified for Phase 1
                    return_type=type(None),  # Simplified for Phase 1
                    is_required=True,
                )

        return functions
