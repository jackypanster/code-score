# Quickstart: Checklist Evaluation System

## Overview
This quickstart guide demonstrates the checklist evaluation system that converts repository metrics into structured scoring input for automated hackathon evaluation.

## Prerequisites
- Python 3.11+ with UV package manager
- Existing submission.json file from Phase 1 metrics collection
- Git repository access for testing

## Installation
```bash
# Install dependencies (UV required)
uv sync

# Verify installation
uv run python -m src.cli.main --version
```

## Basic Usage

### 1. Evaluate Existing Metrics
```bash
# Evaluate submission.json and generate score_input.json
uv run python -m src.cli.evaluate \
  --input output/submission.json \
  --output output/score_input.json \
  --verbose

# Expected output:
# Checklist Evaluation Complete
# Total Score: 67.5/100 (67.5%)
# - Code Quality: 25/40 (62.5%)
# - Testing: 21/35 (60.0%)
# - Documentation: 21.5/25 (86.0%)
# Output: output/score_input.json
```

### 2. Generate Human-Readable Report
```bash
# Append evaluation summary to report
uv run python -m src.cli.evaluate \
  --input output/submission.json \
  --output output/score_input.json \
  --report output/report.md \
  --verbose

# Check the updated report
tail -n 50 output/report.md
```

### 3. Validate Output Format
```bash
# Validate generated score_input.json against schema
uv run python -c "
import json
import jsonschema
from pathlib import Path

# Load schema and data
schema = json.loads(Path('specs/002-git-log-docs/contracts/score_input_schema.json').read_text())
data = json.loads(Path('output/score_input.json').read_text())

# Validate
jsonschema.validate(data, schema)
print('✅ score_input.json validates against schema')
"
```

## Testing the System

### 1. Run Contract Tests
```bash
# Test output schema validation
uv run pytest tests/contract/test_score_input_schema.py -v

# Expected output:
# test_score_input_schema_valid ✓
# test_required_fields_present ✓
# test_score_calculations_correct ✓
```

### 2. Run Integration Tests
```bash
# Test full evaluation workflow
uv run pytest tests/integration/test_checklist_evaluation.py -v

# Expected output:
# test_evaluation_with_complete_metrics ✓
# test_evaluation_with_partial_metrics ✓
# test_evaluation_with_missing_metrics ✓
# test_multi_language_evaluation ✓
```

### 3. Run Unit Tests
```bash
# Test individual components
uv run pytest tests/unit/ -v

# Expected output:
# test_checklist_evaluator.py ✓✓✓
# test_scoring_mapper.py ✓✓✓
# test_evidence_tracker.py ✓✓✓
```

## Example Outputs

### Sample score_input.json Structure
```json
{
  "schema_version": "1.0.0",
  "repository_info": {
    "url": "https://github.com/example/repo.git",
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
        "description": "Lint/static analysis pipeline passes successfully",
        "evaluation_status": "met",
        "score": 15.0,
        "evidence_references": [
          {
            "source_type": "lint_output",
            "source_path": "$.metrics.code_quality.lint_results",
            "description": "Ruff linting passed with 0 issues",
            "confidence": 1.0,
            "raw_data": "passed: true, issues_count: 0, tool_used: ruff"
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
        "actual_points": 25.0,
        "percentage": 62.5
      }
    },
    "evaluation_metadata": {
      "evaluator_version": "1.0.0",
      "processing_duration": 0.125,
      "warnings": [],
      "metrics_completeness": 0.9
    },
    "evidence_summary": [
      "✅ Static linting passed (ruff)",
      "⚠️ Build status unknown",
      "✅ No high-severity security issues",
      "✅ Comprehensive README present"
    ]
  },
  "generation_timestamp": "2025-09-27T11:00:00Z",
  "evidence_paths": {
    "submission_json": "output/submission.json",
    "checklist_mapping": "specs/002-git-log-docs/contracts/checklist_mapping.yaml"
  },
  "human_summary": "## Checklist Evaluation Summary\n\n**Total Score: 67.5/100 (67.5%)**\n\n### Code Quality (25/40 - 62.5%)\n- ✅ Static Linting: 15/15 points\n- ⚠️ Build Success: 5/10 points\n- ✅ Security Scan: 8/8 points\n- ⚠️ Module Docs: 3.5/7 points\n\n### Testing (21/35 - 60.0%)\n- ✅ Automated Tests: 15/15 points\n- ⚠️ Coverage: 5/10 points\n- ⚠️ Integration Tests: 3/6 points\n- ⚠️ Result Docs: 2/4 points\n\n### Documentation (21.5/25 - 86.0%)\n- ✅ README Guide: 12/12 points\n- ✅ Config Setup: 7/7 points\n- ⚠️ API Docs: 3/6 points\n\n### Key Strengths\n- Excellent linting and code quality\n- Strong automated test coverage\n- Comprehensive README documentation\n\n### Improvement Areas\n- Add build/CI success verification\n- Enhance integration test coverage\n- Document API endpoints and usage"
}
```

### Sample Report Appendix
```markdown
## Checklist Evaluation Results

**Generated**: 2025-09-27 11:00:00 UTC
**Total Score**: 67.5/100 (67.5%)

### Score Breakdown
| Dimension | Score | Max | Percentage |
|-----------|-------|-----|------------|
| Code Quality | 25.0 | 40 | 62.5% |
| Testing | 21.0 | 35 | 60.0% |
| Documentation | 21.5 | 25 | 86.0% |

### Individual Items
1. **Static Linting Passed** (15/15) ✅ - Ruff linting passed with 0 issues
2. **Build/Package Success** (5/10) ⚠️ - Build status not available in metrics
3. **Dependency Security Scan** (8/8) ✅ - No high-severity vulnerabilities found
4. **Core Module Documentation** (3.5/7) ⚠️ - README present but limited module descriptions

[... continues for all 11 items ...]

### Evidence Summary
- ✅ 6 items fully met (met status)
- ⚠️ 4 items partially met (partial status)
- ❌ 1 item unmet (unmet status)

### Recommendations
1. Add CI/build verification step
2. Increase test coverage above 60%
3. Document API endpoints with examples
4. Add integration test scenarios

---
*Evaluation performed by code-score v1.0.0*
```

## Validation Scenarios

### Test with Known Repositories
```bash
# Test with code-walker repository
./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git
uv run python -m src.cli.evaluate --input output/submission.json --output output/score_input.json

# Test with multi-language repository
./scripts/run_metrics.sh https://github.com/example/javascript-project.git
uv run python -m src.cli.evaluate --input output/submission.json --output output/score_input.json

# Verify different scoring outcomes
cat output/score_input.json | jq '.evaluation_result.total_score'
```

### Edge Case Testing
```bash
# Test with incomplete metrics
echo '{"metrics": {"code_quality": {}}}' > test_incomplete.json
uv run python -m src.cli.evaluate --input test_incomplete.json --output test_output.json
# Should gracefully handle missing data

# Test with malformed JSON
echo '{"invalid": json}' > test_malformed.json
uv run python -m src.cli.evaluate --input test_malformed.json --output test_output.json
# Should fail fast with clear error message
```

## Next Steps
1. Review generated score_input.json for accuracy
2. Validate evidence references match source data
3. Customize evaluation criteria if needed
4. Integrate with Phase 3 LLM evaluation system

## Troubleshooting

### Common Issues
- **"File not found"**: Ensure submission.json exists from Phase 1
- **"Schema validation failed"**: Check JSON format and required fields
- **"Tool not available"**: Verify UV installation and dependencies

### Debug Mode
```bash
# Enable detailed logging
uv run python -m src.cli.evaluate \
  --input output/submission.json \
  --output output/score_input.json \
  --debug \
  --verbose

# Check evaluation logic step-by-step
python -c "
from src.metrics.checklist_evaluator import ChecklistEvaluator
evaluator = ChecklistEvaluator(debug=True)
result = evaluator.evaluate_from_file('output/submission.json')
print(f'Debug info: {evaluator.debug_log}')
"
```