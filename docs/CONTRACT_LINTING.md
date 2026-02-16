# Contract Linting Guide

## Overview

The ADC Contract Linting tool automatically fixes formatting issues in Agent Design Contract (ADC) files to ensure consistent rendering in Quarto and other Markdown processors. It implements the specifications from the `contract-lint.md` macro.

## Installation

The linting functionality is integrated into the ADC CLI tool. To use it, ensure you have the ADC CLI installed:

```bash
pip install -e agent-design-contracts/
```

## Usage

### Command Line Interface

The linter is available through the `adc lint` command:

```bash
# Lint all contracts in current directory
adc lint

# Lint specific file
adc lint path/to/contract.md

# Lint specific directory
adc lint contracts/

# Dry run - show what would be fixed without applying
adc lint --dry-run

# Don't create backup files
adc lint --no-backup

# Output results as JSON
adc lint --json

# Verbose output
adc lint -v
```

### Python API

You can also use the linter programmatically:

```python
from adc_cli.contract_lint import ContractLinter

# Configure linter
config = {
    'auto_fix': True,
    'backup_originals': True,
    'verbose': True
}

linter = ContractLinter(config)

# Lint a single file
results = linter.lint_contract_file('path/to/contract.md')

# Lint a directory
results = linter.run_contract_lint('/path/to/contracts')
```

## Features

### 1. List Formatting Fixes

-   Standardizes all list items to use `-   ` (dash + 3 spaces) format
-   Converts asterisk lists to dash lists
-   Fixes inconsistent indentation (2-space, 4-space, tabs)
-   Adds proper newlines before and after lists

**Before:**
```markdown
* Item 1
  - Sub-item
    * Sub-sub-item
```

**After:**
```markdown
-   Item 1
    -   Sub-item
        -   Sub-sub-item
```

### 2. Section Header Formatting

-   Ensures section headers like `**Capabilities**` have proper colons
-   Recognizes common ADC section headers

**Before:**
```markdown
**Capabilities**
**Requirements**
```

**After:**
```markdown
**Capabilities**:
**Requirements**:
```

### 3. Mermaid Diagram Enhancements

-   Adds Quarto-specific formatting for proper rendering
-   Fixes common syntax issues (parentheses, ampersands)
-   Applies professional color scheme (black, gold, grey)
-   Ensures proper figure sizing and centering

**Before:**
```markdown
```mermaid
A[Node (with parens)] --> B[Process & Analyze]
```

**After:**
```markdown
::: {.column-page}

```{mermaid}
%%| fig-width: 12
%%| fig-height: 10
%%| fig-align: center

A["Node with parens"] --> B["Process and Analyze"]

    %% Professional styling
    classDef primaryNode fill:#1a1a1a,stroke:#d4af37,stroke-width:3px,color:#ffffff
    classDef secondaryNode fill:#d4af37,stroke:#1a1a1a,stroke-width:2px,color:#1a1a1a
    classDef accentNode fill:#4a4a4a,stroke:#d4af37,stroke-width:2px,color:#ffffff

```

:::
```

### 4. Quarto Diagram Rendering Fixes

-   **Prevents diagram cutoff**: Automatically optimizes figure dimensions and layout
-   **Responsive sizing**: Adds proper `out-width` and margin buffers
-   **Layout optimization**: Converts horizontal layouts to vertical for better fit
-   **YAML header optimization**: Ensures proper Mermaid theme and geometry settings
-   **Complex diagram simplification**: Consolidates subgraphs into compact single nodes

**Before (Problematic):**
```markdown
```{mermaid}
%%| fig-width: 14
%%| fig-height: 12

graph TD
    subgraph ContextStack["🧠 Context Stack"]
        Static[Layer 1: Static Context<br/>• ADC Contracts]
        Dynamic[Layer 2: Dynamic Context<br/>• Git History]
    end
```

**After (Optimized):**
```markdown
```{mermaid}
%%| fig-width: 7
%%| fig-height: 10
%%| out-width: "85%"
%%| fig-align: center

graph TB
    Context[Context Stack<br/>Static + Dynamic + In-Flight] -.-> Simulate
```

### 5. PDF Rendering Optimizations

-   Adds page breaks before major sections
-   Wraps diagrams in `\begin{samepage}...\end{samepage}` to prevent splitting
-   Adds responsive table formatting
-   Ensures proper spacing throughout document

### 6. Code Block Preservation

-   Code blocks are never modified by formatting rules
-   Preserves exact indentation and content within code fences

## Configuration

The linter reads configuration from `~/.adcconfig.yaml`:

```yaml
lint:
  auto_fix: true              # Automatically apply fixes
  backup_originals: true      # Create .backup files before modifying
  check_patterns:             # File patterns to lint
    - "**/*adc*.md"
    - "**/contracts/**/*.md"
  exclude_patterns:           # Patterns to exclude
    - "**/node_modules/**"
    - "**/trash/**"
    - "**/venv/**"
```

## Validation Rules

### Critical Issues (Automatically Fixed)
-   Missing colons in section headers
-   Inconsistent list indentation
-   Mermaid syntax errors
-   Oversized diagrams that cause cutoff
-   Incorrect diagram layout direction (horizontal → vertical)
-   Missing responsive sizing directives
-   Invalid Mermaid theme values in YAML headers
-   Complex subgraphs that exceed page boundaries

### Warnings (Manual Review Suggested)
-   Very long lines (>120 characters)
-   Deep nesting (>3 levels)
-   Complex Mermaid diagrams (>20 nodes)

## Diagram Rendering Solutions

### Common Diagram Issues and Fixes

#### Issue 1: Diagram Cut Off on Right Side
**Problem**: Mermaid diagrams extend beyond page margins and get chopped off

**Solution**: The linter automatically:
1. Changes layout from `graph TD` to `graph TB` (vertical)
2. Reduces figure width from 12+ to 7
3. Adds responsive sizing with `out-width: "85%"`
4. Optimizes YAML header with proper geometry

#### Issue 2: Quarto Validation Errors
**Problem**: Invalid Mermaid theme values cause rendering failures

**Solution**: The linter automatically:
1. Changes `theme: base` to `theme: default`
2. Removes invalid `%%{init: ...}%%` directives
3. Adds proper YAML configuration for both HTML and PDF

#### Issue 3: Complex Diagrams Don't Fit
**Problem**: Diagrams with many subgraphs and nodes exceed page boundaries

**Solution**: The linter automatically:
1. Consolidates subgraphs into single compact nodes
2. Uses line breaks (`<br/>`) for multi-line labels
3. Simplifies complex relationships while preserving meaning

### Before/After Examples

#### Example: GitHub ADC Integration Diagram

**Before (Problematic - Gets Cut Off):**
```yaml
---
format:
  pdf:
    fig-width: 14
    fig-height: 12
mermaid:
  theme: base  # Invalid theme
---

```{mermaid}
%%{init: {'theme':'base'}}%%  # Invalid directive
graph TD
    subgraph ContextStack["🧠 Context Stack"]
        Static[Layer 1: Static Context<br/>• ADC Contracts<br/>• Customer Enabling]
        Dynamic[Layer 2: Dynamic Context<br/>• Git History<br/>• Cached Results]
    end
```

**After (Fixed - Renders Completely):**
```yaml
---
format:
  html:
    mermaid:
      theme: default
    fig-width: 12
    fig-height: 10
  pdf:
    fig-width: 7
    fig-height: 10
    fig-align: center
    geometry: "left=0.75in,right=0.75in,top=1in,bottom=1in"
mermaid:
  theme: default
---

```{mermaid}
%%| fig-width: 7
%%| fig-height: 10
%%| out-width: "85%"
%%| fig-align: center

graph TB
    Context[Context Stack<br/>Static + Dynamic + In-Flight] -.-> Simulate
```

## Examples

### Example 1: Linting Audio Pipeline Documentation

```bash
# Navigate to owltalk directory
cd owltalk

# Run the specialized audio docs linter
python lint_audio_docs.py

# Or use the ADC CLI
adc lint docs/audio-pipeline-best-practices.md
```

### Example 2: Testing the Linter

```bash
# Run the test script to see the linter in action
python agent-design-contracts/examples/test_lint.py
```

### Example 3: Batch Linting All Contracts

```bash
# From project root
adc lint --verbose

# Review changes with dry run first
adc lint --dry-run | less
```

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/lint.yml
name: Lint ADC Contracts

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install ADC CLI
        run: pip install -e agent-design-contracts/
      - name: Lint Contracts
        run: adc lint --dry-run
```

## Troubleshooting

### Common Issues

1. **File not found errors**: Ensure you're running from the correct directory
2. **Permission errors**: Check file permissions and ownership
3. **Backup files accumulating**: Use `--no-backup` or clean up `.backup` files periodically

### Debug Mode

For detailed debugging information:

```bash
adc lint -v --dry-run path/to/problematic-file.md
```

## Best Practices

1. **Always review changes**: Run with `--dry-run` first to preview changes
2. **Keep backups**: Leave backup creation enabled for important files
3. **Regular linting**: Run linter before committing contract changes
4. **Custom patterns**: Update `~/.adcconfig.yaml` for project-specific patterns

## Contributing

To extend the linter with new rules:

1. Add the fix function to `ContractLinter` class
2. Call it in the appropriate order in `lint_contract_file()`
3. Add tests in `test_contract_lint.py`
4. Document the new rule in this guide

## Version History

-   v1.0: Initial implementation based on contract-lint.md macro
-   Supports all formatting fixes specified in the macro
-   Integrated with ADC CLI as `adc lint` command
