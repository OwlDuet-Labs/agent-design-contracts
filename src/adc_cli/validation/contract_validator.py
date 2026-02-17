# ADC-IMPLEMENTS: <cli-validation-feature-01>
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from ..logging_config import logger


@dataclass(frozen=True)
class ContractValidationResult:
    """Results from validating ADC contract implementation compliance."""
    
    contract_id: str
    validation_id: str
    implementation_status: str  # "implemented", "partial", "missing", "error"
    compliance_score: float = 0.0
    parity_check_results: List[Dict] = field(default_factory=list)
    functional_test_results: List = field(default_factory=list)
    performance_validation: Dict = field(default_factory=dict)
    api_validation: Dict = field(default_factory=dict)
    data_model_validation: Dict = field(default_factory=dict)
    issues_found: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    validation_timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))


# ADC-IMPLEMENTS: <cli-validation-feature-01>
class ContractValidator:
    """Comprehensive contract validation capabilities for auditor agent verification."""
    
    def __init__(self, src_dir: str = "src", contracts_dir: str = "contracts"):
        self.src_dir = Path(src_dir)
        self.contracts_dir = Path(contracts_dir)
        self.logger = logger
    
    def validate_all_contracts(self) -> Dict:
        """Validate all contracts and return comprehensive results."""
        validation_summary = {
            "total_contracts": 0,
            "implemented": 0,
            "partial": 0,
            "missing": 0,
            "compliance_score": 0.0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        contract_details = []
        
        # Find all contract files (support both .md and .qmd, preferring .md)
        md_files = list(self.contracts_dir.glob("*.md"))
        qmd_files = list(self.contracts_dir.glob("*.qmd"))
        # Filter out .qmd files that have .md equivalents
        qmd_only = [f for f in qmd_files if f.with_suffix('.md') not in md_files]
        contract_files = md_files + qmd_only
        validation_summary["total_contracts"] = len(contract_files)
        
        for contract_file in contract_files:
            contract_result = self.validate_contract_file(contract_file)
            contract_details.append(contract_result)
            
            # Update summary counts
            if contract_result["implementation_status"] == "implemented":
                validation_summary["implemented"] += 1
            elif contract_result["implementation_status"] == "partial":
                validation_summary["partial"] += 1
            else:
                validation_summary["missing"] += 1
        
        # Calculate overall compliance score
        if validation_summary["total_contracts"] > 0:
            validation_summary["compliance_score"] = (
                validation_summary["implemented"] + 
                (validation_summary["partial"] * 0.5)
            ) / validation_summary["total_contracts"]
        
        return {
            "status": "success",
            "validation_summary": validation_summary,
            "contract_details": contract_details,
            "recommendations": self._generate_recommendations(contract_details)
        }
    
    def validate_contract_file(self, contract_file: Path) -> Dict:
        """Validate a specific contract file implementation."""
        logger.info(f"Validating contract file: {contract_file}")
        
        try:
            with open(contract_file, "r", encoding="utf-8") as f:
                contract_content = f.read()
        except Exception as e:
            logger.error(f"Error reading contract file {contract_file}: {e}")
            return {
                "contract_id": contract_file.stem,
                "status": "error",
                "file_path": str(contract_file),
                "implementation_status": "error",
                "error": str(e)
            }
        
        # Extract contract ID from file
        contract_id_match = re.search(r'contract_id:\s*"([^"]+)"', contract_content)
        contract_id = contract_id_match.group(1) if contract_id_match else contract_file.stem
        
        # Find all contract block IDs
        contract_blocks = re.findall(r'<([^>]+)>', contract_content)
        
        # Check for ADC-IMPLEMENTS markers in source code
        markers_found = []
        missing_implementations = []
        
        for block_id in contract_blocks:
            marker_found = self._find_adc_marker(block_id)
            if marker_found:
                markers_found.append(marker_found)
            else:
                missing_implementations.append(block_id)
        
        # Determine implementation status
        if not missing_implementations:
            implementation_status = "implemented"
        elif markers_found:
            implementation_status = "partial"
        else:
            implementation_status = "missing"
        
        # Generate issues
        issues = []
        for missing_id in missing_implementations:
            issues.append({
                "severity": "high",
                "category": "implementation_missing",
                "description": f"ADC-IMPLEMENTS marker not found for contract {missing_id}",
                "suggestion": f"Add ADC-IMPLEMENTS: <{missing_id}> before implementing class/function"
            })
        
        return {
            "contract_id": contract_id,
            "status": "implemented" if implementation_status == "implemented" else "partial",
            "file_path": str(contract_file),
            "markers_found": [f"ADC-IMPLEMENTS: <{marker['block_id']}>" for marker in markers_found],
            "missing_implementations": missing_implementations,
            "implementation_status": implementation_status,
            "issues": issues,
            "last_verified": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    
    def _find_adc_marker(self, block_id: str) -> Dict:
        """Find ADC-IMPLEMENTS marker for a specific block ID in source code."""
        py_files = list(self.src_dir.rglob("*.py"))
        
        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Look for ADC-IMPLEMENTS marker
                marker_pattern = rf'# ADC-IMPLEMENTS:\s*<{re.escape(block_id)}>'
                if re.search(marker_pattern, content):
                    return {
                        "block_id": block_id,
                        "file_path": str(py_file.relative_to(self.src_dir)),
                        "found": True
                    }
            except Exception as e:
                logger.warning(f"Error reading source file {py_file}: {e}")
                continue
        
        return {}
    
    def _generate_recommendations(self, contract_details: List[Dict]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Count missing implementations
        total_missing = sum(
            len(contract.get("missing_implementations", [])) 
            for contract in contract_details
        )
        
        if total_missing > 0:
            recommendations.append(f"Implement {total_missing} missing contract blocks with ADC-IMPLEMENTS markers")
        
        # Check for error contracts
        error_contracts = [
            contract for contract in contract_details 
            if contract.get("implementation_status") == "error"
        ]
        
        if error_contracts:
            recommendations.append("Fix contract file reading errors")
        
        # Check for partial implementations
        partial_contracts = [
            contract for contract in contract_details
            if contract.get("implementation_status") == "partial"
        ]
        
        if partial_contracts:
            recommendations.append("Complete partial contract implementations")
        
        return recommendations
    
    def validate_specific_contract(self, contract_id: str) -> ContractValidationResult:
        """Validate a specific contract by ID."""
        import uuid
        
        # Find contract file by ID (support both .md and .qmd, preferring .md)
        md_files = list(self.contracts_dir.glob("*.md"))
        qmd_files = list(self.contracts_dir.glob("*.qmd"))
        # Filter out .qmd files that have .md equivalents
        qmd_only = [f for f in qmd_files if f.with_suffix('.md') not in md_files]
        all_contract_files = md_files + qmd_only
        contract_file = None

        for candidate_file in all_contract_files:
            try:
                with open(candidate_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if f'contract_id: "{contract_id}"' in content:
                        contract_file = candidate_file
                        break
            except Exception:
                continue
        
        if not contract_file:
            return ContractValidationResult(
                contract_id=contract_id,
                validation_id=str(uuid.uuid4()),
                implementation_status="error",
                issues_found=[{
                    "severity": "critical",
                    "category": "contract_not_found",
                    "description": f"Contract file not found for ID: {contract_id}",
                    "suggestion": "Verify contract ID exists in contracts directory"
                }]
            )
        
        # Validate the specific contract
        result = self.validate_contract_file(contract_file)
        
        return ContractValidationResult(
            contract_id=contract_id,
            validation_id=str(uuid.uuid4()),
            implementation_status=result.get("implementation_status", "error"),
            compliance_score=1.0 if result.get("implementation_status") == "implemented" else 0.5 if result.get("implementation_status") == "partial" else 0.0,
            parity_check_results=result.get("markers_found", []),
            issues_found=result.get("issues", []),
            recommendations=[
                f"Add missing implementations for: {', '.join(result.get('missing_implementations', []))}"
            ] if result.get("missing_implementations") else []
        )