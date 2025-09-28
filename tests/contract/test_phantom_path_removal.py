"""
Contract tests specifically for phantom path removal validation.

These tests ensure the specific phantom paths (evaluation_summary,
category_breakdowns, warnings_log) are properly removed from evidence_paths.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from src.metrics.scoring_mapper import ScoringMapper
from src.metrics.models.evaluation_result import EvaluationResult, ChecklistItem
from src.metrics.models.evidence_reference import EvidenceReference


class TestPhantomPathRemovalContract:
    """Contract tests for specific phantom path removal."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scoring_mapper = ScoringMapper()

    def test_evaluation_summary_phantom_path_removed(self):
        """Contract: 'evaluation_summary' key must not appear in evidence_paths."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                mock_evaluation, str(temp_dir)
            )

            # ASSERT: evaluation_summary key should not be present
            assert "evaluation_summary" not in result, \
                "Phantom path 'evaluation_summary' should be removed from evidence_paths"

    def test_category_breakdowns_phantom_path_removed(self):
        """Contract: 'category_breakdowns' key must not appear in evidence_paths."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                mock_evaluation, str(temp_dir)
            )

            # ASSERT: category_breakdowns key should not be present
            assert "category_breakdowns" not in result, \
                "Phantom path 'category_breakdowns' should be removed from evidence_paths"

    def test_warnings_log_phantom_path_removed(self):
        """Contract: 'warnings_log' key must not appear in evidence_paths."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                mock_evaluation, str(temp_dir)
            )

            # ASSERT: warnings_log key should not be present
            assert "warnings_log" not in result, \
                "Phantom path 'warnings_log' should be removed from evidence_paths"

    def test_all_phantom_paths_removed_simultaneously(self):
        """Contract: All three phantom paths must be absent simultaneously."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                mock_evaluation, str(temp_dir)
            )

            # ASSERT: All phantom paths should be absent
            phantom_paths = ["evaluation_summary", "category_breakdowns", "warnings_log"]
            for phantom_path in phantom_paths:
                assert phantom_path not in result, \
                    f"Phantom path '{phantom_path}' should be removed from evidence_paths"

    def test_phantom_file_references_do_not_exist(self):
        """Contract: Phantom file paths should point to non-existent files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Define what the phantom paths would point to (if they existed)
            phantom_file_paths = {
                "evaluation_summary": evidence_base / "evaluation_summary.json",
                "category_breakdowns": evidence_base / "category_breakdowns.json",
                "warnings_log": evidence_base / "warnings.log"
            }

            # ASSERT: These files should not exist (confirming they are phantom)
            for phantom_name, phantom_path in phantom_file_paths.items():
                assert not phantom_path.exists(), \
                    f"Phantom file {phantom_path} should not exist (confirming it's phantom)"

    def test_evidence_paths_only_contain_verifiable_files(self):
        """Contract: Only evidence files that can be verified as existing should be included."""
        # ARRANGE: Create a mixed scenario with real and phantom references
        mock_item = Mock(spec=ChecklistItem,
                        id="code_quality_lint",
                        dimension="code_quality",
                        evidence_references=[
                            Mock(spec=EvidenceReference, source_type="lint_results")
                        ])
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = [mock_item]

        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Create only some evidence files (simulating partial file creation)
            (evidence_base / "code_quality").mkdir()
            real_file = evidence_base / "code_quality" / "code_quality_lint_lint_results.json"
            real_file.write_text('{"test": "data"}')

            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                mock_evaluation, str(temp_dir)
            )

            # ASSERT: Only verifiable files should be included
            for evidence_key, file_path in result.items():
                assert Path(file_path).exists(), \
                    f"Evidence file {file_path} for key '{evidence_key}' must exist and be verifiable"

    def test_phantom_paths_removed_with_mixed_real_evidence(self):
        """Contract: Phantom paths removed even when real evidence files exist."""
        # ARRANGE: Create real evidence files
        mock_items = [
            Mock(spec=ChecklistItem,
                 id="code_quality_lint",
                 dimension="code_quality",
                 evidence_references=[
                     Mock(spec=EvidenceReference, source_type="lint_results")
                 ]),
            Mock(spec=ChecklistItem,
                 id="testing_coverage",
                 dimension="testing",
                 evidence_references=[
                     Mock(spec=EvidenceReference, source_type="test_results")
                 ])
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
            file1.write_text('{"test": "data"}')
            file2.write_text('{"test": "data"}')

            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                mock_evaluation, str(temp_dir)
            )

            # ASSERT: Real evidence should be present, phantom paths should be absent
            assert len(result) > 0, "Real evidence files should be included"

            # Check real evidence files are included
            real_evidence_found = False
            for key in result.keys():
                if key.startswith("code_quality_lint") or key.startswith("testing_coverage"):
                    real_evidence_found = True

            assert real_evidence_found, "Real evidence files should be included in evidence_paths"

            # Check phantom paths are absent
            phantom_paths = ["evaluation_summary", "category_breakdowns", "warnings_log"]
            for phantom_path in phantom_paths:
                assert phantom_path not in result, \
                    f"Phantom path '{phantom_path}' should be absent even with real evidence present"

    def test_evidence_paths_file_extension_validation(self):
        """Contract: Evidence paths should point to appropriate file extensions."""
        mock_evaluation = Mock(spec=EvaluationResult)
        mock_evaluation.checklist_items = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                mock_evaluation, str(temp_dir)
            )

            # ASSERT: All paths should have appropriate extensions (.json, .log, etc.)
            for evidence_key, file_path in result.items():
                path_obj = Path(file_path)
                assert path_obj.suffix in ['.json', '.log', '.txt'], \
                    f"Evidence file {file_path} should have appropriate extension (.json, .log, .txt)"

                # Phantom paths should not be present with any extension
                phantom_stems = ["evaluation_summary", "category_breakdowns", "warnings"]
                for phantom_stem in phantom_stems:
                    assert phantom_stem not in path_obj.stem, \
                        f"Evidence path should not contain phantom stem '{phantom_stem}'"