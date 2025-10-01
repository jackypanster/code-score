# Feature Specification: Remove Phantom Evidence Paths from ScoringMapper

**Feature Branch**: `002-scoringmapper-generate-evidence`
**Created**: 2025-09-28
**Status**: Draft
**Input**: User description: "- ScoringMapper._generate_evidence_paths() 会先枚举 checklist item 的真实证据文件（这些稍后由 EvidenceTracker 写出），但函数结尾还硬编码了 evaluation_summary.json、category_breakdowns.json、warnings.log 三个键。
  - 当前版本的流水线并不会生成这些"汇总"文件，EvidenceTracker.save_evidence_files() 和 update_evidence_paths_with_generated_files() 都不会补上。
  - 结果：score_input.json.evidence_paths 向外暴露了并不存在的路径，集成方会按图索骥却找不到文件，文档/接口与真实产物不一致。

  任务目标

  彻底移除这些虚构占位符，让 evidence_paths 只包含真实存在的证据文件。完成后：

  - 运行 CLI / smoke 流水线时，score_input.json.evidence_paths 不再出现 evaluation_summary、category_breakdowns、warnings_log 等键。
  - 相关代码、文档、单测与这一行为保持一致。"

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature targets evidence path consistency in evaluation pipeline
2. Extract key concepts from description
   → Actors: code-score tool users, integrating systems
   → Actions: generate score_input.json, reference evidence files
   → Data: evidence_paths field in JSON output
   → Constraints: paths must point to files that actually exist
3. For each unclear aspect:
   → Clear problem definition provided
4. Fill User Scenarios & Testing section
   → User flow: run evaluation pipeline, consume evidence paths
5. Generate Functional Requirements
   → Each requirement targets actual file existence
6. Identify Key Entities (if data involved)
   → score_input.json structure and evidence file system
7. Run Review Checklist
   → No clarifications needed, implementation boundaries clear
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
When users run the code-score evaluation pipeline and receive a score_input.json file, all file paths listed in the evidence_paths field must point to files that actually exist on the filesystem. Integrating systems should be able to reliably access every referenced evidence file for additional processing or verification.

### Acceptance Scenarios
1. **Given** a repository evaluation has completed, **When** a user examines score_input.json, **Then** every path in evidence_paths field corresponds to an existing file
2. **Given** an integration system processes score_input.json, **When** it attempts to read files from evidence_paths, **Then** all file access operations succeed without file-not-found errors
3. **Given** the evaluation pipeline runs end-to-end, **When** evidence_paths is generated, **Then** it contains only paths for files actually written by the evidence tracking system

### Edge Cases
- What happens when evidence generation partially fails but some files are created?
- How does the system handle permission issues preventing evidence file creation?
- What occurs if disk space runs out during evidence file writing?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST ensure all paths in score_input.json evidence_paths field point to existing files
- **FR-002**: System MUST exclude non-existent placeholder files from evidence_paths output
- **FR-003**: Users MUST be able to access every file referenced in evidence_paths without encountering file-not-found errors
- **FR-004**: System MUST maintain consistency between evidence file generation and path reporting
- **FR-005**: System MUST validate evidence file existence before including paths in final output

### Key Entities *(include if feature involves data)*
- **score_input.json**: JSON output file containing evaluation results and evidence_paths field that lists available evidence files
- **Evidence Files**: Individual files containing detailed evaluation evidence, organized by checklist item and category
- **Evidence Paths Mapping**: Dictionary structure within score_input.json that maps logical evidence categories to actual file system paths

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
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
