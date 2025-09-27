# Tasks: Checklist Mapping & Scoring Input MVP

**Input**: Design documents from `/specs/002-git-log-docs/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extracted: Python 3.11+, Click, jsonschema, pydantic, pytest
2. Load design documents:
   → data-model.md: 5 entities (ChecklistItem, EvaluationResult, ScoreInput, EvidenceReference, CategoryBreakdown)
   → contracts/: score_input_schema.json, checklist_mapping.yaml
   → research.md: Technology decisions and validation strategies
3. Generate tasks by category:
   → Setup: Dependencies, linting configuration
   → Tests: Contract tests, integration tests
   → Core: Models, evaluator, mapper, CLI
   → Integration: Pipeline integration, reporting
   → Polish: Unit tests, performance, docs
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
- [X] T001 Verify existing project structure and UV dependencies per plan.md
- [X] T002 [P] Configure additional linting rules for new modules in pyproject.toml
- [X] T003 [P] Create checklist evaluation module directory structure in src/metrics/

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [X] T004 [P] Contract test for score_input.json schema validation in tests/contract/test_score_input_schema.py
- [X] T005 [P] Contract test for checklist mapping YAML validation in tests/contract/test_checklist_mapping.py
- [X] T006 [P] Integration test for complete evaluation workflow in tests/integration/test_checklist_evaluation.py
- [X] T007 [P] Integration test for multi-language evaluation in tests/integration/test_language_evaluation.py
- [X] T008 [P] Integration test for edge cases (missing metrics) in tests/integration/test_edge_cases.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
### Data Models
- [ ] T009 [P] ChecklistItem model in src/metrics/models/checklist_item.py
- [ ] T010 [P] EvaluationResult model in src/metrics/models/evaluation_result.py
- [ ] T011 [P] ScoreInput model in src/metrics/models/score_input.py
- [ ] T012 [P] EvidenceReference model in src/metrics/models/evidence_reference.py
- [ ] T013 [P] CategoryBreakdown model in src/metrics/models/category_breakdown.py

### Core Logic
- [ ] T014 ChecklistEvaluator class in src/metrics/checklist_evaluator.py
- [ ] T015 ScoringMapper class in src/metrics/scoring_mapper.py
- [ ] T016 EvidenceTracker class in src/metrics/evidence_tracker.py
- [ ] T017 ChecklistLoader utility in src/metrics/checklist_loader.py

### CLI Integration
- [ ] T018 Evaluate command in src/cli/evaluate.py
- [ ] T019 CLI argument parsing and validation in src/cli/evaluate.py
- [ ] T020 Output formatting and reporting in src/metrics/output_formatter.py

## Phase 3.4: Integration
- [ ] T021 Integrate evaluate command with main CLI in src/cli/main.py
- [ ] T022 Submission.json loading and validation pipeline
- [ ] T023 Score_input.json generation and file writing
- [ ] T024 Report.md appendix generation and formatting

## Phase 3.5: Polish
- [ ] T025 [P] Unit tests for ChecklistEvaluator in tests/unit/test_checklist_evaluator.py
- [ ] T026 [P] Unit tests for ScoringMapper in tests/unit/test_scoring_mapper.py
- [ ] T027 [P] Unit tests for EvidenceTracker in tests/unit/test_evidence_tracker.py
- [ ] T028 [P] Unit tests for data models validation in tests/unit/test_models.py
- [ ] T029 Performance testing (<5 seconds target) in tests/performance/test_evaluation_speed.py
- [ ] T030 [P] Update quickstart.md with real examples and outputs
- [ ] T031 Error handling refinement and logging improvements
- [ ] T032 Code cleanup and documentation strings

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T008) before implementation (T009-T024)
- Models (T009-T013) before core logic (T014-T017)
- Core logic (T014-T017) before CLI (T018-T020)
- CLI (T018-T020) before integration (T021-T024)
- Implementation (T009-T024) before polish (T025-T032)

## Parallel Example
```bash
# Launch T004-T008 together (contract and integration tests):
Task: "Contract test for score_input.json schema validation in tests/contract/test_score_input_schema.py"
Task: "Contract test for checklist mapping YAML validation in tests/contract/test_checklist_mapping.py"
Task: "Integration test for complete evaluation workflow in tests/integration/test_checklist_evaluation.py"
Task: "Integration test for multi-language evaluation in tests/integration/test_language_evaluation.py"
Task: "Integration test for edge cases in tests/integration/test_edge_cases.py"

# Launch T009-T013 together (data models):
Task: "ChecklistItem model in src/metrics/models/checklist_item.py"
Task: "EvaluationResult model in src/metrics/models/evaluation_result.py"
Task: "ScoreInput model in src/metrics/models/score_input.py"
Task: "EvidenceReference model in src/metrics/models/evidence_reference.py"
Task: "CategoryBreakdown model in src/metrics/models/category_breakdown.py"

# Launch T025-T028 together (unit tests):
Task: "Unit tests for ChecklistEvaluator in tests/unit/test_checklist_evaluator.py"
Task: "Unit tests for ScoringMapper in tests/unit/test_scoring_mapper.py"
Task: "Unit tests for EvidenceTracker in tests/unit/test_evidence_tracker.py"
Task: "Unit tests for data models validation in tests/unit/test_models.py"
```

## Task Details

### T004: Contract test for score_input.json schema validation
**File**: tests/contract/test_score_input_schema.py
**Purpose**: Validate that generated score_input.json conforms to JSON schema
**Dependencies**: None
**Success Criteria**: Test loads schema from contracts/score_input_schema.json and validates sample data

### T006: Integration test for complete evaluation workflow
**File**: tests/integration/test_checklist_evaluation.py
**Purpose**: Test end-to-end evaluation from submission.json to score_input.json
**Dependencies**: None
**Success Criteria**: Test processes sample submission.json and produces valid score_input.json

### T009: ChecklistItem model
**File**: src/metrics/models/checklist_item.py
**Purpose**: Pydantic model for individual checklist evaluation items
**Dependencies**: T004-T008 (tests must fail first)
**Success Criteria**: Model validates all fields per data-model.md specification

### T014: ChecklistEvaluator class
**File**: src/metrics/checklist_evaluator.py
**Purpose**: Core evaluation logic that processes submission.json against checklist
**Dependencies**: T009-T013 (data models)
**Success Criteria**: Evaluates all 11 checklist items with evidence tracking

### T018: Evaluate command
**File**: src/cli/evaluate.py
**Purpose**: CLI command that accepts input/output paths and runs evaluation
**Dependencies**: T014-T017 (core logic)
**Success Criteria**: Command-line interface matches quickstart.md examples

## Validation Test Scenarios

### Real Repository Testing
- **code-walker**: Test with known Python repository (per requirements)
- **JavaScript project**: Test multi-language support
- **Incomplete metrics**: Test graceful degradation

### Edge Cases
- Malformed submission.json files
- Missing metric sections
- Zero test coverage scenarios
- Empty README files

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
   - score_input_schema.json → T004 contract test
   - checklist_mapping.yaml → T005 contract test

2. **From Data Model**:
   - ChecklistItem → T009 model creation
   - EvaluationResult → T010 model creation
   - ScoreInput → T011 model creation
   - EvidenceReference → T012 model creation
   - CategoryBreakdown → T013 model creation

3. **From Quickstart**:
   - Evaluation workflow → T006 integration test
   - Multi-language support → T007 integration test
   - Edge case handling → T008 integration test

4. **From Plan Structure**:
   - checklist_evaluator.py → T014 core logic
   - scoring_mapper.py → T015 core logic
   - evidence_tracker.py → T016 core logic
   - evaluate.py CLI → T018 CLI integration

## Validation Checklist
*GATE: Checked before task execution*

- [x] All contracts have corresponding tests (T004-T005)
- [x] All entities have model tasks (T009-T013)
- [x] All tests come before implementation (T004-T008 before T009+)
- [x] Parallel tasks truly independent (different files verified)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Core evaluation logic covers all 11 checklist items
- [x] CLI integration matches existing patterns
- [x] Real repository validation included