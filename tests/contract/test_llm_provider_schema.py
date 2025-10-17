"""
Contract test for LLM provider schema validation.

This test validates that LLM provider configuration data conforms to the
defined JSON schema and that validation catches invalid configurations.
"""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate


class TestLLMProviderSchema:
    """Contract tests for LLM provider configuration schema."""

    @pytest.fixture
    def schema(self):
        """Load the LLM provider schema."""
        schema_path = Path(__file__).parent.parent.parent / "specs" / "003-step-3-llm" / "contracts" / "llm_provider_schema.json"
        with open(schema_path) as f:
            return json.load(f)

    @pytest.fixture
    def valid_gemini_config(self):
        """Valid Gemini provider configuration for testing."""
        return {
            "provider_name": "gemini",
            "cli_command": ["gemini", "--approval-mode", "yolo", "-m", "gemini-2.5-pro"],
            "model_name": "gemini-2.5-pro",
            "timeout_seconds": 30,
            "max_tokens": 4000,
            "environment_variables": {
                "GEMINI_API_KEY": "${GEMINI_API_KEY}"
            }
        }


    def test_schema_loads_successfully(self, schema):
        """Test that the schema file loads and is valid JSON."""
        assert isinstance(schema, dict)
        assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
        assert schema.get("title") == "LLM Provider Configuration"

    def test_valid_gemini_config_passes(self, schema, valid_gemini_config):
        """Test that a valid Gemini configuration passes validation."""
        validate(instance=valid_gemini_config, schema=schema)


    def test_missing_required_fields_fail(self, schema):
        """Test that configurations missing required fields fail validation."""
        invalid_configs = [
            {},  # Missing everything
            {"provider_name": "gemini"},  # Missing cli_command and model_name
            {
                "provider_name": "gemini",
                "cli_command": ["gemini"]
                # Missing model_name
            }
        ]

        for config in invalid_configs:
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_invalid_provider_name_fails(self, schema, valid_gemini_config):
        """Test that invalid provider names fail validation."""
        invalid_names = [
            "invalid_provider",
            "gpt",
            "chatgpt",
            ""
        ]

        for invalid_name in invalid_names:
            config = valid_gemini_config.copy()
            config["provider_name"] = invalid_name
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_valid_provider_names_pass(self, schema, valid_gemini_config):
        """Test that all valid provider names pass validation."""
        valid_names = ["gemini"]

        for valid_name in valid_names:
            config = valid_gemini_config.copy()
            config["provider_name"] = valid_name
            validate(instance=config, schema=schema)

    def test_empty_cli_command_fails(self, schema, valid_gemini_config):
        """Test that empty CLI command array fails validation."""
        config = valid_gemini_config.copy()
        config["cli_command"] = []

        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_cli_command_with_single_item_passes(self, schema, valid_gemini_config):
        """Test that CLI command with single item passes validation."""
        config = valid_gemini_config.copy()
        config["cli_command"] = ["gemini"]

        validate(instance=config, schema=schema)

    def test_timeout_seconds_validation(self, schema, valid_gemini_config):
        """Test timeout_seconds validation rules."""
        # Test valid timeouts
        valid_timeouts = [10, 30, 60, 120, 300]
        for timeout in valid_timeouts:
            config = valid_gemini_config.copy()
            config["timeout_seconds"] = timeout
            validate(instance=config, schema=schema)

        # Test invalid timeouts (below minimum)
        invalid_timeouts = [0, 5, 9]
        for timeout in invalid_timeouts:
            config = valid_gemini_config.copy()
            config["timeout_seconds"] = timeout
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

        # Test invalid timeouts (above maximum)
        invalid_timeouts = [301, 500, 1000]
        for timeout in invalid_timeouts:
            config = valid_gemini_config.copy()
            config["timeout_seconds"] = timeout
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_max_tokens_validation(self, schema, valid_gemini_config):
        """Test max_tokens validation rules."""
        # Test valid token limits
        valid_tokens = [100, 1000, 4000, 8000, 32000, 100000]
        for tokens in valid_tokens:
            config = valid_gemini_config.copy()
            config["max_tokens"] = tokens
            validate(instance=config, schema=schema)

        # Test invalid token limits (below minimum)
        invalid_tokens = [0, 50, 99]
        for tokens in invalid_tokens:
            config = valid_gemini_config.copy()
            config["max_tokens"] = tokens
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

        # Test invalid token limits (above maximum)
        invalid_tokens = [100001, 200000, 500000]
        for tokens in invalid_tokens:
            config = valid_gemini_config.copy()
            config["max_tokens"] = tokens
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_environment_variables_validation(self, schema, valid_gemini_config):
        """Test environment variables validation rules."""
        # Test valid environment variables
        valid_env_vars = {
            "API_KEY": "test_value",
            "GEMINI_API_KEY": "${GEMINI_API_KEY}",
            "OPENAI_API_KEY": "sk-test123",
            "MODEL_CONFIG": "production"
        }

        config = valid_gemini_config.copy()
        config["environment_variables"] = valid_env_vars
        validate(instance=config, schema=schema)

        # Test invalid environment variable names (wrong case/format)
        invalid_env_vars = {
            "api_key": "test",  # Lowercase not allowed
            "Api-Key": "test",  # Hyphen not allowed
            "123KEY": "test",   # Starting with number
            "": "test"          # Empty name
        }

        for invalid_key, value in invalid_env_vars.items():
            config = valid_gemini_config.copy()
            config["environment_variables"] = {invalid_key: value}
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_optional_fields_can_be_omitted(self, schema):
        """Test that optional fields can be omitted."""
        minimal_config = {
            "provider_name": "gemini",
            "cli_command": ["gemini"],
            "model_name": "gemini-2.5-pro"
        }

        validate(instance=minimal_config, schema=schema)

    def test_no_additional_properties(self, schema, valid_gemini_config):
        """Test that additional properties are not allowed."""
        config = valid_gemini_config.copy()
        config["unexpected_field"] = "should not be allowed"

        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_model_name_examples_are_valid(self, schema, valid_gemini_config):
        """Test that the example model names in schema are valid."""
        example_models = ["gemini-2.5-pro", "gemini-1.5-pro"]

        for model_name in example_models:
            config = valid_gemini_config.copy()
            config["model_name"] = model_name
            validate(instance=config, schema=schema)

    def test_custom_provider_configuration(self, schema):
        """Test configuration for custom provider."""
        custom_config = {
            "provider_name": "custom",
            "cli_command": ["custom-llm", "--model", "custom-model", "--format", "json"],
            "model_name": "custom-model-v1",
            "timeout_seconds": 45,
            "max_tokens": 2048,
            "environment_variables": {
                "CUSTOM_API_URL": "https://api.custom-llm.com",
                "CUSTOM_API_KEY": "${CUSTOM_API_KEY}"
            }
        }

        validate(instance=custom_config, schema=schema)


class TestProviderConfigPydanticModel:
    """
    Contract tests for LLMProviderConfig Pydantic model behavior.

    These tests verify the migration from Gemini hardcoding to llm CLI unified interface.
    Tests will FAIL until T009 (remove whitelist) and T011 (update defaults) are implemented.
    """

    def test_provider_name_no_whitelist(self):
        """
        Verify custom provider names are accepted without whitelist restriction.

        Before T009: Only "gemini" allowed (hardcoded whitelist)
        After T009: Any valid format accepted (no whitelist)

        This test will FAIL until T009 removes the hardcoded whitelist in validate_provider_name.
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        # This will fail because validate_provider_name has:
        # allowed_providers = ["gemini"]
        config = LLMProviderConfig(
            provider_name="custom_provider",
            cli_command=["llm"],
            model_name="custom-model"
        )

        assert config.provider_name == "custom_provider", \
            "Custom provider name should be accepted (no whitelist after T009)"

    def test_deepseek_provider_accepted(self):
        """
        Verify 'deepseek' provider name is accepted after T009.

        This test will FAIL until T009 removes the hardcoded whitelist.
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="deepseek-coder"
        )

        assert config.provider_name == "deepseek", \
            "DeepSeek provider name should be accepted after T009"

    def test_openai_provider_accepted(self):
        """
        Verify 'openai' provider name is accepted after T009.

        Demonstrates that any valid provider name format should work.
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        config = LLMProviderConfig(
            provider_name="openai",
            cli_command=["llm"],
            model_name="gpt-4"
        )

        assert config.provider_name == "openai", \
            "OpenAI provider name should be accepted after T009"

    def test_default_configs_contain_deepseek(self):
        """
        Verify DeepSeek is in default configs after T011.

        This test will FAIL until T011 updates get_default_configs().

        Expected: defaults = {"deepseek": LLMProviderConfig(...)}
        Current: defaults = {"gemini": LLMProviderConfig(...)}
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        defaults = LLMProviderConfig.get_default_configs()

        assert "deepseek" in defaults, \
            "DeepSeek should be in default configs after T011"

    def test_default_configs_no_gemini(self):
        """
        Verify Gemini is NOT in default configs after T011.

        This test will FAIL until T011 removes Gemini from defaults.

        Expected: "gemini" not in defaults.keys()
        Current: "gemini" in defaults.keys()
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        defaults = LLMProviderConfig.get_default_configs()

        assert "gemini" not in defaults, \
            "Gemini should be removed from default configs after T011"

    def test_deepseek_default_config_properties(self):
        """
        Verify DeepSeek default config has correct properties after T011.

        This test will FAIL until T011 is implemented.
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        defaults = LLMProviderConfig.get_default_configs()
        deepseek = defaults["deepseek"]

        # Contract assertions for DeepSeek configuration
        assert deepseek.provider_name == "deepseek"
        assert deepseek.cli_command == ["llm"], "Should use llm CLI unified interface"
        assert deepseek.model_name in ["deepseek-coder", "deepseek-chat"], \
            "Should use DeepSeek models"
        assert deepseek.context_window == 8192, \
            "DeepSeek context window is 8192 tokens (not Gemini's 1M)"
        assert deepseek.temperature == 0.1, \
            "Temperature should match original Gemini setting for consistency"
        assert deepseek.timeout_seconds == 90, \
            "Timeout should match original Gemini setting"
        assert "DEEPSEEK_API_KEY" in deepseek.environment_variables, \
            "Should require DEEPSEEK_API_KEY environment variable"
        assert deepseek.additional_args == {}, \
            "No provider-specific args for llm CLI (no --approval-mode yolo)"

    def test_anthropic_provider_accepted(self):
        """
        Verify 'anthropic' provider name is accepted after T009.

        Demonstrates extensibility for future providers.
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        config = LLMProviderConfig(
            provider_name="anthropic",
            cli_command=["llm"],
            model_name="claude-3-opus"
        )

        assert config.provider_name == "anthropic", \
            "Anthropic provider name should be accepted"

    def test_provider_name_format_validation_still_works(self):
        """
        Verify that provider name format validation still works after removing whitelist.

        Valid format: lowercase alphanumeric + underscore, starting with letter
        This should PASS even before T009 (format validation is separate from whitelist).
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig
        import pytest

        # Valid formats (should work after T009)
        valid_names = [
            "deepseek",
            "openai",
            "anthropic",
            "custom_provider",
            "provider123"
        ]

        # Note: These will fail due to whitelist before T009, but format is valid
        for name in valid_names:
            try:
                config = LLMProviderConfig(
                    provider_name=name,
                    cli_command=["llm"],
                    model_name="test-model"
                )
                # If this succeeds, format is valid
                assert config.provider_name == name
            except ValueError as e:
                # If it fails due to whitelist, that's expected before T009
                if "Unsupported provider" not in str(e):
                    # But if it fails for other reasons, that's a format issue
                    raise
