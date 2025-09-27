# Feature Specification: Checklist Mapping & Scoring Input MVP

**Feature Branch**: `002-git-log-docs`
**Created**: 2025-09-27
**Status**: Draft
**Input**: User description: "通过git log和项目文档 @docs/ 回顾我们第一步已经落地的工作，然后开始第二步：第二步规划：Checklist 映射与评分输入 MVP

  - 目标
    基于第一步生成的原始度量结果，落地"自动评审打分清单（第一稿）"的判定逻辑，产出结构化 score_input.json，供后续 LLM 评分或直接生成首版分值。这部分工作聚焦在 docs/ai-code-review-judgement.md 的 11 个检查项和功能规格里的"Checklist 映射"阶段。
  - 拆解任务
      1. 规则引擎骨架：新增 ChecklistEvaluator 模块，读取 submission.json 中的 lint/test/audit/README 等指标，逐项产出 status ∈ {met, partial, unmet} 和原始证据引用。
      2. 数值换算与输出格式：根据文档设定的分值（15/10/...），把状态映射为分数（100%、50%、0%），生成统一的 score_input.json（含 11 条记录、总分占位、证据路径），并将 Markdown 摘要写入 output/report.md 尾部，方便人工验证。
      3. 回归验证：以 AIGCInnovatorSpace/code-walker 为示例运行，确认各检查项都有判定结果；再挑选至少一个不同语言的公开仓库快速跑一遍，验证多语言基础指标可映射。
      4. 自动化测试：编写最小单元/集成测试，覆盖典型情况与"部分满足"分支，确保规则可维护、方便迭代。
  - 输出物
      - 新的 score_input.json 文件（机器可读）
      - 更新的 Markdown 报告节（人工检视）
      - 相关实现文档/README 补充使用说明与扩展指南

  完成后，第一个 MVP 阶段就拥有"材料→基础度量→Checklist 得分输入"的闭环，为第三步（调用 LLM 生成解释型报告）打基础。"

## Execution Flow (main)
```
1. Parse user description from Input
   → Identified: checklist evaluation system building on existing metrics collection
2. Extract key concepts from description
   → Actors: hackathon organizers, repository analyzers, LLM scoring system
   → Actions: evaluate checklist items, map metrics to scores, generate structured output
   → Data: submission.json metrics, 11-item checklist, score_input.json output
   → Constraints: 100-point scoring system, three-tier status mapping (met/partial/unmet)
3. For each unclear aspect:
   → Score calculation algorithms defined in ai-code-review-judgement.md
4. Fill User Scenarios & Testing section
   → Clear user flow: metrics → evaluation → structured scoring input
5. Generate Functional Requirements
   → All requirements testable against existing checklist criteria
6. Identify Key Entities (scoring data models)
7. Run Review Checklist
   → No implementation details, focused on evaluation logic and output format
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT evaluation logic is needed and WHY
- ❌ Avoid HOW to implement (no specific code architecture, class names)
- 👥 Written for stakeholders who need automated code quality evaluation

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

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a hackathon organizer using the automated code review system, I need to convert raw repository metrics into structured scoring input that can be processed by LLM evaluation or direct scoring algorithms, so that I can fairly and consistently evaluate multiple participant repositories according to the 11-item quality checklist.

### Acceptance Scenarios
1. **Given** a `submission.json` file with repository metrics from the first phase, **When** the checklist evaluator processes the metrics, **Then** the system generates a `score_input.json` file with status evaluation (met/partial/unmet) for all 11 checklist items
2. **Given** metrics indicating successful linting and build completion, **When** the evaluator maps these to checklist items, **Then** code quality items receive appropriate status scores with evidence references
3. **Given** incomplete or missing test coverage data, **When** the evaluator processes testing metrics, **Then** affected checklist items are marked as "partial" or "unmet" with clear reasoning
4. **Given** a multi-language repository analysis, **When** the system processes language-specific metrics, **Then** the scoring logic adapts appropriately while maintaining consistent evaluation criteria

### Edge Cases
- What happens when submission.json contains null or missing metric sections?
- How does the system handle repositories with no README or documentation?
- What occurs when security audit tools find zero vulnerabilities vs. tools not being available?
- How does the evaluator distinguish between test failures and tests not being run?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST read metrics data from existing `submission.json` format generated by the first phase
- **FR-002**: System MUST evaluate each of the 11 checklist items defined in `ai-code-review-judgement.md` against available metrics
- **FR-003**: System MUST assign status values of "met", "partial", or "unmet" to each checklist item based on evaluation logic
- **FR-004**: System MUST generate structured `score_input.json` output containing all 11 checklist evaluations with evidence references
- **FR-005**: System MUST apply the defined point mapping (15/10/8/7/6/4 points) from the checklist specification
- **FR-006**: System MUST include evidence paths and reasoning for each checklist item evaluation
- **FR-007**: System MUST append evaluation summary to `output/report.md` in human-readable format for verification
- **FR-008**: System MUST handle missing or incomplete metrics gracefully without failing the entire evaluation
- **FR-009**: System MUST support multi-language repository evaluation using language-appropriate metric mappings
- **FR-010**: System MUST validate against known test repositories (code-walker and additional multi-language examples)
- **FR-011**: System MUST provide total score calculation and percentage breakdown by evaluation category
- **FR-012**: System MUST maintain evaluation logic that can be extended or modified for future checklist iterations

### Key Entities *(include if feature involves data)*
- **ChecklistItem**: Represents one of 11 evaluation criteria with dimension (code quality/testing/documentation), point value, evaluation status, and evidence references
- **EvaluationResult**: Container for complete checklist evaluation including item-level results, total score, category breakdowns, and execution metadata
- **ScoreInput**: Structured output format containing evaluation results, evidence paths, and metadata for downstream LLM processing or direct scoring
- **MetricsMapping**: Logic for translating raw submission.json metrics into checklist item evaluations, handling language-specific variations and missing data scenarios
- **EvidenceReference**: Specific citations linking checklist evaluations back to source metrics data, file paths, or tool outputs for auditability

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
