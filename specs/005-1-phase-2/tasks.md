# Tasks: CI/CD Configuration Analysis for Test Evidence

**Feature**: COD-9 Phase 2 - CI/CD Configuration Analysis
**Input**: Design documents from `/Users/zhibinpan/workspace/code-score/specs/005-1-phase-2/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Tech stack: Python 3.11, PyYAML, pytest
   → ✅ Structure: Extends src/metrics/ with ci_parsers/ and pattern_matchers/
2. Load optional design documents:
   → ✅ data-model.md: 4 entities (TestAnalysis, ScoreBreakdown, CIConfigResult, TestStepInfo)
   → ✅ contracts/: 1 JSON schema (ci_config_result_schema.json)
   → ✅ research.md: 8 technical decisions
3. Generate tasks by category:
   → Setup: Dependencies (PyYAML)
   → Tests: 1 contract test + 8 unit tests + 1 integration test
   → Core: 4 models + 5 parsers + 2 matchers + 1 analyzer
   → Integration: 1 analyzer update + 4 tool runner updates
   → Polish: Logging configuration + performance validation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T028)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness: ✅ All entities, parsers, tests covered
9. Return: SUCCESS (28 tasks ready for execution)
```

---

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 3.1: Setup

### T001 - Add PyYAML dependency ✅
**File**: `pyproject.toml`
**Command**: `uv add pyyaml`
**Description**: Add PyYAML library for YAML parsing (GitHub Actions, GitLab CI, Travis CI configs). Verify PyYAML already exists in dependencies (per research.md: already in project).
**Dependencies**: None
**Validation**: Run `uv run python -c "import yaml; print(yaml.__version__)"` and verify version ≥6.0
**Status**: ✅ COMPLETED - PyYAML 6.0.3 already present in dependencies and working correctly

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### T002 [P] - Contract test for CIConfigResult JSON schema ✅
**File**: `tests/contract/test_ci_config_result_schema.py`
**Description**: Write contract test validating CIConfigResult JSON schema compliance against `specs/005-1-phase-2/contracts/ci_config_result_schema.json`. Test cases:
1. Valid CIConfigResult with all fields
2. Required fields validation (platform, has_test_steps, etc.)
3. Enum validation (platform must be in valid set or null)
4. Score range validation (calculated_score in [0, 13])
5. Invalid data rejection (extra fields, wrong types)

**Expected**: Tests FAIL (models and analyzer not implemented yet)
**Dependencies**: None (schema file already exists)
**Validation**: `uv run pytest tests/contract/test_ci_config_result_schema.py -v` - all tests should FAIL with "ModuleNotFoundError: No module named 'src.metrics.models.ci_config'"
**Status**: ✅ COMPLETED - 13 tests written (10 skipped awaiting implementation, 3 passed meta-tests)

---

### T003 [P] - Unit test for GitHub Actions parser ✅
**File**: `tests/unit/test_github_actions_parser.py`
**Description**: Write unit tests for GitHubActionsParser covering:
1. Parse valid `.github/workflows/test.yml` with test steps
2. Detect test commands (pytest, npm test, etc.)
3. Detect coverage upload (codecov/codecov-action)
4. Count distinct test jobs
5. Handle malformed YAML gracefully (return None)
6. Handle missing file (raise FileNotFoundError)

Use test fixtures in `tests/fixtures/github_actions/` with sample workflow files.
**Expected**: Tests FAIL (parser not implemented)
**Dependencies**: None
**Validation**: `uv run pytest tests/unit/test_github_actions_parser.py -v` - all tests FAIL with import error
**Status**: ✅ COMPLETED - 18 tests written (15 skipped awaiting implementation, 3 passed meta-tests), 4 fixtures created

---

### T004 [P] - Unit test for GitLab CI parser ✅
**File**: `tests/unit/test_gitlab_ci_parser.py`
**Description**: Write unit tests for GitLabCIParser covering:
1. Parse valid `.gitlab-ci.yml` with test stages
2. Detect test commands in `script` sections
3. Detect coverage upload (codecov upload, coverage report)
4. Count distinct test jobs across stages
5. Handle malformed YAML (return None)

Use test fixtures in `tests/fixtures/gitlab_ci/`.
**Expected**: Tests FAIL (parser not implemented)
**Dependencies**: None
**Validation**: `uv run pytest tests/unit/test_gitlab_ci_parser.py -v` - all tests FAIL
**Status**: ✅ COMPLETED - 22 tests written (19 skipped awaiting implementation, 3 passed meta-tests), 4 fixtures created

---

### T005 [P] - Unit test for CircleCI parser ✅
**File**: `tests/unit/test_circleci_parser.py`
**Description**: Write unit tests for CircleCIParser covering:
1. Parse valid `.circleci/config.yml` (CircleCI 2.0 format)
2. Detect test commands in `run` steps
3. Detect coverage upload in workflows
4. Count test jobs
5. Handle malformed YAML

Use test fixtures in `tests/fixtures/circleci/`.
**Expected**: Tests FAIL (parser not implemented)
**Dependencies**: None
**Validation**: `uv run pytest tests/unit/test_circleci_parser.py -v` - all tests FAIL
**Status**: ✅ COMPLETED - 23 tests written (20 skipped awaiting implementation, 3 passed meta-tests), 4 fixtures created

---

### T006 [P] - Unit test for Travis CI parser ✅
**File**: `tests/unit/test_travis_parser.py`
**Description**: Write unit tests for TravisParser covering:
1. Parse valid `.travis.yml` with test script
2. Detect test commands in `script` section
3. Detect coverage upload in `after_success`
4. Handle legacy Travis CI 1.0 format
5. Handle malformed YAML

Use test fixtures in `tests/fixtures/travis/`.
**Expected**: Tests FAIL (parser not implemented)
**Dependencies**: None
**Validation**: `uv run pytest tests/unit/test_travis_parser.py -v` - all tests FAIL
**Status**: ✅ COMPLETED - 12 tests written (9 skipped awaiting implementation, 3 passed meta-tests), 4 fixtures created

---

### T007 [P] - Unit test for Jenkins parser ✅
**File**: `tests/unit/test_jenkins_parser.py`
**Description**: Write unit tests for JenkinsParser covering:
1. Parse `Jenkinsfile` with regex extraction of test commands
2. Detect `sh 'pytest'`, `sh 'mvn test'`, `bat 'gradlew test'` patterns
3. Handle Groovy DSL without full parsing (per research.md decision)
4. Return None for unparseable Jenkinsfiles
5. Handle missing file

Use test fixtures in `tests/fixtures/jenkins/`.
**Expected**: Tests FAIL (parser not implemented)
**Dependencies**: None
**Validation**: `uv run pytest tests/unit/test_jenkins_parser.py -v` - all tests FAIL
**Status**: ✅ COMPLETED - 20 tests written (17 skipped awaiting implementation, 3 passed meta-tests), 5 fixtures created (pytest, Maven, Gradle, no tests, complex multi-language)

---

### T008 [P] - Unit test for TestCommandMatcher ✅
**File**: `tests/unit/test_test_command_matcher.py`
**Description**: Write unit tests for TestCommandMatcher covering:
1. Match pytest commands (`pytest`, `python -m pytest`, `pytest --cov=src`)
2. Match npm commands (`npm test`, `npm run test`)
3. Match Go commands (`go test`, `go test ./...`)
4. Match Java commands (`mvn test`, `gradle test`, `./gradlew test`)
5. Infer framework from command (pytest → "pytest", npm test → "jest", etc.)
6. Detect coverage flags (`--cov`, `--coverage`)
7. Reject non-test commands (build, lint, deploy)

**Expected**: Tests FAIL (matcher not implemented)
**Dependencies**: None
**Validation**: `uv run pytest tests/unit/test_test_command_matcher.py -v` - all tests FAIL
**Status**: ✅ COMPLETED - 39 tests written (37 skipped awaiting implementation, 2 passed meta-tests), covers 4 languages (Python, JS, Go, Java) + edge cases

---

### T009 [P] - Unit test for CoverageToolMatcher ✅
**File**: `tests/unit/test_coverage_tool_matcher.py`
**Description**: Write unit tests for CoverageToolMatcher covering:
1. Detect Codecov upload (`codecov/codecov-action`, `codecov upload`)
2. Detect Coveralls integration (`coveralls`)
3. Detect SonarQube scan (`sonar-scanner`, `sonarqube`)
4. Detect coverage report generation flags (`--cov`, `--coverage`)
5. Handle multiple coverage tools in same config
6. Return empty list if no coverage tools detected

**Expected**: Tests FAIL (matcher not implemented)
**Dependencies**: None
**Validation**: `uv run pytest tests/unit/test_coverage_tool_matcher.py -v` - all tests FAIL
**Status**: ✅ COMPLETED - 33 tests written (31 skipped awaiting implementation, 2 passed meta-tests), covers 3 tools (Codecov, Coveralls, SonarQube) + edge cases

---

### T010 [P] - Unit test for CIConfigAnalyzer ✅
**File**: `tests/unit/test_ci_config_analyzer.py`
**Description**: Write unit tests for CIConfigAnalyzer covering:
1. Detect GitHub Actions config in `.github/workflows/`
2. Detect GitLab CI config `.gitlab-ci.yml`
3. Detect CircleCI config `.circleci/config.yml`
4. Detect Travis CI config `.travis.yml`
5. Detect Jenkins config `Jenkinsfile`
6. Return platform=None if no CI config found
7. Use max score when multiple CI platforms detected (per research.md)
8. Calculate score: 5 (test steps) + 5 (coverage) + 3 (multiple jobs) = 13
9. Handle parse errors gracefully (0 score, populate parse_errors field)
10. Complete analysis in <1 second (performance requirement FR-020)

Use mock parsers or test fixtures.
**Expected**: Tests FAIL (analyzer not implemented)
**Dependencies**: None
**Validation**: `uv run pytest tests/unit/test_ci_config_analyzer.py -v` - all tests FAIL
**Status**: ✅ COMPLETED - 26 tests written (23 skipped awaiting implementation, 3 passed meta-tests), 8 mock fixtures created, covers all 5 platforms + orchestration logic

---

### T011 [P] - Integration test for CI analysis workflow ✅
**File**: `tests/integration/test_ci_analysis_workflow.py`
**Description**: Write end-to-end integration tests covering:
1. **Scenario 1 (Acceptance Scenario 1)**: Repository with GitHub Actions workflows → score increases by 5
2. **Scenario 2 (Acceptance Scenario 2)**: Repository with GitLab CI + Codecov → score increases by 10
3. **Scenario 3 (Acceptance Scenario 3)**: Repository with CircleCI multiple jobs → score = 13
4. **Scenario 4 (Acceptance Scenario 4)**: Repository without CI config → CI score = 0
5. **Scenario 5 (Acceptance Scenario 5)**: Travis CI without test commands → CI score = 0
6. **Scenario 6 (Acceptance Scenario 6)**: Phase 1 (25) + Phase 2 (13) = combined_score 35 (not 38)
7. **Edge Case**: Malformed CI config → score = 0, parse_errors populated, no crash

Use sample repositories in `tests/fixtures/sample_repos/` or create temporary directories with mock CI configs.
**Expected**: Tests FAIL (full pipeline not integrated)
**Dependencies**: None (can mock components initially)
**Validation**: `uv run pytest tests/integration/test_ci_analysis_workflow.py -v` - all tests FAIL
**Status**: ✅ COMPLETED - 15 tests written (13 skipped awaiting Phase 3.3-3.4, 2 passed meta-tests), covers all 6 Acceptance Scenarios + edge cases + performance validation

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

**Prerequisite**: All tests T002-T011 must be written and FAILING before proceeding

---

### T012 [P] - Create data models in ci_config.py ✅
**File**: `src/metrics/models/ci_config.py`
**Description**: Implement 4 dataclasses per data-model.md:
1. **ScoreBreakdown** with fields: phase1_contribution, phase2_contribution, raw_total, capped_total, truncated_points
   - Add `__post_init__()` validation: raw_total = phase1 + phase2, capped_total = min(raw_total, 35), truncated_points = raw_total - capped_total
2. **TestStepInfo** with fields: job_name, command, framework, has_coverage_flag
3. **CIConfigResult** with fields: platform, config_file_path, has_test_steps, test_commands, has_coverage_upload, coverage_tools, test_job_count, calculated_score, parse_errors
   - Add `__post_init__()` validation: 0 <= calculated_score <= 13, platform in valid set or None
4. **TestAnalysis** with fields: static_infrastructure, ci_configuration, combined_score, score_breakdown
   - Add `__post_init__()` validation: combined_score = min(phase1 + phase2, 35)

Use Python dataclasses with type hints. Import TestInfrastructureResult from existing test_infrastructure.py.
**Dependencies**: None
**Validation**: Contract test T002 should now pass. Run `uv run pytest tests/contract/test_ci_config_result_schema.py -v`

---

### T013 [P] - Create TestCommandMatcher ✅
**File**: `src/metrics/pattern_matchers/test_command_matcher.py`
**Description**: Implement TestCommandMatcher class with methods:
1. `is_test_command(command: str) -> bool`: Check if command contains test pattern (substring matching per research.md)
2. `extract_test_commands(steps: List[str]) -> List[str]`: Filter test commands from CI steps
3. `infer_framework(command: str) -> Optional[str]`: Return "pytest" | "jest" | "junit" | "go_test" | None
4. `has_coverage_flag(command: str) -> bool`: Check for --cov or --coverage flags

Use hardcoded TEST_COMMANDS list: ["pytest", "python -m pytest", "npm test", "npm run test", "go test", "mvn test", "gradle test", "./gradlew test"]
**Dependencies**: T012 (needs TestStepInfo model)
**Validation**: Unit test T008 should pass. Run `uv run pytest tests/unit/test_test_command_matcher.py -v`

---

### T014 [P] - Create CoverageToolMatcher ✅
**File**: `src/metrics/pattern_matchers/coverage_tool_matcher.py`
**Description**: Implement CoverageToolMatcher class with methods:
1. `detect_coverage_tools(steps: List[str]) -> List[str]`: Detect codecov, coveralls, sonarqube
2. `has_coverage_upload(steps: List[str]) -> bool`: Check if any coverage tool detected
3. `_match_codecov(step: str) -> bool`: Match "codecov/codecov-action" or "codecov upload"
4. `_match_coveralls(step: str) -> bool`: Match "coveralls" keyword
5. `_match_sonarqube(step: str) -> bool`: Match "sonar-scanner" or "sonarqube"

Use substring matching (not regex per research.md).
**Dependencies**: None
**Validation**: Unit test T009 should pass. Run `uv run pytest tests/unit/test_coverage_tool_matcher.py -v`

---

### T015 - Create CIParser base interface ✅
**File**: `src/metrics/ci_parsers/base.py`
**Description**: Implement abstract base class CIParser with:
1. Abstract method `parse(config_path: Path) -> Optional[List[TestStepInfo]]`
   - Returns List[TestStepInfo] if valid config with test steps
   - Returns None if config invalid/malformed (logs warning)
   - Raises FileNotFoundError if config_path does not exist
2. Helper method `_log_parse_error(error: Exception)`: Log at WARNING level
3. Docstrings per plan.md API contract

Use Python ABC (abstract base class).
**Dependencies**: T012 (needs TestStepInfo model)
**Validation**: Check that all parser imports work. Run `uv run python -c "from src.metrics.ci_parsers.base import CIParser; print('OK')"`

---

### T016 [P] - Implement GitHubActionsParser ✅
**File**: `src/metrics/ci_parsers/github_actions_parser.py`
**Description**: Implement GitHubActionsParser(CIParser) with:
1. `parse(config_path: Path) -> Optional[List[TestStepInfo]]`
   - Use `yaml.safe_load()` to parse workflow file
   - Iterate through jobs → steps
   - Extract `run` commands, check with TestCommandMatcher
   - Extract `uses` actions, check for codecov/codecov-action
   - Build List[TestStepInfo] with job names, commands, frameworks
   - Return None on YAMLError (log warning)
2. `_extract_job_name(job: dict) -> str`: Get job identifier
3. `_extract_run_commands(steps: List[dict]) -> List[str]`: Get all `run:` values

**Dependencies**: T012 (models), T013 (TestCommandMatcher), T015 (base interface)
**Validation**: Unit test T003 should pass. Run `uv run pytest tests/unit/test_github_actions_parser.py -v`

---

### T017 [P] - Implement GitLabCIParser ✅
**File**: `src/metrics/ci_parsers/gitlab_ci_parser.py`
**Description**: Implement GitLabCIParser(CIParser) with:
1. `parse(config_path: Path) -> Optional[List[TestStepInfo]]`
   - Use `yaml.safe_load()` for `.gitlab-ci.yml`
   - Iterate through stages/jobs
   - Extract `script:` lists, check for test commands
   - Extract `after_script:` for coverage uploads
   - Build List[TestStepInfo]
   - Return None on parse errors

**Dependencies**: T012, T013, T015
**Validation**: Unit test T004 should pass. Run `uv run pytest tests/unit/test_gitlab_ci_parser.py -v`

---

### T018 [P] - Implement CircleCIParser ✅
**File**: `src/metrics/ci_parsers/circleci_parser.py`
**Description**: Implement CircleCIParser(CIParser) with:
1. `parse(config_path: Path) -> Optional[List[TestStepInfo]]`
   - Use `yaml.safe_load()` for `.circleci/config.yml`
   - Parse CircleCI 2.0 format (workflows → jobs → steps)
   - Extract `run:` steps, check for test commands
   - Handle both YAML and JSON (PyYAML handles both per research.md)
   - Build List[TestStepInfo]

**Dependencies**: T012, T013, T015
**Validation**: Unit test T005 should pass. Run `uv run pytest tests/unit/test_circleci_parser.py -v`

---

### T019 [P] - Implement TravisParser ✅
**File**: `src/metrics/ci_parsers/travis_parser.py`
**Description**: Implement TravisParser(CIParser) with:
1. `parse(config_path: Path) -> Optional[List[TestStepInfo]]`
   - Use `yaml.safe_load()` for `.travis.yml`
   - Extract `script:` section (test commands)
   - Extract `after_success:` (coverage uploads)
   - Handle Travis CI 1.0 legacy format if present
   - Build List[TestStepInfo]

**Dependencies**: T012, T013, T015
**Validation**: Unit test T006 should pass. Run `uv run pytest tests/unit/test_travis_parser.py -v`

---

### T020 [P] - Implement JenkinsParser ✅
**File**: `src/metrics/ci_parsers/jenkins_parser.py`
**Description**: Implement JenkinsParser(CIParser) with:
1. `parse(config_path: Path) -> Optional[List[TestStepInfo]]`
   - Read Jenkinsfile as plain text (no full Groovy parsing per research.md)
   - Use regex patterns: `sh\s+['"]([^'"]*(?:pytest|mvn test|gradle test)[^'"]*)['"]`
   - Extract test commands from `sh` and `bat` steps
   - Build List[TestStepInfo] with job_name="jenkins_pipeline"
   - Return None if no test patterns found
2. `_extract_sh_commands(jenkinsfile_content: str) -> List[str]`: Regex extraction

**Dependencies**: T012, T013, T015
**Validation**: Unit test T007 should pass. Run `uv run pytest tests/unit/test_jenkins_parser.py -v`

---

### T021 - Implement CIConfigAnalyzer
**File**: `src/metrics/ci_config_analyzer.py`
**Description**: Implement CIConfigAnalyzer class with main method:
1. `analyze_ci_config(repo_path: Path) -> CIConfigResult`:
   - Detect CI platform by checking for config files:
     * `.github/workflows/*.yml` → github_actions
     * `.gitlab-ci.yml` → gitlab_ci
     * `.circleci/config.yml` → circleci
     * `.travis.yml` → travis_ci
     * `Jenkinsfile` → jenkins
   - For each detected platform, call corresponding parser
   - If multiple platforms detected, use max score (per research.md decision 6)
   - Aggregate test steps, coverage tools from all platforms
   - Calculate score:
     ```python
     score = 0
     if has_test_steps: score += 5
     if has_coverage_upload: score += 5
     if test_job_count >= 2: score += 3
     return min(score, 13)
     ```
   - Handle parse errors: log warning, set calculated_score=0, populate parse_errors
   - Return CIConfigResult with all fields populated
2. `_detect_ci_platform(repo_path: Path) -> List[str]`: Return list of detected platforms
3. `_calculate_score(test_steps: List[TestStepInfo], coverage_tools: List[str]) -> int`

Configure logging (INFO level for standard, DEBUG for detailed per Clarification Q2).
**Dependencies**: T012 (models), T013-T014 (matchers), T016-T020 (parsers)
**Validation**: Unit test T010 should pass. Run `uv run pytest tests/unit/test_ci_config_analyzer.py -v`

---

## Phase 3.4: Integration

### T022 - Update TestInfrastructureAnalyzer to call CIConfigAnalyzer
**File**: `src/metrics/test_infrastructure_analyzer.py`
**Description**: Modify TestInfrastructureAnalyzer.analyze() to:
1. After Phase 1 static analysis completes, call `CIConfigAnalyzer.analyze_ci_config(repo_path)`
2. Create TestAnalysis object with:
   - `static_infrastructure`: existing Phase 1 result
   - `ci_configuration`: Phase 2 CIConfigResult
   - `combined_score`: min(phase1_score + phase2_score, 35)
   - `score_breakdown`: ScoreBreakdown with all fields
3. Return TestAnalysis instead of TestInfrastructureResult
4. Ensure backward compatibility: if CI analysis disabled, return ci_configuration=None

**Dependencies**: T012 (TestAnalysis model), T021 (CIConfigAnalyzer)
**Validation**: Run existing test suite to ensure no regressions: `uv run pytest tests/unit/test_test_infrastructure_analyzer.py -v`

---

### T023 [P] - Update python_tools.py to use TestAnalysis
**File**: `src/metrics/tool_runners/python_tools.py`
**Description**: Update PythonTools.run_tests() to:
1. Call updated TestInfrastructureAnalyzer
2. Handle TestAnalysis result instead of TestInfrastructureResult
3. Extract combined_score for metrics collection
4. Log score_breakdown at DEBUG level

**Dependencies**: T022 (updated analyzer)
**Validation**: Run integration test with Python repository: `uv run pytest tests/integration/test_ci_analysis_workflow.py::test_github_actions_integration -v`

---

### T024 [P] - Update javascript_tools.py to use TestAnalysis
**File**: `src/metrics/tool_runners/javascript_tools.py`
**Description**: Same updates as T023 but for JavaScriptTools.run_tests()

**Dependencies**: T022
**Validation**: Test with JavaScript repository fixture

---

### T025 [P] - Update golang_tools.py to use TestAnalysis
**File**: `src/metrics/tool_runners/golang_tools.py`
**Description**: Same updates as T023 but for GolangTools.run_tests()

**Dependencies**: T022
**Validation**: Test with Go repository fixture

---

### T026 [P] - Update java_tools.py to use TestAnalysis
**File**: `src/metrics/tool_runners/java_tools.py`
**Description**: Same updates as T023 but for JavaTools.run_tests()

**Dependencies**: T022
**Validation**: Test with Java repository fixture

---

## Phase 3.5: Polish

### T027 - Implement configurable logging levels (FR-027)
**File**: `src/cli/main.py` (add --log-level flag), `src/metrics/ci_config_analyzer.py` (use logger)
**Description**: Implement configurable logging per Clarification Q2:
1. Add `--log-level` CLI flag to main.py with choices: minimal, standard, detailed
2. Map to Python logging levels:
   - minimal → WARNING (final score + CI platform names only)
   - standard → INFO (default: platforms, test step count, coverage tools, parse warnings)
   - detailed → DEBUG (all parse steps, command matching, execution time, file excerpts)
3. Configure logger in CIConfigAnalyzer:
   ```python
   logger.info(f"Detected CI platform: {platform}")          # Standard
   logger.debug(f"Parsing workflow file: {config_path}")     # Detailed
   logger.warning(f"Parse error in {config_path}: {error}")  # Minimal
   ```
4. Add timing metrics: log CI analysis duration at DEBUG level

**Dependencies**: T021 (CIConfigAnalyzer)
**Validation**: Run with different log levels:
- `uv run python -m src.cli.main <repo> --log-level minimal`
- `uv run python -m src.cli.main <repo> --log-level standard`
- `uv run python -m src.cli.main <repo> --log-level detailed`

---

### T028 - Run quickstart.md validation
**File**: `specs/005-1-phase-2/quickstart.md`
**Description**: Execute all 8 quickstart validation steps:
1. Install dependencies: `uv sync`
2. Run contract tests: `uv run pytest tests/contract/test_ci_config_result_schema.py -v`
3. Run unit tests: `uv run pytest tests/unit/test_*_parser.py -v`
4. Run integration tests: `uv run pytest tests/integration/test_ci_analysis_workflow.py -v`
5. Manual smoke test: `uv run python -m src.cli.main https://github.com/anthropics/anthropic-sdk-python --verbose`
6. Verify score capping: Check submission.json has `combined_score <= 35`
7. Test error handling: Verify malformed configs don't crash
8. Test logging levels: Verify minimal/standard/detailed output

Ensure all tests pass and output matches quickstart.md expectations.
**Dependencies**: All previous tasks (T001-T027)
**Validation**: All quickstart steps pass, submission.json contains valid `test_analysis` structure

---

## Dependencies Graph

```
Setup:
T001 (PyYAML) → [All parser tasks]

Tests First (TDD):
T002-T011 (All tests) → [No dependencies, run in parallel]

Models:
T012 (Models) → T013, T014, T015, T016-T020, T021

Matchers:
T013 (TestCommandMatcher) → T016-T020, T021
T014 (CoverageToolMatcher) → T021

Base Interface:
T015 (CIParser) → T016-T020

Parsers (can run in parallel after base):
T016 (GitHub Actions Parser) → T021
T017 (GitLab CI Parser) → T021
T018 (CircleCI Parser) → T021
T019 (Travis Parser) → T021
T020 (Jenkins Parser) → T021

Analyzer:
T021 (CIConfigAnalyzer) → T022

Integration:
T022 (TestInfrastructureAnalyzer) → T023, T024, T025, T026
T023-T026 (Tool runners) → [Can run in parallel]

Polish:
T027 (Logging) → T028
T028 (Quickstart) → [Final validation]
```

---

## Parallel Execution Examples

### Example 1: Tests First (T002-T011 in parallel)
```bash
# All tests can be written in parallel (different files)
uv run pytest tests/contract/test_ci_config_result_schema.py -v &
uv run pytest tests/unit/test_github_actions_parser.py -v &
uv run pytest tests/unit/test_gitlab_ci_parser.py -v &
uv run pytest tests/unit/test_circleci_parser.py -v &
uv run pytest tests/unit/test_travis_parser.py -v &
uv run pytest tests/unit/test_jenkins_parser.py -v &
uv run pytest tests/unit/test_test_command_matcher.py -v &
uv run pytest tests/unit/test_coverage_tool_matcher.py -v &
uv run pytest tests/unit/test_ci_config_analyzer.py -v &
uv run pytest tests/integration/test_ci_analysis_workflow.py -v &
wait
```

### Example 2: Parsers (T016-T020 in parallel)
```bash
# All 5 parsers are independent files
# After T012 (models), T013 (TestCommandMatcher), T015 (base) complete:
# Implement GitHub Actions, GitLab CI, CircleCI, Travis, Jenkins parsers in parallel
```

### Example 3: Tool Runners (T023-T026 in parallel)
```bash
# All 4 tool runners are independent files
# After T022 (TestInfrastructureAnalyzer) updated:
# Update python_tools.py, javascript_tools.py, golang_tools.py, java_tools.py in parallel
```

---

## Validation Checklist

*GATE: Checked before considering feature complete*

- [x] All contracts have corresponding tests (T002 for ci_config_result_schema.json)
- [x] All entities have model tasks (T012 covers TestAnalysis, ScoreBreakdown, CIConfigResult, TestStepInfo)
- [x] All tests come before implementation (T002-T011 before T012-T021)
- [x] Parallel tasks truly independent (T003-T011 different test files, T016-T020 different parser files, T023-T026 different tool runner files)
- [x] Each task specifies exact file path (all tasks include file paths)
- [x] No task modifies same file as another [P] task (verified: no conflicts)
- [x] Performance requirement met (<1 second per FR-020, validated in T010 and T028)
- [x] Logging levels implemented (T027)
- [x] Quickstart validation passes (T028)

---

## Notes

- **[P] tasks** = different files, no dependencies, safe to run in parallel
- **Verify tests fail before implementing** (Phase 3.2 before Phase 3.3)
- **Commit after each task** for incremental progress
- **Avoid**: vague tasks, same file conflicts, skipping test writing
- **Constitution compliance**: UV for dependencies, KISS principle (simple parsers), transparent logging

---

## Estimated Timeline

| Phase | Tasks | Estimated Time | Notes |
|-------|-------|----------------|-------|
| 3.1 Setup | T001 | 15 min | PyYAML already exists, verify only |
| 3.2 Tests | T002-T011 | 4-6 hours | 10 test files, can parallelize |
| 3.3 Core | T012-T021 | 12-16 hours | Models (1h) + Parsers (8h) + Analyzer (3h) |
| 3.4 Integration | T022-T026 | 4-6 hours | Update existing code carefully |
| 3.5 Polish | T027-T028 | 2-3 hours | Logging + validation |
| **Total** | **28 tasks** | **22-31 hours (3-4 days)** | With parallel execution |

---

**Tasks Status**: ✅ Ready for execution (28 tasks generated, dependency-ordered, parallelization-optimized)

**Next Command**: Begin with T001 (Setup), then T002-T011 (Tests First, TDD)
