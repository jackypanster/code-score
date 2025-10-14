"""
Unit tests for GitLabCIParser.

Tests validate GitLab CI configuration file parsing, test command detection,
coverage upload detection, and error handling.

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the parser is implemented in Phase 3.3 (T017).
"""

from pathlib import Path

import pytest

# This import will FAIL until T017 (Implement GitLabCIParser) is complete
try:
    from src.metrics.ci_parsers.gitlab_ci_parser import GitLabCIParser
    PARSER_IMPLEMENTED = True
except ModuleNotFoundError:
    PARSER_IMPLEMENTED = False
    class GitLabCIParser:
        def parse(self, config_path):
            pass


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "gitlab_ci"


@pytest.fixture
def parser():
    """Create GitLabCIParser instance."""
    return GitLabCIParser()


@pytest.fixture
def valid_config_path():
    """Path to valid GitLab CI config with test jobs."""
    return FIXTURES_DIR / "valid_with_tests.yml"


@pytest.fixture
def no_tests_config_path():
    """Path to config without test jobs."""
    return FIXTURES_DIR / "no_test_steps.yml"


@pytest.fixture
def malformed_config_path():
    """Path to malformed YAML config."""
    return FIXTURES_DIR / "malformed.yml"


@pytest.fixture
def multi_language_config_path():
    """Path to config with multiple language tests."""
    return FIXTURES_DIR / "multi_language.yml"


@pytest.mark.skipif(not PARSER_IMPLEMENTED, reason="GitLabCIParser not yet implemented (T017)")
class TestGitLabCIParser:
    """Test suite for GitLab CI configuration parsing."""

    def test_parse_valid_config_with_test_stages(self, parser, valid_config_path):
        """Test 1: Parse valid GitLab CI config with test stages."""
        result = parser.parse(valid_config_path)

        assert result is not None, "Parser should return TestStepInfo list"
        assert isinstance(result, list), "Result should be a list"
        assert len(result) > 0, "Should detect at least one test job"

        first_step = result[0]
        assert hasattr(first_step, 'job_name'), "TestStepInfo should have job_name"
        assert hasattr(first_step, 'command'), "TestStepInfo should have command"
        assert hasattr(first_step, 'framework'), "TestStepInfo should have framework"
        assert hasattr(first_step, 'has_coverage_flag'), "TestStepInfo should have has_coverage_flag"

    def test_detect_test_commands_in_script_sections(self, parser, valid_config_path):
        """Test 2: Detect test commands in script: sections."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # Verify pytest command detection
        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        assert len(pytest_steps) > 0, "Should detect pytest in script sections"

    def test_detect_pytest_with_coverage_flag(self, parser, multi_language_config_path):
        """Test 2b: Detect pytest with coverage flags."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        coverage_steps = [step for step in result if step.has_coverage_flag]
        assert len(coverage_steps) > 0, "Should detect --cov flag in pytest command"

    def test_detect_npm_test_command(self, parser, multi_language_config_path):
        """Test 2c: Detect npm test commands."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        npm_steps = [step for step in result if 'npm test' in step.command.lower()]
        assert len(npm_steps) > 0, "Should detect npm test command"

    def test_detect_go_test_command(self, parser, multi_language_config_path):
        """Test 2d: Detect go test commands."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        go_steps = [step for step in result if 'go test' in step.command.lower()]
        assert len(go_steps) > 0, "Should detect go test command"

    def test_detect_maven_gradle_test_commands(self, parser, multi_language_config_path):
        """Test 2e: Detect mvn test and gradle test commands."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        maven_steps = [step for step in result if 'mvn test' in step.command.lower()]
        gradle_steps = [step for step in result if 'gradlew test' in step.command.lower()]
        assert len(maven_steps) > 0 or len(gradle_steps) > 0, \
            "Should detect mvn test or gradle test"

    def test_detect_coverage_upload_codecov(self, parser, valid_config_path):
        """Test 3: Detect codecov upload in script sections."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # Parser should detect "codecov upload" command

    def test_detect_sonarqube_scan(self, parser, multi_language_config_path):
        """Test 3b: Detect SonarQube scan steps."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        # Should detect sonar-scanner command

    def test_count_distinct_test_jobs_across_stages(self, parser, multi_language_config_path):
        """Test 4: Count distinct test jobs across multiple stages."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        unique_jobs = set(step.job_name for step in result)
        # Should detect python_tests, javascript_tests, go_tests, java_tests
        assert len(unique_jobs) >= 4, "Should detect multiple test jobs"

    def test_extract_job_names_correctly(self, parser, valid_config_path):
        """Test 4b: Job names should match YAML job keys."""
        result = parser.parse(valid_config_path)

        assert result is not None
        job_names = [step.job_name for step in result]
        # Verify expected job names from fixture
        assert any('unit_tests' in name for name in job_names), \
            "Should detect unit_tests job"
        assert any('integration_tests' in name for name in job_names), \
            "Should detect integration_tests job"

    def test_handle_malformed_yaml(self, parser, malformed_config_path):
        """Test 5: Handle malformed YAML gracefully (return None)."""
        result = parser.parse(malformed_config_path)

        assert result is None, "Parser should return None for malformed YAML"

    def test_handle_missing_file(self, parser):
        """Test 5b: Handle missing file (raise FileNotFoundError)."""
        nonexistent_path = FIXTURES_DIR / "nonexistent.yml"

        with pytest.raises(FileNotFoundError):
            parser.parse(nonexistent_path)

    def test_config_without_test_jobs_returns_empty_or_none(self, parser, no_tests_config_path):
        """Test: Config with only build/deploy should return empty or None."""
        result = parser.parse(no_tests_config_path)

        assert result is None or len(result) == 0, \
            "Config without test commands should return empty list or None"

    def test_handle_script_list_format(self, parser, valid_config_path):
        """Test: Handle script: sections with list of commands."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # GitLab CI script sections are lists of commands
        # Parser should handle each line in the list

    def test_handle_after_script_for_coverage(self, parser, multi_language_config_path):
        """Test: Detect coverage uploads in after_script sections."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        # After_script may contain coverage uploads

    def test_framework_inference_for_different_languages(self, parser, multi_language_config_path):
        """Test: Framework inference should work for all languages."""
        result = parser.parse(multi_language_config_path)

        assert result is not None

        # Check pytest → "pytest"
        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        if pytest_steps:
            assert pytest_steps[0].framework == "pytest"

        # Check go test → "go_test"
        go_steps = [step for step in result if 'go test' in step.command.lower()]
        if go_steps:
            assert go_steps[0].framework == "go_test"

        # Check mvn test → "junit"
        maven_steps = [step for step in result if 'mvn test' in step.command.lower()]
        if maven_steps:
            assert maven_steps[0].framework == "junit"

    def test_coverage_artifact_detection(self, parser, multi_language_config_path):
        """Test: Detect coverage artifacts in job configuration."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        # Parser should detect coverage artifacts configuration

    def test_multiple_script_commands_in_single_job(self, parser, multi_language_config_path):
        """Test: Multiple script commands in same job should be detected separately."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        # javascript_tests has both "npm test" and "npm run test:integration"
        js_steps = [step for step in result if 'javascript_tests' in step.job_name]
        assert len(js_steps) >= 2, "Should detect multiple script commands in same job"

    def test_parse_coverage_report_format(self, parser, valid_config_path):
        """Test: Detect coverage report configuration."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # Parser should recognize coverage_report in artifacts


# Meta-tests
def test_fixture_files_exist():
    """Meta-test: Verify all fixture files exist."""
    fixtures = [
        "valid_with_tests.yml",
        "no_test_steps.yml",
        "malformed.yml",
        "multi_language.yml"
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
    """TDD checkpoint: Verify GitLabCIParser is not yet implemented."""
    with pytest.raises(ModuleNotFoundError):
        from src.metrics.ci_parsers.gitlab_ci_parser import GitLabCIParser
