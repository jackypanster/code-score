# Data Model: Provider模型统一切换至llm CLI

**Feature**: 006-provider-llm-cli
**Date**: 2025-10-17
**Status**: Complete

## Overview

本文档定义将LLM provider从Gemini切换到llm CLI统一接口所需的数据模型变更。核心变更集中在`LLMProviderConfig`模型的修改和新增`EnvironmentValidation`模型。

## Entity Modifications

### 1. LLMProviderConfig (Modified)

**Location**: `src/llm/models/llm_provider_config.py`

**Purpose**: 配置外部LLM provider的统一数据模型

#### Fields (保留)

| Field | Type | Default | Validation | Description |
|-------|------|---------|------------|-------------|
| `provider_name` | `str` | (required) | `^[a-z][a-z0-9_]*$` | Provider标识符，**移除白名单限制** |
| `cli_command` | `list[str]` | (required) | `min_items=1` | 基础CLI命令（默认`["llm"]`） |
| `model_name` | `str \| None` | `None` | - | 模型标识符（用于`-m`参数） |
| `timeout_seconds` | `int` | `90` | `10 <= x <= 300` | LLM调用超时时间（秒） |
| `max_tokens` | `int \| None` | `None` | `> 0` | 最大响应长度（provider特定） |
| `temperature` | `float \| None` | `None` | `0.0 <= x <= 2.0` | 采样温度 |
| `environment_variables` | `dict[str, str]` | `{}` | 键匹配`^[A-Z][A-Z0-9_]*$` | 必需的环境变量映射 |
| `additional_args` | `dict[str, str\|int\|float\|bool\|None]` | `{}` | 键以`-`或`--`开头 | Provider特定CLI参数 |
| `supports_streaming` | `bool` | `False` | - | 是否支持流式响应 |
| `context_window` | `int \| None` | `None` | `> 0` | 最大上下文窗口（tokens） |

**Field Changes**:
- `provider_name`: 移除`validate_provider_name`中的`allowed_providers = ["gemini"]`硬编码白名单
- `environment_variables`: 默认改为`{"DEEPSEEK_API_KEY": "required"}`（通过`get_default_configs`）
- `context_window`: DeepSeek默认`8192`（vs Gemini `1048576`）

#### Methods (Modified)

##### `validate_provider_name(cls, v: str) -> str`

**Before** (Gemini硬编码):
```python
@classmethod
@field_validator("provider_name")
def validate_provider_name(cls, v):
    if not v:
        raise ValueError("Provider name cannot be empty")

    allowed_providers = ["gemini"]  # ❌ 硬编码限制

    if v not in allowed_providers:
        raise ValueError(
            f"Unsupported provider: {v}. Only Gemini is supported in this MVP version."
        )

    return v
```

**After** (移除白名单):
```python
@classmethod
@field_validator("provider_name")
def validate_provider_name(cls, v):
    if not v:
        raise ValueError("Provider name cannot be empty")

    # 移除硬编码白名单，支持任意provider
    # llm CLI负责验证provider是否实际可用

    return v
```

##### `build_cli_command(self, prompt: str, output_file: str | None = None) -> list[str]`

**Before** (Gemini特定):
```python
def build_cli_command(self, prompt: str, output_file: str | None = None) -> list[str]:
    command = self.cli_command.copy()  # ["gemini"]

    # Gemini CLI expects --model
    if self.model_name:
        command.extend(["--model", self.model_name])

    # Gemini特定参数
    for arg_name, arg_value in self.additional_args.items():
        if arg_value == "" or arg_value is None:
            command.append(arg_name)  # --approval-mode, --debug
        else:
            command.extend([arg_name, str(arg_value)])

    command.append(prompt)  # Gemini expects prompt as positional arg
    return command
```

**After** (llm CLI标准格式):
```python
def build_cli_command(self, prompt: str, output_file: str | None = None) -> list[str]:
    command = self.cli_command.copy()  # ["llm"]

    # llm CLI standard format: llm -m <model> "<prompt>"
    if self.model_name:
        command.extend(["-m", self.model_name])

    # 通用参数（temperature, max-tokens等）
    for arg_name, arg_value in self.additional_args.items():
        if arg_value == "" or arg_value is None:
            command.append(arg_name)
        else:
            command.extend([arg_name, str(arg_value)])

    # Prompt作为最后一个位置参数
    command.append(prompt)

    return command
```

**Key Changes**:
- `--model` → `-m` (llm CLI标准格式)
- 移除Gemini特定参数（`--approval-mode yolo`, `--debug`）
- 保持prompt作为位置参数（与llm CLI一致）

##### `get_default_configs(cls) -> dict[str, "LLMProviderConfig"]`

**Before** (Gemini配置):
```python
@classmethod
def get_default_configs(cls) -> dict[str, "LLMProviderConfig"]:
    defaults = {
        "gemini": cls(
            provider_name="gemini",
            cli_command=["gemini"],
            model_name="gemini-2.5-pro",
            timeout_seconds=90,
            max_tokens=60000,
            temperature=0.1,
            environment_variables={"GEMINI_API_KEY": "required"},
            supports_streaming=True,
            context_window=1048576,
            additional_args={"--approval-mode": "yolo", "--debug": None},
        )
    }
    return defaults
```

**After** (DeepSeek配置):
```python
@classmethod
def get_default_configs(cls) -> dict[str, "LLMProviderConfig"]:
    defaults = {
        "deepseek": cls(
            provider_name="deepseek",
            cli_command=["llm"],  # llm CLI统一入口
            model_name="deepseek-coder",  # 代码生成场景优化
            timeout_seconds=90,  # 保持不变
            max_tokens=None,  # llm CLI自动管理
            temperature=0.1,  # 保持确定性
            environment_variables={"DEEPSEEK_API_KEY": "required"},
            supports_streaming=False,  # 当前不支持
            context_window=8192,  # DeepSeek限制
            additional_args={},  # 无provider特定参数
        )
    }
    return defaults
```

**Rationale**:
- `cli_command`: `["gemini"]` → `["llm"]` (统一CLI入口)
- `model_name`: `gemini-2.5-pro` → `deepseek-coder` (代码场景优化)
- `context_window`: `1048576` → `8192` (DeepSeek限制，需token检查)
- `additional_args`: 移除Gemini特定参数

#### Methods (New)

##### `estimate_prompt_tokens(self, prompt: str) -> int`

**Purpose**: 使用简单启发式估算prompt的token数量

**Signature**:
```python
def estimate_prompt_tokens(self, prompt: str) -> int:
    """
    Estimate token count using 4 characters ≈ 1 token heuristic.

    Args:
        prompt: Input text to estimate

    Returns:
        Estimated token count

    Note:
        Accuracy: ±10% for English text
        Chinese text uses ~2 chars/token but this is acceptable
        for context window validation
    """
    return len(prompt) // 4
```

**Rationale**:
- **简洁性**: 无需引入tiktoken库（符合KISS原则）
- **精度**: ±10%误差，对8192 tokens上限检查足够
- **性能**: O(1)操作，<1ms延迟

##### `validate_prompt_length(self, prompt: str) -> None`

**Purpose**: 验证prompt是否超过provider的context window上限

**Signature**:
```python
def validate_prompt_length(self, prompt: str) -> None:
    """
    Validate prompt length against context window limit.

    Args:
        prompt: Input text to validate

    Raises:
        ValueError: If prompt exceeds context window limit

    Example:
        >>> config = LLMProviderConfig(context_window=8192, ...)
        >>> config.validate_prompt_length("very long prompt...")
        ValueError: Prompt length 9000 tokens exceeds DeepSeek limit 8192 tokens
    """
    if not self.context_window:
        return  # No limit configured

    estimated_tokens = self.estimate_prompt_tokens(prompt)

    if estimated_tokens > self.context_window:
        raise ValueError(
            f"Prompt length {estimated_tokens} tokens exceeds "
            f"{self.provider_name} context window limit {self.context_window} tokens. "
            f"Actual prompt length: {len(prompt)} characters."
        )
```

**Rationale**:
- **Fail-fast**: 在调用llm CLI前检查，避免浪费API配额
- **清晰错误**: 提供具体的token数和字符数，便于调试
- **符合FR-014**: 直接报错，无自动截断

#### Methods (Removed)

##### `get_provider_specific_limits(self) -> dict[str, int | None]`

**Reason for Removal**: Gemini特定逻辑，llm CLI统一管理provider限制

**Before**:
```python
def get_provider_specific_limits(self) -> dict[str, int | None]:
    """Get Gemini-specific limits and capabilities."""
    if self.provider_name == "gemini":
        return {
            "context_window": self.context_window or 1048576,
            "max_output_tokens": self.max_tokens or 60000,
            "default_temperature": self.temperature if self.temperature is not None else 0.1,
        }
    return {}
```

**Replacement**: 使用标准字段（`context_window`, `max_tokens`, `temperature`），无需provider特定方法

---

### 2. EnvironmentValidation (New)

**Location**: `src/llm/models/environment_validation.py` (new file)

**Purpose**: 统一的环境验证结果对象，用于validate_prerequisites

#### Schema

```python
from pydantic import BaseModel, Field

class EnvironmentValidation(BaseModel):
    """
    Environment validation results for LLM provider prerequisites.

    Used by ReportGenerator.validate_prerequisites() to check
    llm CLI availability and required environment variables.
    """

    llm_cli_available: bool = Field(
        ..., description="Whether llm CLI is found in PATH"
    )

    llm_cli_version: str | None = Field(
        None, description="Detected llm CLI version (e.g., '0.15')"
    )

    required_env_vars: dict[str, bool] = Field(
        default_factory=dict,
        description="Environment variable check results {var_name: is_set}"
    )

    validation_errors: list[str] = Field(
        default_factory=list,
        description="List of validation error messages"
    )

    def is_valid(self) -> bool:
        """Return True if all validation checks passed."""
        return (
            self.llm_cli_available
            and all(self.required_env_vars.values())
            and len(self.validation_errors) == 0
        )

    def get_error_summary(self) -> str:
        """Return formatted error summary for user display."""
        if self.is_valid():
            return "All prerequisites validated successfully."

        errors = []

        if not self.llm_cli_available:
            errors.append(
                "✗ llm CLI not found in PATH. "
                "Install: pip install llm"
            )

        missing_vars = [
            var for var, is_set in self.required_env_vars.items()
            if not is_set
        ]
        if missing_vars:
            errors.append(
                f"✗ Missing environment variables: {', '.join(missing_vars)}"
            )

        errors.extend(self.validation_errors)

        return "\n".join(errors)
```

#### Usage Example

```python
# In ReportGenerator.validate_prerequisites()
def validate_prerequisites(self, provider: str) -> dict[str, Any]:
    """Validate all prerequisites for report generation."""
    # ... existing code ...

    validation = EnvironmentValidation(
        llm_cli_available=check_llm_cli(),
        llm_cli_version=get_llm_version(),
        required_env_vars={
            "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY") is not None
        },
        validation_errors=[]
    )

    if not validation.is_valid():
        raise LLMProviderError(
            f"Prerequisites validation failed:\n{validation.get_error_summary()}"
        )

    return validation.dict()
```

---

## Entity Relationships

```
┌─────────────────────────┐
│  ReportGenerator        │
└──────────┬──────────────┘
           │ uses
           ↓
┌─────────────────────────┐      ┌────────────────────────┐
│  LLMProviderConfig      │      │  EnvironmentValidation │
│  (Modified)             │      │  (New)                 │
├─────────────────────────┤      ├────────────────────────┤
│ + provider_name         │      │ + llm_cli_available    │
│ + cli_command           │      │ + llm_cli_version      │
│ + model_name            │      │ + required_env_vars    │
│ + context_window        │      │ + validation_errors    │
│ + ...                   │      ├────────────────────────┤
├─────────────────────────┤      │ + is_valid()           │
│ + build_cli_command()   │      │ + get_error_summary()  │
│ + estimate_tokens() NEW │      └────────────────────────┘
│ + validate_length() NEW │               ↑
│ - get_specific_limits() │               │ returns
│   REMOVED               │               │
└─────────────────────────┘      ┌────────────────────────┐
           │ generates            │  validate_prerequisites│
           ↓                      │  (method)              │
┌─────────────────────────┐      └────────────────────────┘
│  list[str]              │
│  ["llm", "-m",          │
│   "deepseek-coder",     │
│   "prompt"]             │
└─────────────────────────┘
```

## State Transitions

### LLMProviderConfig State Flow

```
[创建配置]
    ↓
[validate_provider_name] → 移除白名单检查
    ↓
[validate_environment_variables] → 检查DEEPSEEK_API_KEY格式
    ↓
[get_default_configs] → 返回DeepSeek默认配置
    ↓
[validate_prompt_length] → 检查是否超过8192 tokens
    ↓
[build_cli_command] → 生成["llm", "-m", "deepseek-coder", "prompt"]
    ↓
[ReportGenerator执行]
```

### EnvironmentValidation State Flow

```
[validate_prerequisites调用]
    ↓
[检查llm CLI] → llm_cli_available = True/False
    ↓
[检查环境变量] → required_env_vars = {"DEEPSEEK_API_KEY": True/False}
    ↓
[is_valid()] → True: 继续 / False: 抛出LLMProviderError
    ↓
[get_error_summary()] → 格式化错误消息供用户查看
```

## Validation Rules

### Provider Name

**Before**:
- 必须是"gemini" (硬编码白名单)

**After**:
- 非空字符串
- 匹配模式: `^[a-z][a-z0-9_]*$`
- **无白名单限制** (llm CLI负责验证provider可用性)

### Context Window

**Gemini**: 1048576 tokens (1M tokens)
**DeepSeek**: 8192 tokens (严格限制)

**Validation Logic**:
```python
if estimated_tokens > self.context_window:
    raise ValueError(f"Prompt exceeds {self.context_window} token limit")
```

### Environment Variables

**Gemini**: `GEMINI_API_KEY`
**DeepSeek**: `DEEPSEEK_API_KEY`

**Validation Timing**:
- `validate_prerequisites()`: 检查环境变量是否设置
- `generate_report()`: 提前验证（在调用llm CLI前）

## Migration Notes

### Breaking Changes

1. **默认provider改变**: `"gemini"` → `"deepseek"`
   - 影响: `ReportGenerator(..., provider="gemini")` 调用将失败
   - 迁移: 更新为`provider="deepseek"`或移除参数使用默认值

2. **Context window大幅缩小**: `1048576` → `8192`
   - 影响: 超长prompt将抛出ValueError（之前自动截断）
   - 迁移: 确保score_input.json大小<25KB（~6000 tokens安全边际）

3. **移除get_provider_specific_limits()**: Gemini特定方法
   - 影响: 依赖此方法的代码将失败
   - 迁移: 直接使用`context_window`, `max_tokens`, `temperature`字段

### Backwards Compatibility

**保持兼容的设计**:
- LLMProviderConfig字段结构不变（无字段删除）
- Pydantic validators签名不变
- build_cli_command返回类型不变（`list[str]`）

**不兼容的变更**:
- `get_default_configs()["gemini"]` → 不存在，需改为`["deepseek"]`
- provider_name验证规则变更（移除白名单）

## Testing Strategy

### Contract Tests
- test_llm_cli_command_format.py: 验证`build_cli_command`输出符合`llm -m <model> "<prompt>"`格式
- test_llm_provider_schema.py: 验证LLMProviderConfig schema定义

### Unit Tests
- test_estimate_prompt_tokens: 验证4 chars/token启发式精度
- test_validate_prompt_length: 验证超出8192 tokens抛出ValueError
- test_build_cli_command_deepseek: 验证DeepSeek命令格式
- test_get_default_configs: 验证DeepSeek默认配置正确性

### Integration Tests
- test_environment_validation_flow: 验证EnvironmentValidation完整流程
- test_missing_env_var_detection: 验证缺失DEEPSEEK_API_KEY时错误消息

## Performance Considerations

### Token Estimation
- **复杂度**: O(n) 其中n = len(prompt)
- **预期延迟**: <1ms (纯Python字符串操作)
- **精度**: ±10% (对8192上限检查足够)

### Environment Validation
- **llm CLI检查**: ~50ms (subprocess调用)
- **环境变量检查**: <1ms (dict lookup)
- **总延迟**: <100ms (一次性开销，可接受)

### Build CLI Command
- **复杂度**: O(k) 其中k = len(additional_args)
- **预期延迟**: <1ms (list操作)

## Security Considerations

### Environment Variables
- API密钥通过环境变量传递（不在代码中硬编码）
- 日志记录CLI命令时需隐藏敏感信息

### Command Injection Prevention
- `validate_cli_command`: 检查dangerous patterns (`;`, `&&`, `|`, etc.)
- Prompt作为单独的list元素传递，避免shell注入

## Documentation Updates Required

- CLAUDE.md: 添加LLM Provider Migration section
- README.md: 移除Gemini引用，更新为DeepSeek
- API docs: 更新LLMProviderConfig字段说明
