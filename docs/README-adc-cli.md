# ADC Command-Line Tool Documentation

A comprehensive CLI tool for managing Agent Design Contracts across projects with support for multiple AI providers (Anthropic Claude, OpenAI GPT, Google Gemini).

## Installation

```bash
# From the repository root
pip install -e .

# Install AI provider packages as needed
pip install google-generativeai  # For Gemini
pip install openai              # For OpenAI GPT models
pip install anthropic           # For Claude models
```

## Usage

The ADC tool provides several commands for working with Agent Design Contracts:

### Generate Code from Contracts

```bash
adc generate --contracts path/to/contracts [--agent anthropic|openai|gemini] [--model model-name]
```

Options:
- `--contracts`: Path to the directory containing ADC contract files (*.md)
- `--prompts`: (Optional) Path to a directory with custom prompt templates
- `--agent`: (Optional) AI provider to use (anthropic, openai, gemini)
- `--model`: (Optional) Specific model to use (e.g., "claude-3-sonnet-20240229")

### Audit Code Against Contracts

```bash
adc audit --contracts path/to/contracts --code path/to/source [--agent anthropic|openai|gemini]
```

Options:
- `--contracts`: Path to the directory containing ADC contract files (*.md)
- `--code`: Path to the source code directory to audit
- `--prompts`: (Optional) Path to a directory with custom prompt templates
- `--agent`: (Optional) AI provider to use
- `--model`: (Optional) Specific model to use

### Refine Contracts

```bash
adc refine --contracts path/to/contracts [--agent anthropic|openai|gemini]
```

Options:
- `--contracts`: Path to the directory containing ADC contract files (*.md)
- `--prompts`: (Optional) Path to a directory with custom prompt templates
- `--agent`: (Optional) AI provider to use
- `--model`: (Optional) Specific model to use

### Configure Default Agents

```bash
# List current configuration
adc config --list

# Set default agent
adc config --set-default anthropic

# Set task-specific agents
adc config --set-generate anthropic
adc config --set-audit openai
adc config --set-refine gemini
```

### Set Up VSCode Integration

```bash
adc setup-vscode --target-dir path/to/project
```

This command creates a `.vscode/tasks.json` file with pre-configured tasks for ADC commands.

## Using ADC Across Projects

The ADC tool is designed to be installed once and used across multiple projects:

1. **Install the ADC package**:
   ```bash
   cd agent-design-contracts
   pip install -e .
   ```

2. **Set up VSCode integration in each project**:
   ```bash
   cd your-project
   adc setup-vscode
   ```

3. **Run ADC commands from any project**:
   - From the command line: `adc generate --contracts contracts`
   - From VSCode: Press `Ctrl+Shift+P` and select `Tasks: Run Task`, then choose an ADC task

## Environment Variables

- `ANTHROPIC_API_KEY`: Required for Claude models
- `OPENAI_API_KEY`: Required for OpenAI models
- `GOOGLE_API_KEY`: Required for Gemini models

## Configuration

The tool uses a configuration file stored at `~/.adcconfig.json` with the following structure:

```json
{
  "default_agent": "anthropic",
  "task_agents": {
    "generate": "anthropic",
    "audit": "anthropic",
    "refine": "gemini"
  },
  "models": {
    "anthropic": "claude-3-sonnet-20240229",
    "openai": "gpt-4o",
    "gemini": "gemini-1.5-pro-latest"
  }
}
```

You can edit this file directly or use the `adc config` command.

## Custom Prompts

You can customize the prompts used for code generation, auditing, and refinement:

1. Create a directory for your custom prompts
2. Add files named `code_generator.md`, `auditor.md`, and `refiner.md`
3. Pass the directory path with the `--prompts` option

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 