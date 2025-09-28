# Feature Specification: LLM-Generated Code Review Reports

**Feature Branch**: `003-step-3-llm`
**Created**: 2025-09-27
**Status**: Draft
**Input**: User description: "Step 3：LLM 评语生成（最小可行增量）

  目标：在已经跑通的"基础度量 + Checklist AI 打分"基础上，新增一个轻量的 LLM 报告生成步骤，让评审只需一条命令就能得到最终可读的说明文档，同时保持改动范围极小、易于迭代。

  ———

  ### 3.A Prompt 设计（T025）

  - 创建 specs/prompts/llm_report.md，写成模板（Markdown），包含以下占位字段：
      - 项目信息：仓库 URL、语言、分析时间。
      - Checklist 总分与类别分（代码质量 / 测试 / 文档）。
      - 每个状态分组的摘要（✅ met, ⚠️ partial, ❌ unmet）。
      - 关键证据（可限制条数，只取高置信度或 Top N）。
      - Warnings / pipeline 提示。
  - 模板示例片段（占位符双花括号）：

    # AI Code Review Judgement Summary

    - Repository: {{repository.url}}
    - Commit: {{repository.commit_sha}}
    - Language: {{repository.primary_language}}
    - Evaluation Date: {{evaluation.timestamp}}

    ## Score Overview
    - Total Score: {{total.score}} / 100 ({{total.percentage}}%)

    ## Highlights
    {{#each met_items}}
    - ✅ {{name}} — {{description}}
    {{/each}}

    ## Improvement Opportunities
    {{#each unmet_items}}
    - ❌ {{name}} — {{description}}
    {{/each}}
  - 在文档内说明：Prompt 消费 score_input.json 的哪些字段、如何裁剪内容（例如只引 3 条证据、防止超长）。

  ———

  ### 3.B LLM Runner 模块（T026）

  - 新建 src/llm/report_generator.py，提供以下核心方法：
      1. load_score_input(path): 读取 score_input.json（可复用 Pydantic 模型）。
      2. build_prompt(score_input, prompt_template): 按模板填充数据（可用简单的 .format()、Jinja2 或手写替换）。
          - 必要时裁剪数据：例如只选前 3 条 evidence_summary，避免上下文过长。
      3. run_gemini(prompt, output_path): 调用 Gemini CLI：

         cmd = [
             \"gemini\",
             \"--approval-mode\", \"yolo\",
             \"-m\", \"gemini-2.5-pro\",
             \"--debug\",
             prompt
         ]
         subprocess.run(cmd, check=True, text=True, capture_output=not verbose)
          - 将 LLM 输出写入 output/final_report.md（或由调用者指定）。
      4. generate_report(score_input_path, output_dir, prompt_path)：综合上述步骤，完成整个流程。
  - 错误处理与可扩展性：
      - 捕捉 subprocess.CalledProcessError，打印 Gemini CLI 的 stderr 以便调试。
      - 留出"自定义命令/模型"参数，方便以后切换（OpenRouter、Claude CLI 等）。

  ———

  ### 3.C CLI 集成与测试（T027）

  1. 命令行接口
      - 在 src/cli/main.py 或单独命令文件中新增命令：

        code-score llm-report ./output/score_input.json \
          --prompt specs/prompts/llm_report.md \
          --output ./output/final_report.md
      - 对原 code-score analyze 命令新增可选 flag --generate-llm-report，直接在分析结束后调用 Runner（先确认 score_input.json 已生产）。
  2. 单元/集成测试
      - 设计一个假响应的测试：mock subprocess.run，验证传入的命令、Prompt 是否包含预期关键信息。
      - 在集成测试里，构造一个小 score_input.json，运行 Runner，断言生成的 final_report.md 含总分、主要项名称等。
  3. 文档更新 / 使用指南
      - 在 README 或 docs 中新增段落，说明：
          - 如何手动运行 code-score llm-report …
          - 常见参数（如关闭生成、切换模板、只打印 Prompt）
          - Gemini CLI 前置安装要求。

  ———"

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature: Add LLM-generated report step to existing metrics + checklist pipeline
2. Extract key concepts from description
   → Actors: Code reviewers, evaluators, hackathon judges
   → Actions: Generate human-readable reports from structured evaluation data
   → Data: score_input.json from checklist evaluation, prompt templates, final reports
   → Constraints: Minimal code changes, iterative approach, single command execution
3. For each unclear aspect:
   → [NEEDS CLARIFICATION: Which LLM providers beyond Gemini should be supported?]
   → [NEEDS CLARIFICATION: Should reports be customizable for different evaluation contexts?]
4. Fill User Scenarios & Testing section
   → Primary flow: Reviewer runs single command to get final readable report
5. Generate Functional Requirements
   → Template-based report generation, LLM integration, CLI extensions
6. Identify Key Entities
   → Report Template, LLM Provider Configuration, Generated Report
7. Run Review Checklist
   → No implementation details exposed to business stakeholders
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing

### Primary User Story
As a code reviewer or hackathon judge, I want to generate a comprehensive, human-readable evaluation report from structured code quality data, so that I can quickly understand project strengths and areas for improvement without manually interpreting raw metrics.

### Acceptance Scenarios
1. **Given** I have completed code quality analysis and checklist evaluation for a repository, **When** I run the report generation command, **Then** I receive a well-formatted final report that summarizes scores, highlights key strengths, and identifies improvement opportunities
2. **Given** I have custom evaluation criteria or reporting needs, **When** I specify a custom prompt template, **Then** the system uses my template instead of the default one
3. **Given** I want to integrate report generation into my automated workflow, **When** I run the analysis command with the report generation flag, **Then** the system automatically produces both the evaluation data and the final report in a single execution

### Edge Cases
- What happens when the LLM service is unavailable or returns an error?
- How does the system handle very large evaluation datasets that might exceed LLM context limits?
- What occurs when required evaluation data is missing or incomplete?
- How does the system behave when custom prompt templates contain invalid placeholders?

## Requirements

### Functional Requirements
- **FR-001**: System MUST generate human-readable evaluation reports from structured checklist evaluation data
- **FR-002**: System MUST support template-based report customization with predefined placeholder fields
- **FR-003**: Users MUST be able to generate reports as a standalone command using existing evaluation data
- **FR-004**: System MUST integrate report generation as an optional step in the main analysis pipeline
- **FR-006**: System MUST truncate or summarize evaluation data to prevent LLM context overflow
- **FR-007**: System MUST handle LLM service errors gracefully and provide meaningful error messages
- **FR-008**: System MUST support [NEEDS CLARIFICATION: multiple LLM providers - should this be limited to Gemini or include others like OpenAI, Claude, etc.?]
- **FR-009**: Generated reports MUST include project metadata, score summaries, key findings, and improvement recommendations
- **FR-010**: System MUST validate that required evaluation data exists before attempting report generation
- **FR-011**: Users MUST be able to specify custom output paths for generated reports
- **FR-012**: System MUST [NEEDS CLARIFICATION: what level of report customization should be supported - just templates or also output format options?]

### Key Entities
- **Report Template**: Markdown-format template with placeholder fields for dynamic content injection, including project metadata, scores, evidence summaries, and recommendations
- **LLM Provider Configuration**: Settings and parameters for connecting to external language models, including model selection, API endpoints, and request formatting
- **Generated Report**: Final human-readable document containing evaluation summary, project assessment, and actionable recommendations based on code quality analysis

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
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
- [ ] Review checklist passed

---
