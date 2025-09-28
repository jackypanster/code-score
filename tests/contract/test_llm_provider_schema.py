"""
Contract test for LLM provider schema validation.

This test validates that LLM provider configuration data conforms to the
defined JSON schema and that validation catches invalid configurations.
"""

import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path


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

    @pytest.fixture
    def valid_openai_config(self):
        """Valid OpenAI provider configuration for testing."""
        return {
            "provider_name": "openai",
            "cli_command": ["openai", "api", "chat.completions.create"],
            "model_name": "gpt-4",
            "timeout_seconds": 60,
            "max_tokens": 8000
        }

    def test_schema_loads_successfully(self, schema):
        """Test that the schema file loads and is valid JSON."""
        assert isinstance(schema, dict)
        assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
        assert schema.get("title") == "LLM Provider Configuration"

    def test_valid_gemini_config_passes(self, schema, valid_gemini_config):
        """Test that a valid Gemini configuration passes validation."""
        validate(instance=valid_gemini_config, schema=schema)

    def test_valid_openai_config_passes(self, schema, valid_openai_config):
        """Test that a valid OpenAI configuration passes validation."""
        validate(instance=valid_openai_config, schema=schema)

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
        valid_names = ["gemini", "openai", "claude", "custom"]

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
        example_models = ["gemini-2.5-pro", "gpt-4", "claude-3-opus"]

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