# Contract: llm CLI命令格式约束

**Feature**: 006-provider-llm-cli
**Version**: 1.0.0
**Date**: 2025-10-17

## Purpose

定义`LLMProviderConfig.build_cli_command()`生成的llm CLI命令格式约束，确保与llm CLI标准接口兼容。

## Standard Format

### Base Command

```bash
llm -m <model_name> "<prompt>"
```

### Components

| Component | Required | Format | Example |
|-----------|----------|--------|---------|
| `llm` | ✅ Yes | CLI名称 | `llm` |
| `-m <model>` | ✅ Yes | 短参数 + 模型名 | `-m deepseek-coder` |
| `"<prompt>"` | ✅ Yes | 引号包裹的字符串 | `"Generate code"` |

### Optional Parameters

| Parameter | Format | Value Range | Example |
|-----------|--------|-------------|---------|
| `--temperature` | `--temperature <float>` | `0.0 - 2.0` | `--temperature 0.1` |
| `--max-tokens` | `--max-tokens <int>` | `> 0` | `--max-tokens 2048` |
| 其他provider参数 | `--<name> <value>` | 由llm CLI定义 | `--top-p 0.9` |

## Valid Examples

### Minimal Call
```bash
llm -m deepseek-coder "Explain this function"
```

### With Temperature
```bash
llm -m deepseek-chat --temperature 0.1 "Write a report"
```

### With Multiple Parameters
```bash
llm -m deepseek-coder --temperature 0.1 --max-tokens 4096 "Generate unit tests"
```

### Python List Format (build_cli_command output)
```python
# Minimal
["llm", "-m", "deepseek-coder", "prompt text"]

# With parameters
["llm", "-m", "deepseek-chat", "--temperature", "0.1", "prompt text"]
```

## Invalid Examples

### ❌ Missing -m parameter
```bash
llm "prompt"  # ValueError: Model name required
```

### ❌ Empty prompt
```bash
llm -m deepseek-coder ""  # ValueError: Prompt cannot be empty
```

### ❌ Wrong parameter format (--model instead of -m)
```bash
llm --model deepseek-coder "prompt"  # llm CLI error: unrecognized option
```

### ❌ Prompt not as final argument
```bash
llm "prompt" -m deepseek-coder  # Parsing error
```

### ❌ Unquoted prompt with spaces (shell syntax)
```bash
llm -m deepseek-coder Generate code  # Interprets "code" as separate arg
```

## Validation Rules

### Command Structure

1. **First element** MUST be `"llm"`
2. **Model parameter** MUST appear as `-m <model_name>` (not `--model`)
3. **Prompt** MUST be the **last** element in the list
4. **Optional parameters** MUST appear between `-m` and prompt

### Model Name

- MUST NOT be empty
- SHOULD match llm CLI supported models (runtime validation by llm CLI)
- Examples: `deepseek-coder`, `deepseek-chat`, `gpt-4`, `claude-3-opus`

### Prompt

- MUST NOT be empty string
- SHOULD be quoted when passed to shell (handled by subprocess module)
- No length restriction at CLI level (provider context window enforced separately)

## Error Handling

### ValueError Scenarios

| Condition | Exception Message |
|-----------|-------------------|
| Empty model_name | `"Model name required for llm CLI invocation"` |
| Empty prompt | `"Prompt cannot be empty"` |
| Invalid cli_command[0] | `"CLI command must start with 'llm'"` |

### llm CLI Exit Codes

| Exit Code | Meaning | Handling |
|-----------|---------|----------|
| `0` | Success | Parse stdout |
| `1` | Invalid arguments | LLMProviderError with stderr |
| `2` | Model not found | LLMProviderError "Model {name} not available" |
| `124` | Timeout | LLMProviderError "LLM call timed out" |

## Contract Tests

### test_deepseek_command_format

```python
def test_deepseek_command_format():
    """Verify DeepSeek command follows llm CLI standard format."""
    config = LLMProviderConfig.get_default_configs()["deepseek"]
    command = config.build_cli_command("test prompt")

    # Contract assertions
    assert command[0] == "llm", "First element must be 'llm'"
    assert command[1] == "-m", "Model flag must be '-m'"
    assert command[2] in ["deepseek-coder", "deepseek-chat"], "Valid model name"
    assert command[-1] == "test prompt", "Prompt must be last element"
```

### test_no_gemini_specific_args

```python
def test_no_gemini_specific_args():
    """Verify no Gemini-specific parameters remain."""
    config = LLMProviderConfig.get_default_configs()["deepseek"]
    command = config.build_cli_command("test")

    # Contract assertions
    assert "--approval-mode" not in command
    assert "--debug" not in " ".join(command)
    assert "gemini" not in " ".join(command).lower()
```

### test_optional_parameters_format

```python
def test_optional_parameters_format():
    """Verify optional parameters follow llm CLI conventions."""
    config = LLMProviderConfig(
        provider_name="deepseek",
        cli_command=["llm"],
        model_name="deepseek-coder",
        additional_args={"--temperature": "0.5", "--max-tokens": "1024"}
    )
    command = config.build_cli_command("test")

    # Contract assertions
    assert "--temperature" in command
    assert "0.5" in command
    assert "--max-tokens" in command
    assert "1024" in command
```

## Compatibility Notes

### Gemini → llm CLI Migration

| Gemini Format | llm CLI Format | Change |
|---------------|----------------|--------|
| `gemini --model gemini-2.5-pro` | `llm -m deepseek-coder` | ✏️ Modified command |
| `--approval-mode yolo` | (removed) | ❌ Deleted parameter |
| `--debug` | (removed) | ❌ Deleted parameter |
| Prompt position | Prompt position | ✅ Same (last element) |

### Version Requirements

- **llm CLI**: `>= 0.15` (supports -m parameter)
- **Python subprocess**: `>= 3.11` (text mode, timeout support)

## References

- llm CLI Documentation: https://llm.datasette.io/
- llm-deepseek Plugin: https://github.com/simonw/llm-deepseek
- Python subprocess: https://docs.python.org/3/library/subprocess.html
