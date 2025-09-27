# Checklist Evaluation API Reference

## 概述

本文档描述了检查清单评估系统的API接口和核心组件，便于开发人员理解和扩展功能。

## 核心组件

### 1. ChecklistEvaluator

主要的评估引擎，负责将指标数据映射到检查清单评估结果。

```python
from src.metrics.checklist_evaluator import ChecklistEvaluator

# 初始化评估器
evaluator = ChecklistEvaluator("path/to/checklist_mapping.yaml")

# 从文件评估
result = evaluator.evaluate_from_file("submission.json")

# 从字典评估
result = evaluator.evaluate_from_dict(submission_data)
```

#### 关键方法

- `evaluate_from_file(submission_path: str) -> EvaluationResult`
- `evaluate_from_dict(submission_data: Dict, submission_path: str) -> EvaluationResult`
- `evaluate_from_string(submission_json: str) -> EvaluationResult`

### 2. EvidenceTracker

证据收集和管理系统。

```python
from src.metrics.evidence_tracker import EvidenceTracker

tracker = EvidenceTracker(output_dir="./evidence")
tracker.add_evidence(evidence_reference)
evidence_files = tracker.save_evidence_files()
```

### 3. ScoringMapper

将评估结果转换为LLM评分输入格式。

```python
from src.metrics.scoring_mapper import ScoringMapper

mapper = ScoringMapper()
score_input = mapper.create_score_input(evaluation_result, repository_info)
```

## 数据模型

### ChecklistItem

单个检查清单项的数据结构。

```python
from src.metrics.models.checklist_item import ChecklistItem

item = ChecklistItem(
    id="code_quality_lint",
    name="代码风格检查",
    dimension="code_quality",
    max_points=8,
    description="提供代码风格检查工具的执行记录",
    evaluation_status="met",  # "met" | "partial" | "unmet"
    score=8.0,
    evidence_references=[...],
    evaluation_details={...}
)
```

### EvaluationResult

完整的评估结果数据结构。

```python
from src.metrics.models.evaluation_result import EvaluationResult

result = EvaluationResult(
    checklist_items=[...],           # List[ChecklistItem]
    total_score=32.0,               # float
    max_possible_score=100,         # int
    score_percentage=32.0,          # float
    category_breakdowns={...},      # Dict[str, CategoryBreakdown]
    evaluation_metadata={...},      # EvaluationMetadata
    evidence_summary=[...]          # List[str]
)
```

### EvidenceReference

证据引用的数据结构。

```python
from src.metrics.models.evidence_reference import EvidenceReference

evidence = EvidenceReference(
    source_type="file_check",              # "file_check" | "calculation" | "manual"
    source_path="$.metrics.code_quality.lint_results.passed",
    description="检查lint_results.passed: expected True, got False",
    confidence=0.85,                       # 0.0-1.0
    raw_data="False",
    timestamp="2025-09-27T13:49:17.327224"
)
```

## CLI接口

### evaluate命令

```bash
# 基本用法
uv run python -m src.cli.evaluate SUBMISSION_FILE [OPTIONS]

# 选项
--format [json|markdown]    # 输出格式 (默认: json)
--output-dir PATH          # 输出目录 (默认: ./evaluation_output)
--help                     # 显示帮助信息
```

### 示例

```bash
# 生成JSON格式输出
uv run python -m src.cli.evaluate submission.json --format json --output-dir ./results

# 生成Markdown格式输出
uv run python -m src.cli.evaluate submission.json --format markdown --output-dir ./reports
```

## 配置格式

### checklist_mapping.yaml

检查清单配置文件的结构：

```yaml
checklist_items:
  - id: "code_quality_lint"
    name: "代码风格检查"
    dimension: "code_quality"
    max_points: 8
    description: "提供代码风格检查工具的执行记录"
    evaluation_criteria:
      met:
        - lint_results.passed == true
      partial:
        - lint_results.passed == false BUT evidence of attempt
      unmet:
        - lint_results.tool_used == "none"
    metrics_mapping:
      source_path: "$.metrics.code_quality.lint_results"
      required_fields: ["tool_used", "passed"]
```

### 表达式语法

支持的操作符和语法：

- **比较操作符**: `==`, `!=`, `>`, `>=`, `<`, `<=`
- **逻辑操作符**: `AND`, `OR`, `BUT`
- **括号**: `(` `)` 用于分组
- **数组操作**: `.length` 获取数组长度
- **字面量**: `[]`, `{}`, `null`, `true`, `false`, 数字, 字符串

### 表达式示例

```yaml
# 简单比较
- tests_passed > 0

# 逻辑组合
- tests_passed > 0 AND errors == []

# 复杂条件
- coverage >= 60 OR (coverage == null AND tests_run >= 5)

# 数组长度检查
- execution.errors.length == 0

# BUT条件 (等同于AND)
- tests_passed > 0 BUT warnings.length > 0
```

## 扩展开发

### 添加新的评估标准

1. 修改 `checklist_mapping.yaml` 添加新项目
2. 确保数据路径在 `submission.json` 中存在
3. 运行测试验证新标准工作正常

### 自定义证据类型

```python
# 扩展证据类型
class CustomEvidenceReference(EvidenceReference):
    custom_field: str = ""

    def to_dict(self) -> dict:
        base_dict = super().to_dict()
        base_dict["custom_field"] = self.custom_field
        return base_dict
```

### 添加新的输出格式

```python
# 在 output_generators.py 中添加新的生成器
def generate_custom_format(evaluation_result: EvaluationResult) -> str:
    # 实现自定义格式生成逻辑
    pass
```

## 错误处理

### 常见错误类型

- `FileNotFoundError`: 找不到配置文件或输入文件
- `ValueError`: 无效的JSON或YAML格式
- `ValidationError`: Pydantic模型验证失败
- `ExpressionError`: 表达式语法错误

### 错误处理示例

```python
try:
    result = evaluator.evaluate_from_file("submission.json")
except FileNotFoundError:
    print("找不到输入文件")
except ValueError as e:
    print(f"数据格式错误: {e}")
except Exception as e:
    print(f"评估过程出错: {e}")
```

## 性能考虑

### 优化建议

1. **批量处理**: 重用 `ChecklistEvaluator` 实例
2. **内存管理**: 大批量处理时定期清理证据数据
3. **并行处理**: 多个文件可以并行评估
4. **缓存**: 相同配置可以缓存加载结果

### 性能指标

- **单次评估**: ~10ms
- **内存占用**: ~10MB per evaluation
- **并发支持**: 无状态设计，支持多线程

---

**版本**: 1.0.0
**最后更新**: 2025-09-27
**维护者**: Claude Code Assistant