"""
Contract test for generated report schema validation.

This test validates that generated report output data conforms to the
defined JSON schema and that validation catches invalid report formats.
"""

import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path
from datetime import datetime


class TestGeneratedReportSchema:
    """Contract tests for generated report output schema."""

    @pytest.fixture
    def schema(self):
        """Load the generated report schema."""
        schema_path = Path(__file__).parent.parent.parent / "specs" / "003-step-3-llm" / "contracts" / "generated_report_schema.json"
        with open(schema_path) as f:
            return json.load(f)

    @pytest.fixture
    def valid_generated_report(self):
        """Valid generated report for testing."""
        return {
            "content": "# AI Code Review Judgement Summary\n\nThis is a comprehensive report analyzing the code quality...",
            "template_used": {
                "name": "llm_report",
                "file_path": "specs/prompts/llm_report.md"
            },
            "generation_timestamp": "2025-09-27T10:30:00Z",
            "provider_used": {
                "provider_name": "gemini",
                "model_name": "gemini-2.5-pro",
                "api_duration_seconds": 12.5
            },
            "truncation_applied": {
                "evidence_truncated": True,
                "items_removed": 5,
                "original_length": 15000,
                "final_length": 12000
            },
            "input_metadata": {
                "score_input_path": "output/score_input.json",
                "repository_url": "https://github.com/user/repository.git",
                "total_score": 67.5
            }
        }

    def test_schema_loads_successfully(self, schema):
        """Test that the schema file loads and is valid JSON."""
        assert isinstance(schema, dict)
        assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
        assert schema.get("title") == "Generated Report Output"

    def test_valid_generated_report_passes(self, schema, valid_generated_report):
        """Test that a valid generated report passes validation."""
        validate(instance=valid_generated_report, schema=schema)

    def test_missing_required_fields_fail(self, schema):
        """Test that reports missing required fields fail validation."""
        invalid_reports = [
            {},  # Missing everything
            {"content": "test"},  # Missing other required fields
            {
                "content": "test",
                "template_used": {"name": "test", "file_path": "test.md"}
                # Missing generation_timestamp, provider_used, etc.
            }
        ]

        for report in invalid_reports:
            with pytest.raises(ValidationError):
                validate(instance=report, schema=schema)

    def test_content_minimum_length(self, schema, valid_generated_report):
        """Test that content has minimum length requirement."""
        report = valid_generated_report.copy()
        report["content"] = "x" * 99  # Below 100 character minimum

        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)

        # Test that 100 characters passes
        report["content"] = "x" * 100
        validate(instance=report, schema=schema)

    def test_template_used_validation(self, schema, valid_generated_report):
        """Test template_used object validation."""
        # Test missing required fields in template_used
        invalid_templates = [
            {},  # Missing both fields
            {"name": "test"},  # Missing file_path
            {"file_path": "test.md"}  # Missing name
        ]

        for invalid_template in invalid_templates:
            report = valid_generated_report.copy()
            report["template_used"] = invalid_template
            with pytest.raises(ValidationError):
                validate(instance=report, schema=schema)

        # Test additional properties not allowed
        report = valid_generated_report.copy()
        report["template_used"]["unexpected_field"] = "not allowed"
        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)

    def test_generation_timestamp_format(self, schema, valid_generated_report):
        """Test that generation_timestamp follows ISO date-time format."""
        # Test valid ISO 8601 formats
        valid_timestamps = [
            "2025-09-27T10:30:00Z",
            "2025-09-27T10:30:00.123Z",
            "2025-09-27T10:30:00+00:00",
            "2025-09-27T10:30:00-05:00"
        ]

        for timestamp in valid_timestamps:
            report = valid_generated_report.copy()
            report["generation_timestamp"] = timestamp
            validate(instance=report, schema=schema)

        # Test invalid timestamp formats
        invalid_timestamps = [
            "2025-09-27",  # Date only
            "10:30:00",  # Time only
            "2025/09/27 10:30:00",  # Wrong format
            "invalid-date",  # Not a date
            ""  # Empty string
        ]

        for timestamp in invalid_timestamps:
            report = valid_generated_report.copy()
            report["generation_timestamp"] = timestamp
            with pytest.raises(ValidationError):
                validate(instance=report, schema=schema)

    def test_provider_used_validation(self, schema, valid_generated_report):
        """Test provider_used object validation."""
        # Test missing required fields
        invalid_providers = [
            {},  # Missing both required fields
            {"provider_name": "gemini"},  # Missing model_name
            {"model_name": "gemini-2.5-pro"}  # Missing provider_name
        ]

        for invalid_provider in invalid_providers:
            report = valid_generated_report.copy()
            report["provider_used"] = invalid_provider
            with pytest.raises(ValidationError):
                validate(instance=report, schema=schema)

        # Test api_duration_seconds validation
        report = valid_generated_report.copy()
        report["provider_used"]["api_duration_seconds"] = -1  # Negative not allowed
        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)

        # Test valid api_duration_seconds
        valid_durations = [0, 0.5, 1.0, 30.5, 120.0]
        for duration in valid_durations:
            report = valid_generated_report.copy()
            report["provider_used"]["api_duration_seconds"] = duration
            validate(instance=report, schema=schema)

    def test_truncation_applied_validation(self, schema, valid_generated_report):
        """Test truncation_applied object validation."""
        # Test missing required fields
        invalid_truncations = [
            {},  # Missing required fields
            {"evidence_truncated": True},  # Missing items_removed
            {"items_removed": 5}  # Missing evidence_truncated
        ]

        for invalid_truncation in invalid_truncations:
            report = valid_generated_report.copy()
            report["truncation_applied"] = invalid_truncation
            with pytest.raises(ValidationError):
                validate(instance=report, schema=schema)

        # Test invalid values
        report = valid_generated_report.copy()
        report["truncation_applied"]["items_removed"] = -1  # Negative not allowed
        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)

        report["truncation_applied"]["original_length"] = -1  # Negative not allowed
        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)

    def test_input_metadata_validation(self, schema, valid_generated_report):
        """Test input_metadata object validation."""
        # Test missing required fields
        invalid_metadata = [
            {},  # Missing all required fields
            {"score_input_path": "test.json"},  # Missing repository_url
            {"repository_url": "https://github.com/test/repo.git"}  # Missing score_input_path
        ]

        for invalid_meta in invalid_metadata:
            report = valid_generated_report.copy()
            report["input_metadata"] = invalid_meta
            with pytest.raises(ValidationError):
                validate(instance=report, schema=schema)

        # Test repository_url format validation
        invalid_urls = [
            "not-a-url",
            "ftp://invalid.com",
            "github.com/user/repo",  # Missing protocol
            ""
        ]

        for invalid_url in invalid_urls:
            report = valid_generated_report.copy()
            report["input_metadata"]["repository_url"] = invalid_url
            with pytest.raises(ValidationError):
                validate(instance=report, schema=schema)

        # Test total_score validation
        invalid_scores = [-1, 101, 150]  # Outside 0-100 range
        for score in invalid_scores:
            report = valid_generated_report.copy()
            report["input_metadata"]["total_score"] = score
            with pytest.raises(ValidationError):
                validate(instance=report, schema=schema)

        # Test valid scores
        valid_scores = [0, 0.5, 50, 67.5, 100]
        for score in valid_scores:
            report = valid_generated_report.copy()
            report["input_metadata"]["total_score"] = score
            validate(instance=report, schema=schema)

    def test_no_additional_properties(self, schema, valid_generated_report):
        """Test that additional properties are not allowed at root level."""
        report = valid_generated_report.copy()
        report["unexpected_field"] = "should not be allowed"

        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)

    def test_optional_fields_can_be_omitted(self, schema, valid_generated_report):
        """Test that optional fields can be omitted."""
        # Remove optional fields
        report = valid_generated_report.copy()
        del report["provider_used"]["api_duration_seconds"]
        del report["truncation_applied"]["original_length"]
        del report["truncation_applied"]["final_length"]
        del report["input_metadata"]["total_score"]

        validate(instance=report, schema=schema)

    def test_minimal_valid_report(self, schema):
        """Test a minimal valid report with only required fields."""
        minimal_report = {
            "content": "x" * 100,  # Minimum length
            "template_used": {
                "name": "test",
                "file_path": "test.md"
            },
            "generation_timestamp": "2025-09-27T10:30:00Z",
            "provider_used": {
                "provider_name": "gemini",
                "model_name": "gemini-2.5-pro"
            },
            "truncation_applied": {
                "evidence_truncated": False,
                "items_removed": 0
            },
            "input_metadata": {
                "score_input_path": "test.json",
                "repository_url": "https://github.com/test/repo.git"
            }
        }

        validate(instance=minimal_report, schema=schema)