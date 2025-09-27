# Quickstart: Git Repository Metrics Collection

## Prerequisites

### System Requirements
- Python 3.11 or higher
- Git command line tools
- Internet connection for repository cloning

### Tool Installation
```bash
# Install uv for Python dependency management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install language-specific analysis tools (optional, will be checked at runtime)
# Python tools
uv tool install ruff
uv tool install pytest-cov

# JavaScript/TypeScript tools
npm install -g eslint prettier

# Java tools (if analyzing Java projects)
# Download and install Maven or Gradle

# Go tools (if analyzing Go projects)
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```

## Quick Start

### 1. Setup Project
```bash
# Clone the code-score repository
git clone https://github.com/user/code-score.git
cd code-score

# Create virtual environment and install dependencies
uv sync
```

### 2. Basic Usage
```bash
# Analyze default test repository
./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git

# Analyze specific commit
./scripts/run_metrics.sh https://github.com/user/repo.git a1b2c3d4e5f6

# Specify output directory and format
./scripts/run_metrics.sh https://github.com/user/repo.git --output-dir ./results --format json
```

### 3. View Results
```bash
# Check generated output
ls output/
# Expected files:
# - submission.json (consolidated results)
# - metrics/repo-name-timestamp.json (detailed metrics)
# - metrics/repo-name-timestamp.md (human-readable summary)

# View JSON results
cat output/submission.json | jq .

# View Markdown summary
cat output/metrics/*.md
```

## Supported Repository Types

### Python Projects
**Detected by**: `*.py` files, `pyproject.toml`, `requirements.txt`, `setup.py`
**Tools used**: Ruff (linting), pytest (testing), pip-audit (security)
**Example**:
```bash
./scripts/run_metrics.sh https://github.com/psf/requests.git
```

### JavaScript/TypeScript Projects
**Detected by**: `package.json`, `*.js`, `*.ts` files
**Tools used**: ESLint (linting), npm test, npm audit (security)
**Example**:
```bash
./scripts/run_metrics.sh https://github.com/expressjs/express.git
```

### Java Projects
**Detected by**: `pom.xml`, `build.gradle`, `*.java` files
**Tools used**: Maven/Gradle (build), Checkstyle (linting), OWASP dependency-check
**Example**:
```bash
./scripts/run_metrics.sh https://github.com/spring-projects/spring-boot.git
```

### Go Projects
**Detected by**: `go.mod`, `*.go` files
**Tools used**: golangci-lint, go test, osv-scanner (security)
**Example**:
```bash
./scripts/run_metrics.sh https://github.com/gin-gonic/gin.git
```

## Configuration Options

### Command Line Arguments
```bash
./scripts/run_metrics.sh <repository_url> [commit_sha] [options]

Options:
  --output-dir DIR     Output directory (default: ./output)
  --format FORMAT      Output format: json, markdown, both (default: both)
  --timeout MINUTES    Analysis timeout in minutes (default: 5)
  --no-cleanup         Keep temporary files for debugging
  --verbose            Enable detailed logging
```

### Environment Variables
```bash
# Temporary directory for repository clones
export METRICS_TMP_DIR=/tmp/metrics-analysis

# Default output directory
export METRICS_OUTPUT_DIR=./output

# Tool timeout in seconds
export METRICS_TOOL_TIMEOUT=300
```

## Expected Output Structure

### JSON Output (`submission.json`)
```json
{
  "repository": {
    "url": "https://github.com/user/repo.git",
    "commit": "a1b2c3d4e5f6789012345678901234567890abcd",
    "language": "python",
    "timestamp": "2025-09-27T10:30:00Z",
    "size_mb": 12.5
  },
  "metrics": {
    "code_quality": {
      "lint_results": {"passed": true, "issues_count": 3},
      "build_success": true,
      "security_issues": []
    },
    "testing": {
      "test_execution": {"tests_run": 45, "tests_passed": 43},
      "coverage_report": {"line_coverage": 78.5}
    },
    "documentation": {
      "readme_present": true,
      "setup_instructions": true
    }
  },
  "execution": {
    "tools_used": ["ruff", "pytest", "pip-audit"],
    "duration_seconds": 125.3,
    "timestamp": "2025-09-27T10:32:05Z"
  }
}
```

### Markdown Output
- Repository information summary
- Metrics overview with scores
- Detailed findings by category
- Recommendations for improvement

## Troubleshooting

### Common Issues

**Repository clone fails**
- Check repository URL format
- Verify network connectivity
- Ensure repository is publicly accessible

**Tool not found errors**
- Install missing analysis tools
- Check PATH environment variable
- Use `--verbose` for detailed error messages

**Analysis timeout**
- Increase timeout with `--timeout` option
- Check repository size (large repos take longer)
- Monitor system resources

**Permission denied**
- Ensure write permissions to output directory
- Check temporary directory permissions
- Verify Git credentials if needed

### Debug Mode
```bash
# Run with detailed logging and keep temporary files
./scripts/run_metrics.sh https://github.com/user/repo.git \
  --verbose \
  --no-cleanup \
  --timeout 10
```

### Log Files
```bash
# Check execution logs
tail -f /tmp/metrics-analysis/execution.log

# View tool-specific logs
ls /tmp/metrics-analysis/tool-logs/
```

## Validation Tests

### Verify Installation
```bash
# Test with known working repository
./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git

# Expected: Successful analysis with no errors
# Check: output/submission.json exists and validates against schema
```

### Schema Validation
```bash
# Validate output against schema
python -c "
import json, jsonschema
with open('output/submission.json') as f:
    data = json.load(f)
with open('specs/001-docs-git-workflow/contracts/output_schema.json') as f:
    schema = json.load(f)
jsonschema.validate(data, schema)
print('Schema validation passed')
"
```

## Next Steps

1. **Run test analysis**: Use default repository to verify setup
2. **Try different languages**: Test with Python, JS, Java, Go repositories
3. **Batch processing**: Analyze multiple repositories for comparison
4. **Integration**: Incorporate into CI/CD pipelines or hackathon evaluation workflows
5. **Customization**: Modify tool configurations for specific requirements

For issues or questions, check the troubleshooting section or review the execution logs for detailed error information.