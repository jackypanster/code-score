# Quickstart: Checklist Evaluation System

## Overview
This quickstart guide demonstrates the complete checklist evaluation system that converts repository metrics into structured scoring input for automated code quality assessment.

## Prerequisites
- Python 3.11+ with UV package manager
- Git installed and accessible
- Internet access for cloning test repositories

## Installation
```bash
# Clone the repository
git clone https://github.com/your-org/code-score.git
cd code-score

# Install dependencies
uv sync

# Verify installation
uv run python -m src.cli.main --help
```

## Quick Start: Complete Pipeline

### 1. Analyze a Repository with Checklist Evaluation
```bash
# Complete analysis with automatic checklist evaluation
./scripts/run_metrics.sh https://github.com/pallets/click.git --verbose --enable-checklist

# Output shows:
# Analysis completed successfully!
# Generated files:
#   - ./output/submission.json
#   - ./output/report.md
#   - ./output/score_input.json          # ← Checklist evaluation
#   - ./output/evaluation_report.md      # ← Human-readable evaluation
#   Evidence Files: 14 files in ./output/evidence
```

### 2. Evaluate Existing Metrics (Two-Step Process)
```bash
# Step 1: Generate metrics only
./scripts/run_metrics.sh https://github.com/pallets/click.git --enable-checklist=false

# Step 2: Run checklist evaluation separately
uv run python -m src.cli.evaluate output/submission.json --output-dir results/ --verbose

# Output shows:
# 🎉 Evaluation completed successfully!
# 📊 Score: 67.5/100 (67.5%)
# 📈 Category Breakdown:
#    Code Quality: 22.0/40 (55.0%, Grade: F)
#    Testing: 24.0/35 (68.6%, Grade: D)
#    Documentation: 21.5/25 (86.0%, Grade: B)
# 📋 Items: 6 met, 2 partial, 3 unmet
```

## Real Example Walkthrough

Let's walk through a complete example using a real repository:

### Step 1: Analyze Repository
```bash
# Analyze the tiktoken repository
./scripts/run_metrics.sh https://github.com/openai/tiktoken.git --timeout 60 --verbose
```

### Step 2: Review Generated Files
```bash
# Check the basic metrics
cat output/submission.json | jq '.metrics.code_quality.lint_results'

# Review the evaluation results
cat output/score_input.json | jq '.evaluation_result.total_score'

# Read the human-friendly report
head -n 30 output/evaluation_report.md
```

### Step 3: Examine Evidence Files
```bash
# List evidence files
find output/evidence -name "*.json" | head -5

# Check a specific evidence file
cat output/evidence/code_quality/code_quality_lint_file_check.json | jq '.[0]'
```

## CLI Commands Reference

### Analyze Command (Main Pipeline)
```bash
# Basic usage
./scripts/run_metrics.sh <repository-url>

# With checklist evaluation (default)
./scripts/run_metrics.sh <repository-url> --enable-checklist

# Without checklist evaluation
./scripts/run_metrics.sh <repository-url> --enable-checklist=false

# Custom options
./scripts/run_metrics.sh <repository-url> \
  --output-dir ./results \
  --timeout 120 \
  --verbose \
  --checklist-config path/to/custom_checklist.yaml
```

### Evaluate Command (Checklist Only)
```bash
# Basic evaluation
uv run python -m src.cli.evaluate submission.json

# Custom output directory
uv run python -m src.cli.evaluate submission.json --output-dir results/

# Different output formats
uv run python -m src.cli.evaluate submission.json --format json      # JSON only
uv run python -m src.cli.evaluate submission.json --format markdown # Markdown only
uv run python -m src.cli.evaluate submission.json --format both     # Both (default)

# Validation only (no output generation)
uv run python -m src.cli.evaluate submission.json --validate-only

# Verbose output with progress
uv run python -m src.cli.evaluate submission.json --verbose
```

## Real Output Examples

### Sample Score Input JSON
```json
{
  "schema_version": "1.0.0",
  "repository_info": {
    "url": "https://github.com/openai/tiktoken.git",
    "commit_sha": "abc123def456",
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
        "evidence_references": [
          {
            "source_type": "file_check",
            "source_path": "$.metrics.code_quality.lint_results.passed",
            "description": "Checked lint_results.passed: expected True, got True",
            "confidence": 0.95,
            "raw_data": "True"
          }
        ]
      }
    ],
    "total_score": 67.5,
    "max_possible_score": 100,
    "score_percentage": 67.5,
    "category_breakdowns": {
      "code_quality": {
        "dimension": "code_quality",
        "items_count": 4,
        "max_points": 40,
        "actual_points": 22.0,
        "percentage": 55.0
      }
    }
  }
}
```

### Sample Evaluation Report
```markdown
# Code Quality Evaluation Report

**Repository:** https://github.com/openai/tiktoken.git
**Commit:** abc123def456
**Language:** python
**Analysis Date:** 2025-09-27 10:30:00 UTC

## Executive Summary

**Overall Score:** 67.5 / 100 (67.5%)
**Processing Time:** 0.12 seconds
**Metrics Completeness:** 95.0%

**Grade: D** - Below-average code quality requiring significant improvements.

## Category Performance

### Code Quality - Grade F
- **Score:** 22.0 / 40 (55.0%)
- **Items Evaluated:** 4

### Testing - Grade D
- **Score:** 24.0 / 35 (68.6%)
- **Items Evaluated:** 4

### Documentation - Grade B
- **Score:** 21.5 / 25 (86.0%)
- **Items Evaluated:** 3

## Key Insights

- Score distribution: 6 items fully met, 2 partially met, 3 unmet
- Strongest area: Documentation (86.0%)
- Weakest area: Code Quality (55.0%)

## Recommendations

- Implement static linting (e.g., ruff for Python, eslint for JavaScript)
- Set up automated builds and dependency security scanning
- Add automated tests with coverage reporting (target: >60% coverage)
```

## Testing the System

### Run All Tests
```bash
# Contract tests (schema validation)
uv run pytest tests/contract/ -v

# Integration tests (end-to-end workflows)
uv run pytest tests/integration/ -v

# Unit tests (individual components)
uv run pytest tests/unit/ -v

# All tests with coverage
uv run pytest --cov=src
```

### Test with Different Repository Types

```bash
# Python repository (good test coverage)
./scripts/run_metrics.sh https://github.com/pallets/click.git

# JavaScript repository
./scripts/run_metrics.sh https://github.com/lodash/lodash.git

# Go repository
./scripts/run_metrics.sh https://github.com/gin-gonic/gin.git

# Java repository
./scripts/run_metrics.sh https://github.com/spring-projects/spring-boot.git
```

## Customization

### Custom Checklist Configuration
```bash
# Copy default configuration
cp specs/002-git-log-docs/contracts/checklist_mapping.yaml my_checklist.yaml

# Edit your custom criteria
nano my_checklist.yaml

# Use custom configuration
uv run python -m src.cli.evaluate submission.json --checklist-config my_checklist.yaml
```

### Language-Specific Adaptations
The system automatically adapts evaluation criteria based on detected language:
- **Python**: Uses ruff/flake8 for linting, pytest for testing
- **JavaScript**: Uses eslint for linting, jest/mocha for testing
- **Java**: Uses checkstyle for linting, maven/gradle for testing
- **Go**: Uses golangci-lint for linting, go test for testing

## Performance Expectations

- **Small repositories** (<10MB): ~10-30 seconds
- **Medium repositories** (10-100MB): ~30-120 seconds
- **Large repositories** (100-500MB): ~2-5 minutes
- **Evaluation only**: ~0.1-1 seconds (very fast)

## Troubleshooting

### Common Issues

**"Repository too large"**
```bash
# Increase timeout
./scripts/run_metrics.sh <url> --timeout 600
```

**"Checklist evaluation failed"**
```bash
# Check submission.json format
cat output/submission.json | jq '.'

# Run evaluation with verbose output
uv run python -m src.cli.evaluate output/submission.json --verbose
```

**"Missing required sections"**
```bash
# The submission.json must have repository, metrics, and execution sections
# Re-run metrics collection to generate proper format
```

### Debug Mode
```bash
# Enable detailed logging for the entire pipeline
./scripts/run_metrics.sh <url> --verbose

# Debug just the evaluation step
uv run python -m src.cli.evaluate submission.json --verbose

# Check individual components
uv run python -c "
from src.metrics.checklist_loader import ChecklistLoader
loader = ChecklistLoader()
validation = loader.validate_checklist_config()
print(f'Checklist valid: {validation[\"valid\"]}')
if not validation['valid']:
    print(f'Errors: {validation[\"errors\"]}')
"
```

## Next Steps

1. **Try the examples above** with different repositories
2. **Examine the generated evidence files** to understand the evaluation logic
3. **Customize the checklist configuration** for your specific needs
4. **Integrate with your CI/CD pipeline** for automated quality assessment
5. **Use the structured JSON output** for downstream LLM processing

## API Usage

For programmatic use:

```python
from src.metrics.checklist_evaluator import ChecklistEvaluator
from src.metrics.scoring_mapper import ScoringMapper

# Initialize evaluator
evaluator = ChecklistEvaluator()

# Load and evaluate submission
with open('output/submission.json') as f:
    submission_data = json.load(f)

evaluation_result = evaluator.evaluate_from_dict(submission_data, 'output/submission.json')

# Generate structured output
mapper = ScoringMapper('results/')
score_input = mapper.map_to_score_input(evaluation_result, repository_info, 'submission.json')

print(f"Score: {evaluation_result.total_score}/{evaluation_result.max_possible_score}")
```

Ready to start evaluating code quality! 🚀