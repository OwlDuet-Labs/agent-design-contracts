# agent-design-contracts/src/adc/__main__.py
import argparse

from .commands import (
    handle_audit_command,
    handle_config_command,
    handle_generate_command,
    handle_refine_command,
    handle_setup_vscode_command,
)
from .config import load_config

# Import logging configuration
from .logging_config import configure_logging, logger

# Import the new modular components
from .providers import get_available_providers


# ADC-IMPLEMENTS: <adc-tool-agent-01>
def main():
    """
    Main function for the ADC CLI tool.

    This function acts as the ADC Tool Orchestrator, implementing the thinking process:
    1. Parse command-line arguments
    2. Load configuration to determine active AI provider and model
    3. Delegate to appropriate command handler
    """
    # Load configuration
    config = load_config()
    default_agent = config.get("default_agent")

    # Get available providers
    available_providers = get_available_providers()

    if not available_providers:
        logger.error(
            "No AI providers available. Please install at least one of: google-generativeai, openai, or anthropic."
        )
        return

    # Update default_agent if it's not available
    if default_agent not in available_providers:
        if available_providers:
            default_agent = list(available_providers.keys())[0]
            config["default_agent"] = default_agent
        else:
            default_agent = None

    parser = argparse.ArgumentParser(
        description="Agent Design Contracts (ADC) CLI Tool."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- 'generate' command ---
    gen_parser = subparsers.add_parser(
        "generate", help="Generate code scaffold from contracts."
    )
    gen_parser.add_argument(
        "--contracts",
        default="contracts",
        help="Path to the directory with ADC contracts.",
    )
    gen_parser.add_argument(
        "--prompts",
        default=None,
        help="Path to custom prompts directory (optional).",
    )
    gen_parser.add_argument(
        "--agent",
        default=config["task_agents"].get("generate", default_agent),
        help=f"AI agent to use (default: {config['task_agents'].get('generate', default_agent)})",
        choices=list(available_providers.keys()),
    )
    gen_parser.add_argument(
        "--model",
        default=None,
        help="Specific model to use (overrides default for the agent)",
    )
    gen_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    # --- 'audit' command ---
    audit_parser = subparsers.add_parser("audit", help="Audit code against contracts.")
    audit_parser.add_argument(
        "--contracts",
        default="contracts",
        help="Path to the directory with ADC contracts.",
    )
    audit_parser.add_argument(
        "--code", default="src", help="Path to the source code directory to audit."
    )
    audit_parser.add_argument(
        "--prompts",
        default=None,
        help="Path to custom prompts directory (optional).",
    )
    audit_parser.add_argument(
        "--agent",
        default=config["task_agents"].get("audit", default_agent),
        help=f"AI agent to use (default: {config['task_agents'].get('audit', default_agent)})",
        choices=list(available_providers.keys()),
    )
    audit_parser.add_argument(
        "--model",
        default=None,
        help="Specific model to use (overrides default for the agent)",
    )
    audit_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    # --- 'refine' command ---
    refine_parser = subparsers.add_parser("refine", help="Refine ADC contracts.")
    refine_parser.add_argument(
        "--contracts",
        default="contracts",
        help="Path to the directory with ADC contracts to refine.",
    )
    refine_parser.add_argument(
        "--prompts",
        default=None,
        help="Path to custom prompts directory (optional).",
    )
    refine_parser.add_argument(
        "--agent",
        default=config["task_agents"].get("refine", default_agent),
        help=f"AI agent to use (default: {config['task_agents'].get('refine', default_agent)})",
        choices=list(available_providers.keys()),
    )
    refine_parser.add_argument(
        "--model",
        default=None,
        help="Specific model to use (overrides default for the agent)",
    )
    refine_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    # --- 'setup-vscode' command ---
    setup_vscode_parser = subparsers.add_parser(
        "setup-vscode", help="Generate VSCode tasks.json for ADC commands."
    )
    setup_vscode_parser.add_argument(
        "--target-dir",
        default=".",
        help="Target directory to create .vscode/tasks.json (default: current directory)",
    )
    setup_vscode_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    # --- 'config' command ---
    config_parser = subparsers.add_parser(
        "config", help="Configure default agents and models."
    )
    config_parser.add_argument(
        "--list",
        action="store_true",
        help="List current configuration",
    )
    config_parser.add_argument(
        "--set-default",
        help="Set default agent",
        choices=list(available_providers.keys()),
    )
    config_parser.add_argument(
        "--set-generate",
        help="Set agent for code generation",
        choices=list(available_providers.keys()),
    )
    config_parser.add_argument(
        "--set-audit",
        help="Set agent for code auditing",
        choices=list(available_providers.keys()),
    )
    config_parser.add_argument(
        "--set-refine",
        help="Set agent for contract refinement",
        choices=list(available_providers.keys()),
    )
    config_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level based on verbosity
    if hasattr(args, "verbose") and args.verbose:
        configure_logging(verbose=True)
        logger.debug("Debug logging enabled")

    # Delegate to appropriate command handler
    if args.command == "generate":
        handle_generate_command(args, config)
    elif args.command == "audit":
        handle_audit_command(args, config)
    elif args.command == "refine":
        handle_refine_command(args, config)
    elif args.command == "setup-vscode":
        handle_setup_vscode_command(args)
    elif args.command == "config":
        handle_config_command(args, config)


if __name__ == "__main__":
    main()
