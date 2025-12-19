"""
Verification result models for Universal Library Loader.

This module defines data structures for reporting interface verification
results against ADC contracts.
"""

# ADC-IMPLEMENTS: <ull-model-02>

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime

from .metadata import LibraryMetadata


@dataclass
class SignatureMismatch:
    """Details of a signature mismatch."""
    function_name: str
    expected_signature: str
    found_signature: str
    mismatch_details: List[str]  # ["Missing parameter 'description'", ...]


@dataclass
class VerificationResult:
    """Result of verifying library against contract."""

    # Overall status
    is_compliant: bool
    verification_level: str  # "FULL", "LIMITED", "MARKER_ONLY"

    # Function existence checks
    required_functions_found: List[str]
    required_functions_missing: List[str]

    # Signature verification (only if supports_signature_verification)
    signature_matches: Dict[str, bool]  # {function_name: matches}
    signature_mismatches: List[SignatureMismatch]

    # Type verification (only if supports_type_introspection)
    type_mismatches: List[str]

    # Docstring verification (only if supports_docstring_verification)
    missing_docstrings: List[str]

    # Marker verification (always performed)
    adc_implements_markers_found: List[str]  # ["<block-id-1>", "<block-id-2>", ...]
    adc_implements_markers_missing: List[str]  # Expected but not found

    # Metadata
    verification_timestamp: str  # ISO format
    library_metadata: LibraryMetadata

    # Error details
    verification_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def compliance_score(self) -> float:
        """Calculate compliance score 0.0-1.0."""
        total_checks = len(self.required_functions_found) + len(self.required_functions_missing)
        if total_checks == 0:
            return 0.0

        passed_checks = len(self.required_functions_found)

        # Deduct for signature mismatches if verification supported
        if self.library_metadata.supports_signature_verification:
            passed_checks -= len(self.signature_mismatches)

        # Deduct for missing markers (always required)
        passed_checks -= len(self.adc_implements_markers_missing)

        return max(0.0, min(1.0, passed_checks / total_checks))

    @property
    def is_passing(self) -> bool:
        """Check if verification passes minimum requirements."""
        return (
            self.is_compliant
            and len(self.required_functions_missing) == 0
            and len(self.adc_implements_markers_missing) == 0
            and self.compliance_score >= 0.8
        )
