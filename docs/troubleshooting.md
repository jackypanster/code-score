# 检查清单评估系统 - 故障排除指南

## 常见问题和解决方案

### 1. 评分异常低或为0

#### 症状
- 评估结果显示分数为0或异常低
- 所有项目显示为"unmet"状态

#### 可能原因和解决方案

**A. 数据路径错误**
```bash
# 检查submission.json结构
jq . submission.json | head -20

# 验证路径是否存在
jq '.metrics.code_quality.lint_results' submission.json
```

**B. 字段类型不匹配**
```yaml
# 错误: 数组与字符串比较
- execution.errors == "[]"  # ❌

# 正确: 数组与数组比较
- execution.errors == []    # ✅
```

**C. 表达式语法错误**
```yaml
# 错误: 缺少括号
- coverage >= 30 OR coverage == null AND tests >= 5  # ❌

# 正确: 使用括号明确优先级
- coverage >= 30 OR (coverage == null AND tests >= 5)  # ✅
```

### 2. 证据文件生成失败

#### 症状
- 输出目录中缺少evidence文件夹
- evidence文件夹为空

#### 解决方案

**检查输出目录权限**
```bash
# 确保输出目录有写权限
ls -la /path/to/output/directory
chmod 755 /path/to/output/directory
```

**验证证据追踪器配置**
```python
# 检查EvidenceTracker初始化
tracker = EvidenceTracker(output_dir="./evidence")
print(f"输出目录: {tracker.output_dir}")
```

### 3. YAML配置加载错误

#### 症状
- `yaml.scanner.ScannerError`
- `yaml.parser.ParserError`

#### 解决方案

**检查YAML语法**
```bash
# 使用yamllint检查语法
yamllint specs/002-git-log-docs/contracts/checklist_mapping.yaml

# 或使用Python验证
python -c "import yaml; yaml.safe_load(open('checklist_mapping.yaml'))"
```

**常见YAML错误**
```yaml
# 错误: 缩进不一致
evaluation_criteria:
  met:
  - condition1  # ❌ 缩进错误

# 正确: 一致的缩进
evaluation_criteria:
  met:
    - condition1  # ✅
```

### 4. 表达式评估错误

#### 症状
- 逻辑表达式结果不符合预期
- 复杂条件评估失败

#### 调试方法

**测试单个表达式**
```python
# 分解复杂表达式进行调试
expression = "tests_passed > 0 AND execution.errors == []"

# 测试每个部分
part1 = evaluator._evaluate_single_criterion("tests_passed > 0", data, [], mapping)
part2 = evaluator._evaluate_single_criterion("execution.errors == []", data, [], mapping)

print(f"Part 1: {part1}, Part 2: {part2}")
print(f"Expected: {part1 and part2}")
```

**查看详细证据**
```bash
# 检查证据文件了解评估细节
cat output/evidence/testing/testing_results_file_check.json | jq .
```

### 5. 性能问题

#### 症状
- 评估过程耗时过长
- 内存使用过高

#### 优化建议

**批量处理优化**
```python
# 重用评估器实例
evaluator = ChecklistEvaluator("config.yaml")

for file in submission_files:
    result = evaluator.evaluate_from_file(file)
    # 处理结果...
    # 避免重复创建评估器
```

**内存管理**
```python
# 大批量处理时清理证据数据
tracker = EvidenceTracker(output_dir)
for i, file in enumerate(files):
    # 处理文件...
    if i % 100 == 0:  # 每100个文件清理一次
        tracker.clear_cache()
```

### 6. JSON Schema验证失败

#### 症状
- `ValidationError` from Pydantic
- JSON输出格式不正确

#### 解决方案

**验证输入数据格式**
```bash
# 检查submission.json是否符合预期格式
jsonschema -i submission.json schema.json
```

**检查模型定义**
```python
# 验证Pydantic模型
from src.metrics.models.score_input import ScoreInput

try:
    score_input = ScoreInput(**data)
except ValidationError as e:
    print(f"验证错误: {e}")
```

### 7. CLI命令问题

#### 症状
- 命令行参数错误
- CLI无法找到模块

#### 解决方案

**检查Python路径**
```bash
# 确保在正确的项目目录
pwd
ls src/cli/evaluate.py

# 使用正确的模块路径
uv run python -m src.cli.evaluate --help
```

**验证依赖安装**
```bash
# 检查必要依赖
uv run python -c "import yaml, pydantic, click"

# 重新安装依赖
uv sync
```

### 8. 权限和路径问题

#### 症状
- `PermissionError`
- `FileNotFoundError`

#### 解决方案

**检查文件权限**
```bash
# 检查输入文件权限
ls -la submission.json

# 检查输出目录权限
ls -la output/
```

**使用绝对路径**
```bash
# 避免相对路径问题
uv run python -m src.cli.evaluate /absolute/path/to/submission.json
```

## 调试技巧

### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 手动测试表达式

```python
# 在Python REPL中测试
from src.metrics.checklist_evaluator import ChecklistEvaluator

evaluator = ChecklistEvaluator("config.yaml")
test_data = {...}
result = evaluator._evaluate_logical_expression("your_expression", test_data, [], {})
print(result)
```

### 3. 查看中间结果

```python
# 添加调试输出
def debug_evaluate(expression, data):
    print(f"Evaluating: {expression}")
    result = evaluator._evaluate_logical_expression(expression, data, [], {})
    print(f"Result: {result}")
    return result
```

### 4. 验证数据结构

```bash
# 使用jq检查JSON结构
jq '.metrics | keys' submission.json
jq '.execution | keys' submission.json
```

## 获取帮助

### 1. 查看日志文件
```bash
# 检查系统日志
tail -f /var/log/code-score.log
```

### 2. 运行测试套件
```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试
uv run pytest tests/integration/test_checklist_evaluation.py -v
```

### 3. 生成调试报告
```bash
# 生成详细的评估报告
uv run python -m src.cli.evaluate submission.json --format markdown --output-dir debug/
```

### 4. 联系开发团队
- 提供完整的错误信息
- 包含相关的输入文件和配置
- 描述预期行为vs实际行为
- 包含系统环境信息

---

**最后更新**: 2025-09-27
**版本**: 1.0.0