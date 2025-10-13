"""Data models for static test infrastructure analysis.

This module defines the data structures for representing the results of
static test infrastructure analysis without code execution.

Constitutional Compliance:
- Principle II (KISS): Simple dataclass, no complex inheritance
- Principle III (Transparency): Clear field documentation
"""

from dataclasses import dataclass


@dataclass
class TestInfrastructureResult:
    """Result of static test infrastructure analysis.

    This dataclass represents the outcome of analyzing a repository's test
    infrastructure without executing any tests. It feeds into the Testing
    dimension evaluation and populates metrics.testing.test_execution section.

    Attributes:
        test_files_detected: Number of test files found through static analysis (FR-017).
            Must be >= 0. This is the primary indicator of test presence.

        test_config_detected: Whether valid test framework configuration was found (FR-005).
            True if configuration file with required sections exists and parses successfully.

        coverage_config_detected: Whether valid coverage configuration was found (FR-006).
            True if coverage config file with required sections exists and parses successfully.

        test_file_ratio: Ratio of test files to non-test source files (FR-010).
            Calculated as: test_count / (source_count - test_count - docs - configs).
            Range: [0.0, 1.0]. Higher ratios indicate better test coverage.

        calculated_score: Final Testing dimension score from static analysis (0-25 points).
            Scoring breakdown per FR-007 through FR-013:
            - 5 points: test files present
            - 5 points: test config detected
            - 5 points: coverage config detected
            - 5 points: ratio 10-30%
            - 10 points: ratio >30%
            Capped at 25 points per FR-013 (71% of full 35 points).

        inferred_framework: Name of detected test framework (e.g., "pytest", "jest", "go test", "junit").
            Set to "none" if no test infrastructure detected.

    Example:
        >>> result = TestInfrastructureResult(
        ...     test_files_detected=15,
        ...     test_config_detected=True,
        ...     coverage_config_detected=False,
        ...     test_file_ratio=0.25,
        ...     calculated_score=20,
        ...     inferred_framework="pytest"
        ... )
        >>> result.calculated_score
        20
    """

    test_files_detected: int
    test_config_detected: bool
    coverage_config_detected: bool
    test_file_ratio: float
    calculated_score: int  # 0-25, capped per FR-013
    inferred_framework: str

    def __post_init__(self) -> None:
        """Validate field constraints after initialization.

        Raises:
            ValueError: If any field violates its constraints.
        """
        if self.test_files_detected < 0:
            raise ValueError(f"test_files_detected must be >= 0, got {self.test_files_detected}")

        if not 0.0 <= self.test_file_ratio <= 1.0:
            raise ValueError(f"test_file_ratio must be in [0.0, 1.0], got {self.test_file_ratio}")

        if not 0 <= self.calculated_score <= 25:
            raise ValueError(
                f"calculated_score must be in [0, 25] per FR-013, got {self.calculated_score}"
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for JSON output.
        """
        return {
            "test_files_detected": self.test_files_detected,
            "test_config_detected": self.test_config_detected,
            "coverage_config_detected": self.coverage_config_detected,
            "test_file_ratio": self.test_file_ratio,
            "calculated_score": self.calculated_score,
            "inferred_framework": self.inferred_framework,
        }
