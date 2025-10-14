# Phase 1: Data Model Design

**Feature**: CI/CD Configuration Analysis for Test Evidence
**Date**: 2025-10-13
**Status**: Complete

## Overview
This document defines the data models for CI/CD configuration analysis (COD-9 Phase 2). All models are Python dataclasses with JSON schema contracts for validation. Models integrate with existing Phase 1 (`TestInfrastructureResult`) via the independent parallel structure pattern (per Clarification Q3).

---

## Core Entities

### 1. TestAnalysis (Top-Level Container)

**Purpose**: Aggregates Phase 1 (static) and Phase 2 (CI) analysis results with explicit score calculation

**Location**: `src/metrics/models/ci_config.py`

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `static_infrastructure` | `TestInfrastructureResult` | Yes | Phase 1 static file analysis (COD-8) | Existing model validation |
| `ci_configuration` | `Optional[CIConfigResult]` | No | Phase 2 CI config analysis (None if no CI detected) | CIConfigResult validation when present |
| `combined_score` | `int` | Yes | Final Testing dimension score (0-35) | Must equal `min(P1 + P2, 35)` |
| `score_breakdown` | `ScoreBreakdown` | Yes | Detailed phase contributions | ScoreBreakdown validation |

**Relationships**:
- Contains `TestInfrastructureResult` (Phase 1, existing model)
- Contains `CIConfigResult` (Phase 2, new model)
- Contains `ScoreBreakdown` (new supporting model)

**Invariants**:
```python
assert test_analysis.combined_score == min(
    test_analysis.static_infrastructure.calculated_score +
    (test_analysis.ci_configuration.calculated_score if test_analysis.ci_configuration else 0),
    35
)
assert 0 <= test_analysis.combined_score <= 35
```

**Example**:
```python
TestAnalysis(
    static_infrastructure=TestInfrastructureResult(
        test_files_detected=43,
        test_config_detected=True,
        calculated_score=25
    ),
    ci_configuration=CIConfigResult(
        platform="github_actions",
        has_test_steps=True,
        calculated_score=13
    ),
    combined_score=35,  # min(25 + 13, 35) = 35
    score_breakdown=ScoreBreakdown(
        phase1_contribution=25,
        phase2_contribution=13,
        raw_total=38,
        capped_total=35,
        truncated_points=3
    )
)
```

---

### 2. ScoreBreakdown (Supporting Entity)

**Purpose**: Documents how Phase 1 and Phase 2 scores combine with transparency

**Location**: `src/metrics/models/ci_config.py`

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `phase1_contribution` | `int` | Yes | Static analysis score (0-25) | `0 <= value <= 25` |
| `phase2_contribution` | `int` | Yes | CI analysis score (0-13) | `0 <= value <= 13` |
| `raw_total` | `int` | Yes | Sum before capping (may exceed 35) | `phase1 + phase2` |
| `capped_total` | `int` | Yes | Final score after `min(raw_total, 35)` | `0 <= value <= 35` |
| `truncated_points` | `int` | Yes | Excess points discarded | `raw_total - capped_total` |

**Invariants**:
```python
assert score_breakdown.raw_total == score_breakdown.phase1_contribution + score_breakdown.phase2_contribution
assert score_breakdown.capped_total == min(score_breakdown.raw_total, 35)
assert score_breakdown.truncated_points == score_breakdown.raw_total - score_breakdown.capped_total
assert score_breakdown.truncated_points >= 0
```

**Example**:
```python
ScoreBreakdown(
    phase1_contribution=25,
    phase2_contribution=13,
    raw_total=38,        # 25 + 13
    capped_total=35,     # min(38, 35)
    truncated_points=3   # 38 - 35
)
```

---

### 3. CIConfigResult (Phase 2 Analysis Result)

**Purpose**: Represents CI/CD configuration analysis outcome for a single repository

**Location**: `src/metrics/models/ci_config.py`

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `platform` | `Optional[str]` | Yes | CI platform name | Must be None or one of: `"github_actions"`, `"gitlab_ci"`, `"circleci"`, `"travis_ci"`, `"jenkins"` |
| `config_file_path` | `Optional[str]` | No | Relative path from repo root | String or None |
| `has_test_steps` | `bool` | Yes | At least one test command detected (FR-015) | Boolean |
| `test_commands` | `List[str]` | Yes | Detected test commands | List of strings (may be empty) |
| `has_coverage_upload` | `bool` | Yes | Coverage tool detected (FR-016) | Boolean |
| `coverage_tools` | `List[str]` | Yes | Detected tools (codecov, coveralls, etc.) | List of strings (may be empty) |
| `test_job_count` | `int` | Yes | Number of distinct test jobs (FR-017) | `>= 0` |
| `calculated_score` | `int` | Yes | Phase 2 score contribution (0-13) | `0 <= value <= 13` |
| `parse_errors` | `List[str]` | Yes | Warnings from malformed configs | List of strings (empty if successful) |

**Relationships**:
- Contained by `TestAnalysis`
- Contains list of `TestStepInfo` (not stored, used during analysis)

**Scoring Logic** (FR-015 to FR-018):
```python
score = 0
if ci_config.has_test_steps:
    score += 5
if ci_config.has_coverage_upload:
    score += 5
if ci_config.test_job_count >= 2:
    score += 3
ci_config.calculated_score = min(score, 13)
```

**Invariants**:
```python
assert ci_config.calculated_score >= 0 and ci_config.calculated_score <= 13
if ci_config.platform is not None:
    assert ci_config.platform in ["github_actions", "gitlab_ci", "circleci", "travis_ci", "jenkins"]
if ci_config.has_test_steps:
    assert len(ci_config.test_commands) > 0
if ci_config.has_coverage_upload:
    assert len(ci_config.coverage_tools) > 0
```

**Example (GitHub Actions with full score)**:
```python
CIConfigResult(
    platform="github_actions",
    config_file_path=".github/workflows/test.yml",
    has_test_steps=True,
    test_commands=["pytest --cov=src", "npm test"],
    has_coverage_upload=True,
    coverage_tools=["codecov"],
    test_job_count=2,  # unit-tests, integration-tests
    calculated_score=13,  # 5 + 5 + 3
    parse_errors=[]
)
```

**Example (No CI configuration)**:
```python
CIConfigResult(
    platform=None,
    config_file_path=None,
    has_test_steps=False,
    test_commands=[],
    has_coverage_upload=False,
    coverage_tools=[],
    test_job_count=0,
    calculated_score=0,
    parse_errors=[]
)
```

---

### 4. TestStepInfo (Supporting Entity)

**Purpose**: Represents a single test execution step found in CI configuration

**Location**: `src/metrics/models/ci_config.py`

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `job_name` | `str` | Yes | CI job or step name | Non-empty string |
| `command` | `str` | Yes | Full command text | Non-empty string |
| `framework` | `Optional[str]` | Yes | Inferred framework | Must be None or one of: `"pytest"`, `"jest"`, `"junit"`, `"go_test"` |
| `has_coverage_flag` | `bool` | Yes | Command includes coverage flags (`--cov`, `--coverage`) | Boolean |

**Usage**: Intermediate data structure during parsing, not persisted in final JSON output

**Example**:
```python
TestStepInfo(
    job_name="unit-tests",
    command="pytest --cov=src tests/unit",
    framework="pytest",
    has_coverage_flag=True
)
```

---

## Data Flow

```
Repository (cloned)
    ↓
TestInfrastructureAnalyzer.analyze()
    ↓
    ├─→ Phase 1: Static file detection
    │   └─→ TestInfrastructureResult (test_files_detected, calculated_score)
    │
    └─→ Phase 2: CI config analysis
        └─→ CIConfigAnalyzer.analyze_ci_config()
            ├─→ Detect CI platform (GitHub Actions, GitLab CI, etc.)
            ├─→ Parse config file (GitHubActionsParser, etc.)
            ├─→ Extract test steps (TestCommandMatcher)
            ├─→ Detect coverage tools (CoverageToolMatcher)
            └─→ CIConfigResult (platform, has_test_steps, calculated_score)
    ↓
Aggregation Layer
    ├─→ Calculate combined_score = min(Phase1 + Phase2, 35)
    ├─→ Generate score_breakdown
    └─→ TestAnalysis (contains Phase 1 + Phase 2 + aggregation)
    ↓
JSON Output (submission.json)
```

---

## JSON Schema Mapping

### TestAnalysis Output Structure
```json
{
  "test_analysis": {
    "static_infrastructure": {
      "test_files_detected": 43,
      "test_config_detected": true,
      "coverage_config_detected": false,
      "test_file_ratio": 0.107,
      "calculated_score": 25
    },
    "ci_configuration": {
      "platform": "github_actions",
      "config_file_path": ".github/workflows/test.yml",
      "has_test_steps": true,
      "test_commands": ["pytest --cov=src", "npm test"],
      "has_coverage_upload": true,
      "coverage_tools": ["codecov"],
      "test_job_count": 2,
      "calculated_score": 13,
      "parse_errors": []
    },
    "combined_score": 35,
    "score_breakdown": {
      "phase1_contribution": 25,
      "phase2_contribution": 13,
      "raw_total": 38,
      "capped_total": 35,
      "truncated_points": 3
    }
  }
}
```

---

## Validation Rules Summary

| Rule ID | Validation | Enforced By |
|---------|------------|-------------|
| VR-001 | `CIConfigResult.calculated_score` in [0, 13] | Scoring logic |
| VR-002 | `TestAnalysis.combined_score` == min(P1 + P2, 35) | Aggregation logic |
| VR-003 | `ScoreBreakdown.capped_total` <= 35 | Aggregation logic |
| VR-004 | `CIConfigResult.platform` in valid set or None | JSON schema + parser |
| VR-005 | `TestStepInfo.framework` in valid set or None | Pattern matching |
| VR-006 | If `has_test_steps` then `test_commands` non-empty | Scoring logic |
| VR-007 | If `has_coverage_upload` then `coverage_tools` non-empty | Scoring logic |
| VR-008 | `score_breakdown.truncated_points` >= 0 | Mathematical invariant |

---

## State Transitions

**No state transitions** - All models are immutable value objects representing analysis results at a point in time.

---

## Dependencies

| Model | Depends On | Relationship |
|-------|------------|--------------|
| TestAnalysis | TestInfrastructureResult, CIConfigResult, ScoreBreakdown | Composition |
| ScoreBreakdown | None | Standalone |
| CIConfigResult | None (uses TestStepInfo during analysis only) | Composition (transient) |
| TestStepInfo | None | Standalone |

---

## Implementation Notes

### Python Dataclass Definition
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ScoreBreakdown:
    phase1_contribution: int
    phase2_contribution: int
    raw_total: int
    capped_total: int
    truncated_points: int

    def __post_init__(self):
        assert self.raw_total == self.phase1_contribution + self.phase2_contribution
        assert self.capped_total == min(self.raw_total, 35)
        assert self.truncated_points == self.raw_total - self.capped_total

@dataclass
class CIConfigResult:
    platform: Optional[str]
    config_file_path: Optional[str]
    has_test_steps: bool
    test_commands: List[str]
    has_coverage_upload: bool
    coverage_tools: List[str]
    test_job_count: int
    calculated_score: int
    parse_errors: List[str]

    def __post_init__(self):
        assert 0 <= self.calculated_score <= 13
        if self.platform is not None:
            valid_platforms = {"github_actions", "gitlab_ci", "circleci", "travis_ci", "jenkins"}
            assert self.platform in valid_platforms

@dataclass
class TestAnalysis:
    static_infrastructure: TestInfrastructureResult
    ci_configuration: Optional[CIConfigResult]
    combined_score: int
    score_breakdown: ScoreBreakdown

    def __post_init__(self):
        phase1_score = self.static_infrastructure.calculated_score
        phase2_score = self.ci_configuration.calculated_score if self.ci_configuration else 0
        expected_combined = min(phase1_score + phase2_score, 35)
        assert self.combined_score == expected_combined
```

---

**Phase 1 Data Model Status**: ✅ Complete - All entities defined, validated, and ready for implementation.
