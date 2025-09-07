# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Agentic Design Contracts (ADC)** framework - a methodology for designing and building AI-driven systems through machine-readable contracts and specialized AI agents. The framework bridges the gap between system design and implementation by providing traceable links between design blocks and code.

## Development Commands

### Installation & Setup

```bash
# Install core ADC tool
pip install -e .

# Install with specific AI providers
pip install -e ".[anthropic]"  # For Claude
pip install -e ".[openai]"      # For GPT  
pip install -e ".[gemini]"      # For Gemini
pip install -e ".[all]"         # All providers

# Set up API keys (required for ADC commands)
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adc_cli --cov-report=term-missing

# Run specific test file
pytest tests/test_providers.py -v
```

### ADC CLI Commands

```bash
# Generate code from contracts
adc generate
adc generate --agent openai

# Audit implementation compliance
adc audit
adc audit --src-dir ./src

# Refine contracts
adc refine contract.qmd

# Lint contracts for validation
adc lint contracts/

# Validate contract syntax
adc validate contract.qmd

# Configuration management
adc config show
adc config set default_agent anthropic

# Health check
adc health
```

## Architecture

### Core Package Structure

- **`src/adc_cli/`** - Main CLI implementation
  - `providers.py` - AI provider integrations (Anthropic, OpenAI, Gemini)
  - `commands.py` - Command implementations (generate, audit, refine, etc.)
  - `config.py` - Configuration management
  - `contract_lint.py` - Contract validation and linting
  - `agents/` - Agent role implementations
  - `algorithms/` - Contract parsing and processing algorithms
  - `validation/` - Contract schema validation

### AI Agent Roles

- **`roles/`** - Markdown role definitions for AI agents:
  - `code_generator.md` - Transforms contracts into production code
  - `auditor.md` - Verifies code compliance with contracts
  - `refiner.md` - Improves contract quality
  - `system_evaluator.md` - Evaluates compliant systems
  - `pr_orchestrator.md` - Manages deployment process
  - `simulator.md` - Tests system behavior
  - `contract_writer.md` - Creates initial design contracts

### Contract Files

- **`contracts/`** - Example ADC contracts demonstrating schema usage
- **`adc-schema.qmd`** - Complete ADC schema specification defining block types and format

### ADC Contract Schema

Contracts use typed design blocks with unique IDs:
- `[Agent]` - Autonomous agents with personas and algorithms
- `[DataModel]` - Data structures and schemas  
- `[Algorithm]` - Business logic and calculations
- `[Tool]` - External services and integrations
- `[Feature]` - User-facing capabilities
- `[TestScenario]` - Test cases and edge cases
- `[APIEndpoint]` - Service API endpoints
- `[Constraint]` - Non-functional requirements

Each implementable block must include a **Parity** section linking to implementation files and tests.

## Development Workflow

1. **Contract Creation**: Write ADC contracts defining system components with unique IDs
2. **Validation**: Run `adc lint` to validate contract syntax and structure
3. **Code Generation**: Use `adc generate` to create implementation from contracts
4. **Audit Compliance**: Run `adc audit` to verify code matches contracts
5. **Refinement**: Use `adc refine` to improve contract quality based on insights
6. **Testing**: Run pytest to verify implementation correctness

## Important Implementation Details

### ADC-IMPLEMENTS Markers
Code generated from contracts includes `# ADC-IMPLEMENTS: <block-id>` markers to maintain traceability between design and implementation.

### Provider Configuration
The system supports multiple AI providers configured via environment variables. The provider selection hierarchy:
1. Command-line flag (`--agent`)
2. Environment variable (`ADC_DEFAULT_AGENT`)
3. Config file (`~/.adc/config.yaml`)
4. Default fallback (anthropic)

### Contract File Conventions
- Contracts should be stored in a `contracts/` directory
- Use `.qmd` or `.md` extensions for contract files
- Include YAML front matter with metadata
- Use stable, unique IDs for all design blocks