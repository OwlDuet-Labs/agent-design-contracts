# agent-design-contracts/src/adc_cli/providers.py
import os
from dataclasses import dataclass
from typing import Dict

from .logging_config import logger


# ADC-IMPLEMENTS: <adc-cli-datamodel-01>
@dataclass(frozen=True)
class ProviderResult:
    """Result object for provider operations."""

    success: bool
    message: str = ""
    error_details: str = ""

    @classmethod
    def success_result(cls, message: str = "Operation successful") -> "ProviderResult":
        return cls(success=True, message=message)

    @classmethod
    def error_result(cls, message: str, error_details: str = "") -> "ProviderResult":
        return cls(success=False, message=message, error_details=error_details)


# ADC-IMPLEMENTS: <adc-cli-datamodel-01>
@dataclass(frozen=True)
class GenerationResult:
    """Result object for content generation."""

    success: bool
    content: str = ""
    model_used: str = ""
    error_message: str = ""

    @classmethod
    def success_result(cls, content: str, model_used: str = "") -> "GenerationResult":
        return cls(success=True, content=content, model_used=model_used)

    @classmethod
    def error_result(cls, error_message: str) -> "GenerationResult":
        return cls(success=False, error_message=error_message)


# ADC-IMPLEMENTS: <adc-cli-datamodel-01>
@dataclass(frozen=True)
class AIProvider:
    """Functional design for AI provider interface."""

    name: str = "unknown"
    description: str = "No description provided"
    api_key: str = ""
    is_initialized: bool = False

    def initialize(self) -> ProviderResult:
        """Returns success/failure with error details, no exceptions."""
        if not self.api_key:
            return ProviderResult.error_result(
                f"API key not provided for {self.name}",
                f"Set {self.name.upper()}_API_KEY environment variable",
            )
        return ProviderResult.success_result(f"{self.name} initialized successfully")

    def generate(
        self, system_prompt: str, user_content: str, model: str
    ) -> GenerationResult:
        """Returns result object with content and metadata."""
        if not self.is_initialized:
            return GenerationResult.error_result(
                f"Provider {self.name} not initialized"
            )

        # This is the base implementation - specific providers will override
        return GenerationResult.error_result(f"Provider {self.name} not implemented")


# Try to import Gemini
try:
    import google.generativeai as genai

    # ADC-IMPLEMENTS: <adc-cli-datamodel-01>
    @dataclass(frozen=True)
    class GeminiAgent(AIProvider):
        """Gemini AI agent implementation with functional design."""

        name: str = "gemini"
        description: str = "Google's Gemini AI model"
        api_key: str = ""
        is_initialized: bool = False

        @classmethod
        def create(cls) -> "GeminiAgent":
            """Factory method to create initialized Gemini agent."""
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    return cls(api_key=api_key, is_initialized=True)
                except Exception:
                    return cls(api_key=api_key, is_initialized=False)
            return cls(api_key=api_key, is_initialized=False)

        def initialize(self) -> ProviderResult:
            """Initialize the Gemini client."""
            if not self.api_key:
                return ProviderResult.error_result(
                    "GOOGLE_API_KEY environment variable is not set",
                    "Set GOOGLE_API_KEY to your Google API key",
                )
            try:
                genai.configure(api_key=self.api_key)
                return ProviderResult.success_result("Gemini initialized successfully")
            except Exception as e:
                return ProviderResult.error_result(
                    "Failed to initialize Gemini", str(e)
                )

        def generate(
            self,
            system_prompt: str,
            user_content: str,
            model: str = "gemini-1.5-pro-latest",
        ) -> GenerationResult:
            """Generate content using Gemini."""
            if not self.is_initialized:
                return GenerationResult.error_result("Gemini not initialized")

            try:
                model_instance = genai.GenerativeModel(
                    model, system_instruction=system_prompt
                )
                response = model_instance.generate_content(user_content)
                return GenerationResult.success_result(
                    content=response.text, model_used=model
                )
            except Exception as e:
                return GenerationResult.error_result(
                    f"Gemini generation failed: {str(e)}"
                )

    GEMINI_AVAILABLE = True
    logger.info("Gemini AI provider loaded.")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.info(
        "Gemini AI provider not available. Install google-generativeai package to enable."
    )

    @dataclass(frozen=True)
    class GeminiAgent(AIProvider):
        name: str = "gemini"
        description: str = "Google's Gemini AI model (not available)"
        api_key: str = ""
        is_initialized: bool = False

        @classmethod
        def create(cls) -> "GeminiAgent":
            return cls()

        def initialize(self) -> ProviderResult:
            return ProviderResult.error_result(
                "Gemini provider not available",
                "Install google-generativeai package to enable",
            )

        def generate(
            self, system_prompt: str, user_content: str, model: str = ""
        ) -> GenerationResult:
            return GenerationResult.error_result("Gemini provider not available")


# Try to import OpenAI
try:
    import openai

    # ADC-IMPLEMENTS: <adc-cli-datamodel-01>
    @dataclass(frozen=True)
    class OpenAIAgent(AIProvider):
        """OpenAI agent implementation with functional design."""

        name: str = "openai"
        description: str = "OpenAI's GPT models"
        api_key: str = ""
        is_initialized: bool = False

        @classmethod
        def create(cls) -> "OpenAIAgent":
            """Factory method to create initialized OpenAI agent."""
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if api_key:
                try:
                    openai.api_key = api_key
                    return cls(api_key=api_key, is_initialized=True)
                except Exception:
                    return cls(api_key=api_key, is_initialized=False)
            return cls(api_key=api_key, is_initialized=False)

        def initialize(self) -> ProviderResult:
            """Initialize the OpenAI client."""
            if not self.api_key:
                return ProviderResult.error_result(
                    "OPENAI_API_KEY environment variable is not set",
                    "Set OPENAI_API_KEY to your OpenAI API key",
                )
            try:
                openai.api_key = self.api_key
                return ProviderResult.success_result("OpenAI initialized successfully")
            except Exception as e:
                return ProviderResult.error_result(
                    "Failed to initialize OpenAI", str(e)
                )

        def generate(
            self, system_prompt: str, user_content: str, model: str = "gpt-4o"
        ) -> GenerationResult:
            """Generate content using OpenAI."""
            if not self.is_initialized:
                return GenerationResult.error_result("OpenAI not initialized")

            try:
                response = openai.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                )
                return GenerationResult.success_result(
                    content=response.choices[0].message.content, model_used=model
                )
            except Exception as e:
                return GenerationResult.error_result(
                    f"OpenAI generation failed: {str(e)}"
                )

    OPENAI_AVAILABLE = True
    logger.info("OpenAI provider loaded.")
except ImportError:
    OPENAI_AVAILABLE = False
    logger.info("OpenAI provider not available. Install openai package to enable.")

    @dataclass(frozen=True)
    class OpenAIAgent(AIProvider):
        name: str = "openai"
        description: str = "OpenAI's GPT models (not available)"
        api_key: str = ""
        is_initialized: bool = False

        @classmethod
        def create(cls) -> "OpenAIAgent":
            return cls()

        def initialize(self) -> ProviderResult:
            return ProviderResult.error_result(
                "OpenAI provider not available", "Install openai package to enable"
            )

        def generate(
            self, system_prompt: str, user_content: str, model: str = ""
        ) -> GenerationResult:
            return GenerationResult.error_result("OpenAI provider not available")


# Try to import Anthropic
try:
    import anthropic

    # ADC-IMPLEMENTS: <adc-cli-datamodel-01>
    @dataclass(frozen=True)
    class AnthropicAgent(AIProvider):
        """Anthropic Claude agent implementation with functional design."""

        name: str = "anthropic"
        description: str = "Anthropic's Claude models"
        api_key: str = ""
        is_initialized: bool = False
        _client: anthropic.Anthropic = None

        @classmethod
        def create(cls) -> "AnthropicAgent":
            """Factory method to create initialized Anthropic agent."""
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if api_key:
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    return cls(api_key=api_key, is_initialized=True, _client=client)
                except Exception:
                    return cls(api_key=api_key, is_initialized=False)
            return cls(api_key=api_key, is_initialized=False)

        def initialize(self) -> ProviderResult:
            """Initialize the Anthropic client."""
            if not self.api_key:
                return ProviderResult.error_result(
                    "ANTHROPIC_API_KEY environment variable is not set",
                    "Set ANTHROPIC_API_KEY to your Anthropic API key",
                )
            try:
                client = anthropic.Anthropic(api_key=self.api_key)
                # Return new instance with client
                return ProviderResult.success_result(
                    "Anthropic initialized successfully"
                )
            except Exception as e:
                return ProviderResult.error_result(
                    "Failed to initialize Anthropic", str(e)
                )

        def generate(
            self,
            system_prompt: str,
            user_content: str,
            model: str = "claude-3-sonnet-20240229",
        ) -> GenerationResult:
            """Generate content using Anthropic Claude."""
            if not self.is_initialized or not self._client:
                return GenerationResult.error_result("Anthropic not initialized")

            try:
                response = self._client.messages.create(
                    model=model,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_content}],
                    max_tokens=4000,
                )
                return GenerationResult.success_result(
                    content=response.content[0].text, model_used=model
                )
            except Exception as e:
                return GenerationResult.error_result(
                    f"Anthropic generation failed: {str(e)}"
                )

    ANTHROPIC_AVAILABLE = True
    logger.info("Anthropic Claude provider loaded.")
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.info(
        "Anthropic provider not available. Install anthropic package to enable."
    )

    @dataclass(frozen=True)
    class AnthropicAgent(AIProvider):
        name: str = "anthropic"
        description: str = "Anthropic's Claude models (not available)"
        api_key: str = ""
        is_initialized: bool = False

        @classmethod
        def create(cls) -> "AnthropicAgent":
            return cls()

        def initialize(self) -> ProviderResult:
            return ProviderResult.error_result(
                "Anthropic provider not available",
                "Install anthropic package to enable",
            )

        def generate(
            self, system_prompt: str, user_content: str, model: str = ""
        ) -> GenerationResult:
            return GenerationResult.error_result("Anthropic provider not available")


def get_available_providers() -> Dict[str, AIProvider]:
    """Get dictionary of available AI providers."""
    providers = {}

    if GEMINI_AVAILABLE:
        providers["gemini"] = GeminiAgent.create()
    if OPENAI_AVAILABLE:
        providers["openai"] = OpenAIAgent.create()
    if ANTHROPIC_AVAILABLE:
        providers["anthropic"] = AnthropicAgent.create()

    return providers


def call_ai_agent(
    agent_name: str, system_prompt: str, user_content: str, model: str = ""
) -> str:
    """Call an AI agent and return the response."""
    providers = get_available_providers()

    if agent_name not in providers:
        return f"Error: Agent '{agent_name}' not available"

    provider = providers[agent_name]

    # Initialize if not already initialized
    if not provider.is_initialized:
        init_result = provider.initialize()
        if not init_result.success:
            return f"Error: {init_result.message} - {init_result.error_details}"

    # Generate content
    generation_result = provider.generate(system_prompt, user_content, model)

    if not generation_result.success:
        return f"Error: {generation_result.error_message}"

    return generation_result.content
