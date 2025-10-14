"""Pattern matcher for test commands in CI/CD configurations.

This module provides TestCommandMatcher for detecting test execution commands
across multiple programming languages (Python, JavaScript, Go, Java) using
simple substring matching (per research.md Decision 4).

Constitutional Compliance:
- Principle II (KISS): Hardcoded pattern list with O(n) substring matching
- Principle III (Transparency): Explicit command list and matching logic
"""

from typing import List, Optional


class TestCommandMatcher:
    """Matcher for test commands in CI configuration steps.

    Uses hardcoded pattern lists with substring matching for performance
    and simplicity (per research.md). Supports 4 languages:
    - Python: pytest, python -m pytest
    - JavaScript: npm test, npm run test
    - Go: go test
    - Java: mvn test, gradle test, ./gradlew test

    Example:
        >>> matcher = TestCommandMatcher()
        >>> matcher.is_test_command("pytest --cov=src")
        True
        >>> matcher.infer_framework("npm test")
        'jest'
        >>> matcher.has_coverage_flag("go test -cover")
        True
    """

    # Test command patterns per FR-007
    TEST_COMMANDS = [
        # Python
        "pytest",
        "python -m pytest",
        # JavaScript/TypeScript
        "npm test",
        "npm run test",
        # Go
        "go test",
        # Java
        "mvn test",
        "gradle test",
        "./gradlew test",
        "gradlew test",  # Windows or direct execution
    ]

    # Coverage flags for detection
    COVERAGE_FLAGS = [
        "--cov",           # pytest coverage flag
        "--coverage",      # generic coverage flag
        "-cover",          # go test coverage flag
        "-coverprofile",   # go test coverage profile
    ]

    def is_test_command(self, command: str) -> bool:
        """Check if command contains a test pattern.

        Uses substring matching (not regex) per research.md Decision 4.
        Time complexity: O(n * m) where n = len(TEST_COMMANDS), m = len(command).
        Case-insensitive to handle varying CI configuration styles.

        Args:
            command: Command string to check (e.g., "pytest --cov=src tests/").

        Returns:
            True if command contains any test pattern, False otherwise.

        Example:
            >>> matcher = TestCommandMatcher()
            >>> matcher.is_test_command("pytest tests/")
            True
            >>> matcher.is_test_command("PYTEST tests/")
            True
            >>> matcher.is_test_command("npm run build")
            False
        """
        if not command:
            return False

        # Case-insensitive substring matching for each test command pattern
        command_lower = command.lower()
        return any(test_cmd in command_lower for test_cmd in self.TEST_COMMANDS)

    def extract_test_commands(self, steps: List[str]) -> List[str]:
        """Filter test commands from CI steps.

        Args:
            steps: List of CI step commands.

        Returns:
            List of commands that contain test patterns.
            Empty list if no test commands found.

        Example:
            >>> matcher = TestCommandMatcher()
            >>> steps = ["npm install", "npm test", "npm run build"]
            >>> matcher.extract_test_commands(steps)
            ['npm test']
        """
        return [step for step in steps if self.is_test_command(step)]

    def infer_framework(self, command: str) -> Optional[str]:
        """Infer test framework from command string.

        Returns standardized framework names per TestStepInfo.framework field:
        - "pytest": Python pytest framework
        - "jest": JavaScript jest framework (via npm test)
        - "go_test": Go standard testing package
        - "junit": Java JUnit framework (via maven/gradle)
        - None: Cannot infer framework

        Case-insensitive to handle varying CI configuration styles.

        Args:
            command: Test command string.

        Returns:
            Framework name or None if cannot infer.

        Example:
            >>> matcher = TestCommandMatcher()
            >>> matcher.infer_framework("pytest --cov=src")
            'pytest'
            >>> matcher.infer_framework("PYTEST tests/")
            'pytest'
            >>> matcher.infer_framework("npm test")
            'jest'
            >>> matcher.infer_framework("go test ./...")
            'go_test'
        """
        if not command:
            return None

        # Case-insensitive matching
        command_lower = command.lower()

        # Python: pytest
        if "pytest" in command_lower:
            return "pytest"

        # JavaScript: jest (most common npm test runner)
        if "npm test" in command_lower or "npm run test" in command_lower:
            return "jest"

        # Go: go test
        if "go test" in command_lower:
            return "go_test"

        # Java: junit (via maven or gradle)
        if "mvn test" in command_lower or "gradle test" in command_lower or "gradlew test" in command_lower:
            return "junit"

        return None

    def has_coverage_flag(self, command: str) -> bool:
        """Check if command includes coverage flags.

        Detects common coverage flags:
        - --cov (pytest)
        - --coverage (generic)
        - -cover (go test)
        - -coverprofile (go test)

        Args:
            command: Test command string.

        Returns:
            True if any coverage flag detected, False otherwise.

        Example:
            >>> matcher = TestCommandMatcher()
            >>> matcher.has_coverage_flag("pytest --cov=src")
            True
            >>> matcher.has_coverage_flag("go test -cover")
            True
            >>> matcher.has_coverage_flag("npm test")
            False
        """
        if not command:
            return False

        return any(flag in command for flag in self.COVERAGE_FLAGS)
