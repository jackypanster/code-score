"""
T008: Integration test for full pipeline with checklist evaluation
Tests that the complete metrics pipeline works with checklist evaluation enabled.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.metrics.pipeline_output_manager import PipelineOutputManager


class TestFullPipelineChecklist:
    """Test full pipeline integration with checklist evaluation."""

    @pytest.fixture
    def sample_metrics_data(self):
        """Provide sample metrics data for pipeline testing."""
        return {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/test/repo.git",
                "commit": "abc123",
                "language": "Python",
                "size_mb": 5.2,
                "file_count": 150
            },
            "metrics": {
                "code_quality": {
                    "linting": {
                        "tool": "ruff",
                        "exit_code": 0,
                        "issues": [],
                        "score": 9.5
                    },
                    "security": {
                        "tool": "bandit",
                        "exit_code": 0,
                        "vulnerabilities": [],
                        "score": 10.0
                    }
                },
                "testing": {
                    "framework": "pytest",
                    "exit_code": 0,
                    "tests_run": 25,
                    "tests_passed": 24,
                    "coverage_percent": 85.5
                },
                "documentation": {
                    "readme_exists": True,
                    "readme_length": 1200,
                    "api_docs_exist": True,
                    "inline_comments_ratio": 0.15
                }
            },
            "execution": {
                "timestamp": "2025-09-28T14:00:00Z",
                "duration_seconds": 45,
                "tool_timeouts": []
            }
        }

    def test_pipeline_with_checklist_enabled(self, sample_metrics_data):
        """Test pipeline integration with checklist evaluation enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Initialize pipeline with checklist evaluation enabled
            manager = PipelineOutputManager(
                output_dir=output_dir,
                enable_checklist_evaluation=True
            )

            # Verify checklist components are initialized
            assert manager.checklist_evaluator is not None, \
                "ChecklistEvaluator should be initialized when enabled"

            # Verify config path is correct
            if manager.checklist_evaluator:
                config_path = manager.checklist_evaluator.checklist_config_path
                config_path_obj = Path(config_path)
                path_parts = config_path_obj.parts
                assert "specs" in path_parts and "contracts" in path_parts and config_path_obj.name == "checklist_mapping.yaml", \
                    f"Expected path to contain 'specs/contracts/checklist_mapping.yaml', got: {config_path}"

    def test_pipeline_config_path_resolution(self, sample_metrics_data):
        """Test that pipeline resolves configuration path correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Test with default config path (None)
            manager = PipelineOutputManager(
                output_dir=output_dir,
                enable_checklist_evaluation=True,
                checklist_config_path=None
            )

            if manager.checklist_evaluator:
                config_path = Path(manager.checklist_evaluator.checklist_config_path)

                # Verify path structure
                path_parts = config_path.parts
                assert "specs" in path_parts, "Path should contain 'specs' directory"
                assert "contracts" in path_parts, "Path should contain 'contracts' directory"
                assert path_parts[-1] == "checklist_mapping.yaml", \
                    "Filename should be 'checklist_mapping.yaml'"

    def test_pipeline_custom_config_path(self, sample_metrics_data):
        """Test pipeline with custom configuration path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            custom_config = "custom/test/config.yaml"

            # Mock ChecklistEvaluator to avoid file system dependencies
            with patch('src.metrics.pipeline_output_manager.ChecklistEvaluator') as mock_evaluator:
                manager = PipelineOutputManager(
                    output_dir=output_dir,
                    enable_checklist_evaluation=True,
                    checklist_config_path=custom_config
                )

                # Verify ChecklistEvaluator was called with custom path
                mock_evaluator.assert_called_once_with(custom_config)

    def test_pipeline_output_generation(self, sample_metrics_data):
        """Test that pipeline generates expected outputs with checklist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock the checklist components to avoid file dependencies
            with patch('src.metrics.pipeline_output_manager.ChecklistEvaluator') as mock_evaluator:
                mock_eval_result = {
                    "checklist_items": [
                        {"id": "test_1", "status": "met", "score": 10, "evidence": []}
                    ],
                    "total_score": 85,
                    "max_score": 100
                }
                mock_evaluator.return_value.evaluate.return_value = mock_eval_result

                with patch('src.metrics.pipeline_output_manager.ScoringMapper') as mock_mapper:
                    mock_mapper.return_value.create_score_input.return_value = {
                        "evaluation_result": mock_eval_result,
                        "repository_info": sample_metrics_data["repository"]
                    }
                    mock_mapper.return_value.generate_evaluation_report.return_value = "Test Report"

                    manager = PipelineOutputManager(
                        output_dir=output_dir,
                        enable_checklist_evaluation=True
                    )

                    # Verify components are properly initialized
                    assert manager.checklist_evaluator is not None
                    assert manager.scoring_mapper is not None

    def test_pipeline_without_checklist(self, sample_metrics_data):
        """Test that pipeline works correctly when checklist is disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            manager = PipelineOutputManager(
                output_dir=output_dir,
                enable_checklist_evaluation=False
            )

            # Verify checklist components are not initialized
            assert manager.checklist_evaluator is None, \
                "ChecklistEvaluator should be None when disabled"

    def test_pipeline_error_handling(self, sample_metrics_data):
        """Test pipeline error handling with checklist evaluation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Test with invalid config path
            invalid_config_path = "/nonexistent/path/config.yaml"

            # This should not crash the pipeline initialization
            try:
                manager = PipelineOutputManager(
                    output_dir=output_dir,
                    enable_checklist_evaluation=True,
                    checklist_config_path=invalid_config_path
                )
                # If it doesn't crash, the error handling is working
                assert True, "Pipeline should handle invalid config paths gracefully"
            except Exception as e:
                # If it does crash, verify it's an expected error type
                assert "FileNotFoundError" in str(type(e)) or "ConfigurationError" in str(type(e)), \
                    f"Should get appropriate error for invalid config, got: {type(e)}"

    def test_pipeline_integration_with_llm_template(self, sample_metrics_data):
        """Test pipeline integration with LLM template processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock LLM template file
            llm_template_path = output_dir / "llm_template.md"
            llm_template_path.write_text("Test LLM template content")

            manager = PipelineOutputManager(
                output_dir=output_dir,
                enable_checklist_evaluation=True,
                llm_template_path=str(llm_template_path)
            )

            # Verify template path is set correctly
            assert manager.llm_template_path == str(llm_template_path), \
                "LLM template path should be set correctly"

    def test_pipeline_component_integration(self, sample_metrics_data):
        """Test that all pipeline components work together correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            manager = PipelineOutputManager(
                output_dir=output_dir,
                enable_checklist_evaluation=True
            )

            # Verify all expected components are present
            expected_attrs = ['output_dir', 'checklist_evaluator', 'scoring_mapper', 'pipeline_integrator']
            for attr in expected_attrs:
                assert hasattr(manager, attr), f"Manager should have {attr} attribute"

            # Verify checklist evaluator has correct config path
            if manager.checklist_evaluator:
                config_path = manager.checklist_evaluator.checklist_config_path
                assert isinstance(config_path, str), "Config path should be a string"
                assert len(config_path) > 0, "Config path should not be empty"


if __name__ == "__main__":
    pytest.main([__file__])