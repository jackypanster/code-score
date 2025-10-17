# Implementation Plan: Provider模型统一切换至llm CLI

**Branch**: `006-provider-llm-cli` | **Date**: 2025-10-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-provider-llm-cli/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded spec.md successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ All clarifications resolved via 2025-10-17 session
   → Detect Project Type: Single Python project
   → Set Structure Decision: Single project (src/, tests/)
3. Fill the Constitution Check section
   → ✅ Evaluated against Code Score Constitution v1.0.0
4. Evaluate Constitution Check section
   → ✅ No violations detected
   → Update Progress Tracking: Initial Constitution Check PASS
5. Execute Phase 0 → research.md
   → ✅ All technical decisions documented
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ Design artifacts generated
7. Re-evaluate Constitution Check section
   → ✅ Post-design check PASS (KISS principle maintained)
   → Update Progress Tracking: Post-Design Constitution Check PASS
8. Plan Phase 2 → Task generation approach described
9. ✅ STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 9. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

**Primary Requirement**: 将LLM provider模型从Gemini硬编码切换到统一的llm CLI接口，支持DeepSeek provider，完全移除Gemini专用代码。

**Technical Approach**:
1. 移除LLMProviderConfig中的Gemini硬编码限制
2. 重构build_cli_command方法以生成标准llm CLI命令（`llm -m <model> "<prompt>"`）
3. 更新默认配置使用DeepSeek（deepseek-coder/deepseek-chat）
4. 增强环境验证逻辑（llm CLI可用性、context window检查）
5. 清理所有Gemini特定测试和文档引用

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- pydantic>=2.5.0 (配置模型)
- jinja2>=3.1.6 (模板系统，间接依赖)
- subprocess (标准库，CLI调用)
- llm CLI (外部工具，需在PATH中)

**Storage**: N/A (无持久化存储需求)
**Testing**: pytest>=8.4.2 (单元测试 + 集成测试 + contract测试)
**Target Platform**: macOS/Linux (开发和CI环境，支持llm CLI)
**Project Type**: Single Python project (src/, tests/)

**Performance Goals**:
- llm CLI调用延迟: <2s (环境验证)
- 配置验证延迟: <100ms
- Context window检查: <10ms (token估算)

**Constraints**:
- Fail-fast原则: 所有错误必须立即抛出异常
- 无自动降级: Provider失败不尝试fallback
- 单线程执行: MVP不支持并发调用
- Token估算精度: ±10% (基于4 chars/token启发式)

**Scale/Scope**:
- 影响文件: ~6个Python模块
- 需删除代码: ~200行Gemini特定逻辑
- 新增代码: ~150行（环境验证、context window检查）
- 测试用例: ~15个单元测试，5个集成测试

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. UV-Based Dependency Management
✅ **PASS**: 项目使用uv管理依赖（pyproject.toml + dependency-groups）
- 所有Python依赖通过uv sync安装
- llm CLI作为外部工具，通过系统PATH访问（符合CLAUDE.md中的toolchain validation模式）

### II. KISS Principle (Keep It Simple, Stupid)
✅ **PASS**: 设计遵循简洁原则
- **移除抽象层**: 删除Gemini专用的provider验证和命令拼装逻辑
- **统一接口**: 所有LLM调用通过标准llm CLI接口（`llm -m <model> "<prompt>"`）
- **Fail-fast**: 所有错误立即抛出异常，无复杂错误恢复逻辑
- **无过度工程**: 不实现provider降级、自动重试、请求队列等复杂机制

**简化证据**:
- 删除validate_provider_name中的硬编码白名单检查（allowed_providers = ["gemini"]）
- 将get_default_configs从provider-specific逻辑简化为统一的llm CLI配置
- Context window验证使用简单的字符长度估算（4 chars/token），避免引入额外的tokenizer依赖

### III. Transparent Change Communication
✅ **PASS**: 变更透明且有据可查
- 所有16个功能需求（FR-001至FR-016）明确定义了变更内容
- Clarifications section记录了5个关键决策及其理由
- 代码变更将包含详细注释说明移除Gemini的原因和llm CLI的选择依据

## Project Structure

### Documentation (this feature)
```
specs/006-provider-llm-cli/
├── spec.md              # Feature specification (✅ complete)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (技术决策文档)
├── data-model.md        # Phase 1 output (配置模型设计)
├── quickstart.md        # Phase 1 output (验证步骤)
├── contracts/           # Phase 1 output (API约束规范)
│   ├── llm_provider_config_schema.json
│   └── cli_command_format.md
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/
├── llm/
│   ├── models/
│   │   ├── llm_provider_config.py    # ✏️ MODIFY: 移除Gemini限制，添加DeepSeek默认配置
│   │   ├── generated_report.py       # ➖ NO CHANGE
│   │   └── report_template.py        # ➖ NO CHANGE
│   ├── report_generator.py          # ✏️ MODIFY: 更新错误消息，移除Gemini引用
│   ├── prompt_builder.py             # ➖ NO CHANGE
│   └── template_loader.py            # ➖ NO CHANGE
└── cli/
    └── llm_report.py                 # ✏️ MODIFY: 添加dry-run模式支持

tests/
├── unit/
│   └── llm/
│       ├── test_llm_provider_config.py   # ✏️ MODIFY: 移除Gemini测试，添加DeepSeek测试
│       └── test_report_generator.py      # ✏️ MODIFY: 更新错误场景测试
├── integration/
│   └── llm/
│       └── test_llm_workflow.py          # ✏️ MODIFY: DeepSeek端到端测试（替代Gemini）
└── contract/
    └── test_llm_provider_schema.py       # ✏️ MODIFY: 验证llm CLI命令格式约束
```

**Structure Decision**:
采用单一Python项目结构（Code Score现有模式）。核心变更集中在`src/llm/models/llm_provider_config.py`（~80行修改）和相关测试文件。不引入新的模块或包，保持现有架构的简洁性。

## Phase 0: Outline & Research

### Unknowns & Research Tasks

**已通过clarification session解决的不确定性**:
1. ✅ DeepSeek调用方式 → 标准llm CLI接口（`llm -m deepseek-coder/deepseek-chat`）
2. ✅ Gemini处理策略 → 完全移除
3. ✅ 错误处理策略 → Fail-fast，无自动重试
4. ✅ Prompt长度处理 → 直接报错，无截断
5. ✅ 批量场景 → 不在MVP范围

### Research Findings (详见research.md)

1. **llm CLI标准接口规范**:
   - 命令格式: `llm -m <model_name> "<prompt>"`
   - 环境变量: 各provider通过llm CLI统一管理（如DEEPSEEK_API_KEY）
   - 版本检查: `llm --version` (最低兼容版本: 0.15+)
   - 参数传递: 支持--temperature, --max-tokens等通用参数

2. **DeepSeek模型配置**:
   - 推荐模型: `deepseek-coder` (代码生成场景) 或 `deepseek-chat` (通用对话)
   - Context window: 8192 tokens (需在配置中明确)
   - 默认temperature: 0.1 (与原Gemini配置保持一致)
   - 超时建议: 90秒 (与原Gemini配置保持一致)

3. **Token估算方法**:
   - 简单启发式: 4 characters ≈ 1 token (英文文本)
   - 中文文本: 2 characters ≈ 1 token
   - 评估场景: score_input.json通常2000-5000 tokens，远低于8192上限
   - 安全边际: 在80%上限时发出警告 (~6500 tokens)

4. **环境验证最佳实践**:
   - CLI可用性: `shutil.which('llm')` + `subprocess.run(['llm', '--version'])`
   - 环境变量: `os.getenv('DEEPSEEK_API_KEY')` 非空检查
   - 提前失败: 在generate_report入口立即验证，避免中途失败

**Output**: research.md (已整合上述findings)

## Phase 1: Design & Contracts

### 1. Data Model (data-model.md)

#### Entity: LLMProviderConfig (Modified)

**核心字段（保留）**:
- `provider_name: str` - 移除["gemini"]白名单限制
- `cli_command: list[str]` - 默认改为["llm"]
- `model_name: str` - DeepSeek默认: "deepseek-coder"
- `timeout_seconds: int` - 保持90秒
- `temperature: float` - 保持0.1
- `environment_variables: dict[str, str]` - 改为{"DEEPSEEK_API_KEY": "required"}
- `additional_args: dict[str, str | int | float | bool | None]` - 移除Gemini特定参数（--approval-mode yolo, --debug）
- `context_window: int` - 改为8192

**新增字段**:
无（现有字段足以支持llm CLI）

**删除字段**:
无（保持向后兼容的配置模型结构）

**删除方法**:
- `get_provider_specific_limits()` - Gemini特定逻辑，不再需要

**修改方法**:
- `validate_provider_name()`: 移除allowed_providers白名单
- `build_cli_command()`: 生成`llm -m <model> "<prompt>"`格式
- `get_default_configs()`: DeepSeek替代Gemini

**新增方法**:
- `estimate_prompt_tokens(prompt: str) -> int`: 使用4 chars/token启发式估算
- `validate_prompt_length(prompt: str) -> None`: 检查是否超出context_window，超出则抛异常

#### Entity: EnvironmentValidation (New)

**用途**: 统一的环境验证结果对象

**字段**:
- `llm_cli_available: bool` - llm CLI是否在PATH中
- `llm_cli_version: str | None` - 检测到的版本号
- `required_env_vars: dict[str, bool]` - 环境变量检查结果 {变量名: 是否设置}
- `validation_errors: list[str]` - 验证失败的错误消息列表

**方法**:
- `is_valid() -> bool`: 所有检查通过返回True
- `get_error_summary() -> str`: 返回格式化的错误摘要

### 2. API Contracts (contracts/)

#### Contract 1: llm CLI命令格式约束 (cli_command_format.md)

```markdown
# llm CLI命令格式约束

## 基础格式
llm -m <model_name> "<prompt>"

## 参数规范
- 必需参数: -m <model_name> (模型标识符)
- 可选参数:
  - --temperature <float> (0.0-2.0)
  - --max-tokens <int> (>0)
  - 其他provider特定参数通过llm CLI自动处理

## 示例
```bash
# 基础调用
llm -m deepseek-coder "Explain this code"

# 带参数调用
llm -m deepseek-chat --temperature 0.1 "Generate a report"
```

## 错误场景
- 缺少-m参数: ValueError "Model name required"
- 空prompt: ValueError "Prompt cannot be empty"
- 无效参数格式: llm CLI返回退出码1
```

#### Contract 2: LLMProviderConfig Schema (llm_provider_config_schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LLMProviderConfig",
  "type": "object",
  "required": ["provider_name", "cli_command"],
  "properties": {
    "provider_name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "description": "Provider identifier (no whitelist restriction)"
    },
    "cli_command": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1,
      "description": "Base CLI command (e.g., ['llm'])"
    },
    "model_name": {
      "type": "string",
      "description": "Model identifier for -m parameter"
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 10,
      "maximum": 300,
      "default": 90
    },
    "temperature": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 2.0
    },
    "environment_variables": {
      "type": "object",
      "patternProperties": {
        "^[A-Z][A-Z0-9_]*$": {"type": "string"}
      }
    },
    "context_window": {
      "type": "integer",
      "minimum": 1,
      "description": "Maximum context window in tokens"
    }
  }
}
```

### 3. Contract Tests (在tests/contract/创建)

```python
# tests/contract/test_llm_cli_command_format.py
def test_deepseek_command_format():
    """验证DeepSeek命令符合llm CLI标准格式"""
    config = LLMProviderConfig.get_default_configs()["deepseek"]
    command = config.build_cli_command("test prompt")

    assert command[0] == "llm"
    assert "-m" in command
    assert "deepseek-coder" in command or "deepseek-chat" in command
    assert "test prompt" in command

def test_no_gemini_specific_args():
    """验证不包含Gemini特定参数"""
    config = LLMProviderConfig.get_default_configs()["deepseek"]
    command = config.build_cli_command("test")

    # 不应包含Gemini特定参数
    assert "--approval-mode" not in command
    assert "--debug" not in " ".join(command)
```

### 4. Integration Test Scenarios (从user stories提取)

**Scenario 1: DeepSeek默认配置调用** (对应Acceptance Scenario 1)
```python
def test_default_deepseek_report_generation():
    """
    Given: 系统使用默认配置
    When: 调用generate_report()
    Then: 使用llm CLI + DeepSeek生成报告
    """
    generator = ReportGenerator()
    result = generator.generate_report(
        score_input_path="fixtures/sample_score_input.json",
        provider="deepseek"
    )

    assert result['success'] is True
    assert "deepseek" in result['provider_metadata']['provider_name']
```

**Scenario 2: 环境变量缺失检测** (对应Acceptance Scenario 4)
```python
def test_missing_env_var_detection():
    """
    Given: DEEPSEEK_API_KEY未设置
    When: 调用validate_prerequisites()
    Then: 明确报告缺失的环境变量
    """
    # Mock os.getenv to return None
    with patch.dict(os.environ, {}, clear=True):
        generator = ReportGenerator()
        with pytest.raises(LLMProviderError, match="DEEPSEEK_API_KEY"):
            generator.generate_report(...)
```

**Scenario 3: Dry-run模式** (对应Acceptance Scenario 5)
```python
def test_dry_run_mode():
    """
    Given: 启用dry-run模式
    When: 执行报告生成
    Then: 输出命令但不实际执行
    """
    generator = ReportGenerator()
    command = generator.dry_run_generate_report(
        score_input_path="fixtures/sample_score_input.json"
    )

    assert command.startswith("llm -m deepseek-")
    assert "sample_score_input.json" in command
```

### 5. Update CLAUDE.md (Agent Context)

执行更新脚本:
```bash
.specify/scripts/bash/update-agent-context.sh claude
```

**新增内容** (追加到LLM Report Generation Details section):
```markdown
### LLM Provider Migration (006-provider-llm-cli)
**Current Status**: llm-deepseek分支切换至统一llm CLI接口

**Key Changes**:
- Provider: Gemini → DeepSeek (deepseek-coder/deepseek-chat)
- CLI Interface: 统一使用`llm -m <model> "<prompt>"`格式
- Environment: GEMINI_API_KEY → DEEPSEEK_API_KEY
- Error Handling: Fail-fast策略，无自动降级
- Context Window: 1048576 tokens (Gemini) → 8192 tokens (DeepSeek)

**Removed**:
- Gemini专用provider验证逻辑
- --approval-mode yolo, --debug等Gemini特定参数
- get_provider_specific_limits()方法

**Added**:
- estimate_prompt_tokens()方法（4 chars/token启发式）
- validate_prompt_length()方法（超出context window报错）
- Dry-run模式支持（--dry-run flag）
```

**Output**: CLAUDE.md已更新（保留原有内容，仅追加新特性说明）

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

### Task Generation Strategy

**从Phase 1设计文档生成任务**:

1. **Contract Tests** (从contracts/生成):
   - Task T001 [P]: 创建test_llm_cli_command_format.py（验证命令格式）
   - Task T002 [P]: 创建test_llm_provider_schema.py（验证配置schema）

2. **Data Model Modification** (从data-model.md生成):
   - Task T003: 移除LLMProviderConfig.validate_provider_name中的硬编码白名单
   - Task T004: 重构build_cli_command生成llm CLI标准格式
   - Task T005: 更新get_default_configs使用DeepSeek配置
   - Task T006 [P]: 添加estimate_prompt_tokens方法
   - Task T007 [P]: 添加validate_prompt_length方法

3. **Environment Validation** (新功能):
   - Task T008: 创建EnvironmentValidation模型
   - Task T009: 在ReportGenerator添加llm CLI可用性检查
   - Task T010: 在ReportGenerator添加环境变量验证逻辑

4. **Error Handling Enhancement** (从FR-013, FR-014):
   - Task T011: 添加context window超限检测
   - Task T012: 更新错误消息移除Gemini引用

5. **Gemini Code Cleanup** (从FR-011):
   - Task T013: 删除Gemini相关单元测试
   - Task T014: 删除Gemini相关集成测试
   - Task T015: 更新CLAUDE.md文档
   - Task T016: 更新README.md移除Gemini引用

6. **Integration Tests** (从quickstart.md和user stories):
   - Task T017: test_default_deepseek_report_generation（验收场景1）
   - Task T018: test_missing_env_var_detection（验收场景4）
   - Task T019: test_dry_run_mode（验收场景5）
   - Task T020: test_context_window_exceeded（边缘案例3）

7. **CLI Enhancement** (从FR-006):
   - Task T021: 在llm_report.py添加--dry-run参数
   - Task T022: 实现dry_run_generate_report方法

### Ordering Strategy

**TDD Order** (测试优先):
1. Contract tests (T001-T002) - 定义约束
2. Unit tests for new methods (T006, T007, T011) - 失败的测试
3. Implementation (T003-T005, T008-T010) - 让测试通过
4. Integration tests (T017-T020) - 端到端验证
5. Cleanup (T013-T016) - 删除遗留代码
6. CLI enhancement (T021-T022) - 附加功能

**Dependency Order** (模型 → 服务 → CLI):
- T003-T007 (模型修改) 必须在 T009-T010 (服务层验证) 之前
- T008 (EnvironmentValidation模型) 必须在 T009 (使用它的逻辑) 之前
- T001-T022 所有任务必须在 T013-T016 (cleanup) 之前完成

**Parallel Execution Marks**:
- [P] T001, T002: Contract tests独立可并行
- [P] T006, T007: 新增方法独立可并行
- [P] T013-T015: 删除任务独立可并行（但必须在功能完成后）

### Estimated Output

**任务数量**: 22个有序任务
**预估工时**:
- Phase 0-1 (已完成): 4小时
- Phase 2 (任务生成): 0.5小时
- Phase 3 (实现): 8小时
- Phase 4 (验证): 2小时
- **Total**: 14.5小时

**Critical Path**: T003 → T004 → T005 → T009 → T017 (核心provider切换链路)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md with 22 ordered tasks)
**Phase 4**: Implementation (execute tasks.md following fail-fast and KISS principles)
**Phase 5**: Validation (run quickstart.md, verify all 16 FRs, performance validation)

### Validation Checklist (Phase 5)
- [ ] FR-001: Gemini硬编码限制已移除
- [ ] FR-003: DeepSeek默认配置正常工作
- [ ] FR-007: llm CLI命令格式符合标准
- [ ] FR-009: llm CLI可用性检测正常
- [ ] FR-011: 所有Gemini代码已清理
- [ ] FR-013: Fail-fast错误处理正常
- [ ] FR-014: Context window检测正常
- [ ] 所有22个任务测试通过
- [ ] quickstart.md中的验证步骤全部通过
- [ ] 无性能回归（llm CLI调用延迟<2s）

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

**说明**: 本设计无宪法违规。通过移除Gemini特定逻辑实际上**降低了复杂度**，符合KISS原则。

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (UV依赖管理、KISS原则、透明变更)
- [x] Post-Design Constitution Check: PASS (简化provider逻辑，移除抽象层)
- [x] All NEEDS CLARIFICATION resolved (via 2025-10-17 clarification session)
- [x] Complexity deviations documented (无违规，表格标记为N/A)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
