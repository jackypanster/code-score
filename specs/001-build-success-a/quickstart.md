# Quickstart: Build Validation Manual Testing

**Feature**: Complete Build Detection Integration
**Phase**: 1 - Design & Contracts
**Date**: 2025-10-09
**Purpose**: Manual validation procedures to verify build detection works correctly across all supported languages

---

## Overview

This document provides step-by-step manual validation procedures for testing build detection functionality. Use these procedures to:
1. Verify build validation works for each supported language
2. Validate build success/failure detection accuracy
3. Test graceful handling of missing build tools
4. Confirm output format compliance with schema

---

## Prerequisites

### Required Tools
- `uv` (Python package manager)
- `git` (for cloning test repositories)
- Code Score project checked out on `001-build-success-a` branch

### Optional Tools (for full validation)
- **Python**: `python3`, `uv`, `python -m build`
- **JavaScript**: `node`, `npm`, `yarn`
- **Go**: `go` (1.18+)
- **Java**: `mvn` (Maven) or `gradle`

**Note**: Tests should gracefully handle missing tools by returning `build_success=null`

---

## Test Repositories

### Recommended Test Repositories

**Python**:
1. **Simple library**: `https://github.com/requests/toolbelt.git` (small, setuptools-based)
2. **Modern project**: `https://github.com/pydantic/pydantic.git` (pyproject.toml, complex build)
3. **No build config**: `https://github.com/pallets/click.git` (check graceful handling)

**JavaScript/TypeScript**:
1. **React app**: `https://github.com/facebook/create-react-app.git` (npm build script)
2. **TypeScript library**: `https://github.com/microsoft/TypeScript.git` (tsc compilation)
3. **No build script**: Create minimal package.json without build script

**Go**:
1. **CLI tool**: `https://github.com/spf13/cobra.git` (simple Go module)
2. **Web server**: `https://github.com/gorilla/mux.git` (library with tests)
3. **Complex project**: `https://github.com/prometheus/prometheus.git` (large codebase)

**Java**:
1. **Maven project**: `https://github.com/apache/maven.git` (Maven build)
2. **Gradle project**: `https://github.com/spring-projects/spring-boot.git` (Gradle build)
3. **Android library**: `https://github.com/square/okhttp.git` (Gradle + Android)

---

## Validation Procedures

### Procedure 1: Python Build Validation (Success Case)

**Objective**: Verify Python projects with valid build configurations are correctly validated

**Steps**:
1. Navigate to project root:
   ```bash
   cd /path/to/code-score
   git checkout 001-build-success-a
   ```

2. Run analysis on Python test repository:
   ```bash
   ./scripts/run_metrics.sh https://github.com/requests/toolbelt.git --verbose
   ```

3. Verify output file exists:
   ```bash
   ls -lh output/submission.json
   ```

4. Inspect build_success field:
   ```bash
   cat output/submission.json | python3 -m json.tool | grep -A 10 '"build_success"'
   ```

**Expected Results**:
```json
{
  "metrics": {
    "code_quality": {
      "build_success": true,
      "build_details": {
        "success": true,
        "tool_used": "uv",  // or "build"
        "execution_time_seconds": 3.14,  // positive number
        "error_message": null,
        "exit_code": 0
      }
    }
  }
}
```

**Pass Criteria**:
- `build_success` is `true` (not `null`)
- `build_details.tool_used` is `"uv"` or `"build"` (not `"none"`)
- `build_details.execution_time_seconds` is positive
- `build_details.exit_code` is `0`
- `build_details.error_message` is `null`

**Failure Diagnosis**:
- If `build_success` is `null`: Check build tool availability (`which uv`, `python3 -m build`)
- If `build_success` is `false`: Review `build_details.error_message` for build errors
- If `build_details` is `null`: Implementation not complete or not integrated

---

### Procedure 2: JavaScript Build Validation (Success Case)

**Objective**: Verify JavaScript projects with build scripts are correctly validated

**Steps**:
1. Run analysis on JavaScript test repository:
   ```bash
   ./scripts/run_metrics.sh https://github.com/facebook/create-react-app.git --verbose
   ```

2. Inspect build validation results:
   ```bash
   cat output/submission.json | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   build = data['metrics']['code_quality']
   print(f\"build_success: {build['build_success']}\")
   if build.get('build_details'):
       details = build['build_details']
       print(f\"tool_used: {details['tool_used']}\")
       print(f\"execution_time: {details['execution_time_seconds']}s\")
       print(f\"exit_code: {details['exit_code']}\")
   "
   ```

**Expected Results**:
- `build_success`: `true`
- `tool_used`: `"npm"` or `"yarn"`
- `execution_time_seconds`: Positive (typically 5-30 seconds for React apps)
- `exit_code`: `0`

**Pass Criteria**:
- Build validation detected `package.json` with build script
- Correct tool selected (npm/yarn based on lock file presence)
- Build completed successfully

---

### Procedure 3: Build Failure Detection

**Objective**: Verify build failures are correctly detected and reported

**Steps**:
1. Create a temporary repository with intentional build error:
   ```bash
   mkdir /tmp/test-build-failure
   cd /tmp/test-build-failure
   git init

   # Create Python project with syntax error
   cat > setup.py << 'EOF'
   from setuptools import setup
   setup(
       name="test-failure",
       version="0.1.0",
       # Missing closing parenthesis - syntax error
   EOF

   cat > pyproject.toml << 'EOF'
   [build-system]
   requires = ["setuptools"]
   build-backend = "setuptools.build_meta"
   EOF

   git add .
   git commit -m "Test build failure"
   ```

2. Run analysis on failure repository:
   ```bash
   cd /path/to/code-score
   ./scripts/run_metrics.sh /tmp/test-build-failure --verbose
   ```

3. Verify failure detection:
   ```bash
   cat output/submission.json | python3 -m json.tool | grep -A 10 '"build_success"'
   ```

**Expected Results**:
```json
{
  "build_success": false,
  "build_details": {
    "success": false,
    "tool_used": "uv",
    "execution_time_seconds": 0.5,
    "error_message": "SyntaxError: invalid syntax (setup.py, line 5)...",
    "exit_code": 1
  }
}
```

**Pass Criteria**:
- `build_success` is `false` (not `true` or `null`)
- `error_message` contains diagnostic information
- `exit_code` is non-zero
- Error message truncated to max 1000 characters

---

### Procedure 4: Missing Build Tool Handling

**Objective**: Verify graceful degradation when build tools are unavailable

**Steps**:
1. Temporarily rename build tool to simulate unavailability:
   ```bash
   # For Python (if uv is installed)
   sudo mv /usr/local/bin/uv /usr/local/bin/uv.backup  # or appropriate path
   ```

2. Run analysis on Python repository:
   ```bash
   ./scripts/run_metrics.sh https://github.com/requests/toolbelt.git --verbose
   ```

3. Verify graceful handling:
   ```bash
   cat output/submission.json | python3 -m json.tool | grep -A 10 '"build_success"'
   ```

4. Restore build tool:
   ```bash
   sudo mv /usr/local/bin/uv.backup /usr/local/bin/uv
   ```

**Expected Results**:
```json
{
  "build_success": null,
  "build_details": {
    "success": null,
    "tool_used": "none",
    "execution_time_seconds": 0.0,
    "error_message": "UV build tool not available in PATH",
    "exit_code": null
  }
}
```

**Pass Criteria**:
- `build_success` is `null` (indicating unavailability, not failure)
- `tool_used` is `"none"`
- `error_message` explains why tool unavailable
- Analysis pipeline continues despite missing build tool (no crash)

---

### Procedure 5: Go Build Validation

**Objective**: Verify Go build validation works and integrates existing logic

**Steps**:
1. Run analysis on Go repository:
   ```bash
   ./scripts/run_metrics.sh https://github.com/spf13/cobra.git --verbose
   ```

2. Verify build validation:
   ```bash
   cat output/submission.json | python3 -m json.tool | jq '.metrics.code_quality | {build_success, build_details}'
   ```

**Expected Results**:
- `build_success`: `true` (if `go` is available and code compiles)
- `tool_used`: `"go"`
- Execution time: Typically 1-5 seconds for small projects

**Pass Criteria**:
- Existing `GolangToolRunner.run_build()` method is called
- Results are integrated into `MetricsCollection`
- Output matches BuildValidationResult schema

---

### Procedure 6: Java Build Validation

**Objective**: Verify Java build validation detects Maven/Gradle and executes builds

**Steps**:
1. Run analysis on Maven project:
   ```bash
   ./scripts/run_metrics.sh https://github.com/apache/maven.git --verbose
   ```

2. Verify Maven detection:
   ```bash
   cat output/submission.json | python3 -m json.tool | jq '.metrics.code_quality.build_details.tool_used'
   # Should output: "mvn"
   ```

3. Run analysis on Gradle project:
   ```bash
   ./scripts/run_metrics.sh https://github.com/spring-projects/spring-boot.git --verbose
   ```

4. Verify Gradle detection:
   ```bash
   cat output/submission.json | python3 -m json.tool | jq '.metrics.code_quality.build_details.tool_used'
   # Should output: "gradle"
   ```

**Expected Results**:
- Maven projects: `tool_used` is `"mvn"`
- Gradle projects: `tool_used` is `"gradle"`
- Build completes or fails with structured error

---

### Procedure 7: Error Message Truncation

**Objective**: Verify error messages are truncated to 1000 characters (NFR-002)

**Steps**:
1. Create a build failure with verbose output:
   ```bash
   mkdir /tmp/verbose-error
   cd /tmp/verbose-error
   git init

   # Create project with many errors
   cat > setup.py << 'EOF'
   from setuptools import setup
   import syntax_error_1
   import syntax_error_2
   # ... (repeat 50 times to generate long error output)
   EOF

   cat > pyproject.toml << 'EOF'
   [build-system]
   requires = ["setuptools"]
   build-backend = "setuptools.build_meta"
   EOF

   git add .
   git commit -m "Verbose errors"
   ```

2. Run analysis:
   ```bash
   cd /path/to/code-score
   ./scripts/run_metrics.sh /tmp/verbose-error --verbose
   ```

3. Verify truncation:
   ```bash
   cat output/submission.json | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   error_msg = data['metrics']['code_quality']['build_details']['error_message']
   print(f\"Error message length: {len(error_msg)} characters\")
   assert len(error_msg) <= 1000, 'Error message exceeds 1000 chars!'
   print('✓ Error message correctly truncated')
   "
   ```

**Pass Criteria**:
- Error message length ≤ 1000 characters
- Message ends with "..." if truncated
- Diagnostic value preserved (first 997 chars + "...")

---

### Procedure 8: Build Timeout Validation

**Objective**: Verify builds complete within 120-second timeout (NFR-001)

**Steps**:
1. Run analysis on large repository:
   ```bash
   ./scripts/run_metrics.sh https://github.com/prometheus/prometheus.git --verbose --timeout 300
   ```

2. Measure execution time:
   ```bash
   cat output/submission.json | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   build_time = data['metrics']['code_quality']['build_details']['execution_time_seconds']
   print(f\"Build time: {build_time}s\")
   if build_time < 120:
       print('✓ Build completed within timeout')
   else:
       print('⚠ Build exceeded 120-second timeout')
   "
   ```

**Pass Criteria**:
- 99% of test repositories complete build validation within 120 seconds
- Builds exceeding timeout are cancelled gracefully
- Timeout errors recorded in `error_message`

---

### Procedure 9: Schema Validation

**Objective**: Verify output conforms to contract schema

**Steps**:
1. Run contract tests:
   ```bash
   uv run pytest specs/001-build-success-a/contracts/test_build_schema.py -v
   ```

2. Verify all tests pass:
   ```
   test_build_success_field_exists PASSED
   test_build_success_type_validation PASSED
   test_build_details_structure PASSED
   test_error_message_truncation PASSED
   test_execution_time_non_negative PASSED
   test_build_success_consistency_with_details PASSED
   test_tool_used_valid_values PASSED
   ```

**Pass Criteria**:
- All contract tests pass
- Schema compliance verified programmatically
- No regressions in existing tests

---

### Procedure 10: Cross-Language Consistency

**Objective**: Verify consistent behavior across all supported languages

**Steps**:
1. Run analysis on one repository per language:
   ```bash
   # Python
   ./scripts/run_metrics.sh https://github.com/requests/toolbelt.git

   # JavaScript
   ./scripts/run_metrics.sh https://github.com/facebook/create-react-app.git

   # Go
   ./scripts/run_metrics.sh https://github.com/spf13/cobra.git

   # Java
   ./scripts/run_metrics.sh https://github.com/apache/maven.git
   ```

2. Compare build_success field across all outputs:
   ```bash
   for lang in python javascript go java; do
       echo "=== $lang ==="
       cat output/submission.json | python3 -m json.tool | jq '.metrics.code_quality | {build_success, tool_used: .build_details.tool_used}'
   done
   ```

**Expected Results**:
- All languages populate `build_success` field
- Each language uses appropriate tool (`uv/build`, `npm/yarn`, `go`, `mvn/gradle`)
- Consistent field structure across languages
- Consistent error handling patterns

**Pass Criteria**:
- 100% of supported languages have build validation
- No language-specific schema deviations
- Consistent success/failure/unavailable semantics

---

## Validation Checklist

After completing all procedures, verify:

- [ ] **Python**: Build success detected with `uv` or `build`
- [ ] **JavaScript**: Build success detected with `npm` or `yarn`
- [ ] **Go**: Build success detected with `go build`
- [ ] **Java**: Build success detected with `mvn` or `gradle`
- [ ] **Build Failure**: `build_success=false` with error details
- [ ] **Tool Unavailable**: `build_success=null` with graceful handling
- [ ] **Error Truncation**: Messages ≤1000 characters
- [ ] **Timeout Compliance**: 99% of builds complete within 120s
- [ ] **Schema Compliance**: All contract tests pass
- [ ] **Cross-Language Consistency**: Uniform behavior across languages

---

## Troubleshooting

### build_success is always null

**Symptoms**: All repositories show `build_success: null`

**Possible Causes**:
1. Build validation not integrated into `ToolExecutor`
2. Tool runners not calling `run_build()` methods
3. Build tools not available in PATH

**Resolution**:
- Verify `ToolExecutor` includes build validation in parallel_tasks
- Check tool availability: `which uv`, `which npm`, `which go`, `which mvn`
- Review verbose output for error messages

### build_details is missing

**Symptoms**: `build_success` is populated but `build_details` is `null`

**Possible Causes**:
1. `CodeQualityMetrics` not updated with `build_details` field
2. Mapping from `BuildValidationResult` to `CodeQualityMetrics` incomplete

**Resolution**:
- Verify `CodeQualityMetrics` model includes `build_details` field
- Check `ToolExecutor` populates both `build_success` and `build_details`

### Contract tests fail

**Symptoms**: `uv run pytest specs/001-build-success-a/contracts/test_build_schema.py` shows failures

**Possible Causes**:
1. Schema violations in output format
2. Implementation incomplete
3. Test expectations outdated

**Resolution**:
- Review test failure messages for specific violations
- Compare actual output with expected schema
- Update tests if schema evolved during implementation

---

## Next Steps

After successful manual validation:
1. Document any deviations from expected behavior
2. Update `target-repository-scoring.md` to change "△" to "✓" for Build/Package Success
3. Run full test suite: `uv run pytest`
4. Prepare for PR submission with validation results

---

## Validation Results Template

Use this template to document validation results:

```
## Build Validation Test Results

**Date**: YYYY-MM-DD
**Branch**: 001-build-success-a
**Tester**: [Your Name]

### Test Execution Summary

| Procedure | Language | Status | Notes |
|-----------|----------|--------|-------|
| 1 | Python | ✅ PASS | build_success=true, uv detected |
| 2 | JavaScript | ✅ PASS | build_success=true, npm detected |
| 3 | Failure Detection | ✅ PASS | Syntax errors correctly detected |
| 4 | Tool Unavailable | ✅ PASS | Graceful degradation working |
| 5 | Go | ✅ PASS | Existing logic integrated |
| 6 | Java | ✅ PASS | Maven and Gradle both work |
| 7 | Error Truncation | ✅ PASS | 1000-char limit enforced |
| 8 | Timeout | ✅ PASS | 99% complete within 120s |
| 9 | Schema | ✅ PASS | All contract tests pass |
| 10 | Consistency | ✅ PASS | Uniform behavior across languages |

### Issues Encountered

[List any issues, unexpected behaviors, or failures]

### Performance Metrics

- Average build time (Python): X.Xs
- Average build time (JavaScript): X.Xs
- Average build time (Go): X.Xs
- Average build time (Java): X.Xs
- Timeout rate: X%

### Recommendations

[Any suggestions for improvement or follow-up work]
```
