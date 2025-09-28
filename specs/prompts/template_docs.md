# Template Field Documentation

This document describes the available template fields for LLM report generation.

## Repository Information

- `repository.url` - Git repository URL
- `repository.commit_sha` - Specific commit analyzed
- `repository.primary_language` - Main programming language detected
- `repository.size_mb` - Repository size in megabytes

## Evaluation Results

- `evaluation.timestamp` - When the evaluation was performed (ISO format)
- `total.score` - Overall score (0-100)
- `total.percentage` - Overall percentage (0.0-100.0)

## Category Scores

- `category_scores.code_quality.score` - Code quality points earned
- `category_scores.code_quality.max_points` - Maximum code quality points
- `category_scores.code_quality.percentage` - Code quality percentage
- `category_scores.testing.score` - Testing points earned
- `category_scores.testing.max_points` - Maximum testing points
- `category_scores.testing.percentage` - Testing percentage
- `category_scores.documentation.score` - Documentation points earned
- `category_scores.documentation.max_points` - Maximum documentation points
- `category_scores.documentation.percentage` - Documentation percentage

## Checklist Items

- `met_items` - Array of successfully completed criteria
  - `name` - Criterion name
  - `description` - Detailed description
- `unmet_items` - Array of failed criteria
  - `name` - Criterion name
  - `description` - Detailed description
- `partial_items` - Array of partially completed criteria
  - `name` - Criterion name
  - `description` - Detailed description

## Evidence Summary

- `evidence_summary` - Array of evidence by category
  - `category` - Evidence category (code_quality, testing, documentation, system)
  - `items` - Array of evidence items (limited to top 3 per category)
    - `source` - Evidence source file or tool
    - `description` - Evidence description
    - `confidence` - Confidence level (0.0-1.0)

## Pipeline Information

- `warnings` - Array of pipeline warnings
  - `message` - Warning message

## Helper Variables (Generated)

- `lowest_category` - Category with lowest score (for recommendations)
- `code_quality_issues` - Boolean indicating code quality problems
- `testing_issues` - Boolean indicating testing problems
- `documentation_issues` - Boolean indicating documentation problems
- `code_quality_recommendation` - Specific code quality recommendation
- `testing_recommendation` - Specific testing recommendation
- `documentation_recommendation` - Specific documentation recommendation

## Jinja2 Features Available

- `{{variable}}` - Variable interpolation
- `{{#if condition}}...{{/if}}` - Conditional blocks
- `{{#each array}}...{{/each}}` - Iteration over arrays
- `{{#unless condition}}...{{/unless}}` - Negative conditionals
- `(gte value threshold)` - Greater than or equal comparison
- `(lt value threshold)` - Less than comparison

## Content Limits

Templates should respect these limits to avoid LLM context overflow:

- Maximum 3 evidence items per category
- Maximum 500 characters per evidence description
- Maximum 30,000 characters total context length

Evidence truncation is applied automatically when limits are exceeded.