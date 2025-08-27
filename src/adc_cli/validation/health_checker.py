# ADC-IMPLEMENTS: <health-checker-tool-01>
import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from ..logging_config import logger


@dataclass(frozen=True)
class HealthReport:
    """Comprehensive system health check results."""
    
    overall_status: str  # "healthy", "degraded", "failing"
    health_score: float
    components: Dict = field(default_factory=dict)
    performance_metrics: Dict = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))


@dataclass(frozen=True)
class AgentHealthReport:
    """Individual agent health validation results."""
    
    agent_id: str
    status: str  # "healthy", "degraded", "failing"
    response_time_ms: float
    last_activity: str
    error_count: int = 0
    warnings: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)


# ADC-IMPLEMENTS: <health-checker-tool-01>
class HealthChecker:
    """Automated health checking system that validates all ADC-contracted components."""
    
    def __init__(self):
        self.logger = logger
    
    async def check_system_health(self) -> HealthReport:
        """Comprehensive system health check."""
        logger.info("Performing comprehensive system health check")
        
        components = {}
        overall_score = 0.0
        
        # Check infrastructure components
        infra_health = await self._check_infrastructure_health()
        components["infrastructure"] = infra_health
        
        # Check agent health
        agent_health = await self._check_agent_health()
        components["agents"] = agent_health
        
        # Check data flow
        data_flow_health = await self._check_data_flow()
        components["data_flow"] = data_flow_health
        
        # Check contract compliance
        contract_health = await self._check_contract_compliance()
        components["contract_compliance"] = contract_health
        
        # Calculate overall health score
        component_scores = [
            comp.get("score", 0.0) for comp in components.values()
        ]
        overall_score = sum(component_scores) / len(component_scores) if component_scores else 0.0
        
        # Determine overall status
        if overall_score >= 0.9:
            overall_status = "healthy"
        elif overall_score >= 0.7:
            overall_status = "degraded"
        else:
            overall_status = "failing"
        
        # Generate recommendations
        recommendations = []
        for comp_name, comp_data in components.items():
            if comp_data.get("score", 0.0) < 0.8:
                recommendations.extend(comp_data.get("recommendations", []))
        
        return HealthReport(
            overall_status=overall_status,
            health_score=overall_score,
            components=components,
            recommendations=recommendations
        )
    
    async def _check_infrastructure_health(self) -> Dict:
        """Check infrastructure components health."""
        logger.info("Checking infrastructure health")
        
        checks = {
            "filesystem": self._check_filesystem(),
            "python_environment": self._check_python_environment(),
            "dependencies": self._check_dependencies()
        }
        
        # Run checks concurrently
        results = {}
        for check_name, check_coro in checks.items():
            try:
                result = await check_coro
                results[check_name] = result
            except Exception as e:
                results[check_name] = {
                    "status": "failing",
                    "error": str(e),
                    "score": 0.0
                }
        
        # Calculate overall infrastructure score
        scores = [result.get("score", 0.0) for result in results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "status": "healthy" if overall_score >= 0.8 else "failing",
            "score": overall_score,
            "details": results,
            "recommendations": [
                f"Fix {check_name} issues" 
                for check_name, result in results.items()
                if result.get("score", 0.0) < 0.8
            ]
        }
    
    async def _check_filesystem(self) -> Dict:
        """Check filesystem structure and permissions."""
        required_dirs = ["src", "contracts", "roles", "tests"]
        issues = []
        
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                issues.append(f"Required directory missing: {dir_name}")
            elif not dir_path.is_dir():
                issues.append(f"Path exists but is not a directory: {dir_name}")
        
        score = 1.0 - (len(issues) / len(required_dirs))
        
        return {
            "status": "healthy" if score >= 0.8 else "failing",
            "score": score,
            "issues": issues,
            "checked_directories": required_dirs
        }
    
    async def _check_python_environment(self) -> Dict:
        """Check Python environment and version."""
        import sys
        
        python_version = sys.version_info
        required_version = (3, 8)
        
        version_ok = python_version >= required_version
        
        return {
            "status": "healthy" if version_ok else "failing",
            "score": 1.0 if version_ok else 0.0,
            "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "required_version": f"{required_version[0]}.{required_version[1]}+",
            "issues": [] if version_ok else [f"Python version {python_version.major}.{python_version.minor} < required {required_version[0]}.{required_version[1]}"]
        }
    
    async def _check_dependencies(self) -> Dict:
        """Check that required dependencies are available."""
        required_packages = ["pathlib", "json", "subprocess", "asyncio"]
        available_packages = []
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                available_packages.append(package)
            except ImportError:
                missing_packages.append(package)
        
        score = len(available_packages) / len(required_packages) if required_packages else 1.0
        
        return {
            "status": "healthy" if score >= 0.9 else "failing",
            "score": score,
            "available_packages": available_packages,
            "missing_packages": missing_packages,
            "issues": [f"Missing required package: {pkg}" for pkg in missing_packages]
        }
    
    async def _check_agent_health(self) -> Dict:
        """Check health of available AI agents."""
        from ..providers import get_available_providers
        
        providers = get_available_providers()
        agent_results = {}
        
        for agent_name, provider in providers.items():
            start_time = time.time()
            
            if provider.is_initialized:
                status = "healthy"
                response_time = (time.time() - start_time) * 1000
                score = 1.0
            else:
                # Try to initialize
                init_result = provider.initialize()
                response_time = (time.time() - start_time) * 1000
                
                if init_result.success:
                    status = "healthy"
                    score = 1.0
                else:
                    status = "failing"
                    score = 0.0
            
            agent_results[agent_name] = {
                "status": status,
                "response_time_ms": response_time,
                "score": score,
                "is_initialized": provider.is_initialized
            }
        
        # Calculate overall agent health
        scores = [result.get("score", 0.0) for result in agent_results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "status": "healthy" if overall_score >= 0.5 else "failing",
            "score": overall_score,
            "agents": agent_results,
            "total_agents": len(providers),
            "healthy_agents": sum(1 for result in agent_results.values() if result.get("score", 0.0) >= 0.8)
        }
    
    async def _check_data_flow(self) -> Dict:
        """Validate message passing and data processing."""
        # For now, this is a placeholder - in a real system this would
        # check message queues, data pipelines, etc.
        
        return {
            "status": "healthy",
            "score": 1.0,
            "message": "Data flow checking not implemented - placeholder health status"
        }
    
    async def _check_contract_compliance(self) -> Dict:
        """Validate ADC contract implementation status."""
        from .contract_validator import ContractValidator
        
        validator = ContractValidator()
        validation_results = validator.validate_all_contracts()
        
        compliance_score = validation_results.get("validation_summary", {}).get("compliance_score", 0.0)
        
        return {
            "status": "healthy" if compliance_score >= 0.8 else "failing",
            "score": compliance_score,
            "validation_summary": validation_results.get("validation_summary", {}),
            "total_contracts": validation_results.get("validation_summary", {}).get("total_contracts", 0),
            "implemented_contracts": validation_results.get("validation_summary", {}).get("implemented", 0)
        }