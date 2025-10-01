# Code Score

Automated Git repository quality analysis with AI-powered reporting.

**Quick Links**: [Developer Guide](CLAUDE.md) | [API Reference](docs/api-reference.md) | [Documentation Guide](docs/GUIDE.md)

## Overview

Code Score analyzes any public Git repository and generates comprehensive quality reports across three integrated pipelines:

1. **Metrics Collection** - Automated linting, testing, and security analysis
2. **Checklist Evaluation** - 11-item quality scoring with evidence tracking
3. **LLM Report Generation** - AI-powered narrative reports via Gemini

**Use Cases**: Hackathon judging, code review automation, project quality assessment

## Features

- Multi-language support (Python, JavaScript/TypeScript, Java, Go)
- Evidence-based scoring with 11-item quality checklist
- AI-generated narrative reports using Gemini
- Standardized JSON/Markdown output with schema validation
- Performance optimized for large repositories (500MB limit)

## Prerequisites

- **Python 3.11+**
- **UV package manager**: Install from [astral.sh/uv](https://astral.sh/uv)
- **Git**: For repository cloning
- **Gemini CLI** (optional): For AI report generation - [setup guide](https://ai.google.dev/gemini-api/docs/quickstart)

### Optional Analysis Tools

The tool automatically detects and uses language-specific tools:
- **Python**: `ruff`, `pytest`, `pip-audit`
- **JavaScript**: `eslint`, `jest`, `npm audit`
- **Java**: `checkstyle`, `maven`/`gradle`, `spotbugs`
- **Go**: `golangci-lint`, `go test`, `gosec`

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

**Setup Gemini** (one-time):
```bash
# Install Gemini CLI and set API key
export GEMINI_API_KEY="your-api-key-here"
gemini --version  # Verify installation
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
      "dependency_audit": {"vulnerabilities_found": 0, "tool_used": "pip-audit"}
    },
    "testing": {
      "test_execution": {"tests_run": 45, "tests_passed": 43, "framework": "pytest"}
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
| **Testing** | 35 | Automated tests, coverage, integration tests |
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
- Verify Gemini CLI: `which gemini`
- Check API key: `echo $GEMINI_API_KEY`
- Use validation mode: `uv run python -m src.cli.llm_report --validate-only`

**Missing analysis tools**
- Tool-specific analysis degrades gracefully
- Install optional tools for enhanced coverage
- Use `--verbose` to see which tools are detected

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Required for LLM report generation
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
