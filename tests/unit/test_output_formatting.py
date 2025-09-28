"""Unit tests for output formatting functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.metrics.models.metrics_collection import ExecutionMetadata, MetricsCollection
from src.metrics.models.repository import Repository
from src.metrics.output_generators import OutputManager


class TestOutputManager:
    """Test output manager functionality."""

    @pytest.fixture
    def output_manager(self) -> OutputManager:
        """Create output manager with temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield OutputManager(output_dir=temp_dir)

    @pytest.fixture
    def sample_repository(self) -> Repository:
        """Create sample repository data."""
        return Repository(
            url="https://github.com/test/repo.git",
            commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
            detected_language="python",
            local_path="/tmp/repo",
            timestamp=datetime.fromisoformat("2025-09-27T10:30:00"),
            size_mb=12.5
        )

    @pytest.fixture
    def sample_metrics(self) -> MetricsCollection:
        """Create sample metrics collection."""
        return MetricsCollection(
            repository_id="test-repo",
            execution_metadata=ExecutionMetadata(
                tools_used=["ruff", "pytest"],
                errors=[],
                warnings=[],
                duration_seconds=60.0,
                timestamp=datetime.fromisoformat("2025-09-27T10:32:05")
            )
        )

    def test_save_results_json_format(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """Test saving results in JSON format."""
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "json")

        assert len(saved_files) == 1
        saved_file = saved_files[0]

        # Check file was created
        assert Path(saved_file).exists()
        assert saved_file.endswith(".json")

        # Check file content
        with open(saved_file) as f:
            data = json.load(f)
            assert "repository" in data
            assert "metrics" in data

    def test_save_results_markdown_format(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """Test saving results in Markdown format."""
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "markdown")

        assert len(saved_files) == 1
        saved_file = saved_files[0]

        # Check file was created
        assert Path(saved_file).exists()
        assert saved_file.endswith(".md")

        # Check file content
        with open(saved_file) as f:
            content = f.read()
            assert "# Code Quality Report" in content

    def test_save_results_both_formats(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """Test saving results in both formats."""
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "both")

        assert len(saved_files) == 2

        # Check both file types were created
        extensions = [Path(f).suffix for f in saved_files]
        assert ".json" in extensions
        assert ".md" in extensions

    def test_save_results_invalid_format(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """Test error handling for invalid format."""
        with pytest.raises(ValueError, match="Unsupported output format"):
            output_manager.save_results(sample_repository, sample_metrics, "invalid")

    def test_output_filenames_contain_repo_info(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """Test that output filenames contain repository information."""
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "json")
        filename = Path(saved_files[0]).name

        # Should contain repository name or commit
        assert "test" in filename or "repo" in filename or "a1b2c3d4" in filename

    def test_output_directory_creation(self, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_dir = Path(temp_dir) / "output" / "subdir"
            output_manager = OutputManager(output_dir=str(nonexistent_dir))

            saved_files = output_manager.save_results(sample_repository, sample_metrics, "json")

            # Directory should be created
            assert nonexistent_dir.exists()
            assert Path(saved_files[0]).exists()

    @patch('src.metrics.output_generators.Path.mkdir')
    def test_output_directory_creation_error(self, mock_mkdir: MagicMock, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """Test handling of output directory creation errors."""
        mock_mkdir.side_effect = PermissionError("Permission denied")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_manager = OutputManager(output_dir=temp_dir)

            with pytest.raises(PermissionError):
                output_manager.save_results(sample_repository, sample_metrics, "json")

    def test_generate_filename_uniqueness(self, output_manager: OutputManager, sample_repository: Repository) -> None:
        """Test that generated filenames are unique."""
        filename1 = output_manager.generate_filename(sample_repository, "json")
        filename2 = output_manager.generate_filename(sample_repository, "json")

        # Filenames should be different (contain timestamp)
        assert filename1 != filename2

    def test_generate_filename_format(self, output_manager: OutputManager, sample_repository: Repository) -> None:
        """Test generated filename format."""
        filename = output_manager.generate_filename(sample_repository, "json")

        # Should contain expected elements
        assert "test-repo" in filename
        assert ".json" in filename
        assert len(filename) > 10  # Should have reasonable length
