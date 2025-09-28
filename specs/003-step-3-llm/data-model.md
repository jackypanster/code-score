# Data Model: LLM-Generated Code Review Reports

**Phase 1 Output** | **Date**: 2025-09-27

## Overview

This feature reuses existing data models from the checklist evaluation system and introduces minimal new structures for template handling and LLM provider configuration.

## Existing Entities (Reused)

### ScoreInput
**Source**: `src/metrics/models/score_input.py` (existing)
**Purpose**: Primary input data for report generation
**Key Attributes**:
- `repository_info`: Repository metadata (URL, commit, language)
- `evaluation_result`: Complete checklist evaluation with scores
- `evidence_paths`: References to detailed evidence files

**Relationships**:
- Consumed by ReportGenerator
- Contains EvaluationResult and CategoryBreakdown data

### EvaluationResult
**Source**: `src/metrics/models/evaluation_result.py` (existing)
**Purpose**: Complete evaluation data with scoring breakdown
**Key Attributes**:
- `checklist_items`: List of evaluated criteria
- `total_score`: Overall score and percentage
- `category_breakdowns`: Scores by dimension (code quality, testing, documentation)

**Relationships**:
- Embedded in ScoreInput
- Contains multiple ChecklistItem objects

### ChecklistItem
**Source**: `src/metrics/models/checklist_item.py` (existing)
**Purpose**: Individual evaluation criterion
**Key Attributes**:
- `id`: Unique identifier
- `name`: Human-readable name
- `evaluation_status`: "met", "partial", "unmet"
- `score`: Numerical score value
- `evidence_references`: Supporting evidence

**Relationships**:
- Multiple items per EvaluationResult
- Referenced in template grouping logic

## New Entities

### ReportTemplate
**Purpose**: Template configuration and metadata
**Key Attributes**:
- `name`: Template identifier
- `file_path`: Path to template file
- `description`: Human-readable description
- `required_fields`: List of placeholder fields
- `content_limits`: Maximum content lengths for truncation

**Validation Rules**:
- file_path must exist and be readable
- required_fields must be valid Jinja2 identifiers
- content_limits must be positive integers

**State Transitions**: Static configuration, no state changes

### LLMProviderConfig
**Purpose**: LLM service configuration
**Key Attributes**:
- `provider_name`: "gemini", "openai", etc.
- `cli_command`: Base command and arguments
- `model_name`: Specific model identifier
- `timeout_seconds`: API call timeout
- `max_tokens`: Response length limit

**Validation Rules**:
- cli_command must be valid shell command
- timeout_seconds must be between 10-300
- max_tokens must match provider limits

**State Transitions**: Static configuration, no state changes

### GeneratedReport
**Purpose**: Final report output with metadata
**Key Attributes**:
- `content`: Generated markdown content
- `template_used`: Reference to source template
- `generation_timestamp`: When report was created
- `provider_used`: LLM provider information
- `truncation_applied`: Whether content was truncated

**Validation Rules**:
- content must be valid markdown
- generation_timestamp must be ISO format
- truncation_applied must document what was truncated

**State Transitions**: Immutable once generated

## Template Data Structure

### TemplateContext
**Purpose**: Data passed to template rendering
**Key Attributes**:
- `repository`: Repository metadata
- `total`: Score summary information
- `met_items`: Successfully completed criteria
- `partial_items`: Partially completed criteria
- `unmet_items`: Failed criteria
- `evidence_summary`: Top evidence items (truncated)
- `warnings`: Pipeline warnings and issues

**Relationships**:
- Extracted from ScoreInput
- Consumed by Jinja2 template engine

### Evidence Truncation Strategy
**Purpose**: Manage LLM context limits
**Rules**:
- Maximum 3 evidence items per category
- Prioritize by confidence level (highest first)
- Include evidence source and description
- Add truncation indicators when content reduced

## File Structure Mapping

### Input Data Flow
```
score_input.json → ScoreInput model → TemplateContext → Jinja2 → LLM prompt
```

### Output Data Flow
```
LLM response → GeneratedReport model → final_report.md
```

### Configuration Flow
```
template.md → ReportTemplate → Template compilation
provider.yaml → LLMProviderConfig → CLI command generation
```

## Error Handling

### Data Validation Errors
- **Missing required fields**: Raise ValidationError with specific field names
- **Invalid file paths**: Raise FileNotFoundError with full path
- **Malformed JSON**: Raise JSONDecodeError with line information

### Template Processing Errors
- **Invalid template syntax**: Raise TemplateError with line number
- **Missing template variables**: Raise UndefinedError with variable name
- **Template file not found**: Raise FileNotFoundError with search paths

### LLM Provider Errors
- **CLI command not found**: Raise CommandNotFoundError with provider name
- **API timeout**: Raise TimeoutError with duration
- **Invalid API response**: Raise ResponseError with status information

## Performance Characteristics

### Memory Usage
- ScoreInput: ~1-5MB for large repositories
- TemplateContext: ~500KB after truncation
- GeneratedReport: ~10-50KB final output

### Processing Time
- Data model validation: <100ms
- Template rendering: <50ms
- LLM API call: 5-30 seconds (external dependency)

## Future Extensions

### Additional Template Fields
- Custom evaluation criteria
- Repository-specific recommendations
- Historical score comparisons

### Enhanced Evidence Handling
- Evidence categorization by importance
- Multi-language evidence support
- Evidence confidence weighting

### Provider-Specific Optimizations
- Provider-specific prompt formats
- Model-specific token limits
- Response format preferences

---

**Data Model Complete**: All entities defined with validation rules
**Next**: Generate API contracts and test schemas