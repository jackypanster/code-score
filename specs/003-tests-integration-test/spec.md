# Feature Specification: Programmatic CLI Evaluation Entry Point

**Feature Branch**: `003-tests-integration-test`
**Created**: 2025-10-12
**Status**: Draft
**Input**: User description: "问题背景：集成测试 tests/integration/test_evidence_path_consistency.py 尝试从 src.cli.evaluate 导入 evaluate_submission 函数，但 CLI 模块目前只暴露了 Click 命令 evaluate(...)，导致 ImportError，使测试套件在收集阶段就失败（uv run pytest --maxfail=1）。"

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature request: Add programmatic entry point for CLI evaluation workflow
2. Extract key concepts from description
   → Actors: integration tests, internal tooling, CLI users
   → Actions: programmatic evaluation, CLI command execution, test assertion
   → Data: submission.json, score_input.json, evidence files
   → Constraints: maintain CLI backward compatibility, share behavior between test and CLI
3. For each unclear aspect:
   → ✅ All aspects clearly defined in user description
4. Fill User Scenarios & Testing section
   → Integration tests need Python API, CLI users need command-line interface
5. Generate Functional Requirements
   → Extract core logic, create programmatic entry point, preserve CLI behavior
6. Identify Key Entities (if data involved)
   → Evaluation parameters, evaluation results, file paths
7. Run Review Checklist
   → No implementation details, focused on user value
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-12

- Q: When programmatic function encounters quality gate failure (score < 30%), how should it communicate this status to the caller? → A: Throw a specific QualityGateException exception (caller must catch exception to handle)
- Q: When programmatic function encounters filesystem errors (unable to create output directory, unable to write files), how should it handle them? → A: Catch underlying exceptions and wrap as custom EvaluationFileSystemError with context information
- Q: When programmatic function in validate-only mode successfully validates input, what should it return to the caller? → A: Return a dictionary/object containing validation details (validation items, passed checks list)
- Q: When programmatic function executes, how should log output (verbose/quiet mode messages) be handled? → A: Programmatic function logs via Python logging module, caller can configure log handlers
- Q: Programmatic function in normal mode (non-validate-only) after successful evaluation, what minimum required information should the returned status object contain? → A: Include success flag, total score, evaluation grade, list of generated file paths

---

## User Scenarios & Testing

### Primary User Story

**Integration Test Author**: As a developer writing integration tests for the evaluation workflow, I need to programmatically invoke the evaluation logic from Python code so that I can validate end-to-end behavior including evidence file generation and path consistency without spawning CLI processes.

**Internal Tooling Developer**: As a developer building internal automation tools, I need a stable Python API to trigger checklist evaluations so that I can integrate evaluation workflows into larger automation pipelines without parsing CLI output or duplicating evaluation logic.

**CLI User**: As a command-line user, I need the existing CLI command to continue working exactly as before so that my existing scripts and workflows are not disrupted.

### Acceptance Scenarios

1. **Given** an integration test file that imports `evaluate_submission` from `src.cli.evaluate`, **When** pytest collects tests, **Then** no ImportError occurs and test collection completes successfully.

2. **Given** a valid submission.json file, **When** calling `evaluate_submission()` programmatically with appropriate parameters, **Then** the function completes evaluation, writes score_input.json, generates evidence files, and returns a status object containing success flag, total score, evaluation grade, and generated file paths list.

3. **Given** an existing CLI workflow using `uv run python -m src.cli.evaluate submission.json`, **When** the programmatic entry point is added, **Then** the CLI command continues to work with identical behavior and output.

4. **Given** a submission file that fails quality gate (score < 30%), **When** calling `evaluate_submission()` programmatically, **Then** the function raises a specific QualityGateException that calling code can catch and handle.

5. **Given** the programmatic entry point and CLI command executing the same evaluation, **When** comparing their outputs (score_input.json, evidence files), **Then** both produce identical results demonstrating shared behavior.

### Edge Cases

- What happens when programmatic invocation receives invalid file paths?
  → Function should raise clear exceptions with descriptive error messages

- How does the programmatic entry point handle validate-only mode?
  → Function should skip output generation and return a validation result object/dictionary containing validation items checked and passed checks list

- What happens if evidence directory creation fails during programmatic execution?
  → Function should catch underlying filesystem errors (OSError, PermissionError) and wrap them in EvaluationFileSystemError with additional context (operation attempted, target path, original error)

- How does the programmatic API handle verbose/quiet flags?
  → Function logs through Python logging module; verbose mode enables DEBUG level, normal mode uses INFO level, quiet mode suppresses non-error logs; caller can configure log handlers and formatters as needed

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a programmatic Python function `evaluate_submission()` that can be imported from `src.cli.evaluate` without triggering Click dependencies
- **FR-002**: The programmatic function MUST accept all parameters currently available as CLI options (submission file path, output directory, format, checklist config, evidence directory, validate-only flag, quiet flag, verbose flag)
- **FR-003**: The programmatic function MUST return a status object containing evaluation outcome: in validate-only mode, return validation details (items checked, passed checks); in normal mode, return object with success flag, total score, evaluation grade (letter grade A-F), and list of generated file paths
- **FR-004**: The programmatic function MUST raise appropriate typed exceptions on failures rather than calling `sys.exit()`: FileNotFoundError for missing input files, ValueError for validation errors, EvaluationFileSystemError (wrapping OSError/PermissionError with context) for filesystem operations, and preserve other unexpected exceptions
- **FR-005**: The existing Click command `evaluate()` MUST delegate all evaluation logic to the programmatic function to ensure shared behavior
- **FR-006**: System MUST maintain backward compatibility with existing CLI command invocations and output formats
- **FR-007**: The programmatic function MUST update evidence paths in score_input.json identically to the current CLI workflow
- **FR-008**: System MUST write output files (score_input.json, evaluation_report.md) to the same locations whether invoked programmatically or via CLI
- **FR-009**: The programmatic function MUST raise a specific QualityGateException when evaluation score falls below 30% threshold, allowing calling code to distinguish quality gate failures from other error types
- **FR-010**: System MUST provide regression tests covering both success and failure paths through the programmatic entry point
- **FR-011**: Integration test `test_evidence_path_consistency.py` MUST successfully import and call `evaluate_submission()` without ImportError
- **FR-012**: The programmatic function MUST use Python logging module for all output messages (verbose mode = DEBUG level, normal mode = INFO level, quiet mode = WARNING+ only), allowing callers to configure log handlers independently

### Key Entities

- **Evaluation Parameters**: Container for all configuration options (file paths, output format, flags) that control evaluation behavior
- **Evaluation Result**: Container for evaluation outcome; in normal mode contains: success flag, total score, evaluation grade (A-F), list of generated file paths; in validate-only mode contains: validation details (items checked, passed checks list)
- **Submission File**: Input JSON file containing repository metrics to be evaluated
- **Score Input File**: Output JSON file containing structured evaluation results for downstream processing
- **Evidence Files**: Collection of JSON files containing detailed evidence supporting evaluation decisions

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (none found)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
