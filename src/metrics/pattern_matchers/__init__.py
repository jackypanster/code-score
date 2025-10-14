"""Pattern matching utilities for CI/CD configuration analysis.

This package provides pattern matchers for detecting test commands and
coverage tools in CI configuration files.

Constitutional Compliance:
- Principle II (KISS): Simple substring matching, no regex overhead
- Principle III (Transparency): Clear pattern lists and matching logic
"""

from src.metrics.pattern_matchers.coverage_tool_matcher import CoverageToolMatcher
from src.metrics.pattern_matchers.test_command_matcher import TestCommandMatcher

__all__ = ["TestCommandMatcher", "CoverageToolMatcher"]
