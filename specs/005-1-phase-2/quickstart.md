# Quickstart: CI/CD Configuration Analysis

**Feature**: COD-9 Phase 2 - CI/CD Configuration Analysis for Test Evidence
**Purpose**: Validate implementation after development is complete
**Estimated Time**: 5-10 minutes

---

## Prerequisites

- ✅ Phase 1 (COD-8) static test infrastructure analyzer already implemented
- ✅ Python 3.11+ installed
- ✅ UV package manager installed
- ✅ Code Score repository cloned

---

## Quick Validation Steps

### 1. Install Dependencies
```bash
# Navigate to repository root
cd /path/to/code-score

# Install all dependencies (includes PyYAML for Phase 2)
uv sync

# Verify Python environment
uv run python --version  # Should show 3.11+
```

**Expected Output**: `Python 3.11.x` or higher

---

### 2. Run Contract Tests (JSON Schema Validation)

```bash
# Validate CIConfigResult JSON schema compliance
uv run pytest tests/contract/test_ci_config_result_schema.py -v

# Expected: All tests pass (validates schema structure)
```

**Expected Output**:
```
tests/contract/test_ci_config_result_schema.py::test_ci_config_result_schema_valid PASSED
tests/contract/test_ci_config_result_schema.py::test_ci_config_result_required_fields PASSED
tests/contract/test_ci_config_result_schema.py::test_ci_config_result_enum_validation PASSED
===================== 3 passed in 0.15s =====================
```

---

### 3. Run Unit Tests (Platform Parsers)

```bash
# Test GitHub Actions parser (most common CI platform)
uv run pytest tests/unit/test_github_actions_parser.py -v

# Test all 5 platform parsers
uv run pytest tests/unit/test_*_parser.py -v

# Expected: All parser tests pass
```

**Expected Output**:
```
tests/unit/test_github_actions_parser.py::test_parse_valid_workflow PASSED
tests/unit/test_github_actions_parser.py::test_detect_test_steps PASSED
tests/unit/test_github_actions_parser.py::test_detect_coverage_upload PASSED
tests/unit/test_gitlab_ci_parser.py::test_parse_valid_config PASSED
...
===================== 25 passed in 0.42s =====================
```

---

### 4. Run Integration Tests (End-to-End Workflow)

```bash
# Test complete CI analysis workflow with sample repositories
uv run pytest tests/integration/test_ci_analysis_workflow.py::test_github_actions_integration -v

# Expected: CI analysis runs successfully and produces valid results
```

**Expected Output**:
```
tests/integration/test_ci_analysis_workflow.py::test_github_actions_integration PASSED
tests/integration/test_ci_analysis_workflow.py::test_gitlab_ci_integration PASSED
tests/integration/test_ci_analysis_workflow.py::test_no_ci_configuration PASSED
tests/integration/test_ci_analysis_workflow.py::test_score_capping PASSED
===================== 4 passed in 1.23s =====================
```

---

### 5. Manual Smoke Test (Real Repository)

```bash
# Analyze a real repository with GitHub Actions (anthropic-sdk-python)
uv run python -m src.cli.main https://github.com/anthropics/anthropic-sdk-python --verbose

# Wait for analysis to complete (~30-60 seconds including cloning)
# Check output/submission.json for test_analysis section
```

**Expected Output in `output/submission.json`**:
```json
{
  "schema_version": "1.0.0",
  "repository": {
    "url": "https://github.com/anthropics/anthropic-sdk-python",
    "language": "Python"
  },
  "metrics": {
    "testing": {
      "test_analysis": {
        "static_infrastructure": {
          "test_files_detected": 43,
          "test_config_detected": true,
          "coverage_config_detected": false,
          "test_file_ratio": 0.107,
          "calculated_score": 15
        },
        "ci_configuration": {
          "platform": "github_actions",
          "config_file_path": ".github/workflows/test.yml",
          "has_test_steps": true,
          "test_commands": ["pytest --cov=anthropic"],
          "has_coverage_upload": true,
          "coverage_tools": ["codecov"],
          "test_job_count": 2,
          "calculated_score": 13,
          "parse_errors": []
        },
        "combined_score": 28,
        "score_breakdown": {
          "phase1_contribution": 15,
          "phase2_contribution": 13,
          "raw_total": 28,
          "capped_total": 28,
          "truncated_points": 0
        }
      }
    }
  }
}
```

**Key Validation Points**:
- ✅ `ci_configuration.platform` == "github_actions"
- ✅ `ci_configuration.has_test_steps` == true
- ✅ `ci_configuration.calculated_score` in [0, 13]
- ✅ `combined_score` == min(phase1 + phase2, 35)
- ✅ `score_breakdown.truncated_points` >= 0

---

### 6. Test Score Capping Logic (Edge Case)

```bash
# Analyze a repository with high Phase 1 + Phase 2 scores
# (Create test fixture or use repository with comprehensive test setup)
uv run pytest tests/integration/test_ci_analysis_workflow.py::test_score_capping -v
```

**Expected Behavior**:
- If Phase 1 = 25 and Phase 2 = 13, then:
  - `combined_score` == 35 (not 38)
  - `score_breakdown.raw_total` == 38
  - `score_breakdown.capped_total` == 35
  - `score_breakdown.truncated_points` == 3

---

### 7. Test Error Handling (Malformed CI Config)

```bash
# Test graceful handling of malformed CI configuration
uv run pytest tests/integration/test_ci_analysis_workflow.py::test_malformed_ci_config -v
```

**Expected Behavior** (per FR-022, Edge Case):
- Parse error logged at WARNING level
- `ci_configuration.platform` == null (or platform name if partially parsed)
- `ci_configuration.calculated_score` == 0
- `ci_configuration.parse_errors` contains error message
- Analysis continues (does not crash)
- Phase 1 score preserved

---

### 8. Test Logging Levels (FR-027)

```bash
# Test minimal logging (WARNING level)
uv run python -m src.cli.main <repo_url> --log-level minimal

# Test standard logging (INFO level, default)
uv run python -m src.cli.main <repo_url> --log-level standard

# Test detailed logging (DEBUG level)
uv run python -m src.cli.main <repo_url> --log-level detailed
```

**Expected Output**:
- **Minimal**: Only final score and CI platform names
- **Standard**: Detected platforms, test step count, coverage tools, parse warnings
- **Detailed**: All parse steps, command matching process, execution time, file content excerpts

---

## Performance Validation

### Requirement: <1 second CI configuration analysis (FR-020)

```bash
# Run performance benchmark
uv run pytest tests/unit/test_ci_config_analyzer.py::test_performance_benchmark -v

# Expected: Analysis completes in <1 second for typical repository
```

**Acceptance Criteria**:
- GitHub Actions parsing: <10ms per workflow file
- GitLab CI parsing: <10ms per config
- Pattern matching: <5ms per 100 CI steps
- Total CI analysis: <50ms (excluding file I/O)

---

## Common Issues & Troubleshooting

### Issue 1: PyYAML Import Error
```bash
ModuleNotFoundError: No module named 'yaml'
```

**Solution**:
```bash
uv add pyyaml  # Add PyYAML dependency
uv sync        # Reinstall dependencies
```

---

### Issue 2: Test Failures Due to Missing Fixtures
```bash
FileNotFoundError: No such file or directory: 'tests/fixtures/github_actions_workflow.yml'
```

**Solution**:
```bash
# Ensure test fixtures are created in tests/fixtures/
# Refer to tests/unit/test_github_actions_parser.py for required fixture structure
```

---

### Issue 3: Score Capping Not Working
```bash
AssertionError: combined_score == 38, expected 35
```

**Solution**:
- Check aggregation logic in `TestInfrastructureAnalyzer`
- Verify `TestAnalysis.__post_init__()` validates `combined_score == min(phase1 + phase2, 35)`
- Run: `uv run pytest tests/integration/test_ci_analysis_workflow.py::test_score_capping -vv`

---

### Issue 4: Performance Exceeds 1 Second
```bash
Performance warning: CI analysis took 1.35 seconds
```

**Solution**:
- Profile with `cProfile`: `python -m cProfile -s cumtime src/metrics/ci_config_analyzer.py`
- Check for unnecessary file I/O (should only read CI configs once)
- Optimize pattern matching (ensure substring matching, not regex compilation per command)

---

## Success Criteria Checklist

After completing all steps, verify:

- [ ] All contract tests pass (JSON schema validation)
- [ ] All unit tests pass (5 platform parsers + 2 pattern matchers + analyzer)
- [ ] All integration tests pass (end-to-end workflow)
- [ ] Manual smoke test produces valid `ci_configuration` in submission.json
- [ ] Score capping works correctly (35-point limit enforced)
- [ ] Malformed CI configs handled gracefully (no crashes, 0 score)
- [ ] Logging levels work as expected (minimal/standard/detailed)
- [ ] Performance meets <1 second requirement (FR-020)
- [ ] No new dependencies beyond PyYAML (constitutional compliance)

---

## Next Steps

Once all quickstart validations pass:

1. **Code Review**: Submit PR for Phase 2 implementation
2. **Documentation**: Update CLAUDE.md with CI analysis patterns
3. **Integration**: Ensure 4 tool runners call updated `TestInfrastructureAnalyzer`
4. **User Testing**: Validate with 3-5 diverse repositories (different CI platforms)
5. **Performance Monitoring**: Add timing metrics to production logs

---

**Quickstart Status**: ✅ Ready for use after Phase 2 implementation complete

**Estimated Validation Time**: 5-10 minutes (after all tests are implemented)
