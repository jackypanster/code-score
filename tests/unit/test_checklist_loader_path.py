"""
T004: Test for ChecklistLoader path resolution
Tests that ChecklistLoader resolves to the correct configuration path after fix.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml

from src.metrics.checklist_loader import ChecklistLoader


class TestChecklistLoaderPath:
    """Test ChecklistLoader path resolution functionality."""

    def test_default_config_path_resolution(self):
        """Test that ChecklistLoader resolves to correct default path."""
        # Test that the default path construction works correctly
        loader = ChecklistLoader()

        # Verify that the config path ends with the correct path
        config_path_obj = Path(loader.config_path)
        path_parts = config_path_obj.parts
        assert "specs" in path_parts and "contracts" in path_parts and config_path_obj.name == "checklist_mapping.yaml", \
            f"Expected path to contain 'specs/contracts/checklist_mapping.yaml', got: {loader.config_path}"

    def test_config_path_points_to_existing_file(self):
        """Test that the resolved config path points to an existing file."""
        loader = ChecklistLoader()
        config_path = Path(loader.config_path)

        # Verify file exists (this should pass after the path fix)
        assert config_path.exists(), \
            f"Configuration file does not exist at: {loader.config_path}"

        # Verify file is readable
        assert config_path.is_file(), \
            f"Configuration path is not a file: {loader.config_path}"

    def test_custom_config_path_override(self):
        """Test that custom config path can override default."""
        custom_path = "/custom/path/to/config.yaml"

        # Mock the file operations since custom path doesn't exist
        mock_config_data = {
            "checklist_items": [],
            "language_adaptations": {}
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            loader = ChecklistLoader(config_path=custom_path)
            assert loader.config_path == custom_path

    def test_config_loading_succeeds_with_correct_path(self):
        """Test that configuration loading succeeds with the correct path."""
        loader = ChecklistLoader()

        # Verify that config data was loaded successfully
        assert loader.config_data is not None, "Config data should not be None"
        assert isinstance(loader.config_data, dict), "Config data should be a dictionary"

        # Verify expected keys exist in config
        assert "checklist_items" in loader.config_data, "Config should contain 'checklist_items'"
        assert "language_adaptations" in loader.config_data, "Config should contain 'language_adaptations'"

    def test_config_path_construction_from_source_file(self):
        """Test that config path is correctly constructed relative to source file."""
        loader = ChecklistLoader()

        # Verify path construction logic
        # The path should be relative to the source file location
        config_path = Path(loader.config_path)

        # Should contain the expected path segments
        path_parts = config_path.parts
        assert "specs" in path_parts, "Path should contain 'specs' directory"
        assert "contracts" in path_parts, "Path should contain 'contracts' directory"
        assert path_parts[-1] == "checklist_mapping.yaml", "Filename should be 'checklist_mapping.yaml'"

    def test_checklist_items_config_access(self):
        """Test that checklist items configuration is accessible."""
        loader = ChecklistLoader()

        # Verify checklist items config is accessible
        assert hasattr(loader, 'checklist_items_config'), "Loader should have checklist_items_config attribute"
        assert isinstance(loader.checklist_items_config, list), "Checklist items config should be a list"

    def test_language_adaptations_access(self):
        """Test that language adaptations configuration is accessible."""
        loader = ChecklistLoader()

        # Verify language adaptations are accessible
        assert hasattr(loader, 'language_adaptations'), "Loader should have language_adaptations attribute"
        assert isinstance(loader.language_adaptations, dict), "Language adaptations should be a dictionary"


if __name__ == "__main__":
    pytest.main([__file__])