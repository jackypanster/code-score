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

## LLM Report Generation

The LLM (Large Language Model) report generation system transforms structured evaluation data into human-readable narrative reports using external AI services.

### 1. ReportGenerator

The main orchestrator for LLM-powered report generation.

```python
from src.llm.report_generator import ReportGenerator

# Initialize with default components
generator = ReportGenerator()

# Initialize with custom components
from src.llm.template_loader import TemplateLoader
from src.llm.prompt_builder import PromptBuilder

loader = TemplateLoader(use_sandbox=True, cache_templates=True)
builder = PromptBuilder(template_loader=loader)
generator = ReportGenerator(template_loader=loader, prompt_builder=builder)

# Generate report from evaluation data
result = generator.generate_report(
    score_input_path="output/score_input.json",
    output_path="output/final_report.md",
    template_path="templates/custom_template.md",
    provider="gemini",
    verbose=True,
    timeout=60
)
```

#### Key Methods

- `generate_report(**kwargs) -> Dict[str, Any]`
  - Orchestrates complete report generation pipeline
  - Returns metadata about generation process and results

- `validate_prerequisites(provider: str) -> Dict[str, Any]`
  - Checks if all requirements are met for report generation
  - Validates provider availability, environment, and templates

- `get_available_providers() -> List[Dict[str, Any]]`
  - Returns list of configured LLM providers with availability status

- `get_template_info(template_path: Optional[str]) -> Dict[str, Any]`
  - Returns information about template configuration and validation

#### Return Type: Generation Result

```python
{
    "success": bool,                          # Whether generation succeeded
    "output_path": str,                       # Path to generated report
    "generation_time_seconds": float,         # Total processing time
    "report_metadata": {
        "word_count": int,                    # Generated report word count
        "validation_status": str,             # Content validation status
        "warnings": List[str]                 # Generation warnings
    },
    "provider_metadata": {
        "provider_name": str,                 # LLM provider used
        "model_name": str,                    # Specific model identifier
        "response_time_seconds": float        # LLM API response time
    },
    "template_metadata": {
        "template_name": str,                 # Template identifier
        "file_path": str,                     # Template file path
        "required_fields_used": List[str]     # Template variables used
    }
}
```

### 2. TemplateLoader

Handles loading, validation, and compilation of Jinja2 report templates.

```python
from src.llm.template_loader import TemplateLoader

# Initialize loader
loader = TemplateLoader(use_sandbox=True, cache_templates=True)

# Load template configuration
template_config = loader.load_template("path/to/template.md")

# Compile template for rendering
compiled_template = loader.compile_template(template_config)

# Load default template
default_template = loader.load_default_template()

# Create template from string
inline_template = loader.create_template_from_string(
    template_content="# Report\nScore: {{total.score}}",
    name="inline_template"
)

# Validate template syntax
is_valid = loader.validate_template_syntax_only("path/to/template.md")

# Get available templates
templates = loader.get_available_templates()
```

#### Key Methods

- `load_template(template_path: str) -> ReportTemplate`
  - Loads and validates template configuration from file

- `compile_template(template_config: ReportTemplate) -> Template`
  - Compiles Jinja2 template with caching support

- `validate_template_syntax_only(template_path: str) -> bool`
  - Validates template syntax without full loading

- `validate_template_with_context(template_config, sample_context) -> Dict`
  - Comprehensive template validation with sample data

### 3. PromptBuilder

Builds LLM prompts from evaluation data with content management and optimization.

```python
from src.llm.prompt_builder import PromptBuilder

# Initialize builder
builder = PromptBuilder()

# Build prompt from evaluation data
prompt = builder.build_prompt(
    score_input_data=score_data,
    template_config=template_config,
    custom_limits={"max_evidence_items": 5}
)

# Validate input data
issues = builder.validate_context_data(score_data)

# Estimate token usage
estimates = builder.estimate_token_usage(prompt)

# Optimize for specific provider
from src.llm.models.template_context import TemplateContext
context = TemplateContext.from_score_input(score_data)
optimized_context = builder.optimize_context_for_provider(context, "gemini")

# Get context statistics
stats = builder.get_context_statistics(context)
```

#### Key Methods

- `build_prompt(score_input_data, template_config, custom_limits=None) -> str`
  - Builds complete LLM prompt with content truncation

- `validate_context_data(score_input_data: Dict) -> List[str]`
  - Validates evaluation data structure and completeness

- `estimate_token_usage(prompt: str) -> Dict[str, Union[int, float]]`
  - Estimates token usage and costs for different providers

- `optimize_context_for_provider(context, provider_name: str) -> TemplateContext`
  - Applies provider-specific optimizations to context data

### 4. LLM Data Models

#### ReportTemplate

Configuration for report templates.

```python
from src.llm.models.report_template import ReportTemplate

template = ReportTemplate(
    name="custom_template",
    file_path="/path/to/template.md",
    description="Custom report template",
    required_fields=["repository", "total", "met_items"],
    content_limits={"max_evidence_items": 3}
)

# Validate template
template.validate_template_syntax()

# Load content
content = template.load_template_content()

# Check required fields
missing = template.check_required_fields(["repository", "total"])
```

#### LLMProviderConfig

Configuration for external LLM providers.

```python
from src.llm.models.llm_provider_config import LLMProviderConfig

config = LLMProviderConfig(
    provider_name="gemini",
    cli_command=["gemini", "--api-key", "${GEMINI_API_KEY}"],
    model_name="gemini-1.5-pro",
    timeout_seconds=30,
    max_tokens=2048,
    temperature=0.7
)

# Validate environment
missing_vars = config.validate_environment()

# Build CLI command
cmd = config.build_cli_command("Test prompt")

# Get default configurations
defaults = LLMProviderConfig.get_default_configs()
```

#### GeneratedReport

Final report output with metadata.

```python
from src.llm.models.generated_report import GeneratedReport

report = GeneratedReport(
    content="# Generated Report\nReport content here",
    template_used=template_metadata,
    provider_used=provider_metadata,
    input_metadata=input_metadata
)

# Calculate derived fields
report.calculate_derived_fields()

# Validate content
issues = report.validate_markdown_structure()

# Add warnings
report.add_warning("Custom warning message")

# Export to file format
file_content = report.to_file_content()
```

#### TemplateContext

Data structure for template rendering.

```python
from src.llm.models.template_context import TemplateContext

# Create from evaluation data
context = TemplateContext.from_score_input(score_input_data)

# Get categorized items
met_items = context.met_items
partial_items = context.partial_items
unmet_items = context.unmet_items

# Apply content limits
context.apply_content_limits({"max_evidence_items": 3})

# Convert to Jinja2 format
jinja_data = context.to_jinja_dict()

# Get statistics
all_items = context.get_all_items()
stats = {
    "total_items": len(all_items),
    "warnings": len(context.warnings)
}
```

## CLI Integration for LLM Features

### LLM Report Command

```python
# Programmatic usage
from src.cli.llm_report import main as llm_report_main
import sys

# Set command-line arguments
sys.argv = [
    "llm-report",
    "output/score_input.json",
    "--output", "output/final_report.md",
    "--provider", "gemini",
    "--verbose"
]

# Execute command
exit_code = llm_report_main()
```

### Integration with Main Analysis

```python
from src.cli.main import main

# Run analysis with LLM report generation
main.callback(
    repository_url="https://github.com/user/repo.git",
    enable_checklist=True,
    generate_llm_report=True,
    llm_template="templates/custom.md",
    llm_provider="gemini"
)
```

## Error Handling for LLM Features

### Exception Types

```python
from src.llm.report_generator import ReportGeneratorError, LLMProviderError
from src.llm.template_loader import TemplateLoaderError, TemplateValidationError
from src.llm.prompt_builder import PromptBuilderError, ContextLimitExceededError

try:
    generator = ReportGenerator()
    result = generator.generate_report("score_input.json")
except TemplateLoaderError as e:
    print(f"Template loading failed: {e}")
except LLMProviderError as e:
    print(f"LLM service error: {e}")
except ReportGeneratorError as e:
    print(f"Generation failed: {e}")
```

### Validation and Prerequisites

```python
# Check prerequisites before generation
generator = ReportGenerator()
validation = generator.validate_prerequisites("gemini")

if not validation["valid"]:
    print("Prerequisites not met:")
    for issue in validation["issues"]:
        print(f"- {issue}")
else:
    print("All prerequisites satisfied")
    result = generator.generate_report("score_input.json")
```

## Performance Considerations for LLM Features

- **Template compilation**: Cached automatically for repeated use
- **Content truncation**: Applied automatically for large datasets
- **Provider timeouts**: Configurable per provider (10-300 seconds)
- **Memory usage**: Optimized for datasets up to 500MB repositories
- **Generation time**: Typically <5 seconds excluding LLM API calls

## Complete LLM Workflow Example

```python
from src.llm.report_generator import ReportGenerator
from src.llm.template_loader import TemplateLoader
from src.llm.prompt_builder import PromptBuilder

# 1. Initialize components
generator = ReportGenerator()

# 2. Validate prerequisites
prerequisites = generator.validate_prerequisites("gemini")
if not prerequisites["valid"]:
    raise Exception(f"Prerequisites not met: {prerequisites['issues']}")

# 3. Generate report
result = generator.generate_report(
    score_input_path="output/score_input.json",
    output_path="output/final_report.md",
    template_path="templates/comprehensive.md",
    provider="gemini",
    verbose=True,
    timeout=60
)

# 4. Check results
if result["success"]:
    print(f"Report generated: {result['output_path']}")
    print(f"Generation time: {result['generation_time_seconds']:.2f}s")
    print(f"Word count: {result['report_metadata']['word_count']}")
else:
    print("Report generation failed")

# 5. Access generated report
with open(result["output_path"], 'r') as f:
    generated_report = f.read()
    print(f"Report length: {len(generated_report)} characters")
```

This LLM API enables flexible, programmatic report generation with comprehensive error handling, validation, and provider management.