"""Pattern matcher for coverage tools in CI/CD configurations.

This module provides CoverageToolMatcher for detecting coverage upload and
reporting tools (Codecov, Coveralls, SonarQube) in CI configuration steps
using simple substring matching (per research.md Decision 4).

Constitutional Compliance:
- Principle II (KISS): Substring matching without regex overhead
- Principle III (Transparency): Explicit tool patterns and matching logic
"""

from typing import List


class CoverageToolMatcher:
    """Matcher for coverage tools in CI configuration steps.

    Detects three major coverage tools using substring matching:
    - Codecov: codecov/codecov-action, codecov upload, codecov command
    - Coveralls: coveralls command, python-coveralls
    - SonarQube: sonar-scanner, sonarqube keyword

    Returns standardized tool names per CIConfigResult.coverage_tools field.

    Example:
        >>> matcher = CoverageToolMatcher()
        >>> steps = ["pytest --cov=src", "codecov upload"]
        >>> matcher.detect_coverage_tools(steps)
        ['codecov']
        >>> matcher.has_coverage_upload(steps)
        True
    """

    def detect_coverage_tools(self, steps: List[str]) -> List[str]:
        """Detect coverage tools from CI steps.

        Scans all steps and returns list of detected coverage tools.
        Returns unique tool names (no duplicates) in standardized format:
        - "codecov": Codecov upload detected
        - "coveralls": Coveralls integration detected
        - "sonarqube": SonarQube scan detected

        Args:
            steps: List of CI step commands (e.g., from workflow YAML).

        Returns:
            List of unique coverage tool names. Empty list if none detected.

        Example:
            >>> matcher = CoverageToolMatcher()
            >>> steps = [
            ...     "pytest --cov=src tests/",
            ...     "codecov upload",
            ...     "coveralls"
            ... ]
            >>> tools = matcher.detect_coverage_tools(steps)
            >>> sorted(tools)
            ['codecov', 'coveralls']
        """
        if not steps:
            return []

        detected_tools = []

        for step in steps:
            if not step:
                continue

            # Check each tool type (maintain order for consistency)
            if self._match_codecov(step) and "codecov" not in detected_tools:
                detected_tools.append("codecov")

            if self._match_coveralls(step) and "coveralls" not in detected_tools:
                detected_tools.append("coveralls")

            if self._match_sonarqube(step) and "sonarqube" not in detected_tools:
                detected_tools.append("sonarqube")

        return detected_tools

    def has_coverage_upload(self, steps: List[str]) -> bool:
        """Check if any coverage tool detected in steps.

        Convenience method for boolean check. Equivalent to
        `len(detect_coverage_tools(steps)) > 0`.

        Args:
            steps: List of CI step commands.

        Returns:
            True if at least one coverage tool detected, False otherwise.

        Example:
            >>> matcher = CoverageToolMatcher()
            >>> matcher.has_coverage_upload(["pytest tests/"])
            False
            >>> matcher.has_coverage_upload(["pytest tests/", "codecov"])
            True
        """
        return len(self.detect_coverage_tools(steps)) > 0

    def _match_codecov(self, step: str) -> bool:
        """Match Codecov patterns in CI step.

        Detects Codecov as substring (per research.md - substring matching).
        Matches patterns like:
        - codecov/codecov-action (GitHub Actions)
        - codecov upload (command)
        - codecov (simple command)
        - run-codecov-upload (substring)
        - codecov.io (bash script)

        Case-insensitive matching to handle varying CI styles.

        Args:
            step: Single CI step command string.

        Returns:
            True if Codecov pattern detected, False otherwise.

        Example:
            >>> matcher = CoverageToolMatcher()
            >>> matcher._match_codecov("uses: codecov/codecov-action@v3")
            True
            >>> matcher._match_codecov("codecov upload")
            True
            >>> matcher._match_codecov("run-codecov-upload")
            True
            >>> matcher._match_codecov("bash <(curl -s https://codecov.io/bash)")
            True
        """
        if not step:
            return False

        step_lower = step.lower()

        # Simple substring matching per research.md Decision 4
        return "codecov" in step_lower

    def _match_coveralls(self, step: str) -> bool:
        """Match Coveralls patterns in CI step.

        Detects Coveralls patterns:
        - coveralls (command)
        - python-coveralls (Python package)

        Case-insensitive matching to handle varying CI styles.

        Args:
            step: Single CI step command string.

        Returns:
            True if Coveralls pattern detected, False otherwise.

        Example:
            >>> matcher = CoverageToolMatcher()
            >>> matcher._match_coveralls("coveralls")
            True
            >>> matcher._match_coveralls("python-coveralls")
            True
            >>> matcher._match_coveralls("coveralls --service=github-actions")
            True
        """
        if not step:
            return False

        step_lower = step.lower()

        # Match coveralls keyword (substring matching)
        return "coveralls" in step_lower

    def _match_sonarqube(self, step: str) -> bool:
        """Match SonarQube patterns in CI step.

        Detects SonarQube patterns:
        - sonar-scanner (command)
        - sonarqube (Maven/Gradle keyword)

        Case-insensitive matching to handle varying CI styles.

        Args:
            step: Single CI step command string.

        Returns:
            True if SonarQube pattern detected, False otherwise.

        Example:
            >>> matcher = CoverageToolMatcher()
            >>> matcher._match_sonarqube("sonar-scanner")
            True
            >>> matcher._match_sonarqube("mvn sonarqube:sonar")
            True
            >>> matcher._match_sonarqube("sonar-scanner -Dsonar.projectKey=myproject")
            True
        """
        if not step:
            return False

        step_lower = step.lower()

        # Match sonar-scanner or sonarqube keyword
        return "sonar-scanner" in step_lower or "sonarqube" in step_lower
