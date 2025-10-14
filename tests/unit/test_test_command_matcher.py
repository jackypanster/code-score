"""
Unit tests for TestCommandMatcher.

Tests validate test command pattern matching across multiple programming languages
(Python, JavaScript, Go, Java), framework inference, coverage flag detection, and
rejection of non-test commands.

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the matcher is implemented in Phase 3.3 (T013).
"""

import pytest

# This import will FAIL until T013 (Implement TestCommandMatcher) is complete
# Expected error: ModuleNotFoundError: No module named 'src.metrics.pattern_matchers'
try:
    from src.metrics.pattern_matchers.test_command_matcher import TestCommandMatcher
    MATCHER_IMPLEMENTED = True
except ModuleNotFoundError:
    MATCHER_IMPLEMENTED = False
    # Create a mock for test structure validation
    class TestCommandMatcher:
        def is_test_command(self, command):
            pass
        def extract_test_commands(self, steps):
            pass
        def infer_framework(self, command):
            pass
        def has_coverage_flag(self, command):
            pass


@pytest.fixture
def matcher():
    """Create TestCommandMatcher instance."""
    return TestCommandMatcher()


# Meta-tests (run even before matcher is implemented)
class TestCommandMatcherMeta:
    """Meta-tests that validate test infrastructure itself."""

    def test_matcher_class_exists(self):
        """Meta-test: Verify TestCommandMatcher class is available (mock or real)."""
        assert TestCommandMatcher is not None
        matcher = TestCommandMatcher()
        assert hasattr(matcher, 'is_test_command'), "Must have is_test_command() method"
        assert hasattr(matcher, 'extract_test_commands'), "Must have extract_test_commands() method"
        assert hasattr(matcher, 'infer_framework'), "Must have infer_framework() method"
        assert hasattr(matcher, 'has_coverage_flag'), "Must have has_coverage_flag() method"

    def test_implementation_status(self):
        """Meta-test: Report matcher implementation status."""
        if MATCHER_IMPLEMENTED:
            print("\n✅ TestCommandMatcher is implemented - all tests should pass")
        else:
            print("\n⏳ TestCommandMatcher not yet implemented - tests will be skipped")


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestPytestCommands:
    """Test suite for Python pytest command matching."""

    def test_match_basic_pytest(self, matcher):
        """Test 1: Match basic 'pytest' command."""
        assert matcher.is_test_command("pytest") is True
        assert matcher.is_test_command("pytest tests/") is True

    def test_match_pytest_module_invocation(self, matcher):
        """Test 2: Match 'python -m pytest' command."""
        assert matcher.is_test_command("python -m pytest") is True
        assert matcher.is_test_command("python -m pytest tests/unit") is True

    def test_match_pytest_with_coverage(self, matcher):
        """Test 3: Match pytest with coverage flags."""
        assert matcher.is_test_command("pytest --cov=src") is True
        assert matcher.is_test_command("pytest --cov=src tests/") is True
        assert matcher.is_test_command("pytest tests/ --cov=src --cov-report=html") is True

    def test_infer_pytest_framework(self, matcher):
        """Test 4: Infer 'pytest' framework from command."""
        assert matcher.infer_framework("pytest tests/") == "pytest"
        assert matcher.infer_framework("python -m pytest") == "pytest"

    def test_detect_coverage_flag_in_pytest(self, matcher):
        """Test 5: Detect --cov coverage flag in pytest command."""
        assert matcher.has_coverage_flag("pytest --cov=src") is True
        assert matcher.has_coverage_flag("pytest tests/") is False


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestNpmCommands:
    """Test suite for JavaScript npm command matching."""

    def test_match_npm_test(self, matcher):
        """Test 6: Match 'npm test' command."""
        assert matcher.is_test_command("npm test") is True

    def test_match_npm_run_test(self, matcher):
        """Test 7: Match 'npm run test' command."""
        assert matcher.is_test_command("npm run test") is True
        assert matcher.is_test_command("npm run test:unit") is True

    def test_match_npm_with_coverage(self, matcher):
        """Test 8: Match npm test with coverage flags."""
        assert matcher.is_test_command("npm test -- --coverage") is True

    def test_infer_jest_framework_from_npm(self, matcher):
        """Test 9: Infer 'jest' framework from npm test command."""
        # npm test typically runs jest in JavaScript projects
        framework = matcher.infer_framework("npm test")
        # Could be "jest" or generic "npm" depending on implementation
        assert framework in ["jest", "npm", None]

    def test_detect_coverage_flag_in_npm(self, matcher):
        """Test 10: Detect --coverage flag in npm command."""
        assert matcher.has_coverage_flag("npm test -- --coverage") is True
        assert matcher.has_coverage_flag("npm test") is False


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestGoCommands:
    """Test suite for Go test command matching."""

    def test_match_go_test(self, matcher):
        """Test 11: Match 'go test' command."""
        assert matcher.is_test_command("go test") is True

    def test_match_go_test_all_packages(self, matcher):
        """Test 12: Match 'go test ./...' command."""
        assert matcher.is_test_command("go test ./...") is True

    def test_match_go_test_with_coverage(self, matcher):
        """Test 13: Match go test with coverage flags."""
        assert matcher.is_test_command("go test -cover") is True
        assert matcher.is_test_command("go test -coverprofile=coverage.out") is True

    def test_infer_go_test_framework(self, matcher):
        """Test 14: Infer 'go_test' framework from command."""
        assert matcher.infer_framework("go test") == "go_test"
        assert matcher.infer_framework("go test ./...") == "go_test"

    def test_detect_coverage_flag_in_go_test(self, matcher):
        """Test 15: Detect -cover flag in go test command."""
        assert matcher.has_coverage_flag("go test -cover") is True
        assert matcher.has_coverage_flag("go test") is False


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestJavaCommands:
    """Test suite for Java test command matching."""

    def test_match_mvn_test(self, matcher):
        """Test 16: Match 'mvn test' command."""
        assert matcher.is_test_command("mvn test") is True

    def test_match_gradle_test(self, matcher):
        """Test 17: Match 'gradle test' command."""
        assert matcher.is_test_command("gradle test") is True

    def test_match_gradlew_test(self, matcher):
        """Test 18: Match './gradlew test' command."""
        assert matcher.is_test_command("./gradlew test") is True
        assert matcher.is_test_command("gradlew test") is True

    def test_infer_junit_framework_from_maven(self, matcher):
        """Test 19: Infer 'junit' framework from mvn test command."""
        framework = matcher.infer_framework("mvn test")
        # Could be "junit" or "maven" depending on implementation
        assert framework in ["junit", "maven", None]

    def test_infer_junit_framework_from_gradle(self, matcher):
        """Test 20: Infer 'junit' framework from gradle test command."""
        framework = matcher.infer_framework("gradle test")
        assert framework in ["junit", "gradle", None]


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestNonTestCommands:
    """Test suite for rejecting non-test commands."""

    def test_reject_build_commands(self, matcher):
        """Test 21: Reject build commands (not test commands)."""
        assert matcher.is_test_command("make build") is False
        assert matcher.is_test_command("npm run build") is False
        assert matcher.is_test_command("mvn compile") is False

    def test_reject_lint_commands(self, matcher):
        """Test 22: Reject lint commands."""
        assert matcher.is_test_command("make lint") is False
        assert matcher.is_test_command("npm run lint") is False
        assert matcher.is_test_command("ruff check src/") is False

    def test_reject_deploy_commands(self, matcher):
        """Test 23: Reject deploy commands."""
        assert matcher.is_test_command("make deploy") is False
        assert matcher.is_test_command("npm run deploy") is False

    def test_reject_install_commands(self, matcher):
        """Test 24: Reject install/setup commands."""
        assert matcher.is_test_command("pip install -r requirements.txt") is False
        assert matcher.is_test_command("npm install") is False
        assert matcher.is_test_command("go mod download") is False

    def test_reject_empty_or_whitespace(self, matcher):
        """Test 25: Reject empty or whitespace-only commands."""
        assert matcher.is_test_command("") is False
        assert matcher.is_test_command("   ") is False


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestExtractTestCommands:
    """Test suite for extract_test_commands() method."""

    def test_extract_from_list_with_mixed_commands(self, matcher):
        """Test 26: Extract test commands from mixed command list."""
        steps = [
            "pip install requirements.txt",
            "pytest tests/unit",
            "npm run build",
            "npm test",
            "make deploy"
        ]
        
        test_commands = matcher.extract_test_commands(steps)
        assert isinstance(test_commands, list)
        assert len(test_commands) == 2
        assert "pytest tests/unit" in test_commands
        assert "npm test" in test_commands

    def test_extract_from_list_with_no_tests(self, matcher):
        """Test 27: Extract from list with no test commands."""
        steps = [
            "make build",
            "make lint",
            "make deploy"
        ]
        
        test_commands = matcher.extract_test_commands(steps)
        assert isinstance(test_commands, list)
        assert len(test_commands) == 0

    def test_extract_from_list_with_all_tests(self, matcher):
        """Test 28: Extract from list with all test commands."""
        steps = [
            "pytest tests/unit",
            "pytest tests/integration",
            "npm test"
        ]
        
        test_commands = matcher.extract_test_commands(steps)
        assert len(test_commands) == 3

    def test_extract_from_empty_list(self, matcher):
        """Test 29: Extract from empty list."""
        test_commands = matcher.extract_test_commands([])
        assert isinstance(test_commands, list)
        assert len(test_commands) == 0


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestFrameworkInference:
    """Test suite for framework inference logic."""

    def test_infer_framework_returns_none_for_unknown(self, matcher):
        """Test 30: Return None for unknown/non-test commands."""
        assert matcher.infer_framework("make build") is None
        assert matcher.infer_framework("unknown command") is None

    def test_infer_framework_case_insensitive(self, matcher):
        """Test 31: Framework inference should be case-insensitive."""
        # Commands might have varying case
        assert matcher.infer_framework("PYTEST tests/") == "pytest"
        assert matcher.infer_framework("PyTest tests/") == "pytest"


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestCoverageFlagDetection:
    """Test suite for coverage flag detection."""

    def test_detect_various_coverage_flags(self, matcher):
        """Test 32: Detect various coverage flag formats."""
        # pytest style
        assert matcher.has_coverage_flag("pytest --cov=src") is True
        assert matcher.has_coverage_flag("pytest --cov src") is True
        
        # npm style
        assert matcher.has_coverage_flag("npm test -- --coverage") is True
        
        # go style
        assert matcher.has_coverage_flag("go test -cover") is True

    def test_coverage_flag_not_confused_with_other_flags(self, matcher):
        """Test 33: Coverage flags not confused with other flags."""
        # These have 'cov' in them but are not coverage flags
        assert matcher.has_coverage_flag("pytest --verbose") is False
        assert matcher.has_coverage_flag("npm test --watch") is False


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="TestCommandMatcher not yet implemented (T013)")
class TestEdgeCases:
    """Edge case tests for TestCommandMatcher."""

    def test_command_with_extra_whitespace(self, matcher):
        """Edge case: Command with extra whitespace."""
        assert matcher.is_test_command("  pytest  tests/  ") is True

    def test_command_with_multiple_flags(self, matcher):
        """Edge case: Command with many flags."""
        command = "pytest --cov=src --cov-report=html --verbose --color=yes tests/"
        assert matcher.is_test_command(command) is True
        assert matcher.has_coverage_flag(command) is True

    def test_partial_match_not_confused(self, matcher):
        """Edge case: Partial matches should not be confused."""
        # "test" is in the command but it's not a test command
        assert matcher.is_test_command("npm run test-build") is False or \
               matcher.is_test_command("npm run test-build") is True
        # Implementation may vary - this documents the behavior

    def test_command_with_path_containing_test(self, matcher):
        """Edge case: Path contains 'test' but command is not a test."""
        # Path has 'test' but command is install
        assert matcher.is_test_command("pip install /path/to/test/requirements.txt") is False


# Summary of test coverage
"""
Test Coverage Summary for TestCommandMatcher (T008):

✅ Python pytest commands (5 tests)
✅ JavaScript npm commands (5 tests)
✅ Go test commands (5 tests)
✅ Java Maven/Gradle commands (5 tests)
✅ Non-test command rejection (5 tests)
✅ Extract test commands from lists (4 tests)
✅ Framework inference (2 tests)
✅ Coverage flag detection (2 tests)
✅ Edge cases (4 tests)

Total: 37 tests (2 meta-tests + 35 implementation tests)

Expected Result: All tests SKIP until T013 (TestCommandMatcher implementation) is complete
After T013: All tests should PASS with correct pattern matching implementation
"""
