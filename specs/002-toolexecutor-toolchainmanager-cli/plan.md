
# Implementation Plan: Unified Toolchain Health Check Layer

**Branch**: `002-toolexecutor-toolchainmanager-cli` | **Date**: 2025-10-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-toolexecutor-toolchainmanager-cli/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → SUCCESS: Loaded spec.md with 17 functional requirements
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type: Single project (Python metrics collection tool)
   → Set Structure Decision: Single project with src/ and tests/ layout
3. Fill the Constitution Check section
   → SUCCESS: All constitutional principles align with feature design
4. Evaluate Constitution Check section
   → PASS: No violations detected
   → Update Progress Tracking: Initial Constitution Check ✓
5. Execute Phase 0 → research.md
   → All clarifications resolved (5/5 from spec)
   → Research tool detection patterns, version parsing strategies
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, AGENTS.md
   → SUCCESS: All design artifacts generated
7. Re-evaluate Constitution Check
   → PASS: Design adheres to KISS principle and fail-fast patterns
   → Update Progress Tracking: Post-Design Constitution Check ✓
8. Plan Phase 2 → Describe task generation approach
   → SUCCESS: Task planning strategy documented
9. STOP - Ready for /tasks command
```

## Summary

Implement a **unified toolchain health check layer** that validates all required analysis tools (linters, testers, security scanners) are present and correctly versioned before any repository analysis begins. The system will use a hardcoded tool registry organized by programming language (Global, Python, JavaScript/TypeScript, Java, Go) and fail immediately with detailed, categorized error messages if any tool is missing, outdated, or has permission issues. This eliminates silent fallbacks and partial analysis results that cause score instability.

**Technical Approach**: Create a `ToolchainManager` class that executes at CLI startup (before `ToolExecutor`), uses `shutil.which()` for tool detection and subprocess calls for version checking, maintains a static tool registry with minimum version requirements, and collects all validation errors for comprehensive reporting grouped by category (missing/outdated/permission).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- Standard library: `shutil`, `subprocess`, `pathlib`, `dataclasses`
- Existing: `src/metrics/error_handling.py` (custom exceptions)
- New dependency: None (pure Python solution using stdlib)

**Storage**: Configuration stored as Python constants (tool registry with versions/URLs)
**Testing**: pytest with contract tests (schema validation), unit tests (tool detection logic), integration tests (full validation workflow)
**Target Platform**: Linux server, macOS development (analysis host environments)
**Project Type**: Single project (metrics collection tool)

**Performance Goals**:
- Validation completes in <3 seconds for all 4 languages
- Tool detection timeout: 500ms per tool maximum
- Version parsing must handle common formats (semver, date-based)

**Constraints**:
- Must execute before any repository cloning (startup gate)
- No external API calls or network dependencies
- Error messages must be bilingual-ready (current: Chinese format)
- Cannot modify existing tool runner classes initially (integration point at CLI level)

**Scale/Scope**:
- 4 supported languages: Python, JavaScript/TypeScript, Java, Go
- ~15-20 tools total across all languages
- Global tools (git, uv, curl/tar) checked for all analyses

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### UV-Based Dependency Management ✓
**Status**: PASS - No new external dependencies required; uses Python standard library (`shutil`, `subprocess`)

**Rationale**: This feature uses only Python 3.11+ standard library modules. All tool detection happens via `shutil.which()` and `subprocess.run()`, both stdlib functions. No pip/conda packages needed.

### KISS Principle ✓
**Status**: PASS - Simple fail-fast validation with minimal abstractions

**Design Approach**:
- Single `ToolchainManager` class with straightforward detection logic
- Tool registry as simple dataclasses/dictionaries (no ORM, no database)
- Immediate exception throwing on any validation failure (no recovery attempts)
- Direct `shutil.which()` calls without caching or complex fallback chains
- Version parsing uses simple string splitting (no regex unless absolutely necessary)

**Fail-Fast Pattern**: FR-003, FR-008, FR-016 all mandate immediate failure. No graceful degradation, no partial execution, no silent fallbacks.

### Transparent Change Communication ✓
**Status**: PASS - All decisions documented in this plan and will be reflected in commit messages

**Documentation Strategy**:
- This plan documents WHY we need centralized validation (score stability)
- research.md will explain tool detection approach choices
- data-model.md will clarify tool registry structure rationale
- Commits will follow format: "feat: add toolchain validation - prevents partial analysis (FR-003)"

## Project Structure

### Documentation (this feature)
```
specs/002-toolexecutor-toolchainmanager-cli/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output - tool detection patterns research
├── data-model.md        # Phase 1 output - ToolRequirement, ValidationResult models
├── quickstart.md        # Phase 1 output - validation workflow walkthrough
├── contracts/           # Phase 1 output - JSON schemas for validation models
│   ├── tool_requirement_schema.json
│   ├── validation_result_schema.json
│   └── validation_report_schema.json
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

```
src/
├── metrics/
│   ├── toolchain_manager.py         # NEW: Main validation orchestrator
│   ├── models/
│   │   ├── tool_requirement.py      # NEW: Tool registry data model
│   │   ├── validation_result.py     # NEW: Single tool validation outcome
│   │   └── validation_report.py     # NEW: Comprehensive validation report
│   ├── tool_registry.py             # NEW: Hardcoded tool definitions by language
│   ├── tool_detector.py             # NEW: shutil.which + version parsing logic
│   ├── tool_executor.py             # MODIFIED: Kept for reference (integration point)
│   └── error_handling.py            # MODIFIED: Add ToolchainValidationError
├── cli/
│   └── main.py                      # MODIFIED: Call ToolchainManager before analysis

tests/
├── contract/
│   ├── test_tool_requirement_schema.py    # NEW: JSON schema validation
│   ├── test_validation_result_schema.py   # NEW: JSON schema validation
│   └── test_validation_report_schema.py   # NEW: JSON schema validation
├── unit/
│   ├── test_toolchain_manager.py          # NEW: Validation orchestration logic
│   ├── test_tool_detector.py              # NEW: Tool detection + version parsing
│   └── test_tool_registry.py              # NEW: Tool definitions structure
├── integration/
│   └── test_full_toolchain_validation.py  # NEW: End-to-end validation workflow
└── smoke/
    └── test_cli_with_toolchain_gate.py    # NEW: CLI startup with validation gate
```

**Structure Decision**: Single project layout (existing `src/` and `tests/` structure). This feature adds a new validation layer at the CLI entry point, integrating with existing `ToolExecutor` but executing before it. New files are organized under `src/metrics/` to colocate with existing tool execution logic, following the established pattern of `tool_executor.py` and `tool_runners/`.

## Phase 0: Outline & Research

**Objective**: Resolve tool detection implementation details and version parsing strategies

### Research Tasks

1. **Tool Detection Approaches**
   - Research: How to reliably detect CLI tool availability using `shutil.which()`
   - Research: Fallback strategies when tool not in PATH (e.g., checking common install locations)
   - Research: Handling tools installed via different package managers (brew, apt, pip, npm -g)
   - Decision needed: Do we check only PATH, or also scan `/usr/local/bin`, `/opt/homebrew/bin`, etc.?

2. **Version Parsing Strategies**
   - Research: Common version flag patterns (`--version`, `-v`, `version`, `-V`)
   - Research: Version output formats (semver, date-based, commit hash)
   - Research: Specific version commands for required tools:
     - Python tools: `ruff --version`, `pytest --version`, `pip-audit --version`
     - JS tools: `npm --version`, `eslint --version`, `node --version`
     - Go tools: `go version`, `golangci-lint --version`, `osv-scanner --version`
     - Java tools: `mvn --version`, `gradle --version`, `java --version`
   - Decision needed: How to handle tools that don't support version checking?

3. **Error Message Internationalization**
   - Research: Current project's i18n approach (if any)
   - Research: Template string format for bilingual support
   - Decision needed: Hardcode Chinese messages now, or prepare for future localization?

4. **Permission Detection**
   - Research: Using `os.access(path, os.X_OK)` vs `stat.S_IXUSR` for executability check
   - Research: Cross-platform permission representation (Unix vs Windows)
   - Decision needed: Report octal permissions (`-rw-r--r--`) or simplified message?

5. **Integration Point with Existing Code**
   - Research: Where in CLI flow to inject validation (before arg parsing, after, or in main pipeline)
   - Research: How `ToolExecutor` currently handles missing tools (to understand what we're replacing)
   - Research: Existing exception hierarchy in `error_handling.py`
   - Decision needed: Modify `cli/main.py` entry point or create new validation CLI command?

### Consolidation Format (research.md)

Each research item will be documented as:
```markdown
## [Decision Area]

**Decision**: [chosen approach]

**Rationale**: [why this approach was selected]

**Alternatives Considered**:
- [Alternative 1]: [why rejected]
- [Alternative 2]: [why rejected]

**Implementation Notes**: [any caveats or edge cases]
```

**Output**: `research.md` with all 5 research areas resolved and actionable implementation decisions

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

### 1. Data Model Design → `data-model.md`

Extract entities from spec (FR-014, FR-015, Key Entities section):

**ToolRequirement** (spec line 148):
```python
@dataclass
class ToolRequirement:
    name: str                          # e.g., "ruff", "npm", "go"
    language: str                      # "python" | "javascript" | "java" | "go" | "global"
    category: str                      # "lint" | "test" | "security" | "build"
    doc_url: str                       # Official documentation URL
    min_version: Optional[str] = None  # e.g., "8.0.0" for npm, None if no requirement
    version_command: str = "--version" # Command flag to get version
```

**ValidationResult** (spec line 150):
```python
@dataclass
class ValidationResult:
    tool_name: str
    found: bool
    path: Optional[str] = None         # Where tool was found (if found)
    version: Optional[str] = None      # Detected version (if checkable)
    version_ok: bool = True            # Whether version meets minimum
    permissions: Optional[str] = None  # File permissions (if permission error)
    error_category: Optional[str] = None  # "missing" | "outdated" | "permission" | "other"
    error_details: Optional[str] = None   # Specific error message
```

**ValidationReport** (spec line 154):
```python
@dataclass
class ValidationReport:
    passed: bool
    language: str
    checked_tools: List[str]
    errors_by_category: Dict[str, List[ValidationResult]]  # Keyed by error_category
    timestamp: datetime

    def format_error_message(self) -> str:
        """Generate Chinese error message grouped by category per FR-013, FR-017"""
```

**Validation Rules** (from functional requirements):
- FR-012: All tools strictly required (no optional flag)
- FR-015: Version comparison logic (semver-aware)
- FR-016: Permission checking via `os.access()`
- FR-017: Error collection and categorization

**State Transitions**: N/A (validation is stateless, happens once at startup)

### 2. API Contracts → `/contracts/`

Since this is an internal validation layer (not a REST API), contracts focus on **data schemas** and **exception contracts**:

**contracts/tool_requirement_schema.json**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "language", "category", "doc_url"],
  "properties": {
    "name": {"type": "string", "minLength": 1},
    "language": {"type": "string", "enum": ["python", "javascript", "typescript", "java", "go", "global"]},
    "category": {"type": "string", "enum": ["lint", "test", "security", "build"]},
    "doc_url": {"type": "string", "format": "uri"},
    "min_version": {"type": ["string", "null"]},
    "version_command": {"type": "string", "default": "--version"}
  }
}
```

**contracts/validation_result_schema.json**: Schema for single tool validation outcome
**contracts/validation_report_schema.json**: Schema for comprehensive report structure

**Exception Contract** (to be added to `error_handling.py`):
```python
class ToolchainValidationError(Exception):
    """Raised when toolchain validation fails.

    Attributes:
        report: ValidationReport with categorized errors
        message: Formatted Chinese error message
    """
    def __init__(self, report: ValidationReport):
        self.report = report
        self.message = report.format_error_message()
        super().__init__(self.message)
```

### 3. Contract Tests → `tests/contract/`

**test_tool_requirement_schema.py**:
```python
def test_tool_requirement_schema_valid():
    """ToolRequirement instances must match JSON schema"""
    tool = ToolRequirement(name="ruff", language="python", category="lint", doc_url="https://docs.astral.sh/ruff")
    assert validate_against_schema(tool, "tool_requirement_schema.json")

def test_tool_requirement_missing_name_invalid():
    """Schema must reject tools without name"""
    invalid_tool = {"language": "python", "category": "lint"}
    with pytest.raises(ValidationError):
        validate_against_schema(invalid_tool, "tool_requirement_schema.json")
```

**test_validation_report_schema.py**: Ensure error categorization structure matches schema
**test_toolchain_manager_integration.py**: End-to-end validation flow contract test

### 4. Integration Test Scenarios → `tests/integration/`

Map from acceptance scenarios (spec lines 84-98):

**test_full_toolchain_validation.py**:
```python
def test_all_tools_present_passes_validation():
    """Scenario 1: All required tools installed → validation passes"""
    # Given: Mock shutil.which to return paths for all tools
    # When: ToolchainManager.validate(language="python")
    # Then: report.passed == True

def test_missing_tool_fails_with_chinese_message():
    """Scenario 2: Missing ruff → detailed error message"""
    # Given: Mock shutil.which to return None for "ruff"
    # When: ToolchainManager.validate(language="python")
    # Then: ToolchainValidationError raised with "缺少工具 ruff。请在评分主机安装后重试（参考 ...）"

def test_outdated_version_fails_with_comparison():
    """Scenario 6: npm 7.5.0 vs required 8.0.0"""
    # Given: Mock subprocess to return version "7.5.0"
    # When: Validate npm tool
    # Then: Error message shows current vs required version

def test_permission_error_shows_path_and_permissions():
    """Scenario 7: Tool exists but not executable"""
    # Given: Mock os.access to return False for execute permission
    # When: Validate tool
    # Then: Error shows path and permission flags

def test_multiple_errors_grouped_by_category():
    """Scenario 8: Missing pytest, outdated npm, permission error on ruff"""
    # Given: Three different error conditions
    # When: Validation runs
    # Then: Report groups errors into 3 categories with all details
```

### 5. Update AGENTS.md

Run the update script:
```bash
./.specify/scripts/bash/update-agent-context.sh claude
```

This will add:
- New module: `src/metrics/toolchain_manager.py` (validation orchestrator)
- New models: `ToolRequirement`, `ValidationResult`, `ValidationReport`
- Recent changes: "Added unified toolchain health check layer (002-toolexecutor-toolchainmanager-cli)"
- Keep existing context, preserve manual additions between markers

**Output**: Updated AGENTS.md at repository root (O(1) incremental update)

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load design artifacts**:
   - Parse `data-model.md` for all entities (3 dataclasses)
   - Parse `contracts/` for schema files (3 schemas)
   - Parse `research.md` for implementation decisions (5 areas)

2. **Generate contract test tasks** (from contracts/):
   - Task: "Implement contract test for ToolRequirement schema" [P]
   - Task: "Implement contract test for ValidationResult schema" [P]
   - Task: "Implement contract test for ValidationReport schema" [P]

3. **Generate model creation tasks** (from data-model.md):
   - Task: "Create ToolRequirement dataclass in src/metrics/models/" [P]
   - Task: "Create ValidationResult dataclass in src/metrics/models/" [P]
   - Task: "Create ValidationReport dataclass with format_error_message()" [P]

4. **Generate tool registry tasks** (from FR-014):
   - Task: "Define global tool requirements (git, uv, curl/tar)"
   - Task: "Define Python tool requirements (ruff, pytest, pip-audit, python3.11+)"
   - Task: "Define JavaScript/TypeScript tool requirements (node, npm≥8, eslint)"
   - Task: "Define Go tool requirements (go, golangci-lint, osv-scanner)"
   - Task: "Define Java tool requirements (mvn, gradle, java 17+)"

5. **Generate core validation logic tasks** (from FR-001 to FR-017):
   - Task: "Implement ToolDetector.check_availability() using shutil.which"
   - Task: "Implement ToolDetector.get_version() with subprocess"
   - Task: "Implement ToolDetector.compare_versions() for semver"
   - Task: "Implement ToolDetector.check_permissions() using os.access"
   - Task: "Implement ToolchainManager.validate_for_language()"
   - Task: "Implement ValidationReport.format_error_message() with Chinese template"
   - Task: "Add ToolchainValidationError to error_handling.py"

6. **Generate integration tasks** (from acceptance scenarios):
   - Task: "Integrate ToolchainManager into cli/main.py startup"
   - Task: "Add --skip-toolchain-check flag for emergency bypass (with warning)"
   - Task: "Update CLI error handling to catch ToolchainValidationError"

7. **Generate integration test tasks** (from test scenarios):
   - Task: "Write integration test: all tools present scenario"
   - Task: "Write integration test: missing tool scenario"
   - Task: "Write integration test: outdated version scenario"
   - Task: "Write integration test: permission error scenario"
   - Task: "Write integration test: multiple errors grouped scenario"

8. **Generate quickstart validation task**:
   - Task: "Execute quickstart.md walkthrough and verify validation flow"

**Ordering Strategy**:
- **TDD order**: Contract tests → Models → Implementation → Integration tests
- **Dependency order**:
  1. Models (dataclasses) - no dependencies
  2. Tool registry (depends on models)
  3. Tool detector (depends on models)
  4. Toolchain manager (depends on detector + registry)
  5. CLI integration (depends on manager)
  6. Integration tests (depends on all implementation)
- **Parallelization**: Mark `[P]` for independent tasks:
  - All 3 contract test files can run in parallel
  - All 3 model creation tasks can run in parallel
  - All 5 language tool registry tasks can run in parallel

**Estimated Output**: 30-35 numbered, ordered tasks in tasks.md

**Task Template Format** (from tasks-template.md):
```markdown
### Task N: [Description]
**Type**: [Contract Test | Model | Implementation | Integration]
**Priority**: [Critical | High | Medium]
**Parallel**: [Yes | No]
**Depends On**: [Task numbers or "None"]
**Estimated Time**: [hours]

**Acceptance Criteria**:
- [ ] [Specific testable criterion from FR-XXX]
- [ ] [Another criterion]

**Implementation Notes**:
- [Guidance from research.md or data-model.md]
```

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute ~30-35 tasks following TDD order)
**Phase 5**: Validation (run full test suite, execute quickstart.md, verify all 8 acceptance scenarios pass)

**Phase 4 Execution Notes**:
- Use `uv run pytest tests/contract/` to verify schemas before implementation
- Use `uv run pytest tests/unit/` to drive TDD for core logic
- Use `uv run pytest tests/integration/` to verify end-to-end flow
- Test manually with `./scripts/run_metrics.sh <test-repo>` to ensure startup validation works

**Phase 5 Validation Checklist**:
- [ ] All 17 functional requirements have passing tests
- [ ] All 8 acceptance scenarios validated via integration tests
- [ ] Quickstart.md executes without errors
- [ ] Performance goal met: validation completes <3 seconds
- [ ] Edge cases documented in research.md have handling code
- [ ] AGENTS.md updated with final implementation details

## Complexity Tracking

*No constitutional violations detected - this section intentionally left empty per template instructions*

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md generated
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md, AGENTS.md updated
- [x] Phase 2: Task planning complete (/plan command - approach documented above)
- [x] Phase 3: Tasks generated (/tasks command) - 32 tasks created, 18 parallel
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (no violations)
- [x] Post-Design Constitution Check: PASS (fail-fast design, no new dependencies)
- [x] All NEEDS CLARIFICATION resolved (5/5 from spec clarification session)
- [x] Complexity deviations documented (none required)

**Artifacts Generated**:
- [x] plan.md (this file)
- [x] research.md (Phase 0 - 5 implementation decisions documented)
- [x] data-model.md (Phase 1 - 4 entities with validation rules)
- [x] contracts/ (Phase 1 - 3 JSON schemas generated)
  - [x] tool_requirement_schema.json
  - [x] validation_result_schema.json
  - [x] validation_report_schema.json
- [x] quickstart.md (Phase 1 - 8 acceptance scenarios walkthrough)
- [x] CLAUDE.md updated (Phase 1 - feature context added via update-agent-context.sh)
- [x] tasks.md (Phase 3 - /tasks command) - 32 TDD tasks generated, 18 parallel-ready

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
*All phases complete - Ready for Phase 4 implementation via tasks.md*
