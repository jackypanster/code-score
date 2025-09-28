"""
Unit tests for evidence validation edge cases and comprehensive validation.

These tests validate the evidence validation models and utility functions
for edge cases and comprehensive scenarios.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.metrics.models.evidence_validation import (
    EvidencePathsMapping,
    EvidencePathsCollection,
    EvidenceFileMetadata,
    ValidationResult,
    validate_evidence_paths,
    clean_evidence_paths
)


class TestEvidencePathsMappingValidation:
    """Unit tests for EvidencePathsMapping validation edge cases."""

    def test_evidence_paths_mapping_valid_creation(self):
        """Test valid EvidencePathsMapping creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test_evidence.json"
            test_file.write_text('{"test": "data"}')

            # Create valid mapping
            mapping = EvidencePathsMapping(
                evidence_key="code_quality_lint_results",
                file_path=str(test_file),
                dimension="code_quality",
                source_type="lint_results"
            )

            assert mapping.evidence_key == "code_quality_lint_results"
            assert mapping.file_path == str(test_file)
            assert mapping.dimension == "code_quality"
            assert mapping.source_type == "lint_results"

    def test_evidence_paths_mapping_nonexistent_file_error(self):
        """Test EvidencePathsMapping validation fails for nonexistent files."""
        with pytest.raises(ValueError, match="Evidence file does not exist"):
            EvidencePathsMapping(
                evidence_key="test_key",
                file_path="/nonexistent/path/file.json",
                dimension="code_quality",
                source_type="lint_results"
            )

    def test_evidence_paths_mapping_directory_not_file_error(self):
        """Test EvidencePathsMapping validation fails for directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Evidence path is not a file"):
                EvidencePathsMapping(
                    evidence_key="test_key",
                    file_path=temp_dir,  # Directory, not file
                    dimension="code_quality",
                    source_type="lint_results"
                )

    def test_evidence_paths_mapping_invalid_key_pattern(self):
        """Test EvidencePathsMapping validation fails for invalid key patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')

            with pytest.raises(ValueError, match="Evidence key must contain underscore separator"):
                EvidencePathsMapping(
                    evidence_key="invalidkey",  # No underscore
                    file_path=str(test_file),
                    dimension="code_quality",
                    source_type="lint_results"
                )

    def test_evidence_paths_mapping_invalid_dimension(self):
        """Test EvidencePathsMapping validation fails for invalid dimensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')

            with pytest.raises(ValueError, match="Dimension must be one of"):
                EvidencePathsMapping(
                    evidence_key="test_key",
                    file_path=str(test_file),
                    dimension="invalid_dimension",
                    source_type="lint_results"
                )


class TestEvidencePathsCollectionValidation:
    """Unit tests for EvidencePathsCollection validation edge cases."""

    def test_evidence_paths_collection_valid_creation(self):
        """Test valid EvidencePathsCollection creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = Path(temp_dir) / "file1.json"
            file2 = Path(temp_dir) / "file2.json"
            file1.write_text('{"test": "data1"}')
            file2.write_text('{"test": "data2"}')

            evidence_paths = {
                "key1": str(file1),
                "key2": str(file2)
            }

            collection = EvidencePathsCollection(
                evidence_paths=evidence_paths,
                evidence_base_path=temp_dir,
                total_evidence_files=2
            )

            assert len(collection.evidence_paths) == 2
            assert collection.total_evidence_files == 2

    def test_evidence_paths_collection_nonexistent_file_error(self):
        """Test EvidencePathsCollection validation fails for nonexistent files."""
        evidence_paths = {
            "key1": "/nonexistent/file1.json",
            "key2": "/nonexistent/file2.json"
        }

        with pytest.raises(ValueError, match="Evidence file does not exist"):
            EvidencePathsCollection(
                evidence_paths=evidence_paths,
                evidence_base_path="/tmp",
                total_evidence_files=2
            )

    def test_evidence_paths_collection_count_mismatch_error(self):
        """Test EvidencePathsCollection validation fails for count mismatch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "file1.json"
            file1.write_text('{"test": "data1"}')

            evidence_paths = {"key1": str(file1)}

            with pytest.raises(ValueError, match="Total evidence files count"):
                EvidencePathsCollection(
                    evidence_paths=evidence_paths,
                    evidence_base_path=temp_dir,
                    total_evidence_files=5  # Mismatch: 1 file but claims 5
                )


class TestEvidenceFileMetadataValidation:
    """Unit tests for EvidenceFileMetadata validation edge cases."""

    def test_evidence_file_metadata_valid_creation(self):
        """Test valid EvidenceFileMetadata creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')

            metadata = EvidenceFileMetadata(
                file_path=str(test_file),
                evidence_key="test_key",
                file_size=test_file.stat().st_size,
                content_type="checklist_item"
            )

            assert metadata.file_path == str(test_file)
            assert metadata.evidence_key == "test_key"
            assert metadata.file_size > 0
            assert metadata.content_type == "checklist_item"

    def test_evidence_file_metadata_nonexistent_file_error(self):
        """Test EvidenceFileMetadata validation fails for nonexistent files."""
        with pytest.raises(ValueError, match="Evidence file does not exist"):
            EvidenceFileMetadata(
                file_path="/nonexistent/file.json",
                evidence_key="test_key",
                file_size=100,
                content_type="checklist_item"
            )

    def test_evidence_file_metadata_zero_file_size_error(self):
        """Test EvidenceFileMetadata validation fails for zero file size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')

            with pytest.raises(ValueError, match="Evidence file must be non-empty"):
                EvidenceFileMetadata(
                    file_path=str(test_file),
                    evidence_key="test_key",
                    file_size=0,  # Invalid zero size
                    content_type="checklist_item"
                )

    def test_evidence_file_metadata_invalid_content_type_error(self):
        """Test EvidenceFileMetadata validation fails for invalid content type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')

            with pytest.raises(ValueError, match="Content type must be one of"):
                EvidenceFileMetadata(
                    file_path=str(test_file),
                    evidence_key="test_key",
                    file_size=test_file.stat().st_size,
                    content_type="invalid_type"
                )

    def test_evidence_file_metadata_unreadable_file_error(self):
        """Test EvidenceFileMetadata validation fails for unreadable files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')

            # Mock file to be unreadable
            with patch.object(Path, 'read_bytes', side_effect=PermissionError("Access denied")):
                with pytest.raises(ValueError, match="Evidence file not readable"):
                    EvidenceFileMetadata(
                        file_path=str(test_file),
                        evidence_key="test_key",
                        file_size=test_file.stat().st_size,
                        content_type="checklist_item"
                    )


class TestValidateEvidencePathsFunction:
    """Unit tests for validate_evidence_paths function edge cases."""

    def test_validate_evidence_paths_empty_dict(self):
        """Test validate_evidence_paths with empty evidence paths."""
        result = validate_evidence_paths({})

        assert result.is_valid is True
        assert result.total_paths_checked == 0
        assert result.valid_paths_count == 0
        assert len(result.invalid_paths) == 0
        assert len(result.phantom_paths_removed) == 0

    def test_validate_evidence_paths_all_phantom_paths(self):
        """Test validate_evidence_paths with all phantom paths."""
        phantom_evidence = {
            "evaluation_summary": "/path/to/evaluation_summary.json",
            "category_breakdowns": "/path/to/category_breakdowns.json",
            "warnings_log": "/path/to/warnings.log"
        }

        result = validate_evidence_paths(phantom_evidence)

        assert result.is_valid is False
        assert result.total_paths_checked == 3
        assert result.valid_paths_count == 0
        assert len(result.phantom_paths_removed) == 3
        assert "evaluation_summary" in result.phantom_paths_removed
        assert "category_breakdowns" in result.phantom_paths_removed
        assert "warnings_log" in result.phantom_paths_removed

    def test_validate_evidence_paths_mixed_valid_invalid(self):
        """Test validate_evidence_paths with mixed valid and invalid paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create one valid file
            valid_file = Path(temp_dir) / "valid.json"
            valid_file.write_text('{"test": "data"}')

            evidence_paths = {
                "valid_key": str(valid_file),
                "invalid_key": "/nonexistent/file.json",
                "evaluation_summary": "/path/to/phantom.json"  # Phantom path
            }

            result = validate_evidence_paths(evidence_paths)

            assert result.is_valid is False
            assert result.total_paths_checked == 3
            assert result.valid_paths_count == 1
            assert len(result.invalid_paths) == 1
            assert len(result.phantom_paths_removed) == 1
            assert "invalid_key" in result.invalid_paths
            assert "evaluation_summary" in result.phantom_paths_removed

    def test_validate_evidence_paths_empty_files_invalid(self):
        """Test validate_evidence_paths treats empty files as invalid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty file
            empty_file = Path(temp_dir) / "empty.json"
            empty_file.touch()  # Creates empty file

            evidence_paths = {"empty_key": str(empty_file)}
            result = validate_evidence_paths(evidence_paths)

            assert result.is_valid is False
            assert result.valid_paths_count == 0
            assert "empty_key" in result.invalid_paths

    def test_validate_evidence_paths_directory_instead_of_file(self):
        """Test validate_evidence_paths fails for directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_paths = {"dir_key": temp_dir}  # Directory, not file
            result = validate_evidence_paths(evidence_paths)

            assert result.is_valid is False
            assert result.valid_paths_count == 0
            assert "dir_key" in result.invalid_paths

    def test_validate_evidence_paths_file_permission_error(self):
        """Test validate_evidence_paths handles permission errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')

            evidence_paths = {"test_key": str(test_file)}

            # Mock file.stat() to raise permission error
            with patch.object(Path, 'stat', side_effect=PermissionError("Access denied")):
                result = validate_evidence_paths(evidence_paths)

                assert result.is_valid is False
                assert "test_key" in result.invalid_paths

    def test_validate_evidence_paths_recommendations_generated(self):
        """Test validate_evidence_paths generates appropriate recommendations."""
        phantom_evidence = {
            "evaluation_summary": "/path/to/phantom.json",
            "invalid_key": "/nonexistent/file.json"
        }

        result = validate_evidence_paths(phantom_evidence)

        assert len(result.recommendations) >= 2
        assert any("phantom path" in rec.lower() for rec in result.recommendations)
        assert any("evidence files are created" in rec.lower() for rec in result.recommendations)


class TestCleanEvidencePathsFunction:
    """Unit tests for clean_evidence_paths function edge cases."""

    def test_clean_evidence_paths_empty_dict(self):
        """Test clean_evidence_paths with empty evidence paths."""
        result = clean_evidence_paths({})
        assert result == {}

    def test_clean_evidence_paths_all_phantom_paths_removed(self):
        """Test clean_evidence_paths removes all phantom paths."""
        phantom_evidence = {
            "evaluation_summary": "/path/to/evaluation_summary.json",
            "category_breakdowns": "/path/to/category_breakdowns.json",
            "warnings_log": "/path/to/warnings.log"
        }

        result = clean_evidence_paths(phantom_evidence)
        assert result == {}

    def test_clean_evidence_paths_preserves_valid_files(self):
        """Test clean_evidence_paths preserves valid existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid files
            file1 = Path(temp_dir) / "file1.json"
            file2 = Path(temp_dir) / "file2.json"
            file1.write_text('{"test": "data1"}')
            file2.write_text('{"test": "data2"}')

            evidence_paths = {
                "valid_key1": str(file1),
                "valid_key2": str(file2),
                "evaluation_summary": "/path/to/phantom.json",  # Should be removed
                "invalid_key": "/nonexistent/file.json"  # Should be removed
            }

            result = clean_evidence_paths(evidence_paths)

            assert len(result) == 2
            assert "valid_key1" in result
            assert "valid_key2" in result
            assert "evaluation_summary" not in result
            assert "invalid_key" not in result

    def test_clean_evidence_paths_removes_empty_files(self):
        """Test clean_evidence_paths removes empty files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty file
            empty_file = Path(temp_dir) / "empty.json"
            empty_file.touch()

            # Create valid file
            valid_file = Path(temp_dir) / "valid.json"
            valid_file.write_text('{"test": "data"}')

            evidence_paths = {
                "empty_key": str(empty_file),
                "valid_key": str(valid_file)
            }

            result = clean_evidence_paths(evidence_paths)

            assert len(result) == 1
            assert "valid_key" in result
            assert "empty_key" not in result

    def test_clean_evidence_paths_removes_directories(self):
        """Test clean_evidence_paths removes directory paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid file
            valid_file = Path(temp_dir) / "valid.json"
            valid_file.write_text('{"test": "data"}')

            evidence_paths = {
                "dir_key": temp_dir,  # Directory
                "valid_key": str(valid_file)
            }

            result = clean_evidence_paths(evidence_paths)

            assert len(result) == 1
            assert "valid_key" in result
            assert "dir_key" not in result

    def test_clean_evidence_paths_handles_exceptions_gracefully(self):
        """Test clean_evidence_paths handles file system exceptions gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_file = Path(temp_dir) / "valid.json"
            valid_file.write_text('{"test": "data"}')

            evidence_paths = {
                "valid_key": str(valid_file),
                "problematic_key": "/some/path/that/causes/issues.json"
            }

            # Mock Path.exists() to raise an exception for the problematic path
            original_exists = Path.exists

            def mock_exists(self):
                if "problematic_key" in str(self):
                    raise OSError("Simulated file system error")
                return original_exists(self)

            with patch.object(Path, 'exists', mock_exists):
                result = clean_evidence_paths(evidence_paths)

                # Should still include valid paths
                assert "valid_key" in result
                # Should exclude problematic path
                assert "problematic_key" not in result


class TestValidationResultModel:
    """Unit tests for ValidationResult model edge cases."""

    def test_validation_result_summary_property(self):
        """Test ValidationResult validation_summary property calculation."""
        result = ValidationResult(
            is_valid=False,
            total_paths_checked=10,
            valid_paths_count=5,
            invalid_paths=["path1", "path2"],
            validation_errors=["error1", "error2"],
            phantom_paths_removed=["phantom1"],
            recommendations=["rec1", "rec2"]
        )

        summary = result.validation_summary
        assert summary["total_checked"] == 10
        assert summary["valid"] == 5
        assert summary["invalid"] == 2
        assert summary["phantom_removed"] == 1

    def test_validation_result_empty_lists(self):
        """Test ValidationResult with empty error lists."""
        result = ValidationResult(
            is_valid=True,
            total_paths_checked=5,
            valid_paths_count=5,
            invalid_paths=[],
            validation_errors=[],
            phantom_paths_removed=[],
            recommendations=[]
        )

        assert result.is_valid is True
        assert len(result.invalid_paths) == 0
        assert len(result.validation_errors) == 0
        assert len(result.phantom_paths_removed) == 0
        assert len(result.recommendations) == 0