# Example Outputs

This directory contains sample outputs from the Code Score tool to help you understand what to expect when analyzing different types of repositories.

## Files

### JSON Outputs
- **`python-project.json`** - Analysis of a Python Flask API project
- **`javascript-project.json`** - Analysis of a React dashboard application
- **`go-project.json`** - Analysis of a Go microservice

### Markdown Outputs
- **`python-project.md`** - Human-readable report for the Python project

## Output Highlights

### Python Project (Flask API)
- **Language:** Python
- **Size:** 15.8 MB
- **Quality:** Good with minor linting issues
- **Testing:** 45/47 tests passing (95.7%)
- **Security:** 1 medium vulnerability
- **Documentation:** Excellent (0.9/1.0 score)

### JavaScript Project (React Dashboard)
- **Language:** JavaScript
- **Size:** 245.3 MB (large project)
- **Quality:** Issues with ESLint (12 problems)
- **Testing:** 82/89 tests passing (92.1%)
- **Security:** 5 vulnerabilities (2 high severity)
- **Documentation:** Good (0.75/1.0 score)

### Go Project (Microservice)
- **Language:** Go
- **Size:** 8.7 MB (compact)
- **Quality:** Excellent with minimal issues
- **Testing:** 34/34 tests passing (100%)
- **Security:** No vulnerabilities found
- **Documentation:** Excellent (0.95/1.0 score)

## Understanding the Schema

### JSON Structure
```json
{
  "schema_version": "1.0.0",
  "repository": { /* repo metadata */ },
  "metrics": {
    "code_quality": { /* linting, security, build */ },
    "testing": { /* test results, coverage */ },
    "documentation": { /* readme, docs quality */ }
  },
  "execution": { /* tools used, duration, errors */ }
}
```

### Key Metrics Explained

**Code Quality:**
- `lint_results.passed` - Whether linting passed overall
- `lint_results.issues_count` - Number of style/quality issues
- `dependency_audit.vulnerabilities_found` - Security vulnerabilities
- `build_success` - Whether the project builds successfully

**Testing:**
- `test_execution.tests_passed/tests_run` - Test pass rate
- `coverage_report.line_coverage` - Percentage of code covered by tests
- `framework` - Testing framework detected (pytest, jest, etc.)

**Documentation:**
- `readme_quality_score` - Quality score from 0-1 based on content analysis
- `api_documentation` - Whether API docs were found
- `setup_instructions` - Whether installation instructions exist

**Execution:**
- `tools_used` - List of analysis tools that ran successfully
- `errors` - Critical errors that stopped analysis
- `warnings` - Non-critical issues or degraded functionality
- `duration_seconds` - Total analysis time

## Interpretation Guide

### Quality Indicators

**Excellent Projects:**
- All tests passing (100%)
- No security vulnerabilities
- High code coverage (>90%)
- Clean linting results
- Comprehensive documentation

**Good Projects:**
- Most tests passing (>95%)
- No high-severity vulnerabilities
- Decent coverage (>80%)
- Minor linting issues
- Basic documentation present

**Projects Needing Attention:**
- Failing tests (<90% pass rate)
- Security vulnerabilities present
- Low coverage (<70%)
- Many linting issues
- Missing or poor documentation

### Common Patterns

**Large JavaScript Projects:**
- Often have more dependencies → more security vulnerabilities
- Complex build systems → longer analysis times
- Higher file counts → performance warnings

**Go Projects:**
- Typically very clean linting (Go tooling is strict)
- Fast test execution
- Smaller dependency trees → fewer security issues

**Python Projects:**
- Rich tooling ecosystem (many analysis options)
- Good balance of features and maintainability
- Package security important due to PyPI ecosystem

## Using These Examples

1. **Compare your results** to these examples to understand relative quality
2. **Set quality thresholds** based on what's achievable in similar projects
3. **Identify improvement areas** by seeing what excellent projects include
4. **Understand tool output** by reviewing the detailed breakdowns