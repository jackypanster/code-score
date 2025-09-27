# Code Score API Reference

## Overview

This document describes the API interfaces and core components of the Code Score system, including both metrics collection and checklist evaluation functionality.

## Core Components

### 1. ChecklistEvaluator

The main evaluation engine that processes submission data against the 11-item quality checklist.

```python
from src.metrics.checklist_evaluator import ChecklistEvaluator

# Initialize evaluator with default configuration
evaluator = ChecklistEvaluator()

# Initialize with custom configuration
evaluator = ChecklistEvaluator("path/to/custom_checklist.yaml")

# Evaluate from submission file
result = evaluator.evaluate_from_file("submission.json")

# Evaluate from dictionary
result = evaluator.evaluate_from_dict(submission_data, "submission.json")
```

#### Key Methods

- `evaluate_from_file(submission_path: str) -> EvaluationResult`
  - Loads and evaluates a submission.json file
  - Returns complete evaluation results with scoring and evidence

- `evaluate_from_dict(submission_data: Dict, submission_path: str) -> EvaluationResult`
  - Evaluates submission data from a Python dictionary
  - Useful for programmatic processing

#### Return Type: EvaluationResult

```python
class EvaluationResult:
    checklist_items: List[ChecklistItem]        # Individual item evaluations
    total_score: float                          # Total points earned
    max_possible_score: int                     # Maximum possible points (100)
    score_percentage: float                     # Score as percentage
    category_breakdowns: Dict[str, CategoryBreakdown]  # Scores by dimension
    evaluation_metadata: EvaluationMetadata    # Processing information
    evidence_summary: List[str]                # Human-readable evidence list
```

### 2. ScoringMapper

Transforms evaluation results into structured output formats for LLM processing.

```python
from src.metrics.scoring_mapper import ScoringMapper
from src.metrics.models.evaluation_result import RepositoryInfo

mapper = ScoringMapper(output_base_path="./output")

# Create repository information
repository_info = RepositoryInfo(
    url="https://github.com/user/repo.git",
    commit_sha="abc123",
    primary_language="python",
    analysis_timestamp=datetime.now(),
    metrics_source="submission.json"
)

# Map evaluation to score input format
score_input = mapper.map_to_score_input(
    evaluation_result=result,
    repository_info=repository_info,
    submission_path="submission.json"
)

# Generate JSON output
json_path = mapper.generate_score_input_json(score_input, "score_input.json")

# Generate markdown report
md_path = mapper.generate_markdown_report(score_input, "report.md")
```

#### Key Methods

- `map_to_score_input() -> ScoreInput`: Converts evaluation to structured format
- `generate_score_input_json()`: Saves JSON output file
- `generate_markdown_report()`: Saves human-readable report

### 3. EvidenceTracker

Manages evidence collection and organization for evaluation transparency.

```python
from src.metrics.evidence_tracker import EvidenceTracker
from src.metrics.models.evidence_reference import EvidenceReference

tracker = EvidenceTracker(evidence_base_path="./evidence")

# Track evidence for evaluation
tracker.track_evaluation_evidence(evaluation_result)

# Save evidence files to disk
evidence_files = tracker.save_evidence_files()  # Returns Dict[str, str]
file_paths = list(evidence_files.values())     # Get actual file paths

# Generate evidence report
report_path = tracker.export_evidence_report("evidence_report.md")
```

#### Evidence Structure

Evidence files are organized by dimension:
```
evidence/
├── code_quality/           # Code quality evidence
├── testing/               # Testing evidence
├── documentation/         # Documentation evidence
├── system/               # System metadata
├── evidence_summary.json # Overall summary
└── manifest.json         # File manifest
```

### 4. ChecklistLoader

Manages checklist configuration and language adaptations.

```python
from src.metrics.checklist_loader import ChecklistLoader

# Load default configuration
loader = ChecklistLoader()

# Load custom configuration
loader = ChecklistLoader("path/to/custom_checklist.yaml")

# Validate configuration
validation = loader.validate_checklist_config()
if validation["valid"]:
    print("Configuration is valid")
else:
    print(f"Errors: {validation['errors']}")

# Get language-specific adaptations
python_adaptations = loader.get_language_adaptations("python")

# Export documentation
doc_path = loader.export_checklist_documentation("checklist_docs.md")
```

## CLI Integration

### Main Analysis CLI

```python
from src.cli.main import main

# Programmatic usage
main.callback(
    repository_url="https://github.com/user/repo.git",
    commit_sha=None,
    output_dir="./results",
    output_format="both",
    timeout=300,
    verbose=True,
    enable_checklist=True,
    checklist_config=None
)
```

### Evaluation CLI

```python
from src.cli.evaluate import evaluate

# Direct evaluation
evaluate.callback(
    submission_file=Path("submission.json"),
    output_dir=Path("results"),
    format="both",
    checklist_config=None,
    evidence_dir=Path("evidence"),
    validate_only=False,
    quiet=False,
    verbose=True
)
```

## Data Models

### ChecklistItem

```python
from src.metrics.models.checklist_item import ChecklistItem

item = ChecklistItem(
    id="code_quality_lint",
    name="Static Linting Passed",
    dimension="code_quality",
    max_points=15,
    description="Lint/static analysis pipeline passes successfully",
    evaluation_status="met",  # "met", "partial", "unmet"
    score=15.0,
    evidence_references=[]
)
```

### EvidenceReference

```python
from src.metrics.models.evidence_reference import EvidenceReference

evidence = EvidenceReference(
    source_type="file_check",
    source_path="$.metrics.code_quality.lint_results.passed",
    description="Checked lint_results.passed: expected True, got True",
    confidence=0.95,
    raw_data="True"
)
```

### ScoreInput

```python
from src.metrics.models.score_input import ScoreInput

score_input = ScoreInput(
    schema_version="1.0.0",
    repository_info=repository_info,
    evaluation_result=evaluation_result,
    generation_timestamp=datetime.now(),
    evidence_paths=evidence_paths,
    human_summary=summary_text
)
```

## Error Handling

### Exception Types

```python
from src.metrics.submission_pipeline import SubmissionValidationError

try:
    result = evaluator.evaluate_from_file("submission.json")
except SubmissionValidationError as e:
    print(f"Validation failed: {e}")
except FileNotFoundError:
    print("Submission file not found")
except Exception as e:
    print(f"Evaluation failed: {e}")
```

### Validation Methods

```python
# Validate checklist configuration
validation = loader.validate_checklist_config()

# Validate evidence integrity
evidence_validation = tracker.validate_evidence_integrity()

# Check if evaluation should run
from src.metrics.submission_pipeline import PipelineIntegrator
integrator = PipelineIntegrator()
should_run = integrator.should_run_checklist_evaluation(submission_data)
```

## Pipeline Integration

### PipelineOutputManager

```python
from src.metrics.pipeline_output_manager import PipelineOutputManager

manager = PipelineOutputManager(
    output_dir="./results",
    checklist_config_path="checklist.yaml",
    enable_checklist_evaluation=True
)

# Process submission with checklist
generated_files = manager.process_submission_with_checklist(
    submission_path="submission.json",
    output_format="both"  # "json", "markdown", "both"
)

# Integrate with existing pipeline
all_files = manager.integrate_with_existing_pipeline(
    existing_output_files=["submission.json", "report.md"],
    submission_path="submission.json"
)
```

## Configuration

### Checklist Mapping YAML

```yaml
checklist_items:
  - id: code_quality_lint
    name: "Static Linting Passed"
    dimension: code_quality
    max_points: 15
    description: "Lint/static analysis pipeline passes successfully"
    evaluation_criteria:
      met:
        - "lint_results.passed == true"
        - "lint_results.tool_used is not null"
        - "lint_results.issues_count == 0"
      partial:
        - "lint_results.passed == false"
        - "lint_results.issues_count <= 10"
      unmet:
        - "lint_results.tool_used is null"
    metrics_mapping:
      source_path: "$.metrics.code_quality.lint_results"
      required_fields: ["passed", "tool_used", "issues_count"]

language_adaptations:
  python:
    code_quality_lint:
      preferred_tools: ["ruff", "flake8"]
      confidence_boost: 0.1
  javascript:
    code_quality_lint:
      preferred_tools: ["eslint"]
      confidence_boost: 0.1
```

## Performance Considerations

- **Evaluation speed**: <0.1 seconds for typical submissions
- **Memory usage**: Minimal, processes JSON structures in memory
- **File generation**: Evidence files are written individually for efficiency
- **Concurrent processing**: Thread-safe for parallel evaluations

## Examples

### Complete Evaluation Workflow

```python
import json
from pathlib import Path
from src.metrics.checklist_evaluator import ChecklistEvaluator
from src.metrics.scoring_mapper import ScoringMapper
from src.metrics.evidence_tracker import EvidenceTracker
from src.metrics.models.evaluation_result import RepositoryInfo

# 1. Load submission data
with open("submission.json", "r") as f:
    submission_data = json.load(f)

# 2. Run evaluation
evaluator = ChecklistEvaluator()
evaluation_result = evaluator.evaluate_from_dict(submission_data, "submission.json")

# 3. Track evidence
evidence_tracker = EvidenceTracker("./evidence")
evidence_tracker.track_evaluation_evidence(evaluation_result)
evidence_files = evidence_tracker.save_evidence_files()

# 4. Generate structured output
repository_info = RepositoryInfo(
    url=submission_data["repository"]["url"],
    commit_sha=submission_data["repository"]["commit"],
    primary_language=submission_data["repository"]["language"],
    analysis_timestamp=datetime.now(),
    metrics_source="submission.json"
)

mapper = ScoringMapper("./output")
score_input = mapper.map_to_score_input(
    evaluation_result, repository_info, "submission.json"
)

# 5. Save outputs
mapper.generate_score_input_json(score_input, "score_input.json")
mapper.generate_markdown_report(score_input, "evaluation_report.md")

print(f"Score: {evaluation_result.total_score}/{evaluation_result.max_possible_score}")
print(f"Generated {len(evidence_files)} evidence files")
```

### Custom Evaluation Logic

```python
# Custom evaluation with specific criteria
evaluator = ChecklistEvaluator("custom_checklist.yaml")

# Override specific item evaluation
def custom_lint_evaluation(item, submission_data):
    lint_data = submission_data.get("metrics", {}).get("code_quality", {}).get("lint_results", {})
    if lint_data.get("passed") and lint_data.get("issues_count", 0) == 0:
        return "met", 15.0
    elif lint_data.get("tool_used"):
        return "partial", 7.5
    else:
        return "unmet", 0.0

# Use custom evaluation logic
result = evaluator.evaluate_from_dict(submission_data, "submission.json")
```

This API provides flexible, programmatic access to all checklist evaluation functionality with comprehensive error handling and evidence tracking.