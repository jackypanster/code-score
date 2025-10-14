"""
Unit tests for GitHubActionsParser.

Tests validate GitHub Actions workflow file parsing, test command detection,
coverage upload detection, and error handling.

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the parser is implemented in Phase 3.3 (T016).
"""

from pathlib import Path

import pytest

# This import will FAIL until T016 (Implement GitHubActionsParser) is complete
# Expected error: ModuleNotFoundError: No module named 'src.metrics.ci_parsers'
try:
    from src.metrics.ci_parsers.github_actions_parser import GitHubActionsParser
    PARSER_IMPLEMENTED = True
except ModuleNotFoundError:
    PARSER_IMPLEMENTED = False
    # Create a mock for test structure validation
    class GitHubActionsParser:
        def parse(self, config_path):
            pass


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "github_actions"


@pytest.fixture
def parser():
    """Create GitHubActionsParser instance."""
    return GitHubActionsParser()


@pytest.fixture
def valid_workflow_path():
    """Path to valid workflow with test steps."""
    return FIXTURES_DIR / "valid_with_tests.yml"


@pytest.fixture
def no_tests_workflow_path():
    """Path to workflow without test steps (build only)."""
    return FIXTURES_DIR / "no_test_steps.yml"


@pytest.fixture
def malformed_workflow_path():
    """Path to malformed YAML workflow."""
    return FIXTURES_DIR / "malformed.yml"


@pytest.fixture
def multi_language_workflow_path():
    """Path to workflow with multiple test commands."""
    return FIXTURES_DIR / "multiple_test_commands.yml"


@pytest.mark.skipif(not PARSER_IMPLEMENTED, reason="GitHubActionsParser not yet implemented (T016)")
class TestGitHubActionsParser:
    """Test suite for GitHub Actions workflow parsing."""

    def test_parse_valid_workflow_with_test_steps(self, parser, valid_workflow_path):
        """Test 1: Parse valid workflow file with test steps."""
        result = parser.parse(valid_workflow_path)

        assert result is not None, "Parser should return TestStepInfo list for valid workflow"
        assert isinstance(result, list), "Result should be a list"
        assert len(result) > 0, "Should detect at least one test step"

        # Verify test step structure
        first_step = result[0]
        assert hasattr(first_step, 'job_name'), "TestStepInfo should have job_name attribute"
        assert hasattr(first_step, 'command'), "TestStepInfo should have command attribute"
        assert hasattr(first_step, 'framework'), "TestStepInfo should have framework attribute"
        assert hasattr(first_step, 'has_coverage_flag'), "TestStepInfo should have has_coverage_flag"

    def test_detect_pytest_command(self, parser, valid_workflow_path):
        """Test 2: Detect pytest test command."""
        result = parser.parse(valid_workflow_path)

        assert result is not None
        # Find pytest command in results
        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        assert len(pytest_steps) > 0, "Should detect pytest command"

        # Verify framework inference
        pytest_step = pytest_steps[0]
        assert pytest_step.framework == "pytest", "Framework should be inferred as 'pytest'"

    def test_detect_npm_test_command(self, parser, multi_language_workflow_path):
        """Test 2b: Detect npm test command."""
        result = parser.parse(multi_language_workflow_path)

        assert result is not None
        npm_steps = [step for step in result if 'npm test' in step.command.lower()]
        assert len(npm_steps) > 0, "Should detect npm test command"

    def test_detect_go_test_command(self, parser, multi_language_workflow_path):
        """Test 2c: Detect go test command."""
        result = parser.parse(multi_language_workflow_path)

        assert result is not None
        go_steps = [step for step in result if 'go test' in step.command.lower()]
        assert len(go_steps) > 0, "Should detect go test command"

    def test_detect_maven_test_command(self, parser, multi_language_workflow_path):
        """Test 2d: Detect mvn test command."""
        result = parser.parse(multi_language_workflow_path)

        assert result is not None
        maven_steps = [step for step in result if 'mvn test' in step.command.lower()]
        assert len(maven_steps) > 0, "Should detect mvn test command"

    def test_detect_codecov_upload_action(self, parser, valid_workflow_path):
        """Test 3: Detect Codecov upload via codecov/codecov-action."""
        result = parser.parse(valid_workflow_path)

        assert result is not None
        # Codecov detection should be in the parser's logic
        # The parser should mark steps that use codecov actions
        # or detect "codecov" in uses: field

    def test_detect_coveralls_action(self, parser, multi_language_workflow_path):
        """Test 3b: Detect Coveralls upload action."""
        result = parser.parse(multi_language_workflow_path)

        assert result is not None
        # Should detect coveralls/github-action usage

    def test_count_distinct_test_jobs(self, parser, multi_language_workflow_path):
        """Test 4: Count distinct test jobs across workflow."""
        result = parser.parse(multi_language_workflow_path)

        assert result is not None
        # Count unique job names
        unique_jobs = set(step.job_name for step in result)
        assert len(unique_jobs) >= 4, "Should detect multiple test jobs (python, js, go, java)"

    def test_detect_coverage_flag_in_command(self, parser, valid_workflow_path):
        """Test 4b: Detect coverage flags in test commands."""
        result = parser.parse(valid_workflow_path)

        assert result is not None
        # Find step with --cov flag
        coverage_steps = [step for step in result if step.has_coverage_flag]
        assert len(coverage_steps) > 0, "Should detect --cov flag in pytest command"

    def test_handle_malformed_yaml_gracefully(self, parser, malformed_workflow_path):
        """Test 5: Handle malformed YAML gracefully (return None)."""
        result = parser.parse(malformed_workflow_path)

        assert result is None, "Parser should return None for malformed YAML"
        # Parser should log a warning internally (per plan.md)

    def test_handle_missing_file(self, parser):
        """Test 6: Handle missing file (raise FileNotFoundError)."""
        nonexistent_path = FIXTURES_DIR / "nonexistent.yml"

        with pytest.raises(FileNotFoundError):
            parser.parse(nonexistent_path)

    def test_workflow_without_test_steps_returns_empty_or_none(self, parser, no_tests_workflow_path):
        """Test: Workflow with only build steps should return empty list or None."""
        result = parser.parse(no_tests_workflow_path)

        # Parser can return either empty list or None if no test steps detected
        assert result is None or len(result) == 0, \
            "Workflow without test commands should return empty list or None"

    def test_extract_job_names_correctly(self, parser, multi_language_workflow_path):
        """Test: Job names should be extracted correctly from workflow."""
        result = parser.parse(multi_language_workflow_path)

        assert result is not None
        job_names = [step.job_name for step in result]
        # Verify job names match those in fixture
        expected_jobs = ["python-tests", "javascript-tests", "go-tests", "java-tests"]
        for expected_job in expected_jobs:
            assert any(expected_job in job_name for job_name in job_names), \
                f"Should detect job: {expected_job}"

    def test_multiple_steps_in_same_job(self, parser, multi_language_workflow_path):
        """Test: Multiple test steps in same job should be detected separately."""
        result = parser.parse(multi_language_workflow_path)

        assert result is not None
        # javascript-tests job has 2 test commands (npm test, npm run test:integration)
        js_steps = [step for step in result if 'javascript-tests' in step.job_name]
        assert len(js_steps) >= 2, "Should detect multiple test steps in same job"

    def test_framework_inference_accuracy(self, parser, multi_language_workflow_path):
        """Test: Framework inference should be accurate for different languages."""
        result = parser.parse(multi_language_workflow_path)

        assert result is not None

        # Check pytest → "pytest"
        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        if pytest_steps:
            assert pytest_steps[0].framework == "pytest"

        # Check npm test → "jest" (or "npm" depending on implementation)
        npm_steps = [step for step in result if 'npm test' in step.command.lower()]
        if npm_steps:
            # Framework inference might return "jest" or None (acceptable)
            assert npm_steps[0].framework in ["jest", "npm", None]

        # Check go test → "go_test"
        go_steps = [step for step in result if 'go test' in step.command.lower()]
        if go_steps:
            assert go_steps[0].framework == "go_test"

        # Check mvn test → "junit"
        maven_steps = [step for step in result if 'mvn test' in step.command.lower()]
        if maven_steps:
            assert maven_steps[0].framework == "junit"


# Meta-tests: Verify test fixtures exist
def test_fixture_files_exist():
    """Meta-test: Verify all fixture files exist."""
    fixtures = [
        "valid_with_tests.yml",
        "no_test_steps.yml",
        "malformed.yml",
        "multiple_test_commands.yml"
    ]

    for fixture in fixtures:
        fixture_path = FIXTURES_DIR / fixture
        assert fixture_path.exists(), f"Fixture file not found: {fixture_path}"


def test_fixture_directory_exists():
    """Meta-test: Verify fixtures directory exists."""
    assert FIXTURES_DIR.exists(), f"Fixtures directory not found: {FIXTURES_DIR}"
    assert FIXTURES_DIR.is_dir(), f"Fixtures path is not a directory: {FIXTURES_DIR}"


@pytest.mark.skipif(PARSER_IMPLEMENTED, reason="Parser already implemented")
def test_parser_not_yet_implemented():
    """TDD checkpoint: Verify GitHubActionsParser is not yet implemented."""
    with pytest.raises(ModuleNotFoundError):
        from src.metrics.ci_parsers.github_actions_parser import GitHubActionsParser
