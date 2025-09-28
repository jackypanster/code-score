# Code Score Quickstart Guide

Get started with automated code quality analysis and AI-powered reporting.

## Prerequisites

- **Python 3.11+** with UV package manager
- **Git** installed and accessible
- **Internet access** for cloning repositories

## Installation

```bash
# Clone the repository
git clone https://github.com/jackypanster/code-score.git
cd code-score

# Install dependencies
uv sync

# Verify installation
uv run python -m src.cli.main --help
```

## Quick Start: End-to-End Analysis

### Basic Analysis with Checklist Evaluation

```bash
# Complete analysis with automatic quality assessment
./scripts/run_metrics.sh https://github.com/pallets/click.git --verbose

# Output shows:
# Analysis completed successfully!
# Generated files:
#   - ./output/submission.json      # Raw metrics data
#   - ./output/report.md           # Markdown summary
#   - ./output/score_input.json    # Structured evaluation
#   - ./output/evaluation_report.md # Human-readable assessment
# Evidence Files: 14 files in ./output/evidence/
```

### Two-Step Process (Metrics → Evaluation)

```bash
# Step 1: Generate metrics only
./scripts/run_metrics.sh https://github.com/pallets/click.git --enable-checklist=false

# Step 2: Run evaluation separately
uv run python -m src.cli.evaluate output/submission.json --verbose

# Output shows quality scores:
# 📊 Score: 67.5/100 (67.5%)
# 📈 Category Breakdown:
#    Code Quality: 22.0/40 (55.0%, Grade: F)
#    Testing: 24.0/35 (68.6%, Grade: D)
#    Documentation: 21.5/25 (86.0%, Grade: B)
```

## AI-Powered Report Generation

Generate human-readable evaluation reports using Gemini AI.

### Prerequisites for LLM Features

```bash
# Install Gemini CLI (follow official instructions)
# https://ai.google.dev/gemini-api/docs/quickstart

# Set up API key
export GEMINI_API_KEY="your-api-key-here"

# Verify installation
gemini --version
```

### Generate AI Reports

```bash
# Basic LLM report generation
uv run python -m src.cli.llm_report output/score_input.json

# Expected output:
# ✅ Template loaded: specs/prompts/llm_report.md
# ✅ Score data validated: 67.5/100 (67.5%)
# 🤖 Calling Gemini CLI...
# ✅ Report generated: output/final_report.md
```

### Integrated Workflow

```bash
# Complete analysis + AI report in one command
./scripts/run_metrics.sh https://github.com/pallets/click.git --generate-llm-report

# Custom template for specific use cases
./scripts/run_metrics.sh https://github.com/user/repo.git \
  --generate-llm-report \
  --llm-template ./templates/hackathon_template.md
```

## Real Example Walkthrough

Let's analyze a real repository step by step:

### 1. Repository Analysis

```bash
# Analyze the tiktoken repository with detailed logging
./scripts/run_metrics.sh https://github.com/openai/tiktoken.git --timeout 60 --verbose
```

### 2. Examine Results

```bash
# Check quality metrics
cat output/submission.json | jq '.metrics.code_quality.lint_results'

# Review evaluation scores
cat output/score_input.json | jq '.evaluation_result.total_score'

# Read assessment report
head -n 30 output/evaluation_report.md
```

### 3. Explore Evidence Files

```bash
# List evidence collected
find output/evidence -name "*.json" | head -5

# Examine specific evidence
cat output/evidence/code_quality/code_quality_lint_file_check.json | jq '.[0]'
```

### 4. Generate AI Report

```bash
# Create comprehensive narrative report
uv run python -m src.cli.llm_report output/score_input.json --verbose

# Review generated content
head -n 50 output/final_report.md
```

## Common Use Cases

### Hackathon Judging

```bash
# Process multiple repositories
for repo in $(cat hackathon_repos.txt); do
  ./scripts/run_metrics.sh "$repo" \
    --generate-llm-report \
    --output-dir "results/$(basename $repo)"
done
```

### Code Review Preparation

```bash
# Generate detailed review summary
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt templates/code_review_template.md \
  --output pr_review_summary.md
```

### Continuous Integration

```bash
# Add to CI pipeline
if ./scripts/run_metrics.sh "$CI_REPOSITORY_URL" --generate-llm-report; then
  # Upload reports as CI artifacts
  cp output/*.md "$CI_ARTIFACTS_DIR/"
fi
```

## CLI Commands Reference

### Main Analysis Command

```bash
# Basic usage
./scripts/run_metrics.sh <repository-url>

# With options
./scripts/run_metrics.sh <repository-url> [commit-sha] [options]

# Common options:
#   --output-dir DIR    # Custom output location
#   --format FORMAT     # json, markdown, both
#   --timeout SECONDS   # Analysis timeout
#   --verbose           # Detailed logging
#   --enable-checklist  # Quality evaluation (default: true)
#   --generate-llm-report # AI narrative reports
```

### Evaluation Command

```bash
# Evaluate existing metrics
uv run python -m src.cli.evaluate <submission.json> [options]

# Options:
#   --output-dir DIR    # Output location
#   --verbose           # Show detailed progress
#   --checklist-config  # Custom evaluation criteria
```

### LLM Report Command

```bash
# Generate AI report
uv run python -m src.cli.llm_report <score_input.json> [options]

# Options:
#   --output PATH       # Custom output file
#   --prompt PATH       # Custom template
#   --verbose           # Show generation details
#   --timeout SECONDS   # API call timeout
```

## Output Files Explained

| File | Description | Use Case |
|------|-------------|----------|
| `submission.json` | Raw metrics data | Machine processing, debugging |
| `report.md` | Human-readable summary | Quick overview, documentation |
| `score_input.json` | Structured evaluation | LLM input, detailed analysis |
| `evaluation_report.md` | Assessment breakdown | Quality review, improvement planning |
| `final_report.md` | AI-generated narrative | Executive summaries, presentations |
| `evidence/` | Supporting evidence files | Audit trails, detailed justification |

## Troubleshooting

### Common Issues

**Analysis fails with timeout:**
```bash
# Increase timeout for large repositories
./scripts/run_metrics.sh <repo-url> --timeout 1800
```

**Missing tools warnings:**
```bash
# Install optional analysis tools for better coverage
# Python: pip install ruff pytest
# JavaScript: npm install -g eslint jest
# Java: Install maven/gradle
```

**LLM generation fails:**
```bash
# Check Gemini CLI setup
gemini --version
echo $GEMINI_API_KEY

# Use validation mode
uv run python -m src.cli.llm_report --validate-only
```

## Next Steps

- Read the [API Reference](./api-reference.md) for programmatic usage
- Check [CLAUDE.md](../CLAUDE.md) for development guidelines
- Explore contract schemas in `specs/contracts/`
- Customize evaluation criteria with checklist configuration