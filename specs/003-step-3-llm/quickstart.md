# Quickstart: LLM-Generated Code Review Reports

**Phase 1 Output** | **Date**: 2025-09-27

## Overview

This guide demonstrates how to use the LLM report generation feature to create human-readable evaluation reports from code quality analysis data.

## Prerequisites

1. **Existing Code Score Installation**
   ```bash
   # Ensure code-score is installed and working
   uv run python -m src.cli.main --help
   ```

2. **Gemini CLI Installation** (for default provider)
   ```bash
   # Install Gemini CLI (user responsibility)
   # Follow instructions at: https://ai.google.dev/gemini-api/docs/quickstart

   # Verify installation
   gemini --version
   ```

3. **Test Data Preparation**
   ```bash
   # Run analysis to generate test data
   ./scripts/run_metrics.sh https://github.com/pallets/click.git --enable-checklist

   # Verify score_input.json exists
   ls -la output/score_input.json
   ```

## Basic Usage

### Step 1: Generate Your First Report

```bash
# Generate report using default template
uv run python -m src.cli.llm_report output/score_input.json

# Expected output:
# ✅ Template loaded: specs/prompts/llm_report.md
# ✅ Score data validated: 67.5/100 (67.5%)
# ✅ Prompt generated: 2,847 characters
# 🤖 Calling Gemini CLI...
# ✅ Report generated: output/final_report.md
```

**Expected Result**: A file `output/final_report.md` containing:
- Project overview and score summary
- Key strengths and improvement areas
- Evidence-based recommendations
- Structured evaluation breakdown

### Step 2: Preview Before Generation

```bash
# Generate LLM report directly
uv run python -m src.cli.llm_report output/score_input.json

# Expected output:
# ✅ Template loaded: specs/prompts/llm_report.md
# ✅ Score data validated: 67.5/100 (67.5%)
# 🚀 Generating report using gemini
# You are an expert code reviewer. Please analyze the following...
# [Full prompt content displayed]
# === END PREVIEW ===
```

### Step 3: Custom Template

```bash
# Use custom template for specific evaluation context
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt ./custom_hackathon_template.md \
  --output ./hackathon_evaluation.md

# Expected output:
# ✅ Template loaded: ./custom_hackathon_template.md
# ✅ Score data validated: 67.5/100 (67.5%)
# ✅ Report generated: ./hackathon_evaluation.md
```

## Integrated Workflow

### Full Analysis with Report Generation

```bash
# Run complete pipeline with automatic report generation
./scripts/run_metrics.sh https://github.com/user/repository.git --generate-llm-report

# Expected workflow:
# 1. Repository analysis (metrics collection)
# 2. Checklist evaluation (scoring)
# 3. LLM report generation (final report)
#
# Files generated:
# - output/submission.json (raw metrics)
# - output/score_input.json (evaluation data)
# - output/evaluation_report.md (structured report)
# - output/final_report.md (LLM-generated report)
```

## Test Scenarios

### Scenario 1: Successful Generation

**Given**: Valid score_input.json with complete evaluation data
**When**: Running `llm-report` command with default settings
**Then**:
- Report generated in <30 seconds
- Contains project metadata, score breakdown, and recommendations
- File size between 5-20KB
- Valid markdown format

**Validation Steps**:
```bash
# Check file was created
test -f output/final_report.md

# Validate markdown structure
head -20 output/final_report.md | grep "^# "

# Check content includes required sections
grep -q "Score Overview" output/final_report.md
grep -q "Highlights" output/final_report.md
grep -q "Improvement Opportunities" output/final_report.md
```

### Scenario 2: Custom Template

**Given**: Custom template file with specific format
**When**: Running with `--prompt` parameter
**Then**:
- Custom template used instead of default
- Template-specific sections included
- Generated content matches template structure

**Validation Steps**:
```bash
# Create minimal custom template
cat > test_template.md << 'EOF'
# Test Report for {{repository.url}}

Score: {{total.score}}/100

## Met Criteria
{{#each met_items}}
- {{name}}: {{description}}
{{/each}}
EOF

# Generate report with custom template
uv run python -m src.cli.llm_report output/score_input.json --prompt test_template.md

# Validate custom content
grep -q "Test Report for" output/final_report.md
grep -q "Met Criteria" output/final_report.md
```

### Scenario 4: Error Handling

**Given**: Missing or invalid input file
**When**: Running `llm-report` command
**Then**:
- Clear error message displayed
- Exit code non-zero
- No partial files created

**Validation Steps**:
```bash
# Test missing file
! uv run python -m src.cli.llm_report nonexistent.json 2>&1 | \
  grep -q "File not found: nonexistent.json"

# Test invalid JSON
echo "invalid json" > invalid.json
! uv run python -m src.cli.llm_report invalid.json 2>&1 | \
  grep -q "validation failed"
```

## Common Use Cases

### 1. Hackathon Judging
```bash
# Process multiple repositories for evaluation
for repo in $(cat hackathon_repos.txt); do
  ./scripts/run_metrics.sh "$repo" --generate-llm-report --output-dir "results/$(basename $repo)"
done

# Batch results in results/ directory for comparison
```

### 2. Code Review Preparation
```bash
# Generate detailed report for PR review
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt templates/code_review.md \
  --output pr_review_summary.md

# Share pr_review_summary.md with team
```

### 3. Continuous Integration
```bash
# Add to CI pipeline
if ./scripts/run_metrics.sh "$CI_REPOSITORY_URL" --generate-llm-report; then
  # Upload final_report.md as CI artifact
  cp output/final_report.md "$CI_ARTIFACTS_DIR/"
fi
```

## Troubleshooting

### Common Issues

**Issue**: "Gemini CLI not found"
**Solution**: Install Gemini CLI and ensure it's in PATH
```bash
which gemini  # Should return path
gemini --version  # Should show version
```

**Issue**: "Template processing failed"
**Solution**: Validate template syntax
```bash
# Check template for valid Jinja2 syntax
python -c "
from jinja2 import Template
Template(open('template.md').read())
print('Template syntax valid')
"
```

**Issue**: "Context too long for LLM"
**Solution**: Adjust content limits in template configuration
```bash
# Reduce evidence items in prompt
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt templates/short_template.md
```

### Performance Optimization

**Slow LLM responses**: Increase timeout or use lighter model
```bash
# Set longer timeout (environment variable)
export LLM_TIMEOUT_SECONDS=60
uv run python -m src.cli.llm_report output/score_input.json
```

**Large evaluation data**: Use summary template
```bash
# Use template designed for large datasets
uv run python -m src.cli.llm_report output/score_input.json \
  --prompt templates/summary_only.md
```

## Next Steps

1. **Explore Templates**: Check `specs/prompts/` for additional templates
2. **Customize Providers**: Configure different LLM providers in settings
3. **Batch Processing**: Set up scripts for multiple repository evaluation
4. **Integration**: Add to existing code review workflows

---

**Quickstart Complete**: All basic workflows validated and documented
**Next**: Update agent context and finalize implementation plan