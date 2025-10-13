# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Code Score is a parameterized Git repository metrics collection tool with integrated checklist evaluation for automated code quality assessment. It analyzes any public Git repository and produces standardized JSON/Markdown reports with evidence-based scoring suitable for hackathon judging, code review automation, and project quality assessment.

The system consists of three integrated pipelines:
1. **Metrics Collection Pipeline**: Collects raw quality metrics (linting, testing, documentation)
2. **Checklist Evaluation Pipeline**: Evaluates metrics against 11-item quality checklist with evidence tracking
3. **LLM Report Generation Pipeline**: Transforms structured data into human-readable narrative reports using Gemini

## Core Architecture

### Triple Pipeline Architecture

**Metrics Collection Pipeline**: **Clone → Detect → Analyze → Report → Cleanup**
1. **Git Operations** ([src/metrics/git_operations.py](src/metrics/git_operations.py)): Repository cloning and commit switching
2. **Language Detection** ([src/metrics/language_detection.py](src/metrics/language_detection.py)): Identifies primary programming language
3. **Tool Execution** ([src/metrics/tool_executor.py](src/metrics/tool_executor.py)): Parallel execution of language-specific tools
4. **Tool Runners** ([src/metrics/tool_runners/](src/metrics/tool_runners/)): Language-specific analysis implementations (Python, JavaScript, Java, Go)
5. **Output Generation** ([src/metrics/output_generators.py](src/metrics/output_generators.py)): Produces submission.json

**Checklist Evaluation Pipeline**: **Load → Evaluate → Evidence → Score → Report**
1. **ChecklistEvaluator** ([src/metrics/checklist_evaluator.py](src/metrics/checklist_evaluator.py)): Rule-based evaluation engine with 11 quality criteria
2. **EvidenceTracker** ([src/metrics/evidence_tracker.py](src/metrics/evidence_tracker.py)): Collects and organizes supporting evidence with confidence levels
3. **ScoringMapper** ([src/metrics/scoring_mapper.py](src/metrics/scoring_mapper.py)): Transforms evaluation results to structured output for LLM processing
4. **ChecklistLoader** ([src/metrics/checklist_loader.py](src/metrics/checklist_loader.py)): Manages configuration and language adaptations
5. **PipelineOutputManager** ([src/metrics/pipeline_output_manager.py](src/metrics/pipeline_output_manager.py)): Integrates both pipelines

**LLM Report Generation Pipeline**: **Template → Build → Execute → Format**
1. **TemplateLoader** ([src/llm/template_loader.py](src/llm/template_loader.py)): Loads and validates Jinja2 templates from specs/prompts/
2. **PromptBuilder** ([src/llm/prompt_builder.py](src/llm/prompt_builder.py)): Constructs prompts from score_input.json and templates
3. **ReportGenerator** ([src/llm/report_generator.py](src/llm/report_generator.py)): Executes Gemini CLI for report generation
4. **Output Formatter**: Generates final_report.md and generation_metadata.json

### Multi-Language Tool Runners
- **Python**: `ruff`/`flake8` (linting), `pytest` (testing), `pip-audit` (security)
- **JavaScript/TypeScript**: `eslint` (linting), `jest`/`mocha` (testing), `npm audit` (security)
- **Java**: `checkstyle` (linting), `maven`/`gradle` (testing), `spotbugs` (security)
- **Go**: `golangci-lint`/`gofmt` (linting), `go test` (testing), `gosec` (security)

### Static Test Infrastructure Analyzer (NEW - COD-8)
**Purpose**: Zero-execution static analysis of test infrastructure to recover Testing dimension scoring without running code.

**Components** ([specs/004-static-test-infrastructure/](specs/004-static-test-infrastructure/)):
1. **TestInfrastructureAnalyzer** ([src/metrics/test_infrastructure_analyzer.py](src/metrics/test_infrastructure_analyzer.py)): Core analyzer with multi-language support
2. **Config Parsers** ([src/metrics/config_parsers/](src/metrics/config_parsers/)): Language-specific configuration file parsers (TOML, JSON, XML, Makefile)
3. **TestInfrastructureResult** ([src/metrics/models/test_infrastructure.py](src/metrics/models/test_infrastructure.py)): Data model for analysis results

**Key Features**:
- **Zero Code Execution**: Analyzes files without running tests (<1s, safe)
- **Multi-Language Detection**: Supports Python, JavaScript, Go, Java with automatic language detection
- **Score Recovery**: Restores 15-25/25 points in Testing dimension through static analysis
- **Config Detection**: Identifies test frameworks (pytest, jest, JUnit) and coverage tools
- **Test File Discovery**: Pattern-based detection (`test_*.py`, `*.test.js`, `*_test.go`, `src/test/java/`)

**Analysis Output** (5 new fields in `test_execution`):
```json
{
  "test_files_detected": 43,           // Number of test files found
  "test_config_detected": true,        // Framework config exists
  "coverage_config_detected": false,   // Coverage config exists
  "test_file_ratio": 0.107,           // Test files / total files
  "calculated_score": 15              // Static score 0-25
}
```

**Scoring Logic**:
- 5 points: Test files present (`test_files_detected > 0`)
- 5 points: Test configuration detected (`pytest.ini`, `package.json`, etc.)
- 5 points: Coverage configuration detected (`.coveragerc`, `jest.config.json`)
- 0-10 points: Test file ratio bonus (10% = 5pts, 30% = 10pts)
- Max: 25 points (capped per FR-013)

**Integration**: All 4 tool runners (`python_tools.py`, `javascript_tools.py`, `golang_tools.py`, `java_tools.py`) now use `TestInfrastructureAnalyzer` instead of executing tests, enabling safe, fast analysis.

### Toolchain Validation Layer (FR-003 Fail-Fast)
**Purpose**: Pre-flight validation to prevent partial analysis due to missing/outdated tools

**Components** ([specs/002-toolexecutor-toolchainmanager-cli/](specs/002-toolexecutor-toolchainmanager-cli/)):
1. **ToolRegistry** ([src/metrics/tool_registry.py](src/metrics/tool_registry.py)): Centralized registry of tool requirements for all languages (global + language-specific)
2. **ToolDetector** ([src/metrics/tool_detector.py](src/metrics/tool_detector.py)): Low-level tool availability, version, and permission checking
3. **ToolchainManager** ([src/metrics/toolchain_manager.py](src/metrics/toolchain_manager.py)): High-level validation orchestrator that groups errors by category
4. **ValidationModels** ([src/metrics/models/](src/metrics/models/)): ToolRequirement, ValidationResult, ValidationReport data models
5. **Chinese Messages** ([src/metrics/toolchain_messages.py](src/metrics/toolchain_messages.py)): User-facing error message templates with documentation URLs

**Validation Flow**:
```
CLI Entry → ToolchainManager.validate_for_language(language) →
Load tools (global + language-specific) →
For each tool:
  - Check PATH availability (shutil.which)
  - Verify execute permissions (os.access)
  - Extract version (subprocess with 3-second timeout, accommodates JVM tools)
  - Compare semver (tuple comparison)
  - Create ValidationResult →
Group errors by category (missing/outdated/permission/other) →
If any errors: raise ToolchainValidationError (Chinese formatted) →
Otherwise: continue analysis
```

**Key Features**:
- **Language-specific validation** (FR-007): Only checks tools for detected language + global tools (git, uv)
- **Version enforcement** (FR-015): Validates minimum versions (Python ≥3.11, npm ≥8.0, Java ≥17)
- **Permission diagnostics** (FR-016): Reports exact path and Unix permissions for non-executable tools
- **Error categorization** (FR-017): Groups all errors into clear categories for efficient debugging
- **Emergency bypass**: `--skip-toolchain-check` flag for debugging scenarios
- **Performance**: <10 seconds validation time, 3-second per-tool timeout (accommodates JVM startup)

**Testing**: 136 tests (23 contract + 96 unit + 10 integration + 7 smoke), 96-100% coverage

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
uv run pytest tests/integration/   # Integration tests (currently smoke tests)
uv run pytest tests/contract/      # Schema validation tests
uv run pytest tests/smoke/          # End-to-end smoke tests

# Run individual test files or functions
uv run pytest tests/unit/test_language_detection.py -v
uv run pytest tests/unit/test_checklist_evaluator_path.py::test_specific_function -v

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

### LLM Report Generation Workflow
```bash
# Generate human-readable report from evaluation data
uv run python -m src.cli.llm_report output/score_input.json

# Custom output path and template
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt ./templates/custom.md \
  --output ./reports/final.md

# Integrated workflow (analysis + evaluation + LLM report)
./scripts/run_metrics.sh https://github.com/user/repo.git --generate-llm-report

# Validation without generation
uv run python -m src.cli.llm_report output/score_input.json --validate-only
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
- **TestInfrastructureResult** (NEW): Static test infrastructure analysis results (test_files_detected, test_config_detected, coverage_config_detected, test_file_ratio, calculated_score)
- **DocumentationMetrics**: README analysis and documentation quality
- **ExecutionMetadata**: Tool execution tracking and performance data

### Checklist Evaluation Models ([src/metrics/models/](src/metrics/models/))
- **ChecklistItem**: Individual evaluation criterion with scoring and evidence
- **EvaluationResult**: Complete evaluation with 11 items, scores, and category breakdowns
- **ScoreInput**: LLM-ready structured output format
- **EvidenceReference**: Supporting evidence with confidence levels and source tracking
- **CategoryBreakdown**: Score summaries by dimension (Code Quality, Testing, Documentation)

### LLM Models ([src/llm/models/](src/llm/models/))
- **LLMProviderConfig**: Configuration for LLM providers (Gemini settings, timeouts, API keys)
- **ReportTemplate**: Template metadata and validation for Jinja2 templates
- **GeneratedReport**: Container for generated reports with metadata and statistics

### Output Schema
**Metrics Collection** produces `submission.json` with:
- `schema_version`, `repository`, `metrics`, `execution`

**Checklist Evaluation** produces `score_input.json` with:
- `evaluation_result`: 11-item checklist scores with evidence
- `repository_info`: Analysis context and metadata
- `evidence_paths`: File paths to detailed evidence files
- `human_summary`: Comprehensive markdown evaluation report

**LLM Report Generation** produces:
- `final_report.md`: Human-readable narrative report
- `generation_metadata.json`: Generation statistics and provider info

### CLI Command Structure
The tool provides three main CLI commands ([src/cli/](src/cli/)):

1. **Main Analysis** ([main.py](src/cli/main.py)): `uv run python -m src.cli.main <repo_url>`
   - Entry point for repository analysis
   - Coordinates metrics collection and optional checklist evaluation
   - Can trigger LLM report generation via `--generate-llm-report` flag

2. **Checklist Evaluation** ([evaluate.py](src/cli/evaluate.py)): `uv run python -m src.cli.evaluate <submission_json>`
   - Standalone checklist evaluation from existing metrics
   - Generates score_input.json and evaluation reports
   - Can run independently of metrics collection

3. **LLM Report** ([llm_report.py](src/cli/llm_report.py)): `uv run python -m src.cli.llm_report <score_input_json>`
   - Generates human-readable reports from evaluation data
   - Supports custom templates and output paths
   - Requires Gemini CLI and GEMINI_API_KEY

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
- `GEMINI_API_KEY`: Required for LLM report generation (Gemini provider)

### Tool Detection Logic
- Check tool availability before execution
- Prefer more comprehensive tools (e.g., `ruff` over `flake8`)
- Fallback to simpler alternatives when advanced tools unavailable
- Clear error messages when required tools missing

### Checklist Configuration
- Default checklist: [specs/contracts/checklist_mapping.yaml](specs/contracts/checklist_mapping.yaml)
- Contains 11 evaluation criteria with scoring rules and metrics mappings
- Language-specific adaptations can be defined for each checklist item
- Custom checklists can be provided via `--checklist-config` flag to the evaluate command

## Debugging and Troubleshooting

### Common Issues
- **Repository cloning failures**: Check URL format and access permissions
- **Tool timeouts**: Increase timeout or check repository size
- **Missing tool dependencies**: Install language-specific tools or use `--verbose` for details
- **Schema validation errors**: Check JSON output structure against contract tests
- **LLM report generation failures**:
  - Verify Gemini CLI is installed: `which gemini`
  - Check `GEMINI_API_KEY` environment variable is set: `echo $GEMINI_API_KEY`
  - Ensure score_input.json exists and is valid
  - Use `--validate-only` flag to test prerequisites without generating report

### Debugging Techniques
- Use `--verbose` flag for detailed execution logging in all pipelines
- Check [htmlcov/](htmlcov/) directory for test coverage analysis (run `uv run pytest --cov=src --cov-report=html`)
- Examine [output/](output/) directory for generated reports and error logs
- Inspect [evidence/](evidence/) directory for detailed evaluation evidence files
- Run contract tests to validate output format compliance: `uv run pytest tests/contract/ -v`
- Validate checklist configuration: `uv run python -c "from src.metrics.checklist_loader import ChecklistLoader; print(ChecklistLoader().validate_checklist_config())"`
- Test LLM report generation in validation mode: `uv run python -m src.cli.llm_report output/score_input.json --validate-only`
- Check Gemini CLI availability: `which gemini` or `gemini --version`

## Key Implementation Notes

### Evidence System Architecture
Evidence files are organized by dimension (`evidence/code_quality/`, `evidence/testing/`, `evidence/documentation/`, `evidence/system/`) with each file containing detailed JSON data supporting evaluation decisions. The evidence system ensures transparency and auditability of all scoring decisions.

### Integration Points
- The `PipelineOutputManager` coordinates metrics collection and checklist evaluation pipelines
- The `evaluate` CLI command ([src/cli/evaluate.py](src/cli/evaluate.py)) can run independently on existing submission.json files
- The `llm-report` CLI command ([src/cli/llm_report.py](src/cli/llm_report.py)) generates reports from score_input.json files
- The main analysis pipeline can optionally run checklist evaluation (default: enabled)
- LLM report generation requires Gemini CLI installation and GEMINI_API_KEY environment variable
- Schema validation ensures compatibility between all pipeline phases

### LLM Report Generation Details
**Prerequisites:**
- Gemini CLI must be installed and available in PATH
- `GEMINI_API_KEY` environment variable must be set
- Currently only Gemini provider is supported (OpenAI/Claude support planned)

**Template System:**
- Templates use Jinja2 syntax and are located in [specs/prompts/](specs/prompts/)
- Default template: [specs/prompts/llm_report.md](specs/prompts/llm_report.md)
- Templates receive full score_input.json context including evaluation results, evidence, and repository metadata
- Custom templates can be provided via `--prompt` flag

**Output Files:**
- `final_report.md`: AI-generated narrative evaluation report
- `generation_metadata.json`: Generation statistics and provider information

**Performance:**
- Typical generation time: 10-30 seconds (Gemini)
- Large evaluations are automatically truncated to fit context window
- Timeout defaults to provider-specific values (customizable via `--timeout`)
- 使用Google Gemini 2.5 Pro Preview (gemini-2.5-pro-preview-03-25)模型进行测试，如果有问题请及时提出！
