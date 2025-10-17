# Code Score

> **⚠️ Testing Philosophy**: This project follows a **strict no-mock policy**. All tests use real execution with actual tools, APIs, and file operations. See [MOCK_ELIMINATION_FINAL_REPORT.md](MOCK_ELIMINATION_FINAL_REPORT.md) for details.

## Code Score

Automated Git repository quality analysis with AI-powered reporting.

**Quick Links**: [Developer Guide](CLAUDE.md) | [API Reference](docs/api-reference.md) | [Documentation Guide](docs/GUIDE.md)

## Overview

Code Score analyzes any public Git repository and generates comprehensive quality reports across three integrated pipelines:

1. **Metrics Collection** - Automated linting, build checks, security scanning, and static test infrastructure inspection
2. **Checklist Evaluation** - 11-item quality scoring with evidence tracking
3. **LLM Report Generation** - AI-powered narrative reports via DeepSeek

**Use Cases**: Hackathon judging, code review automation, project quality assessment

## Features

- **Multi-language support** (Python, JavaScript/TypeScript, Java, Go)
- **Automated build validation** across all supported languages
- **Evidence-based scoring** with 11-item quality checklist
- **AI-generated narrative reports** using DeepSeek
- **Standardized JSON/Markdown output** with schema validation
- **Static test inference** for MVP: detects test suites/CI metadata without executing user tests
- **Performance optimized** for large repositories (500MB limit)

## Prerequisites

- **Python 3.11+**
- **UV package manager**: Install from [astral.sh/uv](https://astral.sh/uv)
- **Git**: For repository cloning
- **llm CLI with DeepSeek** (optional): For AI report generation - [setup guide](https://llm.datasette.io/)

### Optional Analysis Tools

The tool automatically detects and uses language-specific tools:
- **Python**: `ruff` (linting), `pip-audit` (security), `uv build`/`python -m build` (build validation)
- **JavaScript**: `eslint` (linting), `npm audit` (security), `npm`/`yarn` (build validation)
- **Java**: `checkstyle` (linting), `spotbugs` (security), `maven`/`gradle` (build validation)
- **Go**: `golangci-lint` (linting), `gosec` (security), `go build` (build validation)

> 🧪 **Testing in MVP**: We do **not** execute repository test suites yet. The testing dimension is scored from statically detected test files, framework configs, coverage tooling, and CI metadata. Please ensure these artifacts live in the target repository (e.g., `tests/`, `coverage/`, CI workflow files, saved test reports) so Code Score can credit them.

## Installation

```bash
# Clone and setup
git clone https://github.com/your-org/code-score.git
cd code-score

# Install UV (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Verify installation
./scripts/run_metrics.sh --help
uv run pytest
```

## Usage

### Basic Analysis

```bash
# Analyze repository with full pipeline
./scripts/run_metrics.sh https://github.com/user/repo.git

# Analyze specific commit
./scripts/run_metrics.sh https://github.com/user/repo.git <commit-sha>

# Custom options
./scripts/run_metrics.sh https://github.com/user/repo.git \
  --output-dir ./results \
  --timeout 600 \
  --verbose
```

### Checklist Evaluation

```bash
# Integrated (default - runs with analysis)
./scripts/run_metrics.sh https://github.com/user/repo.git --enable-checklist

# Standalone evaluation
uv run python -m src.cli.evaluate output/submission.json --verbose
```

### AI Report Generation

**Setup llm CLI with DeepSeek** (one-time):
```bash
# Install llm CLI and DeepSeek plugin
uv tool install llm
llm install llm-deepseek

# Set API key
export DEEPSEEK_API_KEY="your-api-key-here"
llm --version  # Verify installation
```

**Generate Reports**:
```bash
# Generate AI report from evaluation data
uv run python -m src.cli.llm_report output/score_input.json

# Integrated workflow (analysis + evaluation + AI report)
./scripts/run_metrics.sh https://github.com/user/repo.git --generate-llm-report

# Custom template
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt ./templates/custom.md \
  --output ./report.md
```

## Testing Evidence (MVP)

- **Commit the artifacts**: Include `tests/` directories, framework configs (e.g., `pytest.ini`, `package.json` scripts), CI workflows, and the most recent test/coverage reports inside the repository. Code Score only inspects the repository contents.
- **Static-only scoring**: During the MVP, testing scores are inferred from these artifacts (`test_execution.calculated_score`, `coverage_config_detected`, `ci_platform`, etc.). We do not execute the target project's tests yet.
- **Future roadmap**: A secure test runner will arrive in the next milestone to execute suites and validate submitted reports against real runs.

## Output Files

### Metrics Collection
| File | Description |
|------|-------------|
| `output/submission.json` | Raw metrics data (consolidated) |
| `output/metrics/{repo}_{timestamp}.md` | Human-readable analysis (timestamped) |
| `output/metrics/{repo}_{timestamp}.json` | Detailed metrics data (timestamped) |

**Finding latest file**: `ls -lt output/metrics/*.md | head -1`

### Checklist Evaluation
| File | Description |
|------|-------------|
| `output/score_input.json` | Structured evaluation for LLM processing |
| `output/evaluation_report.md` | Human-readable quality assessment |
| `evidence/*.json` | Detailed evidence files by category |

### LLM Reports
| File | Description |
|------|-------------|
| `output/final_report.md` | AI-generated narrative report (fixed name) |
| `output/generation_metadata.json` | Generation statistics |

**Note**: Metrics files use timestamps to prevent overwrites. LLM reports use fixed filename `final_report.md` (customizable via `--output` flag).

## JSON Schema Examples

### Metrics Collection Output (submission.json)

```json
{
  "schema_version": "1.0.0",
  "repository": {
    "url": "https://github.com/user/repo.git",
    "commit": "abc123...",
    "language": "python",
    "size_mb": 12.5
  },
  "metrics": {
    "code_quality": {
      "lint_results": {"tool_used": "ruff", "passed": true, "issues_count": 0},
      "build_success": true,
      "build_details": {
        "success": true,
        "tool_used": "uv",
        "execution_time_seconds": 3.2,
        "error_message": null,
        "exit_code": 0
      },
      "dependency_audit": {"vulnerabilities_found": 0, "tool_used": "pip-audit"}
    },
    "testing": {
      "test_execution": {
        "test_files_detected": 18,
        "test_config_detected": true,
        "coverage_config_detected": true,
        "test_file_ratio": 0.14,
        "framework": "pytest",
        "ci_platform": "github_actions",
        "ci_score": 8,
        "calculated_score": 26,
        "phase1_score": 18,
        "phase2_score": 8,
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0
      }
    },
    "documentation": {
      "readme_present": true,
      "readme_quality_score": 0.85
    }
  }
}
```

### Evaluation Output (score_input.json)

```json
{
  "schema_version": "1.0.0",
  "repository_info": {"url": "...", "primary_language": "python"},
  "evaluation_result": {
    "total_score": 67.5,
    "max_possible_score": 100,
    "category_breakdowns": {
      "code_quality": {"score": 22.0, "max_points": 40},
      "testing": {"score": 24.0, "max_points": 35},
      "documentation": {"score": 21.5, "max_points": 25}
    }
  }
}
```

## Custom Templates (Jinja2)

Create custom AI report templates using Jinja2 syntax:

```jinja2
# Code Quality Report

**Repository**: {{repository.url}}
**Score**: {{total.score}}/100 ({{total.percentage}}%)

## Strengths
{% for item in met_items %}
- ✅ **{{item.name}}**: {{item.description}}
{% endfor %}

## Improvements Needed
{% for item in unmet_items %}
- ❌ **{{item.name}}**: {{item.description}}
{% endfor %}
```

See [template_docs.md](specs/prompts/template_docs.md) for available fields.

## Quality Dimensions

The 11-item checklist evaluates across three dimensions:

| Dimension | Points | Criteria |
|-----------|--------|----------|
| **Code Quality** | 40 | Static linting, builds, security scans, documentation |
| **Testing** | 35 | Static evidence of automated tests, coverage tooling, CI metadata |
| **Documentation** | 25 | README guide, setup instructions, API docs |

## Performance Limits

- **Repository size**: 500MB maximum
- **File count warning**: >10,000 files
- **Tool timeout**: 2 minutes per tool
- **Global timeout**: 300 seconds (customizable via `--timeout`)

## Development

### Testing
```bash
uv run pytest                    # All tests
uv run pytest tests/unit/       # Unit tests only
uv run pytest --cov=src         # With coverage
```

### Code Quality
```bash
uv run ruff check src/ tests/   # Linting
uv run ruff format src/ tests/  # Formatting
uv run mypy src/                # Type checking
```

### Project Structure
```
code-score/
├── src/
│   ├── cli/           # Command-line interface (main, evaluate, llm_report)
│   ├── metrics/       # Analysis pipeline (git, detection, executors, evaluators)
│   └── llm/           # LLM report generation (templates, prompts, generators)
├── tests/             # Unit, integration, contract tests
├── specs/             # Schemas, contracts, templates
└── scripts/           # Entry point (run_metrics.sh)
```

## Troubleshooting

**Repository cloning fails**
- Check URL format and access permissions

**Tool timeouts**
- Increase with `--timeout 600` or check repository size

**LLM generation fails**
- Verify llm CLI: `which llm`
- Check API key: `echo $DEEPSEEK_API_KEY`
- Use validation mode: `uv run python -m src.cli.llm_report --validate-only`

**Missing analysis tools**
- Tool-specific analysis degrades gracefully
- Install optional tools for enhanced coverage
- Use `--verbose` to see which tools are detected

## Configuration

### Environment Variables
- `DEEPSEEK_API_KEY`: Required for LLM report generation
- `METRICS_OUTPUT_DIR`: Override default output directory
- `METRICS_TOOL_TIMEOUT`: Override tool timeout (seconds)

### Custom Checklist
Modify [specs/contracts/checklist_mapping.yaml](specs/contracts/checklist_mapping.yaml) to customize evaluation criteria.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests first (TDD)
4. Ensure all tests pass: `uv run pytest`
5. Submit pull request

## Project Principles

1. **UV-only dependency management** - No pip/conda/poetry
2. **KISS principle** - Simple, fail-fast error handling
3. **Transparent logging** - Clear error messages for debugging

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see LICENSE file for details.
