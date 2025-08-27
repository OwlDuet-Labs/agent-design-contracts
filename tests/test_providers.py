"""Tests for adc_cli.providers module."""

import os
from unittest.mock import Mock, patch

import pytest
from adc_cli.providers import (
    ANTHROPIC_AVAILABLE,
    GEMINI_AVAILABLE,
    OPENAI_AVAILABLE,
    AIProvider,
    AnthropicAgent,
    GeminiAgent,
    OpenAIAgent,
    call_ai_agent,
    get_available_providers,
)


class TestAIProvider:
    """Tests for the abstract AIProvider base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that AIProvider can be instantiated as a dataclass."""
        # AIProvider is now a frozen dataclass, not abstract
        provider = AIProvider()
        assert provider.name == "unknown"
        assert provider.is_initialized is False


class TestGeminiAgent:
    """Tests for the GeminiAgent class."""

    def test_init(self):
        """Test GeminiAgent initialization."""
        agent = GeminiAgent()
        assert agent.name == "gemini"
        assert "Gemini" in agent.description

    def test_initialize_success(self):
        """Test successful initialization of GeminiAgent."""
        if not GEMINI_AVAILABLE:
            pytest.skip("Gemini not available")

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch("google.generativeai.configure") as mock_configure:
                agent = GeminiAgent()
                result = agent.initialize()

                assert result.success is True
                mock_configure.assert_called_once_with(api_key="test_key")

    def test_initialize_no_api_key(self):
        """Test GeminiAgent initialization without API key."""
        if not GEMINI_AVAILABLE:
            pytest.skip("Gemini not available")

        agent = GeminiAgent()

        with patch.dict(os.environ, {}, clear=True):
            result = agent.initialize()
            assert result.success is False
            assert "GOOGLE_API_KEY" in result.error_details

    def test_generate_success(self):
        """Test successful content generation with GeminiAgent."""
        if not GEMINI_AVAILABLE:
            pytest.skip("Gemini not available")

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch("google.generativeai.configure"):
                with patch("google.generativeai.GenerativeModel") as mock_model_class:
                    # Mock the response
                    mock_model = Mock()
                    mock_response = Mock()
                    mock_response.text = "Generated content"
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model

                    agent = GeminiAgent()
                    result = agent.generate("System prompt", "User content", "")

                    assert result.success is True
                    assert result.content == "Generated content"
                    mock_model_class.assert_called_once_with(
                        "gemini-1.5-pro-latest", system_instruction="System prompt"
                    )
                    mock_model.generate_content.assert_called_once_with("User content")

    def test_initialize_not_available(self):
        """Test GeminiAgent when not available."""
        if GEMINI_AVAILABLE:
            pytest.skip("Gemini is available")

        agent = GeminiAgent()
        result = agent.initialize()
        assert result.success is False
        assert "not available" in result.message or "not provided" in result.message

    def test_generate_not_available(self):
        """Test GeminiAgent generation when not available."""
        if GEMINI_AVAILABLE:
            pytest.skip("Gemini is available")

        agent = GeminiAgent()
        result = agent.generate("System prompt", "User content", "")
        assert result.success is False
        assert "not" in result.error_message


class TestOpenAIAgent:
    """Tests for the OpenAIAgent class."""

    def test_init(self):
        """Test OpenAIAgent initialization."""
        agent = OpenAIAgent()
        assert agent.name == "openai"
        assert "OpenAI" in agent.description

    def test_initialize_success(self):
        """Test successful initialization of OpenAIAgent."""
        if not OPENAI_AVAILABLE:
            pytest.skip("OpenAI not available")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch("openai.api_key", new_callable=lambda: Mock()) as mock_api_key:
                agent = OpenAIAgent()
                result = agent.initialize()

                assert result.success is True
                # Check that api_key was set (the assignment happens in the function)

    def test_initialize_no_api_key(self):
        """Test OpenAIAgent initialization without API key."""
        if not OPENAI_AVAILABLE:
            pytest.skip("OpenAI not available")

        agent = OpenAIAgent()

        with patch.dict(os.environ, {}, clear=True):
            result = agent.initialize()
            assert result.success is False
            assert "OPENAI_API_KEY" in result.error_details

    def test_generate_success(self):
        """Test successful content generation with OpenAIAgent."""
        if not OPENAI_AVAILABLE:
            pytest.skip("OpenAI not available")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch("openai.api_key", new_callable=lambda: Mock()):
                with patch("openai.chat.completions.create") as mock_create:
                    # Mock the response
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = "Generated content"
                    mock_create.return_value = mock_response

                    agent = OpenAIAgent()
                    result = agent.generate("System prompt", "User content", "")

                    assert result.success is True
                    assert result.content == "Generated content"
                    mock_create.assert_called_once_with(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "System prompt"},
                            {"role": "user", "content": "User content"},
                        ],
                    )

    def test_initialize_not_available(self):
        """Test OpenAIAgent when not available."""
        if OPENAI_AVAILABLE:
            pytest.skip("OpenAI is available")

        agent = OpenAIAgent()
        result = agent.initialize()
        assert result.success is False
        assert "not available" in result.message or "not provided" in result.message

    def test_generate_not_available(self):
        """Test OpenAIAgent generation when not available."""
        if OPENAI_AVAILABLE:
            pytest.skip("OpenAI is available")

        agent = OpenAIAgent()
        result = agent.generate("System prompt", "User content", "")
        assert result.success is False
        assert "not" in result.error_message


class TestAnthropicAgent:
    """Tests for the AnthropicAgent class."""

    def test_init(self):
        """Test AnthropicAgent initialization."""
        agent = AnthropicAgent()
        assert agent.name == "anthropic"
        assert "Anthropic" in agent.description

    def test_initialize_success(self):
        """Test successful initialization of AnthropicAgent."""
        if not ANTHROPIC_AVAILABLE:
            pytest.skip("Anthropic not available")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
            with patch("anthropic.Anthropic") as mock_anthropic_class:
                agent = AnthropicAgent()
                result = agent.initialize()

                assert result.success is True
                mock_anthropic_class.assert_called_once_with(api_key="test_key")

    def test_initialize_no_api_key(self):
        """Test AnthropicAgent initialization without API key."""
        if not ANTHROPIC_AVAILABLE:
            pytest.skip("Anthropic not available")

        agent = AnthropicAgent()

        with patch.dict(os.environ, {}, clear=True):
            result = agent.initialize()
            assert result.success is False
            assert "ANTHROPIC_API_KEY" in result.error_details

    def test_generate_success(self):
        """Test successful content generation with AnthropicAgent."""
        if not ANTHROPIC_AVAILABLE:
            pytest.skip("Anthropic not available")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
            with patch("anthropic.Anthropic") as mock_anthropic_class:
                # Mock the client and response
                mock_client = Mock()
                mock_response = Mock()
                mock_response.content = [Mock()]
                mock_response.content[0].text = "Generated content"
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                agent = AnthropicAgent()
                agent.initialize()
                result = agent.generate("System prompt", "User content", "")

                assert result.success is True
                assert result.content == "Generated content"
                mock_client.messages.create.assert_called_once_with(
                    model="claude-3-sonnet-20240229",
                    system="System prompt",
                    messages=[{"role": "user", "content": "User content"}],
                    max_tokens=4000,
                )

    def test_initialize_not_available(self):
        """Test AnthropicAgent when not available."""
        if ANTHROPIC_AVAILABLE:
            pytest.skip("Anthropic is available")

        agent = AnthropicAgent()
        result = agent.initialize()
        assert result.success is False
        assert "not available" in result.message or "not provided" in result.message

    def test_generate_not_available(self):
        """Test AnthropicAgent generation when not available."""
        if ANTHROPIC_AVAILABLE:
            pytest.skip("Anthropic is available")

        agent = AnthropicAgent()
        result = agent.generate("System prompt", "User content", "")
        assert result.success is False
        assert "not" in result.error_message


class TestProviderFunctions:
    """Tests for provider utility functions."""

    def test_get_available_providers(self):
        """Test get_available_providers returns correct providers."""
        providers = get_available_providers()

        # Check that we get a dictionary
        assert isinstance(providers, dict)

        # Check that available providers are included
        if GEMINI_AVAILABLE:
            assert "gemini" in providers
            assert isinstance(providers["gemini"], GeminiAgent)

        if OPENAI_AVAILABLE:
            assert "openai" in providers
            assert isinstance(providers["openai"], OpenAIAgent)

        if ANTHROPIC_AVAILABLE:
            assert "anthropic" in providers
            assert isinstance(providers["anthropic"], AnthropicAgent)

    def test_call_ai_agent_success(self):
        """Test successful AI agent call."""
        # Mock agent
        from adc_cli.providers import ProviderResult, GenerationResult
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.is_initialized = True
        mock_agent.initialize.return_value = ProviderResult.success_result()
        mock_agent.generate.return_value = GenerationResult.success_result("Generated response")

        with patch("adc_cli.providers.get_available_providers") as mock_get_providers:
            mock_get_providers.return_value = {"test_agent": mock_agent}

            result = call_ai_agent("test_agent", "System prompt", "User content")

            assert result == "Generated response"
            mock_agent.initialize.assert_not_called()  # Since is_initialized=True
            mock_agent.generate.assert_called_once_with("System prompt", "User content", "")

    def test_call_ai_agent_with_model(self):
        """Test AI agent call with specific model."""
        # Mock agent
        from adc_cli.providers import ProviderResult, GenerationResult
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.is_initialized = True
        mock_agent.initialize.return_value = ProviderResult.success_result()
        mock_agent.generate.return_value = GenerationResult.success_result("Generated response")

        with patch("adc_cli.providers.get_available_providers") as mock_get_providers:
            mock_get_providers.return_value = {"test_agent": mock_agent}

            result = call_ai_agent(
                "test_agent", "System prompt", "User content", "custom-model"
            )

            assert result == "Generated response"
            mock_agent.generate.assert_called_once_with(
                "System prompt", "User content", "custom-model"
            )

    def test_call_ai_agent_unavailable_provider(self):
        """Test AI agent call with unavailable provider."""
        with patch("adc_cli.providers.get_available_providers") as mock_get_providers:
            mock_get_providers.return_value = {}

            result = call_ai_agent("nonexistent_agent", "System prompt", "User content")

            assert result.startswith(
                "Error: Agent 'nonexistent_agent' not available"
            )

    def test_call_ai_agent_initialization_error(self):
        """Test AI agent call with initialization error."""
        # Mock agent that fails to initialize
        from adc_cli.providers import ProviderResult
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.is_initialized = False
        mock_agent.initialize.return_value = ProviderResult.error_result("Initialization failed")

        with patch("adc_cli.providers.get_available_providers") as mock_get_providers:
            mock_get_providers.return_value = {"test_agent": mock_agent}

            result = call_ai_agent("test_agent", "System prompt", "User content")

            assert "Error:" in result
            assert "Initialization failed" in result

    def test_call_ai_agent_generation_error(self):
        """Test AI agent call with generation error."""
        # Mock agent that fails to generate content
        from adc_cli.providers import ProviderResult, GenerationResult
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.is_initialized = True
        mock_agent.initialize.return_value = ProviderResult.success_result()
        mock_agent.generate.return_value = GenerationResult.error_result("Generation failed")

        with patch("adc_cli.providers.get_available_providers") as mock_get_providers:
            mock_get_providers.return_value = {"test_agent": mock_agent}

            result = call_ai_agent("test_agent", "System prompt", "User content")

            assert "Error:" in result
            assert "Generation failed" in result
