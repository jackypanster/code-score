# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Code Score is a parameterized Git repository metrics collection tool with integrated checklist evaluation for automated code quality assessment. It analyzes any public Git repository and produces standardized JSON/Markdown reports with evidence-based scoring suitable for hackathon judging, code review automation, and project quality assessment.

The system consists of two integrated pipelines:
1. **Metrics Collection Pipeline**: Collects raw quality metrics (linting, testing, documentation)
2. **Checklist Evaluation Pipeline**: Evaluates metrics against 11-item quality checklist with evidence tracking

## Core Architecture

### Dual Pipeline Architecture

**Metrics Collection Pipeline**: **Clone → Detect → Analyze → Report → Cleanup**
1. **Git Operations** (`src/metrics/git_operations.py`): Repository cloning and commit switching
2. **Language Detection** (`src/metrics/language_detection.py`): Identifies primary programming language
3. **Tool Execution** (`src/metrics/tool_executor.py`): Parallel execution of language-specific tools
4. **Tool Runners** (`src/metrics/tool_runners/`): Language-specific analysis implementations
5. **Output Generation** (`src/metrics/output_generators.py`): Produces submission.json

**Checklist Evaluation Pipeline**: **Load → Evaluate → Evidence → Score → Report**
1. **ChecklistEvaluator** (`src/metrics/checklist_evaluator.py`): Rule-based evaluation engine with 11 quality criteria
2. **EvidenceTracker** (`src/metrics/evidence_tracker.py`): Collects and organizes supporting evidence with confidence levels
3. **ScoringMapper** (`src/metrics/scoring_mapper.py`): Transforms evaluation results to structured output for LLM processing
4. **ChecklistLoader** (`src/metrics/checklist_loader.py`): Manages configuration and language adaptations
5. **PipelineOutputManager** (`src/metrics/pipeline_output_manager.py`): Integrates both pipelines

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

# Checklist evaluation commands
uv run python -m src.cli.evaluate output/submission.json --verbose
uv run python -m src.cli.evaluate output/submission.json --output-dir results/ --format both
```

### Checklist Evaluation Workflow
```bash
# Complete pipeline with integrated checklist evaluation (default)
./scripts/run_metrics.sh https://github.com/user/repo.git --enable-checklist

# Two-step process: metrics then evaluation
./scripts/run_metrics.sh https://github.com/user/repo.git --enable-checklist=false
uv run python -m src.cli.evaluate output/submission.json

# Custom checklist configuration
uv run python -m src.cli.evaluate output/submission.json --checklist-config custom_checklist.yaml
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

### Metrics Collection Models (`src/metrics/models/`)
- **Repository**: URL, commit, language, size metadata
- **MetricsCollection**: Top-level container for all analysis results
- **CodeQualityMetrics**: Lint results, build status, dependency audit
- **TestingMetrics**: Test execution results and coverage data
- **DocumentationMetrics**: README analysis and documentation quality
- **ExecutionMetadata**: Tool execution tracking and performance data

### Checklist Evaluation Models (`src/metrics/models/`)
- **ChecklistItem**: Individual evaluation criterion with scoring and evidence
- **EvaluationResult**: Complete evaluation with 11 items, scores, and category breakdowns
- **ScoreInput**: LLM-ready structured output format
- **EvidenceReference**: Supporting evidence with confidence levels and source tracking
- **CategoryBreakdown**: Score summaries by dimension (Code Quality, Testing, Documentation)

### Output Schema
**Metrics Collection** produces `submission.json` with:
- `schema_version`, `repository`, `metrics`, `execution`

**Checklist Evaluation** produces `score_input.json` with:
- `evaluation_result`: 11-item checklist scores with evidence
- `repository_info`: Analysis context and metadata
- `evidence_paths`: File paths to detailed evidence files
- `human_summary`: Comprehensive markdown evaluation report

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
5. Update checklist configuration in `specs/002-git-log-docs/contracts/checklist_mapping.yaml` with language adaptations
6. Create integration tests in `tests/integration/`

### Checklist Evaluation System
The evaluation system uses a rule-based approach with evidence tracking:

**Quality Dimensions:**
- **Code Quality** (40 points): Static linting, builds, security scans, module documentation
- **Testing** (35 points): Automated tests, coverage, integration tests, result documentation
- **Documentation** (25 points): README guide, configuration setup, API documentation

**Evaluation Process:**
1. Load submission.json from metrics collection
2. Apply 11-item checklist with language-specific adaptations
3. Generate evidence for each evaluation decision with confidence levels
4. Score items as "met" (full points), "partial" (half points), or "unmet" (0 points)
5. Create structured output for LLM processing and human-readable reports

### Error Handling Strategy
- **Critical failures**: Repository access, invalid URLs, tool crashes
- **Warnings**: Missing tools, partial results, performance issues
- **Graceful degradation**: Continue analysis when individual tools fail
- **Timeout handling**: Individual tools and global pipeline timeouts

## Testing Architecture

### Test Categories
- **Unit tests** (`tests/unit/`): Individual component testing including checklist evaluation components
- **Integration tests** (`tests/integration/`): End-to-end workflow testing including full evaluation pipeline
- **Contract tests** (`tests/contract/`): Schema validation for both submission.json and score_input.json formats

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
- Use `--verbose` flag for detailed execution logging in both pipelines
- Check `htmlcov/` directory for test coverage analysis
- Examine `output/` directory for generated reports and error logs
- Inspect `evidence/` directory for detailed evaluation evidence files
- Run contract tests to validate output format compliance
- Use `uv run python -c "from src.metrics.checklist_loader import ChecklistLoader; print(ChecklistLoader().validate_checklist_config())"` to validate checklist configuration

## Key Implementation Notes

### Evidence System Architecture
Evidence files are organized by dimension (`evidence/code_quality/`, `evidence/testing/`, `evidence/documentation/`, `evidence/system/`) with each file containing detailed JSON data supporting evaluation decisions. The evidence system ensures transparency and auditability of all scoring decisions.

### Integration Points
- The `PipelineOutputManager` coordinates both pipelines and handles evidence file generation
- The `evaluate` CLI command can run independently on existing submission.json files
- The main analysis pipeline can optionally run checklist evaluation (default: enabled)
- Schema validation ensures compatibility between metrics collection and evaluation phases
