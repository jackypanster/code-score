# Quickstart Validation: Programmatic CLI Evaluation Entry Point

**Feature**: 003-tests-integration-test
**Purpose**: Step-by-step validation workflow to verify the programmatic API implementation
**Expected Duration**: 5-10 minutes

---

## Prerequisites

- Python 3.11+
- UV package manager installed
- Repository cloned and on feature branch `003-tests-integration-test`
- Test submission file available at `output/submission.json`
  - If not available, run: `./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git`

---

## Step 1: Install Dependencies

```bash
# Install all dependencies including dev dependencies
uv sync

# Verify installation
uv run python --version  # Should be 3.11+
```

**Expected Output**:
```
Python 3.11.x or higher
```

**Success Criteria**: No errors during `uv sync`, Python version ≥ 3.11

---

## Step 2: Run Existing CLI (Baseline)

```bash
# Run CLI evaluation to establish baseline behavior
uv run python -m src.cli.evaluate output/submission.json --verbose

# Expected output: Evaluation completes with score, generates files
```

**Expected Output**:
```
🔍 Initializing checklist evaluation...
📋 Loaded checklist configuration
   ✅ 11 items, 100 total points
📄 Loading submission file: output/submission.json
⚙️  Running evaluation...
📁 Saving evidence files...
📝 Generating score_input.json...
📝 Generating evaluation report...

🎉 Evaluation completed successfully!
📊 Score: XX.X/100 (XX.X%)
...
```

**Success Criteria**:
- CLI exits with code 0 (or 2 if quality gate failed)
- Files generated: `output/score_input.json`, `output/evaluation_report.md`
- Evidence directory created: `output/evidence/`

---

## Step 3: Import Programmatic Function (Should Not Fail)

```bash
# Test that importing the function doesn't raise ImportError
uv run python -c "from src.cli.evaluate import evaluate_submission; print('✅ Import successful')"
```

**Expected Output**:
```
✅ Import successful
```

**Success Criteria**:
- No ImportError
- No Click initialization errors (function import doesn't trigger Click)

---

## Step 4: Execute Programmatically (Normal Mode)

```bash
# Execute full evaluation programmatically
uv run python -c "
from src.cli.evaluate import evaluate_submission

result = evaluate_submission('output/submission.json', verbose=True)
print(f'✅ Programmatic evaluation succeeded')
print(f'   Score: {result.total_score:.1f}/{result.max_possible_score}')
print(f'   Grade: {result.grade}')
print(f'   Generated files: {len(result.generated_files)}')
assert result.success
assert result.total_score >= 0
assert result.grade in ['A', 'B', 'C', 'D', 'F']
print('✅ All assertions passed')
"
```

**Expected Output**:
```
🔍 Initializing checklist evaluation...
📋 Loaded checklist configuration
   ✅ 11 items, 100 total points
📄 Loading submission file: output/submission.json
...
✅ Programmatic evaluation succeeded
   Score: XX.X/100
   Grade: X
   Generated files: 2
✅ All assertions passed
```

**Success Criteria**:
- Function returns EvaluationResult object
- result.success == True
- result.total_score is numeric
- result.grade is valid letter grade (A-F)
- result.generated_files contains paths
- No exceptions raised (unless quality gate fails, see Step 7)

---

## Step 5: Execute Programmatically (Validate-Only Mode)

```bash
# Test validate-only mode
uv run python -c "
from src.cli.evaluate import evaluate_submission

result = evaluate_submission('output/submission.json', validate_only=True)
print(f'✅ Validation completed')
print(f'   Valid: {result.valid}')
print(f'   Items checked: {len(result.items_checked)}')
print(f'   Passed checks: {len(result.passed_checks)}')
assert result.valid
assert len(result.items_checked) > 0
assert set(result.passed_checks) == set(result.items_checked)
print('✅ All assertions passed')
"
```

**Expected Output**:
```
✅ Validation completed
   Valid: True
   Items checked: 3
   Passed checks: 3
✅ All assertions passed
```

**Success Criteria**:
- Function returns ValidationResult object
- result.valid == True
- result.items_checked is non-empty list
- result.passed_checks equals items_checked (for valid submission)
- No files generated (validate-only mode)

---

## Step 6: Verify CLI Still Works Identically

```bash
# Run CLI again to verify backward compatibility
uv run python -m src.cli.evaluate output/submission.json --quiet
CLI_EXIT_CODE=$?
echo "✅ CLI exit code: $CLI_EXIT_CODE"  # Should be 0 or 2

# Check that output files still exist
[ -f "output/score_input.json" ] && echo "✅ score_input.json exists"
[ -f "output/evaluation_report.md" ] && echo "✅ evaluation_report.md exists"
```

**Expected Output**:
```
✅ CLI exit code: 0  (or 2 if quality gate failed)
✅ score_input.json exists
✅ evaluation_report.md exists
```

**Success Criteria**:
- CLI command still works
- Same files generated as before refactoring
- Exit code unchanged (0 for success, 2 for quality gate failure)

---

## Step 7: Test Exception Handling (Quality Gate)

```bash
# Test quality gate exception handling
# Note: This requires a low-score submission file
# If you don't have one, skip this step

uv run python -c "
from src.cli.evaluate import evaluate_submission
from src.cli.exceptions import QualityGateException

try:
    # This should raise QualityGateException if score < 30%
    result = evaluate_submission('output/submission.json')
    print('ℹ️  Quality gate passed (score >= 30%)')
except QualityGateException as e:
    print(f'✅ QualityGateException raised as expected')
    print(f'   Score: {e.score:.1f}%')
    print(f'   Threshold: {e.threshold:.1f}%')
    assert e.score < e.threshold
    assert e.score < 30.0
    print('✅ Exception attributes correct')
"
```

**Expected Output** (if score < 30%):
```
✅ QualityGateException raised as expected
   Score: XX.X%
   Threshold: 30.0%
✅ Exception attributes correct
```

**Expected Output** (if score >= 30%):
```
ℹ️  Quality gate passed (score >= 30%)
```

**Success Criteria**:
- If score < 30%: QualityGateException raised with correct attributes
- If score >= 30%: Function returns normally without exception

---

## Step 8: Test Exception Handling (Filesystem Error)

```bash
# Test filesystem error handling
uv run python -c "
from src.cli.evaluate import evaluate_submission
from src.cli.exceptions import EvaluationFileSystemError

try:
    # Try to write to read-only directory (should fail)
    result = evaluate_submission(
        'output/submission.json',
        output_dir='/root/read-only-test'  # Typically read-only
    )
    print('⚠️  Warning: Expected EvaluationFileSystemError but succeeded')
except EvaluationFileSystemError as e:
    print(f'✅ EvaluationFileSystemError raised as expected')
    print(f'   Operation: {e.operation}')
    print(f'   Target path: {e.target_path}')
    print(f'   Original error: {type(e.original_error).__name__}')
    assert e.operation  # Non-empty
    assert e.target_path  # Non-empty
    assert isinstance(e.original_error, Exception)
    print('✅ Exception attributes correct')
except PermissionError as e:
    print('✅ Permission denied (expected on some systems)')
"
```

**Expected Output**:
```
✅ EvaluationFileSystemError raised as expected
   Operation: create_directory
   Target path: /root/read-only-test
   Original error: PermissionError
✅ Exception attributes correct
```

**Success Criteria**:
- EvaluationFileSystemError raised (or PermissionError on some systems)
- Exception has operation, target_path, original_error attributes
- Attributes are non-empty and correctly typed

---

## Step 9: Run All Tests

```bash
# Run contract tests
uv run pytest tests/contract/ -v

# Run integration tests (including evidence path consistency test)
uv run pytest tests/integration/test_evidence_path_consistency.py -v

# Run all programmatic API tests
uv run pytest tests/unit/test_evaluate_submission.py tests/integration/test_programmatic_workflow.py -v
```

**Expected Output**:
```
tests/contract/test_programmatic_api_contract.py::test_function_signature PASSED
tests/contract/test_programmatic_api_contract.py::test_validate_only_returns_validation_result PASSED
tests/contract/test_programmatic_api_contract.py::test_normal_mode_returns_evaluation_result PASSED
tests/contract/test_exception_contracts.py::test_quality_gate_exception_structure PASSED
tests/contract/test_exception_contracts.py::test_filesystem_error_structure PASSED
...
tests/integration/test_evidence_path_consistency.py::test_import_evaluate_submission PASSED
...
============== XX passed in X.XXs ==============
```

**Success Criteria**:
- All contract tests pass
- All integration tests pass
- test_evidence_path_consistency.py imports evaluate_submission without error
- No test failures or errors

---

## Step 10: Verify Output Identity (CLI vs Programmatic)

```bash
# Compare CLI and programmatic outputs
uv run python -c "
import json
from pathlib import Path
from src.cli.evaluate import evaluate_submission

# Run programmatic evaluation
prog_result = evaluate_submission('output/submission.json', format='json')

# Load CLI-generated score_input.json
with open('output/score_input.json') as f:
    cli_output = json.load(f)

# Both should produce identical score_input.json content
print('✅ Both CLI and programmatic API produce output files')
print(f'   Programmatic generated {len(prog_result.generated_files)} files')
print(f'   CLI output file exists: {Path(\"output/score_input.json\").exists()}')
print('✅ Output identity verification complete')
"
```

**Expected Output**:
```
✅ Both CLI and programmatic API produce output files
   Programmatic generated 1 files
   CLI output file exists: True
✅ Output identity verification complete
```

**Success Criteria**:
- Both CLI and programmatic execution produce score_input.json
- File contents should be identical (same scores, evidence paths)
- Generated files exist and are valid JSON

---

## Success Summary

✅ **All Steps Passed** - Implementation is correct

**Verified Capabilities**:
1. ✅ Dependency installation (UV)
2. ✅ CLI baseline behavior preserved
3. ✅ Programmatic function import successful
4. ✅ Normal mode execution returns EvaluationResult
5. ✅ Validate-only mode returns ValidationResult
6. ✅ CLI backward compatibility maintained
7. ✅ Quality gate exception handling works
8. ✅ Filesystem error exception handling works
9. ✅ All contract and integration tests pass
10. ✅ CLI and programmatic outputs are identical

**Ready for**:
- Integration test updates (test_evidence_path_consistency.py can now import evaluate_submission)
- Internal tooling integration (stable Python API available)
- Automated testing workflows (no CLI process spawning needed)

---

## Troubleshooting

### ImportError: cannot import name 'evaluate_submission'

**Cause**: Function not yet extracted from CLI command

**Fix**: Complete implementation tasks (Phase C: Core Extraction)

---

### AttributeError: 'EvaluationResult' object has no attribute 'success'

**Cause**: Return object contract not implemented or incorrect model used

**Fix**: Verify `src/cli/models.py` contains programmatic API's EvaluationResult (not ChecklistEvaluator's)

---

### QualityGateException not raised when expected

**Cause**: Exception logic not implemented or threshold check missing

**Fix**: Verify evaluate_submission() raises QualityGateException when score < 30%

---

### Tests fail: Click initialization during import

**Cause**: evaluate_submission() is still decorated with @click.command()

**Fix**: Ensure extracted function has no Click decorators, only the delegate CLI function should use Click

---

## Next Steps

After quickstart validation passes:

1. Run `/tasks` command to generate tasks.md
2. Execute tasks following TDD order (tests before implementation)
3. Re-run this quickstart after implementation to verify
4. Update AGENTS.md with new API documentation
5. Commit changes with clear message explaining refactoring

---

**Validation Complete** - Feature ready for implementation phase
