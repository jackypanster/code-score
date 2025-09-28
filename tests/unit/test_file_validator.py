"""
Unit tests for file validator module.

This module contains unit tests for the file validation utilities,
focusing on isolated testing of individual validation functions.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from tests.smoke.file_validator import (
    validate_output_files,
    validate_single_file,
    validate_json_schema,
    validate_submission_json,
    validate_score_input_json,
    validate_markdown_file,
    get_output_file_summary,
    cleanup_invalid_output_files,
    FileValidationError
)
from tests.smoke.models import OutputArtifact, ValidationResult


class TestFileValidator:
    """Unit tests for file validation functions."""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    @pytest.fixture
    def sample_json_data(self):
        """Sample JSON data for testing."""
        return {
            "test": "data",
            "number": 42,
            "boolean": True,
            "nested": {
                "key": "value"
            }
        }

    @pytest.fixture
    def sample_markdown_content(self):
        """Sample Markdown content for testing."""
        return """# Test Markdown

This is a test markdown file with content.

## Section 2

- List item 1
- List item 2

### Subsection

Some more content here.
"""

    def test_validate_single_file_json_valid(self, temp_output_dir, sample_json_data):
        """Test validation of valid JSON file."""
        json_file = temp_output_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(sample_json_data, f)

        artifact = validate_single_file(json_file, "test.json")

        assert artifact.file_exists is True
        assert artifact.content_valid is True
        assert artifact.file_size_bytes > 0
        assert artifact.last_modified is not None

    def test_validate_single_file_json_invalid(self, temp_output_dir):
        """Test validation of invalid JSON file."""
        json_file = temp_output_dir / "invalid.json"
        json_file.write_text('{"invalid": json}')

        artifact = validate_single_file(json_file, "invalid.json")

        assert artifact.file_exists is True
        assert artifact.content_valid is False

    def test_validate_single_file_markdown_valid(self, temp_output_dir, sample_markdown_content):
        """Test validation of valid Markdown file."""
        md_file = temp_output_dir / "test.md"
        md_file.write_text(sample_markdown_content)

        artifact = validate_single_file(md_file, "test.md")

        assert artifact.file_exists is True
        assert artifact.content_valid is True

    def test_validate_single_file_markdown_empty(self, temp_output_dir):
        """Test validation of empty Markdown file."""
        md_file = temp_output_dir / "empty.md"
        md_file.write_text("")

        artifact = validate_single_file(md_file, "empty.md")

        assert artifact.file_exists is True
        assert artifact.content_valid is False

    def test_validate_single_file_missing(self, temp_output_dir):
        """Test validation of missing file."""
        missing_file = temp_output_dir / "missing.json"

        artifact = validate_single_file(missing_file, "missing.json")

        assert artifact.file_exists is False
        assert artifact.content_valid is False
        assert artifact.file_size_bytes is None

    def test_validate_output_files_all_valid(self, temp_output_dir, sample_json_data, sample_markdown_content):
        """Test validation when all output files are valid."""
        # Create all expected files
        submission_file = temp_output_dir / "submission.json"
        with open(submission_file, 'w') as f:
            json.dump(sample_json_data, f)

        score_file = temp_output_dir / "score_input.json"
        with open(score_file, 'w') as f:
            json.dump(sample_json_data, f)

        report_file = temp_output_dir / "evaluation_report.md"
        report_file.write_text(sample_markdown_content)

        result = validate_output_files(temp_output_dir)

        assert result.test_passed is True
        assert result.all_files_present is True
        assert len(result.output_files) == 3
        assert all(artifact.file_exists for artifact in result.output_files)
        assert all(artifact.content_valid for artifact in result.output_files)

    def test_validate_output_files_missing(self, temp_output_dir):
        """Test validation when output files are missing."""
        result = validate_output_files(temp_output_dir)

        assert result.test_passed is False
        assert result.all_files_present is False
        assert len(result.output_files) == 3
        assert all(not artifact.file_exists for artifact in result.output_files)

        missing_files = result.get_missing_files()
        assert len(missing_files) == 3
        assert "submission.json" in missing_files
        assert "score_input.json" in missing_files
        assert "evaluation_report.md" in missing_files

    def test_validate_output_files_partial(self, temp_output_dir, sample_json_data):
        """Test validation when some files are present and some missing."""
        # Create only one file
        submission_file = temp_output_dir / "submission.json"
        with open(submission_file, 'w') as f:
            json.dump(sample_json_data, f)

        result = validate_output_files(temp_output_dir)

        assert result.test_passed is False
        assert result.all_files_present is False

        missing_files = result.get_missing_files()
        assert len(missing_files) == 2
        assert "score_input.json" in missing_files
        assert "evaluation_report.md" in missing_files

    def test_validate_json_schema_basic(self, temp_output_dir):
        """Test basic JSON schema validation."""
        valid_data = {"key": "value", "number": 42}
        json_file = temp_output_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(valid_data, f)

        is_valid = validate_json_schema(json_file)
        assert is_valid is True

    def test_validate_json_schema_with_requirements(self, temp_output_dir):
        """Test JSON schema validation with requirements."""
        valid_data = {"required_key": "value", "number": 42}
        json_file = temp_output_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(valid_data, f)

        requirements = {"required_key": str, "number": int}
        is_valid = validate_json_schema(json_file, requirements)
        assert is_valid is True

    def test_validate_json_schema_missing_key(self, temp_output_dir):
        """Test JSON schema validation with missing required key."""
        valid_data = {"number": 42}
        json_file = temp_output_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(valid_data, f)

        requirements = {"required_key": str, "number": int}
        is_valid = validate_json_schema(json_file, requirements)
        assert is_valid is False

    def test_validate_json_schema_wrong_type(self, temp_output_dir):
        """Test JSON schema validation with wrong data type."""
        valid_data = {"required_key": 123, "number": 42}  # string expected, int provided
        json_file = temp_output_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(valid_data, f)

        requirements = {"required_key": str, "number": int}
        is_valid = validate_json_schema(json_file, requirements)
        assert is_valid is False

    def test_validate_submission_json_valid(self, temp_output_dir):
        """Test validation of valid submission.json structure."""
        valid_data = {
            "schema_version": "1.0.0",
            "repository": {"url": "test"},
            "metrics": {"code_quality": {}},
            "execution": {"start_time": "2023-01-01"}
        }
        json_file = temp_output_dir / "submission.json"
        with open(json_file, 'w') as f:
            json.dump(valid_data, f)

        is_valid = validate_submission_json(json_file)
        assert is_valid is True

    def test_validate_submission_json_invalid(self, temp_output_dir):
        """Test validation of invalid submission.json structure."""
        invalid_data = {
            "schema_version": "1.0.0",
            # Missing required keys
        }
        json_file = temp_output_dir / "submission.json"
        with open(json_file, 'w') as f:
            json.dump(invalid_data, f)

        is_valid = validate_submission_json(json_file)
        assert is_valid is False

    def test_validate_score_input_json_valid(self, temp_output_dir):
        """Test validation of valid score_input.json structure."""
        valid_data = {
            "evaluation_result": {"total_score": 85},
            "repository_info": {"url": "test"}
        }
        json_file = temp_output_dir / "score_input.json"
        with open(json_file, 'w') as f:
            json.dump(valid_data, f)

        is_valid = validate_score_input_json(json_file)
        assert is_valid is True

    def test_validate_score_input_json_invalid(self, temp_output_dir):
        """Test validation of invalid score_input.json structure."""
        invalid_data = {
            "evaluation_result": {"total_score": 85},
            # Missing repository_info
        }
        json_file = temp_output_dir / "score_input.json"
        with open(json_file, 'w') as f:
            json.dump(invalid_data, f)

        is_valid = validate_score_input_json(json_file)
        assert is_valid is False

    def test_validate_markdown_file_valid(self, temp_output_dir, sample_markdown_content):
        """Test validation of valid Markdown file."""
        md_file = temp_output_dir / "test.md"
        md_file.write_text(sample_markdown_content)

        is_valid = validate_markdown_file(md_file)
        assert is_valid is True

    def test_validate_markdown_file_empty(self, temp_output_dir):
        """Test validation of empty Markdown file."""
        md_file = temp_output_dir / "empty.md"
        md_file.write_text("")

        is_valid = validate_markdown_file(md_file)
        assert is_valid is False

    def test_validate_markdown_file_no_headers(self, temp_output_dir):
        """Test validation of Markdown file without headers."""
        md_file = temp_output_dir / "no_headers.md"
        md_file.write_text("Just plain text without any headers.")

        is_valid = validate_markdown_file(md_file)
        assert is_valid is False

    def test_validate_markdown_file_with_newlines(self, temp_output_dir):
        """Test validation of Markdown file with newlines (should pass)."""
        md_file = temp_output_dir / "with_newlines.md"
        md_file.write_text("# Header\n\nThis is content with newlines.\n\n## Another header\n")

        is_valid = validate_markdown_file(md_file)
        assert is_valid is True

    def test_get_output_file_summary_complete(self, temp_output_dir, sample_json_data, sample_markdown_content):
        """Test getting summary when all files are present."""
        # Create all files
        submission_file = temp_output_dir / "submission.json"
        with open(submission_file, 'w') as f:
            json.dump(sample_json_data, f)

        score_file = temp_output_dir / "score_input.json"
        with open(score_file, 'w') as f:
            json.dump(sample_json_data, f)

        report_file = temp_output_dir / "evaluation_report.md"
        report_file.write_text(sample_markdown_content)

        summary = get_output_file_summary(temp_output_dir)

        assert summary["directory_exists"] is True
        assert summary["all_files_present"] is True
        assert summary["all_files_valid"] is True
        assert summary["total_size_bytes"] > 0
        assert len(summary["files"]) == 3

        for filename in ["submission.json", "score_input.json", "evaluation_report.md"]:
            assert filename in summary["files"]
            assert summary["files"][filename]["exists"] is True
            assert summary["files"][filename]["valid_content"] is True

    def test_get_output_file_summary_missing(self, temp_output_dir):
        """Test getting summary when files are missing."""
        summary = get_output_file_summary(temp_output_dir)

        assert summary["directory_exists"] is True
        assert summary["all_files_present"] is False
        assert summary["all_files_valid"] is False
        assert summary["total_size_bytes"] == 0

        for filename in ["submission.json", "score_input.json", "evaluation_report.md"]:
            assert summary["files"][filename]["exists"] is False

    def test_cleanup_invalid_output_files(self, temp_output_dir):
        """Test cleanup of invalid output files."""
        # Create valid file
        valid_data = {"test": "data"}
        valid_file = temp_output_dir / "submission.json"
        with open(valid_file, 'w') as f:
            json.dump(valid_data, f)

        # Create invalid file
        invalid_file = temp_output_dir / "score_input.json"
        invalid_file.write_text('{"invalid": json}')

        # Cleanup
        cleaned_files = cleanup_invalid_output_files(temp_output_dir)

        # Check results
        assert len(cleaned_files) == 1
        assert "score_input.json" in cleaned_files
        assert valid_file.exists()  # Valid file should remain
        assert not invalid_file.exists()  # Invalid file should be removed

    def test_cleanup_invalid_output_files_no_directory(self, tmp_path):
        """Test cleanup when output directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"

        cleaned_files = cleanup_invalid_output_files(nonexistent_dir)

        assert len(cleaned_files) == 0


class TestOutputArtifactModel:
    """Unit tests for OutputArtifact model."""

    def test_output_artifact_creation(self, tmp_path):
        """Test creating OutputArtifact instance."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        artifact = OutputArtifact(
            file_path=test_file,
            expected_name="test.json"
        )

        assert artifact.file_path == test_file
        assert artifact.expected_name == "test.json"
        assert artifact.file_exists is True
        assert artifact.file_size_bytes > 0
        assert artifact.content_valid is True

    def test_output_artifact_missing_file(self, tmp_path):
        """Test OutputArtifact with missing file."""
        missing_file = tmp_path / "missing.json"

        artifact = OutputArtifact(
            file_path=missing_file,
            expected_name="missing.json"
        )

        assert artifact.file_exists is False
        assert artifact.file_size_bytes is None
        assert artifact.content_valid is False

    def test_output_artifact_refresh(self, tmp_path):
        """Test refreshing OutputArtifact metadata."""
        test_file = tmp_path / "test.json"

        # Create artifact before file exists
        artifact = OutputArtifact(
            file_path=test_file,
            expected_name="test.json"
        )

        assert artifact.file_exists is False

        # Create file and refresh
        test_file.write_text('{"test": "data"}')
        artifact.refresh()

        assert artifact.file_exists is True
        assert artifact.content_valid is True

    def test_output_artifact_validation_empty_name(self, tmp_path):
        """Test OutputArtifact validation with empty name."""
        test_file = tmp_path / "test.json"

        with pytest.raises(ValueError) as exc_info:
            OutputArtifact(
                file_path=test_file,
                expected_name=""
            )

        assert "expected_name must not be empty" in str(exc_info.value)