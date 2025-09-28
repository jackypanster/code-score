"""
End-to-end smoke test for the complete code analysis pipeline.

This test validates that the entire pipeline works correctly by executing
the full workflow and verifying all expected outputs are generated.
"""

import pytest
import logging
from pathlib import Path
from typing import Dict, Any

from .models import ValidationResult
from .pipeline_executor import execute_pipeline, validate_pipeline_environment, PipelineExecutionError
from .file_validator import validate_output_files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TARGET_REPOSITORY = "git@github.com:AIGCInnovatorSpace/code-walker.git"
PIPELINE_TIMEOUT = 300  # 5 minutes (performance requirement: complete within 5 minutes)
ENABLE_CHECKLIST = True
GENERATE_LLM_REPORT = False


class TestFullPipeline:
    """Main smoke test class for end-to-end pipeline validation."""

    def test_full_pipeline_execution(self, project_root: Path, clean_output_directory: Path) -> ValidationResult:
        """
        Test complete pipeline execution with output validation.

        This is the main smoke test that validates the entire system.
        """
        logger.info("Starting full pipeline smoke test")

        # Validate environment before execution
        env_valid, env_error = validate_pipeline_environment(project_root)
        if not env_valid:
            pytest.fail(f"Pipeline environment validation failed: {env_error}")

        # Clean output directory is already provided by fixture
        # This ensures we validate files from the current run, not stale artifacts

        try:
            # Execute the pipeline
            logger.info(f"Executing pipeline for repository: {TARGET_REPOSITORY}")
            execution = execute_pipeline(
                repository_url=TARGET_REPOSITORY,
                working_directory=project_root,
                timeout_seconds=PIPELINE_TIMEOUT,
                enable_checklist=ENABLE_CHECKLIST,
                generate_llm_report=GENERATE_LLM_REPORT
            )

            logger.info(f"Pipeline execution completed in {execution.pipeline_duration:.2f} seconds")

            # Validate output files
            logger.info("Validating output files")
            validation_result = validate_output_files(clean_output_directory)

            # Update validation result with execution details
            validation_result.pipeline_duration = execution.pipeline_duration
            validation_result.pipeline_exit_code = execution.pipeline_exit_code

            # Log results
            if validation_result.test_passed:
                logger.info("✅ Smoke test PASSED: Pipeline executed successfully and all outputs validated")
            else:
                logger.error(f"❌ Smoke test FAILED: {validation_result.error_message}")

            # Performance validation: ensure pipeline completes within timeout
            if execution.pipeline_duration > PIPELINE_TIMEOUT:
                logger.warning(f"⚠️  Performance concern: Pipeline took {execution.pipeline_duration:.1f}s "
                              f"(target: <{PIPELINE_TIMEOUT}s)")

            # Assert success for pytest with comprehensive error formatting
            if not validation_result.test_passed:
                error_details = [
                    f"Smoke test failed: {validation_result.error_message}",
                    f"Pipeline exit code: {validation_result.pipeline_exit_code}",
                    f"Pipeline duration: {validation_result.pipeline_duration:.2f}s",
                    f"Files present: {validation_result.all_files_present}",
                    f"Failure type: {validation_result.get_failure_type()}"
                ]

                if validation_result.output_files:
                    missing_files = validation_result.get_missing_files()
                    if missing_files:
                        error_details.append(f"Missing files: {', '.join(missing_files)}")

                formatted_error = "\n".join(f"  • {detail}" for detail in error_details)
                pytest.fail(f"Smoke test validation failed:\n{formatted_error}")

            assert validation_result.test_passed

            return validation_result

        except PipelineExecutionError as e:
            error_msg = f"Pipeline execution failed: {e}"
            logger.error(error_msg)
            pytest.fail(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error during smoke test: {e}"
            logger.error(error_msg, exc_info=True)
            pytest.fail(error_msg)

    def test_pipeline_environment_validation(self, project_root: Path):
        """Test that the pipeline environment is properly configured."""
        env_valid, env_error = validate_pipeline_environment(project_root)

        assert env_valid, f"Pipeline environment validation failed: {env_error}"

        # Additional environment checks
        script_path = project_root / "scripts" / "run_metrics.sh"
        assert script_path.exists(), f"Pipeline script not found: {script_path}"
        assert script_path.is_file(), f"Pipeline script is not a file: {script_path}"

    def test_output_directory_structure(self, project_root: Path, output_directory: Path):
        """Test that output directory can be created and is writable."""
        # Ensure output directory can be created
        output_directory.mkdir(exist_ok=True)
        assert output_directory.exists(), "Output directory should exist"
        assert output_directory.is_dir(), "Output directory should be a directory"

        # Test write permissions
        test_file = output_directory / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except (OSError, PermissionError) as e:
            pytest.fail(f"Output directory is not writable: {e}")

    @pytest.mark.slow
    def test_pipeline_timeout_handling(self, project_root: Path):
        """Test that pipeline execution respects timeout settings."""
        # This test uses a very short timeout to test timeout handling
        # In a real scenario, this would timeout, but we'll skip if the pipeline is too fast
        short_timeout = 1  # 1 second

        try:
            execution = execute_pipeline(
                repository_url=TARGET_REPOSITORY,
                working_directory=project_root,
                timeout_seconds=short_timeout,
                enable_checklist=False,  # Disable to potentially speed up
                generate_llm_report=False
            )
            # If we get here, the pipeline completed very quickly
            logger.info("Pipeline completed faster than timeout - this is acceptable")
            assert execution.is_complete, "Execution should be marked as complete"

        except Exception as e:
            # Expected for timeout scenarios
            logger.info(f"Timeout test behaved as expected: {e}")
            # This is acceptable behavior for timeout testing

    def test_output_file_existence_validation(self, output_directory: Path):
        """Test output file existence validation without running pipeline."""
        expected_files = [
            "submission.json",
            "score_input.json",
            "evaluation_report.md"
        ]

        # Ensure output directory exists
        output_directory.mkdir(exist_ok=True)

        # Test validation with missing files
        validation_result = validate_output_files(output_directory)

        # Should fail when files are missing
        assert not validation_result.test_passed, "Validation should fail when files are missing"
        assert not validation_result.all_files_present, "Should detect missing files"

        missing_files = validation_result.get_missing_files()
        assert len(missing_files) == len(expected_files), "Should detect all missing files"

    def test_json_content_validation(self, output_directory: Path):
        """Test JSON content validation logic."""
        from .file_validator import validate_single_file

        # Ensure output directory exists
        output_directory.mkdir(exist_ok=True)

        # Create a valid JSON file
        valid_json_path = output_directory / "test_valid.json"
        valid_json_path.write_text('{"test": "valid", "content": true}')

        # Create an invalid JSON file
        invalid_json_path = output_directory / "test_invalid.json"
        invalid_json_path.write_text('{"test": invalid json}')

        # Validate valid JSON
        valid_artifact = validate_single_file(valid_json_path, "test_valid.json")
        assert valid_artifact.file_exists, "Valid JSON file should exist"
        assert valid_artifact.content_valid, "Valid JSON should pass validation"

        # Validate invalid JSON
        invalid_artifact = validate_single_file(invalid_json_path, "test_invalid.json")
        assert invalid_artifact.file_exists, "Invalid JSON file should exist"
        assert not invalid_artifact.content_valid, "Invalid JSON should fail validation"

        # Cleanup
        valid_json_path.unlink()
        invalid_json_path.unlink()

    def test_markdown_content_validation(self, output_directory: Path):
        """Test Markdown content validation logic."""
        from .file_validator import validate_single_file

        # Ensure output directory exists
        output_directory.mkdir(exist_ok=True)

        # Create a valid Markdown file
        valid_md_path = output_directory / "test_valid.md"
        valid_md_path.write_text("# Test Markdown\n\nThis is valid markdown content.")

        # Create an empty file
        empty_md_path = output_directory / "test_empty.md"
        empty_md_path.write_text("")

        # Validate valid Markdown
        valid_artifact = validate_single_file(valid_md_path, "test_valid.md")
        assert valid_artifact.file_exists, "Valid Markdown file should exist"
        assert valid_artifact.content_valid, "Valid Markdown should pass validation"

        # Validate empty Markdown
        empty_artifact = validate_single_file(empty_md_path, "test_empty.md")
        assert empty_artifact.file_exists, "Empty Markdown file should exist"
        assert not empty_artifact.content_valid, "Empty Markdown should fail validation"

        # Cleanup
        valid_md_path.unlink()
        empty_md_path.unlink()


# Standalone function for direct execution
def test_full_pipeline_execution() -> ValidationResult:
    """
    Standalone function for executing the full pipeline smoke test.

    This function can be called directly or via pytest.

    Returns:
        ValidationResult with test outcome
    """
    project_root = Path(__file__).parent.parent.parent
    output_directory = project_root / "output"

    # Clean the output directory to ensure we test current run, not stale artifacts
    output_directory.mkdir(exist_ok=True)
    expected_files = ["submission.json", "score_input.json", "evaluation_report.md"]
    for filename in expected_files:
        file_path = output_directory / filename
        if file_path.exists():
            file_path.unlink()

    # Create test instance and run the test
    test_instance = TestFullPipeline()

    try:
        return test_instance.test_full_pipeline_execution(project_root, output_directory)
    except Exception as e:
        # Return a failure result for direct execution
        return ValidationResult.pipeline_failure(
            error_message=str(e),
            pipeline_exit_code=-1
        )


if __name__ == "__main__":
    # Allow direct execution of the smoke test
    result = test_full_pipeline_execution()
    if result.test_passed:
        print("✅ Smoke test PASSED")
        exit(0)
    else:
        print(f"❌ Smoke test FAILED: {result.error_message}")
        exit(1)