# Target Repository Scoring Transparency

## Why This Document Exists
Code Score reviews external（“target”）仓库，并依据固定的检查清单输出得分。本文件列出当前所有指标、采集到的证据类型，以及默认使用的工具链，帮助仓库维护者提前对齐质量要求。

## 当前评分维度与指标
| 维度 | 指标 | 分值 | 证据期望 | 默认工具／来源* | 当前实现状态（2025-10-09） |
|------|------|------|-----------|----------------|----------------------------|
| 代码质量 | Static Linting Passed | 15 | 最近一次 lint 运行无阻断问题 | Python: `ruff` → `flake8` 回退；JS: `npx eslint`；Go: `golangci-lint`；Java: `mvn checkstyle` / `gradle check` | ✓ `python_tools.run_linting`、`javascript_tools.run_linting`、`golang_tools.run_linting`、`java_tools.run_linting` 已接入 |
| 代码质量 | Build/Package Success | 10 | 构建或打包命令成功执行 | Python: `uv build` → `python -m build` 回退；JS: `npm run build` / `yarn build`；Go: `go build ./...`；Java: `mvn compile` / `gradle compileJava` | ✓ 所有语言 `run_build()` 已实现并接入 metrics；Python/JS/Go/Java 全部支持，结果写入 `build_success` 和 `build_details` 字段 |
| 代码质量 | Dependency Security Scan | 8 | 依赖审计无未解决的高危漏洞 | Python: `pip-audit`；JS: `npm audit --json`；Go: `osv-scanner`；Java: OWASP Dependency Check | ✓ 各语言 `run_security_audit` 已写入执行逻辑；缺工具时返回 `tool_used=none` |
| 代码质量 | Core Module Documentation | 7 | README 描述架构、目录、入口 | README 解析 | ✓ `tool_executor._analyze_documentation` 产出，结果落在 `readme_quality_score` 等字段 |
| 测试 | Automated Test Execution | 15 | 自动化测试执行并通过 | Python: `pytest`；JS: `npm test`（解析 Jest/Mocha）；Go: `go test -json`；Java: `mvn test` / `gradle test` | ✓ 相应 `run_testing` 已接入，记录 `tests_run/tests_passed` 等 |
| 测试 | Coverage or Core Test Evidence | 10 | 覆盖率 ≥60%，或提交关键测试证据 | 覆盖率报告（`pytest --cov`、`jest --coverage`、`go test -cover` 等） | △ 当前收集逻辑未自动生成 `coverage_report`，需用户提供或后续补采集器 |
| 测试 | Integration/Smoke Test Scripts | 6 | 提供集成/冒烟测试脚本及运行结果 | 测试框架运行日志 | △ 依赖 `test_execution` 中的测试数量判断，尚未区分冒烟/单元的语义 |
| 测试 | Test Result Documentation | 4 | 提供日志或 CI link 证明测试通过 | Pipeline execution 日志 | △ 仅记录 `tests_passed`、`execution.errors`，未来可拓展附加产物上报 |
| 文档 | README Quick Start Guide | 12 | README 说明概览、安装、命令、样例 | README 解析 | ✓ README 解析器产出 `setup_instructions/usage_examples` |
| 文档 | Configuration & Environment Setup | 7 | 标注必要环境变量或配置文件 | README / `.env.example` 检查 | ✓ 同 README 解析逻辑覆盖 |
| 文档 | API/Interface Usage Documentation | 6 | 提供 API/CLI/UI 入口与示例 | README/API 文档检查 | ✓ README/`docs/` 目录存在即记为可用；可继续细化判定 |

*流水线会按语言检测可用工具；当工具缺失或运行失败时，该指标可能按“部分达成”或“未达成”计分。

状态图例：✓ 已接入；△ 部分落地或存在明显缺口；✗ 尚未实现。

## 证据采集流程
- **Metrics Pipeline**（`src/metrics/submission_pipeline.py`）：克隆目标仓库、识别语言，并通过 `tool_runners/` 调度 linter、测试、审计工具，将结果汇总到 `output/submission.json`。
- **Checklist Evaluator**（`src/metrics/scoring_mapper.py`、`checklist_evaluator.py`）：读取 metrics 输出，依据 `specs/contracts/checklist_mapping.yaml` 中的判定条件生成评分。
- **LLM Reports**（`src/llm/`）：可选的叙事报告，只消费既有分数，不新增评分逻辑。

## 仓库自检指南
1. **Lint & Format**：在本地执行适配工具（如 `ruff check`、`npm run lint`、`golangci-lint run`），确保阻断级问题为 0。
2. **保持可构建**：维护清晰的构建脚本，在干净环境验证命令成功运行（`uv build`、`npm ci && npm run build`、`mvn verify`）。
3. **自动化测试**：保证指令无需人工输入即可跑通，默认目标是 ≥60% 行覆盖；若不足请在文档中说明原因与补救计划。
4. **文档同步架构**：定期更新 README，覆盖项目概览、目录说明、安装步骤、快速起步命令、常用配置。
5. **安全扫描结果可复现**：在 CI 中保存 `pip-audit`、`npm audit` 等输出并记录处置动作，避免高危漏洞累积。

## 指标扩展与优化建议
- **新增指标**：在 `specs/contracts/checklist_mapping.yaml` 增补条目及必需字段，同时实现相应的采集器（`src/metrics/tool_runners/`）。
- **自定义工具链**：如需支持自定义扫描器，可在工具运行器中添加适配器，输出兼容的 JSON 片段。
- **文档透明度**：每次扩展评分标准时同步更新本文件与 `README.md`，让目标仓库维护者随时了解打分依据。
- **后续 roadmap**：考虑在 `docs/examples/` 发布示例 `output/submission.json` 与已评分报告；提供 GitHub Actions / GitLab CI 模版；为每个指标附加推荐修复资源，帮助用户快速闭环。
- **实现补强优先级**：✓ 已完成 Python/JS/Go/Java 四语言 `run_build` 检测并写入 metrics；下一步重点：补齐自动覆盖率采集，区分冒烟/单元测试语义，使表格中剩余"△"逐步转为"✓"。
