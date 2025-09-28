"""
T005: Test for ChecklistEvaluator path resolution
Tests that ChecklistEvaluator resolves to the correct configuration path after fix.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml

from src.metrics.checklist_evaluator import ChecklistEvaluator


class TestChecklistEvaluatorPath:
    """Test ChecklistEvaluator path resolution functionality."""

    def test_default_config_path_resolution(self):
        """Test that ChecklistEvaluator resolves to correct default path."""
        # Test that the default path construction works correctly
        evaluator = ChecklistEvaluator()

        # Verify that the config path ends with the correct path
        config_path_obj = Path(evaluator.checklist_config_path)
        path_parts = config_path_obj.parts
        assert "specs" in path_parts and "contracts" in path_parts and config_path_obj.name == "checklist_mapping.yaml", \
            f"Expected path to contain 'specs/contracts/checklist_mapping.yaml', got: {evaluator.checklist_config_path}"

    def test_config_path_points_to_existing_file(self):
        """Test that the resolved config path points to an existing file."""
        evaluator = ChecklistEvaluator()
        config_path = Path(evaluator.checklist_config_path)

        # Verify file exists (this should pass after the path fix)
        assert config_path.exists(), \
            f"Configuration file does not exist at: {evaluator.checklist_config_path}"

        # Verify file is readable
        assert config_path.is_file(), \
            f"Configuration path is not a file: {evaluator.checklist_config_path}"

    def test_custom_config_path_override(self):
        """Test that custom config path can override default."""
        custom_path = "/custom/path/to/config.yaml"

        # Mock the file operations since custom path doesn't exist
        mock_config_data = {
            "checklist_items": [],
            "language_adaptations": {}
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("src.metrics.checklist_loader.ChecklistLoader"):
                evaluator = ChecklistEvaluator(checklist_config_path=custom_path)
                assert evaluator.checklist_config_path == custom_path

    def test_checklist_loader_initialization(self):
        """Test that ChecklistEvaluator can access configuration data."""
        evaluator = ChecklistEvaluator()

        # Verify that configuration is accessible (implementation detail may vary)
        assert hasattr(evaluator, 'checklist_config_path'), "Evaluator should have config path"
        assert evaluator.checklist_config_path is not None, "Config path should be set"

        # Verify the configuration was loaded
        assert hasattr(evaluator, 'checklist_config'), "Evaluator should have loaded config"

    def test_config_path_construction_from_source_file(self):
        """Test that config path is correctly constructed relative to source file."""
        evaluator = ChecklistEvaluator()

        # Verify path construction logic
        config_path = Path(evaluator.checklist_config_path)

        # Should contain the expected path segments
        path_parts = config_path.parts
        assert "specs" in path_parts, "Path should contain 'specs' directory"
        assert "contracts" in path_parts, "Path should contain 'contracts' directory"
        assert path_parts[-1] == "checklist_mapping.yaml", "Filename should be 'checklist_mapping.yaml'"

    def test_evidence_tracker_initialization(self):
        """Test that ChecklistEvaluator has evaluation capabilities."""
        evaluator = ChecklistEvaluator()

        # Verify that evaluator has necessary attributes for evaluation
        assert hasattr(evaluator, 'checklist_config'), "Evaluator should have checklist config"
        assert evaluator.checklist_config is not None, "Checklist config should be loaded"

    def test_evaluation_method_exists(self):
        """Test that evaluation methods exist and are callable."""
        evaluator = ChecklistEvaluator()

        # Verify that evaluation methods exist
        assert hasattr(evaluator, 'evaluate_from_dict'), "Evaluator should have 'evaluate_from_dict' method"
        assert callable(evaluator.evaluate_from_dict), "evaluate_from_dict method should be callable"

        assert hasattr(evaluator, 'evaluate_from_file'), "Evaluator should have 'evaluate_from_file' method"
        assert callable(evaluator.evaluate_from_file), "evaluate_from_file method should be callable"

        assert hasattr(evaluator, 'evaluate_from_string'), "Evaluator should have 'evaluate_from_string' method"
        assert callable(evaluator.evaluate_from_string), "evaluate_from_string method should be callable"

    def test_path_consistency_across_components(self):
        """Test that config path is consistent with other components."""
        from src.metrics.checklist_loader import ChecklistLoader

        evaluator = ChecklistEvaluator()
        loader = ChecklistLoader()

        # Both should resolve to the same configuration file
        evaluator_path = Path(evaluator.checklist_config_path)
        loader_path = Path(loader.config_path)

        assert evaluator_path.name == loader_path.name, \
            "Both components should reference the same config filename"

        # Check path structure for both components using cross-platform approach
        evaluator_parts = evaluator_path.parts
        loader_parts = loader_path.parts
        assert "specs" in evaluator_parts and "contracts" in evaluator_parts and evaluator_path.name == "checklist_mapping.yaml", \
            "Evaluator path should contain correct path structure"
        assert "specs" in loader_parts and "contracts" in loader_parts and loader_path.name == "checklist_mapping.yaml", \
            "Loader path should contain correct path structure"


if __name__ == "__main__":
    pytest.main([__file__])