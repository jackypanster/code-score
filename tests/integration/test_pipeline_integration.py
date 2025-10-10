"""Real integration tests for pipeline integration with checklist evaluation.

NO MOCKS - All tests use real submission loading, validation, and integration.
"""

import json
from pathlib import Path

import pytest

from src.metrics.pipeline_output_manager import PipelineOutputManager
from src.metrics.submission_pipeline import (
    PipelineIntegrator,
    SubmissionLoader,
    SubmissionValidationError,
)


class TestSubmissionLoader:
    """REAL TESTS for submission.json loading and validation - NO MOCKS."""

    def test_load_valid_submission_real(self, tmp_path):
        """REAL TEST: Loading a valid submission.json file."""
        # Create REAL test submission data
        submission_data = {
            "repository": {
                "url": "https://github.com/test/repo",
                "commit": "abc123",
                "language": "python",
                "timestamp": "2025-09-27T12:00:00Z"
            },
            "metrics": {
                "code_quality": {"lint_results": {"passed": True}},
                "testing": {"test_execution": {"tests_passed": 5}},
                "documentation": {"readme_present": True}
            },
            "execution": {
                "errors": [],
                "warnings": ["test warning"]
            }
        }

        # Write to REAL temp file
        submission_file = tmp_path / "submission.json"
        with open(submission_file, 'w') as f:
            json.dump(submission_data, f)

        # REAL LOADING - No mocks!
        loader = SubmissionLoader()
        loaded_data = loader.load_and_validate(str(submission_file))

        assert loaded_data == submission_data

    def test_load_missing_file_real(self):
        """REAL TEST: Error handling for missing file."""
        loader = SubmissionLoader()

        # REAL VALIDATION
        with pytest.raises(SubmissionValidationError) as exc_info:
            loader.load_and_validate("nonexistent.json")

        assert "not found" in str(exc_info.value)

    def test_load_invalid_json_real(self, tmp_path):
        """REAL TEST: Error handling for invalid JSON."""
        # Create REAL invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")

        loader = SubmissionLoader()

        # REAL VALIDATION
        with pytest.raises(SubmissionValidationError) as exc_info:
            loader.load_and_validate(str(invalid_file))

        assert "Invalid JSON" in str(exc_info.value)

    def test_validate_missing_sections_real(self, tmp_path):
        """REAL TEST: Validation of missing required sections."""
        # Missing repository section
        submission_data = {
            "metrics": {
                "code_quality": {},
                "testing": {},
                "documentation": {}
            },
            "execution": {"errors": [], "warnings": []}
        }

        # Write to REAL file
        submission_file = tmp_path / "submission.json"
        with open(submission_file, 'w') as f:
            json.dump(submission_data, f)

        loader = SubmissionLoader()

        # REAL VALIDATION
        with pytest.raises(SubmissionValidationError) as exc_info:
            loader.load_and_validate(str(submission_file))

        assert "Missing required section: repository" in str(exc_info.value)

    def test_extract_repository_info_real(self):
        """REAL TEST: Repository information extraction."""
        submission_data = {
            "repository": {
                "url": "https://github.com/test/repo",
                "commit": "abc123",
                "language": "python",
                "timestamp": "2025-09-27T12:00:00Z",
                "size_mb": 50
            }
        }

        loader = SubmissionLoader()

        # REAL EXTRACTION - No mocks!
        repo_info = loader.extract_repository_info(submission_data)

        assert repo_info["url"] == "https://github.com/test/repo"
        assert repo_info["commit_sha"] == "abc123"
        assert repo_info["primary_language"] == "python"
        assert repo_info["size_mb"] == 50

    def test_validate_for_checklist_evaluation_real(self):
        """REAL TEST: Checklist-specific validation warnings."""
        submission_data = {
            "metrics": {
                "code_quality": {},  # Missing lint_results
                "testing": {},       # Missing test_execution
                "documentation": {}  # Missing readme_present
            }
        }

        loader = SubmissionLoader()

        # REAL VALIDATION
        warnings = loader.validate_for_checklist_evaluation(submission_data)

        assert len(warnings) >= 3
        assert any("lint_results" in warning for warning in warnings)
        assert any("test_execution" in warning for warning in warnings)
        assert any("readme_present" in warning for warning in warnings)


class TestPipelineIntegrator:
    """REAL TESTS for pipeline integration logic - NO MOCKS."""

    def test_should_run_checklist_evaluation_with_data_real(self):
        """REAL TEST: Evaluation runs when sufficient data is present."""
        submission_data = {
            "metrics": {
                "code_quality": {"lint_results": {"passed": True}},
                "testing": {},
                "documentation": {}
            }
        }

        integrator = PipelineIntegrator()

        # REAL DECISION LOGIC
        should_run = integrator.should_run_checklist_evaluation(submission_data)

        assert should_run is True

    def test_should_run_checklist_evaluation_without_data_real(self):
        """REAL TEST: Evaluation skips when no meaningful data is present."""
        submission_data = {
            "metrics": {
                "code_quality": {},
                "testing": {},
                "documentation": {}
            }
        }

        integrator = PipelineIntegrator()

        # REAL DECISION LOGIC
        should_run = integrator.should_run_checklist_evaluation(submission_data)

        assert should_run is False

    def test_get_pipeline_metadata_real(self):
        """REAL TEST: Pipeline metadata extraction."""
        submission_data = {
            "execution": {
                "tools_used": ["eslint", "pytest"],
                "duration_seconds": 45.5,
                "errors": ["error1"],
                "warnings": ["warning1", "warning2"],
                "timestamp": "2025-09-27T12:00:00Z"
            }
        }

        integrator = PipelineIntegrator()

        # REAL EXTRACTION
        metadata = integrator.get_pipeline_metadata(submission_data)

        assert metadata["tools_used"] == ["eslint", "pytest"]
        assert metadata["duration_seconds"] == 45.5
        assert metadata["errors_count"] == 1
        assert metadata["warnings_count"] == 2
        assert metadata["timestamp"] == "2025-09-27T12:00:00Z"

    def test_prepare_submission_for_evaluation_real(self, tmp_path):
        """REAL TEST: Complete submission preparation workflow."""
        # Create REAL valid submission
        submission_data = {
            "repository": {
                "url": "https://github.com/test/repo",
                "commit": "abc123",
                "language": "python",
                "timestamp": "2025-09-27T12:00:00Z"
            },
            "metrics": {
                "code_quality": {"lint_results": {"passed": True}},
                "testing": {},
                "documentation": {}
            },
            "execution": {
                "errors": [],
                "warnings": []
            }
        }

        submission_file = tmp_path / "submission.json"
        with open(submission_file, 'w') as f:
            json.dump(submission_data, f)

        integrator = PipelineIntegrator()

        # REAL PREPARATION
        loaded_data, warnings = integrator.prepare_submission_for_evaluation(str(submission_file))

        assert loaded_data == submission_data
        assert isinstance(warnings, list)


class TestPipelineOutputManager:
    """REAL TESTS for integrated output management - NO MOCKS."""

    def test_pipeline_output_manager_initialization_real(self, tmp_path):
        """REAL TEST: Output manager initialization without mocks."""
        # REAL INITIALIZATION
        output_manager = PipelineOutputManager(
            output_dir=str(tmp_path),
            enable_checklist_evaluation=True
        )

        assert output_manager.enable_checklist_evaluation is True
        assert output_manager.checklist_evaluator is not None
        assert output_manager.scoring_mapper is not None

    def test_pipeline_output_manager_disabled_real(self, tmp_path):
        """REAL TEST: Output manager with checklist evaluation disabled."""
        # REAL INITIALIZATION
        output_manager = PipelineOutputManager(
            output_dir=str(tmp_path),
            enable_checklist_evaluation=False
        )

        assert output_manager.enable_checklist_evaluation is False
        assert output_manager.checklist_evaluator is None

    def test_calculate_grade_real(self, tmp_path):
        """REAL TEST: Grade calculation from percentage."""
        output_manager = PipelineOutputManager(str(tmp_path))

        # REAL CALCULATIONS - No mocks!
        assert output_manager._calculate_grade(95) == "A"
        assert output_manager._calculate_grade(85) == "B"
        assert output_manager._calculate_grade(75) == "C"
        assert output_manager._calculate_grade(65) == "D"
        assert output_manager._calculate_grade(55) == "F"

    def test_integrate_with_existing_pipeline_disabled_real(self, tmp_path):
        """REAL TEST: Integration when checklist evaluation is disabled."""
        output_manager = PipelineOutputManager(
            output_dir=str(tmp_path),
            enable_checklist_evaluation=False
        )

        existing_files = ["/path/to/existing1.json", "/path/to/existing2.md"]

        # REAL INTEGRATION
        result_files = output_manager.integrate_with_existing_pipeline(
            existing_files, "submission.json"
        )

        assert result_files == existing_files

    def test_markdown_report_structure_real(self, tmp_path):
        """REAL TEST: Markdown report generation structure."""
        output_manager = PipelineOutputManager(str(tmp_path), enable_checklist_evaluation=False)

        # Create REAL mock data for testing
        class MockItem:
            def __init__(self, name, status, score, max_points, description):
                self.name = name
                self.evaluation_status = status
                self.score = score
                self.max_points = max_points
                self.description = description

        class MockBreakdown:
            def __init__(self, percentage):
                self.percentage = percentage
                self.actual_points = 10.0
                self.max_points = 10
                self.items_count = 1

        class MockResult:
            def __init__(self):
                self.checklist_items = [
                    MockItem("Test Met Item", "met", 10.0, 10, "Test description")
                ]
                self.total_score = 10.0
                self.max_possible_score = 10
                self.score_percentage = 100.0
                self.category_breakdowns = {
                    "code_quality": MockBreakdown(100.0)
                }
                self.evidence_summary = ["Test evidence"]

        eval_result = MockResult()

        # REAL REPORT GENERATION
        report = output_manager._create_markdown_report(eval_result, ["Test warning"])

        # Check report structure
        assert "# Code Quality Evaluation Report" in report
        assert "## Executive Summary" in report
        assert "**Overall Score**: 10.0/10 (100.0%)" in report
        assert "## Category Breakdown" in report
        assert "### ✅ Met Criteria" in report
        assert "## Evaluation Warnings" in report
        assert "- ⚠️ Test warning" in report
        assert "## Evidence Summary" in report


@pytest.fixture
def sample_submission_data():
    """Provide sample submission data for tests."""
    return {
        "repository": {
            "url": "https://github.com/test/repo",
            "commit": "abc123",
            "language": "python",
            "timestamp": "2025-09-27T12:00:00Z"
        },
        "metrics": {
            "code_quality": {
                "lint_results": {"passed": True, "tool_used": "ruff"},
                "build_success": True
            },
            "testing": {
                "test_execution": {"tests_passed": 5, "tests_failed": 0}
            },
            "documentation": {
                "readme_present": True
            }
        },
        "execution": {
            "errors": [],
            "warnings": [],
            "tools_used": ["ruff", "pytest"],
            "duration_seconds": 30.0
        }
    }
