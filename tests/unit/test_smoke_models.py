"""
Unit tests for smoke test data models.

This module contains unit tests for the data models used in the smoke test suite,
focusing on validation, behavior, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from tests.smoke.models import SmokeTestExecution, OutputArtifact, ValidationResult


class TestSmokeTestExecutionModel:
    """Unit tests for SmokeTestExecution model."""

    @pytest.fixture
    def temp_working_dir(self, tmp_path):
        """Create temporary working directory."""
        return tmp_path

    def test_creation_valid(self, temp_working_dir):
        """Test creating valid SmokeTestExecution instance."""
        start_time = datetime.now()
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=temp_working_dir,
            execution_start_time=start_time
        )

        assert execution.repository_url == "git@github.com:test/repo.git"
        assert execution.working_directory == temp_working_dir
        assert execution.execution_start_time == start_time
        assert execution.execution_end_time is None
        assert execution.pipeline_exit_code is None
        assert execution.pipeline_duration is None

    def test_creation_invalid_empty_url(self, temp_working_dir):
        """Test creating SmokeTestExecution with empty URL."""
        with pytest.raises(ValueError) as exc_info:
            SmokeTestExecution(
                repository_url="",
                working_directory=temp_working_dir,
                execution_start_time=datetime.now()
            )

        assert "repository_url must not be empty" in str(exc_info.value)

    def test_creation_invalid_missing_directory(self):
        """Test creating SmokeTestExecution with missing directory."""
        nonexistent_path = Path("/nonexistent/directory")

        with pytest.raises(ValueError) as exc_info:
            SmokeTestExecution(
                repository_url="git@github.com:test/repo.git",
                working_directory=nonexistent_path,
                execution_start_time=datetime.now()
            )

        assert "working_directory must exist" in str(exc_info.value)

    def test_creation_invalid_end_before_start(self, temp_working_dir):
        """Test creating SmokeTestExecution with end time before start time."""
        start_time = datetime.now()
        end_time = start_time - timedelta(seconds=10)

        with pytest.raises(ValueError) as exc_info:
            SmokeTestExecution(
                repository_url="git@github.com:test/repo.git",
                working_directory=temp_working_dir,
                execution_start_time=start_time,
                execution_end_time=end_time
            )

        assert "execution_end_time must be after execution_start_time" in str(exc_info.value)

    def test_is_complete_false(self, temp_working_dir):
        """Test is_complete property when execution is not complete."""
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=temp_working_dir,
            execution_start_time=datetime.now()
        )

        assert execution.is_complete is False

    def test_is_complete_true(self, temp_working_dir):
        """Test is_complete property when execution is complete."""
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=temp_working_dir,
            execution_start_time=datetime.now(),
            execution_end_time=datetime.now()
        )

        assert execution.is_complete is True

    def test_is_successful_false_incomplete(self, temp_working_dir):
        """Test is_successful property when execution is incomplete."""
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=temp_working_dir,
            execution_start_time=datetime.now()
        )

        assert execution.is_successful is False

    def test_is_successful_false_failed(self, temp_working_dir):
        """Test is_successful property when execution failed."""
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=temp_working_dir,
            execution_start_time=datetime.now(),
            execution_end_time=datetime.now(),
            pipeline_exit_code=1
        )

        assert execution.is_successful is False

    def test_is_successful_true(self, temp_working_dir):
        """Test is_successful property when execution succeeded."""
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=temp_working_dir,
            execution_start_time=datetime.now(),
            execution_end_time=datetime.now(),
            pipeline_exit_code=0
        )

        assert execution.is_successful is True

    def test_mark_completed_success(self, temp_working_dir):
        """Test marking execution as completed successfully."""
        start_time = datetime.now()
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=temp_working_dir,
            execution_start_time=start_time
        )

        execution.mark_completed(0)

        assert execution.is_complete is True
        assert execution.is_successful is True
        assert execution.pipeline_exit_code == 0
        assert execution.execution_end_time is not None
        assert execution.execution_end_time >= start_time
        assert execution.pipeline_duration is not None
        assert execution.pipeline_duration >= 0

    def test_mark_completed_failure(self, temp_working_dir):
        """Test marking execution as completed with failure."""
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=temp_working_dir,
            execution_start_time=datetime.now()
        )

        execution.mark_completed(1)

        assert execution.is_complete is True
        assert execution.is_successful is False
        assert execution.pipeline_exit_code == 1


class TestOutputArtifactModel:
    """Unit tests for OutputArtifact model."""

    def test_creation_valid_existing_file(self, tmp_path):
        """Test creating OutputArtifact with existing valid file."""
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
        assert artifact.last_modified is not None
        assert artifact.content_valid is True

    def test_creation_valid_missing_file(self, tmp_path):
        """Test creating OutputArtifact with missing file."""
        missing_file = tmp_path / "missing.json"

        artifact = OutputArtifact(
            file_path=missing_file,
            expected_name="missing.json"
        )

        assert artifact.file_path == missing_file
        assert artifact.expected_name == "missing.json"
        assert artifact.file_exists is False
        assert artifact.file_size_bytes is None
        assert artifact.last_modified is None
        assert artifact.content_valid is False

    def test_creation_invalid_empty_name(self, tmp_path):
        """Test creating OutputArtifact with empty expected name."""
        test_file = tmp_path / "test.json"

        with pytest.raises(ValueError) as exc_info:
            OutputArtifact(
                file_path=test_file,
                expected_name=""
            )

        assert "expected_name must not be empty" in str(exc_info.value)

    def test_refresh_file_created(self, tmp_path):
        """Test refreshing artifact when file is created."""
        test_file = tmp_path / "test.json"

        artifact = OutputArtifact(
            file_path=test_file,
            expected_name="test.json"
        )

        # Initially file doesn't exist
        assert artifact.file_exists is False

        # Create file and refresh
        test_file.write_text('{"test": "data"}')
        artifact.refresh()

        assert artifact.file_exists is True
        assert artifact.content_valid is True

    def test_refresh_file_deleted(self, tmp_path):
        """Test refreshing artifact when file is deleted."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        artifact = OutputArtifact(
            file_path=test_file,
            expected_name="test.json"
        )

        # Initially file exists
        assert artifact.file_exists is True

        # Delete file and refresh
        test_file.unlink()
        artifact.refresh()

        assert artifact.file_exists is False
        assert artifact.content_valid is False

    def test_validate_json_content_valid(self, tmp_path):
        """Test JSON content validation with valid JSON."""
        json_file = tmp_path / "valid.json"
        json_file.write_text('{"key": "value", "number": 42}')

        artifact = OutputArtifact(
            file_path=json_file,
            expected_name="valid.json"
        )

        assert artifact.content_valid is True

    def test_validate_json_content_invalid(self, tmp_path):
        """Test JSON content validation with invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"key": invalid}')

        artifact = OutputArtifact(
            file_path=json_file,
            expected_name="invalid.json"
        )

        assert artifact.content_valid is False

    def test_validate_markdown_content_valid(self, tmp_path):
        """Test Markdown content validation with valid content."""
        md_file = tmp_path / "valid.md"
        md_file.write_text("# Test\n\nThis is valid markdown.")

        artifact = OutputArtifact(
            file_path=md_file,
            expected_name="valid.md"
        )

        assert artifact.content_valid is True

    def test_validate_markdown_content_empty(self, tmp_path):
        """Test Markdown content validation with empty content."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("")

        artifact = OutputArtifact(
            file_path=md_file,
            expected_name="empty.md"
        )

        assert artifact.content_valid is False

    def test_validate_other_content_readable(self, tmp_path):
        """Test content validation with other file types."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is readable text content.")

        artifact = OutputArtifact(
            file_path=txt_file,
            expected_name="test.txt"
        )

        assert artifact.content_valid is True


class TestValidationResultModel:
    """Unit tests for ValidationResult model."""

    def test_creation_basic(self):
        """Test creating basic ValidationResult instance."""
        result = ValidationResult(
            test_passed=True,
            pipeline_successful=True,
            all_files_present=True,
            execution_summary="Test passed successfully"
        )

        assert result.test_passed is True
        assert result.pipeline_successful is True
        assert result.all_files_present is True
        assert result.execution_summary == "Test passed successfully"
        assert result.error_message is None
        assert result.output_files == []

    def test_creation_auto_correct_inconsistency(self):
        """Test auto-correction of inconsistent test_passed value."""
        result = ValidationResult(
            test_passed=True,  # Inconsistent with pipeline_successful=False
            pipeline_successful=False,
            all_files_present=True,
            execution_summary="Test summary"
        )

        # Should auto-correct to False
        assert result.test_passed is False

    def test_creation_auto_add_error_message(self):
        """Test auto-addition of error message when test fails."""
        result = ValidationResult(
            test_passed=False,
            pipeline_successful=False,
            all_files_present=True,
            execution_summary="Test failed"
        )

        assert result.error_message is not None
        assert "Test failed" in result.error_message

    def test_success_factory_method(self):
        """Test ValidationResult.success factory method."""
        output_files = [
            OutputArtifact(Path("/test/file.json"), "file.json")
        ]

        result = ValidationResult.success(
            execution_summary="All tests passed",
            output_files=output_files,
            pipeline_duration=120.5,
            pipeline_exit_code=0
        )

        assert result.test_passed is True
        assert result.pipeline_successful is True
        assert result.all_files_present is True
        assert result.execution_summary == "All tests passed"
        assert result.output_files == output_files
        assert result.pipeline_duration == 120.5
        assert result.pipeline_exit_code == 0

    def test_pipeline_failure_factory_method(self):
        """Test ValidationResult.pipeline_failure factory method."""
        result = ValidationResult.pipeline_failure(
            error_message="Pipeline execution failed",
            pipeline_exit_code=1,
            pipeline_duration=60.0
        )

        assert result.test_passed is False
        assert result.pipeline_successful is False
        assert result.all_files_present is False
        assert result.execution_summary == "Pipeline execution failed"
        assert result.error_message == "Pipeline execution failed"
        assert result.pipeline_exit_code == 1
        assert result.pipeline_duration == 60.0

    def test_file_validation_failure_factory_method(self):
        """Test ValidationResult.file_validation_failure factory method."""
        output_files = [
            OutputArtifact(Path("/test/file.json"), "file.json")
        ]

        result = ValidationResult.file_validation_failure(
            error_message="Files missing or invalid",
            output_files=output_files,
            pipeline_duration=120.0,
            pipeline_exit_code=0
        )

        assert result.test_passed is False
        assert result.pipeline_successful is True
        assert result.all_files_present is False
        assert result.execution_summary == "Output file validation failed"
        assert result.error_message == "Files missing or invalid"
        assert result.output_files == output_files
        assert result.pipeline_duration == 120.0
        assert result.pipeline_exit_code == 0

    def test_get_failure_type_success(self):
        """Test get_failure_type for successful result."""
        result = ValidationResult(
            test_passed=True,
            pipeline_successful=True,
            all_files_present=True,
            execution_summary="Success"
        )

        assert result.get_failure_type() == "success"

    def test_get_failure_type_pipeline_failure(self):
        """Test get_failure_type for pipeline failure."""
        result = ValidationResult(
            test_passed=False,
            pipeline_successful=False,
            all_files_present=False,
            execution_summary="Pipeline failed"
        )

        assert result.get_failure_type() == "pipeline_execution_failed"

    def test_get_failure_type_file_missing(self):
        """Test get_failure_type for missing files."""
        result = ValidationResult(
            test_passed=False,
            pipeline_successful=True,
            all_files_present=False,
            execution_summary="Files missing"
        )

        assert result.get_failure_type() == "output_files_missing"

    def test_get_failure_type_validation_failure(self):
        """Test get_failure_type for validation failure."""
        result = ValidationResult(
            test_passed=False,
            pipeline_successful=True,
            all_files_present=True,
            execution_summary="Validation failed"
        )

        assert result.get_failure_type() == "output_validation_failed"

    def test_get_missing_files_none(self):
        """Test get_missing_files when no output files."""
        result = ValidationResult(
            test_passed=False,
            pipeline_successful=True,
            all_files_present=False,
            execution_summary="Test"
        )

        missing_files = result.get_missing_files()
        assert missing_files == []

    def test_get_missing_files_some_missing(self, tmp_path):
        """Test get_missing_files with some missing files."""
        existing_file = tmp_path / "exists.json"
        existing_file.write_text('{"test": "data"}')
        missing_file = tmp_path / "missing.json"

        output_files = [
            OutputArtifact(existing_file, "exists.json"),
            OutputArtifact(missing_file, "missing.json")
        ]

        result = ValidationResult(
            test_passed=False,
            pipeline_successful=True,
            all_files_present=False,
            execution_summary="Some files missing",
            output_files=output_files
        )

        missing_files = result.get_missing_files()
        assert missing_files == ["missing.json"]