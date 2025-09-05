# ADC-IMPLEMENTS: <agent-cli-feature-01>
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List

from ..validation.cli_validator import CLIResult, CLIValidator, TestResult
from ..validation.contract_validator import ContractValidationResult, ContractValidator
from ..validation.health_checker import HealthChecker, HealthReport


@dataclass(frozen=True)
class SystemHealthReport:
    """System health report for agent consumption."""

    overall_status: str
    health_score: float
    component_count: int
    healthy_components: int
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TestSuiteResult:
    """Test suite execution results."""

    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time_ms: float
    overall_status: str
    test_details: List[TestResult] = field(default_factory=list)


# ADC-IMPLEMENTS: <agent-cli-feature-01>
class AgentCLIInterface:
    """Direct integration allowing ADC agents (especially auditor.md) to execute CLI commands and interpret results."""

    def __init__(self, timeout: int = 300):
        self.cli_validator = CLIValidator(timeout=timeout)
        self.contract_validator = ContractValidator()
        self.health_checker = HealthChecker()

    async def execute_command(
        self, command: str, expect_success: bool = True
    ) -> CLIResult:
        """Execute CLI command with structured output and validation."""
        result = await self.cli_validator.execute_command(command, expect_success)

        # Log the execution for audit trail
        self._log_command_execution(command, result)

        return result

    async def validate_implementation(
        self, contract_id: str
    ) -> ContractValidationResult:
        """Validate specific contract implementation."""
        return self.contract_validator.validate_specific_contract(contract_id)

    async def check_system_health(self) -> SystemHealthReport:
        """Check system health and return structured report."""
        health_report = await self.health_checker.check_system_health()

        healthy_count = sum(
            1
            for comp in health_report.components.values()
            if comp.get("status") == "healthy"
        )

        return SystemHealthReport(
            overall_status=health_report.overall_status,
            health_score=health_report.health_score,
            component_count=len(health_report.components),
            healthy_components=healthy_count,
            issues=[
                f"{name}: {comp.get('status', 'unknown')}"
                for name, comp in health_report.components.items()
                if comp.get("status") != "healthy"
            ],
            recommendations=health_report.recommendations,
        )

    async def run_test_suite(self, suite_name: str) -> TestSuiteResult:
        """Execute test suite and return structured results."""
        test_results = await self.cli_validator.run_test_suite(suite_name)

        passed_count = sum(1 for test in test_results if test.status == "passed")
        failed_count = sum(1 for test in test_results if test.status == "failed")

        total_execution_time = (
            sum(test.duration_seconds for test in test_results) * 1000
        )

        overall_status = "passed" if failed_count == 0 else "failed"

        return TestSuiteResult(
            suite_name=suite_name,
            total_tests=len(test_results),
            passed_tests=passed_count,
            failed_tests=failed_count,
            execution_time_ms=total_execution_time,
            overall_status=overall_status,
            test_details=test_results,
        )

    async def validate_all_contracts(self) -> Dict:
        """Validate all contracts and return comprehensive results."""
        return self.contract_validator.validate_all_contracts()

    async def run_full_audit(self) -> Dict:
        """
        Run a comprehensive audit including health checks, contract validation, and testing.
        This is the primary method auditor agents should use.
        """
        audit_results = {
            "audit_timestamp": "",
            "overall_status": "unknown",
            "health_report": {},
            "contract_validation": {},
            "test_results": {},
            "compliance_score": 0.0,
            "recommendations": [],
        }

        try:
            # 1. Check system health
            health_report = await self.check_system_health()
            audit_results["health_report"] = {
                "status": health_report.overall_status,
                "score": health_report.health_score,
                "healthy_components": health_report.healthy_components,
                "total_components": health_report.component_count,
                "issues": health_report.issues,
            }

            # 2. Validate all contracts
            contract_results = await self.validate_all_contracts()
            audit_results["contract_validation"] = contract_results

            # 3. Run basic tests if available
            try:
                test_results = await self.run_test_suite("basic")
                audit_results["test_results"] = {
                    "total_tests": test_results.total_tests,
                    "passed_tests": test_results.passed_tests,
                    "failed_tests": test_results.failed_tests,
                    "overall_status": test_results.overall_status,
                }
            except Exception:
                audit_results["test_results"] = {
                    "status": "not_available",
                    "message": "Test suite execution not available",
                }

            # 4. Calculate overall compliance score
            health_score = health_report.health_score
            contract_score = contract_results.get("validation_summary", {}).get(
                "compliance_score", 0.0
            )

            # Weight: 40% health, 60% contract compliance
            overall_compliance = (health_score * 0.4) + (contract_score * 0.6)
            audit_results["compliance_score"] = overall_compliance

            # 5. Determine overall status
            if overall_compliance >= 0.9:
                audit_results["overall_status"] = "excellent"
            elif overall_compliance >= 0.8:
                audit_results["overall_status"] = "good"
            elif overall_compliance >= 0.6:
                audit_results["overall_status"] = "needs_improvement"
            else:
                audit_results["overall_status"] = "failing"

            # 6. Aggregate recommendations
            recommendations = []
            recommendations.extend(health_report.recommendations)
            recommendations.extend(contract_results.get("recommendations", []))
            audit_results["recommendations"] = recommendations

            # 7. Set timestamp
            import time

            audit_results["audit_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        except Exception as e:
            audit_results["overall_status"] = "error"
            audit_results["error"] = str(e)

        return audit_results

    def _log_command_execution(self, command: str, result: CLIResult):
        """Log CLI command execution for audit trail."""
        # This would integrate with a proper logging system
        # For now, this is a placeholder
        pass

    # Convenience methods for common auditor operations
    async def verify_adc_markers(self) -> Dict:
        """Verify ADC-IMPLEMENTS markers are present and valid."""
        return await self.validate_all_contracts()

    async def check_performance_compliance(self) -> Dict:
        """Check that system performance meets contract constraints."""
        health_report = await self.check_system_health()
        return {
            "performance_score": health_report.health_score,
            "status": health_report.overall_status,
            "details": health_report.components.get("infrastructure", {}),
        }
