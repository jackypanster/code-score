# Quickstart: End-to-End Smoke Test Suite

**Feature**: End-to-End Smoke Test Suite
**Date**: 2025-09-28
**Purpose**: Quick validation guide for smoke test implementation

## Overview

This quickstart guide provides step-by-step instructions for running and validating the smoke test suite that verifies the complete code analysis pipeline works correctly.

## Prerequisites

### System Requirements
- Python 3.11+ with UV package manager installed
- Git access to target repository
- All existing code-score dependencies installed via `uv sync`

### Environment Setup
```bash
# Ensure you're in the project root
cd /path/to/code-score

# Install/update dependencies
uv sync

# Verify existing pipeline works
./scripts/run_metrics.sh --help
```

## Quick Start Steps

### 1. Run the Smoke Test
```bash
# Execute smoke test via pytest
uv run pytest tests/smoke/test_full_pipeline.py -v

# Alternative: Run all smoke tests
uv run pytest tests/smoke/ -v
```

### 2. Expected Output
**Successful execution should show:**
```
tests/smoke/test_full_pipeline.py::test_full_pipeline_execution PASSED [100%]

=== 1 passed in XX.XXs ===
```

**Successful pipeline creates these files:**
```
output/
├── submission.json         # Metrics collection results
├── score_input.json       # Checklist evaluation results
└── evaluation_report.md   # Human-readable report
```

### 3. Verify Results
```bash
# Check output files exist
ls -la output/

# Validate JSON files are parseable
jq . output/submission.json
jq . output/score_input.json

# View human-readable report
cat output/evaluation_report.md
```

## Detailed Usage

### Running with Custom Options
```bash
# Run with increased verbosity
uv run pytest tests/smoke/ -v -s

# Run with custom timeout (if implemented)
uv run pytest tests/smoke/ --tb=long

# Run and capture output for debugging
uv run pytest tests/smoke/ -v --capture=no
```

### Integration with CI/CD
```bash
# CI-friendly execution (exit codes)
uv run pytest tests/smoke/ --tb=short --quiet

# Generate test report
uv run pytest tests/smoke/ --junitxml=smoke_test_results.xml
```

## Troubleshooting

### Common Issues

#### 1. Pipeline Execution Fails
**Symptoms**: Test fails with pipeline exit code != 0
**Solutions**:
```bash
# Run pipeline manually to diagnose
./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git --enable-checklist --generate-llm-report=false

# Check for missing tools
uv run python -c "from src.metrics.tool_executor import ToolExecutor; print('Tools OK')"

# Verify network access
git clone git@github.com:AIGCInnovatorSpace/code-walker.git /tmp/test-clone
rm -rf /tmp/test-clone
```

#### 2. Output Files Missing
**Symptoms**: Pipeline succeeds but files not found
**Solutions**:
```bash
# Check output directory
ls -la output/

# Verify working directory
pwd

# Check pipeline output location
./scripts/run_metrics.sh --help | grep -i output
```

#### 3. File Validation Fails
**Symptoms**: Files exist but content validation fails
**Solutions**:
```bash
# Check file sizes
ls -lh output/

# Validate JSON structure
python -c "import json; json.load(open('output/submission.json'))"
python -c "import json; json.load(open('output/score_input.json'))"

# Check markdown readability
file output/evaluation_report.md
```

#### 4. Timeout Issues
**Symptoms**: Test times out during execution
**Solutions**:
```bash
# Run pipeline manually with timing
time ./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git --enable-checklist --generate-llm-report=false

# Check system resources
df -h
free -h
```

## Validation Checklist

### Pre-Test Validation
- [ ] Project dependencies installed (`uv sync`)
- [ ] Git access configured for target repository
- [ ] Output directory writable
- [ ] Existing pipeline script executable

### Post-Test Validation
- [ ] Test execution completed without errors
- [ ] All three output files present
- [ ] JSON files are valid JSON
- [ ] Markdown file is readable text
- [ ] File sizes are reasonable (> 100 bytes each)

### Success Criteria
- [ ] Smoke test passes (exit code 0)
- [ ] Pipeline executes within reasonable time (< 5 minutes typical)
- [ ] All expected outputs generated
- [ ] No error messages in test output

## Test Scenarios

### Scenario 1: First-Time Execution
**Purpose**: Validate smoke test works in clean environment

**Steps**:
1. Fresh clone of repository
2. Run `uv sync` for dependencies
3. Execute smoke test
4. Verify all outputs

**Expected**: Complete success with all files generated

### Scenario 2: Repeated Execution
**Purpose**: Validate smoke test handles existing output files

**Steps**:
1. Run smoke test (creates output files)
2. Run smoke test again immediately
3. Verify outputs updated correctly

**Expected**: Second run succeeds, overwrites previous outputs

### Scenario 3: Network Issues
**Purpose**: Validate error handling for repository access

**Steps**:
1. Temporarily block network access
2. Run smoke test
3. Verify appropriate error message

**Expected**: Clear failure message about repository access

## Integration Points

### With Existing Test Suite
```bash
# Run smoke test with full test suite
uv run pytest tests/ -k "not smoke" --quiet  # Run other tests
uv run pytest tests/smoke/ -v                # Run smoke tests separately
```

### With Development Workflow
```bash
# Pre-commit validation
uv run pytest tests/smoke/ --tb=short

# Release readiness check
uv run pytest tests/smoke/ -v --capture=no
```

### With Continuous Integration
```yaml
# Example CI step
- name: Run Smoke Tests
  run: |
    uv sync
    uv run pytest tests/smoke/ -v --junitxml=smoke_results.xml
```

## Performance Expectations

### Typical Execution Times
- Pipeline execution: 2-5 minutes
- File validation: < 1 second
- Total smoke test: 2-6 minutes

### Resource Requirements
- Disk space: ~50MB for temporary files
- Memory: ~500MB for pipeline execution
- Network: Repository clone bandwidth

## Next Steps

### After Successful Validation
1. Integrate smoke test into regular development workflow
2. Add to CI/CD pipeline for release validation
3. Consider scheduling periodic health checks

### For Failed Validation
1. Review troubleshooting section above
2. Check pipeline execution manually
3. Verify environment prerequisites
4. Consult development team if issues persist