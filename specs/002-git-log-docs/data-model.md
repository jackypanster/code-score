# Data Model: Checklist Mapping & Scoring Input

## Overview
Data models for the checklist evaluation system that transforms repository metrics into structured scoring input for LLM processing.

## Core Entities

### ChecklistItem
Represents one of the 11 evaluation criteria from ai-code-review-judgement.md.

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

**State Transitions**:
- Initial state: unmet (0 points)
- Evaluation process updates status and score based on metrics
- Evidence references accumulated during evaluation

### EvaluationResult
Container for complete checklist evaluation results.

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

### ScoreInput
Structured output format for downstream LLM processing.

**Fields**:
- `schema_version`: str - Format version (e.g., "1.0.0")
- `repository_info`: RepositoryInfo - Source repository details
- `evaluation_result`: EvaluationResult - Complete evaluation data
- `generation_timestamp`: datetime - When evaluation was performed
- `evidence_paths`: Dict[str, str] - File paths to supporting evidence
- `human_summary`: str - Markdown summary for manual review

**Validation Rules**:
- `schema_version` must follow semantic versioning
- `generation_timestamp` must be valid ISO 8601 format
- All evidence paths must be valid file references

### RepositoryInfo
Repository context for the evaluation.

**Fields**:
- `url`: str - Repository URL
- `commit_sha`: str - Specific commit evaluated
- `primary_language`: str - Detected programming language
- `analysis_timestamp`: datetime - When metrics were collected
- `metrics_source`: str - Path to submission.json file

### EvidenceReference
Specific citation linking evaluation to source data.

**Fields**:
- `source_type`: str - Type of evidence (lint_output, test_result, file_check)
- `source_path`: str - JSON path or file reference
- `description`: str - Human-readable explanation
- `confidence`: float - Confidence level (0.0 to 1.0)
- `raw_data`: Optional[str] - Excerpt of supporting data

**Validation Rules**:
- `confidence` must be between 0.0 and 1.0
- `source_type` must be from predefined enum

### CategoryBreakdown
Score breakdown by evaluation dimension.

**Fields**:
- `dimension`: str - Category name
- `items_count`: int - Number of items in category
- `max_points`: int - Maximum possible points
- `actual_points`: float - Achieved points
- `percentage`: float - Category percentage score

### EvaluationMetadata
Execution details for the evaluation process.

**Fields**:
- `evaluator_version`: str - Version of evaluation logic
- `processing_duration`: float - Seconds taken for evaluation
- `warnings`: List[str] - Non-fatal issues encountered
- `metrics_completeness`: float - Percentage of required metrics available

## Relationships

### Entity Relationships
- EvaluationResult contains multiple ChecklistItems (1:11)
- ChecklistItem contains multiple EvidenceReferences (1:many)
- ScoreInput contains one EvaluationResult (1:1)
- EvaluationResult contains CategoryBreakdowns by dimension (1:3)

### Data Flow
1. submission.json → MetricsMapping → ChecklistItems
2. ChecklistItems → EvaluationResult → ScoreInput
3. EvidenceReferences accumulated throughout evaluation process
4. Human summary generated from EvaluationResult for report.md

## Scoring Logic

### Status to Score Mapping
- **met**: 100% of max_points
- **partial**: 50% of max_points
- **unmet**: 0% of max_points

### Special Cases
- Missing metrics: "unmet" status with evidence explaining absence
- Tool failures: "partial" status if some data available
- Language-specific variations: adapted evaluation criteria with documentation

### Evidence Requirements
- Each status assignment must have supporting evidence
- Evidence must reference specific data points in submission.json
- Human-readable descriptions required for manual verification

## Validation Schema

### Input Validation
- submission.json structure validation against existing schema
- Required fields presence checking
- Data type validation for all metrics

### Output Validation
- score_input.json schema validation
- Mathematical consistency checking (totals, percentages)
- Evidence reference completeness validation

### Error Handling
- Malformed JSON: Immediate failure with specific error
- Missing required sections: Graceful degradation with "unmet" marking
- Invalid data types: Fail-fast with type error details