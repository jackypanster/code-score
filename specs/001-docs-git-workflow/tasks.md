# Tasks: Parameterized Git Repository Metrics Collection

**Input**: Design documents from `/Users/user/workspace/code-score/specs/001-docs-git-workflow/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/`, `scripts/` at repository root
- Paths shown below follow plan.md structure for CLI tool

## Phase 3.1: Setup
- [x] T001 Create project structure per implementation plan (scripts/, src/metrics/, tests/)
- [x] T002 Initialize Python project with uv and dependencies in pyproject.toml
- [x] T003 [P] Configure linting and formatting tools (ruff configuration in pyproject.toml)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test for CLI interface output schema in tests/contract/test_output_schema.py
- [x] T005 [P] Contract test for metrics collection format in tests/contract/test_metrics_format.py
- [x] T006 [P] Integration test repository cloning workflow in tests/integration/test_repo_cloning.py
- [x] T007 [P] Integration test language detection in tests/integration/test_language_detection.py
- [x] T008 [P] Integration test tool execution workflow in tests/integration/test_tool_execution.py
- [x] T009 [P] Integration test full metrics collection with code-walker repository in tests/integration/test_full_workflow.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T010 [P] Repository entity model in src/metrics/models/repository.py
- [x] T011 [P] MetricsCollection entity model in src/metrics/models/metrics_collection.py
- [x] T012 [P] LanguageDetector implementation in src/metrics/language_detection.py
- [x] T013 [P] Git operations module in src/metrics/git_operations.py
- [x] T014 [P] Python tool runner in src/metrics/tool_runners/python_tools.py
- [x] T015 [P] JavaScript tool runner in src/metrics/tool_runners/javascript_tools.py
- [x] T016 [P] Java tool runner in src/metrics/tool_runners/java_tools.py
- [x] T017 [P] Golang tool runner in src/metrics/tool_runners/golang_tools.py
- [x] T018 [P] Output generators for JSON/Markdown in src/metrics/output_generators.py
- [x] T019 Tool executor coordinator in src/metrics/tool_executor.py
- [x] T020 CLI main interface in src/cli/main.py
- [x] T021 Main entry script in scripts/run_metrics.sh

## Phase 3.4: Integration
- [x] T022 Connect tool runners to file system detection in src/metrics/tool_executor.py
- [x] T023 Integrate output formatting with metrics collection in src/metrics/output_generators.py
- [x] T024 Error handling and logging throughout pipeline in src/metrics/error_handling.py
- [x] T025 Temporary directory management and cleanup in src/metrics/cleanup.py

## Phase 3.5: Polish
- [ ] T026 [P] Unit tests for language detection in tests/unit/test_language_detection.py
- [ ] T027 [P] Unit tests for tool runners in tests/unit/test_tool_runners.py
- [ ] T028 [P] Unit tests for output formatting in tests/unit/test_output_formatting.py
- [ ] T029 [P] Unit tests for git operations in tests/unit/test_git_operations.py
- [ ] T030 Performance optimization for large repositories (5-minute timeout handling)
- [ ] T031 [P] Update README.md with installation and usage instructions
- [ ] T032 [P] Create example outputs in examples/ directory
- [ ] T033 Run validation with code-walker repository as per quickstart.md

## Dependencies
- Setup (T001-T003) before tests (T004-T009)
- Tests (T004-T009) before implementation (T010-T021)
- Core models (T010-T011) before services (T012-T018)
- Individual tool runners (T014-T017) before coordinator (T019)
- Core implementation (T010-T021) before integration (T022-T025)
- Integration (T022-T025) before polish (T026-T033)

## Parallel Example
```bash
# Launch contract tests together (T004-T005):
Task: "Contract test for CLI interface output schema in tests/contract/test_output_schema.py"
Task: "Contract test for metrics collection format in tests/contract/test_metrics_format.py"

# Launch integration tests together (T006-T009):
Task: "Integration test repository cloning workflow in tests/integration/test_repo_cloning.py"
Task: "Integration test language detection in tests/integration/test_language_detection.py"
Task: "Integration test tool execution workflow in tests/integration/test_tool_execution.py"
Task: "Integration test full metrics collection with code-walker repository in tests/integration/test_full_workflow.py"

# Launch core models together (T010-T011):
Task: "Repository entity model in src/metrics/models/repository.py"
Task: "MetricsCollection entity model in src/metrics/models/metrics_collection.py"

# Launch tool runners together (T014-T017):
Task: "Python tool runner in src/metrics/tool_runners/python_tools.py"
Task: "JavaScript tool runner in src/metrics/tool_runners/javascript_tools.py"
Task: "Java tool runner in src/metrics/tool_runners/java_tools.py"
Task: "Golang tool runner in src/metrics/tool_runners/golang_tools.py"

# Launch unit tests together (T026-T029):
Task: "Unit tests for language detection in tests/unit/test_language_detection.py"
Task: "Unit tests for tool runners in tests/unit/test_tool_runners.py"
Task: "Unit tests for output formatting in tests/unit/test_output_formatting.py"
Task: "Unit tests for git operations in tests/unit/test_git_operations.py"
```

## Task Details

### Key Implementation Notes
- **T002**: Use uv for dependency management as per constitution requirements
- **T004-T005**: Validate output against JSON schema defined in contracts/output_schema.json
- **T009**: Must test against git@github.com:AIGCInnovatorSpace/code-walker.git as validation repository
- **T012**: Implement file extension analysis with GitHub Linguist patterns per research.md
- **T013**: Use command-line git with temporary directories per research.md decisions
- **T014-T017**: Implement language-specific tools per research.md tool selection
- **T021**: Bash script that orchestrates Python modules and handles CLI arguments
- **T024**: Follow constitutional KISS principle - fail fast on critical errors, graceful degradation on tool failures
- **T030**: Implement 5-minute timeout per performance goals in plan.md

### Validation Criteria
- All contract tests must validate against schemas in contracts/
- Integration test T009 must successfully analyze code-walker repository
- Tool runners must gracefully handle missing tools (log warning, continue)
- Output must conform to JSON schema in contracts/output_schema.json
- CLI must accept repository URL and optional commit SHA as specified in quickstart.md

## Notes
- [P] tasks target different files with no dependencies
- All tests must fail before implementation begins (TDD)
- Follow constitutional requirements: UV dependency management, KISS principle, transparent error handling
- Each tool runner should be independent and parallel-executable
- Integration phase connects components built in core phase
- Polish phase adds comprehensive testing and documentation