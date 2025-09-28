"""Integration tests for pipeline integration with checklist evaluation."""

import json
from unittest.mock import patch

import pytest

from src.metrics.pipeline_output_manager import PipelineOutputManager
from src.metrics.submission_pipeline import (
    PipelineIntegrator,
    SubmissionLoader,
    SubmissionValidationError,
)


class TestSubmissionLoader:
    """Test submission.json loading and validation."""

    def test_load_valid_submission(self, tmp_path):
        """Test loading a valid submission.json file."""
        # Create test submission data
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

        # Write to temp file
        submission_file = tmp_path / "submission.json"
        with open(submission_file, 'w') as f:
            json.dump(submission_data, f)

        # Test loading
        loader = SubmissionLoader()
        loaded_data = loader.load_and_validate(str(submission_file))

        assert loaded_data == submission_data

    def test_load_missing_file(self):
        """Test error handling for missing file."""
        loader = SubmissionLoader()

        with pytest.raises(SubmissionValidationError) as exc_info:
            loader.load_and_validate("nonexistent.json")

        assert "not found" in str(exc_info.value)

    def test_load_invalid_json(self, tmp_path):
        """Test error handling for invalid JSON."""
        # Create invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")

        loader = SubmissionLoader()

        with pytest.raises(SubmissionValidationError) as exc_info:
            loader.load_and_validate(str(invalid_file))

        assert "Invalid JSON" in str(exc_info.value)

    def test_validate_missing_sections(self, tmp_path):
        """Test validation of missing required sections."""
        # Missing repository section
        submission_data = {
            "metrics": {},
            "execution": {"errors": [], "warnings": []}
        }

        submission_file = tmp_path / "submission.json"
        with open(submission_file, 'w') as f:
            json.dump(submission_data, f)

        loader = SubmissionLoader()

        with pytest.raises(SubmissionValidationError) as exc_info:
            loader.load_and_validate(str(submission_file))

        assert "Missing required section: repository" in str(exc_info.value)

    def test_extract_repository_info(self):
        """Test repository information extraction."""
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
        repo_info = loader.extract_repository_info(submission_data)

        assert repo_info["url"] == "https://github.com/test/repo"
        assert repo_info["commit_sha"] == "abc123"
        assert repo_info["primary_language"] == "python"
        assert repo_info["size_mb"] == 50

    def test_validate_for_checklist_evaluation(self):
        """Test checklist-specific validation warnings."""
        submission_data = {
            "metrics": {
                "code_quality": {},  # Missing lint_results
                "testing": {},       # Missing test_execution
                "documentation": {}  # Missing readme_present
            }
        }

        loader = SubmissionLoader()
        warnings = loader.validate_for_checklist_evaluation(submission_data)

        assert len(warnings) >= 3
        assert any("lint_results" in warning for warning in warnings)
        assert any("test_execution" in warning for warning in warnings)
        assert any("readme_present" in warning for warning in warnings)


class TestPipelineIntegrator:
    """Test pipeline integration logic."""

    def test_should_run_checklist_evaluation_with_data(self):
        """Test that evaluation runs when sufficient data is present."""
        submission_data = {
            "metrics": {
                "code_quality": {"lint_results": {"passed": True}},
                "testing": {},
                "documentation": {}
            }
        }

        integrator = PipelineIntegrator()
        should_run = integrator.should_run_checklist_evaluation(submission_data)

        assert should_run is True

    def test_should_run_checklist_evaluation_without_data(self):
        """Test that evaluation skips when no meaningful data is present."""
        submission_data = {
            "metrics": {
                "code_quality": {},
                "testing": {},
                "documentation": {}
            }
        }

        integrator = PipelineIntegrator()
        should_run = integrator.should_run_checklist_evaluation(submission_data)

        assert should_run is False

    def test_get_pipeline_metadata(self):
        """Test pipeline metadata extraction."""
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
        metadata = integrator.get_pipeline_metadata(submission_data)

        assert metadata["tools_used"] == ["eslint", "pytest"]
        assert metadata["duration_seconds"] == 45.5
        assert metadata["errors_count"] == 1
        assert metadata["warnings_count"] == 2
        assert metadata["timestamp"] == "2025-09-27T12:00:00Z"


class TestPipelineOutputManager:
    """Test integrated output management."""

    @patch('src.metrics.pipeline_output_manager.ChecklistEvaluator')
    @patch('src.metrics.pipeline_output_manager.ScoringMapper')
    def test_pipeline_output_manager_initialization(self, mock_mapper, mock_evaluator, tmp_path):
        """Test output manager initialization."""
        output_manager = PipelineOutputManager(
            output_dir=str(tmp_path),
            enable_checklist_evaluation=True
        )

        assert output_manager.enable_checklist_evaluation is True
        assert output_manager.checklist_evaluator is not None
        assert output_manager.scoring_mapper is not None

    def test_pipeline_output_manager_disabled(self, tmp_path):
        """Test output manager with checklist evaluation disabled."""
        output_manager = PipelineOutputManager(
            output_dir=str(tmp_path),
            enable_checklist_evaluation=False
        )

        assert output_manager.enable_checklist_evaluation is False
        assert output_manager.checklist_evaluator is None

    @patch('src.metrics.pipeline_output_manager.ChecklistEvaluator')
    @patch('src.metrics.pipeline_output_manager.ScoringMapper')
    def test_calculate_grade(self, mock_mapper, mock_evaluator, tmp_path):
        """Test grade calculation from percentage."""
        output_manager = PipelineOutputManager(str(tmp_path))

        assert output_manager._calculate_grade(95) == "A"
        assert output_manager._calculate_grade(85) == "B"
        assert output_manager._calculate_grade(75) == "C"
        assert output_manager._calculate_grade(65) == "D"
        assert output_manager._calculate_grade(55) == "F"

    @patch('src.metrics.pipeline_output_manager.ChecklistEvaluator')
    @patch('src.metrics.pipeline_output_manager.ScoringMapper')
    def test_integrate_with_existing_pipeline_disabled(self, mock_mapper, mock_evaluator, tmp_path):
        """Test integration when checklist evaluation is disabled."""
        output_manager = PipelineOutputManager(
            output_dir=str(tmp_path),
            enable_checklist_evaluation=False
        )

        existing_files = ["/path/to/existing1.json", "/path/to/existing2.md"]
        result_files = output_manager.integrate_with_existing_pipeline(
            existing_files, "submission.json"
        )

        assert result_files == existing_files

    def test_markdown_report_structure(self, tmp_path):
        """Test Markdown report generation structure with simplified data."""
        output_manager = PipelineOutputManager(str(tmp_path), enable_checklist_evaluation=False)

        # Create minimal mock data for testing
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
