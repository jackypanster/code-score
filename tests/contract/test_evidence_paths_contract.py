"""
Contract tests for evidence paths validation and phantom path removal.

These tests validate the contract between ScoringMapper and EvidenceTracker
to ensure evidence_paths only contains existing files.
"""
import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock

from src.metrics.scoring_mapper import ScoringMapper
from src.metrics.models.evaluation_result import EvaluationResult, ChecklistItem
from src.metrics.models.evidence_reference import EvidenceReference


class TestEvidencePathsContract:
    """Contract tests for evidence paths validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scoring_mapper = ScoringMapper()

        # Create mock evaluation result with checklist items
        self.mock_evaluation_result = Mock(spec=EvaluationResult)
        self.mock_evaluation_result.checklist_items = [
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

    def test_evidence_paths_contain_only_existing_files(self):
        """Contract: All paths in evidence_paths must point to existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Create some real evidence files
            (evidence_base / "code_quality").mkdir()
            (evidence_base / "testing").mkdir()
            real_file1 = evidence_base / "code_quality" / "code_quality_lint_lint_results.json"
            real_file2 = evidence_base / "testing" / "testing_coverage_test_results.json"
            real_file1.write_text('{"test": "data"}')
            real_file2.write_text('{"test": "data"}')

            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                self.mock_evaluation_result, str(evidence_base)
            )

            # ASSERT: All paths point to existing files
            for path in result.values():
                assert Path(path).exists(), f"Evidence file {path} must exist"
                assert Path(path).is_file(), f"Evidence path {path} must be a file"

    def test_phantom_paths_are_removed(self):
        """Contract: Phantom paths must be removed from evidence_paths output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                self.mock_evaluation_result, str(evidence_base)
            )

            # ASSERT: No phantom paths in output
            phantom_paths = ["evaluation_summary", "category_breakdowns", "warnings_log"]
            for phantom_path in phantom_paths:
                assert phantom_path not in result, f"Phantom path '{phantom_path}' should be removed"

    def test_score_input_evidence_paths_schema_validation(self):
        """Contract: score_input.json evidence_paths must follow valid schema."""
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Create real evidence files to avoid validation errors
            (evidence_base / "code_quality").mkdir()
            real_file = evidence_base / "code_quality" / "code_quality_lint_lint_results.json"
            real_file.write_text('{"test": "data"}')

            # ACT: Generate evidence paths
            evidence_paths = self.scoring_mapper._generate_evidence_paths(
                self.mock_evaluation_result, str(evidence_base)
            )

            # ASSERT: Schema validation rules
            # All values must be strings (file paths)
            assert all(isinstance(path, str) for path in evidence_paths.values())

            # Keys must follow evidence key pattern (item_id_source_type)
            for key in evidence_paths.keys():
                assert "_" in key, f"Evidence key '{key}' should contain underscore separator"

            # No phantom path keys should be present
            phantom_keys = ["evaluation_summary", "category_breakdowns", "warnings_log"]
            for phantom_key in phantom_keys:
                assert phantom_key not in evidence_paths, f"Phantom key '{phantom_key}' should not be in evidence_paths"

    def test_evidence_paths_validation_error_handling(self):
        """Contract: System must handle non-existent file paths gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Don't create any files - all paths will be non-existent

            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                self.mock_evaluation_result, str(evidence_base)
            )

            # ASSERT: Only paths to existing files should be included
            for path in result.values():
                assert Path(path).exists(), f"Non-existent path {path} should not be in evidence_paths"

    def test_evidence_tracker_scoring_mapper_consistency(self):
        """Contract: EvidenceTracker output must align with ScoringMapper expectations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)

            # Simulate EvidenceTracker.save_evidence_files() output pattern
            (evidence_base / "code_quality").mkdir()
            (evidence_base / "testing").mkdir()

            evidence_file1 = evidence_base / "code_quality" / "code_quality_lint_lint_results.json"
            evidence_file2 = evidence_base / "testing" / "testing_coverage_test_results.json"
            summary_file = evidence_base / "evidence_summary.json"
            manifest_file = evidence_base / "manifest.json"

            # Create the actual files (simulating EvidenceTracker behavior)
            for file_path in [evidence_file1, evidence_file2, summary_file, manifest_file]:
                file_path.write_text('{"test": "data"}')

            # ACT: Generate evidence paths
            scorer_evidence_paths = self.scoring_mapper._generate_evidence_paths(
                self.mock_evaluation_result, str(evidence_base)
            )

            # ASSERT: All paths in scorer output should point to existing files
            for evidence_key, file_path in scorer_evidence_paths.items():
                assert Path(file_path).exists(), f"Evidence file {file_path} must exist"
                assert Path(file_path).is_file(), f"Evidence path {file_path} must be a file"
                assert Path(file_path).stat().st_size > 0, f"Evidence file {file_path} must not be empty"


class TestPhantomPathRemovalValidation:
    """Specific tests for phantom path removal functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scoring_mapper = ScoringMapper()
        self.mock_evaluation_result = Mock(spec=EvaluationResult)
        self.mock_evaluation_result.checklist_items = []

    def test_hardcoded_phantom_paths_are_identified(self):
        """Verify the specific phantom paths that need removal."""
        phantom_paths = [
            "evaluation_summary",     # Points to evaluation_summary.json (never created)
            "category_breakdowns",    # Points to category_breakdowns.json (never created)
            "warnings_log"           # Points to warnings.log (never created)
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            # ACT: Generate evidence paths
            actual_evidence_paths = self.scoring_mapper._generate_evidence_paths(
                self.mock_evaluation_result, str(temp_dir)
            )

            # ASSERT: None of the phantom paths should be present
            actual_keys = set(actual_evidence_paths.keys())
            phantom_found = set(phantom_paths).intersection(actual_keys)
            assert len(phantom_found) == 0, f"Found phantom paths that should be removed: {phantom_found}"

    def test_real_evidence_paths_are_preserved(self):
        """Verify that removing phantom paths doesn't affect real evidence paths."""
        # ARRANGE: Evidence paths that should be preserved
        mock_item = Mock(spec=ChecklistItem,
                        id="code_quality_lint",
                        dimension="code_quality",
                        evidence_references=[
                            Mock(spec=EvidenceReference, source_type="lint_results")
                        ])
        self.mock_evaluation_result.checklist_items = [mock_item]

        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_base = Path(temp_dir)
            (evidence_base / "code_quality").mkdir()
            real_file = evidence_base / "code_quality" / "code_quality_lint_lint_results.json"
            real_file.write_text('{"test": "data"}')

            # ACT: Generate evidence paths
            result = self.scoring_mapper._generate_evidence_paths(
                self.mock_evaluation_result, str(temp_dir)
            )

            # ASSERT: Real evidence paths should be preserved
            assert len(result) > 0, "Real evidence paths should be preserved"
            for key, path in result.items():
                assert Path(path).exists(), f"Real evidence path {path} should exist"