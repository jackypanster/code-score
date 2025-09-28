# Tasks: End-to-End Smoke Test Suite

**Input**: Design documents from `/Users/user/workspace/code-score/specs/001-1-smoke-tests/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow single project structure as defined in plan.md

## Phase 3.1: Setup
- [x] T001 Create smoke test directory structure at tests/smoke/
- [x] T002 [P] Create tests/smoke/__init__.py package marker
- [x] T003 [P] Verify existing pytest configuration supports tests/smoke discovery

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Copy contract tests from contracts/test_validation_schema.py to tests/contract/test_smoke_contract.py
- [x] T005 [P] Create integration test for successful pipeline execution in tests/integration/test_smoke_integration.py
- [x] T006 [P] Create integration test for pipeline failure scenarios in tests/integration/test_smoke_failure_scenarios.py
- [x] T007 [P] Create integration test for output file validation in tests/integration/test_output_validation.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T008 [P] Create SmokeTestExecution data class in tests/smoke/models.py
- [x] T009 [P] Create OutputArtifact data class in tests/smoke/models.py
- [x] T010 [P] Create ValidationResult data class in tests/smoke/models.py
- [x] T011 [P] Create pipeline executor utility in tests/smoke/pipeline_executor.py
- [x] T012 [P] Create output file validator utility in tests/smoke/file_validator.py
- [x] T013 Create main smoke test function in tests/smoke/test_full_pipeline.py
- [x] T014 Add subprocess execution logic for run_metrics.sh in tests/smoke/test_full_pipeline.py
- [x] T015 Add output file existence validation in tests/smoke/test_full_pipeline.py
- [x] T016 Add basic JSON/Markdown content validation in tests/smoke/test_full_pipeline.py

## Phase 3.4: Integration
- [x] T017 Add error handling for pipeline execution failures in tests/smoke/test_full_pipeline.py
- [x] T018 Add timeout handling for long-running pipeline execution in tests/smoke/test_full_pipeline.py
- [x] T019 Add pytest fixtures for test configuration in tests/smoke/conftest.py
- [x] T020 Add cleanup logic for temporary output files in tests/smoke/test_full_pipeline.py

## Phase 3.5: Polish
- [x] T021 [P] Create unit tests for pipeline executor in tests/unit/test_pipeline_executor.py
- [x] T022 [P] Create unit tests for file validator in tests/unit/test_file_validator.py
- [x] T023 [P] Create unit tests for data models in tests/unit/test_smoke_models.py
- [x] T024 Add performance validation (5-minute timeout) in tests/smoke/test_full_pipeline.py
- [x] T025 [P] Verify quickstart.md accuracy with actual implementation
- [x] T026 Add comprehensive error message formatting in tests/smoke/test_full_pipeline.py

## Dependencies
- Setup (T001-T003) before all other tasks
- Tests (T004-T007) before implementation (T008-T026)
- Data models (T008-T010) before utilities (T011-T012)
- Utilities (T011-T012) before main implementation (T013-T016)
- Core implementation (T013-T016) before integration (T017-T020)
- Integration (T017-T020) before polish (T021-T026)

## Parallel Example
```
# Launch T002-T003 together (setup phase):
Task: "Create tests/smoke/__init__.py package marker"
Task: "Verify existing pytest configuration supports tests/smoke discovery"

# Launch T004-T007 together (test phase):
Task: "Copy contract tests from contracts/test_validation_schema.py to tests/contract/test_smoke_contract.py"
Task: "Create integration test for successful pipeline execution in tests/integration/test_smoke_integration.py"
Task: "Create integration test for pipeline failure scenarios in tests/integration/test_smoke_failure_scenarios.py"
Task: "Create integration test for output file validation in tests/integration/test_output_validation.py"

# Launch T008-T012 together (model and utility phase):
Task: "Create SmokeTestExecution data class in tests/smoke/models.py"
Task: "Create OutputArtifact data class in tests/smoke/models.py"
Task: "Create ValidationResult data class in tests/smoke/models.py"
Task: "Create pipeline executor utility in tests/smoke/pipeline_executor.py"
Task: "Create output file validator utility in tests/smoke/file_validator.py"

# Launch T021-T023, T025 together (polish phase):
Task: "Create unit tests for pipeline executor in tests/unit/test_pipeline_executor.py"
Task: "Create unit tests for file validator in tests/unit/test_file_validator.py"
Task: "Create unit tests for data models in tests/unit/test_smoke_models.py"
Task: "Verify quickstart.md accuracy with actual implementation"
```

## Task Details

### T001: Create smoke test directory structure
**Files**: `tests/smoke/` (directory)
**Action**: Create directory structure for smoke test module
**Validation**: Directory exists and is accessible

### T002: Create package marker
**Files**: `tests/smoke/__init__.py`
**Action**: Create empty __init__.py for Python package discovery
**Validation**: File exists, pytest can discover the package

### T003: Verify pytest configuration
**Files**: `pyproject.toml` or `pytest.ini` (read-only verification)
**Action**: Ensure pytest discovers tests/smoke/ directory
**Validation**: `uv run pytest --collect-only tests/smoke/` works

### T004: Copy contract tests
**Files**: `tests/contract/test_smoke_contract.py`
**Action**: Copy and adapt contracts/test_validation_schema.py to contract test directory
**Validation**: Tests exist but fail (no implementation yet)

### T005-T007: Create integration tests
**Files**: `tests/integration/test_smoke_integration.py`, `tests/integration/test_smoke_failure_scenarios.py`, `tests/integration/test_output_validation.py`
**Action**: Create comprehensive integration tests for different scenarios
**Validation**: Tests exist but fail (no implementation yet)

### T008-T010: Create data models
**Files**: `tests/smoke/models.py`
**Action**: Implement SmokeTestExecution, OutputArtifact, ValidationResult classes as dataclasses
**Validation**: Classes importable, have correct attributes

### T011-T012: Create utility modules
**Files**: `tests/smoke/pipeline_executor.py`, `tests/smoke/file_validator.py`
**Action**: Create utility functions for pipeline execution and file validation
**Validation**: Modules importable, functions callable

### T013-T016: Main implementation
**Files**: `tests/smoke/test_full_pipeline.py`
**Action**: Create main smoke test with subprocess calls and validation logic
**Validation**: Test runs and produces meaningful results

### T017-T020: Integration features
**Files**: `tests/smoke/test_full_pipeline.py`, `tests/smoke/conftest.py`
**Action**: Add error handling, timeouts, fixtures, and cleanup
**Validation**: Robust error handling and resource cleanup

### T021-T026: Polish and validation
**Files**: Various unit test files, performance checks
**Action**: Add comprehensive testing and validation
**Validation**: Full test coverage and performance compliance

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Use existing pytest configuration and UV dependency management
- Follow KISS principle: simple, direct implementation
- Target repository: git@github.com:AIGCInnovatorSpace/code-walker.git

## Task Generation Rules Applied

1. **From Contracts**: test_validation_schema.py → T004 contract test task
2. **From Data Model**: 3 entities → T008-T010 model creation tasks [P]
3. **From User Stories**: Pipeline validation scenarios → T005-T007 integration tests [P]
4. **Ordering**: Setup → Tests → Models → Services → Integration → Polish

## Validation Checklist

- [x] All contracts have corresponding tests (T004)
- [x] All entities have model tasks (T008-T010)
- [x] All tests come before implementation (T004-T007 before T008+)
- [x] Parallel tasks truly independent (different files marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task