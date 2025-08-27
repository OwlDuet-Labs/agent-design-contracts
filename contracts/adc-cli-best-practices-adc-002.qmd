---
contract_id: "adc-cli-best-practices-adc-001"
title: "ADC CLI Implementation Best Practices"
author: "ADC Framework"
status: "active"
version: 1.0
created_date: "2025-06-10"
last_updated: "2025-06-10"
---

### [Rationale: Auditor-Verifiable CLI Design] <cli-best-practices-rationale-01>

ADC projects require CLI interfaces that agents (especially the Auditor agent) can programmatically verify for contract compliance. Traditional CLI designs often lack the structured output, error handling, and validation hooks necessary for autonomous agent verification.

This contract establishes best practices for implementing CLI interfaces in ADC projects that enable reliable agent-driven validation, comprehensive error reporting, and automated compliance checking against contract specifications.

### [Feature: Structured Output Format] <cli-output-feature-01>

All CLI commands MUST produce structured, machine-readable output that agents can parse and validate.

**Required Output Schema:**
```json
{
  "status": "success" | "error" | "warning",
  "timestamp": "ISO8601 datetime",
  "command": "exact command executed",
  "execution_time_ms": 123.45,
  "data": {},
  "metadata": {
    "version": "CLI version",
    "environment": "production|development|test"
  },
  "errors": [],
  "warnings": []
}
```

**Implementation Requirements:**
- ALL commands output JSON when `--json` flag is provided
- Human-readable output is default, JSON is opt-in via flag
- Error messages include error codes for programmatic handling
- Execution time tracking for performance validation
- Version information for compatibility checking

**Error Structure:**
```json
{
  "code": "CONTRACT_VALIDATION_FAILED",
  "message": "Contract example-datamodel-01 implementation not found",
  "details": {
    "contract_id": "example-datamodel-01",
    "expected_file": "src/models/example.py",
    "suggestion": "Add ADC-IMPLEMENTS marker before class definition"
  },
  "severity": "high"
}
```

**Parity:**
- **Implementation Scope:** `src/cli/output_formatter.py`
- **Tests:** `tests/cli/test_output_format.py`

### [Feature: Command Category Organization] <cli-organization-feature-01>

CLI commands MUST be organized into logical categories that align with ADC contract verification needs.

**Required Command Categories:**

1. **System Management**
   - `init` - Initialize project with ADC structure
   - `config` - Manage configuration and environment
   - `deploy` - Deploy components with health checks

2. **Contract Operations**
   - `validate` - Verify ADC contract implementations
   - `audit` - Generate compliance reports
   - `contracts list` - List all contracts and their status

3. **Development Support**
   - `generate` - Generate code from contracts
   - `test` - Execute test suites
   - `docs` - Generate documentation

4. **Monitoring & Health**
   - `status` - System component health
   - `metrics` - Performance and business metrics
   - `logs` - Structured log access

**Command Naming Convention:**
- Use clear, descriptive verbs
- Support both short and long forms (`-v` and `--verbose`)
- Include `--dry-run` for destructive operations
- Provide `--help` with examples for all commands

**Parity:**
- **Implementation Scope:** `src/cli/commands/`
- **Configuration Scope:** `config/cli/command_registry.yaml`
- **Tests:** `tests/cli/test_command_structure.py`

### [Feature: Contract Validation Integration] <cli-validation-feature-01>

CLI MUST provide comprehensive contract validation capabilities for auditor agent verification.

**Required Validation Commands:**

```bash
# Validate all contracts
app validate --all --json

# Validate specific contract
app validate --contract=example-datamodel-01 --json

# Full compliance audit
app audit --output=json --report-path=audit_report.json

# Parity checking
app validate parity --scan-markers --check-implementations
```

**Validation Output Requirements:**
- Contract implementation status (implemented/partial/missing)
- ADC-IMPLEMENTS marker verification
- Parity section compliance checking
- Performance constraint validation
- API endpoint compliance (if applicable)

**Expected Validation Response:**
```json
{
  "status": "success",
  "validation_summary": {
    "total_contracts": 15,
    "implemented": 12,
    "partial": 2,
    "missing": 1,
    "compliance_score": 0.87
  },
  "contract_details": [
    {
      "contract_id": "example-datamodel-01",
      "status": "implemented",
      "file_path": "src/models/example.py",
      "markers_found": ["ADC-IMPLEMENTS: <example-datamodel-01>"],
      "issues": [],
      "last_verified": "2025-06-10T14:30:00Z"
    }
  ],
  "recommendations": [
    "Add missing implementation for user-agent-01",
    "Update outdated marker format in database.py"
  ]
}
```

**Parity:**
- **Implementation Scope:** `src/cli/validation/contract_validator.py`
- **Tests:** `tests/cli/test_contract_validation.py`

### [Feature: Performance Monitoring] <cli-performance-feature-01>

CLI commands MUST include performance monitoring for auditor verification of constraint compliance.

**Performance Tracking Requirements:**
- Execution time measurement for all commands
- Memory usage tracking for long-running operations
- Resource utilization reporting
- Performance constraint validation against ADC contracts

**Performance Output Format:**
```json
{
  "performance": {
    "execution_time_ms": 1234.56,
    "memory_peak_mb": 45.2,
    "cpu_time_ms": 890.12,
    "disk_operations": {
      "reads": 15,
      "writes": 3,
      "bytes_read": 1048576,
      "bytes_written": 2048
    },
    "network_operations": {
      "requests": 2,
      "bytes_sent": 512,
      "bytes_received": 8192
    }
  },
  "constraint_compliance": {
    "max_execution_time_ms": 5000,
    "actual_execution_time_ms": 1234.56,
    "compliant": true
  }
}
```

**Parity:**
- **Implementation Scope:** `src/cli/monitoring/performance_tracker.py`
- **Tests:** `tests/cli/test_performance_monitoring.py`

### [DataModel: CLICommand] <cli-best-practices-datamodel-01>

Standardized structure for implementing CLI commands in ADC projects.

- `command_name: str` - Command name (e.g., "validate", "audit") (required)
- `category: str` - Command category (e.g., "contract", "system") (required)
- `description: str` - Human-readable description (required)
- `arguments: List[dict]` - Command arguments specification (defaults to empty list)
- `flags: List[dict]` - Available flags and options (defaults to empty list)
- `output_schema: dict` - JSON schema for structured output (required)
- `requires_project: bool` - Whether command needs ADC project context (defaults to true)
- `supports_json: bool` - Whether command supports --json flag (defaults to true)
- `supports_dry_run: bool` - Whether command supports --dry-run (defaults to false)
- `performance_constraints: dict` - Expected performance limits (defaults to empty dict)
- `contract_dependencies: List[str]` - Contracts this command validates (defaults to empty list)

**Argument Structure:**
```python
argument = {
    "name": "contract_id",
    "type": "string",
    "required": False,
    "description": "Specific contract to validate",
    "validation": {"pattern": r"^[a-zA-Z0-9-_]+-adc-\d{3}$"}
}
```

**Flag Structure:**
```python
flag = {
    "short": "-v",
    "long": "--verbose",
    "type": "boolean",
    "description": "Enable verbose output",
    "default": False
}
```

**Parity:**
- **Implementation Scope:** `src/cli/models/command.py`

### [DataModel: CLIResult] <cli-best-practices-datamodel-02>

Standardized result format for all CLI command executions.

- `command: str` - Command that was executed (required)
- `status: str` - "success", "error", "warning" (required)
- `timestamp: datetime` - When command was executed (defaults to now)
- `execution_time_ms: float` - Command execution duration (required)
- `data: dict` - Command-specific output data (defaults to empty dict)
- `metadata: dict` - System and environment information (defaults to empty dict)
- `errors: List[dict]` - Error details if status is "error" (defaults to empty list)
- `warnings: List[dict]` - Warning details if applicable (defaults to empty list)
- `performance: dict` - Performance metrics (defaults to empty dict)
- `validation_results: dict` - Contract validation results if applicable (defaults to empty dict)

**Metadata Structure:**
```python
metadata = {
    "cli_version": "1.2.3",
    "environment": "development",
    "python_version": "3.11.5",
    "project_root": "/path/to/project",
    "config_file": "config/development.yaml"
}
```

**Parity:**
- **Implementation Scope:** `src/cli/models/result.py`

### [Algorithm: Command Execution Validation] <cli-execution-algorithm-01>

Algorithm for validating CLI command execution and ensuring auditor-compatible output.

**Input:** CLI command, arguments, execution environment
**Output:** Validated CLI result with compliance checking

**Validation Process:**
```
CLI_Execution_Validation = process([
    validate_command_structure(command, args),
    execute_with_monitoring(command, args, environment),
    validate_output_schema(result, expected_schema),
    check_performance_constraints(execution_metrics),
    verify_contract_compliance(validation_results)
])

Validation Steps:
1. Verify command follows naming conventions
2. Validate argument types and constraints
3. Execute command with performance monitoring
4. Validate output matches required schema
5. Check performance against contract constraints
6. Verify any contract validations were successful
7. Generate auditor-compatible result format
```

**Performance Constraint Checking:**
```python
def check_performance_constraints(metrics: dict, constraints: dict) -> bool:
    """Validate command performance against contract constraints"""
    
    checks = [
        metrics["execution_time_ms"] <= constraints.get("max_execution_time_ms", 30000),
        metrics["memory_peak_mb"] <= constraints.get("max_memory_mb", 1024),
        metrics["cpu_time_ms"] <= constraints.get("max_cpu_time_ms", 10000)
    ]
    
    return all(checks)
```

**Output Schema Validation:**
```python
def validate_output_schema(result: dict, schema: dict) -> ValidationResult:
    """Ensure CLI output matches required schema for agent parsing"""
    
    required_fields = ["status", "timestamp", "command", "execution_time_ms"]
    
    for field in required_fields:
        if field not in result:
            return ValidationResult(
                valid=False,
                error=f"Missing required field: {field}"
            )
    
    return ValidationResult(valid=True)
```

**Parity:**
- **Implementation Scope:** `src/cli/algorithms/execution_validator.py`

### [Constraint: Auditor Compatibility] <cli-auditor-constraint-01>

CLI implementation requirements to ensure compatibility with auditor agent verification.

**Output Format Requirements:**
- JSON output MUST be valid and parseable
- All timestamps in ISO8601 format
- Error codes MUST be machine-readable constants
- Performance metrics MUST be included in structured format
- Version information MUST be present in metadata

**Command Structure Requirements:**
- ALL commands MUST support `--help` flag
- ALL commands MUST support `--json` flag for structured output
- Commands MUST have consistent argument naming
- Exit codes MUST follow standard conventions (0=success, 1=error, 2=invalid usage)

**Performance Requirements:**
- Command help text generation: < 100ms
- Simple status commands: < 500ms
- Contract validation commands: < 30 seconds
- Full system audit: < 5 minutes

**Error Handling Requirements:**
- Graceful failure with descriptive error messages
- No uncaught exceptions or stack traces in production
- Error codes map to specific remediation actions
- Timeout protection for long-running operations

**Security Requirements:**
- No sensitive information in command output
- Proper input validation and sanitization
- Limited file system access based on project scope
- Audit logging of all CLI operations

**Parity:**
- **Implementation Scope:** All CLI command implementations
- **Tests:** `tests/cli/test_auditor_compatibility.py`

### [TestScenario: Auditor Agent CLI Verification] <cli-audit-scenario-01>

End-to-end test scenario demonstrating auditor agent verification of CLI implementation.

**Scenario**: Auditor agent validates complete CLI interface compliance

**Test Sequence:**
1. **Command Discovery**
   - Execute: `app --help --json`
   - Validate: All required command categories present
   - Check: JSON output format compliance

2. **Contract Validation Testing**
   - Execute: `app validate --all --json`
   - Validate: Structured validation results
   - Check: Contract compliance scoring

3. **Performance Validation**
   - Execute: `app validate --contract=example-datamodel-01 --json`
   - Validate: Execution time within constraints
   - Check: Performance metrics included in output

4. **Error Handling Testing**
   - Execute: `app validate --contract=nonexistent-contract --json`
   - Validate: Graceful error handling
   - Check: Machine-readable error codes

5. **Output Schema Validation**
   - Parse all JSON outputs
   - Validate: Schema compliance for all commands
   - Check: Required fields present and correctly typed

**Success Criteria:**
- All commands produce valid JSON output
- Error messages include actionable guidance
- Performance metrics available for all operations
- Contract validation results are comprehensive
- No uncaught exceptions or malformed output

**Auditor Agent Integration:**
```python
async def validate_cli_implementation():
    """Auditor agent validation of CLI compliance"""
    
    # Test command discovery
    help_result = await self.cli.execute_command("app --help --json")
    assert_valid_json_schema(help_result.output, HELP_SCHEMA)
    
    # Test contract validation
    validation_result = await self.cli.execute_command("app validate --all --json")
    assert_valid_json_schema(validation_result.output, VALIDATION_SCHEMA)
    
    # Test performance compliance
    assert validation_result.execution_time_ms < 30000
    
    # Test error handling
    error_result = await self.cli.execute_command("app validate --contract=invalid --json")
    assert error_result.status == "error"
    assert "CONTRACT_NOT_FOUND" in error_result.error_code
    
    return CLIAuditReport(
        compliance_score=calculate_compliance_score(results),
        issues=extract_issues(results),
        recommendations=generate_recommendations(results)
    )
```

**Parity:**
- **Implementation Scope:** Full CLI interface
- **Tests:** `tests/scenarios/test_auditor_cli_validation.py` 