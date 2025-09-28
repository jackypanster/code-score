# Code Score Data Models

## Overview

This document describes the core data models used throughout the Code Score system for metrics collection, checklist evaluation, and LLM report generation.

## Core Evaluation Models

### ChecklistItem

Represents one of the 11 evaluation criteria for code quality assessment.

**Location**: `src/metrics/models/checklist_item.py`

**Fields**:
- `id`: str - Unique identifier (e.g., "code_quality_lint", "testing_coverage")
- `name`: str - Human-readable name (e.g., "Static Linting Passed")
- `dimension`: str - Category (code_quality, testing, documentation)
- `max_points`: int - Maximum possible points (15, 10, 8, 7, 6, 4)
- `description`: str - Evaluation criteria description
- `evaluation_status`: str - Current status (met, partial, unmet)
- `score`: float - Calculated score (0.0 to max_points)
- `evidence_references`: List[EvidenceReference] - Supporting evidence

**Validation Rules**:
- `evaluation_status` must be one of: ["met", "partial", "unmet"]
- `score` must be between 0.0 and `max_points`
- `dimension` must be one of: ["code_quality", "testing", "documentation"]

### EvaluationResult

Container for complete checklist evaluation results.

**Location**: `src/metrics/models/evaluation_result.py`

**Fields**:
- `checklist_items`: List[ChecklistItem] - All 11 evaluated items
- `total_score`: float - Sum of all item scores
- `max_possible_score`: int - Maximum possible total (100 points)
- `score_percentage`: float - Percentage score (0.0 to 100.0)
- `category_breakdowns`: Dict[str, CategoryBreakdown] - Score by dimension
- `evaluation_metadata`: EvaluationMetadata - Execution details
- `evidence_summary`: List[str] - Key evidence points for human review

**Validation Rules**:
- Must contain exactly 11 checklist items
- `total_score` must equal sum of individual item scores
- `score_percentage` must equal (total_score / max_possible_score) * 100

### CategoryBreakdown

Score breakdown by evaluation dimension.

**Location**: `src/metrics/models/category_breakdown.py`

**Fields**:
- `category`: str - Dimension name (code_quality, testing, documentation)
- `score`: float - Achieved points in this category
- `max_points`: int - Maximum possible points
- `percentage`: float - Percentage score for this category
- `grade_letter`: str - Letter grade (A, B, C, D, F)
- `status`: str - Overall status (excellent, good, fair, poor, failing)

### ScoreInput

Structured output format for LLM processing and external consumption.

**Location**: `src/metrics/models/score_input.py`

**Fields**:
- `repository_info`: RepositoryInfo - Repository metadata
- `evaluation_result`: EvaluationResult - Complete checklist evaluation
- `evidence_paths`: List[str] - Paths to detailed evidence files
- `human_summary`: str - Markdown-formatted evaluation summary

**Purpose**: Primary interface between evaluation pipeline and LLM report generation.

## LLM Report Generation Models

### ReportTemplate

Configuration for LLM report templates.

**Location**: `src/llm/models/report_template.py`

**Fields**:
- `name`: str - Template identifier
- `file_path`: str - Path to Jinja2 template file
- `description`: str - Template purpose description
- `required_fields`: List[str] - Required template variables
- `content_limits`: Dict[str, int] - Content truncation settings
- `template_type`: str - Template category (general, hackathon, code_review)
- `target_providers`: List[str] - LLM providers (currently ["gemini"])

### LLMProviderConfig

Configuration for external LLM providers.

**Location**: `src/llm/models/llm_provider_config.py`

**Fields**:
- `provider_name`: str - Provider identifier ("gemini")
- `cli_command`: List[str] - Base CLI command and arguments
- `model_name`: str - Specific model identifier
- `timeout_seconds`: int - API call timeout (10-300)
- `max_tokens`: int - Maximum response length
- `temperature`: float - Generation randomness (0.0-1.0)
- `environment_variables`: Dict[str, str] - Required environment variables

### GeneratedReport

Final report output with metadata.

**Location**: `src/llm/models/generated_report.py`

**Fields**:
- `content`: str - Generated report content (Markdown)
- `template_used`: TemplateMetadata - Template information
- `provider_used`: ProviderMetadata - LLM provider details
- `input_metadata`: InputMetadata - Input data statistics
- `generation_metadata`: Dict[str, Any] - Generation process details
- `validation_results`: List[str] - Content validation issues
- `warnings`: List[str] - Generation warnings

### TemplateContext

Data structure for template rendering with content management.

**Location**: `src/llm/models/template_context.py`

**Fields**:
- `repository`: RepositoryInfo - Repository metadata
- `total`: TotalScore - Overall evaluation summary
- `met_items`: List[ChecklistItem] - Successfully met criteria
- `partial_items`: List[ChecklistItem] - Partially met criteria
- `unmet_items`: List[ChecklistItem] - Unmet criteria
- `category_scores`: Dict[str, CategoryBreakdown] - Scores by dimension
- `evidence_summary`: List[EvidenceContext] - Organized evidence
- `generation_metadata`: Dict[str, Any] - Template processing metadata
- `warnings`: List[str] - Content truncation warnings

## Metrics Collection Models

### MetricsCollection

Top-level container for all repository analysis results.

**Location**: `src/metrics/models/metrics_collection.py`

**Fields**:
- `repository`: RepositoryInfo - Repository metadata
- `metrics`: AllMetrics - Complete metrics data
- `execution`: ExecutionMetadata - Analysis execution details

### CodeQualityMetrics

Static analysis and linting results.

**Location**: `src/metrics/models/code_quality_metrics.py`

**Fields**:
- `lint_results`: LintResults - Linting tool outputs
- `build_status`: BuildStatus - Build/compile status
- `dependency_audit`: SecurityAudit - Dependency security scan
- `documentation_check`: DocumentationMetrics - Code documentation analysis

### TestingMetrics

Test execution and coverage analysis.

**Location**: `src/metrics/models/testing_metrics.py`

**Fields**:
- `test_execution`: TestExecution - Test runner results
- `coverage_report`: CoverageReport - Test coverage analysis
- `test_discovery`: TestDiscovery - Available test files

## Supporting Models

### RepositoryInfo

Repository metadata and analysis context.

**Fields**:
- `url`: str - Repository URL
- `commit_sha`: str - Analyzed commit hash
- `primary_language`: str - Detected main programming language
- `size_mb`: float - Repository size in megabytes
- `file_count`: int - Total number of files

### EvidenceReference

Reference to supporting evidence for evaluation decisions.

**Fields**:
- `source`: str - Evidence source (file, command, tool)
- `description`: str - Human-readable evidence description
- `confidence`: float - Confidence level (0.0-1.0)
- `details`: Dict[str, Any] - Additional evidence details

### ExecutionMetadata

Analysis execution tracking and performance data.

**Fields**:
- `start_time`: datetime - Analysis start timestamp
- `end_time`: datetime - Analysis completion timestamp
- `duration_seconds`: float - Total execution time
- `tools_executed`: List[str] - Analysis tools run
- `warnings`: List[str] - Execution warnings
- `errors`: List[str] - Non-fatal errors encountered

## Data Flow

```
Repository URL → GitOperations → LanguageDetection → ToolExecutor
                                                          ↓
Raw Metrics → MetricsCollection → ChecklistEvaluator → EvaluationResult
                                                          ↓
EvaluationResult → ScoringMapper → ScoreInput → LLM Pipeline → GeneratedReport
```

## Validation and Constraints

### Schema Validation
- All models include Pydantic validation
- JSON Schema contracts available in `specs/contracts/`
- Automatic validation during pipeline execution

### Business Rules
- Total checklist score must equal sum of individual items
- Evidence references must have valid confidence levels
- Repository size must not exceed 500MB for analysis
- Timeout values must be between 10-300 seconds

### Data Quality
- Missing evidence results in reduced confidence scores
- Tool execution failures are logged but don't fail analysis
- All timestamps are UTC for consistency
- File paths are normalized to avoid platform issues

## Usage Examples

### Accessing Evaluation Data
```python
# Load evaluation results
score_input = ScoreInput.from_file("output/score_input.json")

# Access specific metrics
total_score = score_input.evaluation_result.total_score
code_quality_score = score_input.evaluation_result.category_breakdowns["code_quality"].score

# Get evidence for specific item
lint_item = next(item for item in score_input.evaluation_result.checklist_items
                if item.id == "code_quality_lint")
evidence = lint_item.evidence_references
```

### Creating Custom Reports
```python
# Create template context from evaluation data
context = TemplateContext.from_score_input(score_input_data)

# Apply content limits for specific providers
context.apply_content_limits({"max_evidence_items": 3})

# Convert to template variables
template_vars = context.to_jinja_dict()
```

This data model documentation provides the foundation for understanding, extending, and maintaining the Code Score system architecture.