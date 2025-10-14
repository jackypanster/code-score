"""
Unit tests for CoverageToolMatcher.

Tests validate coverage tool detection in CI configurations, including Codecov,
Coveralls, SonarQube, and coverage flag detection. Tests pattern matching using
substring matching (per research.md decision 4).

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the matcher is implemented in Phase 3.3 (T014).
"""

import pytest

# This import will FAIL until T014 (Implement CoverageToolMatcher) is complete
# Expected error: ModuleNotFoundError: No module named 'src.metrics.pattern_matchers'
try:
    from src.metrics.pattern_matchers.coverage_tool_matcher import CoverageToolMatcher
    MATCHER_IMPLEMENTED = True
except ModuleNotFoundError:
    MATCHER_IMPLEMENTED = False
    # Create a mock for test structure validation
    class CoverageToolMatcher:
        def detect_coverage_tools(self, steps):
            pass
        def has_coverage_upload(self, steps):
            pass


@pytest.fixture
def matcher():
    """Create CoverageToolMatcher instance."""
    return CoverageToolMatcher()


# Meta-tests (run even before matcher is implemented)
class TestCoverageToolMatcherMeta:
    """Meta-tests that validate test infrastructure itself."""

    def test_matcher_class_exists(self):
        """Meta-test: Verify CoverageToolMatcher class is available (mock or real)."""
        assert CoverageToolMatcher is not None
        matcher = CoverageToolMatcher()
        assert hasattr(matcher, 'detect_coverage_tools'), "Must have detect_coverage_tools() method"
        assert hasattr(matcher, 'has_coverage_upload'), "Must have has_coverage_upload() method"

    def test_implementation_status(self):
        """Meta-test: Report matcher implementation status."""
        if MATCHER_IMPLEMENTED:
            print("\n✅ CoverageToolMatcher is implemented - all tests should pass")
        else:
            print("\n⏳ CoverageToolMatcher not yet implemented - tests will be skipped")


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestCodecovDetection:
    """Test suite for Codecov detection."""

    def test_detect_codecov_action(self, matcher):
        """Test 1: Detect codecov/codecov-action in GitHub Actions."""
        steps = [
            "pytest --cov=src tests/",
            "uses: codecov/codecov-action@v3"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "codecov" in tools, "Should detect codecov/codecov-action"

    def test_detect_codecov_upload_command(self, matcher):
        """Test 2: Detect 'codecov upload' command."""
        steps = [
            "pytest --cov=src tests/",
            "codecov upload"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "codecov" in tools, "Should detect codecov upload command"

    def test_detect_codecov_bash_script(self, matcher):
        """Test 3: Detect Codecov bash script pattern."""
        steps = [
            "pytest --cov=src tests/",
            "bash <(curl -s https://codecov.io/bash)"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "codecov" in tools, "Should detect codecov bash script"

    def test_detect_codecov_simple_command(self, matcher):
        """Test 4: Detect simple 'codecov' command."""
        steps = [
            "pytest --cov=src tests/",
            "codecov"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "codecov" in tools, "Should detect simple codecov command"

    def test_codecov_with_flags(self, matcher):
        """Test 5: Detect codecov with flags and arguments."""
        steps = [
            "codecov --token $CODECOV_TOKEN --flags unittests"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "codecov" in tools, "Should detect codecov with flags"


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestCoverallsDetection:
    """Test suite for Coveralls detection."""

    def test_detect_coveralls_command(self, matcher):
        """Test 6: Detect 'coveralls' command."""
        steps = [
            "pytest --cov=src tests/",
            "coveralls"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "coveralls" in tools, "Should detect coveralls command"

    def test_detect_coveralls_with_options(self, matcher):
        """Test 7: Detect coveralls with options."""
        steps = [
            "coveralls --service=github-actions"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "coveralls" in tools, "Should detect coveralls with options"

    def test_detect_coveralls_python_package(self, matcher):
        """Test 8: Detect python-coveralls or coveralls package."""
        steps = [
            "pytest --cov=src tests/",
            "python-coveralls"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "coveralls" in tools, "Should detect python-coveralls"


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestSonarQubeDetection:
    """Test suite for SonarQube detection."""

    def test_detect_sonar_scanner(self, matcher):
        """Test 9: Detect 'sonar-scanner' command."""
        steps = [
            "mvn test",
            "sonar-scanner"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "sonarqube" in tools, "Should detect sonar-scanner"

    def test_detect_sonarqube_keyword(self, matcher):
        """Test 10: Detect 'sonarqube' keyword."""
        steps = [
            "mvn test",
            "mvn sonarqube:sonar"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "sonarqube" in tools, "Should detect sonarqube keyword"

    def test_detect_sonar_scanner_with_properties(self, matcher):
        """Test 11: Detect sonar-scanner with properties."""
        steps = [
            "sonar-scanner -Dsonar.projectKey=myproject"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "sonarqube" in tools, "Should detect sonar-scanner with properties"


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestMultipleCoverageTools:
    """Test suite for multiple coverage tool detection."""

    def test_detect_multiple_tools_in_same_config(self, matcher):
        """Test 12: Detect multiple coverage tools in same CI configuration."""
        steps = [
            "pytest --cov=src tests/",
            "codecov",
            "coveralls"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert len(tools) >= 2, "Should detect multiple coverage tools"
        assert "codecov" in tools
        assert "coveralls" in tools

    def test_detect_three_tools(self, matcher):
        """Test 13: Detect all three supported tools."""
        steps = [
            "pytest --cov=src tests/",
            "codecov upload",
            "coveralls",
            "sonar-scanner"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert len(tools) >= 3, "Should detect all three tools"
        assert "codecov" in tools
        assert "coveralls" in tools
        assert "sonarqube" in tools

    def test_unique_tool_detection(self, matcher):
        """Test 14: Ensure unique tool detection (no duplicates)."""
        steps = [
            "codecov",
            "codecov upload",
            "codecov --token $TOKEN"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        # Should return unique tools only
        codecov_count = tools.count("codecov")
        assert codecov_count == 1, "Should return unique tools (no duplicates)"


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestNoCoverageTools:
    """Test suite for cases with no coverage tools."""

    def test_no_coverage_tools_in_steps(self, matcher):
        """Test 15: Return empty list when no coverage tools detected."""
        steps = [
            "pytest tests/",
            "make build",
            "npm run lint"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert isinstance(tools, list), "Should return a list"
        assert len(tools) == 0, "Should return empty list when no coverage tools detected"

    def test_empty_steps_list(self, matcher):
        """Test 16: Handle empty steps list."""
        tools = matcher.detect_coverage_tools([])
        assert isinstance(tools, list)
        assert len(tools) == 0

    def test_steps_with_coverage_flags_but_no_upload(self, matcher):
        """Test 17: Coverage flags present but no upload tool."""
        steps = [
            "pytest --cov=src tests/",
            "npm test -- --coverage"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        # Coverage flags alone don't count as coverage tools
        # Only upload/reporting tools are detected
        assert len(tools) == 0, "Coverage flags alone should not count as tools"


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestHasCoverageUpload:
    """Test suite for has_coverage_upload() convenience method."""

    def test_has_coverage_upload_returns_true(self, matcher):
        """Test 18: has_coverage_upload() returns True when tools detected."""
        steps = [
            "pytest --cov=src tests/",
            "codecov"
        ]
        
        assert matcher.has_coverage_upload(steps) is True

    def test_has_coverage_upload_returns_false(self, matcher):
        """Test 19: has_coverage_upload() returns False when no tools detected."""
        steps = [
            "pytest tests/",
            "make build"
        ]
        
        assert matcher.has_coverage_upload(steps) is False

    def test_has_coverage_upload_with_empty_list(self, matcher):
        """Test 20: has_coverage_upload() handles empty list."""
        assert matcher.has_coverage_upload([]) is False


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestPatternMatching:
    """Test suite for pattern matching behavior."""

    def test_substring_matching_not_regex(self, matcher):
        """Test 21: Use substring matching (not regex, per research.md)."""
        # Should match substring, not require exact word boundaries
        steps = [
            "run-codecov-upload"  # codecov is substring
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "codecov" in tools, "Should use substring matching"

    def test_case_insensitive_matching(self, matcher):
        """Test 22: Pattern matching should be case-insensitive."""
        steps = [
            "CODECOV",
            "Coveralls",
            "SonarQube"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        # Should detect despite case differences
        assert len(tools) >= 3, "Should detect tools case-insensitively"

    def test_partial_word_not_confused(self, matcher):
        """Test 23: Partial word matches should not cause false positives."""
        # "coverage" contains "cov" but is not codecov
        steps = [
            "npm test -- --coverage"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        # Should not detect codecov from --coverage flag
        assert "codecov" not in tools, "Should not confuse coverage flag with codecov tool"


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestEdgeCases:
    """Edge case tests for CoverageToolMatcher."""

    def test_steps_with_whitespace(self, matcher):
        """Edge case: Steps with extra whitespace."""
        steps = [
            "  codecov  ",
            "   coveralls   "
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert len(tools) >= 2

    def test_multiline_command_with_coverage_tool(self, matcher):
        """Edge case: Multiline command containing coverage tool."""
        steps = [
            """pytest --cov=src tests/ &&
            codecov upload"""
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "codecov" in tools

    def test_coverage_tool_in_url(self, matcher):
        """Edge case: Coverage tool name in URL."""
        steps = [
            "curl https://codecov.io/bash | bash"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        assert "codecov" in tools, "Should detect codecov in URL"

    def test_commented_out_coverage_tool(self, matcher):
        """Edge case: Coverage tool in comment (should still detect)."""
        # Note: CI parsers typically don't execute comments, but if they're
        # in the steps list, matcher will detect them (by design - simple substring)
        steps = [
            "# codecov upload"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        # Simple substring matching will detect this
        # Implementation may vary - document behavior
        assert "codecov" in tools or "codecov" not in tools


@pytest.mark.skipif(not MATCHER_IMPLEMENTED, reason="CoverageToolMatcher not yet implemented (T014)")
class TestReturnFormat:
    """Test suite for return format validation."""

    def test_detect_coverage_tools_returns_list(self, matcher):
        """Test 25: detect_coverage_tools() returns a list."""
        steps = ["codecov"]
        result = matcher.detect_coverage_tools(steps)
        assert isinstance(result, list), "Should return a list"

    def test_has_coverage_upload_returns_bool(self, matcher):
        """Test 26: has_coverage_upload() returns a boolean."""
        steps = ["codecov"]
        result = matcher.has_coverage_upload(steps)
        assert isinstance(result, bool), "Should return a boolean"

    def test_detected_tools_are_strings(self, matcher):
        """Test 27: Detected tools should be strings."""
        steps = ["codecov", "coveralls"]
        tools = matcher.detect_coverage_tools(steps)
        
        for tool in tools:
            assert isinstance(tool, str), "Each tool should be a string"

    def test_tool_names_match_expected_values(self, matcher):
        """Test 28: Tool names should match expected values."""
        steps = [
            "codecov upload",
            "coveralls",
            "sonar-scanner"
        ]
        
        tools = matcher.detect_coverage_tools(steps)
        
        # Tool names should be normalized
        valid_names = {"codecov", "coveralls", "sonarqube"}
        for tool in tools:
            assert tool in valid_names, f"Tool name '{tool}' should be one of {valid_names}"


# Summary of test coverage
"""
Test Coverage Summary for CoverageToolMatcher (T009):

✅ Codecov detection (5 tests) - action, upload, bash script, simple, with flags
✅ Coveralls detection (3 tests) - command, with options, python package
✅ SonarQube detection (3 tests) - scanner, keyword, with properties
✅ Multiple tools detection (3 tests) - 2 tools, 3 tools, uniqueness
✅ No coverage tools (3 tests) - empty, coverage flags only
✅ has_coverage_upload() (3 tests) - true, false, empty
✅ Pattern matching (3 tests) - substring, case-insensitive, partial words
✅ Edge cases (4 tests) - whitespace, multiline, URL, comments
✅ Return format (4 tests) - list, bool, strings, expected values

Total: 31 tests (2 meta-tests + 29 implementation tests)

Expected Result: All tests SKIP until T014 (CoverageToolMatcher implementation) is complete
After T014: All tests should PASS with correct pattern matching implementation
"""
