# Phase 1: Data Model Design - Toolchain Validation Entities

**Date**: 2025-10-11
**Feature**: Unified Toolchain Health Check Layer
**Spec Reference**: [spec.md](./spec.md) | **Research**: [research.md](./research.md)

This document defines the data structures and validation logic for the toolchain validation system.

---

## Entity Relationship Overview

```
┌─────────────────┐
│ ToolRequirement │ (Static registry, defined once per tool)
└────────┬────────┘
         │ 1 validates
         │
         ↓ N
┌─────────────────┐
│ValidationResult │ (Created per tool during validation)
└────────┬────────┘
         │ N collected by
         │
         ↓ 1
┌─────────────────┐
│ValidationReport │ (Single report per validation run)
└─────────────────┘
         │ raises
         ↓
┌──────────────────────────┐
│ToolchainValidationError │ (Exception with formatted message)
└──────────────────────────┘
```

---

## Core Entities

### 1. ToolRequirement

**Purpose**: Define a single required CLI tool with its validation criteria

**Source**: Spec FR-014 (tool dependencies), Key Entities line 148

**Definition**:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)  # Immutable configuration
class ToolRequirement:
    """Specification for a required analysis tool.

    Attributes:
        name: CLI command name (e.g., "ruff", "npm", "go")
        language: Target language or "global" for all repositories
        category: Tool purpose (lint/test/security/build)
        doc_url: Official documentation URL for error messages
        min_version: Optional minimum version requirement (semver)
        version_command: CLI flag to get version (default: "--version")

    Examples:
        >>> ToolRequirement(
        ...     name="ruff",
        ...     language="python",
        ...     category="lint",
        ...     doc_url="https://docs.astral.sh/ruff",
        ...     min_version="0.1.0",
        ...     version_command="--version"
        ... )
    """
    name: str
    language: str  # "python" | "javascript" | "typescript" | "java" | "go" | "global"
    category: str  # "lint" | "test" | "security" | "build"
    doc_url: str
    min_version: Optional[str] = None
    version_command: str = "--version"

    def __post_init__(self):
        """Validate field constraints."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if self.language not in {"python", "javascript", "typescript", "java", "go", "global"}:
            raise ValueError(f"Invalid language: {self.language}")
        if self.category not in {"lint", "test", "security", "build"}:
            raise ValueError(f"Invalid category: {self.category}")
        if not self.doc_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid doc_url: {self.doc_url}")
```

**Validation Rules** (enforced by contracts/tool_requirement_schema.json):
- `name`: Non-empty string
- `language`: Enum constraint (6 allowed values)
- `category`: Enum constraint (4 allowed values)
- `doc_url`: Valid HTTP/HTTPS URL
- `min_version`: Optional string (null allowed)
- `version_command`: Non-empty string (default provided)

**State**: Immutable (frozen dataclass) - defined at module load time

**Relationships**:
- 1 ToolRequirement → N ValidationResults (one per validation run)
- Stored in: `tool_registry.py` as module-level constants

---

### 2. ValidationResult

**Purpose**: Capture the outcome of validating a single tool

**Source**: Spec Key Entities line 150, FR-010 (error handling), FR-015 (version checking), FR-016 (permission errors)

**Definition**:
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ValidationResult:
    """Result of validating a single tool's availability and compatibility.

    Attributes:
        tool_name: Name of the validated tool
        found: Whether tool was found in PATH
        path: Absolute path to tool executable (if found)
        version: Detected version string (if retrievable)
        version_ok: Whether version meets minimum requirement
        permissions: File permission string (if permission error)
        error_category: Classification of validation error
        error_details: Human-readable error explanation

    Error Categories:
        - "missing": Tool not found via shutil.which()
        - "outdated": Tool found but version < minimum
        - "permission": Tool found but not executable
        - "other": Version check failed or unexpected error

    Examples:
        >>> # Successful validation
        >>> ValidationResult(
        ...     tool_name="ruff",
        ...     found=True,
        ...     path="/usr/bin/ruff",
        ...     version="0.1.8",
        ...     version_ok=True
        ... )

        >>> # Missing tool
        >>> ValidationResult(
        ...     tool_name="pytest",
        ...     found=False,
        ...     error_category="missing",
        ...     error_details="Tool not found in PATH"
        ... )

        >>> # Outdated version
        >>> ValidationResult(
        ...     tool_name="npm",
        ...     found=True,
        ...     path="/usr/local/bin/npm",
        ...     version="7.5.0",
        ...     version_ok=False,
        ...     error_category="outdated",
        ...     error_details="Current: 7.5.0, Minimum: 8.0.0"
        ... )

        >>> # Permission error
        >>> ValidationResult(
        ...     tool_name="ruff",
        ...     found=True,
        ...     path="/usr/bin/ruff",
        ...     permissions="-rw-r--r--",
        ...     version_ok=False,
        ...     error_category="permission",
        ...     error_details="Tool exists but is not executable"
        ... )
    """
    tool_name: str
    found: bool
    path: Optional[str] = None
    version: Optional[str] = None
    version_ok: bool = True  # True by default (no version requirement)
    permissions: Optional[str] = None
    error_category: Optional[str] = None  # "missing" | "outdated" | "permission" | "other"
    error_details: Optional[str] = None

    def __post_init__(self):
        """Validate error category enum."""
        if self.error_category and self.error_category not in {"missing", "outdated", "permission", "other"}:
            raise ValueError(f"Invalid error_category: {self.error_category}")

    def is_valid(self) -> bool:
        """Check if tool passed all validation checks."""
        return self.found and self.version_ok and self.error_category is None
```

**Validation Rules** (enforced by contracts/validation_result_schema.json):
- `tool_name`: Non-empty string (required)
- `found`: Boolean (required)
- `path`: String or null (optional)
- `version`: String or null (optional)
- `version_ok`: Boolean (default true)
- `permissions`: String or null (optional)
- `error_category`: Enum of {"missing", "outdated", "permission", "other"} or null
- `error_details`: String or null (optional)

**State Transitions**: None (created once per validation)

**Relationships**:
- N ValidationResults → 1 ValidationReport (collected into report)

---

### 3. ValidationReport

**Purpose**: Aggregate all tool validation results and generate comprehensive error messages

**Source**: Spec Key Entities line 154, FR-017 (error categorization), FR-013 (message format)

**Definition**:
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

@dataclass
class ValidationReport:
    """Comprehensive report of toolchain validation results.

    Attributes:
        passed: Overall validation status (True if all tools valid)
        language: Target language being validated
        checked_tools: List of tool names that were validated
        errors_by_category: Dict mapping error categories to failed ValidationResults
        timestamp: When validation was performed

    Error Categorization (FR-017):
        errors_by_category = {
            "missing": [ValidationResult(tool_name="pytest", found=False, ...)],
            "outdated": [ValidationResult(tool_name="npm", version="7.5.0", ...)],
            "permission": [ValidationResult(tool_name="ruff", permissions="-rw-r--r--", ...)]
        }

    Examples:
        >>> # All tools pass
        >>> report = ValidationReport(
        ...     passed=True,
        ...     language="python",
        ...     checked_tools=["ruff", "pytest", "pip-audit"],
        ...     errors_by_category={},
        ...     timestamp=datetime.utcnow()
        ... )

        >>> # Multiple errors grouped
        >>> report = ValidationReport(
        ...     passed=False,
        ...     language="python",
        ...     checked_tools=["ruff", "pytest", "npm"],
        ...     errors_by_category={
        ...         "missing": [ValidationResult(tool_name="pytest", found=False, ...)],
        ...         "outdated": [ValidationResult(tool_name="npm", version="7.5.0", ...)],
        ...         "permission": [ValidationResult(tool_name="ruff", permissions="-rw-r--r--", ...)]
        ...     },
        ...     timestamp=datetime.utcnow()
        ... )
    """
    passed: bool
    language: str
    checked_tools: List[str]
    errors_by_category: Dict[str, List[ValidationResult]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def format_error_message(self) -> str:
        """Generate Chinese error message grouped by category (FR-013, FR-017).

        Returns:
            Multi-line string with categorized errors:
            工具链验证失败，发现以下问题：

            【缺少工具】
            - 缺少工具 pytest。请在评分主机安装后重试（参考 https://docs.pytest.org）

            【版本过旧】
            - 工具 npm 版本过旧（当前: 7.5.0，最低要求: 8.0.0）。请升级后重试（参考 https://docs.npmjs.com）

            【权限不足】
            - 工具 ruff 位于 /usr/bin/ruff 但权限不足（当前: -rw-r--r--）。请修复权限后重试。
        """
        from .toolchain_messages import ValidationMessages

        if self.passed:
            return f"✓ 工具链验证通过 (语言: {self.language}，检查工具: {len(self.checked_tools)}个)"

        lines = [ValidationMessages.VALIDATION_FAILED_HEADER]

        # Missing tools section
        if "missing" in self.errors_by_category:
            lines.append(ValidationMessages.CATEGORY_MISSING_HEADER)
            for result in self.errors_by_category["missing"]:
                # Get ToolRequirement to access doc_url (passed in via context)
                lines.append(f"- {result.error_details}")

        # Outdated tools section
        if "outdated" in self.errors_by_category:
            lines.append(ValidationMessages.CATEGORY_OUTDATED_HEADER)
            for result in self.errors_by_category["outdated"]:
                lines.append(f"- {result.error_details}")

        # Permission errors section
        if "permission" in self.errors_by_category:
            lines.append(ValidationMessages.CATEGORY_PERMISSION_HEADER)
            for result in self.errors_by_category["permission"]:
                lines.append(f"- {result.error_details}")

        # Other errors section (if any)
        if "other" in self.errors_by_category:
            lines.append("\n【其他错误】")
            for result in self.errors_by_category["other"]:
                lines.append(f"- {result.tool_name}: {result.error_details}")

        return "\n".join(lines)

    def get_failed_tools(self) -> List[str]:
        """Return list of tool names that failed validation."""
        failed = []
        for results in self.errors_by_category.values():
            failed.extend(r.tool_name for r in results)
        return failed

    def get_error_count(self) -> int:
        """Return total number of validation errors."""
        return sum(len(results) for results in self.errors_by_category.values())
```

**Validation Rules** (enforced by contracts/validation_report_schema.json):
- `passed`: Boolean (required)
- `language`: Non-empty string (required)
- `checked_tools`: Array of strings (required)
- `errors_by_category`: Dict with string keys, array values (required)
- `timestamp`: ISO 8601 datetime string (required)

**State**: Created once at end of validation run

**Relationships**:
- 1 ValidationReport → 1 ToolchainValidationError (if validation fails)

---

## Supporting Entities

### 4. ToolchainValidationError (Exception)

**Purpose**: Custom exception raised when validation fails, containing full report

**Source**: Research section 5 (integration point), FR-003 (immediate failure)

**Definition**:
```python
# src/metrics/error_handling.py (MODIFIED)

from .models.validation_report import ValidationReport

class CodeScoreError(Exception):
    """Base exception for code-score tool."""
    pass

class ToolchainValidationError(CodeScoreError):
    """Raised when toolchain validation fails.

    This exception is raised by ToolchainManager when any required tool
    is missing, outdated, or has permission issues. The exception contains
    a ValidationReport with categorized errors and a formatted Chinese
    error message ready for display.

    Attributes:
        report: ValidationReport with detailed categorized errors
        message: Formatted multi-line Chinese error message (from report.format_error_message())

    Usage:
        try:
            manager.validate_for_language("python")
        except ToolchainValidationError as e:
            print(e.message, file=sys.stderr)
            sys.exit(1)
    """
    def __init__(self, report: ValidationReport):
        self.report = report
        self.message = report.format_error_message()
        super().__init__(self.message)
```

---

## Data Flow Diagram

```
1. CLI Startup
   ↓
2. ToolchainManager.validate_for_language("python")
   ↓
3. Load ToolRequirements for Python from tool_registry
   [ruff, pytest, pip-audit, uv, python3]
   ↓
4. For each ToolRequirement:
   - ToolDetector.check_availability(tool.name)
     → ValidationResult (found? path?)
   - ToolDetector.get_version(tool.name, tool.version_command)
     → ValidationResult (version?)
   - ToolDetector.compare_versions(current, tool.min_version)
     → ValidationResult (version_ok?)
   - ToolDetector.check_permissions(path)
     → ValidationResult (permissions? error_category?)
   ↓
5. Collect all ValidationResults
   ↓
6. Build ValidationReport
   - Group results by error_category
   - Set passed = (no errors)
   ↓
7. If passed == False:
   raise ToolchainValidationError(report)
   ↓
8. Exception caught in cli/main.py
   → Print report.message
   → sys.exit(1)
```

---

## Validation Rules Summary

### From Functional Requirements

- **FR-001**: All language-specific tools validated before analysis
  - Implementation: `ToolchainManager.validate_for_language()` checks all tools for given language
- **FR-002**: Tools organized by language and category
  - Implementation: `ToolRequirement.language` and `ToolRequirement.category` fields
- **FR-003**: Immediate failure on any missing tool
  - Implementation: `ToolchainValidationError` raised, CLI exits with code 1
- **FR-012**: No optional tools (all strictly required)
  - Implementation: No `optional` flag in `ToolRequirement`; all tools checked
- **FR-015**: Version validation with minimum requirements
  - Implementation: `ToolRequirement.min_version` + `ToolDetector.compare_versions()`
- **FR-016**: Permission error detection
  - Implementation: `ValidationResult.permissions` + `os.access(os.X_OK)` check
- **FR-017**: Errors grouped by category
  - Implementation: `ValidationReport.errors_by_category` Dict structure

### From Research Decisions

- **Tool Detection**: Use `shutil.which()` (Research section 1)
  - Implementation: `ToolDetector.check_availability()` calls `shutil.which(tool_name)`
- **Version Parsing**: Subprocess + regex extraction (Research section 2)
  - Implementation: `ToolDetector.get_version()` uses `subprocess.run()` + regex
- **Error Messages**: Chinese f-string templates (Research section 3)
  - Implementation: `ValidationMessages` class with static templates
- **Permissions**: `os.access(os.X_OK)` + `stat.filemode()` (Research section 4)
  - Implementation: `ToolDetector.check_permissions()` returns (bool, str)

---

## File Organization

```
src/metrics/
├── models/
│   ├── tool_requirement.py        # ToolRequirement dataclass
│   ├── validation_result.py       # ValidationResult dataclass
│   └── validation_report.py       # ValidationReport dataclass + format_error_message()
├── toolchain_messages.py          # ValidationMessages constants
├── tool_registry.py               # TOOL_REQUIREMENTS dict by language
├── tool_detector.py               # Low-level detection functions
├── toolchain_manager.py           # High-level validation orchestrator
└── error_handling.py              # ToolchainValidationError (modified)
```

---

## Next Steps

1. Generate JSON schemas for contract testing (Phase 1.2)
2. Write contract tests to validate schemas (Phase 1.3)
3. Implement data models with validation logic (Phase 2 - tasks.md)

---
*Data model design completed: 2025-10-11*
*Ready for contract schema generation*
