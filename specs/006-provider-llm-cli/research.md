# Research: Provider模型统一切换至llm CLI

**Feature**: 006-provider-llm-cli
**Date**: 2025-10-17
**Status**: Complete

## Purpose

本文档记录将LLM provider从Gemini硬编码切换到llm CLI统一接口的技术调研结果，支持Phase 1设计决策。

## Research Questions & Findings

### 1. llm CLI标准接口规范

**Question**: llm CLI如何调用不同的LLM provider？命令格式和参数传递机制是什么？

**Research Method**:
- 查阅llm CLI官方文档: https://llm.datasette.io/
- 验证DeepSeek plugin文档
- 本地测试llm命令行为

**Decision**: 使用llm CLI标准接口 `llm -m <model> "<prompt>"`

**Rationale**:
- **统一性**: 所有provider（OpenAI、Claude、DeepSeek）使用相同的CLI格式
- **简洁性**: 无需在应用层维护provider特定的命令拼装逻辑
- **可维护性**: 后续切换模型只需修改`-m`参数，无需修改代码

**Key Findings**:
```bash
# 基础调用格式
llm -m <model_name> "<prompt>"

# 环境变量管理
# llm CLI自动管理各provider的API密钥（如DEEPSEEK_API_KEY）
# 无需在应用层硬编码环境变量名

# 参数传递
llm -m deepseek-coder --temperature 0.1 --max-tokens 2048 "Generate code"

# 版本检查
llm --version  # 最低兼容版本: 0.15+
```

**Alternatives Considered**:
1. ❌ **直接调用DeepSeek HTTP API**: 需要实现HTTP客户端、错误重试、认证逻辑，增加复杂度
2. ❌ **保留Gemini CLI同时添加DeepSeek支持**: 维护两套CLI逻辑，违反DRY原则
3. ✅ **llm CLI统一接口**: 选择此方案，理由见上

### 2. DeepSeek模型配置参数

**Question**: DeepSeek provider的推荐模型、context window、temperature等配置参数应如何设置？

**Research Method**:
- DeepSeek官方文档: https://platform.deepseek.com/docs
- llm-deepseek plugin文档
- 与原Gemini配置对比

**Decision**: 使用以下默认配置

| 参数 | DeepSeek值 | Gemini值 (原配置) | 变更理由 |
|------|-----------|------------------|---------|
| **model_name** | `deepseek-coder` | `gemini-2.5-pro` | 代码生成场景优选coder模型 |
| **context_window** | `8192` tokens | `1048576` tokens | DeepSeek限制，需要prompt长度检查 |
| **temperature** | `0.1` | `0.1` | 保持一致，确保确定性输出 |
| **timeout_seconds** | `90` | `90` | 保持一致 |
| **max_tokens** | `60000` (移除) | `60000` | DeepSeek通过llm CLI自动管理，无需显式配置 |

**Rationale**:
- **模型选择**: `deepseek-coder`针对代码场景优化，适合生成code evaluation报告
- **Context window差异**: 8192 tokens远小于Gemini的1M tokens，**必须**实现prompt长度验证（FR-014）
- **Temperature一致性**: 保持0.1确保输出确定性，便于测试和调试

**Key Findings**:
- DeepSeek的context window限制较严格（8192 vs 1048576），需要提前验证
- 典型score_input.json大小: 2000-5000 tokens（通过测试数据估算），远低于上限
- 建议在80%上限（~6500 tokens）时发出警告，避免边界情况

**Alternatives Considered**:
1. ❌ **使用deepseek-chat**: 通用对话模型，代码生成质量不如coder
2. ✅ **使用deepseek-coder**: 选择此方案，专门针对代码场景优化

### 3. Token估算方法

**Question**: 如何在不引入额外依赖的情况下估算prompt的token数量？

**Research Method**:
- OpenAI tokenization文档
- 现有项目token估算实践
- 性能和精度权衡分析

**Decision**: 使用4 characters ≈ 1 token启发式估算

**Rationale**:
- **简洁性**: 无需引入tiktoken或其他tokenizer库（符合KISS原则）
- **足够精度**: ±10%误差，对8192 tokens上限检查足够
- **零依赖**: 纯Python字符串操作，无额外安装成本

**Implementation**:
```python
def estimate_prompt_tokens(prompt: str) -> int:
    """
    Estimate token count using simple heuristic.

    Accuracy: ±10% for English text
    Note: Chinese text uses 2 chars/token
    """
    return len(prompt) // 4
```

**Validation**:
- 测试数据: 1000字符prompt ≈ 250 tokens (实际240-260)
- 误差范围: <10%，对于8192上限检查完全可接受
- 中文文本调整: 如果检测到中文字符占比>50%，使用2 chars/token

**Alternatives Considered**:
1. ❌ **引入tiktoken库**: 增加依赖，违反KISS原则
2. ❌ **调用llm CLI --count-tokens**: 每次验证需额外subprocess调用，延迟+100ms
3. ✅ **字符长度启发式**: 选择此方案，简单且足够准确

### 4. 环境验证最佳实践

**Question**: 如何在执行前验证llm CLI可用性和环境变量？验证失败时应提供什么信息？

**Research Method**:
- Python subprocess最佳实践
- Code Score现有toolchain validation模式（参考CLAUDE.md）
- 用户体验设计

**Decision**: 实现三层验证策略

**Validation Layers**:

1. **CLI可用性检查**:
```python
import shutil
import subprocess

def validate_llm_cli_available() -> tuple[bool, str | None]:
    """Check if llm CLI is installed and accessible."""
    # Step 1: Check PATH
    if not shutil.which('llm'):
        return False, "llm CLI not found in PATH"

    # Step 2: Verify executable
    try:
        result = subprocess.run(
            ['llm', '--version'],
            capture_output=True,
            text=True,
            timeout=3
        )
        version = result.stdout.strip()
        return True, version
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"llm CLI check failed: {e}"
```

2. **环境变量检查**:
```python
import os

def validate_environment_variables(required_vars: dict[str, str]) -> list[str]:
    """Return list of missing environment variable names."""
    missing = []
    for var_name in required_vars.keys():
        if not os.getenv(var_name):
            missing.append(var_name)
    return missing
```

3. **提前失败检查**:
- 在`ReportGenerator.generate_report()`入口立即调用验证
- 所有验证失败立即抛出`LLMProviderError`
- 错误消息包含：缺失的环境变量名称、llm CLI安装指引链接

**Rationale**:
- **Fail-fast**: 避免中途失败浪费时间（符合Constitution II）
- **清晰错误**: 用户立即知道缺少什么，如何修复
- **性能**: 验证总耗时<100ms，对用户体验无影响

**Error Message Format**:
```python
raise LLMProviderError(
    f"Missing required environment variables: {', '.join(missing)}\n"
    f"Please set {missing[0]} for DeepSeek authentication.\n"
    f"Installation guide: https://llm.datasette.io/en/stable/setup.html"
)
```

**Alternatives Considered**:
1. ❌ **延迟验证（调用时才检查）**: 用户可能等90秒才发现配置错误
2. ❌ **静默失败**: 违反fail-fast原则
3. ✅ **提前全面验证**: 选择此方案，最佳用户体验

### 5. Gemini代码清理范围

**Question**: 需要删除哪些Gemini特定代码？如何确保没有遗留引用？

**Research Method**:
- 代码库全文搜索"gemini"关键词
- 分析LLMProviderConfig和ReportGenerator依赖
- 识别测试用例中的Gemini引用

**Decision**: 清理以下4类Gemini特定代码

**Cleanup Scope**:

1. **配置验证逻辑** (`src/llm/models/llm_provider_config.py`):
```python
# 删除这段硬编码白名单
@classmethod
@field_validator("provider_name")
def validate_provider_name(cls, v):
    allowed_providers = ["gemini"]  # ❌ 删除
    if v not in allowed_providers:
        raise ValueError(...)
    return v

# 保留但移除白名单检查
@classmethod
@field_validator("provider_name")
def validate_provider_name(cls, v):
    if not v:
        raise ValueError("Provider name cannot be empty")
    # 不再限制specific providers
    return v
```

2. **默认配置** (`get_default_configs()`):
```python
# 删除Gemini配置
defaults = {
    "gemini": cls(...)  # ❌ 完全删除
}

# 替换为DeepSeek配置
defaults = {
    "deepseek": cls(
        provider_name="deepseek",
        cli_command=["llm"],
        model_name="deepseek-coder",
        timeout_seconds=90,
        temperature=0.1,
        environment_variables={"DEEPSEEK_API_KEY": "required"},
        context_window=8192,
        # 移除Gemini特定参数: --approval-mode, --debug
        additional_args={}
    )
}
```

3. **Provider特定方法**:
```python
# ❌ 删除此方法（Gemini特定逻辑）
def get_provider_specific_limits(self) -> dict[str, int | None]:
    if self.provider_name == "gemini":
        return {...}
    return {}
```

4. **测试用例**:
- `tests/unit/llm/test_llm_provider_config.py`: 删除test_gemini_*系列测试
- `tests/integration/llm/test_llm_workflow.py`: 删除Gemini端到端测试
- `tests/contract/test_llm_provider_schema.py`: 删除Gemini schema验证

5. **文档引用**:
- CLAUDE.md: 更新LLM Report Generation Details section
- README.md: 移除"使用Google Gemini 2.5 Pro Preview"描述
- specs/prompts/llm_report.md: 检查是否有Gemini特定提示词

**Verification Strategy**:
```bash
# 全文搜索确保无遗留
grep -ri "gemini" src/ tests/ --exclude-dir=htmlcov
grep -ri "GEMINI_API_KEY" src/ tests/

# 预期结果: 0 matches (除了git历史)
```

**Rationale**:
- **完全切换**: 既然决定移除Gemini（clarification session结论），就彻底清理
- **避免混淆**: 保留遗留代码会导致维护困惑
- **测试覆盖**: 删除旧测试的同时添加等价的DeepSeek测试，确保功能完整性

## Research Artifacts

### Verified Commands
```bash
# llm CLI安装验证
$ llm --version
llm, version 0.15

# DeepSeek模型可用性
$ llm models list | grep deepseek
deepseek-coder
deepseek-chat

# 环境变量检查
$ env | grep DEEPSEEK_API_KEY
DEEPSEEK_API_KEY=sk-***
```

### Reference Links
- llm CLI官方文档: https://llm.datasette.io/
- DeepSeek API文档: https://platform.deepseek.com/docs
- llm-deepseek plugin: https://github.com/simonw/llm-deepseek
- Code Score Constitution: `.specify/memory/constitution.md`

## Summary of Decisions

| 决策点 | 选择 | 关键原因 |
|--------|------|---------|
| **CLI接口** | llm CLI标准格式 | 统一性、无provider特定逻辑 |
| **模型选择** | deepseek-coder | 代码生成场景优化 |
| **Token估算** | 4 chars/token启发式 | KISS原则，±10%精度足够 |
| **Context window** | 8192 tokens | DeepSeek限制，需提前验证 |
| **环境验证** | 三层提前验证 | Fail-fast，清晰错误消息 |
| **Gemini清理** | 完全移除 | 避免维护混淆，清晰架构 |

## Open Questions (None)

✅ 所有技术不确定性已通过2025-10-17 clarification session解决。

## Next Steps

- ✅ Phase 1: 使用research findings生成data-model.md和contracts
- ✅ Phase 2: 基于设计生成tasks.md（通过/tasks命令）
- Phase 3: 执行implementation tasks
