"""
Performance tests for LLM report generation system.

This module tests performance characteristics of the LLM report generation
pipeline to ensure it meets the requirement of <5 seconds generation time
(excluding external LLM API calls).
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.llm.models.llm_provider_config import LLMProviderConfig
from src.llm.models.report_template import ReportTemplate
from src.llm.prompt_builder import PromptBuilder

# Import the modules to test
from src.llm.report_generator import ReportGenerator
from src.llm.template_loader import TemplateLoader


class TestLLMPerformance:
    """Performance tests for LLM report generation components."""

    @pytest.fixture
    def large_score_input_data(self):
        """Generate large score input data for performance testing."""
        # Create a large evaluation dataset
        checklist_items = []
        for i in range(50):  # 50 checklist items (above normal)
            checklist_items.append({
                "id": f"item_{i:03d}",
                "name": f"Test Item {i}",
                "dimension": "code_quality" if i < 20 else "testing" if i < 35 else "documentation",
                "max_points": 10,
                "evaluation_status": "met" if i % 3 == 0 else "partial" if i % 3 == 1 else "unmet",
                "score": 10.0 if i % 3 == 0 else 5.0 if i % 3 == 1 else 0.0,
                "actual_points": 10.0 if i % 3 == 0 else 5.0 if i % 3 == 1 else 0.0,
                "evidence_references": [
                    {
                        "source": f"evidence_{i}_{j}.txt",
                        "description": f"Evidence item {j} for checklist item {i}: " + ("x" * 100),
                        "confidence": 0.9 - (j * 0.1)
                    }
                    for j in range(5)  # 5 evidence items per checklist item
                ]
            })

        # Create evidence summary with many items
        evidence_summary = []
        for category in ["code_quality", "testing", "documentation", "system"]:
            items = []
            for i in range(20):  # 20 evidence items per category
                items.append({
                    "source": f"{category}_evidence_{i}.txt",
                    "description": f"Detailed evidence for {category} item {i}: " + ("x" * 200),
                    "confidence": 0.95 - (i * 0.01)
                })
            evidence_summary.append({
                "category": category,
                "items": items
            })

        return {
            "schema_version": "1.0.0",
            "repository_info": {
                "url": "https://github.com/large/repository.git",
                "commit_sha": "a" * 40,
                "primary_language": "python",
                "analysis_timestamp": "2025-09-27T10:30:00Z",
                "metrics_source": "output/submission.json"
            },
            "evaluation_result": {
                "checklist_items": checklist_items,
                "total_score": sum(item["score"] for item in checklist_items),
                "max_possible_score": len(checklist_items) * 10,
                "score_percentage": (sum(item["score"] for item in checklist_items) / (len(checklist_items) * 10)) * 100,
                "category_breakdowns": {
                    "code_quality": {"score": 100.0, "actual_points": 100.0, "max_points": 200, "percentage": 50.0},
                    "testing": {"score": 75.0, "actual_points": 75.0, "max_points": 150, "percentage": 50.0},
                    "documentation": {"score": 50.0, "actual_points": 50.0, "max_points": 150, "percentage": 33.3},
                    "system": {"score": 25.0, "actual_points": 25.0, "max_points": 50, "percentage": 50.0}
                },
                "evidence_summary": evidence_summary
            },
            "human_summary": "Large dataset for performance testing with extensive evidence and checklist items."
        }

    @pytest.fixture
    def performance_template_content(self):
        """Template content designed for performance testing."""
        return """# Comprehensive Code Review Report

## Repository Information
- **Repository**: {{repository.url}}
- **Commit**: {{repository.commit_sha}}
- **Language**: {{repository.primary_language}}
- **Analysis Date**: {{repository.analysis_timestamp}}

## Executive Summary
- **Total Score**: {{total.score}}/{{total.max_points}} ({{total.percentage}}%)
- **Grade**: {{total.grade_letter}}
- **Overall Status**: {{total.status}}

## Detailed Analysis

### Successfully Met Criteria ({{met_items|length}} items)
{% for item in met_items %}
#### ✅ {{item.name}}
- **Score**: {{item.score}}/{{item.max_points}}
- **Description**: {{item.description|default("No description available")}}
{% endfor %}

### Partially Met Criteria ({{partial_items|length}} items)
{% for item in partial_items %}
#### ⚠️ {{item.name}}
- **Score**: {{item.score}}/{{item.max_points}}
- **Description**: {{item.description|default("No description available")}}
{% endfor %}

### Unmet Criteria ({{unmet_items|length}} items)
{% for item in unmet_items %}
#### ❌ {{item.name}}
- **Score**: {{item.score}}/{{item.max_points}}
- **Description**: {{item.description|default("No description available")}}
{% endfor %}

## Category Breakdown
{% for category, score in category_scores.items() %}
### {{category|title}}
- **Score**: {{score.score}}/{{score.max_points}} ({{score.percentage}}%)
- **Grade**: {{score.grade_letter}}
- **Status**: {{score.status|title}}
{% endfor %}

## Evidence Summary
{% for evidence in evidence_summary %}
### {{evidence.category|title}} Evidence
{% for item in evidence.items[:3] %}
- **{{item.source}}**: {{item.description}}
{% endfor %}
{% if evidence.truncated %}
*Note: Evidence was truncated for brevity*
{% endif %}
{% endfor %}

{% if warnings %}
## Warnings
{% for warning in warnings %}
- {{warning}}
{% endfor %}
{% endif %}

---
*Report generated on {{generation_time}}*
"""

    @pytest.fixture
    def temp_performance_files(self, large_score_input_data, performance_template_content):
        """Create temporary files for performance testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create score input file
            score_input_path = temp_path / "large_score_input.json"
            with open(score_input_path, 'w') as f:
                json.dump(large_score_input_data, f)

            # Create template file
            template_path = temp_path / "performance_template.md"
            template_path.write_text(performance_template_content)

            yield {
                "score_input": str(score_input_path),
                "template": str(template_path),
                "output_dir": str(temp_path)
            }

    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time

    def test_template_loader_performance(self, temp_performance_files):
        """Test TemplateLoader performance with large templates."""
        loader = TemplateLoader()

        # Test loading performance
        template_config, load_time = self.measure_time(
            loader.load_template, temp_performance_files["template"]
        )

        # Test compilation performance
        compiled_template, compile_time = self.measure_time(
            loader.compile_template, template_config
        )

        # Performance assertions
        assert load_time < 0.1, f"Template loading took {load_time:.3f}s, expected <0.1s"
        assert compile_time < 0.1, f"Template compilation took {compile_time:.3f}s, expected <0.1s"

        # Test caching performance
        cached_template, cached_time = self.measure_time(
            loader.compile_template, template_config
        )

        assert cached_time < 0.01, f"Cached template access took {cached_time:.3f}s, expected <0.01s"
        assert compiled_template is cached_template, "Template caching not working"

    def test_prompt_builder_performance(self, temp_performance_files, large_score_input_data):
        """Test PromptBuilder performance with large datasets."""
        builder = PromptBuilder()
        loader = TemplateLoader()

        # Load template
        template_config = loader.load_template(temp_performance_files["template"])

        # Test prompt building performance
        prompt, build_time = self.measure_time(
            builder.build_prompt, large_score_input_data, template_config
        )

        # Performance assertions
        assert build_time < 1.0, f"Prompt building took {build_time:.3f}s, expected <1.0s"
        assert len(prompt) > 1000, "Generated prompt seems too short"

        # Test validation performance
        validation_issues, validation_time = self.measure_time(
            builder.validate_context_data, large_score_input_data
        )

        assert validation_time < 0.1, f"Data validation took {validation_time:.3f}s, expected <0.1s"
        assert validation_issues == [], "Validation should pass for test data"

    def test_template_context_creation_performance(self, large_score_input_data):
        """Test TemplateContext creation performance with large datasets."""
        from src.llm.models.template_context import TemplateContext

        # Test context creation performance
        context, creation_time = self.measure_time(
            TemplateContext.from_score_input, large_score_input_data
        )

        # Performance assertions
        assert creation_time < 0.5, f"Context creation took {creation_time:.3f}s, expected <0.5s"

        # Test context operations performance
        all_items, items_time = self.measure_time(context.get_all_items)
        assert items_time < 0.01, f"Getting all items took {items_time:.3f}s, expected <0.01s"

        jinja_dict, conversion_time = self.measure_time(context.to_jinja_dict)
        assert conversion_time < 0.1, f"Jinja dict conversion took {conversion_time:.3f}s, expected <0.1s"

    def test_report_generator_pipeline_performance(self, temp_performance_files):
        """Test complete ReportGenerator pipeline performance (excluding LLM call)."""
        generator = ReportGenerator()

        # Mock the LLM call to focus on pipeline performance
        with patch.object(generator, '_call_llm') as mock_llm:
            mock_llm.return_value = "# Mock Report\n\nGenerated in performance test"

            # Mock provider config
            mock_provider = Mock(spec=LLMProviderConfig)
            mock_provider.provider_name = 'performance_test'
            mock_provider.timeout_seconds = 30
            mock_provider.validate_environment.return_value = []
            generator._default_providers = {'performance_test': mock_provider}

            # Test complete pipeline performance
            result, pipeline_time = self.measure_time(
                generator.generate_report,
                temp_performance_files["score_input"],
                output_path=temp_performance_files["output_dir"] + "/performance_report.md",
                template_path=temp_performance_files["template"],
                provider="performance_test"
            )

            # Performance assertions (excluding LLM call time)
            assert pipeline_time < 2.0, f"Pipeline took {pipeline_time:.3f}s, expected <2.0s"
            assert result["success"] is True
            assert "generation_time_seconds" in result

    def test_memory_usage_with_large_datasets(self, large_score_input_data):
        """Test memory efficiency with large datasets."""
        import tracemalloc

        # Start memory tracking
        tracemalloc.start()

        # Create components
        loader = TemplateLoader()
        builder = PromptBuilder()

        # Take memory snapshot
        snapshot1 = tracemalloc.take_snapshot()

        # Process large dataset
        template_config = ReportTemplate(
            name="memory_test",
            file_path="/tmp/memory_test.md",
            description="Memory test template"
        )

        # Mock template compilation to avoid file operations
        with patch.object(loader, 'compile_template') as mock_compile:
            mock_template = Mock()
            mock_template.render.return_value = "Rendered content"
            mock_compile.return_value = mock_template

            # Build prompt with large dataset
            prompt = builder.build_prompt(large_score_input_data, template_config)

        # Take final memory snapshot
        snapshot2 = tracemalloc.take_snapshot()

        # Calculate memory usage
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory_mb = sum(stat.size for stat in top_stats) / 1024 / 1024

        # Stop memory tracking
        tracemalloc.stop()

        # Memory assertions
        assert total_memory_mb < 50, f"Memory usage {total_memory_mb:.1f}MB, expected <50MB"
        assert len(prompt) > 0, "Prompt should be generated"

    def test_concurrent_processing_performance(self, temp_performance_files):
        """Test performance under concurrent processing scenarios."""
        import queue
        import threading

        generator = ReportGenerator()
        results_queue = queue.Queue()
        error_queue = queue.Queue()

        def process_report(thread_id):
            """Process report in separate thread."""
            try:
                with patch.object(generator, '_call_llm') as mock_llm:
                    mock_llm.return_value = f"# Report {thread_id}\n\nGenerated by thread {thread_id}"

                    # Mock provider config
                    mock_provider = Mock(spec=LLMProviderConfig)
                    mock_provider.provider_name = 'concurrent_test'
                    mock_provider.timeout_seconds = 30
                    mock_provider.validate_environment.return_value = []
                    generator._default_providers = {'concurrent_test': mock_provider}

                    start_time = time.perf_counter()
                    result = generator.generate_report(
                        temp_performance_files["score_input"],
                        template_path=temp_performance_files["template"],
                        provider="concurrent_test"
                    )
                    end_time = time.perf_counter()

                    results_queue.put({
                        'thread_id': thread_id,
                        'success': result["success"],
                        'time': end_time - start_time
                    })

            except Exception as e:
                error_queue.put(f"Thread {thread_id} failed: {e}")

        # Start multiple threads
        threads = []
        num_threads = 3

        start_time = time.perf_counter()

        for i in range(num_threads):
            thread = threading.Thread(target=process_report, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())

        # Performance assertions
        assert len(errors) == 0, f"Concurrent processing had errors: {errors}"
        assert len(results) == num_threads, f"Expected {num_threads} results, got {len(results)}"
        assert total_time < 5.0, f"Concurrent processing took {total_time:.3f}s, expected <5.0s"

        # Check individual thread performance
        for result in results:
            assert result["success"] is True
            assert result["time"] < 3.0, f"Thread {result['thread_id']} took {result['time']:.3f}s, expected <3.0s"

    @pytest.mark.parametrize("dataset_size", [10, 50, 100])
    def test_scalability_with_dataset_size(self, dataset_size, performance_template_content):
        """Test performance scaling with different dataset sizes."""
        from src.llm.models.template_context import TemplateContext

        # Generate datasets of different sizes
        checklist_items = []
        for i in range(dataset_size):
            checklist_items.append({
                "id": f"item_{i:03d}",
                "name": f"Test Item {i}",
                "evaluation_status": "met" if i % 2 == 0 else "unmet",
                "score": 10.0 if i % 2 == 0 else 0.0,
                "max_points": 10
            })

        score_data = {
            "repository_info": {
                "url": "https://github.com/test/repo.git",
                "commit_sha": "abc123",
                "primary_language": "python"
            },
            "evaluation_result": {
                "checklist_items": checklist_items,
                "total_score": sum(item["score"] for item in checklist_items),
                "max_possible_score": dataset_size * 10,
                "score_percentage": (sum(item["score"] for item in checklist_items) / (dataset_size * 10)) * 100,
                "category_breakdowns": {}
            }
        }

        # Test context creation performance
        context, creation_time = self.measure_time(
            TemplateContext.from_score_input, score_data
        )

        # Performance should scale reasonably
        expected_time = 0.01 * (dataset_size / 10)  # Linear scaling expectation
        assert creation_time < expected_time * 2, f"Dataset size {dataset_size}: took {creation_time:.3f}s, expected <{expected_time * 2:.3f}s"

        # Test prompt building performance
        builder = PromptBuilder()
        template_config = ReportTemplate(
            name="scale_test",
            file_path="/tmp/scale_test.md",
            description="Scalability test template"
        )

        with patch.object(builder.template_loader, 'compile_template') as mock_compile:
            mock_template = Mock()
            mock_template.render.return_value = performance_template_content
            mock_compile.return_value = mock_template

            prompt, build_time = self.measure_time(
                builder.build_prompt, score_data, template_config
            )

        # Build time should scale reasonably
        expected_build_time = 0.1 * (dataset_size / 10)
        assert build_time < expected_build_time * 2, f"Dataset size {dataset_size}: build took {build_time:.3f}s, expected <{expected_build_time * 2:.3f}s"

    def test_template_rendering_performance(self, performance_template_content):
        """Test Jinja2 template rendering performance with complex templates."""
        from jinja2 import Template

        # Create complex context data
        context_data = {
            'repository': {'url': 'https://github.com/test/repo.git'},
            'total': {'score': 85, 'max_points': 100, 'percentage': 85.0, 'grade_letter': 'B'},
            'met_items': [{'name': f'Item {i}', 'score': 10, 'max_points': 10} for i in range(20)],
            'partial_items': [{'name': f'Partial {i}', 'score': 5, 'max_points': 10} for i in range(10)],
            'unmet_items': [{'name': f'Unmet {i}', 'score': 0, 'max_points': 10} for i in range(5)],
            'category_scores': {
                'code_quality': {'score': 80, 'max_points': 100, 'percentage': 80.0, 'grade_letter': 'B'},
                'testing': {'score': 70, 'max_points': 100, 'percentage': 70.0, 'grade_letter': 'C'},
            },
            'evidence_summary': [
                {
                    'category': 'code_quality',
                    'items': [{'source': f'file_{i}.py', 'description': f'Evidence {i}'} for i in range(10)]
                }
            ],
            'warnings': ['Warning 1', 'Warning 2'],
            'generation_time': '2025-09-27T10:30:00Z'
        }

        # Test template compilation performance
        template, compile_time = self.measure_time(
            Template, performance_template_content
        )

        assert compile_time < 0.01, f"Template compilation took {compile_time:.3f}s, expected <0.01s"

        # Test rendering performance
        rendered, render_time = self.measure_time(
            template.render, **context_data
        )

        assert render_time < 0.1, f"Template rendering took {render_time:.3f}s, expected <0.1s"
        assert len(rendered) > 1000, "Rendered template seems too short"

    def test_end_to_end_performance_benchmark(self, temp_performance_files):
        """Comprehensive end-to-end performance benchmark."""
        # This test validates the overall requirement: <5 seconds generation
        # (excluding external LLM API calls)

        generator = ReportGenerator()

        # Mock external dependencies to focus on internal performance
        with patch.object(generator, '_call_llm') as mock_llm:
            mock_llm.return_value = "# Benchmark Report\n\nGenerated for performance testing"

            # Mock provider config
            mock_provider = Mock(spec=LLMProviderConfig)
            mock_provider.provider_name = 'benchmark'
            mock_provider.timeout_seconds = 30
            mock_provider.validate_environment.return_value = []
            generator._default_providers = {'benchmark': mock_provider}

            # Measure complete pipeline
            result, total_time = self.measure_time(
                generator.generate_report,
                temp_performance_files["score_input"],
                output_path=temp_performance_files["output_dir"] + "/benchmark_report.md",
                template_path=temp_performance_files["template"],
                provider="benchmark"
            )

            # Primary performance requirement
            assert total_time < 5.0, f"Total pipeline took {total_time:.3f}s, requirement is <5.0s"

            # Verify successful completion
            assert result["success"] is True
            assert result["generation_time_seconds"] > 0

            # Verify output file was created
            output_path = Path(temp_performance_files["output_dir"]) / "benchmark_report.md"
            assert output_path.exists(), "Output report file was not created"

        print("\n✅ Performance Benchmark Results:")
        print(f"   Total pipeline time: {total_time:.3f}s (target: <5.0s)")
        print(f"   Status: {'PASS' if total_time < 5.0 else 'FAIL'}")
        print(f"   Report generated successfully: {result['success']}")

    def test_performance_regression_detection(self, temp_performance_files):
        """Test for performance regression detection."""
        # Run the same operation multiple times to detect variance
        generator = ReportGenerator()
        times = []

        with patch.object(generator, '_call_llm') as mock_llm:
            mock_llm.return_value = "# Regression Test Report"

            mock_provider = Mock(spec=LLMProviderConfig)
            mock_provider.provider_name = 'regression'
            mock_provider.timeout_seconds = 30
            mock_provider.validate_environment.return_value = []
            generator._default_providers = {'regression': mock_provider}

            # Run multiple iterations
            for i in range(5):
                _, execution_time = self.measure_time(
                    generator.generate_report,
                    temp_performance_files["score_input"],
                    template_path=temp_performance_files["template"],
                    provider="regression"
                )
                times.append(execution_time)

        # Calculate statistics
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)

        # Performance consistency checks
        assert avg_time < 3.0, f"Average time {avg_time:.3f}s exceeds 3.0s threshold"
        assert max_time < 5.0, f"Maximum time {max_time:.3f}s exceeds 5.0s threshold"
        assert variance < 1.0, f"High variance {variance:.3f} indicates inconsistent performance"

        print("\n📊 Performance Statistics:")
        print(f"   Average: {avg_time:.3f}s")
        print(f"   Min: {min_time:.3f}s")
        print(f"   Max: {max_time:.3f}s")
        print(f"   Variance: {variance:.3f}")
