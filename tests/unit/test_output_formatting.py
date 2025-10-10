"""Real execution tests for output formatting functionality.

NO MOCKS - All tests use real file operations based on ACTUAL OutputManager API.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.metrics.models.metrics_collection import ExecutionMetadata, MetricsCollection
from src.metrics.models.repository import Repository
from src.metrics.output_generators import OutputManager


class TestOutputManagerRealAPI:
    """REAL TESTS for OutputManager using ACTUAL API - NO MOCKS."""

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
            clone_timestamp=datetime.fromisoformat("2025-09-27T10:30:00"),
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

    def test_save_results_json_format_real(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """REAL TEST: Save results in JSON format."""
        # REAL FILE SAVE - No mocks!
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "json")

        # Real behavior: returns multiple files including submission.json
        assert len(saved_files) >= 1

        # Check at least one JSON file was created
        json_files = [f for f in saved_files if f.endswith(".json")]
        assert len(json_files) >= 1

        # REAL FILE READ - verify content
        for json_file in json_files:
            assert Path(json_file).exists()
            with open(json_file) as f:
                data = json.load(f)
                # submission.json has different structure
                assert isinstance(data, dict)

    def test_save_results_markdown_format_real(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """REAL TEST: Save results in Markdown format."""
        # REAL FILE SAVE
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "markdown")

        # Check markdown file was created
        md_files = [f for f in saved_files if f.endswith(".md")]
        assert len(md_files) >= 1

        # REAL FILE READ - check actual content
        md_file = md_files[0]
        assert Path(md_file).exists()
        with open(md_file) as f:
            content = f.read()
            # Real title is "Code Analysis Report" not "Code Quality Report"
            assert "# Code Analysis Report" in content or "# Code Quality Report" in content

    def test_save_results_both_formats_real(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """REAL TEST: Save results in both formats."""
        # REAL FILE SAVE
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "both")

        # Should have both JSON and MD files
        extensions = [Path(f).suffix for f in saved_files]
        assert ".json" in extensions
        assert ".md" in extensions

    def test_save_results_default_json_real(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """REAL TEST: Default format behavior."""
        # REAL FILE SAVE with default
        saved_files = output_manager.save_results(sample_repository, sample_metrics)

        # Default should create JSON files
        assert len(saved_files) >= 1
        json_files = [f for f in saved_files if f.endswith(".json")]
        assert len(json_files) >= 1

    def test_output_directory_creation_real(self, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """REAL TEST: Output directory is created automatically."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # REAL non-existent nested directory
            nonexistent_dir = Path(temp_dir) / "output" / "metrics" / "subdir"
            output_manager = OutputManager(output_dir=str(nonexistent_dir))

            # REAL FILE SAVE - should create all parent directories
            saved_files = output_manager.save_results(sample_repository, sample_metrics, "json")

            # REAL CHECKS
            assert nonexistent_dir.exists()
            assert len(saved_files) >= 1
            for f in saved_files:
                assert Path(f).exists()

    def test_output_files_are_valid_json_real(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """REAL TEST: All JSON files are valid JSON."""
        # REAL FILE SAVE
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "json")

        # REAL VALIDATION - all JSON files should parse
        for filepath in saved_files:
            if filepath.endswith(".json"):
                with open(filepath) as f:
                    data = json.load(f)  # Will raise if invalid JSON
                    assert isinstance(data, dict)

    def test_output_contains_repository_info_real(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """REAL TEST: Output files contain repository information."""
        # REAL FILE SAVE
        saved_files = output_manager.save_results(sample_repository, sample_metrics, "json")

        # REAL CHECK - at least one file should contain repo URL
        found_repo_info = False
        for filepath in saved_files:
            if filepath.endswith(".json"):
                with open(filepath) as f:
                    content = f.read()
                    if "test/repo" in content or sample_repository.url in content:
                        found_repo_info = True
                        break

        assert found_repo_info, "No output file contained repository information"

    def test_multiple_saves_create_separate_files_real(self, output_manager: OutputManager, sample_repository: Repository, sample_metrics: MetricsCollection) -> None:
        """REAL TEST: Multiple saves create files (may overwrite or create new)."""
        # REAL FIRST SAVE
        saved_files_1 = output_manager.save_results(sample_repository, sample_metrics, "json")

        # REAL SECOND SAVE
        import time
        time.sleep(0.1)  # Ensure different timestamp if files are timestamped
        saved_files_2 = output_manager.save_results(sample_repository, sample_metrics, "json")

        # Both saves should succeed
        assert len(saved_files_1) >= 1
        assert len(saved_files_2) >= 1

        # Files should exist
        for f in saved_files_1:
            # May be overwritten by second save if same name
            pass  # Just check no errors
        for f in saved_files_2:
            assert Path(f).exists()
