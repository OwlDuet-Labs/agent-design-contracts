# Contributing to Agentic Design Contracts

Thank you for your interest in contributing to the Agentic Design Contracts (ADC) project! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Contract Guidelines](#contract-guidelines)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/agent-design-contracts.git
   cd agent-design-contracts
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/OwlDuet-Labs/agent-design-contracts.git
   ```

## How to Contribute

### Reporting Issues

- Check existing issues to avoid duplicates
- Use issue templates when available
- Provide clear descriptions and steps to reproduce
- Include relevant system information

### Suggesting Features

- Open an issue with the "enhancement" label
- Describe the use case and benefits
- Consider how it fits with ADC methodology

### Contributing Code

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Write/update tests** for your changes

4. **Update documentation** as needed

5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add new provider integration"
   ```

## Development Setup

### Prerequisites

- Python 3.9+
- pip package manager
- git

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[all]"
pip install pytest pytest-cov black isort mypy

# Set up pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### API Keys

For testing AI providers:
```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

## Coding Standards

### Python Style

We follow PEP 8 with these specifics:

- **Line length**: 88 characters (Black default)
- **Imports**: Sorted with isort
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all public APIs

### Code Principles

- **No Optional types**: Use functional patterns instead
- **Fail-fast principle**: No fallback values that mask failures
- **Explicit errors**: Raise exceptions for unmet requirements
- **ADC-IMPLEMENTS markers**: Link code to contract blocks

Example:
```python
# ADC-IMPLEMENTS: <contract-block-id>
@dataclass(frozen=True)
class MyClass:
    """Brief description.
    
    Args:
        param: Description of parameter.
        
    Returns:
        Description of return value.
    """
    param: str = "default"
    
    def method(self) -> Result:
        """Method description."""
        if not self.param:
            raise ValueError("param cannot be empty")
        return Result.success()
```

### Formatting

Run these before committing:
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type check
mypy src/

# Lint
pylint src/
```

## Testing Guidelines

### Test Structure

- Place tests in `tests/` directory
- Mirror source structure: `src/adc_cli/providers.py` → `tests/test_providers.py`
- Use descriptive test names: `test_provider_initialize_with_invalid_key`

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adc_cli --cov-report=html

# Run specific test file
pytest tests/test_providers.py -v

# Run tests matching pattern
pytest -k "test_provider"
```

### Writing Tests

- Test both success and failure cases
- Mock external API calls
- Use fixtures for common setup
- Aim for >80% code coverage

Example:
```python
def test_provider_initialization():
    """Test that provider initializes correctly."""
    provider = AIProvider(name="test")
    assert provider.name == "test"
    assert not provider.is_initialized
    
def test_provider_initialization_failure():
    """Test provider initialization with missing API key."""
    provider = AIProvider()
    result = provider.initialize()
    assert not result.success
    assert "API key" in result.error_details
```

## Submitting Changes

### Branch Protection Rules

The `main` branch is protected. **Never commit directly to main.** All changes must go through pull requests with:

- Required status checks passing (CI/Check workflow)
- Code review approval
- Signed commits (GPG verification)

### Required Workflow

**Always follow this workflow for any changes:**

```bash
# 1. Create a feature branch from main
git checkout main
git pull origin main
git checkout -b feat/your-feature-name

# 2. Make your changes and commit
git add <files>
git commit -m "feat: description of change"

# 3. Push the branch (never push to main directly)
git push -u origin feat/your-feature-name

# 4. Create a pull request
gh pr create --title "feat: description" --body "Description of changes"
```

### Branch Naming Conventions

- `feat/` - New features (e.g., `feat/migrate-command`)
- `fix/` - Bug fixes (e.g., `fix/provider-error`)
- `docs/` - Documentation (e.g., `docs/api-guide`)
- `refactor/` - Code refactoring
- `test/` - Test additions/changes
- `chore/` - Maintenance tasks

### For AI Agents (Claude Code, etc.)

When using AI coding assistants:

1. **Always create a branch first** - Never commit to main
2. **Use `gh pr create`** - Create PRs via CLI, not direct pushes
3. **Wait for CI** - Ensure status checks pass before merging
4. **Include co-author** - Add `Co-Authored-By:` in commits

Example workflow for AI agents:
```bash
# Create branch
git checkout -b feat/new-feature

# Make changes...

# Commit with co-author
git commit -m "feat: add new feature

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push branch and create PR
git push -u origin feat/new-feature
gh pr create --title "feat: add new feature" --body "Description..."
```

### Pull Request Process

1. **Update your fork**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**:
   - Use descriptive title
   - Reference related issues
   - Describe changes and rationale
   - Include test results

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### Commit Message Format

We use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## Contract Guidelines

When contributing ADC contracts:

### Contract Structure

1. **Proper frontmatter** with all required fields
2. **Unique IDs** for all design blocks
3. **Parity sections** for implementable blocks
4. **Clear specifications** without ambiguity

### Contract Organization

- Maximum 8 contracts per directory
- Use numbering: `xxx-001` for overview, `xxx-002+` for components
- Group related contracts together
- Maintain balanced hierarchy

### Contract Quality

- Complete all required sections
- Use consistent terminology
- Include validation criteria
- Specify error handling
- Document performance requirements

Example contract block:
```markdown
### [DataModel: UserProfile] <user-profile-01>
Represents a user's profile information.

- `id: str` - Unique identifier (UUID format)
- `username: str` - Display name (3-50 chars, alphanumeric + underscore)
- `email: str` - Valid email address
- `created_at: datetime` - Account creation timestamp
- `metadata: dict` - Additional user metadata

**Validation:**
- Username must be unique across system
- Email must be verified before activation
- Metadata size limit: 10KB

**Parity:**
- **Implementation Scope:** `src/models/user.py`
- **Tests:** `tests/test_user_model.py`
```

## Questions?

- Open an issue for questions
- Join discussions in existing issues/PRs
- Check the [documentation](docs/)

Thank you for contributing to ADC!
