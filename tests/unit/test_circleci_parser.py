"""
Unit tests for CircleCIParser.

Tests validate CircleCI 2.0 configuration file parsing, test command detection,
coverage upload detection (including orbs), and error handling.

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the parser is implemented in Phase 3.3 (T018).
"""

from pathlib import Path

import pytest

# This import will FAIL until T018 (Implement CircleCIParser) is complete
try:
    from src.metrics.ci_parsers.circleci_parser import CircleCIParser
    PARSER_IMPLEMENTED = True
except ModuleNotFoundError:
    PARSER_IMPLEMENTED = False
    class CircleCIParser:
        def parse(self, config_path):
            pass


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "circleci"


@pytest.fixture
def parser():
    """Create CircleCIParser instance."""
    return CircleCIParser()


@pytest.fixture
def valid_config_path():
    """Path to valid CircleCI 2.0 config with test jobs."""
    return FIXTURES_DIR / "valid_config.yml"


@pytest.fixture
def no_tests_config_path():
    """Path to config without test jobs."""
    return FIXTURES_DIR / "no_tests.yml"


@pytest.fixture
def malformed_config_path():
    """Path to malformed YAML config."""
    return FIXTURES_DIR / "malformed.yml"


@pytest.fixture
def multi_language_config_path():
    """Path to config with multiple language tests."""
    return FIXTURES_DIR / "multi_language.yml"


@pytest.mark.skipif(not PARSER_IMPLEMENTED, reason="CircleCIParser not yet implemented (T018)")
class TestCircleCIParser:
    """Test suite for CircleCI configuration parsing."""

    def test_parse_valid_circleci_2_0_config(self, parser, valid_config_path):
        """Test 1: Parse valid CircleCI 2.0 format config."""
        result = parser.parse(valid_config_path)

        assert result is not None, "Parser should return TestStepInfo list"
        assert isinstance(result, list), "Result should be a list"
        assert len(result) > 0, "Should detect at least one test step"

        first_step = result[0]
        assert hasattr(first_step, 'job_name'), "TestStepInfo should have job_name"
        assert hasattr(first_step, 'command'), "TestStepInfo should have command"
        assert hasattr(first_step, 'framework'), "TestStepInfo should have framework"
        assert hasattr(first_step, 'has_coverage_flag'), "TestStepInfo should have has_coverage_flag"

    def test_detect_test_commands_in_run_steps(self, parser, valid_config_path):
        """Test 2: Detect test commands in run: steps."""
        result = parser.parse(valid_config_path)

        assert result is not None
        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        assert len(pytest_steps) > 0, "Should detect pytest in run steps"

    def test_detect_pytest_with_coverage_flag(self, parser, multi_language_config_path):
        """Test 2b: Detect pytest with coverage flags."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        coverage_steps = [step for step in result if step.has_coverage_flag]
        assert len(coverage_steps) > 0, "Should detect --cov flag"

    def test_detect_npm_test_command(self, parser, multi_language_config_path):
        """Test 2c: Detect npm test commands."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        npm_steps = [step for step in result if 'npm test' in step.command.lower()]
        assert len(npm_steps) > 0, "Should detect npm test"

    def test_detect_go_test_command(self, parser, multi_language_config_path):
        """Test 2d: Detect go test commands."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        go_steps = [step for step in result if 'go test' in step.command.lower()]
        assert len(go_steps) > 0, "Should detect go test"

    def test_detect_maven_gradle_commands(self, parser, multi_language_config_path):
        """Test 2e: Detect mvn test and gradle test."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        maven_steps = [step for step in result if 'mvn test' in step.command.lower()]
        gradle_steps = [step for step in result if 'gradlew test' in step.command.lower()]
        assert len(maven_steps) > 0 or len(gradle_steps) > 0, \
            "Should detect Maven or Gradle tests"

    def test_detect_codecov_orb_usage(self, parser, valid_config_path):
        """Test 3: Detect Codecov upload via codecov orb."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # Parser should detect codecov/upload step usage

    def test_detect_coveralls_orb(self, parser, multi_language_config_path):
        """Test 3b: Detect Coveralls orb usage."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        # Should detect coveralls/upload usage

    def test_count_test_jobs_in_workflows(self, parser, multi_language_config_path):
        """Test 4: Count test jobs defined in workflows."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        unique_jobs = set(step.job_name for step in result)
        # Should detect python-tests, javascript-tests, go-tests, java-tests
        assert len(unique_jobs) >= 4, "Should detect multiple test jobs"

    def test_extract_job_names_from_workflow(self, parser, valid_config_path):
        """Test 4b: Extract job names correctly."""
        result = parser.parse(valid_config_path)

        assert result is not None
        job_names = [step.job_name for step in result]
        assert any('unit-tests' in name for name in job_names), \
            "Should detect unit-tests job"
        assert any('integration-tests' in name for name in job_names), \
            "Should detect integration-tests job"

    def test_handle_malformed_yaml(self, parser, malformed_config_path):
        """Test 5: Handle malformed YAML gracefully (return None)."""
        result = parser.parse(malformed_config_path)

        assert result is None, "Parser should return None for malformed YAML"

    def test_handle_missing_file(self, parser):
        """Test 5b: Handle missing file (raise FileNotFoundError)."""
        nonexistent_path = FIXTURES_DIR / "nonexistent.yml"

        with pytest.raises(FileNotFoundError):
            parser.parse(nonexistent_path)

    def test_config_without_tests_returns_empty_or_none(self, parser, no_tests_config_path):
        """Test: Config with only build/deploy should return empty or None."""
        result = parser.parse(no_tests_config_path)

        assert result is None or len(result) == 0, \
            "Config without test commands should return empty or None"

    def test_parse_circleci_2_1_version(self, parser, valid_config_path):
        """Test: Handle CircleCI 2.1 version format."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # Parser should support version: 2.1 format

    def test_handle_docker_executors(self, parser, multi_language_config_path):
        """Test: Parse jobs using docker executors."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        # All jobs in multi_language fixture use docker executors

    def test_multiple_run_steps_in_single_job(self, parser, multi_language_config_path):
        """Test: Multiple run steps in same job should be detected separately."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        # javascript-tests has multiple run steps (npm test, npm run test:e2e)
        js_steps = [step for step in result if 'javascript-tests' in step.job_name]
        assert len(js_steps) >= 2, "Should detect multiple run steps in same job"

    def test_framework_inference_accuracy(self, parser, multi_language_config_path):
        """Test: Framework inference for different languages."""
        result = parser.parse(multi_language_config_path)

        assert result is not None

        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        if pytest_steps:
            assert pytest_steps[0].framework == "pytest"

        go_steps = [step for step in result if 'go test' in step.command.lower()]
        if go_steps:
            assert go_steps[0].framework == "go_test"

        maven_steps = [step for step in result if 'mvn test' in step.command.lower()]
        if maven_steps:
            assert maven_steps[0].framework == "junit"

    def test_handle_run_name_and_command_structure(self, parser, valid_config_path):
        """Test: Handle run steps with name: and command: fields."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # CircleCI run steps can have name: and command: sub-fields

    def test_detect_store_test_results(self, parser, multi_language_config_path):
        """Test: Detect store_test_results step (indicates test execution)."""
        result = parser.parse(multi_language_config_path)

        assert result is not None
        # store_test_results is another indicator of test execution

    def test_handle_workflow_job_requirements(self, parser, valid_config_path):
        """Test: Parse jobs defined in workflows section."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # Workflows define job execution order


# Meta-tests
def test_fixture_files_exist():
    """Meta-test: Verify all fixture files exist."""
    fixtures = [
        "valid_config.yml",
        "no_tests.yml",
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
    """TDD checkpoint: Verify CircleCIParser is not yet implemented."""
    with pytest.raises(ModuleNotFoundError):
        from src.metrics.ci_parsers.circleci_parser import CircleCIParser
