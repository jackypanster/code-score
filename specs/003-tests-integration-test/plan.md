
# Implementation Plan: Programmatic CLI Evaluation Entry Point

**Branch**: `003-tests-integration-test` | **Date**: 2025-10-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/user/workspace/code-score/specs/003-tests-integration-test/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Spec loaded successfully with clarifications
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ No unknowns - refactoring existing code
   → Project Type: Single Python project
3. Fill the Constitution Check section
   → Evaluating against UV, KISS, and Transparency principles
4. Evaluate Constitution Check section
   → ✅ PASS - Pure refactoring with fail-fast exception handling
5. Execute Phase 0 → research.md
   → ⏭️ SKIPPED - No research needed (refactoring existing code)
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, AGENTS.md
   → Generating data models for exception types and return objects
   → Generating contracts for programmatic API
7. Re-evaluate Constitution Check
   → ✅ PASS - Design maintains simplicity
8. Plan Phase 2 → Describe task generation approach
   → Task decomposition strategy defined
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

**Primary Requirement**: Extract the core evaluation logic from `src/cli/evaluate.py` into a reusable programmatic function `evaluate_submission()` that can be imported and called by integration tests and internal tooling, while maintaining 100% backward compatibility with the existing Click CLI command.

**Technical Approach**:
1. Extract all evaluation logic from the Click command into a pure Python function
2. Replace `sys.exit()` calls with typed exceptions (QualityGateException, EvaluationFileSystemError)
3. Replace `click.echo()` calls with Python logging module
4. Create structured return objects for both normal and validate-only modes
5. Update Click command to delegate to the extracted function
6. Add comprehensive regression tests for both programmatic and CLI entry points

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click 8.1+, Pydantic 2.5+, Python logging (stdlib), existing evaluation pipeline (ChecklistEvaluator, EvidenceTracker, ScoringMapper)
**Storage**: File-based (submission.json input, score_input.json output, evidence/*.json)
**Testing**: pytest 8.4+, pytest-cov for coverage, integration tests with real file I/O
**Target Platform**: Cross-platform (Linux, macOS, Windows) - Python CLI tool
**Project Type**: Single Python project (existing codebase)
**Performance Goals**: No performance degradation from current CLI (refactoring should be zero-cost abstraction)
**Constraints**:
- **Backward Compatibility**: Existing CLI command behavior MUST remain 100% identical
- **Zero External Dependencies**: No new dependencies beyond stdlib logging
- **Import Safety**: Function import MUST NOT trigger Click initialization
**Scale/Scope**: Single module refactoring (~280 lines), 3 new exception classes, 2 return object types, ~10 new test cases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. UV-Based Dependency Management ✅ PASS
- **Status**: Compliant
- **Evidence**: No new dependencies required beyond Python stdlib (logging module)
- **Action**: Continue using existing `uv sync` workflow

### II. KISS Principle (Keep It Simple, Stupid) ✅ PASS
- **Status**: Compliant - Pure extraction refactoring
- **Evidence**:
  - **Fail-fast error handling**: Replacing `sys.exit()` with typed exceptions (simpler to test and handle)
  - **No abstraction layers**: Direct function extraction without intermediate classes or patterns
  - **Single responsibility**: One function handles evaluation, delegation pattern for CLI
- **Action**: Maintain simple exception hierarchy (3 types max), avoid over-engineering return objects

### III. Transparent Change Communication ✅ PASS
- **Status**: Compliant
- **Evidence**: Clear refactoring rationale documented in spec (enable programmatic testing and tool integration)
- **Action**: Document what was extracted, why exceptions replace sys.exit(), and how logging replaces click.echo()

**Initial Constitution Check Result**: ✅ **PASS** - Proceed to Phase 0

## Project Structure

### Documentation (this feature)
```
specs/003-tests-integration-test/
├── plan.md              # This file (/plan command output)
├── research.md          # ⏭️ SKIPPED (no research needed for refactoring)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── programmatic_api.py     # Function signature contract
│   ├── exception_types.py      # Exception hierarchy contract
│   └── return_objects.py       # Return object schemas
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/
├── cli/
│   ├── evaluate.py              # MODIFIED: Extract logic → evaluate_submission(), Click delegates
│   └── exceptions.py            # NEW: QualityGateException, EvaluationFileSystemError
├── metrics/
│   ├── checklist_evaluator.py   # UNCHANGED
│   ├── evidence_tracker.py      # UNCHANGED
│   └── scoring_mapper.py         # UNCHANGED
└── models/                       # UNCHANGED (existing models reused)

tests/
├── contract/
│   ├── test_programmatic_api_contract.py    # NEW: API contract tests
│   └── test_exception_contracts.py          # NEW: Exception type tests
├── integration/
│   ├── test_evidence_path_consistency.py    # MODIFIED: Now imports evaluate_submission
│   ├── test_cli_backward_compat.py          # NEW: CLI behavior regression tests
│   └── test_programmatic_workflow.py        # NEW: End-to-end programmatic tests
└── unit/
    ├── test_evaluate_submission.py          # NEW: Unit tests for extracted function
    └── test_custom_exceptions.py            # NEW: Exception behavior tests
```

**Structure Decision**: Single project structure (Option 1). This is a pure refactoring task within the existing `src/cli/` module. No new projects, services, or architectural layers are introduced. The change is confined to extracting 280 lines of logic into a reusable function while maintaining the existing module structure.

## Phase 0: Outline & Research

**STATUS**: ⏭️ **SKIPPED** - No research required

**Rationale**: This is a code refactoring task with fully-determined technical decisions:
- **No technology choices**: Using existing Python stdlib (logging) and Pydantic
- **No integration unknowns**: Function delegates to existing evaluation pipeline
- **No architectural decisions**: Pure extraction, no new patterns or abstractions
- **No dependency resolution**: Zero new external dependencies

All technical context is clear from the existing codebase analysis (`src/cli/evaluate.py` at 284 lines with known dependencies).

**Output**: No research.md file generated (skipped phase)

## Phase 1: Design & Contracts

*Prerequisites: Technical context fully determined (no research needed)*

### 1. Data Model (`data-model.md`)

**Exception Types**:
```python
# QualityGateException: Business logic failure
class QualityGateException(Exception):
    - score: float           # Actual evaluation score
    - threshold: float       # Quality gate threshold (30.0)
    - evaluation_result: EvaluationResult  # Full evaluation details

# EvaluationFileSystemError: Infrastructure failure
class EvaluationFileSystemError(Exception):
    - operation: str         # e.g., "create_directory", "write_file"
    - target_path: str       # File/directory path that failed
    - original_error: Exception  # Wrapped OSError/PermissionError
```

**Return Objects**:
```python
# ValidationResult: Returned in validate-only mode
class ValidationResult:
    - valid: bool
    - items_checked: List[str]      # ["submission structure", "checklist config", ...]
    - passed_checks: List[str]      # Subset of items_checked that passed
    - warnings: List[str]           # Non-fatal validation warnings

# EvaluationResult: Returned in normal mode
class EvaluationResult:
    - success: bool
    - total_score: float
    - max_possible_score: float
    - grade: str                    # Letter grade A-F
    - generated_files: List[str]    # Absolute paths to output files
    - evidence_files: Dict[str, str]  # {evidence_key: file_path}
    - warnings: List[str]           # Evaluation warnings (if any)
```

### 2. API Contracts (`contracts/programmatic_api.py`)

```python
def evaluate_submission(
    submission_file: str | Path,
    output_dir: str | Path = "output",
    format: Literal["json", "markdown", "both"] = "both",
    checklist_config: str | Path | None = None,
    evidence_dir: str | Path = "evidence",
    validate_only: bool = False,
    verbose: bool = False,
    quiet: bool = False
) -> ValidationResult | EvaluationResult:
    """
    Programmatically evaluate a repository submission.

    Raises:
        FileNotFoundError: If submission_file or checklist_config doesn't exist
        ValueError: If submission structure is invalid or checklist config fails validation
        EvaluationFileSystemError: If output/evidence directory operations fail
        QualityGateException: If evaluation score < 30% (quality gate failure)

    Returns:
        ValidationResult if validate_only=True
        EvaluationResult if validate_only=False and evaluation succeeds
    """
```

### 3. Contract Tests (failing initially)

**Generated Tests**:
- `tests/contract/test_programmatic_api_contract.py`:
  - ✅ Function signature matches contract
  - ✅ validate_only=True returns ValidationResult with required fields
  - ✅ validate_only=False returns EvaluationResult with required fields
  - ✅ FileNotFoundError raised for missing submission file
  - ✅ QualityGateException raised for score < 30%
  - ✅ EvaluationFileSystemError raised for filesystem failures

- `tests/contract/test_exception_contracts.py`:
  - ✅ QualityGateException contains score, threshold, evaluation_result
  - ✅ EvaluationFileSystemError contains operation, target_path, original_error
  - ✅ Both exceptions are properly typed and inherit from Exception

### 4. Integration Test Scenarios (from user stories)

**From Spec Acceptance Scenarios**:

1. **Import Success** (Integration Test Author):
   ```python
   # tests/integration/test_evidence_path_consistency.py (MODIFIED)
   from src.cli.evaluate import evaluate_submission  # Should not raise ImportError
   ```

2. **Programmatic Execution** (Internal Tooling Developer):
   ```python
   # tests/integration/test_programmatic_workflow.py (NEW)
   result = evaluate_submission(submission_file="output/submission.json")
   assert result.success is True
   assert result.total_score > 0
   assert "output/score_input.json" in result.generated_files
   ```

3. **CLI Backward Compatibility** (CLI User):
   ```python
   # tests/integration/test_cli_backward_compat.py (NEW)
   subprocess.run(["uv", "run", "python", "-m", "src.cli.evaluate", "output/submission.json"])
   # Assert identical output format, exit codes, file generation
   ```

4. **Quality Gate Exception** (Tooling Developer):
   ```python
   # tests/integration/test_programmatic_workflow.py (NEW)
   with pytest.raises(QualityGateException) as exc_info:
       evaluate_submission(submission_file="fixtures/low_score_submission.json")
   assert exc_info.value.score < 30.0
   ```

5. **Output Identity** (All Users):
   ```python
   # tests/integration/test_cli_backward_compat.py (NEW)
   prog_result = evaluate_submission(...)
   cli_result = subprocess.run([...], capture_output=True)
   # Assert score_input.json files are identical
   ```

### 5. Quickstart Test (`quickstart.md`)

**Validation Workflow**:
```bash
# Step 1: Install dependencies
uv sync

# Step 2: Run existing CLI (baseline)
uv run python -m src.cli.evaluate output/submission.json --verbose

# Step 3: Import programmatic function (should not fail)
uv run python -c "from src.cli.evaluate import evaluate_submission; print('Import successful')"

# Step 4: Execute programmatically
uv run python -c "
from src.cli.evaluate import evaluate_submission
result = evaluate_submission('output/submission.json', verbose=True)
print(f'Score: {result.total_score}, Grade: {result.grade}')
assert result.success
"

# Step 5: Verify CLI still works identically
uv run python -m src.cli.evaluate output/submission.json --quiet
echo "Exit code: $?"  # Should be 0 or 2 (quality gate)

# Step 6: Run all tests
uv run pytest tests/contract/ tests/integration/test_evidence_path_consistency.py -v

# Success criteria:
# - All imports succeed
# - Programmatic execution returns EvaluationResult with expected fields
# - CLI behavior unchanged (same output files, exit codes)
# - Integration tests pass
```

### 6. Update Agent Context

**Action**: Run `.specify/scripts/bash/update-agent-context.sh claude`

**Expected Updates** to `AGENTS.md`:
- Add section on programmatic evaluation API
- Document exception types for error handling
- Note logging module usage for verbose/quiet modes
- Update recent changes (last 3):
  1. Unified toolchain health check layer (existing)
  2. Mock elimination MVP (existing)
  3. **NEW**: Programmatic CLI evaluation entry point (this feature)

**Phase 1 Output**:
- ✅ data-model.md (exception types, return objects)
- ✅ contracts/programmatic_api.py (function signature)
- ✅ contracts/exception_types.py (exception contracts)
- ✅ contracts/return_objects.py (return object schemas)
- ✅ tests/contract/test_*.py (8 contract tests, initially failing)
- ✅ quickstart.md (validation workflow)
- ✅ AGENTS.md (incremental update)

## Constitution Check (Post-Design)

*Re-evaluation after Phase 1 design completion*

### I. UV-Based Dependency Management ✅ PASS
- **Status**: Still compliant
- **Evidence**: Design uses only stdlib logging, no new dependencies added to pyproject.toml

### II. KISS Principle ✅ PASS
- **Status**: Design maintains simplicity
- **Evidence**:
  - **Fail-fast exceptions**: 3 exception types (QualityGateException, EvaluationFileSystemError, plus stdlib exceptions)
  - **Simple return objects**: 2 Pydantic models (ValidationResult, EvaluationResult) with flat structure
  - **No abstraction layers**: Direct function extraction, Click command delegates via single function call
  - **No complex patterns**: No factories, builders, or strategy patterns
- **Complexity Score**: 3 exception types + 2 return types = 5 new types (acceptable for clear error handling)

### III. Transparent Change Communication ✅ PASS
- **Status**: Compliant
- **Evidence**:
  - Design decisions documented (why exceptions vs sys.exit, why logging vs click.echo)
  - Contracts clearly specify inputs, outputs, and exception conditions
  - Quickstart demonstrates both old (CLI) and new (programmatic) usage

**Post-Design Constitution Check Result**: ✅ **PASS** - Proceed to Phase 2 planning

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **From Phase 1 Contracts** (contracts/):
   - Each contract test → contract test implementation task [P]
   - Exception contracts → exception class creation tasks [P]
   - Return object contracts → Pydantic model creation tasks [P]

2. **From Data Model** (data-model.md):
   - QualityGateException class → implementation task
   - EvaluationFileSystemError class → implementation task
   - ValidationResult model → implementation task
   - EvaluationResult model → implementation task

3. **From Quickstart** (quickstart.md):
   - Each validation step → integration test task
   - Import test → test_evidence_path_consistency.py update
   - CLI backward compat → regression test suite

4. **Core Extraction**:
   - Extract evaluate_submission() function from Click command
   - Replace sys.exit() with exceptions
   - Replace click.echo() with logging
   - Update Click command to delegate
   - Add logging configuration

**Ordering Strategy**:

**Phase A: Models & Contracts** [All Parallel]
1. [P] Create QualityGateException in src/cli/exceptions.py
2. [P] Create EvaluationFileSystemError in src/cli/exceptions.py
3. [P] Create ValidationResult Pydantic model in src/cli/models.py
4. [P] Create EvaluationResult Pydantic model in src/cli/models.py
5. [P] Write contract test: test_exception_contracts.py

**Phase B: Core Extraction** [Sequential - depends on Phase A]
6. Extract evaluate_submission() function (logic only, no CLI integration yet)
7. Replace sys.exit() calls with typed exceptions
8. Replace click.echo() calls with logging.logger calls
9. Add return object construction (ValidationResult/EvaluationResult)
10. Write unit tests for evaluate_submission() in test_evaluate_submission.py

**Phase C: CLI Integration** [Sequential - depends on Phase B]
11. Update Click command to delegate to evaluate_submission()
12. Add exception → sys.exit() translation in Click command
13. Add logging → click.echo() bridge for CLI output
14. Write CLI backward compatibility tests

**Phase D: Integration Tests** [Parallel - depends on Phase C]
15. [P] Update test_evidence_path_consistency.py to import evaluate_submission
16. [P] Write test_programmatic_workflow.py (happy path)
17. [P] Write test_programmatic_workflow.py (exception paths)
18. [P] Write test_cli_backward_compat.py (output identity tests)

**Phase E: Validation** [Sequential - depends on Phase D]
19. Execute quickstart.md validation workflow
20. Run full test suite (contract + unit + integration)
21. Verify CLI behavior unchanged (manual smoke test)

**Estimated Output**: **21 numbered, dependency-ordered tasks** in tasks.md

**Parallelization**:
- Phase A: 5 tasks [P] (independent files)
- Phase D: 4 tasks [P] (independent test files)
- Total parallel opportunities: 9/21 tasks (43%)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md with 21 tasks)
**Phase 4**: Implementation (execute tasks.md following TDD and constitutional principles)
**Phase 5**: Validation (run quickstart.md, verify all tests pass, CLI smoke test)

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: ✅ **NO VIOLATIONS** - Complexity tracking table not needed

This refactoring maintains constitutional compliance:
- UV dependency management: No new dependencies
- KISS principle: Simple extraction, fail-fast exceptions, flat data structures
- Transparent communication: Clear contracts, documented rationale, quickstart validation

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - SKIPPED (refactoring task)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (technical context fully determined)
- [x] Complexity deviations documented (N/A - no violations)

---

`★ Insight ─────────────────────────────────────`

**1. Refactoring as Zero-Research Task**
This plan demonstrates an important pattern: refactoring tasks require no research phase when the codebase is mature and well-understood. The technical decisions are already made (Python, Click, Pydantic), and we're just reorganizing existing code. This saves significant planning time compared to greenfield features.

**2. Exception Design as Architecture Clarification**
The clarification process (5 questions) directly translated into the exception hierarchy design. Q1 (quality gate) → QualityGateException, Q2 (filesystem errors) → EvaluationFileSystemError. This shows how spec clarifications can pre-solve implementation design decisions, reducing planning-phase ambiguity.

**3. TDD Task Ordering with Parallel Optimization**
The 21-task breakdown follows strict TDD (tests before implementation) while maximizing parallelization (9/21 tasks marked [P]). Phase A creates all models in parallel, Phase D runs all integration tests in parallel. This balances dependency constraints with execution speed—a key pattern for larger refactorings.

`─────────────────────────────────────────────────`

---

*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
