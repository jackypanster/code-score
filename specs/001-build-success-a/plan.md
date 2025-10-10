# Implementation Plan: Complete Build Detection Integration

**Branch**: `001-build-success-a` | **Date**: 2025-10-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-build-success-a/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✓ Loaded from /Users/zhibinpan/workspace/code-score/specs/001-build-success-a/spec.md
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✓ Project Type: Single project (metrics collection pipeline)
   → ✓ Structure Decision: Extend existing src/metrics/tool_runners architecture
3. Fill the Constitution Check section based on the constitution document
   → ✓ UV dependency management: Compliant (Python-only project)
   → ✓ KISS principle: Compliant (simple build validation, fail-fast error handling)
   → ✓ Transparent communication: Compliant (clear commit messages, PR descriptions)
4. Evaluate Constitution Check section below
   → ✓ No violations detected
   → ✓ Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → ✓ Researching build detection patterns for 4 languages
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, AGENTS.md
   → ✓ Generate data models for build validation results
7. Re-evaluate Constitution Check section
   → ✓ Post-design compliance verification
8. Plan Phase 2 → Describe task generation approach
   → ✓ TDD-based task ordering defined
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

**Primary Requirement**: Enable automatic build validation for all supported programming languages (Python, JavaScript/TypeScript, Java, Go) to provide comprehensive code quality assessment including build health status.

**Technical Approach**: Extend existing tool runner infrastructure (`src/metrics/tool_runners/`) to add build validation methods (`run_build()`) for each language, integrate results into `MetricsCollection` data model, and ensure `build_success` field is populated with boolean values in `submission.json` output.

**User Value**: Users can comprehensively evaluate code quality with automated build status detection, eliminating manual verification and providing consistent, evidence-based build health reporting across diverse project ecosystems.

## Technical Context
**Language/Version**: Python 3.11+ (project language), analyzing Python 3.x, JavaScript/TypeScript (ES6+, Node 16+), Java 11+, Go 1.18+
**Primary Dependencies**:
- Existing: `subprocess`, `json`, `pathlib`, `typing`
- Build tools (optional): `python -m build`, `uv build`, `npm`, `yarn`, `go`, `maven`, `gradle`
**Storage**: File-based output (JSON schemas), no database required
**Testing**: pytest (unit, integration, contract tests)
**Target Platform**: Linux/macOS servers (CI/CD environments)
**Project Type**: Single project - metrics collection pipeline
**Performance Goals**:
- Build validation completes within 2 minutes per project (NFR-001)
- Overall pipeline timeout: 5 minutes (existing constraint)
- Individual tool timeout: 120 seconds maximum
**Constraints**:
- No repository modification (NFR-003)
- Error messages truncated to 1000 characters (NFR-002)
- Graceful degradation when build tools unavailable (FR-007)
- Offline operation capability (no external API dependencies)
**Scale/Scope**:
- 4 programming languages (Python, JavaScript, Java, Go)
- ~1000 lines of code addition across 4 tool runner files
- 20+ test repositories for validation
- Supports repositories up to 500MB

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: UV-Based Dependency Management
**Status**: ✅ PASS
- All Python development dependencies managed via `uv`
- No new external Python packages required for build validation
- Build tool execution uses `subprocess` (no package dependencies)
- Test dependencies already in `pyproject.toml` managed by `uv`

### Principle II: KISS Principle (Keep It Simple, Stupid)
**Status**: ✅ PASS
- Build validation uses simple subprocess calls, no complex frameworks
- Fail-fast error handling: immediate exception on tool failures
- No over-engineering: Direct tool execution → parse output → record result
- Minimal abstractions: Each language has dedicated `run_build()` method
- Graceful degradation: Return `null` with reason when tools unavailable
- Error handling: Throw exceptions immediately, no silent failures

**Simplicity Verification**:
- Single responsibility: Each `run_build()` method does one thing
- No deep inheritance: Tool runners are flat, independent classes
- Composition over inheritance: Tool executor coordinates runners without inheritance
- Avoid premature optimization: Direct execution, parse on demand

### Principle III: Transparent Change Communication
**Status**: ✅ PASS
- All code changes will include descriptive commit messages (what + why)
- Pull request will document: feature purpose, affected components, test coverage
- Design decisions documented in this plan and research.md
- Breaking changes: Schema version bump if `build_success` format changes
- Change rationale: Addressing "△" status metrics in target-repository-scoring.md

**Communication Plan**:
- Commit message format: `feat(build-detection): add {language} build validation - addresses build_success null values`
- PR description includes: problem statement, solution approach, test results
- Documentation updates: README.md, CLAUDE.md, target-repository-scoring.md

### Post-Design Constitution Re-check
*Updated after Phase 1 completion*
- [x] Verify data models follow KISS principle (simple Pydantic models)
  - ✅ BuildValidationResult: Simple dataclass with 5 fields, no complex logic
  - ✅ CodeQualityMetrics extension: Additive change, 2 new fields
  - ✅ No inheritance hierarchies, flat structure
- [x] Confirm no new dependencies introduced
  - ✅ Zero new Python packages required
  - ✅ Only stdlib imports: subprocess, json, pathlib, typing
  - ✅ Build tools optional (graceful degradation when unavailable)
- [x] Validate contract tests have clear failure messages
  - ✅ All assertions include descriptive error messages
  - ✅ Test names clearly indicate expected behavior
  - ✅ TDD approach: Tests written before implementation (expected to fail initially)

## Project Structure

### Documentation (this feature)
```
specs/001-build-success-a/
├── plan.md              # This file (/plan command output)
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output (build detection research)
├── data-model.md        # Phase 1 output (BuildValidationResult model)
├── quickstart.md        # Phase 1 output (manual validation steps)
└── contracts/           # Phase 1 output (schema validation tests)
    ├── build_result_schema.json     # JSON schema for build validation result
    └── test_build_schema.py         # Contract test for build_success field
```

### Source Code (repository root)
```
src/metrics/
├── models/
│   └── metrics_collection.py       # UPDATE: Add build_results field to CodeQualityMetrics
├── tool_runners/
│   ├── python_tools.py              # ADD: run_build() method
│   ├── javascript_tools.py          # ADD: run_build() method
│   ├── golang_tools.py              # ADD: run_build() method (already exists, wire to output)
│   └── java_tools.py                # ADD: run_build() method (already exists, wire to output)
├── tool_executor.py                 # UPDATE: Add build validation to parallel_tasks
└── output_generators.py             # UPDATE: Include build_success in submission.json

tests/
├── contract/
│   ├── test_build_schema.py         # NEW: Validate build_success field schema
│   └── test_metrics_format.py       # UPDATE: Add build validation assertions
├── integration/
│   ├── test_python_build.py         # NEW: End-to-end Python build validation
│   ├── test_javascript_build.py     # NEW: End-to-end JavaScript build validation
│   ├── test_go_build.py             # NEW: End-to-end Go build validation
│   └── test_java_build.py           # NEW: End-to-end Java build validation
└── unit/
    ├── test_python_tools.py         # UPDATE: Add run_build() tests
    ├── test_javascript_tools.py     # UPDATE: Add run_build() tests
    ├── test_golang_tools.py         # UPDATE: Add run_build() tests
    └── test_java_tools.py           # UPDATE: Add run_build() tests
```

**Structure Decision**: Single project architecture maintained. The feature extends the existing `src/metrics/tool_runners/` module by adding `run_build()` methods to each language-specific tool runner class. Changes are localized to 4 tool runner files, 1 data model file, 1 executor file, and corresponding test files. This follows the existing pattern established for `run_linting()`, `run_testing()`, and `run_security_audit()` methods.

## Phase 0: Outline & Research

### Research Tasks
1. **Python Build Detection Patterns**:
   - Research: Standard Python build tools (`python -m build`, `uv build`, `setuptools`)
   - Decision: Prioritize `uv build` for UV compatibility, fallback to `python -m build`
   - Validation: Check for `pyproject.toml`, `setup.py`, or `setup.cfg` presence
   - Error cases: Missing build backend, invalid configuration

2. **JavaScript/TypeScript Build Detection Patterns**:
   - Research: Build script detection in `package.json`, tool availability
   - Decision: Check `scripts.build` in package.json, prefer `npm run build`, fallback to `yarn build`
   - Validation: Verify `package.json` exists and has build script
   - Error cases: No build script defined, tool unavailable

3. **Go Build Detection Patterns**:
   - Research: Existing `GolangToolRunner` implementation analysis
   - Decision: Use existing `go build ./...` logic, integrate to metrics output
   - Validation: Check for `go.mod` file presence
   - Error cases: Build failures, compilation errors

4. **Java Build Detection Patterns**:
   - Research: Existing `JavaToolRunner` implementation analysis
   - Decision: Use existing `mvn compile` / `gradle compileJava` logic, integrate to metrics
   - Validation: Detect `pom.xml` (Maven) or `build.gradle` (Gradle)
   - Error cases: Build tool unavailable, compilation failures

5. **Build Result Schema Design**:
   - Research: Existing `MetricsCollection` and `CodeQualityMetrics` schemas
   - Decision: Extend `CodeQualityMetrics` with `build_success: bool | None` and `build_error_details: dict`
   - Validation: Schema compatibility with existing output generators
   - Error cases: Schema validation failures

6. **Timeout and Performance Optimization**:
   - Research: Current tool executor timeout strategy
   - Decision: Build validation as parallel task, 2-minute individual timeout
   - Validation: Measure build duration across test repositories
   - Error cases: Timeout handling, cancellation of long-running builds

**Output**: research.md with build detection strategies, tool selection rationale, error handling patterns, and schema extension design

## Phase 1: Design & Contracts

### 1. Data Model Design (`data-model.md`)

**Primary Entities**:
- **BuildValidationResult**: Represents build validation outcome
  - Fields: `success: bool | None`, `tool_used: str`, `execution_time_seconds: float`, `error_message: str | None`, `exit_code: int | None`
  - Validation: `success` is `True` (pass), `False` (fail), or `None` (tool unavailable)
  - State transitions: None → Success, None → Failure, None → Unavailable

- **CodeQualityMetrics Extension**: Add build validation to existing model
  - New field: `build_success: bool | None` (exposed in submission.json)
  - New field: `build_details: BuildValidationResult | None` (internal diagnostics)
  - Backward compatibility: `build_success` defaults to `None` for existing code

**Relationships**:
- `MetricsCollection` → `CodeQualityMetrics` → `build_success` field
- Each `ToolRunner` → produces `BuildValidationResult` → mapped to `build_success`

### 2. API Contracts (`/contracts/`)

**Contract 1: Build Validation Result Schema**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": ["boolean", "null"]},
    "tool_used": {"type": "string"},
    "execution_time_seconds": {"type": "number", "minimum": 0},
    "error_message": {"type": ["string", "null"], "maxLength": 1000},
    "exit_code": {"type": ["integer", "null"]}
  },
  "required": ["success", "tool_used", "execution_time_seconds"]
}
```

**Contract 2: submission.json Extension**
```json
{
  "metrics": {
    "code_quality": {
      "build_success": {"type": ["boolean", "null"]},
      "build_details": {"$ref": "#/definitions/BuildValidationResult"}
    }
  }
}
```

### 3. Contract Tests

**Test File**: `tests/contract/test_build_schema.py`
- Assert `build_success` field exists in submission.json
- Assert `build_success` is boolean or null (never undefined)
- Assert `build_details` matches BuildValidationResult schema
- Assert error messages truncated to 1000 characters
- These tests MUST fail initially (no implementation yet)

### 4. Integration Test Scenarios

**From User Stories** (spec.md Acceptance Scenarios):
1. **Python Build Validation**: Given Python project with `pyproject.toml`, when analysis runs, then `build_success` is `true` or `false`
2. **JavaScript Build Validation**: Given JS project with `package.json` build script, when analysis runs, then `build_success` recorded
3. **Go Build Validation**: Given Go project with `go.mod`, when analysis runs, then build status captured
4. **Java Build Validation**: Given Java project with Maven/Gradle, when analysis runs, then build verified
5. **Build Failure Handling**: Given project with build errors, when analysis runs, then `build_success=false` and error details captured
6. **Tool Unavailable**: Given project where build tools missing, when analysis runs, then `build_success=null` with reason

### 5. Quickstart Validation (`quickstart.md`)

**Manual Validation Steps**:
1. Clone test repository (one per language: Python, JS, Go, Java)
2. Run `./scripts/run_metrics.sh <repo_url>`
3. Verify `output/submission.json` has `build_success` field
4. Verify `build_success` value matches manual build attempt
5. Test error case: Introduce build error, verify `build_success=false`
6. Test unavailable case: Remove build tool, verify `build_success=null`

### 6. Update AGENTS.md

**Incremental Update**:
- Add to "Recent Changes" section: Build detection feature for all languages
- Add to "Common Commands": Example build validation workflow
- Update "Data Models": Mention BuildValidationResult and build_success field
- Preserve existing content, keep under 150 lines

**Execution**: Run `.specify/scripts/bash/update-agent-context.sh claude`

**Output**: data-model.md, /contracts/build_result_schema.json, /contracts/test_build_schema.py (failing), quickstart.md, updated AGENTS.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate tasks from Phase 1 design artifacts:
   - **Contract Tests** (from contracts/):
     - Task: Write failing contract test for build_success schema [P]
     - Task: Write failing contract test for BuildValidationResult format [P]
   - **Data Models** (from data-model.md):
     - Task: Add BuildValidationResult Pydantic model to models/ [P]
     - Task: Extend CodeQualityMetrics with build_success field [depends on BuildValidationResult]
   - **Tool Runners** (from research.md):
     - Task: Implement run_build() in python_tools.py [P]
     - Task: Implement run_build() in javascript_tools.py [P]
     - Task: Wire existing build logic in golang_tools.py to metrics [P]
     - Task: Wire existing build logic in java_tools.py to metrics [P]
   - **Integration** (from spec.md user stories):
     - Task: Add build validation to tool_executor.py parallel tasks
     - Task: Update output_generators.py to include build_success in submission.json
   - **Integration Tests** (from quickstart.md):
     - Task: Write integration test for Python build validation
     - Task: Write integration test for JavaScript build validation
     - Task: Write integration test for Go build validation
     - Task: Write integration test for Java build validation
   - **Unit Tests** (TDD):
     - Task: Write unit tests for python_tools.run_build() [before implementation]
     - Task: Write unit tests for javascript_tools.run_build() [before implementation]
     - Task: Write unit tests for golang_tools build integration
     - Task: Write unit tests for java_tools build integration

**Ordering Strategy**:
- **TDD order**: Contract tests → Unit tests → Implementation → Integration tests
- **Dependency order**:
  1. Data models (BuildValidationResult, CodeQualityMetrics) - foundational
  2. Contract tests (define schema expectations) - [P] parallel
  3. Unit tests for tool runners - [P] parallel per language
  4. Tool runner implementations - [P] parallel per language
  5. Tool executor integration - depends on all tool runners
  6. Output generator updates - depends on executor
  7. Integration tests - final validation
- **Parallel execution markers [P]**: Independent tasks (different files, no shared state)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
- Implement in TDD order (tests first, then implementation)
- Follow UV-based dependency management (no new packages)
- Apply KISS principle (simple subprocess calls, fail-fast errors)
- Document all changes with clear commit messages

**Phase 5**: Validation
- Run contract tests: `uv run pytest tests/contract/test_build_schema.py`
- Run unit tests: `uv run pytest tests/unit/test_*_tools.py`
- Run integration tests: `uv run pytest tests/integration/test_*_build.py`
- Execute quickstart.md validation steps
- Performance validation: Verify 99% of projects complete within 2-minute timeout
- Accuracy validation: Compare automated results with manual builds (≥95% match)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No violations detected. All constitutional principles satisfied:
- ✅ UV-based dependency management: No new Python packages required
- ✅ KISS principle: Simple subprocess execution, fail-fast error handling
- ✅ Transparent communication: Comprehensive documentation and commit messages

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅ research.md created
- [x] Phase 1: Design complete (/plan command) ✅ data-model.md, contracts/, quickstart.md, AGENTS.md updated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅ Approach documented in plan.md
- [ ] Phase 3: Tasks generated (/tasks command) → READY for /tasks
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved (none in spec) ✅
- [x] Complexity deviations documented (none) ✅

**Artifacts Generated**:
- ✅ specs/001-build-success-a/plan.md (this file)
- ✅ specs/001-build-success-a/spec.md (feature specification)
- ✅ specs/001-build-success-a/research.md (Phase 0 research)
- ✅ specs/001-build-success-a/data-model.md (Phase 1 data models)
- ✅ specs/001-build-success-a/quickstart.md (Phase 1 validation procedures)
- ✅ specs/001-build-success-a/contracts/build_result_schema.json (Phase 1 JSON schema)
- ✅ specs/001-build-success-a/contracts/test_build_schema.py (Phase 1 contract tests)
- ✅ CLAUDE.md updated with build detection context

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
