# Research: Build Detection Strategies

**Feature**: Complete Build Detection Integration
**Phase**: 0 - Outline & Research
**Date**: 2025-10-09

## Overview

This document consolidates research findings for implementing build validation across Python, JavaScript/TypeScript, Java, and Go projects. The goal is to determine the best approach for detecting build tools, executing builds, and reporting results while maintaining constitutional compliance (UV-based deps, KISS principle, transparent communication).

---

## 1. Python Build Detection

### Tool Selection Research

**Decision**: Prioritize `uv build`, fallback to `python -m build`

**Rationale**:
- Constitutional requirement: UV-based dependency management (Principle I)
- `uv build` provides consistent, fast builds with built-in dependency isolation
- `python -m build` as fallback ensures compatibility with non-UV projects
- Both tools support PEP 517/518 build backends (setuptools, flit, poetry)

**Alternatives Considered**:
- `setuptools`: Direct usage deprecated, modern projects use build frontends
- `pip install .`: Not a proper build tool, doesn't produce dist artifacts
- `poetry build`: Too opinionated, conflicts with UV-first principle

### Build Configuration Detection

**Check for presence of** (in order of preference):
1. `pyproject.toml` with `[build-system]` section (modern, PEP 518)
2. `setup.py` (legacy but still valid)
3. `setup.cfg` with `[metadata]` section (declarative setuptools)

**Validation Logic**:
```python
def has_python_build_config(repo_path: Path) -> bool:
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        # Parse pyproject.toml and check for [build-system]
        return True
    return (repo_path / "setup.py").exists() or (repo_path / "setup.cfg").exists()
```

### Build Execution Strategy

**Primary approach** (`uv build`):
```bash
cd {repo_path}
uv build --no-isolation  # Skip venv creation for speed
# Returns 0 on success, non-zero on failure
```

**Fallback approach** (`python -m build`):
```bash
cd {repo_path}
python3 -m build --no-isolation
# Check exit code
```

**Tool availability check**:
- `uv`: Check `which uv` or `uv --version`
- `build`: Check `python3 -c "import build"` or `which python`

### Error Cases

1. **Missing build backend**: pyproject.toml exists but no `[build-system]`
   - Action: Return `build_success=null`, error_message="Build backend not configured"

2. **Invalid configuration**: Syntax errors in setup.py or pyproject.toml
   - Action: Return `build_success=false`, capture stderr as error_message

3. **Tool unavailable**: Neither `uv` nor `python -m build` available
   - Action: Return `build_success=null`, tool_used="none"

4. **Build timeout**: Build exceeds 120-second limit
   - Action: Return `build_success=false`, error_message="Build timed out"

---

## 2. JavaScript/TypeScript Build Detection

### Tool Selection Research

**Decision**: Check `package.json` for `scripts.build`, prefer `npm run build`, fallback to `yarn build`

**Rationale**:
- JavaScript ecosystem standardizes on package.json scripts
- `npm` is ubiquitous (bundled with Node.js)
- `yarn` as fallback for projects explicitly using yarn.lock
- Build scripts abstract underlying bundler (webpack, vite, esbuild, tsc, etc.)

**Alternatives Considered**:
- Direct bundler execution (webpack, rollup, etc.): Too tool-specific, fragile
- `npm install && npm run build`: Install step too slow, out of scope
- TypeScript `tsc` only: Many projects use bundlers beyond TypeScript compilation

### Build Configuration Detection

**Check for presence of**:
1. `package.json` with `scripts.build` entry (standard)
2. `yarn.lock` presence → indicates Yarn preference
3. `tsconfig.json` → TypeScript project, may need compilation

**Validation Logic**:
```python
def has_js_build_script(repo_path: Path) -> tuple[bool, str]:
    package_json = repo_path / "package.json"
    if not package_json.exists():
        return False, "none"

    data = json.loads(package_json.read_text())
    scripts = data.get("scripts", {})

    if "build" not in scripts:
        return False, "no_build_script"

    # Determine tool preference
    tool = "yarn" if (repo_path / "yarn.lock").exists() else "npm"
    return True, tool
```

### Build Execution Strategy

**Primary approach** (`npm run build`):
```bash
cd {repo_path}
npm run build --if-present  # --if-present prevents error if no build script
# Exit code 0 = success
```

**Fallback approach** (`yarn build`):
```bash
cd {repo_path}
yarn build
# Exit code 0 = success
```

**Tool availability check**:
- `npm`: Check `which npm` or `npm --version`
- `yarn`: Check `which yarn` or `yarn --version`

### Error Cases

1. **No build script**: package.json exists but no `scripts.build`
   - Action: Return `build_success=null`, error_message="No build script defined"

2. **Build failure**: Script exits with non-zero code
   - Action: Return `build_success=false`, capture stderr (first 1000 chars)

3. **Tool unavailable**: Neither npm nor yarn available
   - Action: Return `build_success=null`, tool_used="none"

4. **Missing dependencies**: node_modules/ doesn't exist
   - Action: Return `build_success=false`, error_message="Dependencies not installed"

---

## 3. Go Build Detection

### Existing Implementation Analysis

**Current state**: `GolangToolRunner` already has build capability (not integrated to metrics)

**Existing code** (from golang_tools.py lines ~105-140):
```python
def run_build(self, repo_path: str) -> dict[str, Any]:
    """Run Go build validation."""
    result = {
        "success": None,
        "tool_used": "go",
        "execution_time_seconds": 0.0,
        "error_message": None,
        "exit_code": None
    }

    if not self._has_go_module(repo_path):
        result["tool_used"] = "none"
        result["error_message"] = "No go.mod file found"
        return result

    # Existing build logic...
```

**Decision**: Wire existing `run_build()` method to `MetricsCollection` output

**Rationale**:
- Implementation already exists and follows KISS principle
- Uses `go build ./...` to build all packages
- Properly handles go.mod detection
- Returns structured result matching our schema

**Required changes**:
- Connect `GolangToolRunner.run_build()` to `ToolExecutor.execute_tools()`
- Map result to `CodeQualityMetrics.build_success` field
- No algorithmic changes to existing build logic

### Build Configuration Detection

**Check for presence of**:
- `go.mod` file (Go modules standard, required since Go 1.16)

**Validation Logic** (existing):
```python
def _has_go_module(self, repo_path: str) -> bool:
    return Path(repo_path, "go.mod").exists()
```

### Build Execution Strategy (existing)

**Approach**:
```bash
cd {repo_path}
go build ./...
# Returns 0 on success, non-zero on compilation errors
```

**Tool availability check** (existing):
```python
self._check_tool_available("go")  # Checks `which go`
```

### Error Cases (already handled)

1. **No go.mod**: Return `success=null`, tool_used="none"
2. **Compilation errors**: Return `success=false`, capture stderr
3. **Go unavailable**: Return `success=null`, tool_used="none"
4. **Build timeout**: Handled by subprocess timeout

---

## 4. Java Build Detection

### Existing Implementation Analysis

**Current state**: `JavaToolRunner` has build methods for Maven/Gradle (not integrated to metrics)

**Existing patterns** (from java_tools.py):
- `_has_maven()`: Checks for `pom.xml`
- `_has_gradle()`: Checks for `build.gradle` or `build.gradle.kts`
- Build logic likely exists but needs extraction/integration

**Decision**: Extract and wire build validation logic to metrics output

**Rationale**:
- Maven (`mvn compile`) and Gradle (`gradle compileJava`) are standard build tools
- Project already has detection logic for Maven/Gradle
- Compilation is language-agnostic (Java, Kotlin, Scala all use same build tools)

**Required changes**:
- Create/enhance `run_build()` method in `JavaToolRunner`
- Implement tool preference: Maven if pom.xml, Gradle if build.gradle
- Wire result to `ToolExecutor` and `MetricsCollection`

### Build Configuration Detection

**Check for presence of** (in order of preference):
1. `pom.xml` → Maven project
2. `build.gradle` or `build.gradle.kts` → Gradle project

**Validation Logic**:
```python
def has_java_build_config(repo_path: Path) -> tuple[bool, str]:
    if (repo_path / "pom.xml").exists():
        return True, "maven"
    if (repo_path / "build.gradle").exists() or (repo_path / "build.gradle.kts").exists():
        return True, "gradle"
    return False, "none"
```

### Build Execution Strategy

**Maven approach**:
```bash
cd {repo_path}
mvn compile -q -DskipTests  # -q=quiet, skip tests for speed
# Exit code 0 = success
```

**Gradle approach**:
```bash
cd {repo_path}
gradle compileJava --console=plain -q
# Exit code 0 = success
```

**Tool availability check**:
- `mvn`: Check `which mvn` or `mvn --version`
- `gradle`: Check `which gradle` or `gradle --version`

### Error Cases

1. **No build file**: Neither pom.xml nor build.gradle exists
   - Action: Return `build_success=null`, error_message="No Maven/Gradle configuration"

2. **Compilation errors**: Non-zero exit code
   - Action: Return `build_success=false`, capture stderr

3. **Tool unavailable**: Maven/Gradle not in PATH
   - Action: Return `build_success=null`, tool_used="none"

4. **Invalid configuration**: Malformed pom.xml or build.gradle
   - Action: Return `build_success=false`, error_message from tool output

---

## 5. Build Result Schema Design

### Research: Existing Schema Structure

**Current `MetricsCollection` structure** (from src/metrics/models/metrics_collection.py):
```python
class MetricsCollection:
    repository_id: str
    collection_timestamp: datetime
    code_quality: CodeQualityMetrics
    testing: TestingMetrics
    documentation: DocumentationMetrics
    execution_metadata: ExecutionMetadata
```

**Current `CodeQualityMetrics` structure**:
```python
class CodeQualityMetrics:
    lint_results: LintResult
    build_success: bool | None = None  # Currently always None
    security_issues: List[SecurityIssue]
    dependency_audit: DependencyAudit
```

### Decision: Extend CodeQualityMetrics with structured build data

**Rationale**:
- `build_success` field already exists but unused (schema-compatible)
- Add `build_details` for diagnostic information
- Maintain backward compatibility (defaults to None)
- Follow existing pattern (lint_results, dependency_audit have structured sub-objects)

**Proposed Schema Extension**:
```python
class BuildValidationResult(BaseModel):
    """Structured build validation result."""
    success: bool | None  # True=pass, False=fail, None=unavailable
    tool_used: str  # "uv", "npm", "go", "mvn", "gradle", "none"
    execution_time_seconds: float
    error_message: str | None = None  # Truncated to 1000 chars
    exit_code: int | None = None

    @validator("error_message")
    def truncate_error_message(cls, v):
        if v and len(v) > 1000:
            return v[:997] + "..."
        return v

class CodeQualityMetrics(BaseModel):
    # ... existing fields ...
    build_success: bool | None = None  # Exposed in submission.json
    build_details: BuildValidationResult | None = None  # Detailed diagnostics
```

### Backward Compatibility

**Existing behavior**: `build_success` is always `None`
**New behavior**: `build_success` populated with `True`/`False`/`None`
**Breaking change**: No (None is still valid value)
**Schema version**: No bump required (additive change)

### Output Mapping

**In `submission.json`**:
```json
{
  "metrics": {
    "code_quality": {
      "build_success": true,  // Simple boolean for checklist evaluation
      "build_details": {       // Detailed diagnostics (optional)
        "tool_used": "uv",
        "execution_time_seconds": 3.14,
        "exit_code": 0
      }
    }
  }
}
```

**In `score_input.json`** (for checklist evaluation):
```json
{
  "metrics": {
    "code_quality": {
      "build_success": true  // Only the boolean is needed for scoring
    }
  }
}
```

---

## 6. Timeout and Performance Optimization

### Current Timeout Strategy Analysis

**From `tool_executor.py` lines 22-30**:
- Overall pipeline timeout: 300 seconds (5 minutes)
- Individual tool timeout: `min(timeout_seconds // 3, 120)` = 120 seconds max
- Parallel execution: ThreadPoolExecutor with max_workers=3

**Decision**: Add build validation to parallel_tasks with 120-second timeout

**Rationale**:
- Build validation is independent of other tools (can run in parallel)
- 120-second limit prevents hanging on slow/broken builds
- Matches existing tool timeout pattern (linting, security audit)
- Graceful cancellation if overall pipeline times out

### Performance Optimization Strategy

**Build Speed Optimizations**:
1. **Python**: Use `--no-isolation` flag (skip venv creation)
2. **JavaScript**: Skip dependency installation (assume pre-installed or fail gracefully)
3. **Go**: Use `go build ./...` (incremental compilation, module caching)
4. **Java**: Use `-q` (quiet mode), `-DskipTests` (skip test compilation)

**Timeout Handling**:
```python
# In tool executor parallel_tasks
parallel_tasks.extend([
    ("linting", self._run_linting),
    ("security_audit", self._run_security_audit),
    ("build_validation", self._run_build_validation),  # NEW
])
```

**Cancellation Strategy** (existing):
- If overall timeout exceeded, cancel remaining futures
- Each tool runner handles `subprocess.TimeoutExpired` exception
- Return partial results with timeout error message

### Validation Across Test Repositories

**Plan**:
- Test against 20+ repositories (5 per language)
- Measure build duration distribution
- Target: 99% complete within 120-second limit
- Adjust timeout if needed based on real-world data

**Test Repository Selection**:
- Python: Small libraries (<100 modules), medium frameworks (100-500 modules)
- JavaScript: Simple React apps, complex Next.js projects
- Go: CLI tools, web servers with many dependencies
- Java: Spring Boot applications, Android libraries

---

## 7. Error Handling Patterns

### Constitutional Compliance: Fail-Fast Error Handling

**Principle II: KISS - Fail Fast**:
- Throw exceptions immediately on critical errors
- No silent failures or error suppression
- Use specific exception types
- Include meaningful error messages with context

### Error Classification

**Critical Errors** (throw exceptions):
- Repository path doesn't exist: `FileNotFoundError`
- Invalid JSON in package.json: `json.JSONDecodeError`
- Subprocess execution fails unexpectedly: `subprocess.SubprocessError`

**Expected Failures** (return structured error):
- Build tool unavailable: `build_success=null`, tool_used="none"
- Build fails: `build_success=false`, capture stderr
- No build configuration: `build_success=null`, error_message="No build config"
- Timeout: `build_success=false`, error_message="Build timed out"

### Error Message Standards

**Requirements** (from NFR-002):
- Truncate to 1000 characters
- Preserve diagnostic value (first 997 chars + "...")
- Include tool name, exit code, and stderr excerpt

**Example**:
```python
error_message = (
    f"{tool_name} failed with exit code {exit_code}: "
    f"{stderr[:900]}..."  # Leave room for prefix
)
```

---

## 8. Alternative Approaches Rejected

### Rejected: Build Artifact Collection
**Reason**: Out of scope (NFR-003: no repository modification)
**Alternative**: Only validate build succeeds, don't collect dist/ or build/ artifacts

### Rejected: Dependency Installation Before Build
**Reason**: Too slow, increases timeout risk
**Alternative**: Assume dependencies pre-installed or fail gracefully with clear error

### Rejected: Multi-stage Build Validation
**Reason**: Over-engineering, violates KISS principle
**Alternative**: Single-pass build validation (compile only, skip packaging/testing)

### Rejected: Build Cache Management
**Reason**: Premature optimization, adds complexity
**Alternative**: Rely on tools' built-in caching (Go modules, npm cache, Maven local repo)

### Rejected: Custom Build System Support
**Reason**: Scope creep, too many edge cases
**Alternative**: Support only standard ecosystem tools (uv/build, npm/yarn, mvn/gradle, go)

---

## 9. Integration Points

### Tool Executor Changes

**Add to `ToolExecutor.execute_tools()` parallel_tasks**:
```python
parallel_tasks.extend([
    ("linting", self._run_linting),
    ("security_audit", self._run_security_audit),
    ("build_validation", self._run_build_validation),  # NEW
])
```

**New method**:
```python
def _run_build_validation(self, runner: ToolRunner, repo_path: str) -> dict:
    """Execute build validation using language-specific runner."""
    if hasattr(runner, 'run_build'):
        return runner.run_build(repo_path)
    return {"success": None, "tool_used": "none", "error_message": "Build not supported"}
```

### Output Generator Changes

**Update `output_generators.py`**:
- Extract `build_success` from `MetricsCollection.code_quality.build_success`
- Include `build_details` in detailed metrics output
- Ensure `submission.json` schema includes build_success field

### Data Model Changes

**Files to modify**:
1. `src/metrics/models/metrics_collection.py`: Add `BuildValidationResult` model
2. `src/metrics/models/metrics_collection.py`: Update `CodeQualityMetrics` with build fields
3. No schema version bump (additive change, backward compatible)

---

## 10. Summary of Decisions

| Language | Primary Tool | Fallback Tool | Config Detection | Execution Command |
|----------|--------------|---------------|------------------|-------------------|
| Python | `uv build` | `python -m build` | pyproject.toml, setup.py | `uv build --no-isolation` |
| JavaScript | `npm run build` | `yarn build` | package.json scripts.build | `npm run build --if-present` |
| Go | `go build` | None | go.mod | `go build ./...` |
| Java | `mvn compile` | `gradle compileJava` | pom.xml, build.gradle | `mvn compile -q -DskipTests` |

**Schema**: Extend `CodeQualityMetrics` with `build_success: bool | None` and `build_details: BuildValidationResult`

**Timeout**: 120 seconds per build, parallel execution with other tools

**Error Handling**: Fail-fast for critical errors, structured error results for expected failures

**Constitutional Compliance**:
- ✅ UV-based dependency management: `uv build` prioritized for Python
- ✅ KISS principle: Simple subprocess calls, no complex frameworks
- ✅ Transparent communication: Detailed error messages, clear logging

---

## Next Steps (Phase 1)

1. Create `data-model.md` with BuildValidationResult Pydantic model
2. Generate `/contracts/build_result_schema.json` JSON schema
3. Write failing contract test in `tests/contract/test_build_schema.py`
4. Create `quickstart.md` with manual validation procedures
5. Update `AGENTS.md` with build detection context

**Gate**: All research complete, no NEEDS CLARIFICATION remaining ✅
