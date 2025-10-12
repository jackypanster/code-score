# Tasks: Programmatic CLI Evaluation Entry Point

**Feature Branch**: `003-tests-integration-test`
**Input**: Design documents from `/Users/user/workspace/code-score/specs/003-tests-integration-test/`
**Prerequisites**: plan.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

---

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Tech stack: Python 3.11+, Click 8.1+, Pydantic 2.5+, pytest 8.4+
   → ✅ Structure: Single project (src/, tests/)
2. Load optional design documents:
   → ✅ data-model.md: 2 exceptions + 2 return objects
   → ✅ contracts/: 3 contract files (API, exceptions, return objects)
   → ⏭️ research.md: SKIPPED (refactoring task)
3. Generate tasks by category:
   → Setup: Dependencies already installed (UV)
   → Tests: 3 contract test files, 3 integration test files
   → Core: 2 exception classes, 2 Pydantic models, function extraction
   → Integration: CLI delegation, logging configuration
   → Polish: Unit tests, quickstart validation
4. Apply task rules:
   → Exception classes: Different files → [P]
   → Models: Different files → [P]
   → Contract tests: Different files → [P]
   → Function extraction: Same file → sequential
5. Number tasks sequentially (T001-T021)
6. Dependency graph generated
7. Parallel execution examples provided
8. Validation:
   → ✅ All 3 contracts have tests
   → ✅ All 4 models have creation tasks
   → ✅ All tests before implementation
9. Return: SUCCESS (21 tasks ready for execution)
```

---

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no shared dependencies)
- All file paths are absolute or relative to repository root
- Tasks follow strict TDD ordering (tests before implementation)

---

## Phase 3.1: Setup

**Note**: Dependencies already installed via UV. No setup tasks needed.

---

## Phase 3.2: Models & Exception Classes [ALL PARALLEL]

**CRITICAL: Create exception classes and return models FIRST**

These tasks are all independent (different files) and can run in parallel:

- [x] **T001** [P] Create `QualityGateException` class in `src/cli/exceptions.py`
  - **File**: `src/cli/exceptions.py` (NEW) ✅ CREATED
  - **Contract**: `specs/003-tests-integration-test/contracts/exception_types.py`
  - **Fields**: `score: float`, `threshold: float`, `evaluation_result: EvaluationResult`
  - **Inherits**: `Exception`
  - **Constructor**: Accept score, threshold, evaluation_result, optional message
  - **Repr**: Include score and threshold in string representation

- [x] **T002** [P] Create `EvaluationFileSystemError` class in `src/cli/exceptions.py`
  - **File**: `src/cli/exceptions.py` (same file as T001, but can be done in same edit) ✅ CREATED
  - **Contract**: `specs/003-tests-integration-test/contracts/exception_types.py`
  - **Fields**: `operation: str`, `target_path: str`, `original_error: Exception`
  - **Inherits**: `Exception`
  - **Constructor**: Accept operation, target_path, original_error, optional message
  - **Repr**: Include operation and target_path in string representation

- [x] **T003** [P] Create `ValidationResult` Pydantic model in `src/cli/models.py`
  - **File**: `src/cli/models.py` (NEW) ✅ CREATED
  - **Contract**: `specs/003-tests-integration-test/contracts/return_objects.py`
  - **Base Class**: `pydantic.BaseModel`
  - **Fields**: `valid: bool`, `items_checked: List[str]`, `passed_checks: List[str]`, `warnings: List[str]`
  - **Validators**:
    - `passed_checks` must be subset of `items_checked`
    - If `valid=True`, `passed_checks` must equal `items_checked`

- [x] **T004** [P] Create `EvaluationResult` Pydantic model in `src/cli/models.py`
  - **File**: `src/cli/models.py` (same file as T003, but can be done in same edit) ✅ CREATED
  - **Contract**: `specs/003-tests-integration-test/contracts/return_objects.py`
  - **Base Class**: `pydantic.BaseModel`
  - **Fields**: `success: bool`, `total_score: float`, `max_possible_score: float`, `grade: str`, `generated_files: List[str]`, `evidence_files: Dict[str, str]`, `warnings: List[str]`
  - **Validators**:
    - `total_score` <= `max_possible_score`
    - `grade` matches score percentage (A/B/C/D/F)
  - **Property**: `score_percentage` returns `(total_score / max_possible_score) * 100`

---

## Phase 3.3: Contract Tests [ALL PARALLEL]

**CRITICAL: These tests MUST be written and MUST FAIL before Phase 3.4**

All contract tests are independent (different files):

- [x] **T005** [P] Contract test for exception types in `tests/contract/test_exception_contracts.py`
  - **File**: `tests/contract/test_exception_contracts.py` (NEW) ✅ CREATED
  - **Contract**: `specs/003-tests-integration-test/contracts/exception_types.py`
  - **Tests**:
    - `test_quality_gate_exception_structure()`: Verify QualityGateException has score, threshold, evaluation_result attributes
    - `test_quality_gate_exception_inheritance()`: Verify inherits from Exception
    - `test_filesystem_error_structure()`: Verify EvaluationFileSystemError has operation, target_path, original_error
    - `test_filesystem_error_inheritance()`: Verify inherits from Exception
  - **Expected**: Tests should PASS after T001-T002 complete

- [x] **T006** [P] Contract test for return objects in `tests/contract/test_return_objects_contract.py`
  - **File**: `tests/contract/test_return_objects_contract.py` (NEW) ✅ CREATED
  - **Contract**: `specs/003-tests-integration-test/contracts/return_objects.py`
  - **Tests**:
    - `test_validation_result_structure()`: Verify ValidationResult fields exist
    - `test_validation_result_validators()`: Test passed_checks subset validation
    - `test_evaluation_result_structure()`: Verify EvaluationResult fields exist
    - `test_evaluation_result_grade_validation()`: Test grade matches score percentage
  - **Expected**: Tests should PASS after T003-T004 complete

- [x] **T007** [P] Contract test for programmatic API in `tests/contract/test_programmatic_api_contract.py`
  - **File**: `tests/contract/test_programmatic_api_contract.py` (NEW) ✅ CREATED
  - **Contract**: `specs/003-tests-integration-test/contracts/programmatic_api.py`
  - **Tests**:
    - `test_evaluate_submission_function_exists()`: Verify function can be imported
    - `test_function_signature()`: Verify signature matches contract
    - `test_validate_only_returns_validation_result()`: Type check return value
    - `test_normal_mode_returns_evaluation_result()`: Type check return value
  - **Expected**: Tests should FAIL until T008-T011 complete
  - **Note**: May need mocking for file I/O tests

---

## Phase 3.4: Core Function Extraction [SEQUENTIAL]

**CRITICAL: These tasks modify the same file (`src/cli/evaluate.py`) and MUST be done sequentially**

- [x] **T008** Extract `evaluate_submission()` function from Click command in `src/cli/evaluate.py`
  - **File**: `src/cli/evaluate.py` (MODIFIED) ✅ COMPLETED
  - **Action**: Copy all logic from `evaluate()` Click command into new `evaluate_submission()` function
  - **Signature**: Match contract in `specs/003-tests-integration-test/contracts/programmatic_api.py`
  - **Parameters**: `submission_file`, `output_dir`, `format`, `checklist_config`, `evidence_dir`, `validate_only`, `verbose`, `quiet`
  - **Returns**: `ValidationResult | EvaluationResult` (from `src.cli.models`)
  - **DO NOT**: Remove sys.exit() or click.echo() yet (next tasks)
  - **DO NOT**: Update Click command yet (later task)
  - **Status**: Function exists but still uses sys.exit/click.echo

- [x] **T009** Replace `sys.exit()` calls with typed exceptions in `evaluate_submission()` function
  - **File**: `src/cli/evaluate.py` (MODIFIED)
  - **Action**: Replace all `sys.exit()` calls in `evaluate_submission()` with appropriate exceptions:
    - `sys.exit(1)` for missing files → `raise FileNotFoundError(f"File not found: {path}")`
    - `sys.exit(1)` for invalid JSON → `raise ValueError(f"Invalid JSON: {error}")`
    - `sys.exit(2)` for quality gate → `raise QualityGateException(score, 30.0, evaluation_result)`
    - Filesystem errors → `raise EvaluationFileSystemError(operation, path, original_error)`
  - **Import**: Add `from .exceptions import QualityGateException, EvaluationFileSystemError`
  - **Wrap**: Try-except around `output_dir.mkdir()`, `evidence_tracker.save_evidence_files()`, file writes

- [x] **T010** Replace `click.echo()` calls with Python logging in `evaluate_submission()` function
  - **File**: `src/cli/evaluate.py` (MODIFIED)
  - **Action**: Replace all `click.echo()` with `logger.info()`, `logger.debug()`, `logger.warning()`
  - **Add**: `import logging` at top, `logger = logging.getLogger(__name__)`
  - **Mapping**:
    - `click.echo()` with `verbose=True` → `logger.debug()`
    - Normal `click.echo()` → `logger.info()`
    - `click.echo(err=True)` → `logger.error()` or `raise Exception()`
  - **Logging levels**:
    - If `verbose=True`: Configure `logger.setLevel(logging.DEBUG)`
    - If `quiet=True`: Configure `logger.setLevel(logging.WARNING)`
    - Normal mode: `logger.setLevel(logging.INFO)`

- [x] **T011** Add return object construction in `evaluate_submission()` function
  - **File**: `src/cli/evaluate.py` (MODIFIED)
  - **Action**: Construct and return appropriate return objects
  - **Validate-only mode**: Return `ValidationResult(valid=True, items_checked=[...], passed_checks=[...], warnings=[])`
    - Items checked: `["submission_structure", "checklist_config", "required_sections"]`
  - **Normal mode**: Return `EvaluationResult(success=True, total_score=..., max_possible_score=..., grade=..., generated_files=[...], evidence_files={...}, warnings=[...])`
    - Get score from `evaluation_result.total_score` and `evaluation_result.max_possible_score`
    - Calculate grade using existing `get_letter_grade()` helper
    - Collect `generated_files` list (absolute paths)
    - Get `evidence_files` from `evidence_tracker`
  - **Import**: Add `from .models import ValidationResult, EvaluationResult`
  - **Remove**: Early returns (convert to return statements with objects)

---

## Phase 3.5: CLI Integration [SEQUENTIAL]

**CRITICAL: Update Click command to delegate to programmatic function**

- [x] **T012** Update Click `evaluate()` command to delegate to `evaluate_submission()` function
  - **File**: `src/cli/evaluate.py` (MODIFIED)
  - **Action**: Replace all logic in Click command with single call to `evaluate_submission()`
  - **Delegation**:
    ```python
    result = evaluate_submission(
        submission_file=submission_file,
        output_dir=output_dir,
        format=format,
        checklist_config=checklist_config,
        evidence_dir=evidence_dir,
        validate_only=validate_only,
        verbose=verbose,
        quiet=quiet
    )
    ```
  - **Keep**: Click decorators and parameter definitions
  - **Keep**: `get_letter_grade()` helper function (used by both)

- [x] **T013** Add exception → `sys.exit()` translation in Click command
  - **File**: `src/cli/evaluate.py` (MODIFIED)
  - **Action**: Wrap `evaluate_submission()` call in try-except to translate exceptions back to sys.exit() for CLI
  - **Exception Handling**:
    - `except FileNotFoundError as e`: `click.echo(f"❌ File not found: {e}", err=True); sys.exit(1)`
    - `except ValueError as e`: `click.echo(f"❌ Validation error: {e}", err=True); sys.exit(1)`
    - `except QualityGateException as e`: `click.echo(f"⚠️ Quality gate: Score {e.score:.1f}% below {e.threshold:.1f}%", err=True); sys.exit(2)`
    - `except EvaluationFileSystemError as e`: `click.echo(f"❌ Filesystem error: {e.operation} failed for {e.target_path}", err=True); sys.exit(1)`
    - `except Exception as e`: `click.echo(f"❌ Unexpected error: {e}", err=True); sys.exit(1)`

- [x] **T014** Add logging → `click.echo()` bridge for CLI output
  - **File**: `src/cli/evaluate.py` (MODIFIED)
  - **Action**: Configure logging to output via click.echo() when in CLI mode
  - **Logging Handler**:
    ```python
    class ClickHandler(logging.Handler):
        def emit(self, record):
            click.echo(self.format(record), err=(record.levelno >= logging.WARNING))

    logger = logging.getLogger("src.cli.evaluate")
    handler = ClickHandler()
    logger.addHandler(handler)
    ```
  - **Alternative**: Keep logging as-is (stdout/stderr) since CLI can use default logging
  - **Note**: This ensures CLI output still goes through click.echo() for consistent formatting

- [x] **T015** Add CLI output generation from return object
  - **File**: `src/cli/evaluate.py` (MODIFIED)
  - **Action**: After `evaluate_submission()` succeeds, generate CLI output from return object
  - **Validate-only mode**: `click.echo("✅ Submission file validation passed")` if `result.valid`
  - **Normal mode**: Generate summary output using `result.total_score`, `result.grade`, `result.generated_files`
    ```python
    click.echo(f"\n🎉 Evaluation completed successfully!")
    click.echo(f"📊 Score: {result.total_score:.1f}/{result.max_possible_score} ({result.score_percentage:.1f}%)")
    click.echo(f"\n📁 Generated Files:")
    for file_path in result.generated_files:
        click.echo(f"   • {file_path}")
    ```
  - **Preserve**: Existing CLI output format for backward compatibility

---

## Phase 3.6: Integration Tests [ALL PARALLEL]

**CRITICAL: Verify both programmatic API and CLI backward compatibility**

- [x] **T016** [P] Update `test_evidence_path_consistency.py` to import `evaluate_submission()`
  - **File**: `tests/integration/test_evidence_path_consistency.py` (MODIFIED)
  - **Action**: Replace any CLI subprocess calls with direct `evaluate_submission()` imports
  - **Test**:
    ```python
    from src.cli.evaluate import evaluate_submission  # Should not raise ImportError

    def test_import_evaluate_submission():
        # Test passes if import succeeds
        assert callable(evaluate_submission)
    ```

- [x] **T017** [P] Write programmatic workflow tests in `tests/integration/test_programmatic_workflow.py`
  - **File**: `tests/integration/test_programmatic_workflow.py` (NEW)
  - **Tests**:
    - `test_programmatic_execution_normal_mode()`: Call `evaluate_submission()`, verify EvaluationResult returned
    - `test_programmatic_execution_validate_only()`: Call with `validate_only=True`, verify ValidationResult
    - `test_quality_gate_exception_raised()`: Use low-score submission, catch QualityGateException
    - `test_filesystem_error_raised()`: Use read-only output_dir, catch EvaluationFileSystemError
  - **Fixtures**: Use real submission.json files from `output/` directory
  - **Assertions**: Check return object types, field values, exception attributes

- [x] **T018** [P] Write CLI backward compatibility tests in `tests/integration/test_cli_backward_compat.py`
  - **File**: `tests/integration/test_cli_backward_compat.py` (NEW)
  - **Tests**:
    - `test_cli_command_still_works()`: Run `uv run python -m src.cli.evaluate output/submission.json`, check exit code
    - `test_cli_output_files_generated()`: Verify `score_input.json`, `evaluation_report.md` created
    - `test_cli_output_format_unchanged()`: Compare CLI output format with baseline
    - `test_cli_quality_gate_exit_code()`: Verify exit code 2 for low scores
  - **Method**: Use `subprocess.run()` to call CLI
  - **Assertions**: Check exit codes, file existence, output format

---

## Phase 3.7: Unit Tests [ALL PARALLEL]

**Test individual function behavior in isolation**

- [x] **T019** [P] Write unit tests for `evaluate_submission()` in `tests/unit/test_evaluate_submission.py`
  - **File**: `tests/unit/test_evaluate_submission.py` (NEW)
  - **Tests**:
    - `test_missing_submission_file_raises_file_not_found()`: Mock missing file
    - `test_invalid_json_raises_value_error()`: Mock invalid JSON
    - `test_missing_required_sections_raises_value_error()`: Mock incomplete submission
    - `test_validate_only_returns_validation_result()`: Test validate-only path
    - `test_normal_mode_returns_evaluation_result()`: Test normal path
    - `test_quality_gate_failure_raises_exception()`: Mock low score
  - **Mocking**: Mock file I/O, ChecklistEvaluator, EvidenceTracker, ScoringMapper
  - **Focus**: Behavior verification, not implementation details

- [x] **T020** [P] Write unit tests for custom exceptions in `tests/unit/test_custom_exceptions.py`
  - **File**: `tests/unit/test_custom_exceptions.py` (NEW)
  - **Tests**:
    - `test_quality_gate_exception_attributes()`: Verify score, threshold, evaluation_result accessible
    - `test_quality_gate_exception_message()`: Verify auto-generated message format
    - `test_filesystem_error_attributes()`: Verify operation, target_path, original_error accessible
    - `test_filesystem_error_message()`: Verify auto-generated message format
    - `test_exceptions_inherit_from_exception()`: Verify inheritance chain
  - **No mocking needed**: Direct exception instantiation tests

---

## Phase 3.8: Validation & Polish

**CRITICAL: Execute quickstart.md and verify all acceptance criteria**

- [x] **T021** Execute `quickstart.md` validation workflow and verify all 10 steps pass
  - **File**: `specs/003-tests-integration-test/quickstart.md`
  - **Action**: Run each step manually and verify success criteria
  - **Steps**:
    1. ✅ Install dependencies (`uv sync`)
    2. ✅ Run existing CLI (baseline)
    3. ✅ Import programmatic function
    4. ✅ Execute programmatically (normal mode)
    5. ✅ Execute programmatically (validate-only mode)
    6. ✅ Verify CLI still works identically
    7. ✅ Test exception handling (quality gate)
    8. ✅ Test exception handling (filesystem error)
    9. ✅ Run all tests (contract: 138 passed, integration: 5 passed, programmatic: 19 passed)
    10. ✅ Verify output identity (CLI vs programmatic)
  - **Success**: All 10 steps pass without errors
  - **Completion**: 2025-10-12 - All quickstart validation steps completed successfully

---

## Dependencies

### Sequential Dependencies
- **T001-T004** BEFORE T005-T007 (models/exceptions needed for contract tests)
- **T005-T007** BEFORE T008 (contract tests define what to implement)
- **T008** BEFORE T009 (function must exist before modifying it)
- **T009** BEFORE T010 (exception handling before logging)
- **T010** BEFORE T011 (logging before return objects)
- **T011** BEFORE T012 (function complete before CLI delegation)
- **T012** BEFORE T013 (delegation before exception translation)
- **T013** BEFORE T014 (exception handling before logging bridge)
- **T014** BEFORE T015 (logging configured before output generation)
- **T015** BEFORE T016-T018 (implementation complete before integration tests)
- **T016-T018** BEFORE T021 (integration tests before quickstart validation)

### Parallel Groups
- **Group A (T001-T004)**: All models and exceptions (different concepts, can be parallel)
- **Group B (T005-T007)**: All contract tests (different files)
- **Group C (T016-T018)**: All integration tests (different files)
- **Group D (T019-T020)**: All unit tests (different files)

### Blocking Relationships
- Core extraction (T008-T011) blocks everything else (critical path)
- CLI integration (T012-T015) blocks integration tests
- Integration tests (T016-T020) block validation (T021)

---

## Parallel Execution Examples

### Example 1: Launch Group A (Models & Exceptions)
```bash
# All 4 tasks can run simultaneously:
Task: "Create QualityGateException in src/cli/exceptions.py per contract"
Task: "Create EvaluationFileSystemError in src/cli/exceptions.py per contract"
Task: "Create ValidationResult Pydantic model in src/cli/models.py per contract"
Task: "Create EvaluationResult Pydantic model in src/cli/models.py per contract"

# Expected: 4 parallel executions, ~2-3 minutes total
```

### Example 2: Launch Group B (Contract Tests)
```bash
# After Group A completes, run all contract tests:
Task: "Write contract tests for exception types in tests/contract/test_exception_contracts.py"
Task: "Write contract tests for return objects in tests/contract/test_return_objects_contract.py"
Task: "Write contract tests for programmatic API in tests/contract/test_programmatic_api_contract.py"

# Expected: 3 parallel executions, ~3-4 minutes total
# Tests should PASS for exceptions/models, FAIL for API (not implemented yet)
```

### Example 3: Launch Group C (Integration Tests)
```bash
# After T015 completes, run all integration tests:
Task: "Update test_evidence_path_consistency.py to import evaluate_submission()"
Task: "Write programmatic workflow tests in tests/integration/test_programmatic_workflow.py"
Task: "Write CLI backward compatibility tests in tests/integration/test_cli_backward_compat.py"

# Expected: 3 parallel executions, ~4-5 minutes total
# All tests should PASS after implementation complete
```

### Example 4: Launch Group D (Unit Tests)
```bash
# Can run anytime after T011 (function extraction complete):
Task: "Write unit tests for evaluate_submission() in tests/unit/test_evaluate_submission.py"
Task: "Write unit tests for custom exceptions in tests/unit/test_custom_exceptions.py"

# Expected: 2 parallel executions, ~3-4 minutes total
```

---

## Validation Checklist

**GATE: Verify before marking tasks.md as complete**

- [x] All 3 contracts have corresponding tests (T005-T007)
- [x] All 4 models/exceptions have creation tasks (T001-T004)
- [x] All tests come before implementation (T005-T007 before T008-T015)
- [x] Parallel tasks are truly independent (different files, no dependencies)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task in same group
- [x] TDD order maintained (contract tests → implementation → integration tests)
- [x] Quickstart validation included (T021)

---

## Progress Tracking

**Recommended Order of Execution**:
1. Complete Group A (T001-T004) in parallel → ~2-3 minutes
2. Complete Group B (T005-T007) in parallel → ~3-4 minutes
3. **CRITICAL PATH**: Complete T008-T015 sequentially → ~60-90 minutes (8 tasks)
4. Complete Group C (T016-T018) in parallel → ~4-5 minutes
5. Complete Group D (T019-T020) in parallel → ~3-4 minutes
6. Execute T021 (quickstart validation) → ~10 minutes

**Total Estimated Time**: ~90-120 minutes (1.5-2 hours)

**Parallelization Savings**:
- Without parallelization: ~150-180 minutes
- With parallelization: ~90-120 minutes
- **Time Saved**: ~40-50% reduction

---

## Notes

- **[P] tasks**: Different files, no dependencies, safe to parallelize
- **Sequential tasks (T008-T015)**: Same file `src/cli/evaluate.py`, MUST be sequential
- **TDD Critical**: Contract tests (T005-T007) MUST FAIL before implementation starts
- **Backward Compatibility**: T015 and T018 verify CLI behavior unchanged
- **Quickstart Validation**: T021 is the final acceptance gate

**Commit Strategy**:
- Commit after each group completes (A, B, C, D)
- Commit after each sequential task in critical path (T008-T015)
- Final commit after T021 quickstart validation passes

---

**Tasks Ready for Execution** - Begin with Group A (T001-T004) in parallel!
