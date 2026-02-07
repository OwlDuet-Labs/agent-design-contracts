"""
Language detection for Universal Library Loader.

This module automatically detects the programming language of a workspace
by scanning for language-specific indicator files.
"""

# ADC-IMPLEMENTS: <ull-feature-01>

from pathlib import Path
from typing import Tuple

from .metadata import LanguageType
from .exceptions import LibraryLoadError


# Language indicator files mapping
LANGUAGE_INDICATORS = {
    LanguageType.PYTHON: [
        "setup.py",
        "pyproject.toml",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
    ],
    LanguageType.NODEJS: [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "tsconfig.json",
    ],
    LanguageType.DART: [
        "pubspec.yaml",
        "pubspec.lock",
    ],
    LanguageType.RUST: [
        "Cargo.toml",
        "Cargo.lock",
    ],
    LanguageType.GO: [
        "go.mod",
        "go.sum",
    ],
    LanguageType.JAVA: [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
    ],
    LanguageType.CPP: [
        "CMakeLists.txt",
        "Makefile",
        "BUILD.bazel",  # C++ Bazel projects
    ],
}


def detect_language(workspace_path: Path) -> Tuple[LanguageType, dict[str, bool]]:
    """
    Detect programming language from workspace structure.

    Args:
        workspace_path: Path to workspace directory

    Returns:
        (detected_language, indicators_found)

    Raises:
        LibraryLoadError: If no language indicators found
    """
    if not workspace_path.exists():
        raise LibraryLoadError(
            f"Workspace path does not exist: {workspace_path}\n"
            f"  Fix: Ensure workspace directory exists"
        )

    if not workspace_path.is_dir():
        raise LibraryLoadError(
            f"Workspace path is not a directory: {workspace_path}\n"
            f"  Fix: Provide path to workspace directory"
        )

    indicators_found = {}
    language_scores = {lang: 0 for lang in LanguageType}

    for language, indicator_files in LANGUAGE_INDICATORS.items():
        for indicator in indicator_files:
            indicator_path = workspace_path / indicator
            exists = indicator_path.exists()
            indicators_found[indicator] = exists

            if exists:
                language_scores[language] += 1

    # Find language with highest score
    best_language = max(language_scores.items(), key=lambda x: x[1])

    if best_language[1] == 0:
        all_indicators = []
        for indicators in LANGUAGE_INDICATORS.values():
            all_indicators.extend(indicators)

        raise LibraryLoadError(
            f"Unable to detect library language in {workspace_path}\n"
            f"  Checked for: {', '.join(sorted(set(all_indicators)))}\n"
            f"  Fix: Ensure workspace contains language indicator file"
        )

    return best_language[0], indicators_found
