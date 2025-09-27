# AI Code Review Judgement MVP 架构设计

## 目标与范围
- 面向 2 周黑客松场景，提供端到端自动化的静态评分能力，完全无需人工干预。
- MVP 聚焦于跑通“提交材料 → 自动检查 → LLM 评分 → 生成报告”闭环，满足首轮横向筛选需求。
- 所有组件选用成熟、易获取的开源或 SaaS 服务，优先无状态、易部署方案，便于快速上线与迭代。
- 明确“不重复造轮子”原则：尽量复用 GitHub Actions、现有 Mac/Ubuntu 环境等基础设施，减少额外平台搭建。

## 功能流概览
1. **材料采集层**：从参赛代码仓库拉取代码、README、测试日志、CI 结果等 artifacts。
2. **基础度量层**：按语言触发预置 `lint`/`audit`/`test` 脚本，收集静态检查、构建、测试、覆盖率与依赖扫描结果。
3. **数据整理层**：把上述产出整理为标准化 JSON/Markdown 片段，并附 checklist 项对应的原始证据引用。
4. **LLM 评分层**：调用高上下文模型（首选 Gemini 2.5 Pro 或等效）执行 checklist 打分 Prompt，输出各项得分、证据片段与置信度。
5. **报告生成层**：汇总 11 个检查项得分，生成 100 分制总分与结构化报告（JSON + 可选 Markdown 摘要），并推送至指定存储/通知通道。

## 组件划分
- **Repo Ingest Service**：负责克隆指定提交、管理工作目录、缓存依赖。MVP 阶段使用 shell 脚本 + Git 工具即可，不额外引入容器调度。
- **Metrics Runner**：封装语言特定脚本（ESLint、SpotBugs、pytest、golangci-lint 等），基于 GitHub Actions 托管 runner 或本地 Mac/Ubuntu 环境直接执行，产出标准化日志。
- **Artifact Collector**：解析日志、测试结果与 README，提取 checklist 所需字段，存储为 `submission.jsonl`。
- **LLM Scoring Engine**：调用 LLM API，执行固定 Prompt 模板，对 11 项逐条打分，产生 `scorecard.json`。
- **Report Publisher**：合成总分、生成 Markdown、JSON 报告，默认保存在任务工作目录并上传到 GitHub Actions Artifact 或本地归档目录，可选触发 Webhook 通知。
- **Orchestrator**：首选 GitHub Actions Workflow；若需离线运行，可用一段简单的 bash/python 脚本串联步骤，避免部署额外调度系统。

## 技术选型（MVP 建议）
- 运行环境：GitHub Actions 托管 runner（Ubuntu）或本地 Mac/Ubuntu 终端，复用原生系统工具即可。
- 语言支持：Node.js 20、Java 17、Python 3.11、Go 1.21，直接通过脚本安装或使用 GitHub Actions 官方套件，无需自建镜像。
- 日志/存储：默认写入工作目录并随任务归档，可直接利用 GitHub Actions Artifacts 或本地文件夹；MVP 阶段不引入额外对象存储。
- LLM 服务：优先选用 Google Gemini 2.5 Pro，通过 OpenRouter API 或官方 CLI（如 `gemini`、`claude` CLI）调用；保持 KISS，能直接访问的方案优先。
- 指令编排：脚本入口 `./scripts/run_judgement.sh <repo> <commit>`，串联所有子模块。

## 数据格式
- `metrics/<check>.json`：每项基础度量的原始数据（例如 `lint.json`, `coverage.json`）。
- `submission.json`：包含项目信息、基础指标摘要、证据路径。
- `scorecard.json`：LLM 输出的逐项得分、置信度、引用证据。
- `report.md` / `report.json`：汇总报告，供评审面板或自动通知使用。

## 安全与权限
- 仅拉取公开仓库或授权的 Fork，使用最小权限访问令牌。
- 依赖扫描报告仅记录高风险条目摘要，避免泄露敏感依赖版本。
- LLM 调用前对输入做脱敏（例如截取访问凭据、密钥）。

## 可观察性
- Metrics Runner 与 LLM Scoring Engine 的 stdout/stderr 直接保留在 GitHub Actions 日志或本地终端输出中，便于快速排查。
- 关键指标：处理成功率、平均耗时、LLM 置信度分布、Checklist 各项平均分，可先以 CSV/Markdown 形式记录在报告中。

## 迭代展望
- 扩展更多语言或工具链（Rust、C# 等）。
- 引入语义检索、跨版本对比、性能/安全深度分析。
- 打通人工复核工作台，与后续评委流程无缝衔接（非 MVP 范围）。
