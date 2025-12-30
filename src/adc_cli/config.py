# agent-design-contracts/src/adc_cli/config.py
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from .logging_config import logger


# ADC-IMPLEMENTS: <adc-cli-datamodel-02>
@dataclass(frozen=True)
class ADCConfig:
    """Configuration object with functional design - no Optional types."""

    default_agent: str = "gemini"
    task_agents: Dict[str, str] = field(
        default_factory=lambda: {
            "generate": "anthropic",
            "audit": "anthropic",
            "refine": "gemini",
            "refactor": "anthropic",
            "initialize": "anthropic",
        }
    )
    models: Dict[str, str] = field(
        default_factory=lambda: {
            "anthropic": "claude-3-sonnet-20240229",
            "openai": "gpt-4o",
            "gemini": "gemini-1.5-pro-latest",
        }
    )

    @classmethod
    def with_defaults(cls) -> "ADCConfig":
        """Factory method to create config with sensible defaults."""
        from .providers import get_available_providers

        # Determine best available provider as default
        available_providers = get_available_providers()
        default_agent = "gemini"
        if "anthropic" in available_providers:
            default_agent = "anthropic"
        elif "openai" in available_providers:
            default_agent = "openai"
        elif "gemini" in available_providers:
            default_agent = "gemini"

        return cls(default_agent=default_agent)

    @classmethod
    def from_file(
        cls, config_path: Path = Path.home() / ".adcconfig.json"
    ) -> "ADCConfig":
        """Factory method to create config from file with fallback to defaults."""
        if not config_path.exists():
            # Create default config and save it
            default_config = cls.with_defaults()
            default_config.save_to_file(config_path)
            logger.info(f"Created default configuration at {config_path}")
            return default_config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            return cls(
                default_agent=config_data.get("default_agent", "gemini"),
                task_agents=config_data.get("task_agents", {}),
                models=config_data.get("models", {}),
            )
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {str(e)}")
            return cls.with_defaults()

    def save_to_file(self, config_path: Path = Path.home() / ".adcconfig.json") -> bool:
        """Save configuration to file."""
        try:
            config_data = {
                "default_agent": self.default_agent,
                "task_agents": self.task_agents,
                "models": self.models,
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Configuration saved to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config to {config_path}: {str(e)}")
            return False

    def with_updates(self, **updates) -> "ADCConfig":
        """Functional update - returns new config with updates applied."""
        new_task_agents = self.task_agents.copy()
        new_models = self.models.copy()
        new_default_agent = self.default_agent

        for key, value in updates.items():
            if key == "default_agent":
                new_default_agent = value
            elif key.startswith("task_"):
                # Handle task-specific agent updates (e.g., task_generate -> task_agents.generate)
                task_name = key[5:]  # Remove "task_" prefix
                new_task_agents[task_name] = value
            elif key.startswith("model_"):
                # Handle model updates (e.g., model_anthropic -> models.anthropic)
                provider_name = key[6:]  # Remove "model_" prefix
                new_models[provider_name] = value
            else:
                logger.warning(f"Unknown configuration key: {key}")

        return ADCConfig(
            default_agent=new_default_agent,
            task_agents=new_task_agents,
            models=new_models,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "default_agent": self.default_agent,
            "task_agents": self.task_agents,
            "models": self.models,
        }


# ADC-IMPLEMENTS: <adc-cli-datamodel-02>
def load_config() -> Dict[str, Any]:
    """Load configuration from .adcconfig.json file - returns dict for backward compatibility."""
    config = ADCConfig.from_file()
    return config.to_dict()


def save_config(
    config: Dict[str, Any], config_path: Path = Path.home() / ".adcconfig.json"
) -> None:
    """Save configuration to .adcconfig.json file - accepts dict for backward compatibility."""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")


def update_config(**updates) -> bool:
    """Update specific configuration values."""
    config = ADCConfig.from_file()
    updated_config = config.with_updates(**updates)
    return updated_config.save_to_file()
