"""
ADC Init Command - Initialize ADC project structure
"""

import shutil
from pathlib import Path
from typing import Optional

from ..logging_config import logger


def add_init_parser(subparsers):
    """Add init command parser."""
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize ADC project structure"
    )
    init_parser.add_argument(
        "--path",
        default=".",
        help="Project root path (default: current directory)"
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing directories and files"
    )


def init_command(path: str = ".", force: bool = False) -> bool:
    """
    Initialize ADC project structure.
    
    Creates the standard ADC directory structure and .gitignore file.
    
    Args:
        path: Project root path
        force: Overwrite existing directories
        
    Returns:
        True if successful, False otherwise
    """
    project_root = Path(path).resolve()
    
    logger.info(f"Initializing ADC project structure in: {project_root}")
    
    # Define directory structure
    directories = [
        "contracts",
        "adc_files/refinement",
        "adc_files/compliance",
        "adc_files/evaluation",
        "adc_files/implementation",
        "adc_files/releases",
        "claude_tmp/scratch",
        "claude_tmp/debug",
        "claude_tmp/temp_outputs",
    ]
    
    # Create directories
    created_dirs = []
    skipped_dirs = []
    
    for dir_path in directories:
        full_path = project_root / dir_path
        
        if full_path.exists() and not force:
            skipped_dirs.append(dir_path)
            logger.debug(f"Directory already exists: {dir_path}")
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(dir_path)
                logger.debug(f"Created directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                return False
    
    # Create .gitignore if it doesn't exist or update it
    gitignore_path = project_root / ".gitignore"
    gitignore_created = False
    gitignore_updated = False
    
    try:
        # Load template .gitignore from package
        import importlib.resources as resources
        import adc.templates
        
        template_content = resources.files(adc.templates).joinpath('gitignore.template').read_text()
        
        if not gitignore_path.exists():
            # Create new .gitignore
            gitignore_path.write_text(template_content)
            gitignore_created = True
            logger.info("Created .gitignore from template")
        else:
            # Check if ADC patterns are already present
            existing_content = gitignore_path.read_text()
            
            if "claude_tmp/" not in existing_content or "adc_files/refinement/" not in existing_content:
                # Append ADC patterns
                with open(gitignore_path, 'a') as f:
                    f.write("\n# ADC Temporary Files\n")
                    f.write("claude_tmp/\n")
                    f.write("adc_files/refinement/\n")
                    f.write("\n# ADC Configuration\n")
                    f.write(".adcconfig.json\n")
                    f.write("*.adc-backup\n")
                    f.write("contracts/*.tmp\n")
                    f.write("contracts/*.bak\n")
                gitignore_updated = True
                logger.info("Updated .gitignore with ADC patterns")
            else:
                logger.debug(".gitignore already contains ADC patterns")
                
    except Exception as e:
        logger.warning(f"Could not create/update .gitignore: {e}")
    
    # Create README in contracts directory
    contracts_readme = project_root / "contracts" / "README.md"
    if not contracts_readme.exists() or force:
        try:
            contracts_readme.write_text("""# ADC Contracts

This directory contains Agent Design Contract (ADC) specifications.

## File Naming Convention

Contracts should follow this naming pattern:
- `ADC_{NUMBER}_{NAME}.qmd`
- Example: `ADC_001_SYSTEM_ARCHITECTURE.qmd`

## Structure

Each contract file should:
1. Start with YAML front matter containing metadata
2. Include design blocks following the ADC schema
3. Reference the schema at `~/.claude/schema/adc-schema.qmd`

## Workflow

1. **Create**: Write new contracts using `@adc-contract-writer`
2. **Refine**: Improve contracts using `@adc-contract-refiner`
3. **Implement**: Generate code using `@adc-code-generator`
4. **Audit**: Check compliance using `@adc-compliance-auditor`
5. **Evaluate**: Test system using `@adc-system-evaluator`
6. **Release**: Create PRs using `@adc-pr-orchestrator`

See the ADC schema for complete documentation.
""")
            logger.debug("Created contracts/README.md")
        except Exception as e:
            logger.warning(f"Could not create contracts/README.md: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("ADC Project Initialization Complete")
    print("=" * 60)
    
    if created_dirs:
        print(f"\n✅ Created {len(created_dirs)} directories:")
        for dir_path in created_dirs:
            print(f"   - {dir_path}")
    
    if skipped_dirs:
        print(f"\n⏭️  Skipped {len(skipped_dirs)} existing directories:")
        for dir_path in skipped_dirs[:5]:  # Show first 5
            print(f"   - {dir_path}")
        if len(skipped_dirs) > 5:
            print(f"   ... and {len(skipped_dirs) - 5} more")
        print(f"\n   Use --force to overwrite existing directories")
    
    if gitignore_created:
        print(f"\n✅ Created .gitignore")
    elif gitignore_updated:
        print(f"\n✅ Updated .gitignore with ADC patterns")
    
    print(f"\n📁 Project root: {project_root}")
    print(f"\n📚 Next steps:")
    print(f"   1. Create your first contract in contracts/")
    print(f"   2. Run 'adc-setup' to install Claude Code integration")
    print(f"   3. Use '@adc-contract-writer' to create contracts")
    print(f"   4. See the schema: cat ~/.claude/schema/adc-schema.qmd")
    print("=" * 60)
    
    return True
