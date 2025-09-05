# ADC-IMPLEMENTS: <cli-testing-algorithm-01>
import json
import subprocess
import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ValidationResult:
    """Result of CLI command validation."""

    valid: bool
    command: str
    execution_time_ms: float
    output_valid: bool
    schema_valid: bool
    performance_valid: bool
    side_effects_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    performance_metrics: Dict = field(default_factory=dict)


# ADC-IMPLEMENTS: <cli-testing-algorithm-01>
class CLICommandValidator:
    """Algorithm for systematically validating CLI command functionality and output correctness."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def validate_command(
        self,
        cli_command: str,
        args: List[str],
        expected_schema: Dict,
        validation_criteria: Dict = None,
    ) -> ValidationResult:
        """
        Validate CLI command functionality and output correctness.

        Input: CLI command, expected output schema, validation criteria
        Output: Validation result with pass/fail status and detailed analysis
        """
        start_time = time.time()
        errors = []
        warnings = []

        # Step 1: Execute command in controlled environment
        execution_result = self._execute_command(cli_command, args)

        # Step 2: Parse output (stdout, stderr, return code)
        parsed_output = self._parse_output(execution_result)

        # Step 3: Validate schema (output format matches expected schema)
        schema_validation = self._validate_schema(
            parsed_output["stdout"], expected_schema
        )

        # Step 4: Check side effects (files created, database updated)
        side_effects_validation = self._check_side_effects(validation_criteria or {})

        # Step 5: Measure performance (execution time, resource usage)
        execution_time_ms = (time.time() - start_time) * 1000
        performance_validation = self._measure_performance(
            execution_time_ms, validation_criteria or {}
        )

        # Determine overall validity
        overall_valid = (
            execution_result["success"]
            and schema_validation["valid"]
            and side_effects_validation["valid"]
            and performance_validation["valid"]
        )

        # Collect errors and warnings
        if not execution_result["success"]:
            errors.append(f"Command execution failed: {execution_result['error']}")

        if not schema_validation["valid"]:
            errors.extend(schema_validation["errors"])

        if not performance_validation["valid"]:
            errors.extend(performance_validation["errors"])

        return ValidationResult(
            valid=overall_valid,
            command=f"{cli_command} {' '.join(args)}",
            execution_time_ms=execution_time_ms,
            output_valid=execution_result["success"],
            schema_valid=schema_validation["valid"],
            performance_valid=performance_validation["valid"],
            side_effects_valid=side_effects_validation["valid"],
            errors=errors,
            warnings=warnings,
            performance_metrics={
                "execution_time_ms": execution_time_ms,
                "return_code": execution_result.get("return_code", -1),
            },
        )

    def _execute_command(self, command: str, args: List[str]) -> Dict:
        """Execute command in controlled environment."""
        try:
            cmd_list = [command] + args
            result = subprocess.run(
                cmd_list, capture_output=True, text=True, timeout=self.timeout
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "error": result.stderr if result.returncode != 0 else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout}s",
                "return_code": -1,
                "error": "Timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "error": str(e),
            }

    def _parse_output(self, execution_result: Dict) -> Dict:
        """Parse command output (stdout, stderr, return code)."""
        return {
            "stdout": execution_result.get("stdout", ""),
            "stderr": execution_result.get("stderr", ""),
            "return_code": execution_result.get("return_code", -1),
        }

    def _validate_schema(self, output: str, expected_schema: Dict) -> Dict:
        """Validate output format matches expected schema."""
        errors = []

        # Try to parse as JSON if schema expects structured data
        if expected_schema.get("type") == "object":
            try:
                parsed_output = json.loads(output)

                # Check required properties
                required_fields = expected_schema.get("required", [])
                for field in required_fields:
                    if field not in parsed_output:
                        errors.append(f"Missing required field: {field}")

                # Basic type checking for properties
                properties = expected_schema.get("properties", {})
                for field, field_schema in properties.items():
                    if field in parsed_output:
                        expected_type = field_schema.get("type")
                        actual_value = parsed_output[field]

                        if expected_type == "string" and not isinstance(
                            actual_value, str
                        ):
                            errors.append(
                                f"Field {field} should be string, got {type(actual_value).__name__}"
                            )
                        elif expected_type == "number" and not isinstance(
                            actual_value, (int, float)
                        ):
                            errors.append(
                                f"Field {field} should be number, got {type(actual_value).__name__}"
                            )
                        elif expected_type == "boolean" and not isinstance(
                            actual_value, bool
                        ):
                            errors.append(
                                f"Field {field} should be boolean, got {type(actual_value).__name__}"
                            )
                        elif expected_type == "array" and not isinstance(
                            actual_value, list
                        ):
                            errors.append(
                                f"Field {field} should be array, got {type(actual_value).__name__}"
                            )
                        elif expected_type == "object" and not isinstance(
                            actual_value, dict
                        ):
                            errors.append(
                                f"Field {field} should be object, got {type(actual_value).__name__}"
                            )

            except json.JSONDecodeError:
                if expected_schema.get("type") == "object":
                    errors.append("Output is not valid JSON")

        return {"valid": len(errors) == 0, "errors": errors}

    def _check_side_effects(self, validation_criteria: Dict) -> Dict:
        """Check for expected side effects (files created, database updated)."""
        # This is a placeholder - in a real implementation, this would check
        # for expected file system changes, database updates, etc.
        return {"valid": True, "checked": validation_criteria.get("side_effects", [])}

    def _measure_performance(
        self, execution_time_ms: float, validation_criteria: Dict
    ) -> Dict:
        """Verify performance meets contract constraints."""
        errors = []

        # Check execution time constraints
        max_execution_time = validation_criteria.get("max_execution_time_ms", 30000)
        if execution_time_ms > max_execution_time:
            errors.append(
                f"Execution time {execution_time_ms:.2f}ms exceeds limit {max_execution_time}ms"
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "execution_time_ms": execution_time_ms,
        }
