"""
Unit tests for ScoringMapper._generate_evidence_paths phantom path removal.

These tests specifically validate the ScoringMapper._generate_evidence_paths
method behavior for phantom path removal and file existence validation.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from src.metrics.scoring_mapper import ScoringMapper
from src.metrics.models.evaluation_result import EvaluationResult, ChecklistItem
from src.metrics.models.evidence_reference import EvidenceReference


class TestScoringMapperEvidencePathsUnit:
    """Unit tests for ScoringMapper evidence paths generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scoring_mapper = ScoringMapper()

    def test_generate_evidence_paths_excludes_phantom_evaluation_summary(self):
        """Unit test: _generate_evidence_paths excludes phantom evaluation_summary."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT
            assert "evaluation_summary" not in result, \
                "evaluation_summary phantom path should not be in evidence_paths"

    def test_generate_evidence_paths_excludes_phantom_category_breakdowns(self):
        """Unit test: _generate_evidence_paths excludes phantom category_breakdowns."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT
            assert "category_breakdowns" not in result, \
                "category_breakdowns phantom path should not be in evidence_paths"

    def test_generate_evidence_paths_excludes_phantom_warnings_log(self):
        """Unit test: _generate_evidence_paths excludes phantom warnings_log."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT
            assert "warnings_log" not in result, \
                "warnings_log phantom path should not be in evidence_paths"

    def test_generate_evidence_paths_validates_file_existence(self):
        """Unit test: _generate_evidence_paths validates file existence before inclusion."""
        # ARRANGE: Create mock with evidence references
        mock_evidence_ref = Mock(spec=EvidenceReference)
        mock_evidence_ref.source_type = "lint_results"

        mock_item = Mock(spec=ChecklistItem)
        mock_item.id = "code_quality_lint"
        mock_item.dimension = "code_quality"
        mock_item.evidence_references = [mock_evidence_ref]

        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = [mock_item]

        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Create the expected evidence file
            (evidence_base / "code_quality").mkdir()
            evidence_file = evidence_base / "code_quality" / "code_quality_lint_lint_results.json"
            evidence_file.write_text('{"test": "data"}')

            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT: Only existing files should be included
            for evidence_key, file_path in result.items():
                assert Path(file_path).exists(), \
                    f"Evidence file {file_path} for key '{evidence_key}' must exist"

    def test_generate_evidence_paths_excludes_nonexistent_files(self):
        """Unit test: _generate_evidence_paths excludes non-existent files."""
        # ARRANGE: Create mock with evidence references but don't create files
        mock_evidence_ref = Mock(spec=EvidenceReference)
        mock_evidence_ref.source_type = "lint_results"

        mock_item = Mock(spec=ChecklistItem)
        mock_item.id = "code_quality_lint"
        mock_item.dimension = "code_quality"
        mock_item.evidence_references = [mock_evidence_ref]

        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = [mock_item]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't create any evidence files

            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT: No paths should be included since files don't exist
            for evidence_key, file_path in result.items():
                assert Path(file_path).exists(), \
                    f"Non-existent file {file_path} should not be in evidence_paths"

    def test_generate_evidence_paths_handles_empty_checklist_items(self):
        """Unit test: _generate_evidence_paths handles empty checklist items."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT: Should return empty dict or dict without phantom paths
            phantom_paths = ["evaluation_summary", "category_breakdowns", "warnings_log"]
            for phantom_path in phantom_paths:
                assert phantom_path not in result, \
                    f"Phantom path '{phantom_path}' should not be present even with empty checklist"

    def test_generate_evidence_paths_preserves_real_evidence_files(self):
        """Unit test: _generate_evidence_paths preserves real evidence files."""
        # ARRANGE: Create multiple real evidence files
        mock_evidence_refs = [
            Mock(spec=EvidenceReference, source_type="lint_results"),
            Mock(spec=EvidenceReference, source_type="test_results")
        ]

        mock_items = [
            Mock(spec=ChecklistItem,
                 id="code_quality_lint",
                 dimension="code_quality",
                 evidence_references=[mock_evidence_refs[0]]),
            Mock(spec=ChecklistItem,
                 id="testing_coverage",
                 dimension="testing",
                 evidence_references=[mock_evidence_refs[1]])
        ]

        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = mock_items

        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Create real evidence files
            (evidence_base / "code_quality").mkdir()
            (evidence_base / "testing").mkdir()
            file1 = evidence_base / "code_quality" / "code_quality_lint_lint_results.json"
            file2 = evidence_base / "testing" / "testing_coverage_test_results.json"
            file1.write_text('{"test": "data1"}')
            file2.write_text('{"test": "data2"}')

            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT: Real evidence files should be preserved
            assert len(result) >= 2, "Real evidence files should be preserved"

            for evidence_key, file_path in result.items():
                assert Path(file_path).exists(), \
                    f"Real evidence file {file_path} should exist and be preserved"

            # Verify no phantom paths are included
            phantom_paths = ["evaluation_summary", "category_breakdowns", "warnings_log"]
            for phantom_path in phantom_paths:
                assert phantom_path not in result, \
                    f"Phantom path '{phantom_path}' should not be present with real evidence"

    def test_generate_evidence_paths_correct_file_structure(self):
        """Unit test: _generate_evidence_paths generates correct file structure."""
        mock_evidence_ref = Mock(spec=EvidenceReference)
        mock_evidence_ref.source_type = "lint_results"

        mock_item = Mock(spec=ChecklistItem)
        mock_item.id = "code_quality_lint"
        mock_item.dimension = "code_quality"
        mock_item.evidence_references = [mock_evidence_ref]

        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = [mock_item]

        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Create evidence file with expected structure
            (evidence_base / "code_quality").mkdir()
            evidence_file = evidence_base / "code_quality" / "code_quality_lint_lint_results.json"
            evidence_file.write_text('{"test": "data"}')

            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT: File paths should follow expected structure
            for evidence_key, file_path in result.items():
                path_obj = Path(file_path)

                # Should be under evidence_base
                assert evidence_base in path_obj.parents or path_obj.parent == evidence_base, \
                    f"Evidence file {file_path} should be under evidence base directory"

                # Should have appropriate extension
                assert path_obj.suffix in ['.json', '.log', '.txt'], \
                    f"Evidence file {file_path} should have appropriate extension"

    def test_generate_evidence_paths_returns_dict_type(self):
        """Unit test: _generate_evidence_paths returns proper dict type."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT: Should return dict
            assert isinstance(result, dict), "Evidence paths should be returned as dict"

            # All keys should be strings
            for key in result.keys():
                assert isinstance(key, str), f"Evidence key '{key}' should be string"

            # All values should be strings (file paths)
            for value in result.values():
                assert isinstance(value, str), f"Evidence path '{value}' should be string"

    def test_generate_evidence_paths_phantom_removal_comprehensive(self):
        """Unit test: Comprehensive phantom path removal validation."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT
            result = self.scoring_mapper._generate_evidence_paths(mock_evaluation, str(temp_dir))

            # ASSERT: Comprehensive phantom path check
            all_phantom_paths = [
                "evaluation_summary",
                "category_breakdowns",
                "warnings_log",
                # Also check variations that might exist
                "evaluation-summary",
                "category-breakdowns",
                "warnings-log"
            ]

            for phantom_path in all_phantom_paths:
                assert phantom_path not in result, \
                    f"Phantom path '{phantom_path}' should not be in evidence_paths"

            # Check that no phantom file paths exist in values
            for evidence_key, file_path in result.items():
                path_name = Path(file_path).name.lower()
                for phantom in ["evaluation_summary", "category_breakdowns", "warnings"]:
                    assert phantom not in path_name, \
                        f"Evidence path {file_path} should not contain phantom reference '{phantom}'"