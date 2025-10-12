# Data Model: Programmatic CLI Evaluation Entry Point

**Feature**: 003-tests-integration-test
**Created**: 2025-10-12
**Purpose**: Define exception types and return objects for the programmatic evaluation API

---

## Exception Types

### QualityGateException

**Purpose**: Signals that evaluation completed successfully but failed the quality gate threshold (score < 30%).

**Classification**: Business logic failure (not a system error)

**Attributes**:
- `score: float` - The actual evaluation score achieved (e.g., 25.5)
- `threshold: float` - The quality gate threshold that was not met (30.0)
- `evaluation_result: EvaluationResult` - Complete evaluation details from ChecklistEvaluator

**Usage Example**:
```python
try:
    result = evaluate_submission("submission.json")
except QualityGateException as e:
    print(f"Quality gate failed: {e.score:.1f} < {e.threshold:.1f}")
    # Access full evaluation details
    for item in e.evaluation_result.checklist_items:
        if item.evaluation_status == "unmet":
            print(f"  - Unmet: {item.description}")
```

**Inheritance**: `Exception` (base class)

**When Raised**: After successful evaluation when `evaluation_result.score_percentage < 30.0`

---

### EvaluationFileSystemError

**Purpose**: Signals filesystem operation failures during evaluation (directory creation, file writing).

**Classification**: Infrastructure failure

**Attributes**:
- `operation: str` - Description of the operation that failed (e.g., "create_directory", "write_file", "create_evidence_dir")
- `target_path: str` - Absolute path to the file/directory that failed
- `original_error: Exception` - The underlying OS exception (OSError, PermissionError, etc.)

**Usage Example**:
```python
try:
    result = evaluate_submission("submission.json", output_dir="/read-only/path")
except EvaluationFileSystemError as e:
    print(f"Filesystem error during {e.operation}: {e.target_path}")
    print(f"Original error: {e.original_error}")
    # Check if it's a permission issue
    if isinstance(e.original_error, PermissionError):
        print("Check directory permissions")
```

**Inheritance**: `Exception` (base class)

**When Raised**: When any filesystem operation fails (mkdir, file write, evidence directory creation)

**Wrapping Strategy**: Catches OSError, PermissionError, IOError and re-raises with context

---

## Return Objects

### ValidationResult

**Purpose**: Return value for `evaluate_submission()` when `validate_only=True`

**Type**: Pydantic BaseModel (for validation and serialization)

**Fields**:
- `valid: bool` - Overall validation result (True if all critical checks passed)
- `items_checked: List[str]` - List of validation items performed
  - Examples: `["submission_structure", "checklist_config", "required_sections"]`
- `passed_checks: List[str]` - Subset of `items_checked` that passed validation
- `warnings: List[str]` - Non-fatal validation warnings (empty list if no warnings)

**Example**:
```python
result = evaluate_submission("submission.json", validate_only=True)
# result.valid = True
# result.items_checked = ["submission_structure", "checklist_config", "required_sections"]
# result.passed_checks = ["submission_structure", "checklist_config", "required_sections"]
# result.warnings = []
```

**Validation Rules**:
- `passed_checks` MUST be a subset of `items_checked`
- If `valid == True`, then `passed_checks == items_checked`
- `warnings` may be non-empty even when `valid == True`

---

### EvaluationResult

**Purpose**: Return value for `evaluate_submission()` when `validate_only=False` (normal evaluation mode)

**Type**: Pydantic BaseModel

**Fields**:
- `success: bool` - Evaluation completed successfully (True unless quality gate failed, but note: quality gate failure raises exception instead)
- `total_score: float` - Actual score achieved (e.g., 75.5)
- `max_possible_score: float` - Maximum possible score from checklist (e.g., 100.0)
- `grade: str` - Letter grade A-F based on score percentage
  - A: ≥90%, B: ≥80%, C: ≥70%, D: ≥60%, F: <60%
- `generated_files: List[str]` - Absolute paths to generated output files
  - Examples: `["/path/to/output/score_input.json", "/path/to/output/evaluation_report.md"]`
- `evidence_files: Dict[str, str]` - Evidence file mapping (key: evidence type, value: absolute path)
  - Examples: `{"code_quality_lint": "/path/to/evidence/code_quality/lint_results.json"}`
- `warnings: List[str]` - Evaluation warnings from ChecklistEvaluator (empty if none)

**Example**:
```python
result = evaluate_submission("submission.json", format="both")
# result.success = True
# result.total_score = 85.5
# result.max_possible_score = 100.0
# result.grade = "B"
# result.generated_files = ["/abs/path/output/score_input.json", "/abs/path/output/evaluation_report.md"]
# result.evidence_files = {"code_quality_lint": "/abs/path/evidence/code_quality/lint.json", ...}
# result.warnings = []
```

**Validation Rules**:
- `total_score` MUST be ≤ `max_possible_score`
- `grade` MUST match score percentage calculation
- `generated_files` MUST contain valid absolute paths
- All paths in `evidence_files` MUST exist at function return time

**Grade Calculation Logic** (matches existing `get_letter_grade()`):
```python
percentage = (total_score / max_possible_score) * 100
if percentage >= 90: grade = "A"
elif percentage >= 80: grade = "B"
elif percentage >= 70: grade = "C"
elif percentage >= 60: grade = "D"
else: grade = "F"
```

---

## Design Decisions

### Why Pydantic Models?
- **Validation**: Automatic field validation (e.g., `total_score <= max_possible_score`)
- **Serialization**: Easy JSON export for logging/debugging
- **Type Safety**: mypy can catch type errors at development time
- **Consistency**: Already using Pydantic in `src/metrics/models/`

### Why Separate Exception Types?
- **Caller Intent**: Quality gate failures may be expected behavior (e.g., automated PR checks), filesystem errors are unexpected
- **Error Handling Strategy**: Different exception types enable different recovery strategies
- **Transparency**: Clear exception names communicate failure modes without inspecting error messages

### Why Flat Structures?
- **KISS Principle**: No nested objects beyond existing types (EvaluationResult from ChecklistEvaluator)
- **Easy Testing**: Simple assertions in contract tests
- **Clear API**: Callers don't need to navigate deep object hierarchies

---

## Relationship to Existing Models

**Reused from `src/metrics/models/evaluation_result.py`**:
- `EvaluationResult` (from ChecklistEvaluator) - Embedded in QualityGateException
- `RepositoryInfo` - Not exposed in programmatic API return values (internal only)

**New Models** (this feature):
- `ValidationResult` - New for validate-only mode
- `EvaluationResult` (programmatic API) - New, different from ChecklistEvaluator's EvaluationResult
  - Simpler structure focused on caller needs (paths, score, grade)
  - Checklist's EvaluationResult is more detailed (item-by-item breakdown)

**Naming Collision Resolution**:
- Checklist's `EvaluationResult`: Keep in `src/metrics/models/evaluation_result.py`
- Programmatic API's `EvaluationResult`: Define in `src/cli/models.py`
- Import alias if needed: `from src.cli.models import EvaluationResult as ProgrammaticResult`

---

## Validation Checklist

- [x] All exception types inherit from Exception
- [x] All Pydantic models use `BaseModel`
- [x] Field types are concrete (no `Any` types)
- [x] Validation rules documented for complex relationships
- [x] Examples provided for all types
- [x] Design rationale documented
- [x] Relationship to existing models clarified
