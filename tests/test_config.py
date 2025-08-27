"""Tests for adc_cli.config module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from adc_cli.config import ADCConfig, load_config, save_config, update_config


class TestADCConfig:
    """Tests for the ADCConfig class."""

    def test_init_default_path(self):
        """Test ADCConfig initialization with default path."""
        config = ADCConfig()
        assert config.default_agent == "gemini"
        assert config.task_agents == {
            "generate": "anthropic",
            "audit": "anthropic",
            "refine": "gemini",
        }
        assert config.models == {
            "anthropic": "claude-3-sonnet-20240229",
            "openai": "gpt-4o",
            "gemini": "gemini-1.5-pro-latest",
        }

    def test_init_custom_path(self):
        """Test ADCConfig initialization with custom values."""
        config = ADCConfig(
            default_agent="openai",
            task_agents={"test": "gemini"},
            models={"openai": "gpt-4"}
        )
        assert config.default_agent == "openai"
        assert config.task_agents == {"test": "gemini"}
        assert config.models == {"openai": "gpt-4"}

    def test_properties_empty_config(self):
        """Test properties with default config."""
        config = ADCConfig()
        assert config.default_agent == "gemini"
        assert len(config.task_agents) > 0
        assert len(config.models) > 0

    def test_properties_with_data(self):
        """Test properties with populated config."""
        config = ADCConfig(
            default_agent="anthropic",
            task_agents={"generate": "openai"},
            models={"anthropic": "claude-3"}
        )

        assert config.default_agent == "anthropic"
        assert config.task_agents == {"generate": "openai"}
        assert config.models == {"anthropic": "claude-3"}

    def test_to_dict(self):
        """Test to_dict method."""
        config = ADCConfig(
            default_agent="test_agent",
            task_agents={"task1": "agent1"},
            models={"provider1": "model1"}
        )

        result = config.to_dict()
        assert result["default_agent"] == "test_agent"
        assert result["task_agents"] == {"task1": "agent1"}
        assert result["models"] == {"provider1": "model1"}

        # Ensure it's a copy
        result["default_agent"] = "modified"
        assert config.default_agent == "test_agent"


class TestLoadConfig:
    """Tests for the load_config function."""

    @patch("adc_cli.config.ADCConfig.from_file")
    def test_load_config_no_file_creates_default(self, mock_from_file):
        """Test load_config creates default config when file doesn't exist."""
        mock_config = ADCConfig(
            default_agent="anthropic",
            task_agents={"generate": "anthropic"},
            models={"anthropic": "claude-3"}
        )
        mock_from_file.return_value = mock_config

        config = load_config()

        # Should return dict from config
        assert config["default_agent"] == "anthropic"
        assert "task_agents" in config
        assert "models" in config
        mock_from_file.assert_called_once()

    @patch("adc_cli.config.ADCConfig.from_file")
    def test_load_config_existing_file(self, mock_from_file):
        """Test load_config reads existing config file."""
        mock_config = ADCConfig(
            default_agent="openai",
            task_agents={"generate": "gemini"},
            models={"openai": "gpt-4"}
        )
        mock_from_file.return_value = mock_config

        config = load_config()

        assert config["default_agent"] == "openai"
        assert config["task_agents"] == {"generate": "gemini"}
        assert config["models"] == {"openai": "gpt-4"}

    @patch("adc_cli.config.ADCConfig.from_file")
    def test_load_config_file_error_returns_default(self, mock_from_file):
        """Test load_config returns default config when file reading fails."""
        # from_file handles errors internally and returns default
        mock_config = ADCConfig.with_defaults()
        mock_from_file.return_value = mock_config

        config = load_config()

        # Should return default config
        assert config["default_agent"] in ["gemini", "anthropic", "openai"]
        assert "task_agents" in config

    @patch("adc_cli.providers.get_available_providers")
    def test_load_config_provider_priority(self, mock_get_providers):
        """Test load_config chooses correct default provider by priority."""
        # Test anthropic priority
        mock_get_providers.return_value = {
            "anthropic": Mock(),
            "openai": Mock(),
            "gemini": Mock(),
        }

        config = ADCConfig.with_defaults()
        assert config.default_agent == "anthropic"

        # Test openai fallback
        mock_get_providers.return_value = {"openai": Mock(), "gemini": Mock()}
        config = ADCConfig.with_defaults()
        assert config.default_agent == "openai"

        # Test gemini fallback
        mock_get_providers.return_value = {"gemini": Mock()}
        config = ADCConfig.with_defaults()
        assert config.default_agent == "gemini"

        # Test no providers available - defaults to gemini
        mock_get_providers.return_value = {}
        config = ADCConfig.with_defaults()
        assert config.default_agent == "gemini"


class TestSaveConfig:
    """Tests for the save_config function."""

    def test_save_config_default_path(self):
        """Test save_config with default path."""
        config = {"test": "value"}

        with tempfile.TemporaryDirectory() as tmpdir:
            test_config_path = Path(tmpdir) / ".adcconfig.json"
            save_config(config, test_config_path)
            
            # Verify the file was created and contains the correct data
            assert test_config_path.exists()
            with open(test_config_path, "r") as f:
                saved_data = json.load(f)
            assert saved_data == config

    def test_save_config_custom_path(self):
        """Test save_config with custom path."""
        config = {"test": "value"}
        custom_path = Path("/custom/path/config.json")

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_dump:
                save_config(config, custom_path)

                mock_file.assert_called_once_with(custom_path, "w", encoding="utf-8")
                mock_dump.assert_called_once_with(
                    config, mock_file().__enter__(), indent=2
                )

    def test_save_config_error_handling(self):
        """Test save_config handles errors gracefully."""
        config = {"test": "value"}

        with patch("builtins.open", side_effect=IOError("Write error")):
            # Should not raise exception
            save_config(config)


class TestUpdateConfig:
    """Tests for the update_config function."""

    @patch("adc_cli.config.ADCConfig.from_file")
    @patch("adc_cli.config.ADCConfig.save_to_file")
    def test_update_config_default_agent(self, mock_save, mock_from_file):
        """Test updating default_agent."""
        old_config = ADCConfig(default_agent="old_agent")
        mock_from_file.return_value = old_config
        mock_save.return_value = True

        result = update_config(default_agent="new_agent")

        assert result is True
        mock_save.assert_called_once()

    @patch("adc_cli.config.ADCConfig.from_file")
    @patch("adc_cli.config.ADCConfig.save_to_file")
    def test_update_config_task_agent(self, mock_save, mock_from_file):
        """Test updating task-specific agent."""
        old_config = ADCConfig(
            default_agent="agent",
            task_agents={"generate": "old_agent"}
        )
        mock_from_file.return_value = old_config
        mock_save.return_value = True

        result = update_config(task_generate="new_agent")

        assert result is True
        mock_save.assert_called_once()

    @patch("adc_cli.config.ADCConfig.from_file")
    @patch("adc_cli.config.ADCConfig.save_to_file")
    def test_update_config_multiple_updates(self, mock_save, mock_from_file):
        """Test updating multiple configuration values."""
        old_config = ADCConfig(
            default_agent="old_agent",
            task_agents={"generate": "old_gen", "audit": "old_audit"}
        )
        mock_from_file.return_value = old_config
        mock_save.return_value = True

        result = update_config(
            default_agent="new_agent", task_generate="new_gen", task_audit="new_audit"
        )

        assert result is True
        mock_save.assert_called_once()

    @patch("adc_cli.config.ADCConfig.from_file")
    @patch("adc_cli.config.ADCConfig.save_to_file")
    def test_update_config_unknown_key(self, mock_save, mock_from_file):
        """Test updating with unknown key logs warning."""
        old_config = ADCConfig(default_agent="agent")
        mock_from_file.return_value = old_config
        mock_save.return_value = True

        with patch("adc_cli.config.logger") as mock_logger:
            result = update_config(unknown_key="value")

            assert result is True
            mock_logger.warning.assert_called_once_with(
                "Unknown configuration key: unknown_key"
            )
            mock_save.assert_called_once()
