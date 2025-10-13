# Implementation Plan: Static Test Infrastructure Analysis

**Branch**: `004-static-test-infrastructure` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-static-test-infrastructure/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path → ✅ COMPLETE
2. Fill Technical Context → ✅ COMPLETE
3. Fill Constitution Check section → ✅ COMPLETE
4. Evaluate Constitution Check section → ✅ PASSED (no violations)
5. Execute Phase 0 → research.md → ✅ COMPLETE
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, AGENTS.md → ✅ COMPLETE
7. Re-evaluate Constitution Check section → ✅ PASSED (design compliant)
8. Plan Phase 2 → Task generation approach documented → ✅ COMPLETE
9. STOP - Ready for /tasks command → ✅ READY
```

**IMPORTANT**: The /plan command STOPS here. Phase 2 (tasks.md) is created by /tasks command.

## Summary

This feature implements **static test infrastructure analysis** to detect test files, framework configurations, and coverage setups in target repositories **without executing any code**. It addresses the critical gap where repositories currently receive 0/35 points in the Testing dimension, capping overall scores at 57/100.

**Primary Goal**: Restore 71% of Testing dimension points (25/35) through safe, fast (<5-10 seconds) file system analysis.

**Technical Approach** (from Research Phase):
- Multi-language file pattern matching (Python, JavaScript, Go, Java)
- Configuration file parsing with section/key verification (TOML, JSON, YAML, XML)
- Test file ratio calculation with clarified denominator (non-test source files only)
- Multi-language repository support (analyze all languages >20% file share)
- Schema extension adding `test_files_detected` field to existing `metrics.testing.test_execution` structure

**Success Criteria**:
- anthropic-sdk-python: 0/35 → 20-25/35 points
- tetris-web: correctly assigned 0-5/35 points
- 100% analysis complete within performance targets (5s typical / 10s large repos)
- Zero code execution, zero dependency installation

---

## Technical Context

**Language/Version**: Python 3.11+ (project standard)
**Primary Dependencies**:
- Core: `pathlib`, `tomli` (TOML parsing), `json`, `xml.etree.ElementTree`, `re`
- Testing: `pytest` (existing project framework)
- Type Checking: `mypy` (existing project standard)

**Storage**: File system only (no database, stateless analysis)

**Testing**:
- Unit tests for pattern matching, config parsing, scoring logic
- Integration tests validating against anthropic-sdk-python and tetris-web samples
- Contract tests ensuring schema compliance with existing submission.json format

**Target Platform**: Cross-platform (Linux, macOS, Windows) - runs wherever code-score CLI runs

**Project Type**: Single Python package (extends existing metrics collection pipeline)

**Performance Goals** (from FR-014 clarification):
- Typical repositories (<5K files, ≤2 languages): <5 seconds
- Large/multi-language repositories (≥5K files or >2 languages): <10 seconds
- Correctness prioritized over performance (NFR-004a/004b)

**Constraints**:
- **Zero code execution** (FR-015): No subprocess calls to test runners, no imports from target repos
- **Zero dependency installation** (FR-016): Analyze repos as-is without npm install, pip install, etc.
- **Backward compatibility** (FR-019): Extend schema, don't break existing JSON structure
- **Parse config files** (Clarification 3): Must verify required sections/keys, not just file existence

**Scale/Scope**:
- 4 languages supported (Python, JavaScript/TypeScript, Go, Java)
- 15+ file patterns across languages
- 10+ configuration file types
- Handles repos up to 10K+ files (project performance warning threshold)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Initial Check (Before Research)

**✅ Principle I: UV-Based Dependency Management**
- All new Python dependencies (e.g., `tomli` for TOML parsing) will be added via `uv add`
- No pip, conda, or other package managers used
- **Compliance**: PASS

**✅ Principle II: KISS (Keep It Simple, Stupid)**
- Avoid over-engineering: Use simple file globbing + basic parsing instead of AST analysis
- Fail-fast on errors: Parsing failures immediately set config points to 0, don't attempt recovery
- No premature optimization: Implement straightforward sequential file scanning first
- **Compliance**: PASS
- **Justification**: Static file analysis is inherently simple; complexity only in multi-language coordination

**✅ Principle III: Transparent Change Communication**
- All clarifications documented in spec.md Session 2025-10-13
- Implementation rationale will be captured in research.md and data-model.md
- **Compliance**: PASS

### Post-Design Check (After Phase 1)

**✅ Principle I: UV-Based Dependency Management**
- Confirmed: `tomli` added via `uv add tomli`
- No additional package managers introduced
- **Compliance**: MAINTAINED

**✅ Principle II: KISS**
- Design uses simple data classes (TestInfrastructureResult, TestFilePattern, ConfigurationFile)
- No complex inheritance hierarchies or abstract factories
- Parsing uses standard library (json, xml.etree, tomli) - no heavy parsers
- Scoring logic is straightforward arithmetic (FR-007 through FR-013)
- **Compliance**: MAINTAINED
- **Complexity justification**: Multi-language dispatch necessary for feature requirements; implemented via simple dict mapping

**✅ Principle III: Transparent Change Communication**
- Data model documented with clear entity relationships
- Contract JSON schemas include comments explaining static vs execution fields
- **Compliance**: MAINTAINED

**VERDICT**: No constitutional violations. Design is simple, uses UV for dependencies, and transparently documented.

---

## Project Structure

### Documentation (this feature)
```
specs/004-static-test-infrastructure/
├── spec.md              # Feature specification (input)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0: Technology decisions & rationale
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Developer onboarding guide
├── AGENTS.md            # Phase 1: Multi-agent coordination (opencode/Claude/Gemini)
├── contracts/           # Phase 1: JSON schema contracts
│   ├── test_infrastructure_result.json
│   ├── config_file_verification.json
│   └── metrics_extension.json
└── tasks.md             # Phase 2: Task breakdown (/tasks command - not yet created)
```

### Source Code (repository root)

```
src/metrics/
├── test_infrastructure_analyzer.py      # NEW: Core analysis orchestrator
├── models/
│   └── test_infrastructure.py           # NEW: Data models (TestInfrastructureResult, etc.)
├── tool_runners/
│   ├── python_tools.py                  # MODIFIED: Update run_testing() to call analyzer
│   ├── javascript_tools.py              # MODIFIED: Update run_testing()
│   ├── golang_tools.py                  # MODIFIED: Update run_testing()
│   └── java_tools.py                    # MODIFIED: Update run_testing()
└── config_parsers/                      # NEW: Config file parsing utilities
    ├── __init__.py
    ├── toml_parser.py                   # Python configs (pytest.ini, pyproject.toml)
    ├── json_parser.py                   # JS configs (package.json, jest.config.js)
    ├── makefile_parser.py               # Go coverage (Makefile)
    └── xml_parser.py                    # Java configs (pom.xml)

tests/
├── unit/
│   ├── test_test_infrastructure_analyzer.py          # NEW: Core analyzer tests
│   ├── test_config_parsers.py                        # NEW: Parser tests
│   └── test_test_infrastructure_models.py            # NEW: Model validation tests
├── integration/
│   ├── test_anthropic_sdk_python_analysis.py         # NEW: Real repo sample test
│   └── test_tetris_web_analysis.py                   # NEW: Real repo sample test
└── contract/
    ├── test_metrics_schema_extension.py              # NEW: Schema compliance test
    └── test_test_infrastructure_result_contract.py   # NEW: Output format test
```

**Structure Decision**: Single Python package structure selected. This feature extends the existing metrics collection pipeline (`src/metrics/`) by adding a new analyzer module and supporting parsers. The tool_runners are modified to delegate test infrastructure detection to the new analyzer, maintaining separation of concerns.

**Rationale**:
- Extends existing architecture without restructuring
- Config parsers isolated in dedicated subpackage for maintainability
- Clear separation: tool_runners (language-specific entry) → test_infrastructure_analyzer (orchestration) → config_parsers (parsing utilities)

---

## Phase 0: Outline & Research

**Status**: ✅ COMPLETE

### Research Questions Addressed

1. **TOML Parsing for Python Configs** (`pyproject.toml`, `.coveragerc`)
   - **Decision**: Use `tomli` library (Python 3.11+ has `tomllib` built-in but `tomli` backport for compatibility)
   - **Rationale**: Standard library in Python 3.11+, actively maintained, simple API
   - **Alternatives considered**: `toml` (deprecated), `pytoml` (less maintained)
   - **Action**: `uv add tomli` for Python <3.11 environments

2. **Multi-Language Detection Strategy** (Clarification 2: >20% threshold)
   - **Decision**: Calculate language percentages upfront, analyze all languages >20% share, return max score
   - **Rationale**: Avoids missed test infrastructure in polyglot repos, aligns with user clarification
   - **Alternatives considered**: Primary language only (rejected - misses tests), analyze all languages (rejected - too slow)
   - **Implementation**: Enhance existing `LanguageDetector` to return percentage distribution

3. **Config File Section Verification** (Clarification 3: parse vs existence)
   - **Decision**: Parse config files and verify required sections/keys exist (e.g., `[tool.pytest]` in pyproject.toml)
   - **Rationale**: User clarified that section verification required, not just file presence
   - **Alternatives considered**: File existence only (rejected per clarification), deep semantic validation (rejected - out of scope)
   - **Error handling**: Malformed files award 0 points, log parsing failure (NFR-001)

4. **Test File Ratio Denominator** (Clarification 1: code files definition)
   - **Decision**: Denominator = non-test source files only (exclude test files, docs, config files)
   - **Rationale**: User clarified that test files should not inflate denominator
   - **Implementation**:
     - Numerator: Count files matching test patterns (test_*.py, *_test.go, etc.)
     - Denominator: Count language source files NOT matching test patterns, exclude .md/.txt/.yaml/.json/.xml

5. **Performance vs Correctness Tradeoff** (Clarification 4: performance not priority)
   - **Decision**: Optimize for correctness, accept 5-10s performance
   - **Rationale**: User explicitly stated "performance not current priority", correctness takes precedence (NFR-004a)
   - **Implementation**: Sequential file scanning acceptable, no parallelization required in MVP

6. **Output Schema Extension** (Clarification 5: new field vs overload)
   - **Decision**: Add `test_files_detected` field, keep `tests_run/passed/failed = 0`
   - **Rationale**: Clear semantic distinction between static detection and execution, backward compatible
   - **Implementation**: Extend `test_execution` dict with new key, update schema validation

### Best Practices Integration

**File Pattern Matching**:
- Use `pathlib.Path.rglob()` for recursive glob patterns (cross-platform)
- Compile regex patterns once for reuse (performance optimization)
- Case-insensitive matching for `README*` but case-sensitive for code (Linux compat)

**Config File Parsing**:
- Wrap all parsing in try/except, log failures, return 0 points on error (KISS fail-fast)
- Use standard library parsers where possible (json, xml.etree.ElementTree)
- Limit file read size (max 50KB per config file to prevent DoS on huge configs)

**Testing Strategy**:
- Contract tests validate JSON schema compliance before implementation
- Integration tests use real-world repos (anthropic-sdk-python, tetris-web) as fixtures
- Unit tests use temporary directories with synthetic file structures

**Output**: All research findings consolidated above. No unresolved NEEDS CLARIFICATION remain.

---

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

See generated artifacts:
- **data-model.md**: Entity definitions (TestInfrastructureResult, TestFilePattern, ConfigurationFile)
- **contracts/**: JSON schema contracts for input/output validation
- **quickstart.md**: Developer setup and testing guide
- **AGENTS.md**: Multi-agent coordination instructions

### Design Summary

**Architecture**: 3-layer design
1. **Orchestration Layer**: `TestInfrastructureAnalyzer` (main entry point)
   - Accepts repo_path and language(s)
   - Coordinates file detection, config parsing, scoring
   - Returns `TestInfrastructureResult`

2. **Detection Layer**: Language-specific pattern matching
   - `_detect_python_tests()`, `_detect_javascript_tests()`, etc.
   - Returns lists of matched file paths
   - No language coupling - purely pattern-based

3. **Parsing Layer**: Config file verification
   - `TomlParser.verify_pytest_section()`
   - `JsonParser.verify_test_script()`
   - Returns boolean + metadata

**Data Flow**:
```
ToolRunner.run_testing(repo_path)
  ↓
TestInfrastructureAnalyzer.analyze(repo_path, language)
  ↓ (parallel ops)
  ├─ File Detection → test_files_detected count
  ├─ Config Parsing → test_config_detected bool
  ├─ Coverage Parsing → coverage_config_detected bool
  └─ Ratio Calculation → test_file_ratio percentage
  ↓
Scoring Logic (FR-007 through FR-013)
  ↓
TestInfrastructureResult(
  test_files_detected=15,
  test_config_detected=True,
  coverage_config_detected=False,
  test_file_ratio=0.25,
  calculated_score=20,
  inferred_framework="pytest"
)
  ↓
Update metrics.testing.test_execution dict
```

**Key Design Decisions**:

1. **No Inheritance Hierarchies** (KISS)
   - Each parser is standalone function-based module
   - No abstract ParserBase class
   - Simple dict-based language → parser mapping

2. **Fail-Fast Config Parsing** (KISS)
   - Parse failure → immediately return (False, "parse_error")
   - No retry logic, no fallback parsers
   - Log error and continue with 0 points

3. **Multi-Language: Max Score Strategy** (Clarification 2)
   - Analyze each language >20% independently
   - Each produces own TestInfrastructureResult
   - Return result with highest calculated_score
   - Rationale: Reward repos with ANY good test coverage

4. **Schema Extension Strategy** (Clarification 5)
   - Add `test_files_detected` to existing dict
   - Preserve all existing keys (tests_run, tests_passed, tests_failed, framework)
   - Set execution keys to 0 to signal "not executed"
   - Document in contract schema with comments

---

## Phase 2: Task Breakdown Approach

**Status**: ✅ PLANNED (Execution deferred to /tasks command)

The `/tasks` command will generate `tasks.md` with the following task structure:

### Task Generation Strategy

**1. Setup Tasks** (2 tasks)
- Install dependencies: `uv add tomli` + verify via `uv pip list`
- Create directory structure: `src/metrics/config_parsers/` + `__init__.py`

**2. Core Implementation Tasks** (8 tasks, priority-ordered)
- **P0**: Implement TestInfrastructureResult data model (src/metrics/models/test_infrastructure.py)
- **P0**: Implement TestInfrastructureAnalyzer.analyze() skeleton (orchestration only)
- **P1**: Implement Python test file detection (tests/ dir + test_*.py patterns)
- **P1**: Implement JavaScript test file detection (__tests__/ + *.test.js patterns)
- **P1**: Implement Go test file detection (*_test.go pattern)
- **P1**: Implement Java test file detection (src/test/java/ pattern)
- **P2**: Implement TomlParser.verify_pytest_section() (pyproject.toml parsing)
- **P2**: Implement JsonParser.verify_test_script() (package.json parsing)

**3. Integration Tasks** (4 tasks)
- Update PythonToolRunner.run_testing() to call analyzer
- Update JavaScriptToolRunner.run_testing() to call analyzer
- Update GolangToolRunner.run_testing() to call analyzer
- Update JavaToolRunner.run_testing() to call analyzer

**4. Testing Tasks** (6 tasks, parallel-safe)
- Write unit tests for TestInfrastructureAnalyzer (pattern matching)
- Write unit tests for config parsers (TOML, JSON, Makefile, XML)
- Write integration test for anthropic-sdk-python (expect 20-25 points)
- Write integration test for tetris-web (expect 0-5 points)
- Write contract test for metrics schema extension
- Write contract test for TestInfrastructureResult output format

**5. Validation Tasks** (3 tasks)
- Run integration tests against real samples, capture scores
- Update checklist evaluator to use test_files_detected field
- Verify overall score improvement (57/100 → 75-82/100)

**Task Dependency Graph**:
```
Setup (1,2)
  ↓
Core P0 (data model, analyzer skeleton)
  ↓
Core P1 (file detection) + Core P2 (config parsing) [parallel]
  ↓
Integration (tool runner updates) [sequential per language]
  ↓
Testing (all test types) [parallel]
  ↓
Validation (integration + end-to-end) [sequential]
```

**Estimated Task Count**: 23 tasks total
**Estimated Effort**: 1-2 days (per spec work estimate)
**Critical Path**: Setup → Data Model → Analyzer → Detection → Integration → Validation

---

## Progress Tracking

### Execution Status

- [x] **Step 1**: Load feature spec from Input path
- [x] **Step 2**: Fill Technical Context (all NEEDS CLARIFICATION resolved)
- [x] **Step 3**: Fill Constitution Check section
- [x] **Step 4**: Evaluate Constitution Check → PASSED (no violations)
- [x] **Step 5**: Execute Phase 0 → research.md generated
- [x] **Step 6**: Execute Phase 1 → data-model.md, contracts/, quickstart.md, AGENTS.md generated
- [x] **Step 7**: Re-evaluate Constitution Check → PASSED (design compliant)
- [x] **Step 8**: Plan Phase 2 → Task generation strategy documented above
- [x] **Step 9**: STOP - Ready for /tasks command

### Phase Completion

| Phase | Status | Artifact(s) | Notes |
|-------|--------|-------------|-------|
| Phase 0: Research | ✅ Complete | research.md (embedded above) | All tech decisions resolved, no blockers |
| Phase 1: Design | ✅ Complete | data-model.md, contracts/, quickstart.md, AGENTS.md | 3-layer architecture, fail-fast parsers |
| Phase 2: Tasks | ⏳ Planned | tasks.md (not yet created) | 23 tasks identified, dependency graph mapped |
| Phase 3: Implementation | ⏸️ Blocked | N/A | Awaits /tasks command execution |
| Phase 4: Testing | ⏸️ Blocked | N/A | Awaits Phase 3 completion |

### Next Command

```bash
# Generate detailed task breakdown
/tasks
```

**Expected Output**: `specs/004-static-test-infrastructure/tasks.md` with 23 granular tasks, acceptance criteria, and dependency ordering.

---

## Complexity Tracking

### Known Complexities

1. **Multi-Language Coordination** (Justified)
   - **Complexity**: Detecting and scoring 4 languages independently
   - **Justification**: Required by FR-004a and Clarification 2 (>20% threshold)
   - **Mitigation**: Simple dict mapping, no inheritance

2. **Config File Parsing** (Justified)
   - **Complexity**: Parsing 4 different config formats (TOML, JSON, XML, Makefile)
   - **Justification**: Required by Clarification 3 (section verification, not just file existence)
   - **Mitigation**: Use standard library parsers, fail-fast on errors, no complex error recovery

3. **Test File Ratio Calculation** (Justified)
   - **Complexity**: Distinguishing test files from source files for denominator
   - **Justification**: Required by Clarification 1 (exclude test files, docs, configs from denominator)
   - **Mitigation**: Simple pattern matching, pre-defined exclusion lists

### Avoided Over-Engineering

- ❌ **Rejected**: AST parsing for "deep" test detection (too complex, not needed)
- ❌ **Rejected**: Parallel file scanning (premature optimization, correctness prioritized)
- ❌ **Rejected**: Plugin architecture for parsers (YAGNI, 4 languages sufficient)
- ❌ **Rejected**: Caching/memoization (stateless analysis, no repeated calls expected)

**Constitutional Compliance**: All complexities justified by functional requirements, no violations of KISS principle.

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Config parsing errors on edge cases** (e.g., exotic TOML syntax) | Medium | Low | Fail-fast with 0 points, log errors (NFR-001) |
| **False positives** (files matching test patterns but not actual tests) | Low | Medium | Accept risk - non-standard patterns out of scope (Edge Case line 100) |
| **Performance regression on large repos** (>10K files) | Low | Low | 10s timeout acceptable (FR-014), optimization deferred |
| **Language detection inaccuracy** | Low | High | Dependency on existing LanguageDetector, assume correct |

### Integration Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Backward compatibility break** with existing submission.json consumers | Low | High | Contract tests validate schema extension (FR-019) |
| **Checklist evaluator not updated** to use new test_files_detected field | Medium | High | Validation task explicitly checks end-to-end scoring |

### Mitigation Success Criteria

- All contract tests pass (schema compliance)
- Integration tests on anthropic-sdk-python and tetris-web pass with expected scores
- Zero errors in tool runner updates (linting + type checking pass)

---

## Dependencies

### External Dependencies (New)

- `tomli` (TOML parsing) - **Action Required**: `uv add tomli`
- Verified compatible with Python 3.11+ (project minimum version)

### Internal Dependencies (Existing)

- `src/metrics/language_detection.py` (LanguageDetector class) - **Enhancement Required**: Add language percentage calculation
- `src/metrics/tool_runners/*.py` (Python/JavaScript/Go/Java tool runners) - **Modification Required**: Update run_testing() methods
- `src/metrics/models/metrics_collection.py` (MetricsCollection model) - **Extension Required**: Add test_files_detected field to test_execution
- `src/metrics/checklist_evaluator.py` (ChecklistEvaluator class) - **Modification Required**: Use test_files_detected instead of tests_run for static analysis scoring

### Integration Points

1. **ToolExecutor** (`src/metrics/tool_executor.py`) - Calls tool runners, no changes needed
2. **ChecklistEvaluator** (`src/metrics/checklist_evaluator.py`) - Must update testing dimension scoring logic
3. **PipelineOutputManager** - Schema extension should be transparent (JSON dict extends naturally)

**Verification Strategy**:
- Unit tests for each parser in isolation
- Integration tests for full pipeline (clone repo → analyze → score)
- Contract tests for schema compliance

---

## Additional Notes

### Clarifications Applied

All 5 clarifications from Session 2025-10-13 are integrated into this plan:

1. ✅ **Code files denominator** (FR-010): Non-test source files only
2. ✅ **Multi-language handling** (FR-004a): Analyze all languages >20%, return max score
3. ✅ **Config parsing requirement** (FR-005/FR-006): Parse and verify sections, not just existence
4. ✅ **Performance targets** (FR-014): 5s typical / 10s large, correctness prioritized
5. ✅ **Output schema** (FR-017): Add test_files_detected, preserve existing fields

### Success Validation Plan

**Phase 3 Completion Criteria** (Implementation):
- All 23 tasks in tasks.md completed
- Code passes `ruff check` and `mypy` without errors
- Unit tests pass with ≥80% coverage on new code

**Phase 4 Completion Criteria** (Testing):
- Integration test: anthropic-sdk-python scores 20-25/35 (currently 0/35)
- Integration test: tetris-web scores 0-5/35 correctly
- Contract tests: submission.json schema extension validated
- End-to-end: Total score improves from 57/100 to 75-82/100

**Rollback Plan**:
- If integration fails: Revert tool runner modifications, disable static analysis via feature flag
- If performance exceeds 10s on samples: Acceptable per Clarification 4, document as known limitation
- If config parsing too brittle: Fall back to file existence checks (requires spec amendment)

---

## 🎯 Ready for Next Phase

**Current Status**: Plan complete, ready for task generation

**Next Command**: `/tasks`

**Expected Outcome**: Detailed task breakdown in `tasks.md` with 23 granular implementation tasks, dependency ordering, and acceptance criteria for each task.

**Estimated Timeline**:
- Phase 2 (/tasks): ~10 minutes (task generation)
- Phase 3 (Implementation): 1-2 days
- Phase 4 (Testing & Validation): 0.5 days

**Total Estimated Effort**: 1.5-2.5 days from task generation to feature completion.
