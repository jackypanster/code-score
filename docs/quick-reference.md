# 检查清单评估系统 - 快速参考

## 🚀 快速开始

```bash
# 1. 运行评估
uv run python -m src.cli.evaluate submission.json --format json --output-dir results/

# 2. 查看结果
cat results/score_input.json | jq .total_score

# 3. 查看详细报告
cat results/evaluation_report.md
```

## 📁 关键文件位置

| 文件 | 路径 | 作用 |
|------|------|------|
| CLI入口 | `src/cli/evaluate.py` | 命令行接口 |
| 核心引擎 | `src/metrics/checklist_evaluator.py` | 评估逻辑 |
| 配置文件 | `specs/002-git-log-docs/contracts/checklist_mapping.yaml` | 检查清单定义 |
| 数据模型 | `src/metrics/models/` | Pydantic模型 |
| 测试套件 | `tests/` | 单元测试和集成测试 |

## 🔧 常用命令

### 开发
```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试
uv run pytest tests/integration/test_checklist_evaluation.py -v

# 检查代码格式
uv run ruff check .

# 同步依赖
uv sync
```

### 调试
```bash
# 查看JSON结构
jq . submission.json

# 验证YAML语法
yamllint checklist_mapping.yaml

# 测试表达式
uv run python -c "
from src.metrics.checklist_evaluator import ChecklistEvaluator
evaluator = ChecklistEvaluator('config.yaml')
# 测试逻辑...
"
```

## 📊 输出格式

### score_input.json 结构
```json
{
  "repository_info": {
    "url": "https://github.com/...",
    "commit_sha": "abc123...",
    "primary_language": "python"
  },
  "checklist_items": [...],
  "total_score": 32.0,
  "max_possible_score": 100,
  "category_breakdowns": {...},
  "evaluation_metadata": {...}
}
```

### 证据文件结构
```
evidence/
├── code_quality/           # 代码质量相关证据
├── testing/               # 测试相关证据
├── documentation/         # 文档相关证据
├── system/               # 系统元数据
└── manifest.json         # 证据清单
```

## ⚡ 表达式语法速查

| 操作符 | 用途 | 示例 |
|--------|------|------|
| `==` | 等于 | `tests_passed == 0` |
| `!=` | 不等于 | `tool_used != "none"` |
| `>`, `>=` | 大于 | `coverage >= 60` |
| `<`, `<=` | 小于 | `errors < 5` |
| `AND` | 逻辑与 | `A AND B` |
| `OR` | 逻辑或 | `A OR B` |
| `BUT` | 等同AND | `A BUT B` (相当于 `A AND B`) |
| `()` | 分组 | `A OR (B AND C)` |
| `.length` | 数组长度 | `errors.length == 0` |

## 🔍 调试检查清单

### 1. 评分为0时检查
- [ ] JSON路径是否正确？
- [ ] 数据类型是否匹配？
- [ ] 表达式语法是否正确？
- [ ] 括号是否配对？

### 2. 表达式不工作时检查
- [ ] 操作符优先级是否正确？
- [ ] 是否需要括号分组？
- [ ] 字段名是否拼写正确？
- [ ] 数组比较是否使用了正确的语法？

### 3. 证据文件缺失时检查
- [ ] 输出目录权限是否正确？
- [ ] 磁盘空间是否足够？
- [ ] 证据追踪器是否正确初始化？

## 🏗️ 扩展开发

### 添加新检查项
1. 编辑 `checklist_mapping.yaml`
2. 添加evaluation_criteria
3. 设置metrics_mapping
4. 运行测试验证

```yaml
- id: "new_check"
  name: "新检查项"
  dimension: "code_quality"
  max_points: 5
  evaluation_criteria:
    met:
      - your_condition == true
  metrics_mapping:
    source_path: "$.metrics.your_data"
```

### 自定义输出格式
1. 创建新的生成器函数
2. 注册到CLI选项
3. 实现格式化逻辑

```python
def generate_custom_format(result: EvaluationResult) -> str:
    # 实现自定义格式
    return formatted_output
```

## 📈 性能优化

### 批量处理
```python
# ✅ 正确: 重用评估器
evaluator = ChecklistEvaluator("config.yaml")
for file in files:
    result = evaluator.evaluate_from_file(file)

# ❌ 错误: 重复创建评估器
for file in files:
    evaluator = ChecklistEvaluator("config.yaml")  # 低效
    result = evaluator.evaluate_from_file(file)
```

### 内存管理
```python
# 大批量处理时定期清理
if file_count % 100 == 0:
    tracker.clear_cache()
    gc.collect()
```

## 🚨 常见错误及解决

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `FileNotFoundError` | 文件路径错误 | 检查文件路径和权限 |
| `ValidationError` | 数据格式错误 | 验证JSON/YAML格式 |
| `ExpressionError` | 表达式语法错误 | 检查表达式语法 |
| `KeyError` | 缺少必要字段 | 检查数据结构完整性 |

## 📞 获取帮助

### 查看帮助
```bash
uv run python -m src.cli.evaluate --help
```

### 查看配置示例
```bash
cat specs/002-git-log-docs/contracts/checklist_mapping.yaml
```

### 运行示例
```bash
# 使用示例数据测试
uv run python -m src.cli.evaluate output/submission.json --format json --output-dir test_output/
```

---

**快速链接**:
- [完整文档](./checklist-evaluation-progress.md)
- [API参考](./api-reference.md)
- [故障排除](./troubleshooting.md)

**最后更新**: 2025-09-27