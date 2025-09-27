# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Code Score is a parameterized Git repository metrics collection tool designed for automated code quality evaluation. It analyzes any public Git repository and produces standardized JSON/Markdown reports suitable for hackathon judging, code review automation, and project quality assessment.

## Core Architecture

### Pipeline-Based Design
The system follows a clear pipeline: **Clone → Detect → Analyze → Report → Cleanup**

1. **Git Operations** (`src/metrics/git_operations.py`): Handles repository cloning and commit switching
2. **Language Detection** (`src/metrics/language_detection.py`): Identifies primary programming language
3. **Tool Execution** (`src/metrics/tool_executor.py`): Coordinates parallel execution of language-specific tools
4. **Tool Runners** (`src/metrics/tool_runners/`): Language-specific analysis implementations
5. **Output Generation** (`src/metrics/output_generators.py`): Produces standardized JSON/Markdown reports

### Multi-Language Tool Runners
- **Python**: `ruff`/`flake8` (linting), `pytest` (testing), `pip-audit` (security)
- **JavaScript/TypeScript**: `eslint` (linting), `jest`/`mocha` (testing), `npm audit` (security)
- **Java**: `checkstyle` (linting), `maven`/`gradle` (testing), `spotbugs` (security)
- **Go**: `golangci-lint`/`gofmt` (linting), `go test` (testing), `gosec` (security)

### Performance Optimizations
- Repository size limit: 500MB maximum
- File count warning: >10,000 files
- Individual tool timeout: 2 minutes maximum
- Parallel tool execution with ThreadPoolExecutor
- Graceful degradation when tools are unavailable

## Common Commands

### Development Workflow
```bash
# Install dependencies (UV required)
uv sync

# Install development dependencies
uv sync --dev

# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/           # Unit tests
uv run pytest tests/integration/   # Integration tests
uv run pytest tests/contract/      # Schema validation tests

# Code quality checks
uv run ruff check src/ tests/       # Linting
uv run ruff format src/ tests/      # Formatting
uv run mypy src/                    # Type checking

# Coverage analysis
uv run pytest --cov=src --cov-report=html
```

### Primary Tool Usage
```bash
# Basic repository analysis
./scripts/run_metrics.sh https://github.com/user/repo.git

# Analyze specific commit
./scripts/run_metrics.sh https://github.com/user/repo.git a1b2c3d4e5f6

# Custom output and format options
./scripts/run_metrics.sh https://github.com/user/repo.git \
  --output-dir ./results \
  --format json \
  --timeout 600 \
  --verbose

# Programmatic usage
uv run python -m src.cli.main https://github.com/user/repo.git --verbose
```

### Test and Validation
```bash
# Run validation against default test repository
./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git

# Test individual components
uv run pytest tests/unit/test_language_detection.py -v
uv run pytest tests/integration/test_full_workflow.py -v

# Validate output schema
uv run pytest tests/contract/ -v
```

## Data Models and Schemas

### Core Models (`src/metrics/models/`)
- **Repository**: URL, commit, language, size metadata
- **MetricsCollection**: Top-level container for all analysis results
- **CodeQualityMetrics**: Lint results, build status, dependency audit
- **TestingMetrics**: Test execution results and coverage data
- **DocumentationMetrics**: README analysis and documentation quality
- **ExecutionMetadata**: Tool execution tracking and performance data

### Output Schema
The system produces JSON output conforming to a strict schema with these top-level sections:
- `schema_version`: Version compatibility identifier
- `repository`: Repository metadata and analysis context
- `metrics`: Quality analysis results organized by category
- `execution`: Tool execution summary and performance metrics

## Constitutional Principles

This project follows three core principles defined in the project constitution:

1. **UV-based dependency management**: All Python dependencies managed exclusively via UV
2. **KISS principle**: Simple, fail-fast error handling with minimal abstraction layers
3. **Transparent communication**: Clear logging and descriptive error messages for debugging

## Language-Specific Patterns

### Adding New Language Support
1. Create tool runner class in `src/metrics/tool_runners/new_language_tools.py`
2. Implement required interface methods: `check_availability()`, `run_linting()`, `run_tests()`, `run_security_audit()`
3. Register language mapping in `ToolExecutor.__init__()`
4. Add detection patterns to `LanguageDetector._get_language_patterns()`
5. Create integration tests in `tests/integration/`

### Error Handling Strategy
- **Critical failures**: Repository access, invalid URLs, tool crashes
- **Warnings**: Missing tools, partial results, performance issues
- **Graceful degradation**: Continue analysis when individual tools fail
- **Timeout handling**: Individual tools and global pipeline timeouts

## Testing Architecture

### Test Categories
- **Unit tests** (`tests/unit/`): Individual component testing
- **Integration tests** (`tests/integration/`): End-to-end workflow testing
- **Contract tests** (`tests/contract/`): Output schema validation

### Test Data Strategy
- Mock external dependencies (Git operations, tool execution)
- Use real sample repositories for integration testing
- Validate against known output schemas for contract testing

## Performance Considerations

### Large Repository Handling
- Size validation before cloning (500MB limit)
- File count monitoring (warning at 10,000 files)
- Streaming output for large analysis results
- Temporary directory cleanup with signal handlers

### Tool Execution Optimization
- Parallel execution of independent tools
- Individual tool timeouts prevent hanging
- Resource cleanup on timeout or failure
- Progress tracking for long-running operations

## Configuration and Environment

### Environment Variables
- `METRICS_OUTPUT_DIR`: Default output directory override
- `METRICS_TOOL_TIMEOUT`: Default timeout override in seconds

### Tool Detection Logic
- Check tool availability before execution
- Prefer more comprehensive tools (e.g., `ruff` over `flake8`)
- Fallback to simpler alternatives when advanced tools unavailable
- Clear error messages when required tools missing

## Debugging and Troubleshooting

### Common Issues
- **Repository cloning failures**: Check URL format and access permissions
- **Tool timeouts**: Increase timeout or check repository size
- **Missing tool dependencies**: Install language-specific tools or use `--verbose` for details
- **Schema validation errors**: Check JSON output structure against contract tests

### Debugging Techniques
- Use `--verbose` flag for detailed execution logging
- Check `htmlcov/` directory for test coverage analysis
- Examine `output/` directory for generated reports and error logs
- Run contract tests to validate output format compliance
