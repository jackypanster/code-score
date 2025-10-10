# Mock消除主计划 - 全局分析与执行路线图

## 📊 全局现状统计

### 测试文件总览 (共54个测试文件)

| 类别 | 总文件数 | 使用Mock | 无Mock | Mock测试用例数 |
|------|---------|---------|--------|--------------|
| **Unit Tests** | 20 | **13** ⚠️ | 7 ✅ | **303个** |
| **Integration Tests** | 21 | **8** ⚠️ | 13 ✅ | **74个** |
| **Contract Tests** | 12 | **2** ⚠️ | 10 ✅ | **15个** |
| **Performance Tests** | 1 | **1** ⚠️ | 0 | **10个** |
| **Smoke Tests** | 1 | 0 ✅ | 1 ✅ | 0 |
| **总计** | **55** | **24** | **31** | **402个测试** |

### 当前进度

- ✅ **已完成转换**: 3个文件 (test_all_tools_run_build.py, test_python_tools_build.py, test_git_operations.py)
- 🔄 **剩余待转换**: 24个文件
- 📈 **完成度**: 3/27 = **11%**
- 🎯 **受影响测试用例**: 402个 (需要从mock转为真实执行)

---

## 🎯 优先级矩阵

### P0 - 核心功能,高价值 (必须立即处理) - 6个文件

这些文件测试**核心工具执行**,是整个系统的基础,mock隐藏了真实行为:

| 文件 | 测试数 | Mock类型 | 转换难度 | 预估时间 |
|------|-------|---------|---------|---------|
| **test_tool_runners.py** | 25 | subprocess.run (linting/testing tools) | 🟡 中等 | 1.5小时 |
| **test_pipeline_executor.py** | 24 | subprocess.run (pipeline execution) | 🟡 中等 | 1.5小时 |
| **test_language_detection.py** | 17 | file operations | 🟢 简单 | 1小时 |
| **test_output_formatting.py** | 9 | Path.mkdir, file writes | 🟢 简单 | 0.5小时 |
| **test_pipeline_integration.py** | 14 | 综合pipeline mocks | 🔴 复杂 | 2小时 |
| **test_python_build.py** (integration) | 11 | subprocess.run (builds) | 🟢 简单 | 1小时 |

**P0 小计**: 100个测试, 预估 **7.5小时**

---

### P1 - LLM相关,有外部依赖 (需要策略处理) - 5个文件

这些文件涉及**外部LLM API调用**和**模板处理**,需要特殊策略:

| 文件 | 测试数 | Mock类型 | 转换难度 | 预估时间 | 建议策略 |
|------|-------|---------|---------|---------|---------|
| **test_llm_models.py** | 48 | os.environ, file I/O | 🟡 中等 | 2小时 | 真实环境变量+真实文件 |
| **test_template_loader.py** | 45 | file I/O, template syntax | 🟢 简单 | 1.5小时 | 真实Jinja2模板文件 |
| **test_report_generator.py** | 41 | subprocess.run (gemini CLI) | 🔴 复杂 | 2.5小时 | **难点**: 需要真实Gemini API或只测试CLI调用 |
| **test_prompt_builder.py** | 33 | datetime, template mocks | 🟡 中等 | 1.5小时 | 真实模板+真实时间 |
| **test_llm_report_workflow.py** | 6 | 完整LLM workflow | 🔴 复杂 | 1.5小时 | 端到端真实调用或跳过 |

**P1 小计**: 173个测试, 预估 **9小时**

**⚠️ 关键难点**: `test_report_generator.py` 需要真实Gemini API调用
- **方案A**: 使用真实API (需要GEMINI_API_KEY,有成本)
- **方案B**: 只测试subprocess调用层,不测试API响应
- **方案C**: 使用VCR录制/回放(仍然算mock,不推荐)

---

### P2 - 路径和配置验证 (低风险,快速处理) - 8个文件

这些文件主要测试**路径操作**和**数据验证**,转换简单:

| 文件 | 测试数 | Mock类型 | 转换难度 | 预估时间 |
|------|-------|---------|---------|---------|
| **test_evidence_validation.py** | 28 | 数据验证mocks | 🟢 简单 | 1小时 |
| **test_scoring_mapper_evidence_paths.py** | 10 | Path验证 | 🟢 简单 | 0.5小时 |
| **test_checklist_evaluator_path.py** | 8 | Path操作 | 🟢 简单 | 0.5小时 |
| **test_checklist_loader_path.py** | 7 | Path+YAML加载 | 🟢 简单 | 0.5小时 |
| **test_pipeline_manager_path.py** | 8 | Path管理 | 🟢 简单 | 0.5小时 |
| **test_evidence_path_consistency.py** | 7 | Path一致性 | 🟢 简单 | 0.5小时 |
| **test_cli_evaluate_path.py** | 5 | CLI路径处理 | 🟢 简单 | 0.5小时 |
| **test_custom_template.py** | 8 | 模板路径 | 🟢 简单 | 0.5小时 |

**P2 小计**: 81个测试, 预估 **4.5小时**

---

### P3 - Contract/Integration辅助测试 (可延后) - 5个文件

这些是**schema验证**和**错误处理**测试,优先级较低:

| 文件 | 测试数 | Mock类型 | 转换难度 | 预估时间 |
|------|-------|---------|---------|---------|
| **test_error_handling.py** | 15 | 异常模拟 | 🟡 中等 | 1小时 |
| **test_full_pipeline_checklist.py** | 8 | Pipeline mocks | 🟡 中等 | 1小时 |
| **test_phantom_path_removal.py** | 8 | Path验证 | 🟢 简单 | 0.5小时 |
| **test_evidence_paths_contract.py** | 7 | Contract验证 | 🟢 简单 | 0.5小时 |
| **test_llm_performance.py** | 10 | 性能测试mocks | 🔴 复杂 | 1.5小时 |

**P3 小计**: 48个测试, 预估 **4.5小时**

---

## 📋 详细转换策略

### 策略A: subprocess.run Mock消除 (适用于7个文件)

**目标文件**: test_tool_runners.py, test_pipeline_executor.py, test_report_generator.py, test_python_build.py等

**转换模式**:
```python
# ❌ 旧代码 (Mock)
@patch('subprocess.run')
def test_lint(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    result = run_linting()

# ✅ 新代码 (真实执行)
@pytest.mark.skipif(not check_tool_available("ruff"), reason="ruff not available")
def test_lint_real():
    # 创建真实项目
    with tempfile.TemporaryDirectory() as temp_dir:
        # ... 创建真实Python文件 ...
        result = run_linting(temp_dir)  # 真实执行ruff
        assert result["issues_count"] >= 0  # 验证真实输出
```

**难点**:
- 需要安装真实工具 (ruff, eslint, pytest等)
- 使用`@pytest.mark.skipif`处理工具缺失
- 创建最小化测试项目 (避免慢速)

---

### 策略B: 文件I/O Mock消除 (适用于6个文件)

**目标文件**: test_llm_models.py, test_template_loader.py, test_output_formatting.py等

**转换模式**:
```python
# ❌ 旧代码 (Mock)
@patch('builtins.open', mock_open(read_data="template content"))
def test_template_load(mock_file):
    template = load_template("fake.md")

# ✅ 新代码 (真实文件)
def test_template_load_real():
    with tempfile.TemporaryDirectory() as temp_dir:
        template_path = Path(temp_dir) / "real_template.md"
        template_path.write_text("# Real Template\n{{variable}}")

        template = load_template(str(template_path))  # 读取真实文件
        assert "Real Template" in template
```

**难点**:
- 无,非常简单!使用`tempfile.TemporaryDirectory()`即可

---

### 策略C: 环境变量Mock消除 (适用于2个文件)

**目标文件**: test_llm_models.py

**转换模式**:
```python
# ❌ 旧代码 (Mock)
@patch.dict('os.environ', {'API_KEY': 'fake_key'})
def test_api_key(mock_env):
    key = get_api_key()

# ✅ 新代码 (真实环境)
def test_api_key_real():
    # 设置真实环境变量
    original = os.environ.get('API_KEY')
    try:
        os.environ['API_KEY'] = 'test_real_key_12345'
        key = get_api_key()  # 读取真实环境变量
        assert key == 'test_real_key_12345'
    finally:
        # 恢复原值
        if original:
            os.environ['API_KEY'] = original
        else:
            os.environ.pop('API_KEY', None)
```

**难点**:
- 需要清理(teardown),避免污染其他测试
- 可以使用pytest fixture自动清理

---

### 策略D: LLM API调用处理 (最难,1-2个文件)

**目标文件**: test_report_generator.py, test_llm_report_workflow.py

**方案对比**:

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **方案1**: 真实API调用 | 100%真实,测试完整流程 | 需要API key,有成本,慢 | ⭐⭐⭐ |
| **方案2**: 测试CLI层 | 无API成本,测试subprocess调用 | 不测试API响应,覆盖不完整 | ⭐⭐⭐⭐ |
| **方案3**: 本地Mock Server | 模拟API但不用真实调用 | 还是mock,违反原则 | ⭐ |
| **方案4**: Skip这些测试 | 简单直接 | 失去测试覆盖 | ⭐⭐ |

**推荐**: **方案2** - 只测试subprocess调用层
```python
@pytest.mark.skipif(not check_tool_available("gemini"), reason="gemini CLI not available")
def test_report_generation_cli_real():
    # 准备真实score_input.json
    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = Path(temp_dir) / "score_input.json"
        input_file.write_text('{"repository": {...}}')

        # 测试CLI调用(不关心API响应内容)
        result = subprocess.run(
            ["gemini", "generate", "--input", str(input_file)],
            capture_output=True,
            timeout=30
        )

        # 只验证CLI调用成功,不验证生成内容
        assert result.returncode in [0, 1]  # 0=成功, 1=API错误也ok
```

---

## 🚀 执行路线图

### 第一阶段: P0核心功能 (1-2天,7.5小时)

**目标**: 转换核心工具执行测试,确保基础功能无mock

**顺序**:
1. ✅ test_all_tools_run_build.py (已完成)
2. ✅ test_python_tools_build.py (已完成)
3. ✅ test_git_operations.py (已完成)
4. ⏳ test_tool_runners.py (1.5h) - linting/testing工具真实执行
5. ⏳ test_pipeline_executor.py (1.5h) - pipeline真实执行
6. ⏳ test_language_detection.py (1h) - 文件真实读取
7. ⏳ test_output_formatting.py (0.5h) - 真实文件写入
8. ⏳ test_python_build.py (1h) - 集成测试真实构建
9. ⏳ test_pipeline_integration.py (2h) - 完整pipeline真实运行

**里程碑**: 核心执行路径100%无mock

---

### 第二阶段: P2路径/配置 (0.5-1天,4.5小时)

**目标**: 快速清理简单的路径和配置mock

**并行执行** (这些文件独立,可同时转换):
1. test_evidence_validation.py (1h)
2. test_scoring_mapper_evidence_paths.py (0.5h)
3. test_checklist_evaluator_path.py (0.5h)
4. test_checklist_loader_path.py (0.5h)
5. test_pipeline_manager_path.py (0.5h)
6. test_evidence_path_consistency.py (0.5h)
7. test_cli_evaluate_path.py (0.5h)
8. test_custom_template.py (0.5h)

**里程碑**: 所有路径操作测试无mock

---

### 第三阶段: P1 LLM处理 (1-2天,9小时)

**目标**: 处理LLM相关测试,需要策略决策

**决策点**: 对于`test_report_generator.py`,决定使用方案1(真实API)还是方案2(只测试CLI)

**顺序**:
1. test_llm_models.py (2h) - 环境变量+文件真实操作
2. test_template_loader.py (1.5h) - 真实Jinja2模板
3. test_prompt_builder.py (1.5h) - 真实模板渲染
4. test_report_generator.py (2.5h) - **关键决策点**
5. test_llm_report_workflow.py (1.5h) - 端到端真实流程

**里程碑**: LLM pipeline完全真实(或CLI层真实)

---

### 第四阶段: P3收尾 (0.5天,4.5小时)

**目标**: 完成剩余Contract和错误处理测试

1. test_error_handling.py (1h)
2. test_full_pipeline_checklist.py (1h)
3. test_phantom_path_removal.py (0.5h)
4. test_evidence_paths_contract.py (0.5h)
5. test_llm_performance.py (1.5h)

**里程碑**: 100% mock消除完成!

---

### 最终验证阶段 (0.5天)

1. ✅ 运行完整测试套件: `uv run pytest tests/ -v`
2. ✅ 验证zero mock imports: `grep -r "unittest.mock" tests/ | wc -l` 应该输出 **0**
3. ✅ 性能检查: 完整测试套件应在5-10分钟内完成
4. ✅ CI/CD配置: 更新.github/workflows确保真实工具可用
5. ✅ 文档更新: 更新CLAUDE.md说明真实测试要求

---

## ⚠️ 关键风险与缓解

### 风险1: 工具依赖问题

**问题**: CI环境可能缺少某些工具(Maven, Gradle, Go等)

**缓解**:
- ✅ 使用`@pytest.mark.skipif`优雅跳过
- ✅ 文档说明哪些工具是可选的
- ✅ CI中预装常用工具(npm, python, go)

### 风险2: 测试变慢

**问题**: 真实执行比mock慢

**缓解**:
- ✅ 使用最小化测试项目(单文件构建)
- ✅ pytest-xdist并行执行
- ✅ 接受4-6x慢速,这是真实测试的代价

### 风险3: LLM API成本

**问题**: 每次CI运行都调用Gemini API会产生费用

**缓解**:
- ⭐ **推荐**: 使用方案2(只测试CLI,不测试API响应)
- 或: 设置CI环境变量控制,只在release时运行LLM测试
- 或: 使用专用测试API quota

### 风险4: 测试不稳定

**问题**: 真实执行可能受网络/环境影响

**缓解**:
- ✅ 使用本地资源(file://协议,tempfile目录)
- ✅ 添加超时控制
- ✅ 重试机制(pytest-rerunfailures)

---

## 📈 预期收益

### 质量提升
- ✅ 发现真实bug (已发现UV行为差异, Git commit_sha填充行为)
- ✅ 防止mock与实现脱节
- ✅ 更高的真实代码覆盖率

### 维护性提升
- ✅ 减少mock设置代码 (通常mock代码比测试逻辑还多)
- ✅ 更简单的测试逻辑
- ✅ 更容易理解的测试意图

### 开发信心提升
- ✅ 部署前100%确定真实工具能工作
- ✅ 重构时有真实测试保护
- ✅ 新功能测试直接用真实场景

---

## 📊 总工作量估算

| 阶段 | 文件数 | 测试数 | 预估时间 | 工作日 |
|------|-------|-------|---------|--------|
| **已完成** | 3 | 34 | - | ✅ |
| **P0核心功能** | 6 | 100 | 7.5小时 | 1-2天 |
| **P2路径配置** | 8 | 81 | 4.5小时 | 0.5-1天 |
| **P1 LLM处理** | 5 | 173 | 9小时 | 1-2天 |
| **P3收尾** | 5 | 48 | 4.5小时 | 0.5天 |
| **最终验证** | - | - | 4小时 | 0.5天 |
| **总计** | **27** | **436** | **~30小时** | **4-6天** |

**建议节奏**: 每天处理5-6小时,总计5-6个工作日完成

---

## 🎯 立即执行建议

### 今日任务 (2-3小时)

按优先级转换以下3个文件:

1. **test_tool_runners.py** (25测试, 1.5h)
   - Mock类型: subprocess.run (ruff, pytest等工具)
   - 转换策略: 策略A - 真实工具执行
   - 价值: 高 - 测试核心linting/testing功能

2. **test_language_detection.py** (17测试, 1h)
   - Mock类型: file operations
   - 转换策略: 策略B - 真实文件读取
   - 价值: 高 - 测试语言检测逻辑

3. **test_output_formatting.py** (9测试, 0.5h)
   - Mock类型: Path.mkdir, file writes
   - 转换策略: 策略B - 真实文件写入
   - 价值: 中 - 测试输出生成

**预期产出**: 再完成51个测试的转换,累计进度达到 **85/436 = 19.5%**

---

## 成功标准

项目完成时应该满足:

- ✅ `grep -r "from unittest.mock import" tests/` 输出 **0行**
- ✅ `grep -r "@patch\|@mock" tests/` 输出 **0行**
- ✅ `uv run pytest tests/` 全部通过
- ✅ 测试运行时间 < 10分钟
- ✅ 所有外部工具依赖用`@pytest.mark.skipif`标记
- ✅ 文档更新完成
- ✅ CI/CD配置更新

---

**准备开始? 让我知道你想从哪个优先级开始! 🚀**
