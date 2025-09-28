# Code Score

Parameterized Git repository metrics collection for automated code quality evaluation.

## Overview

Code Score is a CLI tool that automatically analyzes code quality metrics from any public Git repository. It supports multiple programming languages and provides standardized JSON/Markdown output for consistent evaluation across different projects.

Perfect for hackathon judging, code review automation, and project quality assessment.

## Features

- **Multi-language support**: Python, JavaScript/TypeScript, Java, Go
- **Comprehensive analysis**: Linting, testing, security audits, documentation quality
- **Checklist evaluation**: 11-item quality assessment with evidence-based scoring
- **Performance optimized**: Handles large repositories with timeout controls
- **Standardized output**: JSON and Markdown formats with schema validation
- **Evidence tracking**: Detailed audit trail for all evaluation decisions
- **Configurable timeouts**: Prevents hanging on problematic repositories
- **Error handling**: Graceful degradation when tools are unavailable
- **CLI integration**: Both analysis and evaluation commands available
- **LLM report generation**: AI-powered narrative reports using external LLM services

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

### Checklist Evaluation

After generating metrics, you can run the checklist evaluation system:

```bash
# Evaluate existing submission.json
uv run python -m src.cli.evaluate output/submission.json

# Custom output directory
uv run python -m src.cli.evaluate output/submission.json --output-dir results/

# Different output formats
uv run python -m src.cli.evaluate output/submission.json --format json      # JSON only
uv run python -m src.cli.evaluate output/submission.json --format markdown # Markdown only
uv run python -m src.cli.evaluate output/submission.json --format both     # Both (default)

# Custom checklist configuration
uv run python -m src.cli.evaluate output/submission.json --checklist-config custom_checklist.yaml

# Validation only (check input without generating outputs)
uv run python -m src.cli.evaluate output/submission.json --validate-only

# Verbose evaluation with detailed progress
uv run python -m src.cli.evaluate output/submission.json --verbose
```

### Integrated Pipeline

The analysis command can automatically run checklist evaluation:

```bash
# Analysis with checklist evaluation (default)
./scripts/run_metrics.sh https://github.com/user/repo.git --enable-checklist

# Analysis without checklist evaluation
./scripts/run_metrics.sh https://github.com/user/repo.git --enable-checklist=false
```

### LLM Report Generation

The tool can generate human-readable reports using external Large Language Model (LLM) services. This feature transforms structured evaluation data into comprehensive, narrative reports suitable for code reviews, hackathon judging, and project documentation.

#### Prerequisites for LLM Features

**Gemini CLI** (required):
```bash
# Install Gemini CLI
# Follow installation instructions at: https://ai.google.dev/gemini-api/docs/quickstart

# Verify installation
gemini --version

# Set up API key (required)
export GEMINI_API_KEY="your-api-key-here"
```

> **Note**: Currently only Gemini is supported as the LLM provider in this MVP version.

#### Basic LLM Report Usage

```bash
# Generate report from existing evaluation data
uv run python -m src.cli.llm_report output/score_input.json

# Custom output path
uv run python -m src.cli.llm_report output/score_input.json --output ./reports/final_report.md

# Verbose mode with detailed progress
uv run python -m src.cli.llm_report output/score_input.json --verbose
```

#### Custom Templates

```bash
# Use custom report template
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt ./templates/hackathon_template.md \
  --output ./hackathon_evaluation.md
```

#### Integrated Workflow

```bash
# Complete analysis with automatic LLM report generation
./scripts/run_metrics.sh https://github.com/user/repo.git --generate-llm-report

# Custom LLM template
./scripts/run_metrics.sh https://github.com/user/repo.git \
  --generate-llm-report \
  --llm-template ./templates/custom.md
```

#### Template Customization

Create custom report templates using Jinja2 syntax:

```markdown
# Code Review Report for {{repository.url}}

## Executive Summary
- **Total Score**: {{total.score}}/100 ({{total.percentage}}%)
- **Grade**: {{total.grade_letter}}
- **Primary Language**: {{repository.primary_language}}

## Strengths
{{#each met_items}}
- ✅ **{{name}}**: {{description}}
{{/each}}

## Areas for Improvement
{{#each unmet_items}}
- ❌ **{{name}}**: {{description}}
{{/each}}

## Detailed Analysis
{{#each category_scores}}
### {{@key|title}}
- Score: {{score}}/{{max_points}} ({{percentage}}%)
- Status: {{status|title}}
{{/each}}
```

#### LLM Output

The LLM report generation produces:

**Files generated:**
- `final_report.md` - AI-generated narrative report
- `generation_metadata.json` - Generation details and statistics

**Report includes:**
- Executive summary with overall assessment
- Categorized strengths and improvement areas
- Evidence-based recommendations
- Project-specific insights and suggestions
- Actionable next steps for code quality improvement

#### Performance and Limitations

- **Generation time**: Typically 10-30 seconds using Gemini
- **Context limits**: Large evaluations are automatically truncated to fit Gemini's context window
- **Content quality**: Reports are generated from structured data and may require human review
- **Provider dependency**: Requires Gemini CLI installation and GEMINI_API_KEY configuration

#### Use Cases

**Hackathon Judging:**
```bash
# Process multiple repositories for evaluation
for repo in $(cat hackathon_repos.txt); do
  ./scripts/run_metrics.sh "$repo" --generate-llm-report --output-dir "results/$(basename $repo)"
done
```

**Code Review Preparation:**
```bash
# Generate detailed report for PR review using Gemini
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt templates/code_review.md \
  --output pr_review_summary.md
```

**Continuous Integration:**
```bash
# Add to CI pipeline
if ./scripts/run_metrics.sh "$CI_REPOSITORY_URL" --generate-llm-report; then
  # Upload final_report.md as CI artifact
  cp output/final_report.md "$CI_ARTIFACTS_DIR/"
fi
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

The tool generates multiple output files depending on the analysis mode:

### Basic Analysis Output

**Files generated:**
- `submission.json` - Raw metrics data
- `report.md` - Human-readable analysis report

### Checklist Evaluation Output

**Files generated:**
- `score_input.json` - Structured evaluation results for LLM processing
- `evaluation_report.md` - Detailed human-readable evaluation report
- `evidence/` directory - Detailed evidence files supporting all evaluation decisions

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

### Checklist Evaluation JSON Output

The evaluation system generates structured output for LLM processing:

```json
{
  "schema_version": "1.0.0",
  "repository_info": {
    "url": "https://github.com/user/repo.git",
    "commit_sha": "a1b2c3d4e5f6789012345678901234567890abcd",
    "primary_language": "python",
    "analysis_timestamp": "2025-09-27T10:30:00Z",
    "metrics_source": "output/submission.json"
  },
  "evaluation_result": {
    "checklist_items": [
      {
        "id": "code_quality_lint",
        "name": "Static Linting Passed",
        "dimension": "code_quality",
        "max_points": 15,
        "evaluation_status": "met",
        "score": 15.0,
        "evidence_references": [...]
      }
    ],
    "total_score": 67.5,
    "max_possible_score": 100,
    "score_percentage": 67.5,
    "category_breakdowns": {...},
    "evidence_summary": [...]
  },
  "human_summary": "# Code Quality Evaluation Report\n..."
}
```

### Markdown Output

The tool generates comprehensive human-readable reports with:
- Repository information and analysis context
- Code quality summary with pass/fail indicators
- Testing results and coverage analysis
- Documentation quality assessment
- Tool execution summary
- **Checklist evaluation** with detailed scoring breakdown
- **Evidence tracking** with confidence levels
- **Recommendations** for improvement

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
│   ├── cli/                     # Command-line interface
│   │   ├── main.py             # Main analysis CLI
│   │   └── evaluate.py         # Checklist evaluation CLI
│   └── metrics/                 # Core analysis modules
│       ├── models/              # Data models
│       │   ├── checklist_item.py
│       │   ├── evaluation_result.py
│       │   ├── score_input.py
│       │   ├── evidence_reference.py
│       │   └── category_breakdown.py
│       ├── tool_runners/        # Language-specific tools
│       │   ├── python_tools.py
│       │   ├── javascript_tools.py
│       │   ├── java_tools.py
│       │   └── golang_tools.py
│       ├── checklist_evaluator.py   # Core evaluation logic
│       ├── scoring_mapper.py        # Output formatting
│       ├── evidence_tracker.py     # Evidence management
│       ├── checklist_loader.py     # Configuration loading
│       ├── pipeline_output_manager.py # Pipeline integration
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
├── specs/                 # Design documentation
│   └── 002-git-log-docs/  # Checklist evaluation specs
│       ├── contracts/     # JSON schemas and YAML configs
│       ├── tasks.md       # Implementation tasks
│       ├── research.md    # Technical decisions
│       ├── data-model.md  # Data model documentation
│       └── quickstart.md  # Usage examples
└── CLAUDE.md              # Development guidelines
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
5. Update checklist configuration for language-specific adaptations
6. Update documentation

### Checklist Evaluation System

The checklist evaluation system provides standardized quality assessment:

**Core Components:**
- **ChecklistEvaluator**: Rule-based evaluation engine with 11 quality criteria
- **ScoringMapper**: Transforms evaluation results to structured output
- **EvidenceTracker**: Collects and organizes supporting evidence
- **ChecklistLoader**: Manages configuration and language adaptations

**Quality Dimensions:**
- **Code Quality** (40 points): Linting, builds, security, documentation
- **Testing** (35 points): Test automation, coverage, integration tests
- **Documentation** (25 points): README, setup, API documentation

**Evaluation Process:**
1. Load submission.json from metrics analysis
2. Apply 11-item checklist with language-specific adaptations
3. Generate evidence for each evaluation decision
4. Score items as "met", "partial", or "unmet"
5. Create structured output for LLM processing
6. Generate human-readable reports with recommendations

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