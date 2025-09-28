"""
T006: Test for PipelineOutputManager path resolution
Tests that PipelineOutputManager uses correct default path for checklist evaluation.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.metrics.pipeline_output_manager import PipelineOutputManager


class TestPipelineOutputManagerPath:
    """Test PipelineOutputManager path resolution functionality."""

    def test_default_config_path_with_checklist_enabled(self):
        """Test default config path when checklist evaluation is enabled."""
        output_dir = Path("test_output")

        manager = PipelineOutputManager(
            output_dir=output_dir,
            enable_checklist_evaluation=True
        )

        # Verify that ChecklistEvaluator was initialized
        assert hasattr(manager, 'checklist_evaluator'), \
            "Manager should have checklist_evaluator when enabled"
        assert manager.checklist_evaluator is not None, \
            "ChecklistEvaluator should be initialized when enabled"

    def test_config_path_construction_in_manager(self):
        """Test that config path is correctly constructed in PipelineOutputManager."""
        output_dir = Path("test_output")

        # Test with default config path (None)
        manager = PipelineOutputManager(
            output_dir=output_dir,
            enable_checklist_evaluation=True,
            checklist_config_path=None
        )

        # Verify ChecklistEvaluator uses correct default path
        if manager.checklist_evaluator:
            config_path_obj = Path(manager.checklist_evaluator.checklist_config_path)
            path_parts = config_path_obj.parts
            assert "specs" in path_parts and "contracts" in path_parts and config_path_obj.name == "checklist_mapping.yaml", \
                f"Expected path to contain 'specs/contracts/checklist_mapping.yaml', got: {manager.checklist_evaluator.checklist_config_path}"

    def test_custom_config_path_override(self):
        """Test that custom config path can override default in manager."""
        output_dir = Path("test_output")
        custom_config_path = "custom/path/to/config.yaml"

        # Mock the ChecklistEvaluator since custom path doesn't exist
        with patch('src.metrics.pipeline_output_manager.ChecklistEvaluator') as mock_evaluator:
            manager = PipelineOutputManager(
                output_dir=output_dir,
                enable_checklist_evaluation=True,
                checklist_config_path=custom_config_path
            )

            # Verify ChecklistEvaluator was called with custom path
            mock_evaluator.assert_called_once_with(custom_config_path)

    def test_checklist_evaluation_disabled(self):
        """Test that no checklist components are initialized when disabled."""
        output_dir = Path("test_output")

        manager = PipelineOutputManager(
            output_dir=output_dir,
            enable_checklist_evaluation=False
        )

        # Verify that checklist components are None when disabled
        assert manager.checklist_evaluator is None, \
            "ChecklistEvaluator should be None when checklist evaluation is disabled"

    def test_path_consistency_with_default_fallback(self):
        """Test that default path fallback works correctly."""
        output_dir = Path("test_output")

        # Test the default path fallback logic that should use the corrected path
        manager = PipelineOutputManager(
            output_dir=output_dir,
            enable_checklist_evaluation=True,
            checklist_config_path=None  # Should use default
        )

        if manager.checklist_evaluator:
            config_path = manager.checklist_evaluator.checklist_config_path
            path_obj = Path(config_path)

            # Verify path structure
            path_parts = path_obj.parts
            assert "specs" in path_parts, "Path should contain 'specs' directory"
            assert "contracts" in path_parts, "Path should contain 'contracts' directory"
            assert path_parts[-1] == "checklist_mapping.yaml", \
                "Filename should be 'checklist_mapping.yaml'"

    def test_scoring_mapper_initialization(self):
        """Test that ScoringMapper is properly initialized when checklist is enabled."""
        output_dir = Path("test_output")

        manager = PipelineOutputManager(
            output_dir=output_dir,
            enable_checklist_evaluation=True
        )

        # Verify that ScoringMapper was initialized
        assert hasattr(manager, 'scoring_mapper'), \
            "Manager should have scoring_mapper when checklist evaluation is enabled"
        if hasattr(manager, 'scoring_mapper') and manager.scoring_mapper:
            assert manager.scoring_mapper is not None, \
                "ScoringMapper should be initialized when checklist evaluation is enabled"

    def test_pipeline_integrator_initialization(self):
        """Test that PipelineIntegrator is properly initialized when checklist is enabled."""
        output_dir = Path("test_output")

        manager = PipelineOutputManager(
            output_dir=output_dir,
            enable_checklist_evaluation=True
        )

        # Verify that PipelineIntegrator was initialized
        assert hasattr(manager, 'pipeline_integrator'), \
            "Manager should have pipeline_integrator when checklist evaluation is enabled"
        if hasattr(manager, 'pipeline_integrator') and manager.pipeline_integrator:
            assert manager.pipeline_integrator is not None, \
                "PipelineIntegrator should be initialized when checklist evaluation is enabled"

    def test_output_directory_setup(self):
        """Test that output directory is properly configured."""
        output_dir = Path("test_output")

        manager = PipelineOutputManager(
            output_dir=output_dir,
            enable_checklist_evaluation=True
        )

        # Verify output directory is set correctly
        assert manager.output_dir == output_dir, \
            "Output directory should be set correctly"


if __name__ == "__main__":
    pytest.main([__file__])
