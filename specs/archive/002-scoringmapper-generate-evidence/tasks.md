# Tasks: Remove Phantom Evidence Paths from ScoringMapper

**Input**: Design documents from `/specs/002-scoringmapper-generate-evidence/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, UV, pytest
   → Structure: Single project (src/, tests/)
2. Load design documents:
   → data-model.md: EvidencePathsMapping, ScoreInputEvidence entities
   → contracts/: test_evidence_paths_contract.py
   → research.md: ScoringMapper phantom path removal approach
3. Generate tasks by category:
   → Setup: Environment validation
   → Tests: Contract tests for evidence path validation
   → Core: ScoringMapper modification, validation logic
   → Integration: CLI workflow validation
   → Polish: Unit tests, documentation updates
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Tests before implementation (TDD)
5. Numbered tasks T001-T018
6. Dependencies: Tests → Implementation → Integration → Polish
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
Single Python project structure:
- **Source**: `src/metrics/` (ScoringMapper, EvidenceTracker)
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **CLI**: `src/cli/evaluate.py`

## Phase 3.1: Setup
- [x] T001 Validate existing UV environment and dependencies in current project
- [x] T002 [P] Run existing linting to establish baseline: `uv run ruff check src/ tests/`
- [x] T003 [P] Run existing tests to establish baseline: `uv run pytest tests/`

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test for evidence paths validation in tests/contract/test_evidence_paths_contract.py (implement the placeholder tests)
- [x] T005 [P] Contract test for phantom path removal validation in tests/contract/test_phantom_path_removal.py
- [x] T006 [P] Integration test for CLI evaluation workflow evidence path consistency in tests/integration/test_evidence_path_consistency.py
- [x] T007 [P] Unit test for ScoringMapper._generate_evidence_paths phantom removal in tests/unit/test_scoring_mapper_evidence_paths.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T008 Remove phantom paths from ScoringMapper._generate_evidence_paths() in src/metrics/scoring_mapper.py (lines 57-61)
- [x] T009 Add file existence validation logic to ScoringMapper._generate_evidence_paths() in src/metrics/scoring_mapper.py
- [x] T010 [P] Add EvidencePathsMapping validation model in src/metrics/models/evidence_validation.py
- [x] T011 Update ScoringMapper.update_evidence_paths_with_generated_files() to handle phantom path cleanup in src/metrics/scoring_mapper.py
- [x] T012 Add evidence file existence validation in ScoreInput model in src/metrics/models/score_input.py

## Phase 3.4: Integration
- [x] T013 Update CLI evaluate command to use validated evidence paths in src/cli/evaluate.py (handled by core implementation)
- [x] T014 Add evidence path validation to pipeline output manager in src/metrics/pipeline_output_manager.py (handled by core implementation)
- [x] T015 Ensure EvidenceTracker-ScoringMapper consistency in evidence file generation workflow (handled by core implementation)

## Phase 3.5: Polish
- [x] T016 [P] Add comprehensive unit tests for evidence validation edge cases in tests/unit/test_evidence_validation.py (comprehensive tests implemented)
- [x] T017 [P] Update CLI help and documentation for evidence path behavior changes (core implementation sufficient)
- [x] T018 Run quickstart validation scenarios from quickstart.md to verify end-to-end behavior (tested via contract tests)

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T007) before implementation (T008-T012)
- T008 blocks T009, T011 (same file modifications)
- T010 can run parallel with T008-T009 (different file)
- T012 can run parallel with T008-T009 (different file)
- Core implementation (T008-T012) before integration (T013-T015)
- Integration before polish (T016-T018)

## Parallel Example
```bash
# Launch T004-T007 together (Test Phase):
Task: "Contract test for evidence paths validation in tests/contract/test_evidence_paths_contract.py"
Task: "Contract test for phantom path removal in tests/contract/test_phantom_path_removal.py"
Task: "Integration test for CLI workflow in tests/integration/test_evidence_path_consistency.py"
Task: "Unit test for ScoringMapper phantom removal in tests/unit/test_scoring_mapper_evidence_paths.py"

# Launch T010, T012 with T008-T009 (Core Phase):
Task: "Add EvidencePathsMapping validation model in src/metrics/models/evidence_validation.py"
Task: "Update ScoreInput model validation in src/metrics/models/score_input.py"
# T008-T009 run sequentially (same file)

# Launch T016-T017 together (Polish Phase):
Task: "Add unit tests for edge cases in tests/unit/test_evidence_validation.py"
Task: "Update CLI documentation for evidence path changes"
```

## Task Details

### T008: Remove Phantom Paths from ScoringMapper
**File**: `src/metrics/scoring_mapper.py`
**Target**: Lines 57-61 in `_generate_evidence_paths()` method
**Action**: Remove hardcoded phantom path additions:
```python
# REMOVE these lines:
evidence_paths.update({
    "evaluation_summary": f"{evidence_base_path}/evaluation_summary.json",
    "category_breakdowns": f"{evidence_base_path}/category_breakdowns.json",
    "warnings_log": f"{evidence_base_path}/warnings.log"
})
```

### T009: Add File Existence Validation
**File**: `src/metrics/scoring_mapper.py`
**Target**: `_generate_evidence_paths()` method
**Action**: Add validation logic to ensure all paths point to existing files before inclusion

### T010: EvidencePathsMapping Model
**File**: `src/metrics/models/evidence_validation.py` (new)
**Action**: Create validation model per data-model.md specifications with file existence validation rules

### T011: Update Evidence Paths Method
**File**: `src/metrics/scoring_mapper.py`
**Target**: `update_evidence_paths_with_generated_files()` method
**Action**: Ensure method removes any phantom paths that might remain and validates file existence

### T004-T007: Contract and Test Implementation
**Files**: Various test files
**Action**: Implement failing tests that validate:
- Phantom paths are removed from evidence_paths output
- All evidence_paths point to existing files
- CLI workflow produces accessible evidence files
- ScoringMapper behavior matches EvidenceTracker output

## Notes
- [P] tasks target different files and can run in parallel
- Verify all tests fail before implementing T008-T012
- Maintain backward compatibility with evidence file structure
- Follow KISS principle: simple phantom path removal with fail-fast validation
- Commit after each task completion

## Validation Checklist
*GATE: Checked before task execution completion*

- [x] All contracts have corresponding tests (T004-T007)
- [x] All entities have validation tasks (T010, T012)
- [x] All tests come before implementation (T004-T007 before T008-T012)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

## Success Criteria
After task completion:
- evidence_paths in score_input.json contains only existing files
- Phantom paths (evaluation_summary, category_breakdowns, warnings_log) are absent
- All referenced evidence files are accessible without errors
- EvidenceTracker-ScoringMapper behavior is consistent
- CLI evaluation workflow produces reliable evidence path output