# Data Model: Smoke Test Suite

**Feature**: End-to-End Smoke Test Suite
**Date**: 2025-09-28
**Status**: Design Phase

## Entity Overview

The smoke test feature involves simple entities for validation workflow without complex data relationships.

## Core Entities

### SmokeTestExecution
**Purpose**: Represents a single execution of the smoke test workflow

**Attributes**:
- `repository_url`: Target repository for testing (string, immutable)
- `execution_start_time`: When test execution began (datetime)
- `execution_end_time`: When test execution completed (datetime)
- `pipeline_exit_code`: Return code from pipeline script execution (integer)
- `pipeline_duration`: Time taken for pipeline execution (timedelta)
- `working_directory`: Project root directory for execution (pathlib.Path)

**Validation Rules**:
- `repository_url` must be valid Git repository URL
- `execution_start_time` must be before `execution_end_time`
- `pipeline_exit_code` of 0 indicates success
- `working_directory` must exist and be readable

### OutputArtifact
**Purpose**: Represents expected output files from the pipeline

**Attributes**:
- `file_path`: Path to output file (pathlib.Path)
- `expected_name`: Expected filename (string)
- `file_exists`: Whether file was found (boolean)
- `file_size`: Size of output file in bytes (integer, optional)
- `last_modified`: File modification timestamp (datetime, optional)

**Validation Rules**:
- `file_path` must be under output/ directory
- `expected_name` must match one of: submission.json, score_input.json, evaluation_report.md
- `file_exists` is True for successful validation
- `file_size` > 0 for valid output files

### ValidationResult
**Purpose**: Represents overall smoke test validation outcome

**Attributes**:
- `test_passed`: Overall test success status (boolean)
- `pipeline_successful`: Whether pipeline execution succeeded (boolean)
- `all_files_present`: Whether all expected files exist (boolean)
- `error_message`: Descriptive error for failures (string, optional)
- `execution_summary`: Brief result description (string)

**Validation Rules**:
- `test_passed` is True only if both `pipeline_successful` and `all_files_present` are True
- `error_message` required when `test_passed` is False
- `execution_summary` always provided for test reporting

## Entity Relationships

```
SmokeTestExecution (1) ─── creates ───> (3) OutputArtifact
                    │
                    └─── produces ───> (1) ValidationResult
```

### Relationship Rules
- One SmokeTestExecution creates exactly 3 OutputArtifacts (one per expected file)
- One SmokeTestExecution produces exactly 1 ValidationResult
- ValidationResult depends on both pipeline execution and OutputArtifact validation

## State Transitions

### SmokeTestExecution States
1. **Initialized**: Test created with repository URL and working directory
2. **Executing**: Pipeline script running via subprocess
3. **Completed**: Pipeline finished (success or failure)
4. **Validated**: Output files checked and ValidationResult created

### OutputArtifact States
1. **Expected**: File anticipated from pipeline execution
2. **Verified**: File existence and basic validation completed

### ValidationResult States
1. **Success**: All validations passed
2. **Pipeline Failure**: Script execution failed
3. **File Missing**: Expected outputs not found
4. **Unknown Error**: Unexpected failure condition

## Implementation Notes

### Data Storage
- All entities are transient (test execution lifetime only)
- No persistent storage required
- Data exists as Python objects during test execution

### Error Handling
- Entity validation follows KISS principle: immediate failure on invalid state
- No complex error recovery or state rollback mechanisms
- Clear error messages for debugging test failures

### Performance Considerations
- Minimal memory footprint (only 3 output files to track)
- No indexing or query optimization needed
- Validation checks are simple file system operations

## Schema Validation

### Expected Output File Formats
- `submission.json`: Valid JSON with metrics collection schema
- `score_input.json`: Valid JSON with evaluation results schema
- `evaluation_report.md`: Valid Markdown with human-readable content

### Basic Format Validation
- JSON files: Validate parseable JSON structure
- Markdown files: Validate readable text content
- All files: Non-zero size requirement

## Dependencies

### Internal Dependencies
- No dependencies on existing code-score data models
- Independent validation logic for smoke test purposes

### External Dependencies
- pathlib for file path operations
- subprocess for pipeline execution
- datetime for execution timing
- JSON parsing for basic output validation