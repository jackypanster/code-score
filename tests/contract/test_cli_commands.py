"""
Contract test for CLI commands specification.

This test validates that CLI command specifications conform to the
defined YAML structure and that command definitions are complete and valid.
"""

import yaml
import pytest
from pathlib import Path


class TestCLICommandsSpecification:
    """Contract tests for CLI commands specification."""

    @pytest.fixture
    def cli_spec(self):
        """Load the CLI commands specification."""
        spec_path = Path(__file__).parent.parent.parent / "specs" / "003-step-3-llm" / "contracts" / "cli_commands.yaml"
        with open(spec_path) as f:
            return yaml.safe_load(f)

    def test_specification_loads_successfully(self, cli_spec):
        """Test that the CLI specification file loads and has expected structure."""
        assert isinstance(cli_spec, dict)
        assert "cli_commands" in cli_spec
        assert isinstance(cli_spec["cli_commands"], dict)

    def test_llm_report_command_structure(self, cli_spec):
        """Test that llm_report command has complete specification."""
        commands = cli_spec["cli_commands"]
        assert "llm_report" in commands

        llm_report = commands["llm_report"]

        # Required top-level fields
        assert "description" in llm_report
        assert "command" in llm_report
        assert "arguments" in llm_report
        assert "examples" in llm_report

        # Verify field types
        assert isinstance(llm_report["description"], str)
        assert isinstance(llm_report["command"], str)
        assert isinstance(llm_report["arguments"], list)
        assert isinstance(llm_report["examples"], list)

    def test_llm_report_required_arguments(self, cli_spec):
        """Test that llm_report command has all required arguments."""
        llm_report = cli_spec["cli_commands"]["llm_report"]
        arguments = llm_report["arguments"]

        # Extract argument names
        arg_names = [arg["name"] for arg in arguments]

        # Check for required arguments
        required_args = [
            "score_input_path",
            "prompt",
            "output",
            "provider",
            "verbose"
        ]

        for required_arg in required_args:
            assert required_arg in arg_names, f"Missing required argument: {required_arg}"

    def test_score_input_path_argument(self, cli_spec):
        """Test score_input_path argument specification."""
        llm_report = cli_spec["cli_commands"]["llm_report"]
        arguments = {arg["name"]: arg for arg in llm_report["arguments"]}

        score_input = arguments["score_input_path"]
        assert score_input["type"] == "string"
        assert score_input["required"] is True
        assert "Path to score_input.json file" in score_input["description"]
        assert score_input["validation"] == "file_must_exist"

    def test_prompt_argument(self, cli_spec):
        """Test prompt argument specification."""
        llm_report = cli_spec["cli_commands"]["llm_report"]
        arguments = {arg["name"]: arg for arg in llm_report["arguments"]}

        prompt = arguments["prompt"]
        assert prompt["type"] == "string"
        assert prompt["required"] is False
        assert prompt["default"] == "specs/prompts/llm_report.md"
        assert "Path to prompt template file" in prompt["description"]
        assert prompt["validation"] == "file_must_exist"

    def test_output_argument(self, cli_spec):
        """Test output argument specification."""
        llm_report = cli_spec["cli_commands"]["llm_report"]
        arguments = {arg["name"]: arg for arg in llm_report["arguments"]}

        output = arguments["output"]
        assert output["type"] == "string"
        assert output["required"] is False
        assert output["default"] == "output/final_report.md"
        assert "Output path for generated report" in output["description"]
        assert output["validation"] == "directory_must_exist"


    def test_provider_argument(self, cli_spec):
        """Test provider argument specification."""
        llm_report = cli_spec["cli_commands"]["llm_report"]
        arguments = {arg["name"]: arg for arg in llm_report["arguments"]}

        provider = arguments["provider"]
        assert provider["type"] == "string"
        assert provider["required"] is False
        assert provider["default"] == "gemini"
        assert "LLM provider to use" in provider["description"]
        assert "choices" in provider
        assert isinstance(provider["choices"], list)
        assert "gemini" in provider["choices"]
        assert len(provider["choices"]) == 1  # Only Gemini supported in MVP

    def test_verbose_argument(self, cli_spec):
        """Test verbose argument specification."""
        llm_report = cli_spec["cli_commands"]["llm_report"]
        arguments = {arg["name"]: arg for arg in llm_report["arguments"]}

        verbose = arguments["verbose"]
        assert verbose["type"] == "boolean"
        assert verbose["required"] is False
        assert verbose["default"] is False
        assert "Enable detailed logging" in verbose["description"]

    def test_llm_report_examples(self, cli_spec):
        """Test that llm_report command has comprehensive examples."""
        llm_report = cli_spec["cli_commands"]["llm_report"]
        examples = llm_report["examples"]

        assert len(examples) >= 4, "Should have at least 4 examples"

        # Each example should have description and command
        for example in examples:
            assert "description" in example
            assert "command" in example
            assert isinstance(example["description"], str)
            assert isinstance(example["command"], str)
            assert "code-score llm-report" in example["command"]

        # Check for specific example types
        example_descriptions = [ex["description"] for ex in examples]

        # Should have basic usage example
        assert any("default settings" in desc for desc in example_descriptions)

        # Should have custom template example
        assert any("custom template" in desc or "custom" in desc for desc in example_descriptions)


    def test_analyze_with_llm_command_structure(self, cli_spec):
        """Test that analyze_with_llm command extension is specified."""
        commands = cli_spec["cli_commands"]
        assert "analyze_with_llm" in commands

        analyze_llm = commands["analyze_with_llm"]

        # Required fields
        assert "description" in analyze_llm
        assert "command" in analyze_llm
        assert "new_arguments" in analyze_llm
        assert "examples" in analyze_llm

        # Command should be 'analyze' (extending existing command)
        assert analyze_llm["command"] == "analyze"

    def test_analyze_with_llm_new_arguments(self, cli_spec):
        """Test new arguments for analyze command with LLM support."""
        analyze_llm = cli_spec["cli_commands"]["analyze_with_llm"]
        new_args = analyze_llm["new_arguments"]

        # Extract argument names
        arg_names = [arg["name"] for arg in new_args]

        # Check for expected new arguments
        expected_args = [
            "generate_llm_report",
            "llm_template",
            "llm_provider"
        ]

        for expected_arg in expected_args:
            assert expected_arg in arg_names, f"Missing new argument: {expected_arg}"

    def test_exit_codes_specification(self, cli_spec):
        """Test that exit codes are properly specified."""
        assert "exit_codes" in cli_spec
        exit_codes = cli_spec["exit_codes"]

        # Should have common exit codes
        expected_codes = [0, 1, 2, 3, 4, 5]
        for code in expected_codes:
            assert code in exit_codes or str(code) in exit_codes

        # Exit code 0 should be success
        success_msg = exit_codes.get(0) or exit_codes.get("0")
        assert "Success" in success_msg

    def test_error_handling_specification(self, cli_spec):
        """Test that error handling is properly specified."""
        assert "error_handling" in cli_spec
        error_handling = cli_spec["error_handling"]

        # Should have common error types
        expected_errors = [
            "file_not_found",
            "template_error",
            "llm_provider_error",
            "validation_error"
        ]

        for error_type in expected_errors:
            assert error_type in error_handling

            error_spec = error_handling[error_type]
            assert "message" in error_spec
            assert "suggestion" in error_spec

    def test_command_argument_validation_types(self, cli_spec):
        """Test that all argument types are valid."""
        valid_types = ["string", "boolean", "integer", "float"]

        for command_name, command_spec in cli_spec["cli_commands"].items():
            if "arguments" in command_spec:
                for arg in command_spec["arguments"]:
                    assert arg["type"] in valid_types, f"Invalid type '{arg['type']}' in {command_name}.{arg['name']}"

            if "new_arguments" in command_spec:
                for arg in command_spec["new_arguments"]:
                    assert arg["type"] in valid_types, f"Invalid type '{arg['type']}' in {command_name}.{arg['name']}"

    def test_validation_types_are_consistent(self, cli_spec):
        """Test that validation types are consistent across arguments."""
        valid_validations = [
            "file_must_exist",
            "directory_must_exist",
            "url_format",
            "positive_integer"
        ]

        for command_name, command_spec in cli_spec["cli_commands"].items():
            if "arguments" in command_spec:
                for arg in command_spec["arguments"]:
                    if "validation" in arg:
                        assert arg["validation"] in valid_validations, f"Unknown validation '{arg['validation']}' in {command_name}.{arg['name']}"

    def test_boolean_arguments_have_defaults(self, cli_spec):
        """Test that boolean arguments have explicit default values."""
        for command_name, command_spec in cli_spec["cli_commands"].items():
            if "arguments" in command_spec:
                for arg in command_spec["arguments"]:
                    if arg["type"] == "boolean":
                        assert "default" in arg, f"Boolean argument {command_name}.{arg['name']} missing default value"
                        assert isinstance(arg["default"], bool), f"Boolean argument {command_name}.{arg['name']} default is not boolean"