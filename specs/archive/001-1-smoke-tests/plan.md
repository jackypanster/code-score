
# Implementation Plan: End-to-End Smoke Test Suite

**Branch**: `001-1-smoke-tests` | **Date**: 2025-09-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/user/workspace/code-score/specs/001-1-smoke-tests/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Create a lightweight smoke test script that validates the complete code analysis pipeline by executing the full workflow against a known repository and verifying all expected output files are generated correctly. This provides quick system health validation for development teams before releases or after making changes.

## Technical Context
**Language/Version**: Python 3.11+ (using UV for dependency management)
**Primary Dependencies**: pytest (testing), subprocess (process execution), pathlib (file operations)
**Storage**: File system (verifying output files: submission.json, score_input.json, evaluation_report.md)
**Testing**: pytest framework with smoke test module in tests/smoke/
**Target Platform**: Cross-platform (Linux, macOS, Windows) where existing code-score toolchain runs
**Project Type**: single (smoke test module within existing repository structure)
**Performance Goals**: Complete full pipeline smoke test within 5 minutes maximum
**Constraints**: Must use existing scripts/run_metrics.sh interface, no external dependencies beyond current toolchain
**Scale/Scope**: Single test script validating end-to-end pipeline with known test repository

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. UV-Based Dependency Management ✅
- **Compliance**: PASS - No new Python dependencies required for smoke test
- **Implementation**: Uses existing pytest framework managed via UV
- **Note**: Smoke test leverages subprocess to call existing scripts/run_metrics.sh

### II. KISS Principle (Keep It Simple, Stupid) ✅
- **Compliance**: PASS - Extremely simple two-step process
- **Implementation**:
  1. Execute subprocess call to run_metrics.sh
  2. Assert expected output files exist
- **Error Handling**: Immediate failure with descriptive messages if pipeline fails or files missing

### III. Transparent Change Communication ✅
- **Compliance**: PASS - Adding new smoke test capability
- **Documentation**: Clear test purpose, execution method, and expected outcomes
- **Rationale**: Validates system health for development workflow reliability

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
tests/
├── smoke/                   # New smoke test directory
│   ├── __init__.py         # Python package marker
│   └── test_full_pipeline.py  # Main smoke test module
├── contract/               # Existing contract tests
├── integration/            # Existing integration tests
└── unit/                   # Existing unit tests

scripts/
└── run_metrics.sh          # Existing pipeline script (used by smoke test)

output/                     # Expected output directory
├── submission.json         # Metrics collection output (verified by smoke test)
├── score_input.json       # Checklist evaluation output (verified by smoke test)
└── evaluation_report.md   # Human-readable report (verified by smoke test)
```

**Structure Decision**: Single project structure with new smoke test module added to existing tests/ directory. The smoke test leverages the existing pipeline infrastructure (scripts/run_metrics.sh) and validates the standard output artifacts.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Contract test validation → contract test task [P]
- Smoke test module creation → implementation task
- File validation logic → utility task
- Integration with pytest → configuration task

**Specific Task Categories**:
1. **Directory Setup**: Create tests/smoke/ directory structure
2. **Contract Tests**: Implement contract validation tests (can fail initially)
3. **Core Implementation**: Create test_full_pipeline.py module
4. **Validation Logic**: Implement output file checking utilities
5. **Integration**: Ensure pytest discovery and execution works
6. **Documentation**: Verify quickstart guide accuracy

**Ordering Strategy**:
- TDD order: Contract tests before implementation
- Structure order: Directory setup → contract tests → implementation → validation
- Mark [P] for parallel execution where tasks are independent
- Sequential dependencies: directory setup must complete before other tasks

**Estimated Output**: 8-12 numbered, ordered tasks in tasks.md

**Key Implementation Tasks**:
- Create tests/smoke/__init__.py
- Implement test_full_pipeline.py with subprocess execution
- Add output file validation functions
- Create helper utilities for error handling
- Integrate with existing pytest configuration

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
