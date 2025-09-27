"""Contract test for checklist mapping YAML validation.

This test validates that the checklist mapping YAML file contains all required
evaluation criteria and can be loaded correctly.
"""

import yaml
import pytest
from pathlib import Path

# Get the mapping path relative to the test file
MAPPING_PATH = Path(__file__).parent.parent.parent / "specs" / "002-git-log-docs" / "contracts" / "checklist_mapping.yaml"


class TestChecklistMapping:
    """Test checklist mapping YAML structure and content."""

    @pytest.fixture
    def checklist_mapping(self):
        """Load the checklist mapping YAML file."""
        with open(MAPPING_PATH, 'r') as f:
            return yaml.safe_load(f)

    def test_mapping_file_loads_successfully(self, checklist_mapping):
        """Test that the YAML file loads without errors."""
        assert checklist_mapping is not None
        assert isinstance(checklist_mapping, dict)

    def test_contains_all_required_sections(self, checklist_mapping):
        """Test that mapping contains all required top-level sections."""
        required_sections = ['checklist_items', 'language_adaptations']
        for section in required_sections:
            assert section in checklist_mapping, f"Missing required section: {section}"

    def test_has_exactly_11_checklist_items(self, checklist_mapping):
        """Test that exactly 11 checklist items are defined."""
        items = checklist_mapping['checklist_items']
        assert len(items) == 11, f"Expected 11 checklist items, got {len(items)}"

    def test_checklist_items_have_required_fields(self, checklist_mapping):
        """Test that each checklist item has all required fields."""
        required_fields = ['id', 'name', 'dimension', 'max_points', 'description',
                          'evaluation_criteria', 'metrics_mapping']

        for item in checklist_mapping['checklist_items']:
            for field in required_fields:
                assert field in item, f"Item {item.get('id', 'unknown')} missing field: {field}"

    def test_dimensions_are_valid(self, checklist_mapping):
        """Test that all dimensions are from the allowed set."""
        valid_dimensions = {'code_quality', 'testing', 'documentation'}

        for item in checklist_mapping['checklist_items']:
            dimension = item['dimension']
            assert dimension in valid_dimensions, f"Invalid dimension: {dimension}"

    def test_max_points_sum_to_100(self, checklist_mapping):
        """Test that maximum points across all items sum to 100."""
        total_points = sum(item['max_points'] for item in checklist_mapping['checklist_items'])
        assert total_points == 100, f"Total max points should be 100, got {total_points}"

    def test_evaluation_criteria_structure(self, checklist_mapping):
        """Test that evaluation criteria have correct structure."""
        required_statuses = {'met', 'partial', 'unmet'}

        for item in checklist_mapping['checklist_items']:
            criteria = item['evaluation_criteria']
            assert isinstance(criteria, dict)

            for status in required_statuses:
                assert status in criteria, f"Item {item['id']} missing status: {status}"
                assert isinstance(criteria[status], list), f"Criteria for {status} should be a list"

    def test_metrics_mapping_structure(self, checklist_mapping):
        """Test that metrics mapping has correct structure."""
        for item in checklist_mapping['checklist_items']:
            mapping = item['metrics_mapping']
            assert 'source_path' in mapping, f"Item {item['id']} missing source_path"
            assert 'required_fields' in mapping, f"Item {item['id']} missing required_fields"
            assert isinstance(mapping['required_fields'], list)

    def test_language_adaptations_exist(self, checklist_mapping):
        """Test that language adaptations are defined for supported languages."""
        expected_languages = {'python', 'javascript', 'typescript', 'java', 'go'}
        adaptations = checklist_mapping['language_adaptations']

        for lang in expected_languages:
            assert lang in adaptations, f"Missing language adaptation: {lang}"

    def test_unique_checklist_item_ids(self, checklist_mapping):
        """Test that all checklist item IDs are unique."""
        ids = [item['id'] for item in checklist_mapping['checklist_items']]
        assert len(ids) == len(set(ids)), "Checklist item IDs must be unique"

    def test_point_distribution_by_dimension(self, checklist_mapping):
        """Test that point distribution matches expected allocations."""
        dimension_totals = {}

        for item in checklist_mapping['checklist_items']:
            dimension = item['dimension']
            if dimension not in dimension_totals:
                dimension_totals[dimension] = 0
            dimension_totals[dimension] += item['max_points']

        # Expected distribution from ai-code-review-judgement.md
        expected_totals = {
            'code_quality': 40,
            'testing': 35,
            'documentation': 25
        }

        for dimension, expected in expected_totals.items():
            actual = dimension_totals.get(dimension, 0)
            assert actual == expected, f"Dimension {dimension}: expected {expected} points, got {actual}"

    def test_checklist_loader_not_implemented(self):
        """Test that ChecklistLoader is not yet implemented."""
        # This test will fail until ChecklistLoader is implemented
        with pytest.raises(ImportError):
            from src.metrics.checklist_loader import ChecklistLoader
            ChecklistLoader()

    def test_evaluation_criteria_parsing_not_implemented(self):
        """Test that evaluation criteria parsing is not yet implemented."""
        # This test will fail until criteria parsing logic is implemented
        with pytest.raises(ImportError):
            from src.metrics.scoring_mapper import ScoringMapper
            ScoringMapper()