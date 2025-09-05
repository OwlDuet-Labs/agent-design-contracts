#!/usr/bin/env python3
"""
ADC (Agent Design Contracts) CLI Tool

A command-line interface for managing Agent Design Contracts
across software projects with multi-provider AI support.
"""

import argparse
import sys

from .commands import (
    audit_command,
    config_command,
    generate_command,
    health_command,
    lint_command,
    refine_command,
    setup_vscode_command,
    validate_command,
)
from .logging_config import configure_logging, logger


# ADC-IMPLEMENTS: <adc-tool-agent-01>
def main():
    """Main entry point for the ADC CLI tool."""
    parser = argparse.ArgumentParser(
        description="ADC (Agent Design Contracts) CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  adc generate                    # Generate code from contracts
  adc generate --agent openai     # Use specific AI agent
  adc audit                       # Audit implementation
  adc audit --src-dir ./src       # Audit specific source directory
  adc refine contract.qmd         # Refine a contract
  adc config show                 # Show current configuration
  adc config set default_agent anthropic  # Set default agent
  adc setup-vscode               # Setup VS Code integration
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate code from ADC contracts"
    )
    generate_parser.add_argument(
        "--contracts-dir",
        default=".",
        help="Directory containing contracts (default: current directory)",
    )
    generate_parser.add_argument("--agent", help="AI agent to use (overrides config)")
    generate_parser.add_argument("--model", help="Model to use (overrides config)")

    # Audit command
    audit_parser = subparsers.add_parser(
        "audit", help="Audit implementation against ADC contracts"
    )
    audit_parser.add_argument(
        "--contracts-dir",
        default=".",
        help="Directory containing contracts (default: current directory)",
    )
    audit_parser.add_argument(
        "--src-dir", default="src", help="Source directory to audit (default: src)"
    )
    audit_parser.add_argument("--agent", help="AI agent to use (overrides config)")
    audit_parser.add_argument("--model", help="Model to use (overrides config)")

    # Refine command
    refine_parser = subparsers.add_parser("refine", help="Refine an ADC contract")
    refine_parser.add_argument(
        "contract_file", help="Path to the contract file to refine"
    )
    refine_parser.add_argument("--agent", help="AI agent to use (overrides config)")
    refine_parser.add_argument("--model", help="Model to use (overrides config)")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage ADC configuration")
    config_parser.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "set"],
        help="Configuration action (default: show)",
    )
    config_parser.add_argument("key", nargs="?", help="Configuration key to set")
    config_parser.add_argument("value", nargs="?", help="Configuration value to set")

    # Setup VS Code command
    vscode_parser = subparsers.add_parser(
        "setup-vscode", help="Set up VS Code integration for ADC"
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate ADC contract implementations"
    )
    validate_parser.add_argument("--contract", help="Specific contract ID to validate")
    validate_parser.add_argument(
        "--all", action="store_true", help="Validate all contracts"
    )
    validate_parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )

    # Health command
    health_parser = subparsers.add_parser(
        "health", help="Check system health and component status"
    )
    health_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed component information"
    )
    health_parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )

    # Lint command
    lint_parser = subparsers.add_parser(
        "lint", help="Lint and fix formatting issues in ADC contract files"
    )
    lint_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to directory or file to lint (default: current directory)",
    )
    lint_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without applying changes",
    )
    lint_parser.add_argument(
        "--no-backup", action="store_true", help="Do not create backup files"
    )
    lint_parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    configure_logging(verbose=args.verbose)

    # Handle no command case
    if not args.command:
        parser.print_help()
        return 0

    # Route to appropriate command handler
    try:
        if args.command == "generate":
            success = generate_command(
                contracts_dir=args.contracts_dir,
                agent=args.agent,
                model=args.model,
                verbose=args.verbose,
            )
        elif args.command == "audit":
            success = audit_command(
                contracts_dir=args.contracts_dir,
                src_dir=args.src_dir,
                agent=args.agent,
                model=args.model,
                verbose=args.verbose,
            )
        elif args.command == "refine":
            success = refine_command(
                contract_file=args.contract_file,
                agent=args.agent,
                model=args.model,
                verbose=args.verbose,
            )
        elif args.command == "config":
            success = config_command(
                action=args.action, key=args.key, value=args.value, verbose=args.verbose
            )
        elif args.command == "setup-vscode":
            success = setup_vscode_command(verbose=args.verbose)
        elif args.command == "validate":
            success = validate_command(
                contract_id=args.contract or "",
                all_contracts=args.all,
                json_output=args.json,
                verbose=args.verbose,
            )
        elif args.command == "health":
            success = health_command(
                detailed=args.detailed, json_output=args.json, verbose=args.verbose
            )
        elif args.command == "lint":
            success = lint_command(
                path=args.path,
                dry_run=args.dry_run,
                no_backup=args.no_backup,
                json_output=args.json,
                verbose=args.verbose,
            )
        else:
            logger.error(f"Unknown command: {args.command}")
            parser.print_help()
            return 1

        # Return appropriate exit code
        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
