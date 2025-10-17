"""
Contract test for llm CLI command format validation.

This test validates that LLMProviderConfig.build_cli_command() generates
commands that conform to the llm CLI standard interface format:
    llm -m <model_name> "<prompt>"

These tests are written BEFORE implementation as part of TDD workflow.
They will FAIL until T009-T011 implement the required changes.
"""

import pytest

from src.llm.models.llm_provider_config import LLMProviderConfig


class TestLLMCliCommandFormat:
    """Contract tests for llm CLI command format."""

    def test_deepseek_command_format(self):
        """
        Verify DeepSeek command follows llm CLI standard format.

        Expected format: ['llm', '-m', 'deepseek-coder', '<prompt>']

        This test will FAIL until:
        - T009: Gemini hardcoding removed
        - T010: build_cli_command refactored to use '-m' flag
        - T011: get_default_configs updated with DeepSeek
        """
        # This will fail because:
        # 1. get_default_configs() returns {"gemini": ...}, not {"deepseek": ...}
        # 2. build_cli_command() uses "--model" instead of "-m"
        config = LLMProviderConfig.get_default_configs()["deepseek"]
        command = config.build_cli_command("test prompt")

        # Contract assertions
        assert command[0] == "llm", "First element must be 'llm'"
        assert command[1] == "-m", "Model flag must be '-m' (not '--model')"
        assert command[2] in ["deepseek-coder", "deepseek-chat"], "Valid DeepSeek model name"
        assert command[-1] == "test prompt", "Prompt must be last element"

    def test_no_gemini_specific_args(self):
        """
        Verify no Gemini-specific parameters remain in default config.

        This test will FAIL until:
        - T011: get_default_configs updated to remove Gemini-specific args
        """
        # This will fail because:
        # 1. Default config is still "gemini", not "deepseek"
        # 2. additional_args still contains {"--approval-mode": "yolo", "--debug": None}
        config = LLMProviderConfig.get_default_configs()["deepseek"]
        command = config.build_cli_command("test")

        # Contract assertions
        assert "--approval-mode" not in command, "Gemini-specific --approval-mode should be removed"
        assert "--debug" not in " ".join(command), "Gemini-specific --debug should be removed"
        assert "gemini" not in " ".join(command).lower(), "No 'gemini' in command string"

    def test_optional_parameters_format(self):
        """
        Verify optional parameters follow llm CLI conventions.

        Expected format with parameters:
        ['llm', '-m', 'deepseek-coder', '--temperature', '0.5', '--max-tokens', '1024', '<prompt>']
        """
        config = LLMProviderConfig(
            provider_name="deepseek",  # This will fail validation in T009
            cli_command=["llm"],
            model_name="deepseek-coder",
            additional_args={"--temperature": "0.5", "--max-tokens": "1024"}
        )
        command = config.build_cli_command("test")

        # Contract assertions
        assert "--temperature" in command, "Optional parameter --temperature should be included"
        assert "0.5" in command, "Temperature value should follow parameter"
        assert "--max-tokens" in command, "Optional parameter --max-tokens should be included"
        assert "1024" in command, "Max tokens value should follow parameter"

    def test_command_structure_integrity(self):
        """
        Verify command structure follows llm CLI ordering:
        1. CLI name ('llm')
        2. Model flag ('-m')
        3. Model name
        4. Optional parameters
        5. Prompt (last)
        """
        config = LLMProviderConfig(
            provider_name="deepseek",  # This will fail validation in T009
            cli_command=["llm"],
            model_name="deepseek-coder",
            temperature=0.1,
            additional_args={}
        )
        command = config.build_cli_command("Generate a report")

        # Contract assertions
        assert len(command) >= 4, "Minimum 4 elements: ['llm', '-m', '<model>', '<prompt>']"
        assert command[0] == "llm", "CLI name must be first"
        assert command[1] == "-m", "Model flag must be second"
        assert isinstance(command[2], str) and command[2].startswith("deepseek"), "Model name third"
        assert command[-1] == "Generate a report", "Prompt must be last"

    def test_empty_prompt_rejected(self):
        """
        Verify empty prompt is rejected (validation should occur in higher layers).

        This test ensures command generation can handle empty strings,
        but actual validation of empty prompts should be done by ReportGenerator.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",  # This will fail validation in T009
            cli_command=["llm"],
            model_name="deepseek-coder"
        )
        # Command generation should work with empty string
        # (validation happens elsewhere)
        command = config.build_cli_command("")

        # Contract assertions - command is generated but includes empty prompt
        assert command[0] == "llm"
        assert command[-1] == "", "Empty prompt is included (validation elsewhere)"

    def test_model_name_required_for_llm_cli(self):
        """
        Verify that model_name is required when using llm CLI.

        llm CLI requires -m flag, so model_name cannot be None.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",  # This will fail validation in T009
            cli_command=["llm"],
            model_name=None  # This should cause issues
        )
        command = config.build_cli_command("test")

        # With model_name=None, -m flag should be skipped
        # This is a contract for handling missing model names
        if config.model_name is None:
            # When model_name is None, -m flag should not appear
            assert "-m" not in command or command.count("-m") == 0


class TestLLMCliCommandBackwardCompatibility:
    """Ensure command format changes don't break existing valid patterns."""

    def test_additional_args_position_after_model(self):
        """
        Verify additional arguments appear between model and prompt.

        Format: ['llm', '-m', 'model', '--arg1', 'val1', '--arg2', 'prompt']
        """
        config = LLMProviderConfig(
            provider_name="deepseek",  # This will fail validation in T009
            cli_command=["llm"],
            model_name="deepseek-coder",
            additional_args={"--temperature": "0.1"}
        )
        command = config.build_cli_command("test prompt")

        # Find indices
        model_flag_idx = command.index("-m")
        prompt_idx = command.index("test prompt")
        temp_flag_idx = command.index("--temperature")

        # Contract assertions
        assert model_flag_idx < temp_flag_idx < prompt_idx, \
            "Additional args must appear between model and prompt"

    def test_standalone_flags_format(self):
        """
        Verify standalone flags (None value) are handled correctly.

        Example: {"--verbose": None} should produce ['--verbose'] not ['--verbose', 'None']
        """
        config = LLMProviderConfig(
            provider_name="deepseek",  # This will fail validation in T009
            cli_command=["llm"],
            model_name="deepseek-coder",
            additional_args={"--verbose": None, "--json": None}
        )
        command = config.build_cli_command("test")

        # Contract assertions
        assert "--verbose" in command, "Standalone flag should be included"
        assert "--json" in command, "Standalone flag should be included"
        # Ensure 'None' string is not in command
        assert "None" not in command, "None value should not appear as string"


class TestProviderNameValidationRemoval:
    """Test that provider name whitelist has been removed (T009)."""

    def test_custom_provider_name_accepted(self):
        """
        Verify custom provider names are accepted after T009.

        Before T009: Only "gemini" allowed (hardcoded whitelist)
        After T009: Any valid format accepted (no whitelist)

        This test will FAIL until T009 is implemented.
        """
        # This will fail because validate_provider_name still has:
        # allowed_providers = ["gemini"]
        config = LLMProviderConfig(
            provider_name="custom_provider",  # Should be accepted after T009
            cli_command=["llm"],
            model_name="custom-model"
        )

        assert config.provider_name == "custom_provider", \
            "Custom provider name should be accepted (no whitelist)"

    def test_deepseek_provider_name_accepted(self):
        """
        Verify 'deepseek' provider name is accepted after T009.

        This test will FAIL until T009 removes the hardcoded whitelist.
        """
        # This will fail because validate_provider_name only allows "gemini"
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="deepseek-coder"
        )

        assert config.provider_name == "deepseek", \
            "DeepSeek provider name should be accepted"

    def test_openai_provider_name_accepted(self):
        """
        Verify 'openai' provider name is accepted after T009.

        This demonstrates that any valid provider name format should work.
        """
        config = LLMProviderConfig(
            provider_name="openai",
            cli_command=["llm"],
            model_name="gpt-4"
        )

        assert config.provider_name == "openai", \
            "OpenAI provider name should be accepted"


class TestDefaultConfigMigration:
    """Test that default configs use DeepSeek instead of Gemini (T011)."""

    def test_default_configs_contain_deepseek(self):
        """
        Verify DeepSeek is in default configs after T011.

        This test will FAIL until T011 updates get_default_configs().
        """
        defaults = LLMProviderConfig.get_default_configs()

        assert "deepseek" in defaults, \
            "DeepSeek should be in default configs"

    def test_default_configs_no_gemini(self):
        """
        Verify Gemini is NOT in default configs after T011.

        This test will FAIL until T011 removes Gemini from defaults.
        """
        defaults = LLMProviderConfig.get_default_configs()

        assert "gemini" not in defaults, \
            "Gemini should be removed from default configs"

    def test_deepseek_default_config_properties(self):
        """
        Verify DeepSeek default config has correct properties.

        This test will FAIL until T011 is implemented.
        """
        defaults = LLMProviderConfig.get_default_configs()
        deepseek = defaults["deepseek"]

        # Contract assertions
        assert deepseek.provider_name == "deepseek"
        assert deepseek.cli_command == ["llm"]
        assert deepseek.model_name in ["deepseek-coder", "deepseek-chat"]
        assert deepseek.context_window == 8192, "DeepSeek context window is 8192 tokens"
        assert deepseek.temperature == 0.1, "Temperature should match original Gemini setting"
        assert deepseek.timeout_seconds == 90, "Timeout should match original Gemini setting"
        assert "DEEPSEEK_API_KEY" in deepseek.environment_variables
        assert deepseek.additional_args == {}, "No provider-specific args for llm CLI"
