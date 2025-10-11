# Phase 0: Research - Toolchain Validation Implementation Decisions

**Date**: 2025-10-11
**Feature**: Unified Toolchain Health Check Layer
**Spec Reference**: [spec.md](./spec.md)

This document consolidates all technical research findings and implementation decisions for the toolchain validation feature.

---

## 1. Tool Detection Approaches

**Decision**: Use `shutil.which()` exclusively for PATH-based detection; do not scan additional directories

**Rationale**:
- **KISS Principle**: `shutil.which()` is stdlib, cross-platform, and handles PATH correctly on all OSes
- **Operational Responsibility**: If tools aren't in PATH, the analysis host is misconfigured; validation should fail loudly
- **Consistent Behavior**: Scanning `/usr/local/bin`, `/opt/homebrew/bin`, etc. introduces platform-specific logic and makes errors harder to diagnose
- **Fail-Fast Philosophy**: FR-003 mandates immediate failure. If `shutil.which()` returns `None`, the tool is unavailable per system configuration

**Alternatives Considered**:
- **Alternative 1**: Scan common install locations (`/usr/local/bin`, `/opt/homebrew/bin`, `~/.local/bin`)
  - **Why rejected**: Adds complexity, platform-specific paths, and masks configuration issues. If a tool isn't in PATH, that's an infrastructure problem to fix, not to work around
- **Alternative 2**: Check package manager registries (e.g., `brew list`, `pip list`)
  - **Why rejected**: Package managers don't guarantee CLI availability (e.g., installed but not linked). Also requires parsing different package manager outputs

**Implementation Notes**:
```python
import shutil

def check_tool_availability(tool_name: str) -> Optional[str]:
    """Returns absolute path if tool found in PATH, None otherwise."""
    return shutil.which(tool_name)
```

- Edge case: If tool exists but has no execute permissions, `shutil.which()` returns `None` (correct behavior; we'll detect this in permission check)
- Edge case: Windows `.exe` extensions handled automatically by `shutil.which()`

---

## 2. Version Parsing Strategies

**Decision**: Use tool-specific version commands with `subprocess.run()`, parse stdout with simple string operations, fallback to "unknown" if version check fails

**Rationale**:
- **Heterogeneous Tools**: Different tools use different version flags and output formats (no universal standard)
- **Pragmatic Parsing**: Most tools output version in first line/token; simple split/regex sufficient for semver comparison
- **Graceful Degradation**: If version cannot be determined, report "unknown" and skip version validation for that tool (but warn in logs)
- **Performance**: Subprocess calls timeout at 3 seconds per tool (accommodates JVM tools like mvn/gradle)

**Version Command Registry** (tool-specific):
```python
VERSION_COMMANDS = {
    # Python ecosystem
    "ruff": ["ruff", "--version"],           # Output: "ruff 0.1.8"
    "pytest": ["pytest", "--version"],       # Output: "pytest 7.4.3"
    "pip-audit": ["pip-audit", "--version"], # Output: "pip-audit, version 2.6.1"
    "python3": ["python3", "--version"],     # Output: "Python 3.11.6"

    # JavaScript ecosystem
    "node": ["node", "--version"],           # Output: "v20.9.0"
    "npm": ["npm", "--version"],             # Output: "10.1.0"
    "eslint": ["eslint", "--version"],       # Output: "v8.52.0"

    # Go ecosystem
    "go": ["go", "version"],                 # Output: "go version go1.21.3 darwin/arm64"
    "golangci-lint": ["golangci-lint", "--version"],  # Output: "golangci-lint has version 1.55.2"
    "osv-scanner": ["osv-scanner", "--version"],      # Output: "osv-scanner v1.4.3"

    # Java ecosystem
    "mvn": ["mvn", "--version"],             # Output: "Apache Maven 3.9.5 ..."
    "gradle": ["gradle", "--version"],       # Output: "Gradle 8.4 ..."
    "java": ["java", "--version"],           # Output: "openjdk 17.0.9 ..."

    # Global tools
    "git": ["git", "--version"],             # Output: "git version 2.42.0"
    "uv": ["uv", "--version"],               # Output: "uv 0.1.6"
}
```

**Version Extraction Logic**:
```python
import re
from typing import Optional

def extract_version(stdout: str, tool_name: str) -> Optional[str]:
    """Extract semantic version from tool stdout using simple regex."""
    # Pattern matches: X.Y.Z, vX.Y.Z, X.Y, vX.Y
    # Handles common formats like "v1.2.3", "1.2.3", "version 1.2.3"
    pattern = r'v?(\d+\.\d+(?:\.\d+)?)'
    match = re.search(pattern, stdout)
    if match:
        return match.group(1)  # Return without 'v' prefix
    return None
```

**Version Comparison** (semver-aware):
```python
from packaging.version import Version  # Wait, this requires packaging library!

# CORRECTION: Use stdlib only per constitution
def compare_versions(current: str, minimum: str) -> bool:
    """Compare versions using tuple comparison (semver-compatible)."""
    def parse_version(v: str) -> tuple:
        # Handle "1.2.3" -> (1, 2, 3), "1.2" -> (1, 2, 0)
        parts = v.split('.')
        return tuple(int(p) for p in parts) + (0,) * (3 - len(parts))

    try:
        return parse_version(current) >= parse_version(minimum)
    except ValueError:
        # Non-numeric version components -> cannot compare
        return False
```

**Alternatives Considered**:
- **Alternative 1**: Use `packaging.version.Version` for robust semver parsing
  - **Why rejected**: Requires external dependency (`packaging`), violates UV-only constitution principle
- **Alternative 2**: Regex-only parsing without version comparison
  - **Why rejected**: Cannot enforce FR-015 (version validation requirement)
- **Alternative 3**: Shell parsing with `awk`/`sed`
  - **Why rejected**: Platform-specific, less portable than Python stdlib

**Implementation Notes**:
- Timeout: 3 seconds per tool (using `subprocess.run(timeout=3.0)`) to accommodate JVM startup
- Edge case: Tool exists but `--version` hangs → timeout, treat as "unknown version", skip validation
- Edge case: Version format doesn't match regex → return None, log warning, skip validation for that tool
- Edge case: Tool returns non-zero exit code for version check → capture anyway (some tools do this)

---

## 3. Error Message Internationalization

**Decision**: Hardcode Chinese messages with f-string templates now; prepare for future i18n by using message key constants

**Rationale**:
- **Current Requirement**: FR-013 specifies Chinese format ("缺少工具 {tool_name}...")
- **KISS Principle**: No translation framework needed for single language
- **Future-Ready**: Use constant keys for message templates, making future i18n straightforward
- **No External Dependencies**: Avoids `gettext`, `babel`, or other i18n libraries

**Message Template Design**:
```python
# src/metrics/toolchain_messages.py (NEW FILE)

class ValidationMessages:
    """Chinese error message templates for toolchain validation."""

    TOOL_MISSING = "缺少工具 {tool_name}。请在评分主机安装后重试（参考 {doc_url}）"

    TOOL_OUTDATED = "工具 {tool_name} 版本过旧（当前: {current_version}，最低要求: {minimum_version}）。请升级后重试（参考 {doc_url}）"

    TOOL_PERMISSION_ERROR = "工具 {tool_name} 位于 {path} 但权限不足（当前: {permissions}）。请修复权限后重试。"

    VALIDATION_FAILED_HEADER = "工具链验证失败，发现以下问题：\n"

    CATEGORY_MISSING_HEADER = "\n【缺少工具】"
    CATEGORY_OUTDATED_HEADER = "\n【版本过旧】"
    CATEGORY_PERMISSION_HEADER = "\n【权限不足】"

    @staticmethod
    def format_missing(tool_name: str, doc_url: str) -> str:
        return ValidationMessages.TOOL_MISSING.format(
            tool_name=tool_name, doc_url=doc_url
        )

    @staticmethod
    def format_outdated(tool_name: str, current: str, minimum: str, doc_url: str) -> str:
        return ValidationMessages.TOOL_OUTDATED.format(
            tool_name=tool_name, current_version=current,
            minimum_version=minimum, doc_url=doc_url
        )

    @staticmethod
    def format_permission(tool_name: str, path: str, permissions: str) -> str:
        return ValidationMessages.TOOL_PERMISSION_ERROR.format(
            tool_name=tool_name, path=path, permissions=permissions
        )
```

**Alternatives Considered**:
- **Alternative 1**: Use `gettext` for proper i18n support
  - **Why rejected**: Overkill for single language, adds external dependency
- **Alternative 2**: JSON-based message files
  - **Why rejected**: Adds file I/O, parsing overhead, and complexity without current benefit
- **Alternative 3**: Inline f-strings throughout code
  - **Why rejected**: Hard to maintain, difficult to audit message consistency

**Implementation Notes**:
- Future i18n path: Replace `ValidationMessages` constants with `gettext` calls, keep same API
- Edge case: Tool names with special characters → use `{tool_name!r}` to escape if needed
- Bilingual support later: Add `ValidationMessages_EN` class, select based on environment variable

---

## 4. Permission Detection

**Decision**: Use `os.access(path, os.X_OK)` for executability check; format permissions with `stat.filemode()` for user-friendly output

**Rationale**:
- **Simple API**: `os.access()` is stdlib, cross-platform, directly checks effective permissions
- **Correct Semantics**: `os.X_OK` checks if current user can execute (respects ACLs, SELinux, etc.)
- **Human-Readable Output**: `stat.filemode()` converts numeric permissions to Unix format (`-rw-r--r--`, `-rwxr-xr-x`)
- **FR-016 Compliance**: Provides "path + permissions" as required by spec

**Permission Check Implementation**:
```python
import os
import stat
from pathlib import Path

def check_tool_permissions(tool_path: str) -> tuple[bool, str]:
    """Check if tool is executable and return (is_executable, permission_string)."""
    path = Path(tool_path)

    # Check executability (respects ACLs, file attributes, etc.)
    is_executable = os.access(path, os.X_OK)

    # Get human-readable permission string
    try:
        mode = path.stat().st_mode
        permission_str = stat.filemode(mode)  # e.g., "-rwxr-xr-x"
    except OSError:
        permission_str = "unknown"

    return is_executable, permission_str
```

**Usage in Validation Flow**:
```python
tool_path = shutil.which("ruff")
if tool_path:
    is_exec, perms = check_tool_permissions(tool_path)
    if not is_exec:
        # Trigger FR-016 permission error
        error_msg = ValidationMessages.format_permission("ruff", tool_path, perms)
        # Error: "工具 ruff 位于 /usr/bin/ruff 但权限不足（当前: -rw-r--r--）。请修复权限后重试。"
```

**Alternatives Considered**:
- **Alternative 1**: Use `stat.S_IXUSR & st_mode` for permission bitwise check
  - **Why rejected**: Doesn't respect effective permissions (ACLs, group membership, sudo context)
- **Alternative 2**: Try executing tool with `subprocess.run()` to test executability
  - **Why rejected**: Side effects (tool might do something), slower, harder to interpret errors
- **Alternative 3**: Octal permission representation (e.g., `0o755`)
  - **Why rejected**: Less user-friendly than Unix `-rwxr-xr-x` format

**Implementation Notes**:
- Cross-platform: `os.access()` works on Windows (checks file extension registry), macOS, Linux
- Edge case: Symlink to non-executable → `os.access()` follows symlink, reports target permissions
- Edge case: Tool on NFS/CIFS mount → `os.access()` may fail; catch `OSError`, report as "permission check failed"
- Windows: `stat.filemode()` shows generic permissions (Windows doesn't use Unix permission bits)

---

## 5. Integration Point with Existing Code

**Decision**: Inject validation in `cli/main.py` immediately after argument parsing, before any repository operations

**Rationale**:
- **FR-006 Requirement**: "Validation once at analysis startup, before repository cloning"
- **Minimal Disruption**: CLI entry point is natural gate; no changes to `ToolExecutor` or tool runners needed initially
- **Clear Separation**: Validation logic encapsulated in `ToolchainManager`, CLI only calls it
- **Fail-Fast Execution**: If validation fails, program exits immediately with error code 1

**Integration Flow**:
```python
# cli/main.py (MODIFIED)

from metrics.toolchain_manager import ToolchainManager
from metrics.error_handling import ToolchainValidationError

def main():
    # 1. Parse CLI arguments (repository URL, options, etc.)
    args = parse_args()

    # 2. NEW: Toolchain validation gate
    if not args.skip_toolchain_check:  # Emergency bypass flag
        try:
            # Detect language early (lightweight detection, no cloning)
            # Or validate all languages if --all-languages flag set
            language = detect_language_from_url(args.repo_url) or "python"

            validator = ToolchainManager()
            validator.validate_for_language(language)

            print(f"✓ 工具链验证通过 (语言: {language})")
        except ToolchainValidationError as e:
            # Print comprehensive error message (FR-017: categorized errors)
            print(f"✗ 工具链验证失败:\n{e.message}", file=sys.stderr)
            sys.exit(1)
    else:
        print("⚠ 警告: 已跳过工具链验证 (--skip-toolchain-check)", file=sys.stderr)

    # 3. Continue with existing pipeline (repository cloning, ToolExecutor, etc.)
    pipeline = AnalysisPipeline(args)
    results = pipeline.run()
    ...
```

**Existing Tool Handling Analysis**:
After reviewing `tool_executor.py:66-71`:
```python
runner_class = self.tool_runners.get(language)
if not runner_class:
    # Unknown language - create minimal metrics
    metrics.execution_metadata.errors.append(f"No tools available for language: {language}")
    metrics.execution_metadata.duration_seconds = time.time() - start_time
    return metrics
```

**Current Behavior**: `ToolExecutor` silently returns empty metrics if language unknown → **This is the silent fallback we're preventing**

**New Behavior**: `ToolchainManager` fails before `ToolExecutor` runs, preventing partial results

**Exception Hierarchy Integration**:
```python
# error_handling.py (EXISTING FILE, MODIFIED)

class CodeScoreError(Exception):
    """Base exception for code-score tool."""
    pass

class ToolchainValidationError(CodeScoreError):  # NEW
    """Raised when required tools are missing or misconfigured."""
    def __init__(self, report: ValidationReport):
        self.report = report
        self.message = report.format_error_message()
        super().__init__(self.message)
```

**Alternatives Considered**:
- **Alternative 1**: Inject validation inside `ToolExecutor.__init__()`
  - **Why rejected**: `ToolExecutor` runs after repository cloning (too late per FR-006)
- **Alternative 2**: Create new `validate-toolchain` CLI subcommand
  - **Why rejected**: Adds user friction; validation should be automatic, not opt-in
- **Alternative 3**: Validate inside each tool runner class (`PythonToolRunner`, etc.)
  - **Why rejected**: Duplicates validation logic 4 times (violates DRY), harder to maintain

**Implementation Notes**:
- Edge case: `--skip-toolchain-check` flag exists for emergency debugging (e.g., partial analysis for troubleshooting)
- Early language detection: Use lightweight heuristics (file extensions, repo name) to determine language before cloning
- If language unknown: Validate only global tools (git, uv) and warn user
- Performance: Validation runs once per CLI invocation, not per repository (batch mode TBD for future)

---

## Summary of Decisions

| Research Area | Decision | Key Principle |
|---------------|----------|---------------|
| Tool Detection | `shutil.which()` only, PATH-based | KISS, fail-fast |
| Version Parsing | Tool-specific subprocess + regex | Pragmatic, stdlib-only |
| Error Messages | Hardcoded Chinese, f-string templates | Current requirement, future-ready |
| Permission Check | `os.access(os.X_OK)` + `stat.filemode()` | Correct semantics, user-friendly |
| Integration Point | CLI entry (`main.py`) after arg parse | FR-006, minimal disruption |

**Next Steps**: Proceed to Phase 1 (Design & Contracts) with these research findings as implementation foundation.

**Constitutional Compliance**:
- ✅ UV-only: All solutions use Python stdlib (no external dependencies)
- ✅ KISS: Straightforward detection logic, no caching, no fallback chains
- ✅ Transparent: All decisions rationale documented

---
*Research completed: 2025-10-11*
*Ready for Phase 1: Data Model & Contract Design*
