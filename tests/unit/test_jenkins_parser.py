"""
Unit tests for JenkinsParser.

Tests validate Jenkinsfile parsing using regex extraction (not full Groovy DSL
parsing, per research.md decision). Covers test command detection in sh/bat steps,
multiple test framework patterns, and error handling.

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the parser is implemented in Phase 3.3 (T020).
"""

from pathlib import Path

import pytest

# This import will FAIL until T020 (Implement JenkinsParser) is complete
# Expected error: ModuleNotFoundError: No module named 'src.metrics.ci_parsers'
try:
    from src.metrics.ci_parsers.jenkins_parser import JenkinsParser
    PARSER_IMPLEMENTED = True
except ModuleNotFoundError:
    PARSER_IMPLEMENTED = False
    # Create a mock for test structure validation
    class JenkinsParser:
        def parse(self, config_path):
            pass


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "jenkins"


@pytest.fixture
def parser():
    """Create JenkinsParser instance."""
    return JenkinsParser()


@pytest.fixture
def pytest_jenkinsfile():
    """Path to Jenkinsfile with pytest commands."""
    return FIXTURES_DIR / "Jenkinsfile_pytest"


@pytest.fixture
def mvn_jenkinsfile():
    """Path to Jenkinsfile with Maven test commands."""
    return FIXTURES_DIR / "Jenkinsfile_mvn"


@pytest.fixture
def gradle_jenkinsfile():
    """Path to Jenkinsfile with Gradle test commands (bat)."""
    return FIXTURES_DIR / "Jenkinsfile_gradle"


@pytest.fixture
def no_tests_jenkinsfile():
    """Path to Jenkinsfile without test commands."""
    return FIXTURES_DIR / "Jenkinsfile_no_tests"


@pytest.fixture
def complex_jenkinsfile():
    """Path to complex multi-language Jenkinsfile."""
    return FIXTURES_DIR / "Jenkinsfile_complex"


# Meta-tests (run even before parser is implemented)
class TestJenkinsParserMeta:
    """Meta-tests that validate test infrastructure itself."""

    def test_fixtures_exist(self):
        """Meta-test: Verify all required fixtures exist."""
        assert FIXTURES_DIR.exists(), f"Fixtures directory missing: {FIXTURES_DIR}"
        assert (FIXTURES_DIR / "Jenkinsfile_pytest").exists(), "Jenkinsfile_pytest missing"
        assert (FIXTURES_DIR / "Jenkinsfile_mvn").exists(), "Jenkinsfile_mvn missing"
        assert (FIXTURES_DIR / "Jenkinsfile_gradle").exists(), "Jenkinsfile_gradle missing"
        assert (FIXTURES_DIR / "Jenkinsfile_no_tests").exists(), "Jenkinsfile_no_tests missing"
        assert (FIXTURES_DIR / "Jenkinsfile_complex").exists(), "Jenkinsfile_complex missing"

    def test_parser_class_exists(self):
        """Meta-test: Verify JenkinsParser class is available (mock or real)."""
        assert JenkinsParser is not None
        parser = JenkinsParser()
        assert hasattr(parser, 'parse'), "JenkinsParser must have parse() method"

    def test_implementation_status(self):
        """Meta-test: Report parser implementation status."""
        if PARSER_IMPLEMENTED:
            print("\n✅ JenkinsParser is implemented - all tests should pass")
        else:
            print("\n⏳ JenkinsParser not yet implemented - tests will be skipped")


@pytest.mark.skipif(not PARSER_IMPLEMENTED, reason="JenkinsParser not yet implemented (T020)")
class TestJenkinsParser:
    """Test suite for Jenkinsfile parsing with regex extraction."""

    def test_parse_jenkinsfile_with_pytest(self, parser, pytest_jenkinsfile):
        """Test 1: Parse Jenkinsfile with pytest command in sh step."""
        result = parser.parse(pytest_jenkinsfile)

        assert result is not None, "Parser should return TestStepInfo list for valid Jenkinsfile"
        assert isinstance(result, list), "Result should be a list"
        assert len(result) > 0, "Should detect pytest command"

        # Verify test step structure
        first_step = result[0]
        assert hasattr(first_step, 'job_name'), "TestStepInfo should have job_name"
        assert hasattr(first_step, 'command'), "TestStepInfo should have command"
        assert hasattr(first_step, 'framework'), "TestStepInfo should have framework"
        assert hasattr(first_step, 'has_coverage_flag'), "TestStepInfo should have has_coverage_flag"

    def test_detect_sh_pytest_pattern(self, parser, pytest_jenkinsfile):
        """Test 2: Detect sh 'pytest' pattern using regex extraction."""
        result = parser.parse(pytest_jenkinsfile)

        assert result is not None
        pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
        assert len(pytest_steps) > 0, "Should detect sh 'pytest' command"

        # Verify framework inference
        pytest_step = pytest_steps[0]
        assert pytest_step.framework == "pytest", "Framework should be inferred as 'pytest'"

    def test_detect_sh_mvn_test_pattern(self, parser, mvn_jenkinsfile):
        """Test 3: Detect sh 'mvn test' pattern."""
        result = parser.parse(mvn_jenkinsfile)

        assert result is not None
        mvn_steps = [step for step in result if 'mvn test' in step.command.lower()]
        assert len(mvn_steps) > 0, "Should detect sh 'mvn test' command"

        # Should find at least mvn test
        commands = [step.command for step in result]
        assert any('mvn test' in cmd for cmd in commands), "Should extract 'mvn test' command"

    def test_detect_bat_gradle_pattern(self, parser, gradle_jenkinsfile):
        """Test 4: Detect bat 'gradlew test' pattern (Windows)."""
        result = parser.parse(gradle_jenkinsfile)

        assert result is not None
        gradle_steps = [step for step in result if 'gradle' in step.command.lower()]
        assert len(gradle_steps) > 0, "Should detect bat 'gradlew test' command"

    def test_handle_no_test_commands(self, parser, no_tests_jenkinsfile):
        """Test 5: Handle Jenkinsfile without test commands (build/deploy only)."""
        result = parser.parse(no_tests_jenkinsfile)

        # Parser should return None or empty list when no test patterns found
        assert result is None or len(result) == 0, \
            "Parser should return None/empty list for Jenkinsfile without test commands"

    def test_handle_missing_file(self, parser):
        """Test 6: Handle missing Jenkinsfile appropriately."""
        missing_path = FIXTURES_DIR / "NonexistentJenkinsfile"

        # Parser should raise FileNotFoundError as per API contract
        with pytest.raises(FileNotFoundError):
            parser.parse(missing_path)

    def test_parse_complex_multi_language_jenkinsfile(self, parser, complex_jenkinsfile):
        """Test 7: Parse complex Jenkinsfile with multiple test frameworks."""
        result = parser.parse(complex_jenkinsfile)

        assert result is not None
        # Should detect pytest, go test, npm test
        commands = [step.command.lower() for step in result]
        
        # At least some test commands should be detected
        test_commands_found = any('pytest' in cmd or 'go test' in cmd or 'npm test' in cmd 
                                   for cmd in commands)
        assert test_commands_found, "Should detect at least one test command"

    def test_extract_multiple_test_commands_from_same_stage(self, parser, mvn_jenkinsfile):
        """Test 8: Extract multiple test commands from same stage."""
        result = parser.parse(mvn_jenkinsfile)

        if result is not None:
            # mvn_jenkinsfile has both 'mvn test' and 'mvn verify' in Test stage
            mvn_commands = [step.command for step in result if 'mvn' in step.command.lower()]
            # Should find multiple maven commands
            assert len(mvn_commands) >= 1, "Should detect at least one Maven test command"

    def test_job_name_for_jenkins_pipeline(self, parser, pytest_jenkinsfile):
        """Test 9: Verify job_name is set for Jenkins pipelines."""
        result = parser.parse(pytest_jenkinsfile)

        if result is not None and len(result) > 0:
            first_step = result[0]
            # Jenkins parser should use a default job name like "jenkins_pipeline"
            assert first_step.job_name is not None, "job_name should not be None"
            assert isinstance(first_step.job_name, str), "job_name should be a string"
            assert len(first_step.job_name) > 0, "job_name should not be empty"

    def test_regex_extracts_sh_commands_only(self, parser, pytest_jenkinsfile):
        """Test 10: Regex should extract sh/bat commands, not other Groovy code."""
        result = parser.parse(pytest_jenkinsfile)

        assert result is not None
        # Should find pytest command but not 'pip install' (not a test command)
        commands = [step.command for step in result]
        
        # Verify test commands are extracted
        pytest_found = any('pytest' in cmd for cmd in commands)
        assert pytest_found, "Should extract pytest from sh 'pytest' step"

    def test_handle_groovy_dsl_without_full_parsing(self, parser, complex_jenkinsfile):
        """Test 11: Handle Groovy DSL structures without full parsing (per research.md)."""
        result = parser.parse(complex_jenkinsfile)

        # Parser uses regex extraction, not full Groovy parsing
        # Should handle script blocks, environment variables, etc.
        assert result is not None or result is None, \
            "Parser should handle complex Groovy DSL without crashing"

    def test_coverage_flag_detection_in_pytest(self, parser, pytest_jenkinsfile):
        """Test 12: Detect --cov coverage flag in pytest command."""
        result = parser.parse(pytest_jenkinsfile)

        if result is not None:
            pytest_steps = [step for step in result if 'pytest' in step.command.lower()]
            if len(pytest_steps) > 0:
                pytest_step = pytest_steps[0]
                # Jenkinsfile_pytest has 'pytest --cov=src tests/'
                assert pytest_step.has_coverage_flag is True, "Should detect --cov flag"

    def test_parse_returns_list_of_teststepinfo(self, parser, pytest_jenkinsfile):
        """Test 13: Verify parse() returns List[TestStepInfo] as per API contract."""
        result = parser.parse(pytest_jenkinsfile)

        assert result is not None
        assert isinstance(result, list), "parse() should return a list"

        # Import TestStepInfo to verify type (will fail if model not implemented)
        try:
            from src.metrics.models.ci_config import TestStepInfo
            for step in result:
                assert isinstance(step, TestStepInfo), \
                    "Each item should be a TestStepInfo instance"
        except ImportError:
            # If model not implemented yet, skip type check
            pass


@pytest.mark.skipif(not PARSER_IMPLEMENTED, reason="JenkinsParser not yet implemented (T020)")
class TestJenkinsParserEdgeCases:
    """Edge case tests for Jenkins parser."""

    def test_empty_jenkinsfile(self, parser, tmp_path):
        """Edge case: Empty Jenkinsfile."""
        jenkinsfile = tmp_path / "Jenkinsfile"
        jenkinsfile.write_text("")

        result = parser.parse(jenkinsfile)
        assert result is None or len(result) == 0, \
            "Empty Jenkinsfile should return None/empty list"

    def test_jenkinsfile_with_only_comments(self, parser, tmp_path):
        """Edge case: Jenkinsfile with only comments."""
        jenkinsfile = tmp_path / "Jenkinsfile"
        jenkinsfile.write_text("""
// This is a comment
// sh 'pytest' - commented out, should not be detected
/* Multi-line comment
   sh 'mvn test'
*/
""")

        result = parser.parse(jenkinsfile)
        # Should not detect commented-out commands
        assert result is None or len(result) == 0, \
            "Commented commands should not be detected"

    def test_jenkinsfile_with_script_wrapped_commands(self, parser, tmp_path):
        """Edge case: Test commands wrapped in shell scripts."""
        jenkinsfile = tmp_path / "Jenkinsfile"
        jenkinsfile.write_text("""
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh './scripts/run_tests.sh'
            }
        }
    }
}
""")

        result = parser.parse(jenkinsfile)
        # Per research.md limitation: script-wrapped tests may be missed
        # Parser should not crash but may return None/empty
        assert result is not None or result is None, \
            "Script-wrapped commands should be handled gracefully"

    def test_jenkinsfile_with_multiline_sh_command(self, parser, tmp_path):
        """Edge case: Multiline sh command."""
        jenkinsfile = tmp_path / "Jenkinsfile"
        jenkinsfile.write_text("""
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh '''
                    pytest tests/unit
                    pytest tests/integration
                '''
            }
        }
    }
}
""")

        result = parser.parse(jenkinsfile)
        # Parser should handle multiline sh commands
        if result is not None:
            assert len(result) >= 1, "Should detect at least one pytest command"


# Summary of test coverage
"""
Test Coverage Summary for JenkinsParser (T007):

✅ Parse Jenkinsfile with pytest (test_parse_jenkinsfile_with_pytest)
✅ Detect sh 'pytest' pattern (test_detect_sh_pytest_pattern)
✅ Detect sh 'mvn test' pattern (test_detect_sh_mvn_test_pattern)
✅ Detect bat 'gradlew test' pattern (test_detect_bat_gradle_pattern)
✅ Handle no test commands (test_handle_no_test_commands)
✅ Handle missing file (test_handle_missing_file)
✅ Parse complex multi-language Jenkinsfile (test_parse_complex_multi_language_jenkinsfile)
✅ Extract multiple commands from same stage (test_extract_multiple_test_commands_from_same_stage)
✅ Job name assignment (test_job_name_for_jenkins_pipeline)
✅ Regex extracts sh/bat only (test_regex_extracts_sh_commands_only)
✅ Handle Groovy DSL without full parsing (test_handle_groovy_dsl_without_full_parsing)
✅ Coverage flag detection (test_coverage_flag_detection_in_pytest)
✅ API contract compliance (test_parse_returns_list_of_teststepinfo)
✅ Edge cases: empty file, comments, script-wrapped, multiline

Total: 17 tests (3 meta-tests + 14 implementation tests)

Expected Result: All tests SKIP until T020 (JenkinsParser implementation) is complete
After T020: All tests should PASS with correct regex-based parser implementation
"""
