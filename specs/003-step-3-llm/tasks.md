# Tasks: LLM-Generated Code Review Reports

**Input**: Design documents from `/specs/003-step-3-llm/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11+, Click, Pydantic, subprocess, jinja2, pytest
2. Load design documents:
   → data-model.md: 3 new entities (ReportTemplate, LLMProviderConfig, GeneratedReport)
   → contracts/: 4 schemas + CLI specification
   → quickstart.md: 4 test scenarios + error handling
3. Generate tasks by category:
   → Setup: Dependencies, linting, directory structure
   → Tests: Contract tests, integration tests (TDD)
   → Core: New models, LLM modules, template system
   → Integration: CLI commands, pipeline integration
   → Polish: Unit tests, performance, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests ✓
   → All entities have models ✓
   → All CLI commands implemented ✓
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root (confirmed from plan.md)
- All paths relative to repository root `/Users/user/workspace/code-score/`

## Phase 3.1: Setup
- [x] T001 Add jinja2 dependency to pyproject.toml using uv
- [x] T002 [P] Create LLM module directory structure: src/llm/__init__.py
- [x] T003 [P] Create default prompt template directory: specs/prompts/llm_report.md
- [x] T004 [P] Configure linting rules for new LLM modules in pyproject.toml

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T005 [P] Contract test for template schema validation in tests/contract/test_template_schema.py
- [x] T006 [P] Contract test for LLM provider schema validation in tests/contract/test_llm_provider_schema.py
- [x] T007 [P] Contract test for generated report schema validation in tests/contract/test_generated_report_schema.py
- [x] T008 [P] Contract test for CLI commands specification in tests/contract/test_cli_commands.py
- [x] T009 [P] Integration test for basic report generation workflow in tests/integration/test_llm_report_workflow.py
- [x] T010 [P] Integration test for dry-run mode in tests/integration/test_dry_run_mode.py
- [x] T011 [P] Integration test for custom template usage in tests/integration/test_custom_template.py
- [x] T012 [P] Integration test for error handling scenarios in tests/integration/test_error_handling.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
### Data Models
- [x] T013 [P] ReportTemplate model in src/llm/models/report_template.py
- [x] T014 [P] LLMProviderConfig model in src/llm/models/llm_provider_config.py
- [x] T015 [P] GeneratedReport model in src/llm/models/generated_report.py
- [x] T016 [P] TemplateContext data structure in src/llm/models/template_context.py

### Core LLM Modules
- [x] T017 TemplateLoader class in src/llm/template_loader.py
- [x] T018 PromptBuilder class in src/llm/prompt_builder.py
- [x] T019 ReportGenerator class in src/llm/report_generator.py

### CLI Integration
- [x] T020 Standalone llm-report command in src/cli/llm_report.py
- [x] T021 Add --generate-llm-report flag to src/cli/main.py analyze command
- [x] T022 CLI argument validation and help text for llm-report command
- [x] T023 Error handling and user feedback for CLI operations

## Phase 3.4: Integration
- [x] T024 Create default template file at specs/prompts/llm_report.md
- [x] T025 Integrate report generation with pipeline_output_manager.py
- [x] T026 Add LLM report generation to scripts/run_metrics.sh
- [x] T027 Subprocess timeout handling and error recovery
- [x] T028 Template validation and security (Jinja2 sandboxing)

## Phase 3.5: Polish
- [ ] T029 [P] Unit tests for TemplateLoader in tests/unit/test_template_loader.py
- [ ] T030 [P] Unit tests for PromptBuilder in tests/unit/test_prompt_builder.py
- [ ] T031 [P] Unit tests for ReportGenerator in tests/unit/test_report_generator.py
- [ ] T032 [P] Unit tests for data models in tests/unit/test_llm_models.py
- [ ] T033 Performance testing (<5 seconds generation) in tests/performance/test_llm_performance.py
- [ ] T034 [P] Update README.md with LLM report generation usage examples
- [ ] T035 [P] Update docs/api-reference.md with LLM module documentation
- [ ] T036 Code cleanup and comprehensive docstrings for all LLM modules

## Dependencies
- Setup (T001-T004) before everything
- Tests (T005-T012) before implementation (T013-T028)
- Models (T013-T016) before core modules (T017-T019)
- Core modules (T017-T019) before CLI (T020-T023)
- CLI (T020-T023) before integration (T024-T028)
- Implementation (T013-T028) before polish (T029-T036)

## Parallel Example
```bash
# Launch T005-T012 together (contract and integration tests):
Task: "Contract test for template schema validation in tests/contract/test_template_schema.py"
Task: "Contract test for LLM provider schema validation in tests/contract/test_llm_provider_schema.py"
Task: "Contract test for generated report schema validation in tests/contract/test_generated_report_schema.py"
Task: "Contract test for CLI commands specification in tests/contract/test_cli_commands.py"
Task: "Integration test for basic report generation workflow in tests/integration/test_llm_report_workflow.py"
Task: "Integration test for dry-run mode in tests/integration/test_dry_run_mode.py"
Task: "Integration test for custom template usage in tests/integration/test_custom_template.py"
Task: "Integration test for error handling scenarios in tests/integration/test_error_handling.py"

# Launch T013-T016 together (data models):
Task: "ReportTemplate model in src/llm/models/report_template.py"
Task: "LLMProviderConfig model in src/llm/models/llm_provider_config.py"
Task: "GeneratedReport model in src/llm/models/generated_report.py"
Task: "TemplateContext data structure in src/llm/models/template_context.py"

# Launch T029-T032 together (unit tests):
Task: "Unit tests for TemplateLoader in tests/unit/test_template_loader.py"
Task: "Unit tests for PromptBuilder in tests/unit/test_prompt_builder.py"
Task: "Unit tests for ReportGenerator in tests/unit/test_report_generator.py"
Task: "Unit tests for data models in tests/unit/test_llm_models.py"
```

## Task Details

### T005: Contract test for template schema validation
**File**: tests/contract/test_template_schema.py
**Purpose**: Validate template configuration against JSON schema
**Dependencies**: None
**Success Criteria**: Test loads schema from contracts/template_schema.json and validates sample data

### T009: Integration test for basic report generation workflow
**File**: tests/integration/test_llm_report_workflow.py
**Purpose**: Test end-to-end workflow from score_input.json to final_report.md
**Dependencies**: None
**Success Criteria**: Test processes sample score_input.json and produces valid report

### T013: ReportTemplate model
**File**: src/llm/models/report_template.py
**Purpose**: Pydantic model for template configuration and metadata
**Dependencies**: T005-T008 (tests must fail first)
**Success Criteria**: Model validates all fields per data-model.md specification

### T019: ReportGenerator class
**File**: src/llm/report_generator.py
**Purpose**: Core class that orchestrates template loading, prompt building, and LLM calls
**Dependencies**: T013-T018 (models and supporting classes)
**Success Criteria**: Generates reports from score_input.json with subprocess LLM calls

### T020: Standalone llm-report command
**File**: src/cli/llm_report.py
**Purpose**: CLI command that accepts input/output paths and runs report generation
**Dependencies**: T019 (ReportGenerator)
**Success Criteria**: Command-line interface matches CLI specification in contracts/cli_commands.yaml

### T024: Create default template file
**File**: specs/prompts/llm_report.md
**Purpose**: Default Jinja2 template with placeholders for repository data, scores, and evidence
**Dependencies**: T017 (TemplateLoader)
**Success Criteria**: Template includes all required fields from quickstart.md examples

## Validation Test Scenarios

### Real Repository Testing
- **pallets/click**: Test with known Python repository (per quickstart.md)
- **Custom template**: Test template customization workflow
- **Error conditions**: Test missing files, invalid templates, LLM failures

### Edge Cases
- Malformed score_input.json files
- Missing template files
- LLM CLI command failures
- Timeout scenarios
- Large evaluation datasets requiring truncation

## Notes
- [P] tasks = different files, no dependencies between them
- All tests must fail initially (TDD requirement)
- Commit after each significant task completion
- Follow constitutional principles: UV-only, KISS, transparent communication
- Use existing test patterns from tests/unit/, tests/integration/, tests/contract/
- Maintain compatibility with existing CLI structure in src/cli/main.py

## Task Generation Rules Applied
*Verified during generation*

1. **From Contracts**:
   - template_schema.json → T005 contract test
   - llm_provider_schema.json → T006 contract test
   - generated_report_schema.json → T007 contract test
   - cli_commands.yaml → T008 contract test

2. **From Data Model**:
   - ReportTemplate → T013 model creation
   - LLMProviderConfig → T014 model creation
   - GeneratedReport → T015 model creation
   - TemplateContext → T016 model creation

3. **From Quickstart**:
   - Basic usage workflow → T009 integration test
   - Dry-run mode → T010 integration test
   - Custom template → T011 integration test
   - Error handling → T012 integration test

4. **From Plan Structure**:
   - template_loader.py → T017 core module
   - prompt_builder.py → T018 core module
   - report_generator.py → T019 core module
   - llm_report.py CLI → T020 CLI command

## Validation Checklist
*GATE: Checked before task execution*

- [x] All contracts have corresponding tests (T005-T008)
- [x] All entities have model tasks (T013-T016)
- [x] All tests come before implementation (T005-T012 before T013+)
- [x] Parallel tasks truly independent (different files verified)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Core LLM functionality covers report generation workflow
- [x] CLI integration matches existing patterns
- [x] Real repository validation included