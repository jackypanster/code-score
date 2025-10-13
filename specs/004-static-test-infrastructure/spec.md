# Feature Specification: Static Test Infrastructure Analysis

**Feature Branch**: `004-static-test-infrastructure`
**Created**: 2025-10-13
**Status**: Draft
**Input**: User description: "Static test infrastructure analysis (COD-8)"
**Linear Issue**: [COD-8](https://linear.app/code-score/issue/COD-8)

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature: Analyze test infrastructure without executing code
2. Extract key concepts from description
   → Actors: Repository analysts, quality evaluators
   → Actions: Detect test files, identify configurations, estimate coverage
   → Data: Test file patterns, configuration files, scoring metrics
   → Constraints: No code execution, <1 second performance, multi-language support
3. For each unclear aspect:
   → All aspects clearly defined in COD-8
4. Fill User Scenarios & Testing section
   → Primary flow: Analyze repository → Detect test infrastructure → Calculate score
5. Generate Functional Requirements
   → 13 testable requirements covering detection, scoring, and output
6. Identify Key Entities
   → TestInfrastructureResult, TestFilePattern, ConfigurationFile
7. Run Review Checklist
   → No implementation details, user-focused, business value clear
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## Clarifications

### Session 2025-10-13

- Q: What files should count as "code files" in the test file ratio denominator (FR-010)? → A: Only non-test source files (exclude test files, docs, configs from denominator)
- Q: How should the system handle repositories with multiple significant languages (e.g., 40% Python + 40% JavaScript)? → A: Analyze all languages with >20% file share and combine scores
- Q: Should the system parse config file contents to verify specific sections/keys, or only check file existence? → A: Parse config files to verify test-related sections exist
- Q: Should the 1-second performance target apply to all repository sizes and multi-language scenarios? → A: Typical repos (<5K files, ≤2 languages) <5 seconds; large/multi-language repos <10 seconds; performance not current priority
- Q: What values should be populated in test_execution section for static analysis (no tests actually run)? → A: Add new field test_files_detected for static file count; keep tests_run/passed/failed as 0 or null; populate framework with inferred framework name; FR-017 clarified to reflect static detection results not execution data

---

## User Scenarios & Testing

### Primary User Story
As a **repository quality analyst**, I want to quickly assess whether a code repository has testing infrastructure in place, so that I can assign appropriate testing scores without waiting for slow test execution or risking security issues from running untrusted code.

### Acceptance Scenarios

1. **Given** a Python repository with a `tests/` directory and `pytest.ini` configuration,
   **When** the system analyzes the repository structure,
   **Then** it detects test files, recognizes pytest configuration, and assigns 20-25 points out of 35 for the Testing dimension.

2. **Given** a JavaScript repository with no test files or test scripts in `package.json`,
   **When** the system analyzes the repository,
   **Then** it correctly identifies the absence of test infrastructure and assigns 0-5 points.

3. **Given** a repository with test files but no coverage configuration,
   **When** scoring is calculated,
   **Then** the system awards points for test presence but not for coverage setup, resulting in a partial score (10-15 points).

4. **Given** a repository with 30% test file ratio (test files / total files),
   **When** the ratio-based scoring is applied,
   **Then** the system adds 10 bonus points for high test coverage estimation.

5. **Given** any typical repository (<5,000 files, ≤2 languages),
   **When** the infrastructure detection runs,
   **Then** the entire process completes in under 5 seconds without executing any code.

5b. **Given** a large or multi-language repository (≥5,000 files or >2 languages),
   **When** the infrastructure detection runs,
   **Then** the entire process completes in under 10 seconds without executing any code.

6. **Given** a repository with 40% Python files and 40% JavaScript files (both >20% threshold),
   **When** the system analyzes the repository,
   **Then** it detects test infrastructure for both languages independently and reports the maximum score achieved (e.g., if Python scores 20 and JavaScript scores 15, final score is 20).

7. **Given** a Python repository with `pyproject.toml` but missing the `[tool.pytest]` section,
   **When** the system parses the configuration file,
   **Then** it awards 0 points for test configuration (not the expected 5 points), resulting in lower overall score.

8. **Given** a repository with 15 detected test files,
   **When** the system populates the output JSON,
   **Then** `metrics.testing.test_execution.test_files_detected = 15`, `tests_run = 0`, `tests_passed = 0`, `tests_failed = 0`, and `framework` contains the inferred framework name (e.g., "pytest").

### Edge Cases

- **What happens when a repository has test files but no recognizable test framework configuration?**
  System awards points for test file presence (5 points) but not for configuration (0 points), resulting in partial credit.

- **What happens when test files are in non-standard locations?**
  System may not detect them if they don't match the defined patterns for that language. This is acceptable as non-standard patterns suggest poor project organization.

- **What happens when a repository mixes multiple languages?**
  System analyzes all languages that represent >20% of repository files and combines their test infrastructure scores. Each language's test detection patterns are applied independently, and the final score is the maximum score achieved across all analyzed languages.

- **How does the system handle empty test directories?**
  Empty directories matching test patterns (e.g., `tests/` with no files) do not count as valid test infrastructure and receive 0 points.

- **What happens when configuration files exist but are malformed or missing required sections?**
  System parses the configuration file and verifies the required test-related section/key exists. If parsing fails or the required section is absent, the file receives 0 configuration points. For example, a `pyproject.toml` without `[tool.pytest]` section is not counted as valid test configuration.

- **How should downstream consumers distinguish static analysis results from actual test execution?**
  The new `test_files_detected` field contains the static file count (may be >0), while `tests_run = 0` explicitly indicates no execution occurred. Future phases (COD-9, COD-10, COD-7) will populate `tests_run` with actual execution counts, making the distinction clear.

---

## Requirements

### Functional Requirements

**Test File Detection**
- **FR-001**: System MUST detect test files for Python repositories using patterns: `tests/` directory, `test_*.py` files, `*_test.py` files
- **FR-002**: System MUST detect test files for JavaScript/TypeScript repositories using patterns: `__tests__/` directory, `*.test.js` files, `*.spec.js` files
- **FR-003**: System MUST detect test files for Go repositories using pattern: `*_test.go` files
- **FR-004**: System MUST detect test files for Java repositories using pattern: `src/test/java/` directory
- **FR-004a**: System MUST analyze all languages that represent more than 20% of repository files in multi-language repositories, and report the maximum score achieved across all analyzed languages

**Test Configuration Detection**
- **FR-005**: System MUST parse and verify test framework configuration files contain test-related sections:
  - Python: `pytest.ini` (any content), `pyproject.toml` (must contain `[tool.pytest]` section), `tox.ini` (any content)
  - JavaScript: `package.json` (must contain `scripts.test` key), `jest.config.js` (any content)
  - Go: `go.mod` (presence only, no parsing required) combined with test files
  - Java: `pom.xml` (must contain surefire plugin reference), `build.gradle` (must contain test task)
- **FR-005a**: System MUST award configuration points only if the required section/key is verified present; malformed files that fail parsing receive 0 points

**Coverage Configuration Detection**
- **FR-006**: System MUST parse and verify coverage configuration files contain coverage-related sections:
  - Python: `.coveragerc` (any content), `pyproject.toml` (must contain `[tool.coverage]` section)
  - JavaScript: `jest.config.js` (must contain `coverageThreshold` key)
  - Go: `Makefile` (must contain coverage-related flags like `-cover` or `coverage`)
  - Java: `pom.xml` or `build.gradle` (must contain jacoco plugin reference)
- **FR-006a**: System MUST award coverage configuration points only if the required section/key is verified present; malformed files that fail parsing receive 0 points

**Scoring Logic**
- **FR-007**: System MUST award 5 points when one or more test files are detected
- **FR-008**: System MUST award 5 points when test framework configuration is detected
- **FR-009**: System MUST award 5 points when coverage configuration is detected
- **FR-010**: System MUST calculate test file ratio as: (number of test files) / (total number of non-test source files). Non-test source files are programming language files (e.g., `.py`, `.js`, `.go`, `.java`) excluding test files, documentation files, and configuration files
- **FR-011**: System MUST award 10 additional points when test file ratio exceeds 30%
- **FR-012**: System MUST award 5 additional points when test file ratio is between 10% and 30%
- **FR-013**: System MUST cap the maximum Testing dimension score at 25 points for static analysis (71% of the full 35 points)

**Performance & Safety**
- **FR-014**: System MUST complete analysis within performance targets based on repository characteristics:
  - Typical repositories (<5,000 files, ≤2 languages): Complete in <5 seconds
  - Large or multi-language repositories (≥5,000 files or >2 languages): Complete in <10 seconds
  - Performance optimization is not a current priority; correctness takes precedence
- **FR-015**: System MUST NOT execute any code from the target repository
- **FR-016**: System MUST NOT require installation of dependencies from the target repository

**Output Integration**
- **FR-017**: System MUST populate the `metrics.testing.test_execution` section with static analysis results:
  - Add new field `test_files_detected` (integer) containing the count of test files found through static analysis
  - Set `tests_run`, `tests_passed`, `tests_failed` to 0 or null to indicate no tests were actually executed
  - Populate `framework` field with the inferred test framework name (e.g., "pytest", "jest", "go test", "junit") based on detected configuration
  - These fields reflect static infrastructure detection, not actual test execution results
- **FR-018**: System MUST update the Testing dimension score in evaluation results based on static analysis scoring (FR-007 through FR-013)
- **FR-019**: System MUST extend (not break) the existing `submission.json` schema by adding the new `test_files_detected` field while maintaining all existing fields

### Non-Functional Requirements

**Reliability**
- **NFR-001**: System MUST handle missing directories, files, and malformed configuration files gracefully without errors. Parsing failures result in 0 points for that configuration type, not system crashes
- **NFR-002**: System MUST produce deterministic results for the same repository state

**Maintainability**
- **NFR-003**: Detection patterns MUST be easily extensible for new languages
- **NFR-004**: Scoring thresholds (e.g., 30% ratio) MUST be configurable

**Performance Priorities**
- **NFR-004a**: Correctness takes absolute precedence over performance; the system MUST produce accurate results even if it exceeds performance targets
- **NFR-004b**: Performance targets in FR-014 are goals for typical cases, not hard requirements; edge cases exceeding targets are acceptable

**Observability**
- **NFR-005**: System MUST log detection results for debugging purposes
- **NFR-006**: System MUST report which detection patterns matched or failed
- **NFR-007**: System MUST log configuration file parsing results, including which files were found, which were successfully parsed, and which failed verification (missing required sections)

### Key Entities

**TestInfrastructureResult**
- Represents the outcome of analyzing a repository's test infrastructure
- Attributes:
  - test_files_detected (integer): Number of test files found through static analysis
  - test_config_detected (boolean): Whether valid test framework configuration was found
  - coverage_config_detected (boolean): Whether valid coverage configuration was found
  - test_file_ratio (percentage): Ratio of test files to non-test source files
  - calculated_score (0-25 points): Final Testing dimension score from static analysis
  - inferred_framework (string): Name of detected test framework (e.g., "pytest", "jest")
- Relationships: One per repository analysis, feeds into Testing dimension evaluation and populates metrics.testing.test_execution section

**TestFilePattern**
- Represents a file pattern used to identify test files for a specific language
- Attributes: language (Python/JavaScript/Go/Java), pattern_type (directory/filename/extension), pattern_string (e.g., "test_*.py")
- Relationships: Multiple patterns per language, applied during test file detection

**ConfigurationFile**
- Represents a configuration file that indicates test infrastructure presence
- Attributes: file_path, file_type (test_framework/coverage), language, detected (boolean), parsed_successfully (boolean), required_section_present (boolean)
- Relationships: Multiple configuration files per repository, contributes to scoring only if both parsed_successfully and required_section_present are true

**TestFileRatioThreshold**
- Represents scoring thresholds based on test-to-code file ratios
- Attributes: threshold_percentage (e.g., 30%, 10%), points_awarded (10, 5)
- Relationships: Applied to TestInfrastructureResult to calculate bonus points

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

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
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (none found)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---

## Additional Context

### Business Value
This feature addresses a critical gap in the current quality assessment system where repositories with test infrastructure receive 0/35 points in the Testing dimension, capping total scores at 57/100. By implementing static infrastructure analysis, the system can:
- **Restore 71% of Testing dimension points** (25/35) without code execution risks
- **Improve assessment accuracy** by differentiating between repos with and without tests
- **Enable fast analysis** completing in <5-10 seconds versus 5-30 minutes for full test execution
- **Maintain security** by avoiding execution of untrusted code

### Success Metrics
- **anthropic-sdk-python** sample: Score increases from 0/35 to 20-25/35 in Testing dimension
- **tetris-web** sample: Correctly assigned 0-5/35 points (no test infrastructure)
- **Total score improvement**: From 57/100 to approximately 75-82/100 for repos with tests
- **Performance**:
  - 100% of typical repositories (<5K files, ≤2 languages) complete in <5 seconds
  - 100% of large/multi-language repositories complete in <10 seconds
  - Performance optimization deferred to later phases if correctness is achieved
- **Reliability**: 0 errors due to code execution or dependency conflicts; malformed config files handled gracefully

### Dependencies & Assumptions
- **Dependency on existing language detection**: System relies on correct primary language identification for single-language repos; for multi-language repos, detects all languages >20% file share
- **Dependency on existing schema**: Extends `metrics.testing.test_execution` with new `test_files_detected` field while preserving existing fields (`tests_run`, `tests_passed`, `tests_failed`, `framework`)
- **Assumption**: Test files follow community conventions for naming and location
- **Assumption**: Presence of required configuration sections indicates functional test setup
- **Clarification**: `tests_run = 0` in output explicitly means "static analysis performed, no tests executed", distinguishing from "tests were executed and zero passed"
- **Out of scope**: Verifying whether detected tests actually run or pass (covered by COD-9, COD-10, COD-7)
- **Out of scope**: Deep validation of configuration file correctness (only presence of required section/key is verified, not semantic validity)

### Phase Relationship
This is **Phase 1** of a 4-phase testing improvement roadmap:
- **Phase 1 (COD-8 - this spec)**: Static infrastructure analysis → 25/35 points
- **Phase 2 (COD-9)**: CI/CD configuration analysis → additional 5 points → 30/35 total
- **Phase 3 (COD-10)**: Optional lightweight test verification → additional 5 points → 35/35 total
- **Phase 4 (COD-7)**: Full test execution with coverage → 35/35 points with real results

Completion of this phase unblocks all subsequent phases.
