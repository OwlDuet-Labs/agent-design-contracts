# ADC Setup Guide for New Projects

This guide covers different ways to set up and use ADC (Agent Design Contracts) in your projects, from simple installations to full team integrations.

## Installation Methods

### Method 1: System-wide Installation (Recommended for Individual Developers)

Install ADC globally so it's available for all your projects:

```bash
# Clone the ADC repository
git clone https://github.com/OwlDuet-Labs/agent-design-contracts.git ~/adc-framework
cd ~/adc-framework

# Install with all AI providers
pip install -e ".[all]"

# Or install with specific providers
pip install -e ".[anthropic]"  # For Claude
pip install -e ".[openai]"      # For GPT
pip install -e ".[gemini]"      # For Gemini

# Set up API keys
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

After installation, the `adc` command is available system-wide:

```bash
cd ~/your-project
adc generate --contracts ./contracts
adc audit --contracts ./contracts --src-dir ./src
```

### Method 2: IDE Integration with Symbolic Links

For AI-powered IDEs (Claude Code, Cursor, etc.) to access ADC roles and schemas:

```bash
cd ~/your-project

# Create symbolic link to ADC framework
ln -s ~/adc-framework ./adc

# This provides IDE visibility into:
# - adc/roles/*.md (for using @role.md patterns)
# - adc/adc-schema.md (for schema reference)
# - adc/contracts/* (for examples)
```

Now you can use ADC roles in your IDE:
```
@contract_writer.md create contracts in ./contracts for user authentication
@auditor.md analyze my implementation in ./src
@code_generator.md implement the contracts in ./contracts
```

### Method 3: Git Submodule (For Team Projects)

Include ADC as part of your project repository:

```bash
cd ~/your-project

# Add ADC as a submodule
git submodule add https://github.com/OwlDuet-Labs/agent-design-contracts.git adc
git submodule init
git submodule update

# Install ADC from the submodule
pip install -e ./adc[all]

# Commit the submodule reference
git add .gitmodules adc
git commit -m "Add ADC framework as submodule"
```

Team members can then clone with:
```bash
git clone --recurse-submodules your-project-repo
cd your-project
pip install -e ./adc[all]
```

### Method 4: Minimal Setup (Contracts Only)

If you only need the contract workflow without the CLI tool:

```bash
cd ~/your-project

# Create contracts directory
mkdir -p contracts

# Copy essential files
cp ~/adc-framework/adc-schema.md ./
cp -r ~/adc-framework/roles ./

# Create your first contract
cat > contracts/my-app-adc-001.md << 'EOF'
---
contract_id: "my-app-adc-001"
title: "My Application Design"
author: "Your Name"
status: "active"
version: 1.0
created_date: "2024-01-01"
---

### [Feature: Main Application] <main-app-01>
Core application functionality.

**Parity:**
- **Implementation Scope:** `src/`
- **Tests:** `tests/`
EOF
```

## Recommended Project Structure

```
your-project/
├── contracts/              # ADC contract files (*.md)
│   ├── core-adc-001.md
│   ├── auth-adc-002.md
│   └── api-adc-003.md
├── src/                    # Implementation (generated + manual)
│   ├── __init__.py
│   ├── models/            # From [DataModel] blocks
│   ├── agents/            # From [Agent] blocks
│   └── algorithms/        # From [Algorithm] blocks
├── tests/                  # Test files
│   └── test_*.py
├── adc -> ~/adc-framework  # Symlink to ADC (for IDE)
├── adc-schema.md          # Contract schema reference (optional)
├── CLAUDE.md               # Project-specific Claude instructions
└── README.md               # Project documentation
```

## Workflow for New Projects

### 1. Initial Setup

```bash
# Create project directory
mkdir my-new-project
cd my-new-project

# Initialize git
git init

# Set up ADC (using Method 1 + Method 2)
ln -s ~/adc-framework ./adc
mkdir contracts

# Create initial project structure
mkdir -p src tests docs
```

### 2. Create Initial Contracts

Using Claude Code or your IDE:
```
@contract_writer.md create contracts in ./contracts for a web API with:
- User authentication
- Database models for users and posts
- REST endpoints for CRUD operations
```

Or manually create contracts following the schema.

### 3. Generate Implementation

```bash
# Generate code from contracts
adc generate --contracts ./contracts

# Or use specific AI provider
adc generate --contracts ./contracts --agent openai
```

### 4. Audit and Refine

```bash
# Audit implementation compliance
adc audit --contracts ./contracts --src-dir ./src

# Refine contracts based on insights
adc refine contracts/core-adc-001.md

# Lint contracts for validation
adc lint contracts/
```

### 5. Iterate

Continue the ADC workflow cycle:
1. Update contracts as requirements evolve
2. Generate/update implementation
3. Audit for compliance
4. Refine and improve

## Best Practices

### For Individual Developers

1. **Use system-wide installation** (Method 1) for the `adc` CLI
2. **Create symbolic links** (Method 2) in each project for IDE integration
3. **Keep contracts in version control** to track design evolution
4. **Use ADC-IMPLEMENTS markers** in manual code to maintain traceability

### For Teams

1. **Use git submodules** (Method 3) to ensure version consistency
2. **Document API keys setup** in your project README
3. **Create project-specific CLAUDE.md** with team conventions
4. **Establish contract review process** before implementation
5. **Use CI/CD integration** to run `adc audit` automatically

### For CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: ADC Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          submodules: recursive
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install ADC
        run: pip install -e ./adc[all]
      
      - name: Run ADC Audit
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: adc audit --contracts ./contracts --src-dir ./src
```

## Troubleshooting

### Common Issues

1. **"adc: command not found"**
   - Ensure you installed with `pip install -e .` (editable mode)
   - Check your PATH includes pip's script directory

2. **"API key not found"**
   - Set environment variables: `export ANTHROPIC_API_KEY="your-key"`
   - Or use config: `adc config set anthropic_api_key your-key`

3. **IDE can't find ADC roles**
   - Create symbolic link: `ln -s ~/adc-framework ./adc`
   - Ensure the link path is correct

4. **Contract validation errors**
   - Run `adc lint contracts/` to identify issues
   - Check contract follows schema in `adc-schema.md`

## Additional Resources

- [ADC CLI Documentation](README-adc-cli.md)
- [Contract Linting Guide](CONTRACT_LINTING.md)
- [ADC Schema Reference](../adc-schema.md)
- [Example Contracts](../contracts/)
- [Contributing Guide](../CONTRIBUTING.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/OwlDuet-Labs/agent-design-contracts/issues)
- **Documentation**: [ADC Wiki](https://github.com/OwlDuet-Labs/agent-design-contracts/wiki)
- **Community**: [Discussions](https://github.com/OwlDuet-Labs/agent-design-contracts/discussions)