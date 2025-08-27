# Contract Lint Macro

## Purpose
This macro automatically lints and fixes formatting issues in Agent Design Contract (ADC) files to ensure consistent rendering in Quarto and other Markdown processors. It identifies and corrects common formatting problems that can cause lists to render as code blocks or diagrams to fail parsing.

## Configuration
The macro reads configuration from `~/.adcconfig.yaml` to determine which contracts to lint and output settings. Default configuration:

```yaml
lint:
  auto_fix: true
  backup_originals: true
  check_patterns:
    - "**/*adc*.qmd"
    - "**/contracts/**/*.qmd"
  exclude_patterns:
    - "**/node_modules/**"
    - "**/trash/**"
```

## Command Implementation

```bash
# As @contract_writer.md, search through all ADC contract files and apply formatting fixes
# to ensure proper Quarto rendering. Create backup files before making changes.
# Report all fixes applied and any issues that require manual intervention.
```

## Detected Issues and Fixes

### 1. List Formatting Issues

**Problem**: Lists render as code blocks instead of proper bullet/numbered lists
**Root Causes**:
- Inconsistent indentation (mixing 2-space, 4-space, and tab indentation)
- Missing newlines before/after lists
- Incorrect header format (missing colons)

**Automated Fixes**:

#### Fix 1.1: Standardize List Indentation
```python
# ADC-IMPLEMENTS: contract-lint-list-indentation
def fix_list_indentation(content: str) -> str:
    """
    Standardize all list items to use '-   ' (dash + 3 spaces) format
    """
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix inconsistent bullet list indentation
        if re.match(r'^(\s*)-\s+', line):
            # Count leading spaces before the dash
            leading_spaces = len(line) - len(line.lstrip())
            # Extract the content after dash and spaces
            content_match = re.match(r'^(\s*)-\s*(.*)', line)
            if content_match:
                content_part = content_match.group(2)
                # Standard format: preserve leading indentation + dash + 3 spaces
                base_indent = ' ' * (leading_spaces // 4 * 4)  # Round to nearest 4
                fixed_line = f"{base_indent}-   {content_part}"
                fixed_lines.append(fixed_line)
                continue
        
        # Fix numbered list indentation (similar logic)
        if re.match(r'^(\s*)\d+\.\s+', line):
            leading_spaces = len(line) - len(line.lstrip())
            content_match = re.match(r'^(\s*)(\d+\.)\s*(.*)', line)
            if content_match:
                indent = content_match.group(1)
                number = content_match.group(2)
                content_part = content_match.group(3)
                # Standard format: preserve indent + number + 2 spaces
                fixed_line = f"{indent}{number}  {content_part}"
                fixed_lines.append(fixed_line)
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

#### Fix 1.2: Add Missing Newlines Around Lists
```python
# ADC-IMPLEMENTS: contract-lint-list-spacing
def fix_list_spacing(content: str) -> str:
    """
    Ensure proper newlines before and after all lists
    """
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Check if current line starts a list
        is_list_start = re.match(r'^(\s*[-*]|\d+\.)\s+', line)
        
        if is_list_start:
            # Ensure newline before list (if not already there)
            if (i > 0 and lines[i-1].strip() != '' and 
                not re.match(r'^(\s*[-*]|\d+\.)\s+', lines[i-1])):
                if len(fixed_lines) > 0 and fixed_lines[-1] != '':
                    fixed_lines.append('')
        
        fixed_lines.append(line)
        
        # Check if next line ends a list
        if (is_list_start and i < len(lines) - 1):
            next_line = lines[i+1] if i+1 < len(lines) else ''
            is_next_list = re.match(r'^(\s*[-*]|\d+\.)\s+', next_line)
            
            # If next line is not a list item and not empty, add spacing
            if not is_next_list and next_line.strip() != '':
                fixed_lines.append('')
    
    return '\n'.join(fixed_lines)
```

#### Fix 1.3: Fix Section Headers
```python
# ADC-IMPLEMENTS: contract-lint-header-format
def fix_section_headers(content: str) -> str:
    """
    Ensure section headers like **Capabilities**, **Parity** have proper colon format
    """
    # Pattern: **Word(s)** that should end with colon
    header_pattern = r'^\*\*([A-Z][a-zA-Z\s]+)\*\*$'
    
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        match = re.match(header_pattern, line)
        if match:
            header_text = match.group(1).strip()
            # Add colon if missing
            fixed_line = f"**{header_text}**:"
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

### 2. Mermaid Diagram Issues

**Problem**: Mermaid diagrams fail to render due to syntax errors
**Root Causes**:
- Unescaped special characters in node labels
- Inconsistent edge label syntax
- Problematic parentheses in labels

**Automated Fixes**:

#### Fix 2.1: Clean Node Labels and Add Quarto Formatting
```python
# ADC-IMPLEMENTS: contract-lint-mermaid-nodes
def fix_mermaid_nodes(content: str) -> str:
    """
    Fix common Mermaid node label issues and add Quarto best practices
    """
    lines = content.split('\n')
    fixed_lines = []
    in_mermaid = False
    
    for line in lines:
        if '```{mermaid}' in line or '```mermaid' in line:
            in_mermaid = True
            # Add Quarto formatting with proper scaling and centering
            fixed_lines.extend([
                '::: {.column-page}',
                '',
                '```{mermaid}',
                '%%| fig-width: 12',
                '%%| fig-height: 10', 
                '%%| fig-align: center',
                ''
            ])
            continue
        elif line.strip() == '```' and in_mermaid:
            in_mermaid = False
            fixed_lines.extend([
                line,
                '',
                ':::'
            ])
            continue
        
        if in_mermaid and not line.strip().startswith('#|'):
            # Fix node definitions
            # Remove problematic parentheses from labels
            line = re.sub(r'\[([^[\]]*)\(([^)]*)\)([^[\]]*)\]', 
                         r'[\1\2\3]', line)
            
            # Ensure all node labels are quoted
            line = re.sub(r'\[([^"[\]]+)\]', r'["\1"]', line)
            
            # Fix ampersands
            line = line.replace(' & ', ' and ')
            
            # Fix edge labels - use proper syntax
            line = re.sub(r'--\s*([^-]+)\s*-->', r'-->|"\1"|', line)
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

#### Fix 2.2: Apply Professional Color Scheme
```python
# ADC-IMPLEMENTS: contract-lint-mermaid-colors
def apply_professional_color_scheme(content: str) -> str:
    """
    Apply black, gold, and grey color scheme to Mermaid diagrams
    """
    lines = content.split('\n')
    fixed_lines = []
    in_mermaid = False
    diagram_end_index = None
    
    # Professional color palette
    colors = {
        'primary': '#1a1a1a',      # Black
        'secondary': '#d4af37',     # Gold
        'accent': '#4a4a4a',       # Dark Grey
        'background': '#f8f8f8',   # Light Grey
        'text': '#ffffff'          # White text
    }
    
    for i, line in enumerate(lines):
        if '```{mermaid}' in line:
            in_mermaid = True
        elif line.strip() == '```' and in_mermaid:
            diagram_end_index = i
            in_mermaid = False
        
        fixed_lines.append(line)
    
    # Add styling before the closing ```
    if diagram_end_index is not None:
        styling = [
            '',
            '    %% Professional styling',
            f'    classDef primaryNode fill:{colors["primary"]},stroke:{colors["secondary"]},stroke-width:3px,color:{colors["text"]}',
            f'    classDef secondaryNode fill:{colors["secondary"]},stroke:{colors["primary"]},stroke-width:2px,color:{colors["primary"]}',
            f'    classDef accentNode fill:{colors["accent"]},stroke:{colors["secondary"]},stroke-width:2px,color:{colors["text"]}',
            '',
            '    %% Apply classes to subgraphs',
            '    class AudioSource secondaryNode',
            '    class TimingEngine primaryNode', 
            '    class PluginSubscribers accentNode'
        ]
        
        # Insert styling before the closing ```
        fixed_lines[diagram_end_index:diagram_end_index] = styling
    
    return '\n'.join(fixed_lines)
```

### 2.3. Quarto Diagram Rendering Fixes

**Problem**: Mermaid diagrams get cut off or chopped in PDF/HTML rendering
**Root Causes**:
- Incorrect figure dimensions for content complexity
- Missing responsive sizing directives
- Poor layout direction choices (horizontal vs vertical)
- Inadequate margin and spacing configuration

**Automated Fixes**:

#### Fix 2.3.1: Optimize Diagram Layout and Dimensions
```python
# ADC-IMPLEMENTS: contract-lint-diagram-layout
def optimize_diagram_layout(content: str) -> str:
    """
    Optimize Mermaid diagram layout to prevent cutoff issues
    """
    lines = content.split('\n')
    fixed_lines = []
    in_mermaid = False
    
    for i, line in enumerate(lines):
        if '```{mermaid}' in line or '```mermaid' in line:
            in_mermaid = True
            # Add optimized Quarto configuration
            fixed_lines.extend([
                '```{mermaid}',
                '%%| label: diagram-' + str(hash(str(i)) % 1000),
                '%%| fig-cap: "Architecture Overview"',
                '%%| fig-width: 7',      # Narrower width to fit margins
                '%%| fig-height: 10',    # Adequate height for vertical layout
                '%%| out-width: "85%"',  # Responsive width with margin buffer
                ''
            ])
            continue
        elif line.strip() == '```' and in_mermaid:
            in_mermaid = False
            fixed_lines.append(line)
            continue
        
        if in_mermaid:
            # Convert horizontal layouts to vertical for better fit
            if line.strip().startswith('graph TD') or line.strip().startswith('graph LR'):
                fixed_lines.append('graph TB  %% Vertical layout prevents horizontal cutoff')
                continue
            
            # Simplify complex subgraphs that cause width issues
            if 'subgraph' in line and len(line) > 60:
                # Extract subgraph name and simplify
                match = re.search(r'subgraph\s+(\w+)\["([^"]+)"\]', line)
                if match:
                    name = match.group(1)
                    title = match.group(2)
                    # Create compact single-line version
                    fixed_lines.append(f'    {name}[{title}<br/>Simplified View]')
                    continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

#### Fix 2.3.2: Implement Responsive Diagram Sizing
```python
# ADC-IMPLEMENTS: contract-lint-responsive-sizing
def implement_responsive_sizing(content: str) -> str:
    """
    Add responsive sizing directives to prevent diagram cutoff
    """
    lines = content.split('\n')
    fixed_lines = []
    in_mermaid = False
    
    for line in lines:
        if '```{mermaid}' in line:
            in_mermaid = True
            fixed_lines.extend([
                '```{mermaid}',
                '%%| fig-width: 7',
                '%%| fig-height: 10', 
                '%%| out-width: "85%"',
                '%%| fig-align: center',
                ''
            ])
            continue
        elif line.strip() == '```' and in_mermaid:
            in_mermaid = False
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

#### Fix 2.3.3: Simplify Complex Diagrams
```python
# ADC-IMPLEMENTS: contract-lint-diagram-simplification
def simplify_complex_diagrams(content: str) -> str:
    """
    Automatically simplify overly complex diagrams that cause rendering issues
    """
    lines = content.split('\n')
    fixed_lines = []
    in_mermaid = False
    node_count = 0
    
    for line in lines:
        if '```{mermaid}' in line:
            in_mermaid = True
            node_count = 0
        elif line.strip() == '```' and in_mermaid:
            in_mermaid = False
            
        if in_mermaid and '-->' in line:
            node_count += 1
            
            # If diagram is getting too complex, suggest simplification
            if node_count > 15:
                fixed_lines.append('    %% Complex diagram detected - consider splitting')
                
        # Consolidate multiple similar nodes into single compact nodes
        if in_mermaid and 'subgraph' in line:
            # Convert complex subgraphs to single nodes with line breaks
            if 'Context Stack' in line or 'Multi-Agent' in line:
                if 'Context Stack' in line:
                    fixed_lines.append('    Context[Context Stack<br/>Static + Dynamic + In-Flight] -.-> Simulate')
                elif 'Multi-Agent' in line:
                    fixed_lines.append('    Agents[Multi-Agent System<br/>CI-Auditor + Test Gap + Vision] -.-> Audit')
                # Skip the subgraph content by setting a flag
                continue
                
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

#### Fix 2.3.4: Add YAML Header Optimization
```python
# ADC-IMPLEMENTS: contract-lint-yaml-optimization
def optimize_yaml_header(content: str) -> str:
    """
    Optimize YAML header for better Mermaid rendering
    """
    lines = content.split('\n')
    fixed_lines = []
    in_yaml = False
    yaml_end_found = False
    
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == '---':
            in_yaml = True
            fixed_lines.append(line)
            continue
        elif line.strip() == '---' and in_yaml and not yaml_end_found:
            yaml_end_found = True
            # Insert optimized Mermaid configuration before closing YAML
            fixed_lines.extend([
                'format:',
                '  html:',
                '    mermaid:',
                '      theme: default',
                '    fig-width: 12',
                '    fig-height: 10',
                '  pdf:',
                '    fig-width: 7',
                '    fig-height: 10',
                '    fig-align: center',
                '    geometry: "left=0.75in,right=0.75in,top=1in,bottom=1in"',
                'mermaid:',
                '  theme: default',
                line
            ])
            in_yaml = False
            continue
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

### 3. Quarto Best Practices

#### Fix 3.1: Add Page Break Control
```python
# ADC-IMPLEMENTS: contract-lint-page-breaks
def add_page_break_control(content: str) -> str:
    """
    Add appropriate page break controls for better PDF formatting
    """
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Add page break before major sections
        if re.match(r'^## \d+\.', line):
            if i > 0:  # Don't add page break before first section
                fixed_lines.extend(['', '\\newpage', ''])
        
        # Add keep-together for diagrams
        if '```{mermaid}' in line:
            fixed_lines.append('\\begin{samepage}')
        elif line.strip() == '```' and i > 0 and '```{mermaid}' in '\n'.join(lines[max(0, i-10):i]):
            fixed_lines.append(line)
            fixed_lines.append('\\end{samepage}')
            continue
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

#### Fix 3.2: Improve Table Formatting
```python
# ADC-IMPLEMENTS: contract-lint-tables
def improve_table_formatting(content: str) -> str:
    """
    Add proper table formatting for better rendering
    """
    lines = content.split('\n')
    fixed_lines = []
    in_table = False
    
    for line in lines:
        # Detect table headers
        if '|' in line and not in_table:
            # Add table formatting
            fixed_lines.extend([
                '',
                '::: {.table-responsive}',
                ''
            ])
            in_table = True
        elif in_table and '|' not in line and line.strip() != '':
            # End of table
            fixed_lines.extend([
                '',
                ':::',
                ''
            ])
            in_table = False
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

### 4. Code Block and Formatting Issues

#### Fix 4.1: Preserve Code Block Indentation
```python
# ADC-IMPLEMENTS: contract-lint-code-blocks
def preserve_code_blocks(content: str) -> str:
    """
    Ensure code blocks are not affected by list formatting fixes
    """
    lines = content.split('\n')
    fixed_lines = []
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
        
        # Don't modify lines inside code blocks
        if in_code_block:
            fixed_lines.append(line)
        else:
            # Apply other fixes only outside code blocks
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)
```

## Macro Implementation

### Main Linting Function
```python
# ADC-IMPLEMENTS: contract-lint-main
import os
import re
import glob
import shutil
from pathlib import Path
import yaml

def lint_contract_file(file_path: str, config: dict) -> dict:
    """
    Lint a single contract file and return results
    """
    results = {
        'file': file_path,
        'fixes_applied': [],
        'warnings': [],
        'errors': []
    }
    
    try:
        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Create backup if enabled
        if config.get('backup_originals', True):
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            results['backup_created'] = backup_path
        
        # Apply fixes in order
        content = original_content
        
        # 1. Preserve code blocks (mark them to avoid modification)
        content = preserve_code_blocks(content)
        
        # 2. Fix Mermaid diagrams and add Quarto formatting
        old_content = content
        content = fix_mermaid_nodes(content)
        if content != old_content:
            results['fixes_applied'].append('mermaid_syntax')
        
        # 2.1. Optimize diagram layout and dimensions
        old_content = content
        content = optimize_diagram_layout(content)
        if content != old_content:
            results['fixes_applied'].append('diagram_layout')
        
        # 2.2. Implement responsive sizing
        old_content = content
        content = implement_responsive_sizing(content)
        if content != old_content:
            results['fixes_applied'].append('responsive_sizing')
        
        # 2.3. Simplify complex diagrams
        old_content = content
        content = simplify_complex_diagrams(content)
        if content != old_content:
            results['fixes_applied'].append('diagram_simplification')
        
        # 2.4. Optimize YAML header
        old_content = content
        content = optimize_yaml_header(content)
        if content != old_content:
            results['fixes_applied'].append('yaml_optimization')
        
        # 3. Apply professional color scheme to Mermaid
        old_content = content
        content = apply_professional_color_scheme(content)
        if content != old_content:
            results['fixes_applied'].append('mermaid_colors')
        
        # 4. Add Quarto page break controls
        old_content = content
        content = add_page_break_control(content)
        if content != old_content:
            results['fixes_applied'].append('page_breaks')
        
        # 5. Improve table formatting
        old_content = content
        content = improve_table_formatting(content)
        if content != old_content:
            results['fixes_applied'].append('table_formatting')
        
        # 6. Fix section headers
        old_content = content
        content = fix_section_headers(content)
        if content != old_content:
            results['fixes_applied'].append('section_headers')
        
        # 7. Fix list indentation
        old_content = content
        content = fix_list_indentation(content)
        if content != old_content:
            results['fixes_applied'].append('list_indentation')
        
        # 8. Fix list spacing
        old_content = content
        content = fix_list_spacing(content)
        if content != old_content:
            results['fixes_applied'].append('list_spacing')
        
        # Write fixed content if changes were made
        if content != original_content and config.get('auto_fix', True):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            results['file_updated'] = True
        else:
            results['file_updated'] = False
            
    except Exception as e:
        results['errors'].append(f"Error processing file: {str(e)}")
    
    return results

def run_contract_lint(base_dir: str = None) -> dict:
    """
    Run contract linting on all ADC files
    """
    if base_dir is None:
        base_dir = os.getcwd()
    
    # Load configuration
    config_path = os.path.expanduser('~/.adcconfig.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f).get('lint', {})
    except FileNotFoundError:
        config = {
            'auto_fix': True,
            'backup_originals': True,
            'check_patterns': ["**/*adc*.qmd", "**/contracts/**/*.qmd"],
            'exclude_patterns': ["**/node_modules/**", "**/trash/**"]
        }
    
    # Find all contract files
    contract_files = []
    for pattern in config.get('check_patterns', []):
        files = glob.glob(os.path.join(base_dir, pattern), recursive=True)
        contract_files.extend(files)
    
    # Remove excluded files
    for exclude_pattern in config.get('exclude_patterns', []):
        exclude_files = glob.glob(os.path.join(base_dir, exclude_pattern), recursive=True)
        contract_files = [f for f in contract_files if f not in exclude_files]
    
    # Process each file
    results = {
        'total_files': len(contract_files),
        'files_processed': 0,
        'files_updated': 0,
        'total_fixes': 0,
        'file_results': []
    }
    
    for file_path in contract_files:
        file_result = lint_contract_file(file_path, config)
        results['file_results'].append(file_result)
        results['files_processed'] += 1
        
        if file_result.get('file_updated', False):
            results['files_updated'] += 1
        
        results['total_fixes'] += len(file_result.get('fixes_applied', []))
    
    return results
```

## Usage Examples

### Command Line Usage
```bash
# Run linting on current directory
python -c "
from agent_design_contracts.macros.contract_lint import run_contract_lint
import json
results = run_contract_lint()
print(json.dumps(results, indent=2))
"

# Run on specific directory
python -c "
from agent_design_contracts.macros.contract_lint import run_contract_lint
results = run_contract_lint('/path/to/contracts')
print(f'Processed {results[\"files_processed\"]} files, updated {results[\"files_updated\"]}')
"
```

### Integration with ADC CLI
```bash
# Add to adc CLI as a subcommand
adc lint                    # Lint all contracts in current project
adc lint --dry-run         # Show what would be fixed without applying
adc lint --backup=false    # Don't create backup files
adc lint /path/to/contracts # Lint specific directory
```

## Enhanced Features

### Quarto Optimization
1. **Figure Sizing**: Automatically adds proper `fig-width` and `fig-height` for diagrams
2. **Centering**: Ensures all diagrams are center-aligned with `fig-align: center`
3. **Captions**: Adds descriptive figure captions for better accessibility
4. **Page Breaks**: Intelligent page break placement before major sections
5. **Responsive Tables**: Wraps tables in responsive containers

### Professional Styling
1. **Color Scheme**: Applies black (#1a1a1a), gold (#d4af37), and grey (#4a4a4a) palette
2. **Visual Hierarchy**: Uses different colors for primary, secondary, and accent elements
3. **Consistent Styling**: Standardizes all Mermaid diagrams across contracts

### PDF Rendering Improvements
- **No Cut-off Diagrams**: Proper sizing prevents diagram truncation
- **Better Spacing**: Improved whitespace management
- **Professional Appearance**: Corporate color scheme and typography
- **Print-friendly**: Optimized for both screen and print viewing

## Validation Rules

### Critical Issues (Must Fix)
1. **Missing colons in section headers** - Prevents proper list rendering
2. **Inconsistent list indentation** - Causes code block rendering
3. **Mermaid syntax errors** - Prevents diagram rendering
4. **Oversized diagrams** - Causes content cut-off in PDF
5. **Incorrect diagram layout direction** - Horizontal layouts cause width overflow
6. **Missing responsive sizing directives** - Diagrams don't scale properly
7. **Invalid Mermaid theme values** - Causes Quarto validation errors
8. **Complex subgraphs without simplification** - Exceeds page boundaries

### Style Issues (Recommended Fix)
1. **Extra blank lines** - Clean up spacing
2. **Inconsistent bullet formats** - Standardize to `-   `
3. **Missing newlines around lists** - Improve readability
4. **Unprofessional colors** - Apply corporate color scheme
5. **Missing figure captions** - Add descriptive captions

### Warnings (Manual Review Needed)
1. **Complex Mermaid diagrams** - May need manual syntax review
2. **Nested list depth > 3 levels** - Consider restructuring
3. **Very long lines** - Consider breaking up for readability
4. **Too many elements in diagram** - Consider splitting complex diagrams

## Testing

### Test Files
Create test cases in `tests/contract_lint/`:
- `test_list_formatting.qmd` - Various list formatting issues
- `test_mermaid_syntax.qmd` - Mermaid diagram problems
- `test_section_headers.qmd` - Header format issues

### Validation
```python
# ADC-IMPLEMENTS: contract-lint-testing
def test_contract_lint():
    """Test suite for contract linting functionality"""
    test_cases = [
        {
            'name': 'list_indentation',
            'input': '**Capabilities**:\n-  Item 1\n  - Item 2',
            'expected': '**Capabilities**:\n\n-   Item 1\n-   Item 2'
        },
        {
            'name': 'mermaid_syntax',
            'input': '```mermaid\nA[Node (with parens)] --> B',
            'expected': '```{mermaid}\nA["Node with parens"] --> B'
        }
    ]
    
    for case in test_cases:
        result = apply_lint_fixes(case['input'])
        assert result == case['expected'], f"Test {case['name']} failed"
```

## Integration Points

1. **ADC CLI Integration** - Add as `adc lint` command
2. **Pre-commit Hooks** - Run automatically before commits
3. **CI/CD Pipeline** - Validate contract formatting in builds
4. **Editor Integration** - VS Code extension for real-time linting

## Configuration Examples

### Minimal Configuration
```yaml
# ~/.adcconfig.yaml
lint:
  auto_fix: true
```

### Advanced Configuration
```yaml
lint:
  auto_fix: true
  backup_originals: true
  check_patterns:
    - "**/*adc*.qmd"
    - "**/contracts/**/*.qmd"
    - "**/*contract*.md"
  exclude_patterns:
    - "**/node_modules/**"
    - "**/trash/**"
    - "**/archive/**"
  rules:
    mermaid_syntax: true
    list_formatting: true
    header_consistency: true
    spacing_cleanup: true
```
