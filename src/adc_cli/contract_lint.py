#!/usr/bin/env python3
"""
Contract Lint - Automatically lint and fix formatting issues in ADC files
Based on the contract-lint.md macro specification
"""

import os
import re
import glob
import shutil
import argparse
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class ContractLinter:
    """Lints and fixes formatting issues in Agent Design Contract files"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize linter with configuration"""
        self.config = config or self._load_default_config()
        self.professional_colors = {
            'primary': '#1a1a1a',      # Black
            'secondary': '#d4af37',     # Gold
            'accent': '#4a4a4a',       # Dark Grey
            'background': '#f8f8f8',   # Light Grey
            'text': '#ffffff'          # White text
        }
    
    def _load_default_config(self) -> Dict:
        """Load configuration from ~/.adcconfig.yaml or use defaults"""
        config_path = os.path.expanduser('~/.adcconfig.yaml')
        default_config = {
            'auto_fix': True,
            'backup_originals': True,
            'check_patterns': ["**/*adc*.qmd", "**/contracts/**/*.qmd"],
            'exclude_patterns': ["**/node_modules/**", "**/trash/**", "**/venv/**"],
            'dry_run': False
        }
        
        try:
            with open(config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config and 'lint' in loaded_config:
                    return {**default_config, **loaded_config['lint']}
        except FileNotFoundError:
            pass
        
        return default_config
    
    def fix_list_indentation(self, content: str) -> str:
        """
        Standardize all list items to use '-   ' (dash + 3 spaces) format
        ADC-IMPLEMENTS: contract-lint-list-indentation
        """
        lines = content.split('\n')
        fixed_lines = []
        in_code_block = False
        
        for line in lines:
            # Track code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                fixed_lines.append(line)
                continue
            
            # Don't modify lines inside code blocks
            if in_code_block:
                fixed_lines.append(line)
                continue
            
            # Fix bullet list indentation
            bullet_match = re.match(r'^(\s*)-\s+(.*)$', line)
            if bullet_match:
                leading_spaces = len(bullet_match.group(1))
                content_part = bullet_match.group(2)
                # Round to nearest 4-space indent level
                indent_level = (leading_spaces + 2) // 4
                base_indent = '    ' * indent_level
                fixed_line = f"{base_indent}-   {content_part}"
                fixed_lines.append(fixed_line)
                continue
            
            # Fix numbered list indentation
            number_match = re.match(r'^(\s*)(\d+\.)\s*(.*)$', line)
            if number_match:
                indent = number_match.group(1)
                number = number_match.group(2)
                content_part = number_match.group(3)
                # Standard format: preserve indent + number + 2 spaces
                fixed_line = f"{indent}{number}  {content_part}"
                fixed_lines.append(fixed_line)
                continue
            
            # Fix asterisk lists to dash lists
            asterisk_match = re.match(r'^(\s*)\*\s+(.*)$', line)
            if asterisk_match:
                leading_spaces = len(asterisk_match.group(1))
                content_part = asterisk_match.group(2)
                indent_level = (leading_spaces + 2) // 4
                base_indent = '    ' * indent_level
                fixed_line = f"{base_indent}-   {content_part}"
                fixed_lines.append(fixed_line)
                continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def fix_list_spacing(self, content: str) -> str:
        """
        Ensure proper newlines before and after all lists
        ADC-IMPLEMENTS: contract-lint-list-spacing
        """
        lines = content.split('\n')
        fixed_lines = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            # Track code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                fixed_lines.append(line)
                continue
            
            if in_code_block:
                fixed_lines.append(line)
                continue
            
            # Check if current line starts a list
            is_list_start = re.match(r'^(\s*)([-*]|\d+\.)\s+', line)
            
            if is_list_start:
                # Check previous line
                if i > 0:
                    prev_line = lines[i-1]
                    prev_is_list = re.match(r'^(\s*)([-*]|\d+\.)\s+', prev_line)
                    
                    # Add newline before list if previous line is not empty and not a list
                    if prev_line.strip() != '' and not prev_is_list:
                        if len(fixed_lines) > 0 and fixed_lines[-1].strip() != '':
                            fixed_lines.append('')
            
            fixed_lines.append(line)
            
            # Check if this is the last item in a list
            if is_list_start and i < len(lines) - 1:
                next_line = lines[i+1]
                is_next_list = re.match(r'^(\s*)([-*]|\d+\.)\s+', next_line)
                
                # If next line is not a list item and not empty, add spacing
                if not is_next_list and next_line.strip() != '' and not next_line.strip().startswith('#'):
                    # Check if we need to add a blank line after this list
                    if i < len(lines) - 2:
                        fixed_lines.append('')
        
        return '\n'.join(fixed_lines)
    
    def fix_section_headers(self, content: str) -> str:
        """
        Ensure section headers like **Capabilities**, **Parity** have proper colon format
        ADC-IMPLEMENTS: contract-lint-header-format
        """
        lines = content.split('\n')
        fixed_lines = []
        in_code_block = False
        
        # Common section headers that should have colons
        header_keywords = [
            'Capabilities', 'Parity', 'Requirements', 'Dependencies',
            'Inputs', 'Outputs', 'Configuration', 'Example', 'Examples',
            'Usage', 'Notes', 'Warning', 'Important', 'Critical',
            'Implementation', 'Testing', 'Validation', 'Integration'
        ]
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                fixed_lines.append(line)
                continue
            
            if in_code_block:
                fixed_lines.append(line)
                continue
            
            # Pattern: **Word(s)** that should end with colon
            match = re.match(r'^\*\*([A-Z][a-zA-Z\s]+)\*\*\s*$', line)
            if match:
                header_text = match.group(1).strip()
                # Check if it's a known header that should have a colon
                if any(header_text.startswith(kw) for kw in header_keywords):
                    fixed_line = f"**{header_text}**:"
                    fixed_lines.append(fixed_line)
                    continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def fix_mermaid_nodes(self, content: str) -> str:
        """
        Fix common Mermaid node label issues and add Quarto best practices
        ADC-IMPLEMENTS: contract-lint-mermaid-nodes
        """
        lines = content.split('\n')
        fixed_lines = []
        in_mermaid = False
        mermaid_content = []
        
        for i, line in enumerate(lines):
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
                # Process collected mermaid content
                for mermaid_line in mermaid_content:
                    fixed_lines.append(self._fix_mermaid_line(mermaid_line))
                mermaid_content = []
                fixed_lines.extend([
                    '```',
                    '',
                    ':::'
                ])
                continue
            
            if in_mermaid:
                mermaid_content.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_mermaid_line(self, line: str) -> str:
        """Fix individual Mermaid diagram line"""
        if line.strip().startswith('%%'):
            return line
        
        # Remove problematic parentheses from labels
        line = re.sub(r'\[([^[\]]*)\(([^)]*)\)([^[\]]*)\]', 
                     r'[\1\2\3]', line)
        
        # Ensure all node labels are quoted (but don't double-quote)
        line = re.sub(r'\[([^"[\]][^[\]]*[^"[\]])\]', r'["\1"]', line)
        
        # Fix ampersands
        line = line.replace(' & ', ' and ')
        
        # Fix edge labels - use proper syntax
        line = re.sub(r'--\s*([^-]+)\s*-->', r'-->|"\1"|', line)
        
        return line
    
    def apply_professional_color_scheme(self, content: str) -> str:
        """
        Apply black, gold, and grey color scheme to Mermaid diagrams
        ADC-IMPLEMENTS: contract-lint-mermaid-colors
        """
        lines = content.split('\n')
        fixed_lines = []
        in_mermaid = False
        mermaid_start_index = -1
        
        for i, line in enumerate(lines):
            if '```{mermaid}' in line:
                in_mermaid = True
                mermaid_start_index = len(fixed_lines)
            elif line.strip() == '```' and in_mermaid:
                in_mermaid = False
                # Add styling before the closing ```
                styling = [
                    '',
                    '    %% Professional styling',
                    f'    classDef primaryNode fill:{self.professional_colors["primary"]},stroke:{self.professional_colors["secondary"]},stroke-width:3px,color:{self.professional_colors["text"]}',
                    f'    classDef secondaryNode fill:{self.professional_colors["secondary"]},stroke:{self.professional_colors["primary"]},stroke-width:2px,color:{self.professional_colors["primary"]}',
                    f'    classDef accentNode fill:{self.professional_colors["accent"]},stroke:{self.professional_colors["secondary"]},stroke-width:2px,color:{self.professional_colors["text"]}',
                    ''
                ]
                fixed_lines.extend(styling)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def add_page_break_control(self, content: str) -> str:
        """
        Add appropriate page break controls for better PDF formatting
        ADC-IMPLEMENTS: contract-lint-page-breaks
        """
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Add page break before major sections (## followed by number)
            if re.match(r'^## \d+\.', line):
                if i > 0:  # Don't add page break before first section
                    fixed_lines.extend(['', '\\newpage', ''])
            
            # Add keep-together for Mermaid diagrams
            if '```{mermaid}' in line:
                fixed_lines.append('\\begin{samepage}')
                fixed_lines.append(line)
                continue
            elif line.strip() == '```' and i > 0:
                # Check if this closes a Mermaid block
                check_range = max(0, i-20)
                recent_lines = '\n'.join(lines[check_range:i])
                if '```{mermaid}' in recent_lines:
                    fixed_lines.append(line)
                    fixed_lines.append('\\end{samepage}')
                    continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def improve_table_formatting(self, content: str) -> str:
        """
        Add proper table formatting for better rendering
        ADC-IMPLEMENTS: contract-lint-tables
        """
        lines = content.split('\n')
        fixed_lines = []
        in_table = False
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                fixed_lines.append(line)
                continue
            
            if in_code_block:
                fixed_lines.append(line)
                continue
            
            # Detect table headers
            if '|' in line and not in_table:
                # Check if it's really a table (has separator line)
                if len(fixed_lines) > 0 or '---' in line:
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
        
        # Close table if still open at end
        if in_table:
            fixed_lines.extend([
                '',
                ':::',
                ''
            ])
        
        return '\n'.join(fixed_lines)
    
    def lint_contract_file(self, file_path: str) -> Dict:
        """
        Lint a single contract file and return results
        ADC-IMPLEMENTS: contract-lint-main
        """
        results = {
            'file': file_path,
            'fixes_applied': [],
            'warnings': [],
            'errors': [],
            'file_updated': False
        }
        
        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Create backup if enabled
            if self.config.get('backup_originals', True) and not self.config.get('dry_run', False):
                backup_path = f"{file_path}.backup"
                shutil.copy2(file_path, backup_path)
                results['backup_created'] = backup_path
            
            # Apply fixes in order
            content = original_content
            
            # 1. Fix Mermaid diagrams first (before other formatting)
            old_content = content
            content = self.fix_mermaid_nodes(content)
            if content != old_content:
                results['fixes_applied'].append('mermaid_syntax')
            
            # 2. Apply professional color scheme to Mermaid
            old_content = content
            content = self.apply_professional_color_scheme(content)
            if content != old_content:
                results['fixes_applied'].append('mermaid_colors')
            
            # 3. Add Quarto page break controls
            old_content = content
            content = self.add_page_break_control(content)
            if content != old_content:
                results['fixes_applied'].append('page_breaks')
            
            # 4. Improve table formatting
            old_content = content
            content = self.improve_table_formatting(content)
            if content != old_content:
                results['fixes_applied'].append('table_formatting')
            
            # 5. Fix section headers
            old_content = content
            content = self.fix_section_headers(content)
            if content != old_content:
                results['fixes_applied'].append('section_headers')
            
            # 6. Fix list indentation
            old_content = content
            content = self.fix_list_indentation(content)
            if content != old_content:
                results['fixes_applied'].append('list_indentation')
            
            # 7. Fix list spacing
            old_content = content
            content = self.fix_list_spacing(content)
            if content != old_content:
                results['fixes_applied'].append('list_spacing')
            
            # Validate the result
            validation_issues = self._validate_content(content)
            results['warnings'].extend(validation_issues)
            
            # Write fixed content if changes were made
            if content != original_content:
                if self.config.get('auto_fix', True) and not self.config.get('dry_run', False):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    results['file_updated'] = True
                else:
                    results['preview'] = content[:500] + '...' if len(content) > 500 else content
            
        except Exception as e:
            results['errors'].append(f"Error processing file: {str(e)}")
        
        return results
    
    def _validate_content(self, content: str) -> List[str]:
        """Validate content for remaining issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for very long lines
        for i, line in enumerate(lines):
            if len(line) > 120 and not line.strip().startswith('http'):
                issues.append(f"Line {i+1}: Very long line ({len(line)} chars)")
        
        # Check for nested lists > 3 levels
        max_indent = 0
        for line in lines:
            if re.match(r'^(\s*)([-*]|\d+\.)\s+', line):
                indent = len(line) - len(line.lstrip())
                level = indent // 4
                if level > max_indent:
                    max_indent = level
        
        if max_indent > 3:
            issues.append(f"Very deep nesting detected ({max_indent} levels)")
        
        # Check for complex Mermaid diagrams
        if content.count('```{mermaid}') > 0:
            mermaid_blocks = re.findall(r'```{mermaid}(.*?)```', content, re.DOTALL)
            for block in mermaid_blocks:
                node_count = block.count('[')
                if node_count > 20:
                    issues.append(f"Complex Mermaid diagram with {node_count} nodes - consider splitting")
        
        return issues
    
    def run_contract_lint(self, base_dir: Optional[str] = None) -> Dict:
        """
        Run contract linting on all ADC files
        """
        if base_dir is None:
            base_dir = os.getcwd()
        
        # Find all contract files
        contract_files = []
        for pattern in self.config.get('check_patterns', []):
            files = glob.glob(os.path.join(base_dir, pattern), recursive=True)
            contract_files.extend(files)
        
        # Remove excluded files
        for exclude_pattern in self.config.get('exclude_patterns', []):
            exclude_files = set(glob.glob(os.path.join(base_dir, exclude_pattern), recursive=True))
            contract_files = [f for f in contract_files if f not in exclude_files]
        
        # Remove duplicates
        contract_files = list(set(contract_files))
        
        # Process each file
        results = {
            'total_files': len(contract_files),
            'files_processed': 0,
            'files_updated': 0,
            'total_fixes': 0,
            'file_results': []
        }
        
        for file_path in sorted(contract_files):
            if self.config.get('verbose', False):
                print(f"Processing: {file_path}")
            
            file_result = self.lint_contract_file(file_path)
            results['file_results'].append(file_result)
            results['files_processed'] += 1
            
            if file_result.get('file_updated', False):
                results['files_updated'] += 1
            
            results['total_fixes'] += len(file_result.get('fixes_applied', []))
        
        return results


def main():
    """Command line interface for contract linting"""
    parser = argparse.ArgumentParser(
        description='Lint and fix formatting issues in Agent Design Contract files'
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to directory or file to lint (default: current directory)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be fixed without applying changes'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup files'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file (default: ~/.adcconfig.yaml)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f).get('lint', {})
    
    # Apply command line overrides
    if args.dry_run:
        config['dry_run'] = True
    if args.no_backup:
        config['backup_originals'] = False
    if args.verbose:
        config['verbose'] = True
    
    # Create linter and run
    linter = ContractLinter(config)
    
    # Check if path is a file or directory
    if os.path.isfile(args.path):
        # Lint single file
        results = linter.lint_contract_file(args.path)
        results = {
            'total_files': 1,
            'files_processed': 1,
            'files_updated': 1 if results['file_updated'] else 0,
            'total_fixes': len(results['fixes_applied']),
            'file_results': [results]
        }
    else:
        # Lint directory
        results = linter.run_contract_lint(args.path)
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\nContract Linting Report")
        print(f"=" * 50)
        print(f"Files processed: {results['files_processed']}")
        print(f"Files updated: {results['files_updated']}")
        print(f"Total fixes applied: {results['total_fixes']}")
        
        if args.dry_run:
            print("\n[DRY RUN] No files were actually modified")
        
        if results['file_results']:
            print(f"\nDetailed Results:")
            print(f"-" * 50)
            
            for file_result in results['file_results']:
                if file_result['fixes_applied'] or file_result['warnings'] or file_result['errors']:
                    print(f"\n{file_result['file']}:")
                    
                    if file_result['fixes_applied']:
                        print(f"  Fixes applied: {', '.join(file_result['fixes_applied'])}")
                    
                    if file_result['warnings']:
                        print(f"  Warnings:")
                        for warning in file_result['warnings']:
                            print(f"    - {warning}")
                    
                    if file_result['errors']:
                        print(f"  Errors:")
                        for error in file_result['errors']:
                            print(f"    - {error}")
                    
                    if 'backup_created' in file_result:
                        print(f"  Backup: {file_result['backup_created']}")
        
        print("\nLinting complete!")


if __name__ == '__main__':
    main()
