# Data Model: Build Validation

**Feature**: Complete Build Detection Integration
**Phase**: 1 - Design & Contracts
**Date**: 2025-10-09

## Overview

This document defines the data models required to support build validation across all supported programming languages (Python, JavaScript/TypeScript, Java, Go). The models extend the existing `MetricsCollection` schema to include structured build validation results while maintaining backward compatibility.

---

## Core Entities

### 1. BuildValidationResult

**Purpose**: Represents the outcome of attempting to build a project, including success status, tool information, and diagnostic details.

**Pydantic Model**:
```python
from pydantic import BaseModel, validator
from typing import Optional

class BuildValidationResult(BaseModel):
    """
    Structured result from build validation execution.

    Fields:
        success: Build outcome - True (success), False (failure), None (tool unavailable)
        tool_used: Name of build tool executed ("uv", "npm", "go", "mvn", "gradle", "none")
        execution_time_seconds: Duration of build execution
        error_message: Error details if build failed (truncated to 1000 chars)
        exit_code: Process exit code from build tool
    """
    success: Optional[bool]  # True=pass, False=fail, None=unavailable
    tool_used: str
    execution_time_seconds: float
    error_message: Optional[str] = None
    exit_code: Optional[int] = None

    @validator("error_message")
    def truncate_error_message(cls, v: Optional[str]) -> Optional[str]:
        """Truncate error messages to 1000 characters per NFR-002."""
        if v and len(v) > 1000:
            return v[:997] + "..."
        return v

    @validator("execution_time_seconds")
    def validate_execution_time(cls, v: float) -> float:
        """Ensure execution time is non-negative."""
        if v < 0:
            raise ValueError("Execution time cannot be negative")
        return v

    @validator("tool_used")
    def validate_tool_name(cls, v: str) -> str:
        """Ensure tool_used is a known value."""
        valid_tools = {"uv", "build", "npm", "yarn", "go", "mvn", "gradle", "none"}
        if v not in valid_tools:
            # Allow unknown tools but log warning
            pass
        return v
```

**Field Semantics**:
- `success`:
  - `True`: Build completed successfully (exit code 0)
  - `False`: Build attempted but failed (exit code != 0)
  - `None`: Build could not be attempted (tool unavailable, no build config)
- `tool_used`: Identifies which build tool was executed
  - `"none"`: No build tool available or no build configuration detected
  - Specific tool name: Indicates which tool performed the validation
- `execution_time_seconds`: Wall-clock time from process start to completion
  - Includes tool startup time and actual build time
  - Used for performance monitoring and timeout analysis
- `error_message`: Human-readable error description
  - Captured from stderr when build fails
  - Truncated to 1000 characters to prevent output bloat
  - Null when build succeeds or tool unavailable
- `exit_code`: Process exit code from build tool
  - 0: Success
  - Non-zero: Failure (specific code depends on tool)
  - Null: Tool not executed (unavailable or no config)

**State Transitions**:
```
Initial State: success=None, tool_used="none"
    ↓
    ├─→ Tool Available & Config Detected
    │       ↓
    │       ├─→ Build Succeeds → success=True, exit_code=0
    │       └─→ Build Fails → success=False, exit_code!=0, error_message set
    │
    └─→ Tool Unavailable → success=None, tool_used="none", error_message="Tool not available"
```

**Example Instances**:
```python
# Successful Python build
BuildValidationResult(
    success=True,
    tool_used="uv",
    execution_time_seconds=3.14,
    error_message=None,
    exit_code=0
)

# Failed JavaScript build
BuildValidationResult(
    success=False,
    tool_used="npm",
    execution_time_seconds=8.52,
    error_message="ERROR in src/app.js\nModule not found: Cannot resolve './missing-module'...",
    exit_code=1
)

# Tool unavailable
BuildValidationResult(
    success=None,
    tool_used="none",
    execution_time_seconds=0.0,
    error_message="Maven not available in PATH",
    exit_code=None
)
```

---

### 2. CodeQualityMetrics (Extended)

**Purpose**: Extend existing `CodeQualityMetrics` model to include build validation data.

**Existing Model** (from `src/metrics/models/metrics_collection.py`):
```python
class CodeQualityMetrics(BaseModel):
    lint_results: LintResult
    build_success: Optional[bool] = None  # Currently always None
    security_issues: List[SecurityIssue]
    dependency_audit: DependencyAudit
```

**Proposed Extension**:
```python
class CodeQualityMetrics(BaseModel):
    lint_results: LintResult
    build_success: Optional[bool] = None  # NOW POPULATED: True/False/None
    build_details: Optional[BuildValidationResult] = None  # NEW: Detailed diagnostics
    security_issues: List[SecurityIssue]
    dependency_audit: DependencyAudit
```

**Field Changes**:
- `build_success`: **Behavior change** (not schema change)
  - Before: Always `None` (placeholder)
  - After: Populated with actual build outcome
  - Values: `True` (success), `False` (failure), `None` (unavailable)
  - Purpose: Simple boolean for checklist evaluation (FR-005)
  - Backward compatible: `None` is still valid (existing code unaffected)

- `build_details`: **New field** (additive change)
  - Type: `Optional[BuildValidationResult]`
  - Purpose: Provide diagnostic information for debugging
  - Contains: Tool name, execution time, error messages, exit codes
  - Null when: Build validation not performed or skipped
  - Included in: Detailed metrics output, not required for basic evaluation

**Backward Compatibility**:
- Schema version: No bump required (additive change)
- Existing code: Continues to work (build_success defaults to None)
- Checklist evaluation: Now sees True/False/None instead of always None
- Output generators: Must handle new build_details field (optional)

**JSON Representation**:
```json
{
  "code_quality": {
    "lint_results": { ... },
    "build_success": true,
    "build_details": {
      "success": true,
      "tool_used": "uv",
      "execution_time_seconds": 3.14,
      "error_message": null,
      "exit_code": 0
    },
    "security_issues": [],
    "dependency_audit": { ... }
  }
}
```

---

## Data Relationships

### Entity Relationship Diagram

```
MetricsCollection
    └── CodeQualityMetrics
            ├── build_success: bool | None (simple outcome)
            └── build_details: BuildValidationResult | None (detailed diagnostics)
                    ├── success: bool | None
                    ├── tool_used: str
                    ├── execution_time_seconds: float
                    ├── error_message: str | None
                    └── exit_code: int | None
```

### Data Flow

```
ToolRunner.run_build()
    ↓ returns BuildValidationResult
ToolExecutor._run_build_validation()
    ↓ collects from runner
ToolExecutor.execute_tools()
    ↓ populates MetricsCollection
MetricsCollection.code_quality.build_success ← BuildValidationResult.success
MetricsCollection.code_quality.build_details ← BuildValidationResult (full object)
    ↓
OutputGenerator.save_results()
    ↓ serializes to JSON
submission.json (includes build_success and build_details)
```

---

## Validation Rules

### BuildValidationResult Validation

1. **Execution Time**: Must be non-negative float
   - Validation: `execution_time_seconds >= 0`
   - Error: `ValueError("Execution time cannot be negative")`

2. **Error Message Length**: Must not exceed 1000 characters
   - Validation: Automatic truncation in validator
   - Action: Truncate to 997 chars + "..."

3. **Success/Tool Consistency**:
   - If `tool_used="none"`, then `success` should be `None`
   - If `exit_code=0`, then `success` should be `True`
   - If `exit_code!=0`, then `success` should be `False`

4. **Error Message Presence**:
   - If `success=False`, `error_message` should be populated
   - If `success=True`, `error_message` should be `None`
   - If `success=None`, `error_message` may describe unavailability reason

### CodeQualityMetrics Validation

1. **Build Fields Consistency**:
   - If `build_success` is not `None`, `build_details` should be populated
   - If `build_details` is `None`, `build_success` should be `None`

2. **Backward Compatibility**:
   - All fields optional or have defaults
   - Can deserialize old JSON (missing build_details)
   - Can serialize to old format (omit build_details if None)

---

## Schema Compatibility

### submission.json Schema Extension

**Before** (existing):
```json
{
  "metrics": {
    "code_quality": {
      "build_success": null
    }
  }
}
```

**After** (with feature):
```json
{
  "metrics": {
    "code_quality": {
      "build_success": true,
      "build_details": {
        "success": true,
        "tool_used": "uv",
        "execution_time_seconds": 3.14,
        "error_message": null,
        "exit_code": 0
      }
    }
  }
}
```

**Compatibility**: ✅ Backward compatible
- Old readers: Ignore `build_details`, see `build_success` change from always-null to boolean
- New readers: Use both `build_success` and `build_details`
- Schema version: No bump (additive change, nullable fields)

### score_input.json Schema (for LLM)

**Checklist evaluator only needs**:
```json
{
  "metrics": {
    "code_quality": {
      "build_success": true
    }
  }
}
```

**LLM report can optionally include** (from build_details):
- Tool used for transparency
- Execution time for performance insights
- Error messages for failure analysis

---

## Implementation Notes

### File Locations

1. **BuildValidationResult Model**:
   - File: `src/metrics/models/build_validation.py` (NEW)
   - Import: `from src.metrics.models.build_validation import BuildValidationResult`

2. **CodeQualityMetrics Extension**:
   - File: `src/metrics/models/metrics_collection.py` (MODIFY)
   - Change: Add `build_details: Optional[BuildValidationResult] = None`
   - Import: `from .build_validation import BuildValidationResult`

### Migration Path

**Phase 1: Add BuildValidationResult model** (this PR)
- Create new model file
- Import in metrics_collection.py
- Add build_details field to CodeQualityMetrics
- No behavior change yet (field remains None)

**Phase 2: Populate build_success** (tool runner implementations)
- Implement run_build() in each tool runner
- Wire to ToolExecutor
- Populate build_success and build_details fields

**Phase 3: Update consumers** (checklist evaluator)
- Update checklist_mapping.yaml to use build_success
- Change evaluation from "always unmet" to actual scoring
- Update target-repository-scoring.md status from "△" to "✓"

---

## Testing Strategy

### Unit Tests

**Test BuildValidationResult**:
- Valid instances with all field combinations
- Error message truncation (>1000 chars)
- Negative execution time rejection
- Serialization/deserialization

**Test CodeQualityMetrics**:
- Backward compatibility (deserialize old JSON)
- Forward compatibility (serialize with build_details)
- Field defaults (build_success=None, build_details=None)

### Integration Tests

**Test data flow**:
- ToolRunner.run_build() → BuildValidationResult
- BuildValidationResult → CodeQualityMetrics
- CodeQualityMetrics → submission.json
- submission.json → score_input.json

### Contract Tests

**Schema validation**:
- submission.json includes build_success field
- build_success is bool | null (never undefined)
- build_details matches BuildValidationResult schema
- Error messages truncated to 1000 chars

---

## Summary

**New Models**:
1. `BuildValidationResult`: Structured build outcome with diagnostics

**Modified Models**:
1. `CodeQualityMetrics`: Add `build_details` field, populate `build_success`

**Backward Compatibility**: ✅ Fully compatible (additive changes, nullable fields)

**Next Steps**:
- Create JSON schema for contract tests
- Implement Pydantic models in source code
- Write failing contract tests
- Proceed to implementation (tool runners)
