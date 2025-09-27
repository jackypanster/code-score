# Code Score

Parameterized Git repository metrics collection for automated code quality evaluation.

## Overview

Code Score is a CLI tool that automatically analyzes code quality metrics from any public Git repository. It supports multiple programming languages and provides standardized JSON/Markdown output for consistent evaluation across different projects.

Perfect for hackathon judging, code review automation, and project quality assessment.

## Features

- **Multi-language support**: Python, JavaScript/TypeScript, Java, Go
- **Comprehensive analysis**: Linting, testing, security audits, documentation quality
- **Performance optimized**: Handles large repositories with timeout controls
- **Standardized output**: JSON and Markdown formats with schema validation
- **Configurable timeouts**: Prevents hanging on problematic repositories
- **Error handling**: Graceful degradation when tools are unavailable

## Prerequisites

- **Python 3.11+**: Required for the core application
- **UV**: Modern Python package manager (install from [astral.sh](https://astral.sh/uv))
- **Git**: For repository cloning operations

### Optional Tools (for enhanced analysis)

The tool will automatically detect and use these if available:

**Python:**
- `ruff` or `flake8` (linting)
- `pytest` or `unittest` (testing)
- `pip-audit` (security scanning)
- `coverage` (test coverage)

**JavaScript/TypeScript:**
- `eslint` (linting)
- `jest`, `mocha`, or `npm test` (testing)
- `npm audit` or `yarn audit` (security)

**Java:**
- `checkstyle` (linting)
- `maven` or `gradle` (testing and building)
- `spotbugs` (security)

**Go:**
- `golangci-lint` or `gofmt` (linting)
- `go test` (testing)
- `gosec` (security)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/code-score.git
cd code-score
```

### 2. Install UV (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### 3. Install Dependencies

```bash
# Install project dependencies
uv sync

# Install development dependencies (optional)
uv sync --dev
```

### 4. Verify Installation

```bash
# Test the CLI
./scripts/run_metrics.sh --help

# Run tests to ensure everything works
uv run pytest
```

## Usage

### Basic Usage

```bash
# Analyze a repository (outputs to ./output/)
./scripts/run_metrics.sh https://github.com/user/repo.git

# Analyze specific commit
./scripts/run_metrics.sh https://github.com/user/repo.git a1b2c3d4e5f6789012345678901234567890abcd
```

### Advanced Options

```bash
# Custom output directory
./scripts/run_metrics.sh https://github.com/user/repo.git --output-dir /path/to/output

# JSON output only
./scripts/run_metrics.sh https://github.com/user/repo.git --format json

# Markdown output only
./scripts/run_metrics.sh https://github.com/user/repo.git --format markdown

# Both formats (default)
./scripts/run_metrics.sh https://github.com/user/repo.git --format both

# Custom timeout (default: 300 seconds)
./scripts/run_metrics.sh https://github.com/user/repo.git --timeout 600

# Verbose output
./scripts/run_metrics.sh https://github.com/user/repo.git --verbose
```

### Python Module Usage

```python
from src.cli.main import main

# Programmatic usage
main.callback(
    repository_url="https://github.com/user/repo.git",
    commit_sha=None,
    output_dir="./results",
    output_format="both",
    timeout=300,
    verbose=True
)
```

## Output Format

### JSON Output

The tool generates JSON output conforming to a strict schema:

```json
{
  "schema_version": "1.0.0",
  "repository": {
    "url": "https://github.com/user/repo.git",
    "commit": "a1b2c3d4e5f6789012345678901234567890abcd",
    "language": "python",
    "timestamp": "2025-09-27T10:30:00Z",
    "size_mb": 12.5
  },
  "metrics": {
    "code_quality": {
      "lint_results": {
        "tool_used": "ruff",
        "passed": true,
        "issues_count": 0,
        "issues": []
      },
      "build_success": true,
      "dependency_audit": {
        "vulnerabilities_found": 0,
        "high_severity_count": 0,
        "tool_used": "pip-audit"
      }
    },
    "testing": {
      "test_execution": {
        "tests_run": 45,
        "tests_passed": 43,
        "tests_failed": 2,
        "framework": "pytest",
        "execution_time_seconds": 12.5
      }
    },
    "documentation": {
      "readme_present": true,
      "readme_quality_score": 0.85,
      "api_documentation": false,
      "setup_instructions": true,
      "usage_examples": true
    }
  },
  "execution": {
    "tools_used": ["ruff", "pytest", "pip-audit"],
    "errors": [],
    "warnings": ["Some test files have low coverage"],
    "duration_seconds": 125.3,
    "timestamp": "2025-09-27T10:32:05Z"
  }
}
```

### Markdown Output

The tool also generates human-readable Markdown reports with:
- Repository information
- Code quality summary with pass/fail indicators
- Testing results and coverage
- Documentation analysis
- Tool execution summary

## Performance Considerations

The tool includes several optimizations for large repositories:

- **Size limits**: Repositories larger than 500MB are rejected
- **File limits**: Analysis warns when >10,000 files are detected
- **Timeouts**: Individual tools timeout after 2 minutes
- **Parallel execution**: Independent tools run concurrently
- **Early termination**: Stops gracefully when global timeout is reached

## Language-Specific Behavior

### Python
- **Linting**: Prefers `ruff`, falls back to `flake8`
- **Testing**: Uses `pytest` or `unittest`
- **Security**: `pip-audit` for dependency vulnerabilities

### JavaScript/TypeScript
- **Linting**: Uses `eslint`
- **Testing**: Detects `jest`, `mocha`, or `npm test`
- **Security**: `npm audit` or `yarn audit`

### Java
- **Linting**: Uses `checkstyle`
- **Testing**: Maven (`mvn test`) or Gradle
- **Building**: `mvn compile` for build verification

### Go
- **Linting**: Prefers `golangci-lint`, falls back to `gofmt`
- **Testing**: Standard `go test`
- **Security**: `gosec` for vulnerability scanning

## Error Handling

The tool follows the KISS principle with fail-fast error handling:

- **Critical errors**: Repository access failures, invalid URLs
- **Warnings**: Missing tools, partial analysis results
- **Graceful degradation**: Continues analysis when individual tools fail

## Development

### Project Structure

```
code-score/
├── src/
│   ├── cli/                 # Command-line interface
│   │   └── main.py
│   └── metrics/             # Core analysis modules
│       ├── models/          # Data models
│       ├── tool_runners/    # Language-specific tools
│       ├── git_operations.py
│       ├── language_detection.py
│       ├── tool_executor.py
│       ├── output_generators.py
│       ├── error_handling.py
│       └── cleanup.py
├── tests/
│   ├── contract/           # Schema validation tests
│   ├── integration/        # End-to-end tests
│   └── unit/              # Unit tests
├── scripts/
│   └── run_metrics.sh     # Entry point script
└── specs/                 # Design documentation
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific test types
uv run pytest tests/unit/           # Unit tests only
uv run pytest tests/integration/   # Integration tests only
uv run pytest tests/contract/      # Contract tests only

# With coverage
uv run pytest --cov=src

# Verbose output
uv run pytest -v
```

### Code Quality

```bash
# Linting
uv run ruff check src/ tests/

# Formatting
uv run ruff format src/ tests/

# Type checking
uv run mypy src/
```

### Adding New Language Support

1. Create new tool runner in `src/metrics/tool_runners/`
2. Add language mapping in `ToolExecutor.__init__()`
3. Update language detection patterns in `LanguageDetector`
4. Add integration tests in `tests/integration/`
5. Update documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests first (TDD approach)
4. Implement features
5. Ensure all tests pass
6. Submit a pull request

## Constitutional Principles

This project follows three core principles:

1. **UV-based dependency management**: All Python dependencies managed via UV
2. **KISS principle**: Simple, fail-fast error handling with minimal abstraction
3. **Transparent communication**: Clear logging and error messages for debugging

## Troubleshooting

### Common Issues

**"Git command not found"**
- Install Git on your system
- Ensure Git is in your PATH

**"Repository size exceeds maximum"**
- Repository is larger than 500MB limit
- Use a smaller repository or increase limits in configuration

**"Tool timeout"**
- Increase timeout with `--timeout` option
- Check if repository is too large or tools are hanging

**"UV not found"**
- Install UV following the installation instructions above
- Ensure UV is in your PATH

### Getting Help

- Check the [Issues](https://github.com/your-org/code-score/issues) page
- Review the test files for usage examples
- Enable verbose mode (`--verbose`) for detailed logging

## License

MIT License - see LICENSE file for details.