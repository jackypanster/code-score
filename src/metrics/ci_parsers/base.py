"""Abstract base class for CI/CD configuration parsers.

This module defines the CIParser interface that all CI platform parsers
must implement. Provides common error handling and logging utilities.

Constitutional Compliance:
- Principle II (KISS): Simple abstract interface, minimal inheritance hierarchy
- Principle III (Transparency): Clear error logging and documentation
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from src.metrics.models.ci_config import TestStepInfo


class CIParser(ABC):
    """Abstract base class for CI configuration parsers.

    All platform-specific parsers (GitHub Actions, GitLab CI, CircleCI,
    Travis CI, Jenkins) must inherit from this class and implement the
    parse() method.

    The parser contract:
    - Returns List[TestStepInfo] if config is valid and contains test steps
    - Returns None if config is invalid/malformed (logs warning)
    - Raises FileNotFoundError if config file does not exist

    Error Handling Strategy:
    - Missing file: Raise FileNotFoundError (caller's responsibility)
    - Parse errors: Log warning and return None (graceful degradation)
    - Empty config: Return empty list [] (valid but no tests)

    Example:
        >>> class GitHubActionsParser(CIParser):
        ...     def parse(self, config_path: Path) -> Optional[List[TestStepInfo]]:
        ...         try:
        ...             # Parse GitHub Actions workflow
        ...             return test_steps
        ...         except yaml.YAMLError as e:
        ...             self._log_parse_error(e)
        ...             return None
    """

    def __init__(self):
        """Initialize parser with logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def parse(self, config_path: Path) -> Optional[List[TestStepInfo]]:
        """Parse a CI configuration file to extract test steps.

        This method must be implemented by all subclasses. It should:
        1. Check if config_path exists (raise FileNotFoundError if not)
        2. Parse the configuration file (YAML, Groovy, etc.)
        3. Extract test execution steps using TestCommandMatcher
        4. Build List[TestStepInfo] with job names, commands, frameworks
        5. Return None on parse errors (after logging warning)

        Args:
            config_path: Absolute path to CI configuration file.
                Examples:
                - .github/workflows/test.yml (GitHub Actions)
                - .gitlab-ci.yml (GitLab CI)
                - .circleci/config.yml (CircleCI)
                - .travis.yml (Travis CI)
                - Jenkinsfile (Jenkins)

        Returns:
            List[TestStepInfo] if config valid and test steps found.
                Empty list [] if config valid but no test steps.
            None if config is malformed/unparseable (logs warning).

        Raises:
            FileNotFoundError: If config_path does not exist.

        Side Effects:
            Logs parse errors at WARNING level via _log_parse_error().

        Performance:
            Must complete in <1 second per file (per FR-020).

        Example:
            >>> parser = GitHubActionsParser()
            >>> config_path = Path(".github/workflows/test.yml")
            >>> test_steps = parser.parse(config_path)
            >>> if test_steps:
            ...     print(f"Found {len(test_steps)} test steps")
        """
        pass

    def _log_parse_error(self, error: Exception, config_path: Optional[Path] = None) -> None:
        """Log a parse error at WARNING level.

        Helper method for consistent error logging across all parsers.
        Logs the error message and optionally the config file path.

        Args:
            error: The exception that occurred during parsing.
            config_path: Optional path to the config file being parsed.

        Side Effects:
            Logs at WARNING level (visible in standard logging mode).

        Example:
            >>> try:
            ...     yaml.safe_load(invalid_yaml)
            ... except yaml.YAMLError as e:
            ...     self._log_parse_error(e, config_path)
        """
        if config_path:
            self.logger.warning(
                f"Failed to parse CI config {config_path}: {type(error).__name__}: {error}"
            )
        else:
            self.logger.warning(
                f"Parse error: {type(error).__name__}: {error}"
            )
