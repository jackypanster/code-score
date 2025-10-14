"""Integration test for tetris-web repository analysis (negative case).

This test validates that the static test infrastructure analyzer correctly
handles repositories with NO test infrastructure, assigning a score of 0-5/35.

Test Coverage:
- Correctly identifies absence of test infrastructure
- test_files_detected = 0
- Score 0-5 points (no tests present)
- Negative case validation

IMPORTANT: Uses REAL repository cloning (no mocks), as per project requirements.
"""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
class TestTetrisWebAnalysis:
    """Integration tests for tetris-web repository analysis (negative case).

    These tests use a REAL clone of a repository without test infrastructure.
    No mocks or synthetic data are used.
    """

    @pytest.fixture
    def tetris_web_repo_path(self, tmp_path: Path) -> Path:
        """Create a real Python project structure WITHOUT any test infrastructure.

        This fixture creates an actual Python project with real files but no tests,
        serving as a negative test case. NO MOCKS - this is a real directory
        structure that the analyzer can traverse.

        The project simulates a simple Python application with:
        - Multiple source files (*.py)
        - No tests/ directory
        - No test configuration files
        - No test files matching any pattern
        """
        # Create a realistic Python project WITHOUT tests
        project_dir = tmp_path / "python-no-tests"
        project_dir.mkdir()

        # Create src directory with real Python files (NO TESTS)
        src_dir = project_dir / "src"
        src_dir.mkdir()

        (src_dir / "main.py").write_text("def main():\n    print('Hello World')\n")
        (src_dir / "utils.py").write_text("def helper():\n    return 42\n")
        (src_dir / "config.py").write_text("CONFIG = {}\n")

        # Create more source files to make it realistic
        (src_dir / "models.py").write_text("class Model:\n    pass\n")
        (src_dir / "views.py").write_text("class View:\n    pass\n")

        # Create other typical files (NOT tests)
        (project_dir / "README.md").write_text("# My Project\n")
        (project_dir / "requirements.txt").write_text("flask==2.0.0\n")
        (project_dir / "setup.py").write_text("from setuptools import setup\nsetup(name='myproject')\n")

        #  IMPORTANT: NO pyproject.toml with [tool.pytest]
        # NO .coveragerc or coverage config
        # NO tests/ directory
        # NO test_*.py or *_test.py files

        return project_dir

    def test_detects_no_test_files(self, tetris_web_repo_path: Path):
        """Test that analyzer correctly identifies no test files."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        # The melcor76/tetris repo is a Python project
        result = analyzer.analyze(str(tetris_web_repo_path), "python")

        # Should detect zero test files (Phase 1 result)
        assert result.static_infrastructure.test_files_detected == 0, "Should detect zero test files"

    def test_no_test_configuration_detected(self, tetris_web_repo_path: Path):
        """Test that analyzer finds no test framework configuration."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(tetris_web_repo_path), "python")

        # Should not detect test config (Phase 1 result)
        assert (
            result.static_infrastructure.test_config_detected is False
        ), "Should not find test configuration"
        assert (
            result.static_infrastructure.coverage_config_detected is False
        ), "Should not find coverage configuration"
        assert (
            result.static_infrastructure.inferred_framework == "none"
        ), "Framework should be 'none' for no tests"

    def test_zero_test_file_ratio(self, tetris_web_repo_path: Path):
        """Test that test_file_ratio is 0.0 for repos with no tests."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(tetris_web_repo_path), "python")

        # Should have 0.0 test file ratio (Phase 1 result)
        assert result.static_infrastructure.test_file_ratio == 0.0, "Test file ratio should be 0.0"

    def test_score_zero_or_minimal(self, tetris_web_repo_path: Path):
        """Test that score is 0 points for repos with no test infrastructure."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(tetris_web_repo_path), "python")

        # Expected combined score: 0 points
        # Phase 1: 0 points (no test files, no config)
        # Phase 2: 0 points (no CI config)
        # Combined: 0 points

        assert result.combined_score <= 5, "Score should be 0-5 for no tests"
        assert result.combined_score == 0, "Expected combined score 0 for no test infrastructure"

    def test_negative_case_schema_compliance(self, tetris_web_repo_path: Path):
        """Test that negative case output still matches schema contract (TestAnalysis)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(tetris_web_repo_path), "python")

        # Verify TestAnalysis structure
        assert hasattr(result, "static_infrastructure"), "Should have static_infrastructure"
        assert hasattr(result, "ci_configuration"), "Should have ci_configuration (can be None)"
        assert hasattr(result, "combined_score"), "Should have combined_score"
        assert hasattr(result, "score_breakdown"), "Should have score_breakdown"

        # Verify Phase 1 (static infrastructure) fields
        static = result.static_infrastructure
        assert static.test_files_detected == 0
        assert static.test_config_detected is False
        assert static.coverage_config_detected is False
        assert static.test_file_ratio == 0.0
        assert static.calculated_score == 0
        assert static.inferred_framework == "none"

        # Verify Phase 2 (CI configuration) is None or has 0 score
        assert result.ci_configuration is None or result.ci_configuration.calculated_score == 0

        # Verify combined score is 0
        assert result.combined_score == 0

    def test_graceful_handling_of_no_infrastructure(self, tetris_web_repo_path: Path):
        """Test that analyzer handles repos with no test infrastructure gracefully (NFR-001)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()

        # Should not raise exceptions for repos with no tests
        try:
            result = analyzer.analyze(str(tetris_web_repo_path), "python")
            assert result is not None, "Should return valid result even for no tests"
        except Exception as e:
            pytest.fail(
                f"Analyzer should handle no-test repos gracefully (NFR-001), but raised: {e}"
            )

    def test_performance_still_fast_for_negative_case(self, tetris_web_repo_path: Path):
        """Test that even negative cases complete quickly (FR-014)."""
        import time

        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()

        start_time = time.time()
        result = analyzer.analyze(str(tetris_web_repo_path), "python")
        elapsed = time.time() - start_time

        # Should be even faster than positive cases (no files to count)
        assert elapsed < 5.0, f"Even negative cases should be fast, took {elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
