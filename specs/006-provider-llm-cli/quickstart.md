# Quickstart: Provider模型统一切换至llm CLI

**Feature**: 006-provider-llm-cli
**Date**: 2025-10-17
**Purpose**: 验证llm CLI provider切换功能的完整工作流程

## Prerequisites

### 1. Install llm CLI

```bash
# Install llm CLI using uv (matches Constitution I)
uv tool install llm

# Verify installation
llm --version
# Expected: llm, version 0.15 or higher
```

### 2. Install DeepSeek Plugin

```bash
# Install llm-deepseek plugin
llm install llm-deepseek

# Verify DeepSeek models available
llm models list | grep deepseek
# Expected output:
# deepseek-coder
# deepseek-chat
```

### 3. Set Environment Variable

```bash
# Set DeepSeek API key
export DEEPSEEK_API_KEY="your-api-key-here"

# Verify environment variable
echo $DEEPSEEK_API_KEY
# Expected: your-api-key-here (non-empty)
```

## Validation Steps

### Step 1: Verify LLMProviderConfig Changes

**Goal**: 确认Gemini硬编码限制已移除

```bash
# Navigate to project root
cd /Users/zhibinpan/workspace/code-score

# Run Python interactive shell
uv run python
```

```python
# Test 1: Provider name validation removed
from src.llm.models.llm_provider_config import LLMProviderConfig

# Should NOT raise error (previously rejected)
config = LLMProviderConfig(
    provider_name="deepseek",
    cli_command=["llm"],
    model_name="deepseek-coder"
)
print(f"✓ Provider name validation passed: {config.provider_name}")

# Test 2: Default config uses DeepSeek
defaults = LLMProviderConfig.get_default_configs()
assert "deepseek" in defaults, "DeepSeek not in defaults"
assert "gemini" not in defaults, "Gemini still in defaults!"
print(f"✓ Default configs updated: {list(defaults.keys())}")

# Test 3: CLI command format
deepseek_config = defaults["deepseek"]
command = deepseek_config.build_cli_command("test prompt")
assert command[0] == "llm", "First element should be 'llm'"
assert command[1] == "-m", "Second element should be '-m'"
assert command[2] in ["deepseek-coder", "deepseek-chat"], "Invalid model"
print(f"✓ CLI command format correct: {command}")
```

**Expected Output**:
```
✓ Provider name validation passed: deepseek
✓ Default configs updated: ['deepseek']
✓ CLI command format correct: ['llm', '-m', 'deepseek-coder', 'test prompt']
```

### Step 2: Verify Token Estimation

**Goal**: 确认新增的prompt length validation方法

```python
# Test 4: Token estimation
config = defaults["deepseek"]

short_prompt = "Hello world"
estimated = config.estimate_prompt_tokens(short_prompt)
print(f"✓ Token estimation: '{short_prompt}' → {estimated} tokens (expected ~2-3)")

# Test 5: Context window validation (should NOT raise)
normal_prompt = "x" * 1000  # 1000 chars ≈ 250 tokens
try:
    config.validate_prompt_length(normal_prompt)
    print(f"✓ Normal prompt accepted ({len(normal_prompt)} chars)")
except ValueError as e:
    print(f"✗ FAIL: {e}")

# Test 6: Context window exceeded (should raise ValueError)
huge_prompt = "x" * 40000  # 40000 chars ≈ 10000 tokens > 8192
try:
    config.validate_prompt_length(huge_prompt)
    print("✗ FAIL: Should have raised ValueError for huge prompt")
except ValueError as e:
    assert "exceeds" in str(e).lower(), "Error message should mention 'exceeds'"
    print(f"✓ Huge prompt rejected: {str(e)[:80]}...")
```

**Expected Output**:
```
✓ Token estimation: 'Hello world' → 2 tokens (expected ~2-3)
✓ Normal prompt accepted (1000 chars)
✓ Huge prompt rejected: Prompt length 10000 tokens exceeds deepseek context window limit 8192...
```

### Step 3: Environment Validation

**Goal**: 验证环境检查功能

```python
# Test 7: Environment validation
from src.llm.report_generator import ReportGenerator

generator = ReportGenerator()
validation = generator.validate_prerequisites("deepseek")

assert validation['provider_available'], "Provider should be available"
assert validation['environment_valid'], "Environment should be valid"
print(f"✓ Prerequisites validation passed: {validation}")
```

**Expected Output**:
```
✓ Prerequisites validation passed: {
    'valid': True,
    'provider_available': True,
    'environment_valid': True,
    'template_available': True,
    'issues': []
}
```

### Step 4: Generate Test Report (Dry-Run)

**Goal**: 验证完整报告生成流程（不实际调用API）

**Note**: 由于dry-run模式将在Task T021实现，此步骤暂时使用模拟数据

```python
# Test 8: Build command for realistic prompt
import json

# Load sample score_input.json
with open("tests/fixtures/sample_score_input.json") as f:
    score_input = json.load(f)

# Build prompt (simplified version of PromptBuilder logic)
prompt = f"Generate report for repository: {score_input['repository_info']['url']}"

config = defaults["deepseek"]
command = config.build_cli_command(prompt)

print(f"✓ Generated command: {' '.join(command[:4])}... (truncated)")
print(f"  Full command elements: {len(command)}")
print(f"  Prompt length: {len(prompt)} chars ≈ {config.estimate_prompt_tokens(prompt)} tokens")
```

**Expected Output**:
```
✓ Generated command: llm -m deepseek-coder Generate... (truncated)
  Full command elements: 4
  Prompt length: 67 chars ≈ 16 tokens
```

### Step 5: Verify Gemini Code Removal

**Goal**: 确认所有Gemini引用已清理

```bash
# Exit Python shell
exit()

# Search for Gemini references in source code
grep -ri "gemini" src/ tests/ --exclude-dir=htmlcov --exclude-dir=__pycache__

# Expected: 0 matches (or only in comments explaining migration)
# If any matches found, verify they are migration notes, not actual code
```

**Expected Output**:
```
(no output, meaning no "gemini" references found)
```

## Integration Test Execution

### Run Contract Tests

```bash
# Execute contract tests
uv run pytest tests/contract/test_llm_cli_command_format.py -v

# Expected: All tests PASS
# - test_deepseek_command_format
# - test_no_gemini_specific_args
# - test_optional_parameters_format
```

### Run Unit Tests

```bash
# Execute LLMProviderConfig unit tests
uv run pytest tests/unit/llm/test_llm_provider_config.py -v

# Expected: All tests PASS
# - test_provider_name_no_whitelist
# - test_build_cli_command_deepseek
# - test_estimate_prompt_tokens
# - test_validate_prompt_length_exceeds
# - test_get_default_configs_deepseek
```

### Run Integration Tests (Optional - Requires API Key)

**Warning**: This will make real API calls to DeepSeek and consume tokens

```bash
# Set API key if not already set
export DEEPSEEK_API_KEY="your-api-key"

# Run integration test
uv run pytest tests/integration/llm/test_llm_workflow.py::test_deepseek_report_generation -v

# Expected: Test PASS (report generated successfully)
```

## Acceptance Criteria Verification

### FR-001: Gemini硬编码限制已移除

```python
# Should NOT raise ValueError
config = LLMProviderConfig(
    provider_name="custom_provider",
    cli_command=["llm"],
    model_name="custom-model"
)
assert config.provider_name == "custom_provider"
```

✅ **Result**: PASS if no ValueError raised

### FR-003: DeepSeek默认配置

```python
defaults = LLMProviderConfig.get_default_configs()
assert "deepseek" in defaults
assert defaults["deepseek"].model_name in ["deepseek-coder", "deepseek-chat"]
assert defaults["deepseek"].context_window == 8192
```

✅ **Result**: PASS if all assertions pass

### FR-007: llm CLI命令格式

```python
command = defaults["deepseek"].build_cli_command("test")
assert command == ["llm", "-m", "deepseek-coder", "test"]
```

✅ **Result**: PASS if command matches expected format

### FR-009: llm CLI可用性检测

```bash
llm --version
# If command not found, validate_prerequisites should raise LLMProviderError
```

✅ **Result**: PASS if llm CLI installed and version detected

### FR-011: Gemini代码清理

```bash
grep -r "gemini" src/llm/ | wc -l
# Expected: 0 (no Gemini references)
```

✅ **Result**: PASS if count == 0

### FR-013: Fail-fast错误处理

```python
# Simulate missing environment variable
import os
original_key = os.getenv("DEEPSEEK_API_KEY")
os.environ.pop("DEEPSEEK_API_KEY", None)

try:
    generator = ReportGenerator()
    generator.validate_prerequisites("deepseek")
    print("✗ FAIL: Should have raised error")
except Exception as e:
    assert "DEEPSEEK_API_KEY" in str(e)
    print(f"✓ PASS: Fail-fast error: {e}")
finally:
    # Restore environment
    if original_key:
        os.environ["DEEPSEEK_API_KEY"] = original_key
```

✅ **Result**: PASS if LLMProviderError raised with clear message

### FR-014: Context window检测

```python
config = defaults["deepseek"]
huge_prompt = "x" * 40000  # >8192 tokens
try:
    config.validate_prompt_length(huge_prompt)
    print("✗ FAIL: Should reject huge prompt")
except ValueError as e:
    assert "8192" in str(e)
    print(f"✓ PASS: Context window check: {e}")
```

✅ **Result**: PASS if ValueError raised with token limit

## Performance Validation

### Token Estimation Performance

```python
import time

prompt = "x" * 10000  # 10KB prompt
start = time.time()
for _ in range(1000):
    config.estimate_prompt_tokens(prompt)
elapsed = time.time() - start

assert elapsed < 0.1, f"Too slow: {elapsed}s for 1000 calls"
print(f"✓ Token estimation performance: {elapsed*1000:.2f}ms for 1000 calls")
```

**Expected**: <100ms for 1000 calls (<0.1ms per call)

### Environment Validation Performance

```python
start = time.time()
validation = generator.validate_prerequisites("deepseek")
elapsed = time.time() - start

assert elapsed < 2.0, f"Too slow: {elapsed}s"
print(f"✓ Environment validation performance: {elapsed*1000:.0f}ms")
```

**Expected**: <2000ms (includes subprocess call to `llm --version`)

## Troubleshooting

### Issue: "llm CLI not found"

**Solution**:
```bash
# Install llm CLI
uv tool install llm

# Verify installation
which llm
llm --version
```

### Issue: "deepseek model not available"

**Solution**:
```bash
# Install deepseek plugin
llm install llm-deepseek

# Verify
llm models list | grep deepseek
```

### Issue: "Missing environment variable: DEEPSEEK_API_KEY"

**Solution**:
```bash
# Get API key from https://platform.deepseek.com
export DEEPSEEK_API_KEY="sk-your-key-here"

# Add to shell profile for persistence
echo 'export DEEPSEEK_API_KEY="sk-your-key-here"' >> ~/.zshrc
```

### Issue: "Context window exceeded"

**Solution**:
- Check prompt length: `len(prompt) // 4` should be <8192
- Reduce score_input.json size
- Or split into multiple prompts (out of MVP scope)

## Success Criteria

All acceptance criteria MUST pass:

- [ ] FR-001: Custom provider names accepted (no whitelist)
- [ ] FR-003: DeepSeek default config correct
- [ ] FR-007: llm CLI command format valid
- [ ] FR-009: llm CLI availability checked
- [ ] FR-011: No Gemini references in source code
- [ ] FR-013: Fail-fast errors for missing env vars
- [ ] FR-014: Context window validation works
- [ ] All contract tests pass
- [ ] All unit tests pass
- [ ] Performance targets met (<2s validation, <0.1ms token estimation)

## Next Steps

After quickstart validation:

1. Run `/tasks` command to generate tasks.md
2. Execute implementation tasks (T001-T022)
3. Run full test suite: `uv run pytest`
4. Update CLAUDE.md with migration notes
5. Update README.md to remove Gemini references
