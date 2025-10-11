# Feature Specification: Unified Toolchain Health Check Layer

**Feature Branch**: `002-toolexecutor-toolchainmanager-cli`
**Created**: 2025-10-11
**Status**: Draft
**Input**: User description: "统一的工具链健康检查层 - 核心动作：在入口（ToolExecutor 或更高层）新增一个 ToolchainManager，按语言和场景列出必须存在的 CLI（如 ruff、pytest、pip-audit、npm、go 等），使用 shutil.which 或 sys.executable 级别的检测。只要有任一工具缺失，就立即抛出自定义异常并中断流程，提示'请在评分主机安装缺失工具'，绝不做自动 fallback。收益最大化：现在的误报主要来自检测失真或静默 fallback，这会导致后续分数和报告全部偏差。统一检查后，所有仓库要么在完整工具链上执行，要么直接失败并指向运维问题，评分数据稳定性立刻提升。"

## Execution Flow (main)
```
1. Parse user description from Input
   → SUCCESS: Feature is about validating tool availability before analysis
2. Extract key concepts from description
   → Actors: System operators, automated analysis pipeline
   → Actions: Validate tool presence, fail fast on missing tools, prevent silent fallbacks
   → Data: Tool availability status, error messages
   → Constraints: All required tools must be present, no partial execution allowed
3. For each unclear aspect:
   → RESOLVED: All tools strictly required, no optional distinction
   → RESOLVED: Error messages show tool name + official doc link
   → RESOLVED: Version validation with minimum requirements
   → RESOLVED: Permission errors with detailed diagnostics
   → RESOLVED: Multi-error collection grouped by category
4. Fill User Scenarios & Testing section
   → SUCCESS: 8 acceptance scenarios covering all validation types
5. Generate Functional Requirements
   → SUCCESS: 17 testable requirements covering validation behavior
6. Identify Key Entities
   → SUCCESS: Tool requirements, validation results, error reporting with categorization
7. Run Review Checklist
   → SUCCESS: All checklist items passed
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

### Session 2025-10-11

- Q: When a tool is marked as "optional" (e.g., an additional linter like pylint beyond the required ruff), what should happen if it's missing? → A: No distinction between optional and required tools. All tools in the hardcoded dependency manifest are strictly required. The system uses a single unified tool registry organized by language: Global (git, uv, curl/tar), Python (ruff, pytest, pip-audit, uv, python3.11+), JavaScript/TypeScript (node, npm with npx, eslint, npm ≥8), Go (go, golangci-lint, osv-scanner), Java (mvn, gradle, java JDK 17+). All tools validated via shutil.which at startup; missing tool causes immediate failure.

- Q: When tools are missing, what level of installation guidance should error messages provide? → A: Error messages should follow the format "缺少工具 {tool_name}。请在评分主机安装后重试（参考 {official_documentation_url}）". This provides tool name, actionable instruction, and reference to official documentation without platform-specific commands.

- Q: When a tool exists but is outdated (may produce incompatible output), how should the system handle it? → A: Validate tool version meets minimum requirements. If version is below minimum, fail validation and provide error message indicating current version and minimum required version. Example: "工具 npm 版本过旧（当前: 7.5.0，最低要求: 8.0.0）。请升级后重试（参考 https://docs.npmjs.com）"

- Q: When a tool exists but is not executable (e.g., permission errors), how should the system handle it? → A: Immediately halt execution with detailed permission error message including tool path and current permissions. Example format: "工具 ruff 位于 /usr/bin/ruff 但权限不足（当前: -rw-r--r--）。请修复权限后重试。" This allows operations team to diagnose and fix the exact issue before rerunning analysis.

- Q: When multiple validation errors occur (e.g., tool A missing, tool B outdated, tool C permission error), how should the error report be organized? → A: Collect all validation errors and report them together in a single comprehensive error message, grouped by error category (missing tools, outdated tools, permission errors). This allows operations team to see the complete scope of issues and fix all problems systematically before rerunning analysis, rather than discovering issues one at a time through multiple failed attempts.

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a system operator running code quality analysis, I need the system to validate that all required analysis tools are installed before starting any repository analysis, so that I receive accurate and complete analysis results rather than misleading partial results from missing tools.

### Acceptance Scenarios

1. **Given** the analysis environment has all required tools installed for Python repositories, **When** the system starts analyzing a Python repository, **Then** the validation passes and analysis proceeds normally

2. **Given** the analysis environment is missing the Python linting tool (ruff), **When** the system attempts to analyze a Python repository, **Then** the validation fails immediately with an error message in the format "缺少工具 ruff。请在评分主机安装后重试（参考 https://docs.astral.sh/ruff）"

3. **Given** the analysis environment has complete tooling for JavaScript but incomplete tooling for Python, **When** the system analyzes a JavaScript repository, **Then** the validation passes because only JavaScript-relevant tools are checked

4. **Given** multiple required tools are missing from the environment (e.g., ruff and pytest), **When** the system performs validation, **Then** all missing tools are reported in a single comprehensive error message with each tool following the format "缺少工具 {tool_name}。请在评分主机安装后重试（参考 {url}）"

5. **Given** the system previously allowed partial execution with missing tools, **When** the new validation layer is active, **Then** no analysis proceeds until all required tools are present, preventing data quality issues

6. **Given** the analysis environment has npm version 7.5.0 installed but minimum requirement is 8.0.0, **When** the system performs validation for a JavaScript repository, **Then** the validation fails with error message "工具 npm 版本过旧（当前: 7.5.0，最低要求: 8.0.0）。请升级后重试（参考 https://docs.npmjs.com）"

7. **Given** the ruff tool exists at /usr/bin/ruff but has incorrect permissions (-rw-r--r--), **When** the system performs validation for a Python repository, **Then** the validation fails immediately with error message "工具 ruff 位于 /usr/bin/ruff 但权限不足（当前: -rw-r--r--）。请修复权限后重试。"

8. **Given** multiple validation issues exist simultaneously (pytest missing, npm version 7.5.0 vs required 8.0.0, ruff with wrong permissions), **When** the system performs validation, **Then** all errors are collected and reported in a single message grouped by category: "缺少工具" section listing pytest, "版本过旧" section listing npm, "权限不足" section listing ruff with details

### Edge Cases

- What happens during validation if detecting tool availability itself times out or hangs?
- How should the system behave when analyzing a repository with an unrecognized or newly-supported language?
- What happens when the same tool is required for multiple purposes (e.g., pip used for both package management and auditing)?
- What happens when a tool's version cannot be detected (tool exists but doesn't support --version flag)?
- What happens when an error category has no errors (e.g., all tools present but some outdated) - should empty categories be shown or omitted?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST validate presence of all language-specific analysis tools before beginning repository analysis

- **FR-002**: System MUST organize tool requirements by language (Python, JavaScript, Java, Go) and analysis category (linting, testing, security, build)

- **FR-003**: System MUST immediately fail and halt execution when any required tool is missing, without attempting partial analysis or silent fallback behavior

- **FR-004**: System MUST provide clear error messages identifying which specific tool(s) are missing when validation fails

- **FR-005**: System MUST include actionable guidance in error messages (e.g., "Please install ruff on the analysis host") when tools are missing

- **FR-006**: System MUST perform tool validation once at analysis startup, before repository cloning or any analysis activity

- **FR-007**: System MUST distinguish between tools required for the target repository's language and tools not needed for that analysis

- **FR-008**: System MUST prevent all silent fallback behavior where the system continues with reduced functionality when tools are absent

- **FR-009**: System MUST report validation success clearly when all required tools are present

- **FR-010**: System MUST handle the scenario where tool detection itself fails (e.g., permission errors, path issues) as a validation failure

- **FR-011**: System MUST support validation of tools across all currently supported languages (Python, JavaScript/TypeScript, Java, Go)

- **FR-012**: System MUST treat all tools in the dependency manifest as strictly required with no distinction between core and optional tools; any missing tool causes validation failure

- **FR-013**: Error messages MUST follow the format "缺少工具 {tool_name}。请在评分主机安装后重试（参考 {official_documentation_url}）" providing tool name and official documentation reference without platform-specific installation commands

- **FR-014**: System MUST define hardcoded tool dependencies organized as: Global tools (git, uv, curl/tar), Python-specific (ruff, pytest, pip-audit, uv, python3.11+), JavaScript/TypeScript-specific (node, npm with npx, eslint, npm version ≥8), Go-specific (go, golangci-lint, osv-scanner), Java-specific (mvn, gradle, java JDK 17+)

- **FR-015**: System MUST validate tool versions against minimum version requirements where specified; tools below minimum version MUST cause validation failure with error message format "工具 {tool_name} 版本过旧（当前: {current_version}，最低要求: {minimum_version}）。请升级后重试（参考 {url}）"

- **FR-016**: System MUST detect when a tool exists but is not executable (permission errors) and immediately halt with detailed error message format "工具 {tool_name} 位于 {path} 但权限不足（当前: {permissions}）。请修复权限后重试。" including tool path and current permission flags

- **FR-017**: System MUST collect all validation errors during startup check and report them together in a single comprehensive message, organized by error category (missing tools section, outdated tools section, permission errors section), allowing operations team to fix all issues before retry rather than discovering problems incrementally

### Key Entities *(include if feature involves data)*

- **Tool Requirement**: Represents a single required command-line tool with its name, purpose category (lint/test/security/build), target language (or global if applicable to all repositories), official documentation URL for error message references, and optional minimum version requirement

- **Validation Result**: Represents the outcome of checking a single tool, including its name, whether it was found, its location if found, detected version (if applicable), whether version meets minimum requirements, file permissions (if applicable), and any error details with specific error category (missing/outdated/permission/other)

- **Language Toolchain**: Represents the complete set of tool requirements for a specific programming language, organized by analysis category

- **Validation Report**: Comprehensive report of all tool validations performed, including overall pass/fail status, and validation errors organized by category (missing tools, outdated tools, permission errors) with each category containing specific tool details and actionable error messages

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain (all 5 clarifications resolved)
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (5 clarifications identified)
- [x] Ambiguities resolved (5/5 clarifications completed)
- [x] User scenarios defined and updated
- [x] Requirements generated (17 functional requirements)
- [x] Entities identified and refined
- [x] Review checklist passed

---

## Business Value & Motivation

### Problem Statement
Currently, the code analysis system allows execution to continue even when required tools are missing or unavailable. This leads to:
- **Data Quality Issues**: Partial analysis results are misleading and create false confidence in incomplete assessments
- **Silent Failures**: Missing tools cause silent fallbacks that hide problems until reports are reviewed
- **Operational Ambiguity**: Users cannot distinguish between "repository has no issues" and "analysis tools were not available"
- **Score Instability**: Different analysis runs produce inconsistent scores depending on which tools happened to be available

### Expected Benefits
1. **Data Reliability**: Every analysis result represents a complete assessment with all tools executed
2. **Fail-Fast Operations**: Infrastructure problems are immediately visible rather than hidden in partial results
3. **Operational Clarity**: Clear separation between "analysis succeeded" and "environment needs configuration"
4. **Score Consistency**: All repositories analyzed with identical tool availability guarantee comparable results
5. **Reduced False Positives**: Elimination of scenarios where missing tools incorrectly suggest clean codebases

### Success Metrics
- Zero instances of partial analysis proceeding with missing tools after implementation
- 100% of tool availability issues reported before repository cloning begins
- Reduction in time-to-diagnose environment configuration issues
- Elimination of score discrepancies caused by tool availability variations

---
