# ADC Installation Guide

This guide covers how to install ADC (Agent Design Contracts) as a standalone package without needing the source code.

## 📦 Installation Methods

### Method 1: Install from PyPI (Recommended)

Once published to PyPI, you can install ADC with a single command:

```bash
# Install with all AI providers
pipx install agentic-design-contracts[all]

# Or install with specific providers
pipx install agentic-design-contracts[anthropic]  # Claude only
pipx install agentic-design-contracts[openai]     # GPT only
pipx install agentic-design-contracts[gemini]     # Gemini only
```

### Method 2: Install from Wheel File

If you have a `.whl` file:

```bash
# Install the wheel
pipx install agentic_design_contracts-0.9.0-py3-none-any.whl[all]
```

### Method 3: Install from Git Repository

```bash
# Install directly from GitHub
pipx install "git+https://github.com/OwlDuet-Labs/agent-design-contracts.git[all]"
```

### Method 4: Install from Local Source

```bash
# Clone and install
git clone https://github.com/OwlDuet-Labs/agent-design-contracts.git
cd agent-design-contracts
pipx install -e ".[all]"
```

## 🔧 Post-Installation Setup

After installing ADC, run the setup command to configure your environment:

```bash
adc-setup
```

This will:
- ✅ Install `/adc` command for Claude Code
- ✅ Install ADC agents (`@adc-*`) for Claude Code
- ✅ Set up necessary directories

## 🔑 Configure API Keys

Add your AI provider API keys to your shell profile (`~/.zshrc` or `~/.bash_profile`):

```bash
# Add these lines to ~/.zshrc
export ANTHROPIC_API_KEY="your-anthropic-key-here"
export OPENAI_API_KEY="your-openai-key-here"
export GOOGLE_API_KEY="your-google-key-here"
```

Then reload your shell:

```bash
source ~/.zshrc
```

### Get API Keys

- **Anthropic (Claude)**: https://console.anthropic.com/
- **OpenAI (GPT)**: https://platform.openai.com/api-keys
- **Google (Gemini)**: https://makersuite.google.com/app/apikey

## ✅ Verify Installation

Test that everything is working:

```bash
# Check ADC CLI is installed
adc --help

# Check system health
adc health

# Verify Claude Code integration
# Open Claude Code and type: /adc
```

## 📋 What Gets Installed

### 1. CLI Tool (`adc` command)
Available system-wide for:
- `adc generate` - Generate code from contracts
- `adc audit` - Audit implementation compliance
- `adc refine` - Improve contract quality
- `adc lint` - Validate contract syntax
- `adc health` - Check system status

### 2. Claude Code Command (`/adc`)
Location: `~/.claude/commands/adc.md`

Use in Claude Code:
```
/adc create contracts for user authentication
/adc run full ADC loop
adc-test: Create a simple blog engine
adc-eval: Test with 100 users
```

### 3. Claude Code Agents
Location: `~/.claude/agents/`

Available agents:
- `@adc-code-generator` - Generate code from contracts
- `@adc-compliance-auditor` - Audit code compliance
- `@adc-contract-writer` - Create ADC contracts
- `@adc-contract-refiner` - Improve contracts
- `@adc-app-simulator` - Generate test applications
- `@adc-pr-orchestrator` - Manage releases
- `@adc-workflow-orchestrator` - Coordinate workflows

## 🚀 Quick Start

### 1. Create Your First Project

```bash
# Create project directory
mkdir my-adc-project
cd my-adc-project

# Initialize contracts directory
mkdir contracts

# Open in Claude Code
code .
```

### 2. Use ADC in Claude Code

In Claude Code chat:
```
/adc create contracts for a REST API with user authentication and CRUD operations
```

### 3. Generate Implementation

```bash
# Generate code from contracts
adc generate --contracts-dir ./contracts

# Audit the implementation
adc audit --contracts-dir ./contracts --src-dir ./src
```

## 🔄 Updating ADC

To update to the latest version:

```bash
# Update from PyPI
pipx upgrade agentic-design-contracts

# Re-run setup to update Claude Code files
adc-setup
```

## 🗑️ Uninstalling

To completely remove ADC:

```bash
# Uninstall the package
pipx uninstall agentic-design-contracts

# Optionally remove Claude Code files
rm -rf ~/.claude/commands/adc.md
rm -rf ~/.claude/agents/adc-*.md
```

## 🆘 Troubleshooting

### "adc: command not found"
- Ensure pipx is installed: `brew install pipx`
- Ensure pipx path is configured: `pipx ensurepath`
- Restart your terminal

### "API key not found"
- Add API keys to `~/.zshrc` (see Configure API Keys section)
- Run `source ~/.zshrc` to reload

### "/adc command not working in Claude Code"
- Run `adc-setup` to install Claude Code files
- Restart Claude Code
- Check that `~/.claude/commands/adc.md` exists

### "Agents not showing up"
- Run `adc-setup` to install agents
- Check that `~/.claude/agents/` contains `adc-*.md` files
- Restart Claude Code

## 📚 Additional Resources

- **Documentation**: https://github.com/OwlDuet-Labs/agent-design-contracts
- **Schema Reference**: Access via `adc` package data
- **Examples**: See contracts in the repository
- **Issues**: https://github.com/OwlDuet-Labs/agent-design-contracts/issues

## 🎯 Next Steps

1. ✅ Install ADC
2. ✅ Run `adc-setup`
3. ✅ Configure API keys
4. ✅ Test with `adc health`
5. 🚀 Start building with `/adc` in Claude Code!

---

**Need help?** Open an issue on GitHub or check the documentation.
