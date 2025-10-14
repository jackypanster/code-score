
# Implementation Plan: CI/CD Configuration Analysis for Test Evidence

**Branch**: `005-1-phase-2` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/zhibinpan/workspace/code-score/specs/005-1-phase-2/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded: CI/CD configuration analysis specification
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ Project Type: Single Python project (existing codebase)
   → ✅ Structure Decision: Extend existing src/metrics architecture
3. Fill Constitution Check section
   → ✅ Evaluating UV dependency management, KISS principle, transparency
4. Evaluate Constitution Check section
   → ✅ No violations detected
   → Update Progress Tracking: Initial Constitution Check ✅
5. Execute Phase 0 → research.md
   → In progress
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → Pending
7. Re-evaluate Constitution Check section
   → Pending
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → Pending
9. STOP - Ready for /tasks command
   → Pending
```

**IMPORTANT**: The /plan command STOPS at step 9. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
CI/CD Configuration Analysis extends the existing Code Score metrics collection pipeline (COD-8 Phase 1 static analysis) with Phase 2 capabilities to parse CI/CD configuration files (GitHub Actions, GitLab CI, CircleCI, Travis CI, Jenkins), extract test execution and coverage upload evidence, and contribute 0-13 additional points to the Testing dimension score. The system uses pure YAML/JSON parsing without code execution, maintains <1 second performance, and structures results in an independent `ci_configuration` field alongside Phase 1's `static_infrastructure` for clean architectural separation.

**Technical Approach**: Extend TestInfrastructureAnalyzer with CIConfigAnalyzer module using platform-specific parsers (PyYAML for GitHub Actions/GitLab CI/Travis CI, JSON for CircleCI, custom parser for Jenkinsfile Groovy DSL), pattern-based command matching for test steps (pytest, npm test, go test, etc.) and coverage tools (Codecov, Coveralls, SonarQube), with configurable logging (minimal/standard/detailed) and graceful error handling for malformed configurations.

## Technical Context
**Language/Version**: Python 3.11
**Primary Dependencies**: PyYAML (YAML parsing), existing Code Score models (TestInfrastructureResult, MetricsCollection)
**Storage**: JSON output files (extends existing submission.json schema with test_analysis.ci_configuration field)
**Testing**: pytest (unit tests for parsers, contract tests for JSON schema, integration tests with sample CI configs)
**Target Platform**: Linux/macOS (same as existing Code Score CLI)
**Project Type**: Single Python project (extends existing src/metrics/ architecture)
**Performance Goals**: <1 second CI configuration analysis per repository (FR-020)
**Constraints**: Zero code execution (FR-021), must handle parse errors gracefully (FR-022), cap Phase 1 + Phase 2 at 35 points (FR-019)
**Scale/Scope**: 5 CI platforms (GitHub Actions, GitLab CI, CircleCI, Travis CI, Jenkins), 8 test command patterns, 4 coverage tool patterns

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. UV-Based Dependency Management
- ✅ **PASS**: PyYAML will be added via `uv add pyyaml`
- ✅ **PASS**: No new package managers introduced
- ✅ **PASS**: Development dependencies (pytest fixtures) managed via `uv add --dev`

### II. KISS Principle
- ✅ **PASS**: Platform-specific parsers are simple classes with single responsibility (parse YAML/JSON)
- ✅ **PASS**: Pattern matching uses straightforward regex/substring checks, no complex NLP
- ✅ **PASS**: Error handling: immediate exception on critical errors (file not found, invalid YAML root structure), graceful None return on parse errors (malformed YAML content) per FR-022
- ✅ **PASS**: No premature abstractions - each CI platform has dedicated parser, no complex inheritance hierarchy
- ✅ **PASS**: Fail-fast: parse errors logged and return empty result (0 points), pipeline continues with Phase 1 score

### III. Transparent Change Communication
- ✅ **PASS**: Implementation plan documents architectural decisions (independent ci_configuration field, simple truncation scoring)
- ✅ **PASS**: Clarifications session recorded 3 key decisions with rationale
- ✅ **PASS**: Commit messages will follow existing convention: "feat: add CI config analysis (COD-9 Phase 2)"

**Constitution Check Result**: ✅ PASS - No violations, all principles satisfied

## Project Structure

### Documentation (this feature)
```
specs/005-1-phase-2/
├── spec.md              # Business requirements (completed)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   └── ci_config_result_schema.json
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/metrics/
├── models/
│   ├── test_infrastructure.py     # Existing (COD-8, contains TestInfrastructureResult)
│   └── ci_config.py               # NEW: CIConfigResult, TestStepInfo, TestAnalysis models
├── ci_parsers/                    # NEW module
│   ├── __init__.py
│   ├── base.py                    # Abstract CIParser interface
│   ├── github_actions_parser.py   # Parses .github/workflows/*.yml
│   ├── gitlab_ci_parser.py        # Parses .gitlab-ci.yml
│   ├── circleci_parser.py         # Parses .circleci/config.yml
│   ├── travis_parser.py           # Parses .travis.yml
│   └── jenkins_parser.py          # Parses Jenkinsfile (Groovy DSL)
├── pattern_matchers/              # NEW module
│   ├── __init__.py
│   ├── test_command_matcher.py    # Matches pytest, npm test, go test, etc.
│   └── coverage_tool_matcher.py   # Matches codecov, coveralls, sonarqube
├── ci_config_analyzer.py          # NEW: Main analyzer (orchestrates parsers)
├── test_infrastructure_analyzer.py # Existing (COD-8, will call CIConfigAnalyzer)
└── tool_runners/
    ├── python_tools.py            # Modified: integrate CI analysis results
    ├── javascript_tools.py        # Modified: integrate CI analysis results
    ├── golang_tools.py            # Modified: integrate CI analysis results
    └── java_tools.py              # Modified: integrate CI analysis results

tests/
├── contract/
│   └── test_ci_config_result_schema.py  # NEW: Validate JSON schema compliance
├── unit/
│   ├── test_github_actions_parser.py    # NEW: Test GitHub Actions parser
│   ├── test_gitlab_ci_parser.py         # NEW: Test GitLab CI parser
│   ├── test_circleci_parser.py          # NEW: Test CircleCI parser
│   ├── test_travis_parser.py            # NEW: Test Travis parser
│   ├── test_jenkins_parser.py           # NEW: Test Jenkins parser
│   ├── test_test_command_matcher.py     # NEW: Test command pattern matching
│   ├── test_coverage_tool_matcher.py    # NEW: Test coverage tool detection
│   └── test_ci_config_analyzer.py       # NEW: Test main analyzer orchestration
└── integration/
    └── test_ci_analysis_workflow.py     # NEW: End-to-end CI analysis with sample repos
```

**Structure Decision**: Extends existing single Python project structure (src/metrics/) with new ci_parsers/ and pattern_matchers/ modules. Follows established Code Score architecture patterns: models in src/metrics/models/, analyzers at src/metrics/ root, unit tests mirror src/ structure, integration tests validate end-to-end workflows.

## Phase 0: Outline & Research

### Research Tasks

1. **YAML parsing library selection**
   - Decision: PyYAML (already in project dependencies)
   - Rationale: Mature, well-tested, handles GitHub Actions/GitLab CI/Travis CI YAML formats
   - Alternatives considered: ruamel.yaml (more features but overkill for read-only parsing)

2. **Groovy DSL parsing strategy for Jenkinsfile**
   - Decision: Regular expression extraction of test command patterns (no full Groovy parser)
   - Rationale: Jenkinsfile syntax highly variable, full parsing requires complex Groovy interpreter; MVP focuses on common patterns (sh 'pytest', sh 'mvn test')
   - Alternatives considered: pyparsing Groovy grammar (rejected: excessive complexity for MVP)

3. **CircleCI JSON vs YAML format handling**
   - Decision: Parse as YAML (CircleCI 2.0+ uses YAML, JSON is legacy 1.0)
   - Rationale: config.yml is standard filename, legacy JSON format rare in modern projects
   - Alternatives considered: Dual parser (rejected: adds complexity, limited value)

4. **Test command pattern matching strategy**
   - Decision: Hardcoded pattern list with substring matching (FR-007 explicitly lists commands)
   - Rationale: Finite, well-defined command set; regex overhead unnecessary for exact substring matches
   - Alternatives considered: Regex compilation (rejected: premature optimization, substring is O(n) sufficient)

5. **Logging level implementation approach**
   - Decision: Python standard library logging with configurable level (DEBUG=detailed, INFO=standard, WARNING=minimal)
   - Rationale: Aligns with existing Code Score logging patterns, no new dependencies
   - Alternatives considered: Custom logging facade (rejected: KISS violation, standard logging sufficient)

6. **Multi-platform score aggregation strategy (Edge Case)**
   - Decision: Take max score across all detected CI platforms (per Edge Case clarification)
   - Rationale: Project quality is best represented by most comprehensive CI setup
   - Alternatives considered: Sum all platforms (rejected: inflates score unfairly), average (rejected: penalizes comprehensive setups)

7. **Phase 1/Phase 2 data structure integration**
   - Decision: Independent parallel structure with top-level TestAnalysis container (per Clarification Q3)
   - Rationale: Clean separation allows Phase 1/Phase 2 independent evolution, no breaking changes to existing TestInfrastructureResult model
   - Alternatives considered: Extend TestInfrastructureResult with ci_config field (rejected: couples phases, complicates versioning)

8. **Error handling for malformed CI configs**
   - Decision: Log warning + return CIConfigResult with 0 score + all detection flags False (per FR-022, Edge Case)
   - Rationale: Fail-safe rather than fail-fast for parsing errors (not critical path), preserves Phase 1 score
   - Alternatives considered: Raise exception (rejected: fails entire analysis), silent skip (rejected: no observability)

**Output**: research.md (generated below)

## Phase 1: Design & Contracts

### Data Model Design (data-model.md)

**Core Entities**:

1. **TestAnalysis** (NEW top-level container per Clarification Q3)
   - `static_infrastructure: TestInfrastructureResult` - Phase 1 results (existing model)
   - `ci_configuration: Optional[CIConfigResult]` - Phase 2 results (None if no CI detected)
   - `combined_score: int` - Final Testing dimension score (0-35)
   - `score_breakdown: ScoreBreakdown` - Detailed phase contributions

2. **ScoreBreakdown** (NEW supporting entity)
   - `phase1_contribution: int` - Static analysis score (0-25)
   - `phase2_contribution: int` - CI analysis score (0-13)
   - `raw_total: int` - Sum before capping (may exceed 35)
   - `capped_total: int` - Final score after min(raw_total, 35)
   - `truncated_points: int` - Excess points discarded (raw_total - capped_total)

3. **CIConfigResult** (NEW per FR-023 to FR-026)
   - `platform: Optional[str]` - "github_actions" | "gitlab_ci" | "circleci" | "travis_ci" | "jenkins" | None
   - `config_file_path: Optional[str]` - Relative path from repo root
   - `has_test_steps: bool` - At least one test command detected (FR-015)
   - `test_commands: List[str]` - Detected test commands (e.g., ["pytest --cov=src", "npm test"])
   - `has_coverage_upload: bool` - Coverage tool detected (FR-016)
   - `coverage_tools: List[str]` - Detected tools (e.g., ["codecov", "coveralls"])
   - `test_job_count: int` - Number of distinct test jobs (FR-017)
   - `calculated_score: int` - Phase 2 score contribution (0-13, per FR-015 to FR-018)
   - `parse_errors: List[str]` - Warnings from malformed configs (empty if successful)

4. **TestStepInfo** (NEW supporting entity)
   - `job_name: str` - CI job or step name
   - `command: str` - Full command text
   - `framework: Optional[str]` - Inferred framework ("pytest" | "jest" | "junit" | "go_test" | None)
   - `has_coverage_flag: bool` - Command includes coverage flags (--cov, --coverage)

**Validation Rules**:
- `CIConfigResult.calculated_score` MUST be in range [0, 13] (enforced by scoring logic)
- `TestAnalysis.combined_score` MUST equal min(phase1 + phase2, 35) (FR-019)
- `ScoreBreakdown.capped_total` MUST NOT exceed 35
- `CIConfigResult.platform` MUST be None or one of 5 valid platform names
- `TestStepInfo.framework` MUST be None or match known framework names

**State Transitions**: N/A (immutable data models, no lifecycle)

### API Contracts (contracts/)

**Internal API Contract** (Python function signatures, not REST endpoints):

```python
# src/metrics/ci_config_analyzer.py
class CIConfigAnalyzer:
    def analyze_ci_config(self, repo_path: Path) -> CIConfigResult:
        """
        Analyze CI/CD configuration files in a repository.

        Args:
            repo_path: Absolute path to cloned repository root

        Returns:
            CIConfigResult with detected platform, test steps, coverage tools, and calculated score

        Raises:
            ValueError: If repo_path does not exist or is not a directory

        Performance:
            Must complete in <1 second per FR-020

        Side Effects:
            Logs parse warnings at standard level (INFO)
            Logs detailed parse steps at DEBUG level
        """
```

```python
# src/metrics/ci_parsers/base.py
class CIParser(ABC):
    @abstractmethod
    def parse(self, config_path: Path) -> Optional[List[TestStepInfo]]:
        """
        Parse a CI configuration file to extract test steps.

        Args:
            config_path: Absolute path to CI config file

        Returns:
            List of TestStepInfo if config valid and test steps found
            None if config invalid/malformed (logs warning internally)

        Raises:
            FileNotFoundError: If config_path does not exist

        Side Effects:
            Logs parse errors as warnings
        """
```

**JSON Schema Contract** (contracts/ci_config_result_schema.json):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CIConfigResult",
  "type": "object",
  "required": ["platform", "has_test_steps", "has_coverage_upload", "test_job_count", "calculated_score"],
  "properties": {
    "platform": {
      "type": ["string", "null"],
      "enum": ["github_actions", "gitlab_ci", "circleci", "travis_ci", "jenkins", null]
    },
    "config_file_path": {
      "type": ["string", "null"]
    },
    "has_test_steps": {
      "type": "boolean"
    },
    "test_commands": {
      "type": "array",
      "items": {"type": "string"}
    },
    "has_coverage_upload": {
      "type": "boolean"
    },
    "coverage_tools": {
      "type": "array",
      "items": {"type": "string"}
    },
    "test_job_count": {
      "type": "integer",
      "minimum": 0
    },
    "calculated_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 13
    },
    "parse_errors": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

### Test Scenarios from User Stories

**Integration Test Scenarios** (maps to Acceptance Scenarios 1-6):

1. **GitHub Actions with test steps** (Scenario 1)
   - Given: Repository with `.github/workflows/test.yml` containing `run: pytest`
   - When: CIConfigAnalyzer.analyze_ci_config(repo_path) called
   - Then: CIConfigResult.has_test_steps == True, calculated_score >= 5

2. **GitLab CI with Codecov upload** (Scenario 2)
   - Given: Repository with `.gitlab-ci.yml` containing `pytest --cov` and `codecov upload`
   - When: CIConfigAnalyzer.analyze_ci_config(repo_path) called
   - Then: CIConfigResult.has_test_steps == True, has_coverage_upload == True, calculated_score == 10

3. **CircleCI with multiple test jobs** (Scenario 3)
   - Given: Repository with `.circleci/config.yml` containing jobs: unit-tests, integration-tests, e2e-tests
   - When: CIConfigAnalyzer.analyze_ci_config(repo_path) called
   - Then: CIConfigResult.test_job_count >= 2, calculated_score == 13

4. **No CI configuration** (Scenario 4)
   - Given: Repository without any CI config files
   - When: CIConfigAnalyzer.analyze_ci_config(repo_path) called
   - Then: CIConfigResult.platform == None, calculated_score == 0

5. **Travis CI without test commands** (Scenario 5)
   - Given: Repository with `.travis.yml` containing only `script: make build`
   - When: CIConfigAnalyzer.analyze_ci_config(repo_path) called
   - Then: CIConfigResult.has_test_steps == False, calculated_score == 0

6. **Phase 1 + Phase 2 score capping** (Scenario 6)
   - Given: Phase 1 static_score = 25, Phase 2 ci_score = 13
   - When: TestAnalysis aggregation logic applied
   - Then: combined_score == 35, score_breakdown.truncated_points == 3

### Quickstart Validation (quickstart.md)

**Quick Validation Steps** (to be executed after implementation):

```bash
# 1. Install dependencies
uv sync

# 2. Run contract tests (validates JSON schema)
uv run pytest tests/contract/test_ci_config_result_schema.py -v

# 3. Run unit tests for GitHub Actions parser (most common CI platform)
uv run pytest tests/unit/test_github_actions_parser.py -v

# 4. Run integration test with sample repository
uv run pytest tests/integration/test_ci_analysis_workflow.py::test_github_actions_integration -v

# 5. Manual smoke test with real repository
uv run python -m src.cli.main https://github.com/anthropics/anthropic-sdk-python --verbose

# Expected output in submission.json:
# {
#   "metrics": {
#     "testing": {
#       "test_analysis": {
#         "static_infrastructure": { ... },
#         "ci_configuration": {
#           "platform": "github_actions",
#           "has_test_steps": true,
#           "calculated_score": 13
#         },
#         "combined_score": 35
#       }
#     }
#   }
# }
```

### Agent Context Update

Will execute after Phase 1 completion: `.specify/scripts/bash/update-agent-context.sh claude`

**Expected updates to CLAUDE.md**:
- **Recent Changes**: Add "COD-9: CI/CD configuration analysis for Phase 2 test evidence extraction"
- **New Components**: ci_parsers/, pattern_matchers/, ci_config_analyzer.py
- **Key Patterns**: Platform-specific parsers, pattern-based command matching, independent parallel structure (test_analysis container)
- **Testing Notes**: Contract tests validate JSON schema, unit tests cover each parser independently, integration tests use fixtures with sample CI configs

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs:
  - **Contract tests** (1 task): Validate CIConfigResult JSON schema compliance
  - **Model creation** (3 tasks): TestAnalysis, ScoreBreakdown, CIConfigResult/TestStepInfo models
  - **Parser creation** (5 tasks): GitHub Actions, GitLab CI, CircleCI, Travis CI, Jenkins parsers (parallel [P])
  - **Pattern matcher creation** (2 tasks): TestCommandMatcher, CoverageToolMatcher (parallel [P])
  - **Analyzer orchestration** (1 task): CIConfigAnalyzer main logic
  - **Integration** (4 tasks): Update TestInfrastructureAnalyzer and 4 tool runners
  - **Unit tests** (8 tasks): One per parser (5) + matchers (2) + analyzer (1)
  - **Integration tests** (1 task): End-to-end workflow with sample repositories
  - **Logging configuration** (1 task): Implement configurable log levels (FR-027)

**Ordering Strategy**:
- TDD order: Contract tests → Models → Unit tests (failing) → Implementation → Integration tests
- Dependency order:
  1. Models (TestAnalysis, CIConfigResult, TestStepInfo) - no dependencies
  2. Pattern matchers (TestCommandMatcher, CoverageToolMatcher) - depend on models [P]
  3. Base parser interface (CIParser abstract class) - depends on models
  4. Platform parsers (5 parsers) - depend on base parser interface [P]
  5. CIConfigAnalyzer - depends on parsers and matchers
  6. TestInfrastructureAnalyzer update - depends on CIConfigAnalyzer
  7. Tool runner updates (4 runners) - depend on updated TestInfrastructureAnalyzer [P]
  8. Integration tests - depend on all above

**Parallelization Markers [P]**:
- All 5 platform parsers can be developed in parallel (independent files)
- All 2 pattern matchers can be developed in parallel (independent logic)
- All 4 tool runner updates can be applied in parallel (independent files)

**Estimated Output**: ~28 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation <1 second per FR-020)

## Complexity Tracking
*No complexity violations detected - this section intentionally left empty per Constitution Check PASS result*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (clarifications session documented in spec.md)
- [x] Complexity deviations documented (none - no violations)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
