
# Implementation Plan: LLM-Generated Code Review Reports

**Branch**: `003-step-3-llm` | **Date**: 2025-09-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-step-3-llm/spec.md`

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
Add lightweight LLM-generated report generation to existing metrics + checklist evaluation pipeline. System will consume structured evaluation data (score_input.json) and produce human-readable final reports using template-based prompt generation and external LLM APIs. Minimal code changes with single-command execution for reviewers.

## Technical Context
**Language/Version**: Python 3.11+ (matches existing codebase)
**Primary Dependencies**: Click (CLI), Pydantic (data models), subprocess (LLM CLI calls), jinja2 (template rendering)
**Storage**: File-based JSON inputs/outputs (score_input.json → final_report.md)
**Testing**: pytest (unit), pytest (integration), mock subprocess for LLM calls
**Target Platform**: CLI tool for code evaluation workflow
**Project Type**: single - extends existing src/ directory structure
**Performance Goals**: <5 seconds report generation, <30 seconds end-to-end with LLM call
**Constraints**: LLM context limits (truncate evidence), external API dependency, template-driven approach
**Scale/Scope**: Handle evaluation data from repositories up to 500MB, support template customization

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. UV-Based Dependency Management**: ✅ PASS
- All new dependencies (jinja2) will be added via uv
- Existing project already uses uv exclusively
- No pip, conda, or other package managers involved

**II. KISS Principle**: ✅ PASS
- Simple template-based approach with string substitution
- Fail-fast error handling for LLM API failures
- No complex error recovery - immediate exception on subprocess errors
- Single responsibility modules (template loading, LLM calling, report generation)

**III. Transparent Change Communication**: ✅ PASS
- Clear commit messages documenting what and why
- Comprehensive documentation updates planned
- Integration with existing CLI patterns maintains consistency

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
├── llm/                    # NEW: LLM report generation module
│   ├── __init__.py
│   ├── report_generator.py # Core LLM integration and report generation
│   ├── template_loader.py  # Template loading and validation utilities
│   └── prompt_builder.py   # Prompt construction and data filtering
├── cli/                    # EXISTING: Command-line interface
│   ├── main.py            # MODIFY: Add --generate-llm-report flag
│   ├── evaluate.py        # EXISTING: Checklist evaluation commands
│   └── llm_report.py      # NEW: Standalone LLM report command
├── metrics/               # EXISTING: Core analysis modules
│   └── models/            # EXISTING: Pydantic data models (reuse for score_input.json)
└── templates/             # NEW: Report templates directory
    └── llm_report.md      # Default report template

tests/
├── unit/
│   └── test_llm/          # NEW: Unit tests for LLM modules
├── integration/
│   └── test_llm_workflow.py # NEW: End-to-end LLM report generation
└── contract/
    └── test_report_schema.py # NEW: Generated report format validation

specs/
└── prompts/               # NEW: Prompt templates directory
    ├── llm_report.md      # Default Gemini prompt template
    └── template_docs.md   # Template field documentation
```

**Structure Decision**: Single project structure extending existing src/ directory with new llm/ module. Minimal changes to existing CLI structure, following established patterns for metrics collection.

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
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

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
