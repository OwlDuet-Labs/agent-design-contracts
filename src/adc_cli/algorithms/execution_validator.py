# ADC-IMPLEMENTS: <cli-execution-algorithm-01>
import json
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ValidationResult:
    """Result of execution validation."""
    
    valid: bool
    error: str = ""


# ADC-IMPLEMENTS: <cli-execution-algorithm-01>
class ExecutionValidator:
    """Algorithm for validating CLI command execution and ensuring auditor-compatible output."""
    
    def validate_command_structure(self, command: str, args: List[str]) -> bool:
        """Verify command follows naming conventions."""
        # Check that command follows expected patterns
        valid_commands = ["adc", "python", "pytest"]
        base_command = command.split()[0] if command else ""
        
        return base_command in valid_commands or command.startswith("./")
    
    def validate_output_schema(self, result: Dict, expected_schema: Dict) -> ValidationResult:
        """Ensure CLI output matches required schema for agent parsing."""
        
        required_fields = ["status", "timestamp", "command", "execution_time_ms"]
        
        for field in required_fields:
            if field not in result:
                return ValidationResult(
                    valid=False,
                    error=f"Missing required field: {field}"
                )
        
        # Validate field types
        if not isinstance(result.get("status"), str):
            return ValidationResult(
                valid=False,
                error="Status field must be string"
            )
        
        if not isinstance(result.get("execution_time_ms"), (int, float)):
            return ValidationResult(
                valid=False,
                error="execution_time_ms field must be number"
            )
        
        # Validate status values
        valid_statuses = ["success", "error", "warning"]
        if result.get("status") not in valid_statuses:
            return ValidationResult(
                valid=False,
                error=f"Status must be one of: {', '.join(valid_statuses)}"
            )
        
        return ValidationResult(valid=True)
    
    def check_performance_constraints(self, metrics: Dict, constraints: Dict) -> bool:
        """Validate command performance against contract constraints."""
        
        checks = [
            metrics.get("execution_time_ms", 0) <= constraints.get("max_execution_time_ms", 30000),
            metrics.get("memory_peak_mb", 0) <= constraints.get("max_memory_mb", 1024),
            metrics.get("cpu_time_ms", 0) <= constraints.get("max_cpu_time_ms", 10000)
        ]
        
        return all(checks)
    
    def validate_json_output(self, output_text: str) -> ValidationResult:
        """Validate that output is proper JSON."""
        try:
            json.loads(output_text)
            return ValidationResult(valid=True)
        except json.JSONDecodeError as e:
            return ValidationResult(
                valid=False,
                error=f"Invalid JSON: {str(e)}"
            )
    
    def validate_error_format(self, error_data: Dict) -> ValidationResult:
        """Validate error format follows ADC standards."""
        required_error_fields = ["code", "message", "severity"]
        
        for field in required_error_fields:
            if field not in error_data:
                return ValidationResult(
                    valid=False,
                    error=f"Error missing required field: {field}"
                )
        
        valid_severities = ["low", "medium", "high", "critical"]
        if error_data.get("severity") not in valid_severities:
            return ValidationResult(
                valid=False,
                error=f"Error severity must be one of: {', '.join(valid_severities)}"
            )
        
        return ValidationResult(valid=True)