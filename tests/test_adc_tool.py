#!/usr/bin/env python3
"""
Comprehensive test suite for adc_cli.

This test suite can be run directly without pytest:
    PYTHONPATH=src python tests/test_adc_tool.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add src to path so we can import adc_cli
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_providers():
    """Test the providers module."""
    print("Testing providers...")

    from adc_cli.providers import AIProvider, call_ai_agent, get_available_providers

    # Test that AIProvider is now a frozen dataclass (not abstract)
    provider = AIProvider()
    assert provider.name == "unknown"
    assert provider.is_initialized is False

    # Test get_available_providers returns dictionary
    providers = get_available_providers()
    assert isinstance(providers, dict), "get_available_providers should return dict"

    # Test call_ai_agent with invalid provider
    result = call_ai_agent("nonexistent_provider", "system", "user")
    assert result.startswith("Error:"), "Should return error for nonexistent provider"

    print("✅ Providers tests passed")


def test_config():
    """Test the config module."""
    print("Testing config...")

    from adc_cli.config import ADCConfig, load_config

    # Test ADCConfig initialization (frozen dataclass)
    config = ADCConfig()
    assert config.default_agent == "gemini"  # Default value
    assert len(config.task_agents) > 0  # Has default task agents
    assert len(config.models) > 0  # Has default models

    # Test with custom values
    config = ADCConfig(
        default_agent="openai",
        task_agents={"test": "gemini"},
        models={"openai": "gpt-4"}
    )
    assert config.default_agent == "openai"
    assert config.task_agents == {"test": "gemini"}
    assert config.models == {"openai": "gpt-4"}

    # Test load_config returns dict
    config_data = load_config()
    assert isinstance(config_data, dict), "load_config should return dict"
    assert "default_agent" in config_data
    assert "task_agents" in config_data
    assert "models" in config_data

    print("✅ Config tests passed")


def test_commands():
    """Test the commands module."""
    print("Testing commands...")

    from adc_cli.commands import config_command

    # Test config show command
    # We can't easily mock builtins.print, so we'll just test it doesn't crash
    try:
        result = config_command(action="show")
        assert result is True, "config show should return True"
    except Exception as e:
        assert False, f"config show should not raise exception: {e}"

    # Test invalid config action
    result = config_command(action="invalid")
    assert result is False, "invalid config action should return False"

    print("✅ Commands tests passed")


def test_main_module():
    """Test the main module functionality."""
    print("Testing main module...")

    from adc_cli.__main__ import main

    # Test main function exists and is callable
    assert callable(main), "main function should be callable"

    print("✅ Main module tests passed")


def test_logging_config():
    """Test the logging configuration."""
    print("Testing logging config...")

    from adc_cli.logging_config import configure_logging, logger

    # Test logger exists
    assert logger is not None, "logger should exist"

    # Test configure_logging returns logger
    test_logger = configure_logging(verbose=True)
    assert test_logger is not None, "configure_logging should return logger"

    # Test logger name
    assert logger.name == "adc_cli", "logger should have correct name"

    print("✅ Logging config tests passed")


def test_integration():
    """Test basic integration by running CLI commands."""
    print("Testing CLI integration...")

    import subprocess

    # Test help command
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'src'); from adc_cli.__main__ import main; sys.argv = ['adc', '--help']; main()",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    # The help command should exit with code 0 and contain usage info
    assert (
        "ADC (Agent Design Contracts) CLI Tool" in result.stdout
        or "usage:" in result.stdout
    ), "Help should contain usage information"

    print("✅ CLI integration tests passed")


def test_vs_code_setup():
    """Test VS Code setup functionality."""
    print("Testing VS Code setup...")

    from adc_cli.commands import setup_vscode_command

    # Test in a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            result = setup_vscode_command()
            assert result is True, "VS Code setup should succeed"

            # Check that files were created
            vscode_dir = Path(tmpdir) / ".vscode"
            assert vscode_dir.exists(), ".vscode directory should be created"

            settings_file = vscode_dir / "settings.json"
            tasks_file = vscode_dir / "tasks.json"

            assert settings_file.exists(), "settings.json should be created"
            assert tasks_file.exists(), "tasks.json should be created"

            # Check settings content
            with open(settings_file) as f:
                settings = json.load(f)
                assert "files.associations" in settings, (
                    "settings should contain file associations"
                )
                assert settings["files.associations"]["*.qmd"] == "markdown", (
                    "qmd files should be associated with markdown"
                )

            # Check tasks content
            with open(tasks_file) as f:
                tasks = json.load(f)
                assert "tasks" in tasks, "tasks.json should contain tasks"
                assert len(tasks["tasks"]) == 2, "should have 2 tasks"

                task_labels = [task["label"] for task in tasks["tasks"]]
                assert "ADC: Generate Code" in task_labels, "should have generate task"
                assert "ADC: Audit Implementation" in task_labels, (
                    "should have audit task"
                )

        finally:
            os.chdir(original_cwd)

    print("✅ VS Code setup tests passed")


def run_all_tests():
    """Run all tests."""
    print("🧪 Running adc_cli test suite...\n")

    tests = [
        test_providers,
        test_config,
        test_commands,
        test_main_module,
        test_logging_config,
        test_integration,
        test_vs_code_setup,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
        print()

    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
