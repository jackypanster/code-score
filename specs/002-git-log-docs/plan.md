
# Implementation Plan: Checklist Mapping & Scoring Input MVP

**Branch**: `002-git-log-docs` | **Date**: 2025-09-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-git-log-docs/spec.md`

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
Build a checklist evaluation system that reads repository metrics from the existing submission.json format and maps them to the 11-item code quality checklist defined in ai-code-review-judgement.md. The system will generate structured score_input.json output with status evaluations (met/partial/unmet) and evidence references for each checklist item. This creates the crucial bridge between raw metrics collection (Phase 1) and LLM-powered evaluation (Phase 3), enabling automated hackathon scoring with auditability and consistency across multiple programming languages.

## Technical Context
**Language/Version**: Python 3.11+ (consistent with existing codebase)
**Primary Dependencies**: Click (CLI), jsonschema (validation), pydantic (data models), requests (for future LLM integration)
**Storage**: JSON files (submission.json input, score_input.json output), Markdown reports (output/report.md)
**Testing**: pytest (consistent with existing test framework)
**Target Platform**: Cross-platform CLI tool (Linux, macOS, Windows)
**Project Type**: single (extends existing metrics collection pipeline)
**Performance Goals**: <5 seconds evaluation for typical repositories, memory efficient for large submission files
**Constraints**: Must be fail-fast per constitution, graceful degradation when metrics incomplete, extensible for future checklist changes
**Scale/Scope**: 11 checklist items initially, support for 4 programming languages, designed for hundreds of hackathon submissions

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. UV-Based Dependency Management**: ✅ PASS
- All new dependencies will be added via `uv add` command
- No pip, conda, or other package managers will be used
- Consistent with existing project setup

**II. KISS Principle (Keep It Simple, Stupid)**: ✅ PASS
- Simple evaluation logic: read JSON → apply rules → output JSON
- Fail-fast on missing required data rather than complex error recovery
- Single responsibility modules: evaluator, mapper, output generator
- No over-engineering or premature optimization

**III. Transparent Change Communication**: ✅ PASS
- Clear commit messages explaining checklist evaluation logic
- Documentation of evaluation rules and scoring mappings
- Evidence references for auditability of scoring decisions

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
src/
├── metrics/
│   ├── checklist_evaluator.py     # New: Core evaluation logic
│   ├── scoring_mapper.py          # New: Status to score mapping
│   ├── evidence_tracker.py       # New: Evidence reference management
│   └── models/
│       ├── checklist_item.py     # New: ChecklistItem data model
│       ├── evaluation_result.py  # New: EvaluationResult container
│       └── score_input.py        # New: ScoreInput output format
├── cli/
│   └── evaluate.py               # New: CLI command for evaluation
└── output/
    ├── score_input.json          # New: Generated scoring input
    └── report.md                 # Enhanced: Append evaluation summary

tests/
├── contract/
│   └── test_score_input_schema.py # New: Output format validation
├── integration/
│   └── test_checklist_evaluation.py # New: End-to-end evaluation
└── unit/
    ├── test_checklist_evaluator.py  # New: Core logic tests
    ├── test_scoring_mapper.py       # New: Mapping logic tests
    └── test_evidence_tracker.py     # New: Evidence tracking tests
```

**Structure Decision**: Single project structure extending the existing metrics collection pipeline. New checklist evaluation components integrate with existing src/metrics/ modules while maintaining clear separation of concerns.

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
- Each contract → contract test task [P]
  - test_score_input_schema.py validates output format
  - test_checklist_mapping.py validates evaluation rules
- Each entity → model creation task [P]
  - ChecklistItem, EvaluationResult, ScoreInput Pydantic models
  - EvidenceReference, CategoryBreakdown supporting models
- Core evaluation logic tasks in dependency order:
  - ChecklistEvaluator (reads submission.json, applies rules)
  - ScoringMapper (status → score conversion)
  - EvidenceTracker (tracks evaluation reasoning)
- CLI integration task (evaluate command)
- Integration test tasks covering full workflows

**Ordering Strategy**:
- TDD order: Contract tests → Unit tests → Implementation → Integration tests
- Dependency order: Models → Core logic → CLI → Full workflow
- Mark [P] for parallel execution where files are independent
- Critical path: Models → Evaluator → Mapper → CLI → Integration

**Specific Task Categories**:
1. **Contract Tests** [P]: Schema validation, rule verification
2. **Data Models** [P]: Pydantic model creation with validation
3. **Core Logic**: Evaluation engine, mapping logic, evidence tracking
4. **CLI Interface**: Command integration with existing pipeline
5. **Integration Tests**: End-to-end workflow validation
6. **Documentation**: Update quickstart with real examples

**Estimated Output**: 22-26 numbered, ordered tasks in tasks.md

**Key Dependencies**:
- Tasks 1-5: Contract tests (parallel, no dependencies)
- Tasks 6-10: Data models (parallel, depend on contracts)
- Tasks 11-15: Core logic (sequential, depend on models)
- Tasks 16-18: CLI integration (depends on core logic)
- Tasks 19-22: Integration tests (depend on all implementation)

**Validation Criteria**:
- All contract tests pass (schema compliance)
- All unit tests pass (component functionality)
- Integration tests pass with sample data (end-to-end workflow)
- CLI produces valid score_input.json from submission.json
- Manual verification with code-walker repository

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
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
