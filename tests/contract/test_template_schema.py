"""
Contract test for template schema validation.

This test validates that template configuration data conforms to the
defined JSON schema and that validation catches invalid configurations.
"""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate


class TestTemplateSchema:
    """Contract tests for template configuration schema."""

    @pytest.fixture
    def schema(self):
        """Load the template schema."""
        schema_path = Path(__file__).parent.parent.parent / "specs" / "003-step-3-llm" / "contracts" / "template_schema.json"
        with open(schema_path) as f:
            return json.load(f)

    @pytest.fixture
    def valid_template_config(self):
        """Valid template configuration for testing."""
        return {
            "name": "llm_report",
            "file_path": "specs/prompts/llm_report.md",
            "description": "Default LLM report generation template",
            "required_fields": [
                "repository.url",
                "repository.commit_sha",
                "total.score",
                "met_items",
                "unmet_items"
            ],
            "content_limits": {
                "evidence_items_per_category": 3,
                "max_evidence_length": 500,
                "max_total_context": 30000
            }
        }

    def test_schema_loads_successfully(self, schema):
        """Test that the schema file loads and is valid JSON."""
        assert isinstance(schema, dict)
        assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
        assert schema.get("title") == "Report Template Configuration"

    def test_valid_template_config_passes(self, schema, valid_template_config):
        """Test that a valid template configuration passes validation."""
        # This should not raise any exceptions
        validate(instance=valid_template_config, schema=schema)

    def test_missing_required_fields_fail(self, schema):
        """Test that configurations missing required fields fail validation."""
        invalid_configs = [
            {},  # Missing everything
            {"name": "test"},  # Missing file_path, description, required_fields
            {
                "name": "test",
                "file_path": "test.md",
                "description": "test"
                # Missing required_fields
            }
        ]

        for config in invalid_configs:
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_invalid_name_pattern_fails(self, schema, valid_template_config):
        """Test that invalid name patterns fail validation."""
        invalid_names = [
            "invalid name with spaces",
            "invalid@name",
            "invalid/name",
            ""
        ]

        for invalid_name in invalid_names:
            config = valid_template_config.copy()
            config["name"] = invalid_name
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_invalid_file_path_pattern_fails(self, schema, valid_template_config):
        """Test that non-markdown file paths fail validation."""
        invalid_paths = [
            "template.txt",
            "template",
            "template.json",
            ""
        ]

        for invalid_path in invalid_paths:
            config = valid_template_config.copy()
            config["file_path"] = invalid_path
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_invalid_required_fields_fail(self, schema, valid_template_config):
        """Test that invalid required field patterns fail validation."""
        invalid_field_configs = [
            ["123invalid"],  # Starts with number
            ["invalid-field"],  # Contains hyphen
            [""],  # Empty string
            ["field with spaces"],  # Contains spaces
        ]

        for invalid_fields in invalid_field_configs:
            config = valid_template_config.copy()
            config["required_fields"] = invalid_fields
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_content_limits_validation(self, schema, valid_template_config):
        """Test content limits validation rules."""
        # Test valid limits
        valid_limits = {
            "evidence_items_per_category": 5,
            "max_evidence_length": 1000,
            "max_total_context": 50000
        }
        config = valid_template_config.copy()
        config["content_limits"] = valid_limits
        validate(instance=config, schema=schema)

        # Test invalid limits (below minimum)
        invalid_limits = [
            {"evidence_items_per_category": 0},  # Below minimum
            {"max_evidence_length": 50},  # Below minimum
            {"max_total_context": 500}  # Below minimum
        ]

        for invalid_limit in invalid_limits:
            config = valid_template_config.copy()
            config["content_limits"].update(invalid_limit)
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_content_limits_maximum_values(self, schema, valid_template_config):
        """Test content limits maximum value validation."""
        # Test values above maximum
        invalid_limits = [
            {"evidence_items_per_category": 15},  # Above maximum
            {"max_evidence_length": 10000},  # Above maximum
            {"max_total_context": 200000}  # Above maximum
        ]

        for invalid_limit in invalid_limits:
            config = valid_template_config.copy()
            config["content_limits"].update(invalid_limit)
            with pytest.raises(ValidationError):
                validate(instance=config, schema=schema)

    def test_description_max_length(self, schema, valid_template_config):
        """Test that description has maximum length limit."""
        config = valid_template_config.copy()
        config["description"] = "x" * 201  # Exceeds 200 character limit

        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_no_additional_properties(self, schema, valid_template_config):
        """Test that additional properties are not allowed."""
        config = valid_template_config.copy()
        config["unexpected_field"] = "should not be allowed"

        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_content_limits_no_additional_properties(self, schema, valid_template_config):
        """Test that content_limits doesn't allow additional properties."""
        config = valid_template_config.copy()
        config["content_limits"]["unexpected_limit"] = 100

        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)
