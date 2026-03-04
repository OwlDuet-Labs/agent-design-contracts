"""
ADC Migrate Command

Migrates ADC contract files from .qmd to .md extension,
and converts Quarto-specific Mermaid syntax to standard Markdown.
"""

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass
class MigrationReport:
    """Results from a migration operation."""
    files_found: int = 0
    files_renamed: int = 0
    files_skipped: int = 0
    references_updated: int = 0
    mermaid_blocks_converted: int = 0
    latex_directives_removed: int = 0
    errors: List[str] = field(default_factory=list)
    renamed_files: List[tuple] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "=== ADC QMD to MD Migration Report ===",
            f"Files found:              {self.files_found}",
            f"Files renamed:            {self.files_renamed}",
            f"Files skipped:            {self.files_skipped}",
            f"References updated:       {self.references_updated}",
            f"Mermaid blocks converted: {self.mermaid_blocks_converted}",
            f"LaTeX directives removed: {self.latex_directives_removed}",
        ]
        if self.errors:
            lines.append(f"Errors: {len(self.errors)}")
            for err in self.errors:
                lines.append(f"  - {err}")
        if self.renamed_files:
            lines.append("\nRenamed files:")
            for old, new in self.renamed_files:
                lines.append(f"  {old} -> {new}")
        return "\n".join(lines)


def find_qmd_files(directory: Path) -> List[Path]:
    """Find all .qmd files recursively in directory."""
    return sorted(directory.rglob("*.qmd"))


def rename_file(qmd_path: Path, dry_run: bool = False) -> Path:
    """Rename a .qmd file to .md extension."""
    new_path = qmd_path.with_suffix(".md")
    if not dry_run:
        qmd_path.rename(new_path)
    return new_path


def convert_quarto_mermaid(file_path: Path, dry_run: bool = False) -> int:
    """Convert Quarto-style ```{mermaid} blocks to standard ```mermaid in .md files.

    Strips Quarto-only directives (%%| lines) and ::: {.column-page} wrappers.

    Returns the number of blocks converted.
    """
    if file_path.suffix != ".md":
        return 0

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return 0

    if '```{mermaid}' not in content:
        return 0

    lines = content.split('\n')
    new_lines: List[str] = []
    converted = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Remove ::: {.column-page} wrapper before a mermaid block
        if re.match(r'^:::\s*\{\.column-page\}', line.strip()):
            # Look ahead: skip blank lines then check for ```{mermaid}
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and '```{mermaid}' in lines[j]:
                # Skip the ::: line and blanks — we'll handle the mermaid block next
                i = j
                continue
            # Not followed by mermaid, keep the line
            new_lines.append(line)
            i += 1
            continue

        # Convert ```{mermaid} to ```mermaid
        if '```{mermaid}' in line:
            new_lines.append(line.replace('```{mermaid}', '```mermaid'))
            converted += 1
            i += 1

            # Strip Quarto-only %%| directives at the top of the block
            while i < len(lines):
                stripped = lines[i].strip()
                if stripped.startswith('%%|'):
                    i += 1  # skip this directive
                    continue
                # Skip blank line that followed directives
                if stripped == '' and i + 1 < len(lines) and lines[i - 1].strip().startswith('%%|'):
                    i += 1
                    continue
                break
            continue

        # Remove closing ::: that wrapped a mermaid block
        if line.strip() == ':::':
            # Check if this closes a column-page div after a mermaid block
            # Look back for a recent ```mermaid (within ~30 lines)
            lookback = '\n'.join(new_lines[-30:]) if len(new_lines) >= 30 else '\n'.join(new_lines)
            if '```mermaid' in lookback:
                # Only skip if the preceding non-blank line is ``` (end of mermaid)
                k = len(new_lines) - 1
                while k >= 0 and new_lines[k].strip() == '':
                    k -= 1
                if k >= 0 and new_lines[k].strip() == '```':
                    # Also remove trailing blank line before :::
                    while new_lines and new_lines[-1].strip() == '':
                        new_lines.pop()
                    i += 1
                    continue
            new_lines.append(line)
            i += 1
            continue

        new_lines.append(line)
        i += 1

    if converted > 0 and not dry_run:
        file_path.write_text('\n'.join(new_lines), encoding="utf-8")

    return converted


def strip_quarto_latex(file_path: Path, dry_run: bool = False) -> int:
    """Strip Quarto/LaTeX directives from .md files.

    Removes:
    - \\newpage lines
    - \\begin{samepage} / \\end{samepage} lines
    - ::: {.table-responsive} opener lines and their matching ::: closers

    Returns the number of directives removed.
    """
    if file_path.suffix != ".md":
        return 0

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return 0

    # Quick check — skip files with no relevant patterns
    if not any(pat in content for pat in [
        '\\newpage', '\\begin{samepage}', '\\end{samepage}',
        '::: {.table-responsive}'
    ]):
        return 0

    lines = content.split('\n')
    new_lines: List[str] = []
    removed = 0
    # Track how many ::: {.table-responsive} openers are open
    table_responsive_depth = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Remove \newpage
        if stripped == '\\newpage':
            removed += 1
            i += 1
            continue

        # Remove \begin{samepage} and \end{samepage}
        if stripped in ('\\begin{samepage}', '\\end{samepage}'):
            removed += 1
            i += 1
            continue

        # Remove ::: {.table-responsive} opener
        if re.match(r'^:::\s*\{\.table-responsive\}', stripped):
            table_responsive_depth += 1
            removed += 1
            i += 1
            continue

        # Remove matching ::: closer for table-responsive
        if stripped == ':::' and table_responsive_depth > 0:
            table_responsive_depth -= 1
            removed += 1
            i += 1
            continue

        new_lines.append(line)
        i += 1

    if removed > 0 and not dry_run:
        file_path.write_text('\n'.join(new_lines), encoding="utf-8")

    return removed


def update_references(
    file_path: Path,
    dry_run: bool = False,
    extensions_to_check: Set[str] = None
) -> int:
    """Update .qmd references to .md within a file."""
    if extensions_to_check is None:
        extensions_to_check = {".md", ".py", ".toml", ".yaml", ".yml", ".sh"}

    if file_path.suffix not in extensions_to_check:
        return 0

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return 0

    # Pattern to find .qmd references
    pattern = r'(\b\w[\w\-/]*\.qmd\b)'
    matches = re.findall(pattern, content)
    if not matches:
        return 0

    # Replace .qmd with .md
    new_content = re.sub(pattern, lambda m: m.group(1)[:-4] + ".md", content)

    if not dry_run and new_content != content:
        file_path.write_text(new_content, encoding="utf-8")

    return len(matches)


def migrate_directory(
    directory: Path,
    dry_run: bool = False,
    update_refs: bool = True,
    exclude_patterns: List[str] = None
) -> MigrationReport:
    """Perform full migration of a directory."""
    if exclude_patterns is None:
        exclude_patterns = [".git", "node_modules", "venv", "__pycache__"]

    report = MigrationReport()

    # Find all .qmd files
    qmd_files = find_qmd_files(directory)

    # Filter excluded paths
    qmd_files = [
        f for f in qmd_files
        if not any(excl in str(f) for excl in exclude_patterns)
    ]

    report.files_found = len(qmd_files)

    # Rename files
    for qmd_path in qmd_files:
        md_path = qmd_path.with_suffix(".md")

        # Skip if .md already exists
        if md_path.exists():
            report.files_skipped += 1
            report.errors.append(f"Skipped {qmd_path}: {md_path} already exists")
            continue

        try:
            new_path = rename_file(qmd_path, dry_run=dry_run)
            report.files_renamed += 1
            report.renamed_files.append((str(qmd_path), str(new_path)))
        except Exception as e:
            report.errors.append(f"Error renaming {qmd_path}: {e}")

    # Update references and convert mermaid syntax in all files
    all_files = list(directory.rglob("*"))
    all_files = [
        f for f in all_files
        if f.is_file() and not any(excl in str(f) for excl in exclude_patterns)
    ]

    for file_path in all_files:
        if update_refs:
            refs_updated = update_references(file_path, dry_run=dry_run)
            report.references_updated += refs_updated

        # Convert Quarto mermaid syntax to standard in .md files
        blocks_converted = convert_quarto_mermaid(file_path, dry_run=dry_run)
        report.mermaid_blocks_converted += blocks_converted

        # Strip Quarto/LaTeX directives from .md files
        latex_removed = strip_quarto_latex(file_path, dry_run=dry_run)
        report.latex_directives_removed += latex_removed

    return report


def add_migrate_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add the migrate command parser to subparsers."""
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate ADC contracts from .qmd to .md format"
    )
    migrate_parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Directory to migrate (default: current directory)"
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    migrate_parser.add_argument(
        "--no-update-refs",
        action="store_true",
        help="Don't update .qmd references in files"
    )
    migrate_parser.add_argument(
        "--exclude",
        nargs="*",
        default=[".git", "node_modules", "venv", "__pycache__"],
        help="Patterns to exclude from migration"
    )


def migrate_command(
    directory: Path,
    dry_run: bool = False,
    no_update_refs: bool = False,
    exclude: list = None
) -> bool:
    """Execute the migrate command.

    Args:
        directory: Directory to migrate
        dry_run: If True, show what would be done without changes
        no_update_refs: If True, don't update .qmd references
        exclude: Patterns to exclude

    Returns:
        True if successful, False otherwise
    """
    if exclude is None:
        exclude = [".git", "node_modules", "venv", "__pycache__"]

    if dry_run:
        print("=== DRY RUN MODE ===\n")

    report = migrate_directory(
        directory,
        dry_run=dry_run,
        update_refs=not no_update_refs,
        exclude_patterns=exclude
    )

    print(report.summary())

    if dry_run:
        print("\n=== No changes made (dry run) ===")

    return len(report.errors) == 0
