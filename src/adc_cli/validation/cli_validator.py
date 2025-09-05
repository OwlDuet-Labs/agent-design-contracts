# ADC-IMPLEMENTS: <cli-tool-01>
import asyncio
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from ..logging_config import logger


@dataclass(frozen=True)
class CLIResult:
    """Standardized result format for CLI command executions."""

    command: str
    status: str  # "success", "error", "warning"
    timestamp: str
    execution_time_ms: float
    data: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    errors: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    performance: Dict = field(default_factory=dict)
    validation_results: Dict = field(default_factory=dict)


@dataclass(frozen=True)
class TestResult:
    """Standardized format for test execution results that agents can interpret."""

    test_id: str
    test_name: str
    test_type: str  # "unit", "integration", "e2e", "performance", "contract"
    status: str  # "passed", "failed", "error", "skipped"
    start_time: str
    end_time: str
    duration_seconds: float = 0.0
    error_message: str = ""
    assertions: List[Dict] = field(default_factory=list)
    performance_metrics: Dict = field(default_factory=dict)
    contract_compliance: Dict = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


# ADC-IMPLEMENTS: <cli-tool-01>
class CLIValidator:
    """Standardized interface for agents to execute and validate ADC-contracted CLI commands."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.logger = logger

    async def execute_command(
        self, command: str, expect_success: bool = True, working_dir: str = ""
    ) -> CLIResult:
        """Execute CLI command with structured output and validation."""
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            # Parse command into components
            cmd_parts = command.split()

            # Execute command
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=working_dir if working_dir else None,
            )

            execution_time = (time.time() - start_time) * 1000

            # Determine status
            if result.returncode == 0:
                status = "success"
            else:
                status = "error"

            # Parse JSON output if available
            data = {}
            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    data = {"output": result.stdout}

            # Build error information
            errors = []
            if result.stderr:
                errors.append(
                    {
                        "code": f"EXIT_CODE_{result.returncode}",
                        "message": result.stderr,
                        "severity": "high" if result.returncode != 0 else "low",
                    }
                )

            # Performance metrics
            performance = {
                "execution_time_ms": execution_time,
                "return_code": result.returncode,
            }

            return CLIResult(
                command=command,
                status=status,
                timestamp=timestamp,
                execution_time_ms=execution_time,
                data=data,
                metadata={
                    "timeout": self.timeout,
                    "working_directory": working_dir or str(Path.cwd()),
                },
                errors=errors,
                performance=performance,
            )

        except subprocess.TimeoutExpired:
            execution_time = (time.time() - start_time) * 1000
            return CLIResult(
                command=command,
                status="error",
                timestamp=timestamp,
                execution_time_ms=execution_time,
                errors=[
                    {
                        "code": "TIMEOUT",
                        "message": f"Command timed out after {self.timeout}s",
                        "severity": "high",
                    }
                ],
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return CLIResult(
                command=command,
                status="error",
                timestamp=timestamp,
                execution_time_ms=execution_time,
                errors=[
                    {"code": "EXECUTION_ERROR", "message": str(e), "severity": "high"}
                ],
            )

    async def run_test_suite(self, suite_name: str) -> List[TestResult]:
        """Execute test suite and return structured results."""
        logger.info(f"Running test suite: {suite_name}")

        # Execute pytest with JSON output
        result = await self.execute_command(
            f"python -m pytest tests/ -v --tb=short --json-report --json-report-file=test_results.json"
        )

        # Parse test results
        test_results = []
        try:
            if Path("test_results.json").exists():
                with open("test_results.json", "r") as f:
                    pytest_data = json.load(f)

                for test in pytest_data.get("tests", []):
                    test_result = TestResult(
                        test_id=test.get("nodeid", ""),
                        test_name=test.get("name", ""),
                        test_type="unit",  # Default type
                        status="passed"
                        if test.get("outcome") == "passed"
                        else "failed",
                        start_time=test.get("start", ""),
                        end_time=test.get("stop", ""),
                        duration_seconds=test.get("duration", 0.0),
                        error_message=test.get("call", {}).get("longrepr", ""),
                    )
                    test_results.append(test_result)
        except Exception as e:
            logger.error(f"Error parsing test results: {e}")

        return test_results

    async def check_system_health(self) -> Dict:
        """Check system health and return structured report."""
        health_report = {
            "overall_status": "healthy",
            "components": {},
            "score": 1.0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        # Check Python environment
        python_result = await self.execute_command("python --version")
        health_report["components"]["python"] = {
            "status": "healthy" if python_result.status == "success" else "failing",
            "details": python_result.data,
        }

        # Check if adc command is available
        adc_result = await self.execute_command("adc --help")
        health_report["components"]["adc_cli"] = {
            "status": "healthy" if adc_result.status == "success" else "failing",
            "details": adc_result.data,
        }

        # Calculate overall health score
        healthy_components = sum(
            1
            for comp in health_report["components"].values()
            if comp["status"] == "healthy"
        )
        total_components = len(health_report["components"])
        health_report["score"] = (
            healthy_components / total_components if total_components > 0 else 0.0
        )

        if health_report["score"] < 0.8:
            health_report["overall_status"] = "degraded"
        if health_report["score"] < 0.5:
            health_report["overall_status"] = "failing"

        return health_report
