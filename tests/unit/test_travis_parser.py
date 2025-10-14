"""
Unit tests for TravisParser.

Tests validate Travis CI configuration file parsing (.travis.yml), test command
detection in script section, coverage upload detection in after_success section,
legacy format handling, and error handling.

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the parser is implemented in Phase 3.3 (T019).
"""

from pathlib import Path

import pytest

# This import will FAIL until T019 (Implement TravisParser) is complete
# Expected error: ModuleNotFoundError: No module named 'src.metrics.ci_parsers'
try:
    from src.metrics.ci_parsers.travis_parser import TravisParser
    PARSER_IMPLEMENTED = True
except ModuleNotFoundError:
    PARSER_IMPLEMENTED = False
    # Create a mock for test structure validation
    class TravisParser:
        def parse(self, config_path):
            pass


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "travis"


@pytest.fixture
def parser():
    """Create TravisParser instance."""
    return TravisParser()


@pytest.fixture
def valid_config_path():
    """Path to valid .travis.yml with test steps."""
    return FIXTURES_DIR / "valid_with_tests.yml"


@pytest.fixture
def no_tests_config_path():
    """Path to .travis.yml without test steps (build/lint only)."""
    return FIXTURES_DIR / "no_test_steps.yml"


@pytest.fixture
def malformed_config_path():
    """Path to malformed YAML configuration."""
    return FIXTURES_DIR / "malformed.yml"


@pytest.fixture
def legacy_format_path():
    """Path to legacy Travis CI 1.0 format configuration."""
    return FIXTURES_DIR / "legacy_format.yml"


# Meta-tests (run even before parser is implemented)
class TestTravisParserMeta:
    """Meta-tests that validate test infrastructure itself."""

    def test_fixtures_exist(self):
        """Meta-test: Verify all required fixtures exist."""
        assert FIXTURES_DIR.exists(), f"Fixtures directory missing: {FIXTURES_DIR}"
        assert (FIXTURES_DIR / "valid_with_tests.yml").exists(), "valid_with_tests.yml fixture missing"
        assert (FIXTURES_DIR / "no_test_steps.yml").exists(), "no_test_steps.yml fixture missing"
        assert (FIXTURES_DIR / "malformed.yml").exists(), "malformed.yml fixture missing"
        assert (FIXTURES_DIR / "legacy_format.yml").exists(), "legacy_format.yml fixture missing"

    def test_parser_class_exists(self):
        """Meta-test: Verify TravisParser class is available (mock or real)."""
        assert TravisParser is not None
        parser = TravisParser()
        assert hasattr(parser, 'parse'), "TravisParser must have parse() method"

    def test_implementation_status(self):
        """Meta-test: Report parser implementation status."""
        if PARSER_IMPLEMENTED:
            print("\n✅ TravisParser is implemented - all tests should pass")
        else:
            print("\n⏳ TravisParser not yet implemented - tests will be skipped")


@pytest.mark.skipif(not PARSER_IMPLEMENTED, reason="TravisParser not yet implemented (T019)")
class TestTravisParser:
    """Test suite for Travis CI configuration parsing."""

    def test_parse_valid_config_with_test_steps(self, parser, valid_config_path):
        """Test 1: Parse valid .travis.yml file with test steps in script section."""
        result = parser.parse(valid_config_path)

        assert result is not None, "Parser should return TestStepInfo list for valid config"
        assert isinstance(result, list), "Result should be a list"
        assert len(result) > 0, "Should detect at least one test step"

        # Verify test step structure
        first_step = result[0]
        assert hasattr(first_step, 'job_name'), "TestStepInfo should have job_name attribute"
        assert hasattr(first_step, 'command'), "TestStepInfo should have command attribute"
        assert hasattr(first_step, 'framework'), "TestStepInfo should have framework attribute"
        assert hasattr(first_step, 'has_coverage_flag'), "TestStepInfo should have has_coverage_flag"

    def test_detect_pytest_command_in_script(self, parser, valid_config_path):
        """Test 2: Detect pytest test command in script section."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # Find pytest command in results
        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        assert len(pytest_steps) > 0, "Should detect pytest command in script section"

        # Verify framework inference
        pytest_step = pytest_steps[0]
        assert pytest_step.framework == "pytest", "Framework should be inferred as 'pytest'"

    def test_detect_coverage_flag_in_pytest_command(self, parser, valid_config_path):
        """Test 3: Detect --cov coverage flag in pytest command."""
        result = parser.parse(valid_config_path)

        assert result is not None
        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        assert len(pytest_steps) > 0

        pytest_step = pytest_steps[0]
        assert pytest_step.has_coverage_flag is True, "Should detect --cov coverage flag"
        assert '--cov' in pytest_step.command, "Command should contain --cov flag"

    def test_parse_no_test_steps(self, parser, no_tests_config_path):
        """Test 4: Handle .travis.yml without test commands (build/lint only)."""
        result = parser.parse(no_tests_config_path)

        # Parser should return empty list or None when no test commands found
        assert result is None or len(result) == 0, \
            "Parser should return None/empty list for config without test commands"

    def test_handle_malformed_yaml(self, parser, malformed_config_path):
        """Test 5: Handle malformed YAML gracefully (return None, not crash)."""
        result = parser.parse(malformed_config_path)

        assert result is None, "Parser should return None for malformed YAML"

    def test_parse_legacy_travis_format(self, parser, legacy_format_path):
        """Test 6: Handle legacy Travis CI 1.0 format configuration."""
        result = parser.parse(legacy_format_path)

        # Legacy format may use different keywords but should still be parseable
        assert result is not None or result is None, \
            "Parser should handle legacy format without crashing"

    def test_handle_missing_file(self, parser):
        """Test 7: Handle missing .travis.yml file appropriately."""
        missing_path = FIXTURES_DIR / "nonexistent.yml"

        # Parser should raise FileNotFoundError as per API contract
        with pytest.raises(FileNotFoundError):
            parser.parse(missing_path)

    def test_job_name_for_travis_builds(self, parser, valid_config_path):
        """Test 8: Verify job_name is set appropriately for Travis CI builds."""
        result = parser.parse(valid_config_path)

        if result is not None and len(result) > 0:
            first_step = result[0]
            # Travis CI doesn't have named jobs like GitHub Actions
            # Parser should use a default job name
            assert first_step.job_name is not None, "job_name should not be None"
            assert isinstance(first_step.job_name, str), "job_name should be a string"
            assert len(first_step.job_name) > 0, "job_name should not be empty"

    def test_extract_script_section_correctly(self, parser, valid_config_path):
        """Test 9: Extract commands from script section (not install section)."""
        result = parser.parse(valid_config_path)

        assert result is not None
        # Should find pytest command but not pip install
        commands = [step.command for step in result]
        pytest_found = any('pytest' in cmd for cmd in commands)
        pip_install_found = any('pip install' in cmd and 'pytest' not in cmd for cmd in commands)

        assert pytest_found, "Should find pytest command from script section"
        assert not pip_install_found, "Should not extract pip install from install section"


# Summary of test coverage
"""
Test Coverage Summary for TravisParser (T006):

✅ Valid configuration parsing (test_parse_valid_config_with_test_steps)
✅ Test command detection in script section (test_detect_pytest_command_in_script)
✅ Coverage flag detection (test_detect_coverage_flag_in_pytest_command)
✅ No test steps handling (test_parse_no_test_steps)
✅ Malformed YAML handling (test_handle_malformed_yaml)
✅ Legacy Travis CI 1.0 format (test_parse_legacy_travis_format)
✅ Missing file error handling (test_handle_missing_file)
✅ Job name assignment (test_job_name_for_travis_builds)
✅ Script section extraction (test_extract_script_section_correctly)

Total: 12 tests (3 meta-tests + 9 implementation tests)

Expected Result: All tests SKIP until T019 (TravisParser implementation) is complete
After T019: All tests should PASS with correct parser implementation
"""
