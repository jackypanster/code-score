"""Data models for CI/CD configuration analysis (Phase 2).

This module defines the data structures for CI configuration analysis results,
integrating with Phase 1 static test infrastructure analysis.

Constitutional Compliance:
- Principle II (KISS): Simple dataclasses, no complex inheritance
- Principle III (Transparency): Clear field documentation and validation
"""

from dataclasses import dataclass
from typing import List, Optional

from src.metrics.models.test_infrastructure import TestInfrastructureResult


@dataclass
class ScoreBreakdown:
    """Documents how Phase 1 and Phase 2 scores combine with transparency.

    Attributes:
        phase1_contribution: Static analysis score (0-25 points).
        phase2_contribution: CI analysis score (0-13 points).
        raw_total: Sum before capping (may exceed 35).
        capped_total: Final score after min(raw_total, 35).
        truncated_points: Excess points discarded (raw_total - capped_total).

    Invariants:
        - raw_total == phase1_contribution + phase2_contribution
        - capped_total == min(raw_total, 35)
        - truncated_points == raw_total - capped_total
        - truncated_points >= 0

    Example:
        >>> breakdown = ScoreBreakdown(
        ...     phase1_contribution=25,
        ...     phase2_contribution=13,
        ...     raw_total=38,
        ...     capped_total=35,
        ...     truncated_points=3
        ... )
        >>> breakdown.capped_total
        35
    """

    phase1_contribution: int
    phase2_contribution: int
    raw_total: int
    capped_total: int
    truncated_points: int

    def __post_init__(self) -> None:
        """Validate score breakdown invariants.

        Raises:
            ValueError: If invariants are violated.
        """
        if not 0 <= self.phase1_contribution <= 25:
            raise ValueError(
                f"phase1_contribution must be in [0, 25], got {self.phase1_contribution}"
            )

        if not 0 <= self.phase2_contribution <= 13:
            raise ValueError(
                f"phase2_contribution must be in [0, 13], got {self.phase2_contribution}"
            )

        if self.raw_total != self.phase1_contribution + self.phase2_contribution:
            raise ValueError(
                f"raw_total must equal phase1 + phase2 "
                f"({self.phase1_contribution} + {self.phase2_contribution} = "
                f"{self.phase1_contribution + self.phase2_contribution}), "
                f"got {self.raw_total}"
            )

        if self.capped_total != min(self.raw_total, 35):
            raise ValueError(
                f"capped_total must equal min(raw_total, 35) = "
                f"{min(self.raw_total, 35)}, got {self.capped_total}"
            )

        if self.truncated_points != self.raw_total - self.capped_total:
            raise ValueError(
                f"truncated_points must equal raw_total - capped_total "
                f"({self.raw_total} - {self.capped_total} = "
                f"{self.raw_total - self.capped_total}), "
                f"got {self.truncated_points}"
            )

        if self.truncated_points < 0:
            raise ValueError(
                f"truncated_points must be >= 0, got {self.truncated_points}"
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for JSON output.
        """
        return {
            "phase1_contribution": self.phase1_contribution,
            "phase2_contribution": self.phase2_contribution,
            "raw_total": self.raw_total,
            "capped_total": self.capped_total,
            "truncated_points": self.truncated_points,
        }


@dataclass
class TestStepInfo:
    """Represents a single test execution step found in CI configuration.

    This is an intermediate data structure used during parsing.
    Not persisted in final JSON output.

    Attributes:
        job_name: CI job or step name (non-empty).
        command: Full command text (non-empty).
        framework: Inferred test framework ("pytest", "jest", "junit", "go_test", or None).
        has_coverage_flag: True if command includes coverage flags (--cov, --coverage).

    Example:
        >>> step = TestStepInfo(
        ...     job_name="unit-tests",
        ...     command="pytest --cov=src tests/unit",
        ...     framework="pytest",
        ...     has_coverage_flag=True
        ... )
        >>> step.framework
        'pytest'
    """

    job_name: str
    command: str
    framework: Optional[str]
    has_coverage_flag: bool

    def __post_init__(self) -> None:
        """Validate test step info constraints.

        Raises:
            ValueError: If job_name or command is empty, or framework is invalid.
        """
        if not self.job_name:
            raise ValueError("job_name must be non-empty")

        if not self.command:
            raise ValueError("command must be non-empty")

        valid_frameworks = {"pytest", "jest", "junit", "go_test"}
        if self.framework is not None and self.framework not in valid_frameworks:
            raise ValueError(
                f"framework must be None or one of {valid_frameworks}, "
                f"got {self.framework}"
            )


@dataclass
class CIConfigResult:
    """Represents CI/CD configuration analysis outcome for a repository.

    Attributes:
        platform: CI platform name or None if no CI detected.
            Valid values: "github_actions", "gitlab_ci", "circleci",
            "travis_ci", "jenkins", None.

        config_file_path: Relative path from repo root to CI config file.
            None if no CI configuration found.

        has_test_steps: True if at least one test command detected (FR-015).
            Awards 5 points if True.

        test_commands: List of detected test commands (may be empty).
            Examples: ["pytest --cov=src", "npm test"]

        has_coverage_upload: True if coverage tool detected (FR-016).
            Awards 5 points if True.

        coverage_tools: List of detected coverage tools (may be empty).
            Examples: ["codecov", "coveralls", "sonarqube"]

        test_job_count: Number of distinct test jobs detected.
            Awards 3 additional points if >= 2 (FR-017).

        calculated_score: Phase 2 score contribution (0-13 points).
            Scoring: 5 (test steps) + 5 (coverage) + 3 (multiple jobs) = max 13.

        parse_errors: List of parse error messages (empty if successful).
            Populated when CI config is malformed (FR-022).

    Invariants:
        - 0 <= calculated_score <= 13
        - platform must be None or in valid set
        - If has_test_steps, then test_commands is non-empty
        - If has_coverage_upload, then coverage_tools is non-empty

    Example (GitHub Actions with full score):
        >>> result = CIConfigResult(
        ...     platform="github_actions",
        ...     config_file_path=".github/workflows/test.yml",
        ...     has_test_steps=True,
        ...     test_commands=["pytest --cov=src", "npm test"],
        ...     has_coverage_upload=True,
        ...     coverage_tools=["codecov"],
        ...     test_job_count=2,
        ...     calculated_score=13,
        ...     parse_errors=[]
        ... )
        >>> result.calculated_score
        13

    Example (No CI configuration):
        >>> result = CIConfigResult(
        ...     platform=None,
        ...     config_file_path=None,
        ...     has_test_steps=False,
        ...     test_commands=[],
        ...     has_coverage_upload=False,
        ...     coverage_tools=[],
        ...     test_job_count=0,
        ...     calculated_score=0,
        ...     parse_errors=[]
        ... )
        >>> result.calculated_score
        0
    """

    platform: Optional[str]
    config_file_path: Optional[str]
    has_test_steps: bool
    test_commands: List[str]
    has_coverage_upload: bool
    coverage_tools: List[str]
    test_job_count: int
    calculated_score: int
    parse_errors: List[str]

    def __post_init__(self) -> None:
        """Validate CI config result constraints.

        Raises:
            ValueError: If any invariant is violated.
        """
        # Validate score range
        if not 0 <= self.calculated_score <= 13:
            raise ValueError(
                f"calculated_score must be in [0, 13] per FR-018, "
                f"got {self.calculated_score}"
            )

        # Validate platform
        valid_platforms = {
            "github_actions",
            "gitlab_ci",
            "circleci",
            "travis_ci",
            "jenkins",
        }
        if self.platform is not None and self.platform not in valid_platforms:
            raise ValueError(
                f"platform must be None or one of {valid_platforms}, "
                f"got {self.platform}"
            )

        # Validate test_job_count
        if self.test_job_count < 0:
            raise ValueError(
                f"test_job_count must be >= 0, got {self.test_job_count}"
            )

        # Validate consistency: has_test_steps implies non-empty test_commands
        if self.has_test_steps and not self.test_commands:
            raise ValueError(
                "has_test_steps is True but test_commands is empty"
            )

        # Validate consistency: has_coverage_upload implies non-empty coverage_tools
        if self.has_coverage_upload and not self.coverage_tools:
            raise ValueError(
                "has_coverage_upload is True but coverage_tools is empty"
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for JSON output.
        """
        return {
            "platform": self.platform,
            "config_file_path": self.config_file_path,
            "has_test_steps": self.has_test_steps,
            "test_commands": self.test_commands,
            "has_coverage_upload": self.has_coverage_upload,
            "coverage_tools": self.coverage_tools,
            "test_job_count": self.test_job_count,
            "calculated_score": self.calculated_score,
            "parse_errors": self.parse_errors,
        }


@dataclass
class TestAnalysis:
    """Top-level container aggregating Phase 1 and Phase 2 test analysis.

    This model combines static infrastructure analysis (Phase 1) with
    CI configuration analysis (Phase 2), applying score capping logic.

    Attributes:
        static_infrastructure: Phase 1 static file analysis result (COD-8).
        ci_configuration: Phase 2 CI config analysis result (COD-9).
            None if no CI configuration detected.
        combined_score: Final Testing dimension score (0-35 points).
            Calculated as min(Phase 1 + Phase 2, 35).
        score_breakdown: Detailed breakdown of phase contributions.

    Invariants:
        - combined_score == min(phase1_score + phase2_score, 35)
        - 0 <= combined_score <= 35
        - combined_score matches score_breakdown.capped_total

    Example (with score capping):
        >>> from src.metrics.models.test_infrastructure import TestInfrastructureResult
        >>> phase1 = TestInfrastructureResult(
        ...     test_files_detected=43,
        ...     test_config_detected=True,
        ...     coverage_config_detected=True,
        ...     test_file_ratio=0.35,
        ...     calculated_score=25,
        ...     inferred_framework="pytest"
        ... )
        >>> phase2 = CIConfigResult(
        ...     platform="github_actions",
        ...     config_file_path=".github/workflows/test.yml",
        ...     has_test_steps=True,
        ...     test_commands=["pytest --cov=src"],
        ...     has_coverage_upload=True,
        ...     coverage_tools=["codecov"],
        ...     test_job_count=2,
        ...     calculated_score=13,
        ...     parse_errors=[]
        ... )
        >>> breakdown = ScoreBreakdown(
        ...     phase1_contribution=25,
        ...     phase2_contribution=13,
        ...     raw_total=38,
        ...     capped_total=35,
        ...     truncated_points=3
        ... )
        >>> analysis = TestAnalysis(
        ...     static_infrastructure=phase1,
        ...     ci_configuration=phase2,
        ...     combined_score=35,
        ...     score_breakdown=breakdown
        ... )
        >>> analysis.combined_score
        35
    """

    static_infrastructure: TestInfrastructureResult
    ci_configuration: Optional[CIConfigResult]
    combined_score: int
    score_breakdown: ScoreBreakdown

    def __post_init__(self) -> None:
        """Validate test analysis invariants.

        Raises:
            ValueError: If any invariant is violated.
        """
        # Calculate expected combined score
        phase1_score = self.static_infrastructure.calculated_score
        phase2_score = (
            self.ci_configuration.calculated_score if self.ci_configuration else 0
        )
        expected_combined = min(phase1_score + phase2_score, 35)

        # Validate combined score
        if self.combined_score != expected_combined:
            raise ValueError(
                f"combined_score must equal min(phase1 + phase2, 35) = "
                f"min({phase1_score} + {phase2_score}, 35) = {expected_combined}, "
                f"got {self.combined_score}"
            )

        if not 0 <= self.combined_score <= 35:
            raise ValueError(
                f"combined_score must be in [0, 35], got {self.combined_score}"
            )

        # Validate consistency with score_breakdown
        if self.combined_score != self.score_breakdown.capped_total:
            raise ValueError(
                f"combined_score ({self.combined_score}) must match "
                f"score_breakdown.capped_total ({self.score_breakdown.capped_total})"
            )

        # Validate score_breakdown matches actual contributions
        if self.score_breakdown.phase1_contribution != phase1_score:
            raise ValueError(
                f"score_breakdown.phase1_contribution "
                f"({self.score_breakdown.phase1_contribution}) must match "
                f"static_infrastructure.calculated_score ({phase1_score})"
            )

        if self.score_breakdown.phase2_contribution != phase2_score:
            raise ValueError(
                f"score_breakdown.phase2_contribution "
                f"({self.score_breakdown.phase2_contribution}) must match "
                f"ci_configuration.calculated_score ({phase2_score})"
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for JSON output.
        """
        return {
            "static_infrastructure": self.static_infrastructure.to_dict(),
            "ci_configuration": (
                self.ci_configuration.to_dict() if self.ci_configuration else None
            ),
            "combined_score": self.combined_score,
            "score_breakdown": self.score_breakdown.to_dict(),
        }
