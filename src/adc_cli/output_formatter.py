# ADC-IMPLEMENTS: <cli-output-feature-01>
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class StructuredOutput:
    """Standardized output format for all CLI commands."""
    
    status: str  # "success", "error", "warning"
    timestamp: str
    command: str
    execution_time_ms: float
    data: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    errors: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)


# ADC-IMPLEMENTS: <cli-output-feature-01>
class OutputFormatter:
    """Formats CLI output according to ADC best practices."""
    
    @staticmethod
    def format_json_output(
        command: str,
        data: Dict,
        status: str = "success",
        execution_time_ms: float = 0.0,
        errors: List[Dict] = None,
        warnings: List[Dict] = None
    ) -> str:
        """Format output as structured JSON."""
        output = StructuredOutput(
            status=status,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            command=command,
            execution_time_ms=execution_time_ms,
            data=data,
            metadata={
                "version": "1.0.0",  # CLI version
                "environment": "development"  # Could be configurable
            },
            errors=errors or [],
            warnings=warnings or []
        )
        
        return json.dumps(asdict(output), indent=2)
    
    @staticmethod
    def format_error(
        command: str,
        error_code: str,
        message: str,
        details: Dict = None,
        severity: str = "high"
    ) -> Dict:
        """Format error information according to ADC schema."""
        return {
            "code": error_code,
            "message": message,
            "details": details or {},
            "severity": severity
        }
    
    @staticmethod
    def format_validation_output(validation_results: Dict) -> str:
        """Format contract validation results for human-readable output."""
        lines = []
        lines.append("=" * 60)
        lines.append("CONTRACT VALIDATION RESULTS")
        lines.append("=" * 60)
        
        if "validation_summary" in validation_results:
            summary = validation_results["validation_summary"]
            lines.append(f"Total Contracts: {summary.get('total_contracts', 0)}")
            lines.append(f"Implemented: {summary.get('implemented', 0)}")
            lines.append(f"Partial: {summary.get('partial', 0)}")
            lines.append(f"Missing: {summary.get('missing', 0)}")
            lines.append(f"Compliance Score: {summary.get('compliance_score', 0.0):.2f}")
            lines.append("")
        
        if "contract_details" in validation_results:
            lines.append("Contract Details:")
            for contract in validation_results["contract_details"]:
                status = contract.get("implementation_status", "unknown")
                contract_id = contract.get("contract_id", "unknown")
                lines.append(f"  {contract_id}: {status.upper()}")
                
                if contract.get("missing_implementations"):
                    lines.append(f"    Missing: {', '.join(contract['missing_implementations'])}")
        
        if validation_results.get("recommendations"):
            lines.append("")
            lines.append("Recommendations:")
            for rec in validation_results["recommendations"]:
                lines.append(f"  - {rec}")
        
        lines.append("=" * 60)
        return "\n".join(lines)