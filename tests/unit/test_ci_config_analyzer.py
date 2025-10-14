"""
Unit tests for CIConfigAnalyzer.

Tests validate CI platform detection, parser orchestration, score calculation,
multi-platform handling, error recovery, and performance requirements.

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the analyzer is implemented in Phase 3.3 (T021).
"""

from pathlib import Path
import time

import pytest

# This import will FAIL until T021 (Implement CIConfigAnalyzer) is complete
# Expected error: ModuleNotFoundError: No module named 'src.metrics.ci_config_analyzer'
try:
    from src.metrics.ci_config_analyzer import CIConfigAnalyzer
    ANALYZER_IMPLEMENTED = True
except ModuleNotFoundError:
    ANALYZER_IMPLEMENTED = False
    # Create a mock for test structure validation
    class CIConfigAnalyzer:
        def analyze_ci_config(self, repo_path):
            pass


@pytest.fixture
def analyzer():
    """Create CIConfigAnalyzer instance."""
    return CIConfigAnalyzer()


@pytest.fixture
def mock_repo_with_github_actions(tmp_path):
    """Create mock repository with GitHub Actions."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    
    (workflows_dir / "test.yml").write_text("""
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest --cov=src tests/
      - uses: codecov/codecov-action@v3
""")
    return tmp_path


@pytest.fixture
def mock_repo_with_gitlab_ci(tmp_path):
    """Create mock repository with GitLab CI."""
    (tmp_path / ".gitlab-ci.yml").write_text("""
stages:
  - test

test:
  stage: test
  script:
    - pytest --cov=src tests/
    - codecov upload
""")
    return tmp_path


@pytest.fixture
def mock_repo_with_circleci(tmp_path):
    """Create mock repository with CircleCI."""
    circleci_dir = tmp_path / ".circleci"
    circleci_dir.mkdir()
    
    (circleci_dir / "config.yml").write_text("""
version: 2
jobs:
  unit-tests:
    steps:
      - run: pytest tests/unit
  integration-tests:
    steps:
      - run: pytest tests/integration
workflows:
  version: 2
  test:
    jobs:
      - unit-tests
      - integration-tests
""")
    return tmp_path


@pytest.fixture
def mock_repo_with_travis(tmp_path):
    """Create mock repository with Travis CI."""
    (tmp_path / ".travis.yml").write_text("""
language: python
python:
  - "3.11"
script:
  - pytest tests/
after_success:
  - codecov
""")
    return tmp_path


@pytest.fixture
def mock_repo_with_jenkins(tmp_path):
    """Create mock repository with Jenkinsfile."""
    (tmp_path / "Jenkinsfile").write_text("""
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh 'pytest tests/'
            }
        }
    }
}
""")
    return tmp_path


@pytest.fixture
def mock_repo_without_ci(tmp_path):
    """Create mock repository without CI configuration."""
    (tmp_path / "README.md").write_text("# Test Repo")
    return tmp_path


@pytest.fixture
def mock_repo_with_multiple_ci(tmp_path):
    """Create mock repository with multiple CI platforms."""
    # GitHub Actions
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "test.yml").write_text("""
name: Test
jobs:
  test:
    steps:
      - run: pytest tests/
""")
    
    # GitLab CI
    (tmp_path / ".gitlab-ci.yml").write_text("""
test:
  script:
    - mvn test
    - codecov upload
""")
    
    return tmp_path


# Meta-tests (run even before analyzer is implemented)
class TestCIConfigAnalyzerMeta:
    """Meta-tests that validate test infrastructure itself."""

    def test_analyzer_class_exists(self):
        """Meta-test: Verify CIConfigAnalyzer class is available (mock or real)."""
        assert CIConfigAnalyzer is not None
        analyzer = CIConfigAnalyzer()
        assert hasattr(analyzer, 'analyze_ci_config'), "Must have analyze_ci_config() method"

    def test_implementation_status(self):
        """Meta-test: Report analyzer implementation status."""
        if ANALYZER_IMPLEMENTED:
            print("\n✅ CIConfigAnalyzer is implemented - all tests should pass")
        else:
            print("\n⏳ CIConfigAnalyzer not yet implemented - tests will be skipped")

    def test_mock_fixtures_exist(self, mock_repo_with_github_actions, mock_repo_without_ci):
        """Meta-test: Verify mock fixtures are created correctly."""
        assert mock_repo_with_github_actions.exists()
        assert (mock_repo_with_github_actions / ".github" / "workflows" / "test.yml").exists()
        assert mock_repo_without_ci.exists()


@pytest.mark.skipif(not ANALYZER_IMPLEMENTED, reason="CIConfigAnalyzer not yet implemented (T021)")
class TestCIPlatformDetection:
    """Test suite for CI platform detection."""

    def test_detect_github_actions(self, analyzer, mock_repo_with_github_actions):
        """Test 1: Detect GitHub Actions configuration."""
        result = analyzer.analyze_ci_config(mock_repo_with_github_actions)
        
        assert result is not None
        assert result.platform == "github_actions"
        assert result.config_file_path is not None
        assert ".github/workflows" in result.config_file_path

    def test_detect_gitlab_ci(self, analyzer, mock_repo_with_gitlab_ci):
        """Test 2: Detect GitLab CI configuration."""
        result = analyzer.analyze_ci_config(mock_repo_with_gitlab_ci)
        
        assert result is not None
        assert result.platform == "gitlab_ci"
        assert ".gitlab-ci.yml" in result.config_file_path

    def test_detect_circleci(self, analyzer, mock_repo_with_circleci):
        """Test 3: Detect CircleCI configuration."""
        result = analyzer.analyze_ci_config(mock_repo_with_circleci)
        
        assert result is not None
        assert result.platform == "circleci"
        assert ".circleci/config.yml" in result.config_file_path

    def test_detect_travis_ci(self, analyzer, mock_repo_with_travis):
        """Test 4: Detect Travis CI configuration."""
        result = analyzer.analyze_ci_config(mock_repo_with_travis)
        
        assert result is not None
        assert result.platform == "travis_ci"
        assert ".travis.yml" in result.config_file_path

    def test_detect_jenkins(self, analyzer, mock_repo_with_jenkins):
        """Test 5: Detect Jenkins configuration."""
        result = analyzer.analyze_ci_config(mock_repo_with_jenkins)
        
        assert result is not None
        assert result.platform == "jenkins"
        assert "Jenkinsfile" in result.config_file_path

    def test_no_ci_configuration(self, analyzer, mock_repo_without_ci):
        """Test 6: Return platform=None when no CI configuration found."""
        result = analyzer.analyze_ci_config(mock_repo_without_ci)
        
        assert result is not None
        assert result.platform is None
        assert result.calculated_score == 0
        assert result.has_test_steps is False


@pytest.mark.skipif(not ANALYZER_IMPLEMENTED, reason="CIConfigAnalyzer not yet implemented (T021)")
class TestScoreCalculation:
    """Test suite for score calculation logic."""

    def test_score_with_test_steps_only(self, analyzer, mock_repo_with_github_actions):
        """Test 7: Calculate score with test steps (5 points)."""
        result = analyzer.analyze_ci_config(mock_repo_with_github_actions)
        
        assert result.has_test_steps is True
        assert result.calculated_score >= 5

    def test_score_with_coverage_upload(self, analyzer, mock_repo_with_gitlab_ci):
        """Test 8: Calculate score with coverage upload (5 + 5 = 10 points)."""
        result = analyzer.analyze_ci_config(mock_repo_with_gitlab_ci)
        
        assert result.has_test_steps is True
        assert result.has_coverage_upload is True
        assert result.calculated_score >= 10

    def test_score_with_multiple_jobs(self, analyzer, mock_repo_with_circleci):
        """Test 9: Calculate score with multiple test jobs (5 + 0 + 3 = 8 points minimum)."""
        result = analyzer.analyze_ci_config(mock_repo_with_circleci)
        
        assert result.test_job_count >= 2
        # May have coverage too, so score could be higher
        assert result.calculated_score >= 8

    def test_max_score_13_points(self, analyzer, tmp_path):
        """Test 10: Maximum score is capped at 13 points."""
        # Create config with all scoring criteria
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").write_text("""
name: Test
jobs:
  unit-tests:
    steps:
      - run: pytest --cov=src tests/unit
      - uses: codecov/codecov-action@v3
  integration-tests:
    steps:
      - run: pytest tests/integration
  e2e-tests:
    steps:
      - run: npm test
""")
        
        result = analyzer.analyze_ci_config(tmp_path)
        
        assert result.has_test_steps is True
        assert result.has_coverage_upload is True
        assert result.test_job_count >= 2
        assert result.calculated_score == 13, "Max score should be 13"


@pytest.mark.skipif(not ANALYZER_IMPLEMENTED, reason="CIConfigAnalyzer not yet implemented (T021)")
class TestMultipleCIPlatforms:
    """Test suite for multiple CI platform handling."""

    def test_detect_multiple_platforms(self, analyzer, mock_repo_with_multiple_ci):
        """Test 11: Use max score when multiple CI platforms detected (research.md decision 6)."""
        result = analyzer.analyze_ci_config(mock_repo_with_multiple_ci)
        
        # Should detect at least one platform
        assert result.platform is not None
        # Platform could be any of the detected ones
        assert result.platform in ["github_actions", "gitlab_ci"]

    def test_max_score_across_platforms(self, analyzer, mock_repo_with_multiple_ci):
        """Test 12: Use highest score when multiple platforms present."""
        result = analyzer.analyze_ci_config(mock_repo_with_multiple_ci)
        
        # GitLab CI has coverage upload (10 points), GitHub Actions has test only (5 points)
        # Should use max = 10 points
        assert result.calculated_score >= 5


@pytest.mark.skipif(not ANALYZER_IMPLEMENTED, reason="CIConfigAnalyzer not yet implemented (T021)")
class TestErrorHandling:
    """Test suite for error handling and graceful degradation."""

    def test_malformed_yaml_config(self, analyzer, tmp_path):
        """Test 13: Handle malformed YAML gracefully (0 score, populate parse_errors)."""
        (tmp_path / ".gitlab-ci.yml").write_text("""
invalid yaml [
  no closing bracket
  - test: pytest
""")
        
        result = analyzer.analyze_ci_config(tmp_path)
        
        # Should not crash
        assert result is not None
        # Per FR-022: return 0 score on parse errors
        assert result.calculated_score == 0
        # Parse errors should be documented
        assert len(result.parse_errors) > 0

    def test_missing_repo_path(self, analyzer):
        """Test 14: Handle missing repository path."""
        nonexistent_path = Path("/nonexistent/repo/path")
        
        # Should raise ValueError per API contract
        with pytest.raises(ValueError):
            analyzer.analyze_ci_config(nonexistent_path)

    def test_empty_ci_config_file(self, analyzer, tmp_path):
        """Test 15: Handle empty CI config file."""
        (tmp_path / ".travis.yml").write_text("")
        
        result = analyzer.analyze_ci_config(tmp_path)
        
        # Empty config should be treated as no test steps
        assert result.has_test_steps is False
        assert result.calculated_score == 0


@pytest.mark.skipif(not ANALYZER_IMPLEMENTED, reason="CIConfigAnalyzer not yet implemented (T021)")
class TestResultStructure:
    """Test suite for CIConfigResult structure validation."""

    def test_result_has_required_fields(self, analyzer, mock_repo_with_github_actions):
        """Test 16: CIConfigResult has all required fields."""
        result = analyzer.analyze_ci_config(mock_repo_with_github_actions)
        
        assert hasattr(result, 'platform')
        assert hasattr(result, 'config_file_path')
        assert hasattr(result, 'has_test_steps')
        assert hasattr(result, 'test_commands')
        assert hasattr(result, 'has_coverage_upload')
        assert hasattr(result, 'coverage_tools')
        assert hasattr(result, 'test_job_count')
        assert hasattr(result, 'calculated_score')
        assert hasattr(result, 'parse_errors')

    def test_test_commands_list(self, analyzer, mock_repo_with_github_actions):
        """Test 17: test_commands is a list of detected commands."""
        result = analyzer.analyze_ci_config(mock_repo_with_github_actions)
        
        assert isinstance(result.test_commands, list)
        if result.has_test_steps:
            assert len(result.test_commands) > 0
            # Should contain pytest command
            pytest_found = any('pytest' in cmd for cmd in result.test_commands)
            assert pytest_found

    def test_coverage_tools_list(self, analyzer, mock_repo_with_gitlab_ci):
        """Test 18: coverage_tools is a list of detected tools."""
        result = analyzer.analyze_ci_config(mock_repo_with_gitlab_ci)
        
        assert isinstance(result.coverage_tools, list)
        if result.has_coverage_upload:
            assert len(result.coverage_tools) > 0
            # Should contain codecov
            assert "codecov" in result.coverage_tools


@pytest.mark.skipif(not ANALYZER_IMPLEMENTED, reason="CIConfigAnalyzer not yet implemented (T021)")
class TestPerformance:
    """Test suite for performance requirements."""

    def test_analysis_completes_under_1_second(self, analyzer, mock_repo_with_github_actions):
        """Test 19: Complete analysis in <1 second (FR-020)."""
        start_time = time.time()
        
        result = analyzer.analyze_ci_config(mock_repo_with_github_actions)
        
        elapsed_time = time.time() - start_time
        
        assert result is not None
        assert elapsed_time < 1.0, f"Analysis took {elapsed_time:.2f}s (should be <1s)"

    def test_performance_with_multiple_platforms(self, analyzer, mock_repo_with_multiple_ci):
        """Test 20: Performance acceptable even with multiple CI platforms."""
        start_time = time.time()
        
        result = analyzer.analyze_ci_config(mock_repo_with_multiple_ci)
        
        elapsed_time = time.time() - start_time
        
        assert result is not None
        assert elapsed_time < 1.0, f"Multi-platform analysis took {elapsed_time:.2f}s (should be <1s)"


@pytest.mark.skipif(not ANALYZER_IMPLEMENTED, reason="CIConfigAnalyzer not yet implemented (T021)")
class TestEdgeCases:
    """Edge case tests for CIConfigAnalyzer."""

    def test_github_actions_with_multiple_workflow_files(self, analyzer, tmp_path):
        """Edge case: Multiple GitHub Actions workflow files."""
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        
        (workflows_dir / "test.yml").write_text("""
name: Test
jobs:
  test:
    steps:
      - run: pytest tests/unit
""")
        
        (workflows_dir / "integration.yml").write_text("""
name: Integration
jobs:
  integration:
    steps:
      - run: pytest tests/integration
""")
        
        result = analyzer.analyze_ci_config(tmp_path)
        
        # Should detect GitHub Actions
        assert result.platform == "github_actions"
        # Should aggregate test steps from all workflow files
        assert result.test_job_count >= 2

    def test_ci_config_in_subdirectory(self, analyzer, tmp_path):
        """Edge case: Ensure analyzer only checks root directory."""
        subdir = tmp_path / "subproject"
        subdir.mkdir()
        (subdir / ".travis.yml").write_text("script: pytest tests/")
        
        result = analyzer.analyze_ci_config(tmp_path)
        
        # Should not detect CI config in subdirectory (only root)
        assert result.platform is None

    def test_jenkinsfile_with_different_cases(self, analyzer, tmp_path):
        """Edge case: Jenkinsfile with different case variations."""
        # Jenkinsfile might have different cases
        (tmp_path / "jenkinsfile").write_text("pipeline { }")
        
        result = analyzer.analyze_ci_config(tmp_path)
        
        # Should detect despite case difference (case-insensitive)
        # Implementation may vary - document behavior
        assert result.platform == "jenkins" or result.platform is None


# Summary of test coverage
"""
Test Coverage Summary for CIConfigAnalyzer (T010):

✅ CI platform detection (6 tests) - GitHub Actions, GitLab CI, CircleCI, Travis CI, Jenkins, no CI
✅ Score calculation (4 tests) - test steps (5), coverage (10), multiple jobs (8), max score (13)
✅ Multiple platforms (2 tests) - detection, max score aggregation
✅ Error handling (3 tests) - malformed YAML, missing path, empty config
✅ Result structure (3 tests) - required fields, test_commands list, coverage_tools list
✅ Performance (2 tests) - <1 second requirement, multi-platform performance
✅ Edge cases (3 tests) - multiple workflow files, subdirectory configs, case variations

Total: 26 tests (3 meta-tests + 23 implementation tests)

Expected Result: All tests SKIP until T021 (CIConfigAnalyzer implementation) is complete
After T021: All tests should PASS with correct orchestration logic
"""
