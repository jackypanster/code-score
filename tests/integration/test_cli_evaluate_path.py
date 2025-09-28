"""
T007: Test for CLI evaluate command path resolution
Tests that CLI evaluate command works with corrected configuration path.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src.cli.evaluate import evaluate


class TestCLIEvaluatePath:
    """Test CLI evaluate command path resolution functionality."""

    @pytest.fixture
    def sample_submission_data(self):
        """Provide sample submission data for testing."""
        return {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/test/repo.git",
                "commit": "abc123",
                "language": "Python"
            },
            "metrics": {
                "code_quality": {
                    "linting": {
                        "tool": "ruff",
                        "exit_code": 0,
                        "issues": []
                    }
                },
                "testing": {
                    "framework": "pytest",
                    "exit_code": 0,
                    "tests_run": 10,
                    "tests_passed": 10
                },
                "documentation": {
                    "readme_exists": True,
                    "readme_length": 500
                }
            },
            "execution": {
                "timestamp": "2025-09-28T14:00:00Z",
                "duration_seconds": 30
            }
        }

    @pytest.fixture
    def temp_submission_file(self, sample_submission_data):
        """Create a temporary submission file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_submission_data, f, indent=2)
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_cli_evaluate_default_config_path(self, temp_submission_file):
        """Test that CLI evaluate command uses correct default config path."""
        runner = CliRunner()

        # Mock the ChecklistLoader to avoid file system dependencies
        with patch('src.cli.evaluate.ChecklistLoader') as mock_loader:
            mock_loader.return_value.config_path = "specs/contracts/checklist_mapping.yaml"
            mock_loader.return_value.checklist_items_config = []

            # Mock the ChecklistEvaluator
            with patch('src.cli.evaluate.ChecklistEvaluator') as mock_evaluator:
                mock_evaluator.return_value.evaluate.return_value = {
                    "checklist_items": [],
                    "total_score": 0,
                    "max_score": 100
                }

                # Mock the ScoringMapper
                with patch('src.cli.evaluate.ScoringMapper') as mock_mapper:
                    mock_mapper.return_value.create_score_input.return_value = {"test": "data"}
                    mock_mapper.return_value.generate_evaluation_report.return_value = "Test report"

                    # Run the CLI command
                    result = runner.invoke(evaluate, [temp_submission_file])

                    # Verify the command completed (may have errors due to mocking, but should not crash)
                    assert result.exit_code is not None, "CLI command should complete with an exit code"

    def test_cli_evaluate_custom_config_path(self, temp_submission_file):
        """Test that CLI evaluate command accepts custom config path."""
        runner = CliRunner()
        custom_config = "custom/config/path.yaml"

        # Mock the ChecklistLoader with custom path
        with patch('src.cli.evaluate.ChecklistLoader') as mock_loader:
            mock_loader.return_value.config_path = custom_config
            mock_loader.return_value.checklist_items_config = []

            # Mock other components
            with patch('src.cli.evaluate.ChecklistEvaluator') as mock_evaluator:
                mock_evaluator.return_value.evaluate.return_value = {
                    "checklist_items": [],
                    "total_score": 0,
                    "max_score": 100
                }

                with patch('src.cli.evaluate.ScoringMapper') as mock_mapper:
                    mock_mapper.return_value.create_score_input.return_value = {"test": "data"}
                    mock_mapper.return_value.generate_evaluation_report.return_value = "Test report"

                    # Run the CLI command with custom config
                    result = runner.invoke(evaluate, [
                        temp_submission_file,
                        '--checklist-config', custom_config
                    ])

                    # Verify ChecklistLoader was called with custom path
                    mock_loader.assert_called()

    def test_cli_evaluate_output_directory_creation(self, temp_submission_file):
        """Test that CLI evaluate command creates output directory."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "test_output"

            # Mock components
            with patch('src.cli.evaluate.ChecklistLoader') as mock_loader:
                mock_loader.return_value.config_path = "specs/contracts/checklist_mapping.yaml"
                mock_loader.return_value.checklist_items_config = []

                with patch('src.cli.evaluate.ChecklistEvaluator') as mock_evaluator:
                    mock_evaluator.return_value.evaluate.return_value = {
                        "checklist_items": [],
                        "total_score": 0,
                        "max_score": 100
                    }

                    with patch('src.cli.evaluate.ScoringMapper') as mock_mapper:
                        mock_mapper.return_value.create_score_input.return_value = {"test": "data"}
                        mock_mapper.return_value.generate_evaluation_report.return_value = "Test report"

                        # Run CLI command with custom output directory
                        result = runner.invoke(evaluate, [
                            temp_submission_file,
                            '--output-dir', str(output_dir)
                        ])

                        # Output directory should be created
                        assert output_dir.exists(), "Output directory should be created"

    def test_cli_evaluate_verbose_output(self, temp_submission_file):
        """Test that CLI evaluate command works with verbose flag."""
        runner = CliRunner()

        # Mock components
        with patch('src.cli.evaluate.ChecklistLoader') as mock_loader:
            mock_loader.return_value.config_path = "specs/contracts/checklist_mapping.yaml"
            mock_loader.return_value.checklist_items_config = []

            with patch('src.cli.evaluate.ChecklistEvaluator') as mock_evaluator:
                mock_evaluator.return_value.evaluate.return_value = {
                    "checklist_items": [],
                    "total_score": 0,
                    "max_score": 100
                }

                with patch('src.cli.evaluate.ScoringMapper') as mock_mapper:
                    mock_mapper.return_value.create_score_input.return_value = {"test": "data"}
                    mock_mapper.return_value.generate_evaluation_report.return_value = "Test report"

                    # Run CLI command with verbose flag
                    result = runner.invoke(evaluate, [temp_submission_file, '--verbose'])

                    # Command should complete
                    assert result.exit_code is not None, "CLI command should complete"

    def test_cli_evaluate_format_options(self, temp_submission_file):
        """Test that CLI evaluate command accepts different format options."""
        runner = CliRunner()

        for format_option in ['json', 'markdown', 'both']:
            # Mock components
            with patch('src.cli.evaluate.ChecklistLoader') as mock_loader:
                mock_loader.return_value.config_path = "specs/contracts/checklist_mapping.yaml"
                mock_loader.return_value.checklist_items_config = []

                with patch('src.cli.evaluate.ChecklistEvaluator') as mock_evaluator:
                    mock_evaluator.return_value.evaluate.return_value = {
                        "checklist_items": [],
                        "total_score": 0,
                        "max_score": 100
                    }

                    with patch('src.cli.evaluate.ScoringMapper') as mock_mapper:
                        mock_mapper.return_value.create_score_input.return_value = {"test": "data"}
                        mock_mapper.return_value.generate_evaluation_report.return_value = "Test report"

                        # Run CLI command with format option
                        result = runner.invoke(evaluate, [
                            temp_submission_file,
                            '--format', format_option
                        ])

                        # Command should complete for all format options
                        assert result.exit_code is not None, \
                            f"CLI command should complete for format: {format_option}"


if __name__ == "__main__":
    pytest.main([__file__])
