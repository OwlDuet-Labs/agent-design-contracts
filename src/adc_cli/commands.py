# agent-design-contracts/src/adc_cli/commands.py
import json
from pathlib import Path

from .config import load_config
from .logging_config import logger
from .providers import call_ai_agent


# ADC-IMPLEMENTS: <adc-tool-feature-01>
def generate_command(
    contracts_dir: str = ".",
    agent: str = "",
    model: str = "",
    verbose: bool = False,
):
    """Generate code from ADC contracts."""
    logger.info(f"Generating code from contracts in {contracts_dir}")

    # Load configuration
    config = load_config()

    # Determine the agent to use
    if not agent:
        agent = config["task_agents"].get("generate", config["default_agent"])

    if not agent:
        logger.error("No agent specified and no default agent configured")
        return False

    # Determine model
    if not model:
        model = config["models"].get(agent, "")

    logger.info(f"Using agent: {agent}, model: {model}")

    # Read the code generator role
    try:
        role_path = Path("roles/code_generator.md")
        if not role_path.exists():
            logger.error(f"Code generator role not found at {role_path}")
            return False

        with open(role_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        logger.error(f"Error reading code generator role: {e}")
        return False

    # Find all contract files in contracts directory (supports both .md and .qmd)
    contracts_path = Path(contracts_dir) / "contracts"
    if not contracts_path.exists():
        logger.error(f"Contracts directory not found: {contracts_path}")
        return False

    # Prefer .md files, include .qmd for backward compatibility
    md_files = list(contracts_path.glob("*.md"))
    qmd_files = list(contracts_path.glob("*.qmd"))
    # Filter out .qmd files that have .md equivalents
    qmd_only = [f for f in qmd_files if f.with_suffix('.md') not in md_files]
    contract_files = md_files + qmd_only

    if not contract_files:
        logger.warning(f"No contract files found in {contracts_path}")
        return False

    logger.info(f"Found {len(contract_files)} contract files")

    # Read all contract files
    contracts_content = ""
    for contract_file in contract_files:
        try:
            with open(contract_file, "r", encoding="utf-8") as f:
                contracts_content += f"\n\n=== {contract_file.name} ===\n"
                contracts_content += f.read()
        except Exception as e:
            logger.error(f"Error reading contract file {contract_file}: {e}")
            continue

    if not contracts_content.strip():
        logger.error("No contract content found")
        return False

    # Generate code using AI
    user_prompt = f"Please generate code for these ADC contracts:\n{contracts_content}"

    response = call_ai_agent(agent, system_prompt, user_prompt, model)

    if response.startswith("Error:"):
        logger.error(f"AI generation failed: {response}")
        return False

    # Output the generated code
    print("\n" + "=" * 50)
    print("GENERATED CODE")
    print("=" * 50)
    print(response)
    print("=" * 50)

    return True


# ADC-IMPLEMENTS: <adc-tool-feature-02>
def audit_command(
    contracts_dir: str = ".",
    src_dir: str = "src",
    agent: str = "",
    model: str = "",
    verbose: bool = False,
):
    """Audit implementation against ADC contracts."""
    logger.info(
        f"Auditing implementation in {src_dir} against contracts in {contracts_dir}"
    )

    # Load configuration
    config = load_config()

    # Determine the agent to use
    if not agent:
        agent = config["task_agents"].get("audit", config["default_agent"])

    if not agent:
        logger.error("No agent specified and no default agent configured")
        return False

    # Determine model
    if not model:
        model = config["models"].get(agent, "")

    logger.info(f"Using agent: {agent}, model: {model}")

    # Read the auditor role
    try:
        role_path = Path("roles/auditor.md")
        if not role_path.exists():
            logger.error(f"Auditor role not found at {role_path}")
            return False

        with open(role_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        logger.error(f"Error reading auditor role: {e}")
        return False

    # Find contracts and source files
    contracts_path = Path(contracts_dir) / "contracts"
    src_path = Path(src_dir)

    if not contracts_path.exists():
        logger.error(f"Contracts directory not found: {contracts_path}")
        return False

    if not src_path.exists():
        logger.error(f"Source directory not found: {src_path}")
        return False

    # Read all contract files (supports both .md and .qmd)
    contracts_content = ""
    md_files = list(contracts_path.glob("*.md"))
    qmd_files = list(contracts_path.glob("*.qmd"))
    # Filter out .qmd files that have .md equivalents
    qmd_only = [f for f in qmd_files if f.with_suffix('.md') not in md_files]
    audit_contract_files = md_files + qmd_only

    for contract_file in audit_contract_files:
        try:
            with open(contract_file, "r", encoding="utf-8") as f:
                contracts_content += f"\n\n=== CONTRACT: {contract_file.name} ===\n"
                contracts_content += f.read()
        except Exception as e:
            logger.error(f"Error reading contract file {contract_file}: {e}")
            continue

    # Read source files (Python files)
    source_content = ""
    py_files = list(src_path.rglob("*.py"))

    for py_file in py_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                source_content += (
                    f"\n\n=== SOURCE: {py_file.relative_to(src_path)} ===\n"
                )
                source_content += f.read()
        except Exception as e:
            logger.error(f"Error reading source file {py_file}: {e}")
            continue

    if not contracts_content.strip():
        logger.error("No contract content found")
        return False

    if not source_content.strip():
        logger.error("No source content found")
        return False

    # Prepare audit prompt
    user_prompt = f"""Please audit this implementation against the ADC contracts.

CONTRACTS:
{contracts_content}

IMPLEMENTATION:
{source_content}
"""

    response = call_ai_agent(agent, system_prompt, user_prompt, model)

    if response.startswith("Error:"):
        logger.error(f"AI audit failed: {response}")
        return False

    # Output the audit results
    print("\n" + "=" * 50)
    print("AUDIT RESULTS")
    print("=" * 50)
    print(response)
    print("=" * 50)

    return True


# ADC-IMPLEMENTS: <adc-tool-feature-03>
def refine_command(
    contract_file: str, agent: str = "", model: str = "", verbose: bool = False
):
    """Refine an ADC contract."""
    logger.info(f"Refining contract: {contract_file}")

    # Load configuration
    config = load_config()

    # Determine the agent to use
    if not agent:
        agent = config["task_agents"].get("refine", config["default_agent"])

    if not agent:
        logger.error("No agent specified and no default agent configured")
        return False

    # Determine model
    if not model:
        model = config["models"].get(agent, "")

    logger.info(f"Using agent: {agent}, model: {model}")

    # Read the refiner role
    try:
        role_path = Path("roles/refiner.md")
        if not role_path.exists():
            logger.error(f"Refiner role not found at {role_path}")
            return False

        with open(role_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        logger.error(f"Error reading refiner role: {e}")
        return False

    # Read the contract file
    contract_path = Path(contract_file)
    if not contract_path.exists():
        logger.error(f"Contract file not found: {contract_path}")
        return False

    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            contract_content = f.read()
    except Exception as e:
        logger.error(f"Error reading contract file: {e}")
        return False

    # Prepare refinement prompt
    user_prompt = f"Please review and refine this ADC contract:\n\n{contract_content}"

    response = call_ai_agent(agent, system_prompt, user_prompt, model)

    if response.startswith("Error:"):
        logger.error(f"AI refinement failed: {response}")
        return False

    # Output the refinement results
    print("\n" + "=" * 50)
    print("REFINEMENT RESULTS")
    print("=" * 50)
    print(response)
    print("=" * 50)

    return True


# ADC-IMPLEMENTS: <adc-tool-feature-04>
def config_command(
    action: str = "show", key: str = "", value: str = "", verbose: bool = False
):
    """Manage ADC configuration."""
    config = load_config()

    if action == "show":
        print("\nCurrent ADC Configuration:")
        print("=" * 30)
        print(json.dumps(config, indent=2))
        return True

    elif action == "set" and key and value:
        from .config import update_config

        # Handle nested keys like task_agents.generate
        if "." in key:
            main_key, sub_key = key.split(".", 1)
            if main_key == "task_agents":
                update_key = f"task_{sub_key}"
                success = update_config(**{update_key: value})
            else:
                logger.error(f"Unsupported nested key: {key}")
                return False
        else:
            success = update_config(**{key: value})

        if success:
            print(f"Configuration updated: {key} = {value}")
            return True
        else:
            print("Failed to update configuration")
            return False
    else:
        print("Usage: adc config [show | set <key> <value>]")
        print("Example: adc config set default_agent anthropic")
        print("Example: adc config set task_agents.generate openai")
        return False


# ADC-IMPLEMENTS: <adc-tool-feature-05>
def setup_vscode_command(verbose: bool = False):
    """Set up VS Code integration for ADC."""
    logger.info("Setting up VS Code integration for ADC")

    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)

    # Create settings.json with ADC file associations
    settings_file = vscode_dir / "settings.json"
    settings = {}

    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read existing VS Code settings: {e}")

    # Add ADC-specific settings
    # Note: *.md association is redundant (VS Code handles natively) but *.qmd needs it
    adc_settings = {
        "files.associations": {"*.qmd": "markdown"},
        "markdown.extension.list.indentationSize": "compact",
        "markdown.extension.toc.levels": "2..6",
    }

    # Merge settings
    for key, value in adc_settings.items():
        if (
            key in settings
            and isinstance(settings[key], dict)
            and isinstance(value, dict)
        ):
            settings[key].update(value)
        else:
            settings[key] = value

    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        print(f"VS Code settings updated at {settings_file}")
    except Exception as e:
        logger.error(f"Error writing VS Code settings: {e}")
        return False

    # Create tasks.json for ADC commands
    tasks_file = vscode_dir / "tasks.json"
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "ADC: Generate Code",
                "type": "shell",
                "command": "adc",
                "args": ["generate"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared",
                },
            },
            {
                "label": "ADC: Audit Implementation",
                "type": "shell",
                "command": "adc",
                "args": ["audit"],
                "group": "test",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared",
                },
            },
        ],
    }

    try:
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
        print(f"VS Code tasks created at {tasks_file}")
    except Exception as e:
        logger.error(f"Error writing VS Code tasks: {e}")
        return False

    print("✅ VS Code integration set up successfully!")
    print("You can now:")
    print("  - Use Ctrl+Shift+P -> 'Tasks: Run Task' -> 'ADC: Generate Code'")
    print("  - Use Ctrl+Shift+P -> 'Tasks: Run Task' -> 'ADC: Audit Implementation'")
    print("  - ADC contract files (.md, .qmd) will be treated as Markdown with syntax highlighting")

    return True


# ADC-IMPLEMENTS: <cli-validation-feature-01>
def validate_command(
    contract_id: str = "",
    all_contracts: bool = False,
    json_output: bool = False,
    verbose: bool = False,
):
    """Validate ADC contract implementations."""
    from .validation.contract_validator import ContractValidator
    
    logger.info("Starting contract validation")
    
    validator = ContractValidator()
    
    if contract_id:
        # Validate specific contract
        result = validator.validate_specific_contract(contract_id)
        output_data = {
            "status": "success" if result.implementation_status == "implemented" else "partial",
            "timestamp": result.validation_timestamp,
            "contract_id": result.contract_id,
            "implementation_status": result.implementation_status,
            "compliance_score": result.compliance_score,
            "issues": result.issues_found,
            "recommendations": result.recommendations
        }
    else:
        # Validate all contracts
        output_data = validator.validate_all_contracts()
    
    if json_output:
        print(json.dumps(output_data, indent=2))
    else:
        print("\n" + "=" * 50)
        print("CONTRACT VALIDATION RESULTS")
        print("=" * 50)
        
        if contract_id:
            print(f"Contract: {contract_id}")
            print(f"Status: {output_data['implementation_status']}")
            print(f"Compliance Score: {output_data['compliance_score']:.2f}")
            if output_data['issues']:
                print("\nIssues Found:")
                for issue in output_data['issues']:
                    print(f"  - {issue.get('description', 'Unknown issue')}")
        else:
            summary = output_data['validation_summary']
            print(f"Total Contracts: {summary['total_contracts']}")
            print(f"Implemented: {summary['implemented']}")
            print(f"Partial: {summary['partial']}")
            print(f"Missing: {summary['missing']}")
            print(f"Overall Compliance: {summary['compliance_score']:.2f}")
        
        print("=" * 50)
    
    return True


# ADC-IMPLEMENTS: <health-checker-tool-01>
def health_command(detailed: bool = False, json_output: bool = False, verbose: bool = False):
    """Check system health and component status."""
    import asyncio
    from .validation.health_checker import HealthChecker
    
    logger.info("Starting system health check")
    
    async def run_health_check():
        checker = HealthChecker()
        return await checker.check_system_health()
    
    # Run the async health check
    health_report = asyncio.run(run_health_check())
    
    output_data = {
        "status": health_report.overall_status,
        "timestamp": health_report.timestamp,
        "health_score": health_report.health_score,
        "overall_status": health_report.overall_status,
        "components": health_report.components if detailed else {
            name: {"status": comp.get("status", "unknown"), "score": comp.get("score", 0.0)}
            for name, comp in health_report.components.items()
        },
        "recommendations": health_report.recommendations
    }
    
    if json_output:
        print(json.dumps(output_data, indent=2))
    else:
        print("\n" + "=" * 50)
        print("SYSTEM HEALTH REPORT")
        print("=" * 50)
        print(f"Overall Status: {health_report.overall_status.upper()}")
        print(f"Health Score: {health_report.health_score:.2f}")
        
        print("\nComponent Status:")
        for name, component in health_report.components.items():
            status = component.get("status", "unknown")
            score = component.get("score", 0.0)
            print(f"  {name}: {status.upper()} (score: {score:.2f})")
        
        if health_report.recommendations:
            print("\nRecommendations:")
            for rec in health_report.recommendations:
                print(f"  - {rec}")
        
        print("=" * 50)
    
    return True


def lint_command(
    path: str = ".",
    dry_run: bool = False,
    no_backup: bool = False,
    json_output: bool = False,
    verbose: bool = False
):
    """Lint and fix formatting issues in ADC contract files."""
    from .contract_lint import ContractLinter
    
    logger.info(f"Running contract linting on: {path}")
    
    # Configure linter
    config = {
        'dry_run': dry_run,
        'backup_originals': not no_backup,
        'verbose': verbose
    }
    
    linter = ContractLinter(config)
    
    # Check if path is a file or directory
    if os.path.isfile(path):
        # Lint single file
        results = linter.lint_contract_file(path)
        results = {
            'total_files': 1,
            'files_processed': 1,
            'files_updated': 1 if results['file_updated'] else 0,
            'total_fixes': len(results['fixes_applied']),
            'file_results': [results]
        }
    else:
        # Lint directory
        results = linter.run_contract_lint(path)
    
    # Output results
    if json_output:
        print(json.dumps(results, indent=2))
    else:
        print(f"\nContract Linting Report")
        print(f"=" * 50)
        print(f"Files processed: {results['files_processed']}")
        print(f"Files updated: {results['files_updated']}")
        print(f"Total fixes applied: {results['total_fixes']}")
        
        if dry_run:
            print("\n[DRY RUN] No files were actually modified")
        
        if results['file_results']:
            print(f"\nDetailed Results:")
            print(f"-" * 50)
            
            for file_result in results['file_results']:
                if file_result['fixes_applied'] or file_result['warnings'] or file_result['errors']:
                    print(f"\n{file_result['file']}:")
                    
                    if file_result['fixes_applied']:
                        print(f"  Fixes applied: {', '.join(file_result['fixes_applied'])}")
                    
                    if file_result['warnings']:
                        print(f"  Warnings:")
                        for warning in file_result['warnings']:
                            print(f"    - {warning}")
                    
                    if file_result['errors']:
                        print(f"  Errors:")
                        for error in file_result['errors']:
                            print(f"    - {error}")
                    
                    if 'backup_created' in file_result:
                        print(f"  Backup: {file_result['backup_created']}")
        
        print("\nLinting complete!")
    
    # Return success if no errors
    return all(
        not file_result.get('errors', [])
        for file_result in results.get('file_results', [])
    )
