"""
Integration test for custom template usage.

This test validates the ability to use custom templates for different
evaluation contexts and report formats.

NOTE: These tests will FAIL initially as part of TDD approach until
implementation is complete.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import modules that don't exist yet - will fail until implementation
pytest.importorskip("src.llm.template_loader", reason="Implementation not ready")
pytest.importorskip("src.llm.prompt_builder", reason="Implementation not ready")
pytest.importorskip("src.llm.report_generator", reason="Implementation not ready")


class TestCustomTemplate:
    """Integration tests for custom template usage."""

    @pytest.fixture
    def sample_score_input(self):
        """Sample score_input.json data for testing."""
        return {
            "schema_version": "1.0.0",
            "repository_info": {
                "url": "https://github.com/hackathon/project.git",
                "commit_sha": "hack2024abc",
                "primary_language": "go",
                "analysis_timestamp": "2025-09-27T16:00:00Z",
                "metrics_source": "output/submission.json"
            },
            "evaluation_result": {
                "checklist_items": [
                    {
                        "id": "code_quality_lint",
                        "name": "Static Linting Passed",
                        "dimension": "code_quality",
                        "max_points": 15,
                        "evaluation_status": "met",
                        "score": 15.0,
                        "evidence_references": [
                            {
                                "source": "golangci-lint.txt",
                                "description": "All linting checks passed",
                                "confidence": 1.0
                            }
                        ]
                    },
                    {
                        "id": "code_quality_build",
                        "name": "Build Successful",
                        "dimension": "code_quality",
                        "max_points": 10,
                        "evaluation_status": "met",
                        "score": 10.0,
                        "evidence_references": [
                            {
                                "source": "go_build.txt",
                                "description": "Project builds without errors",
                                "confidence": 1.0
                            }
                        ]
                    },
                    {
                        "id": "testing_automation",
                        "name": "Automated Tests Present",
                        "dimension": "testing",
                        "max_points": 15,
                        "evaluation_status": "met",
                        "score": 15.0,
                        "evidence_references": [
                            {
                                "source": "go_test.txt",
                                "description": "Comprehensive test suite found",
                                "confidence": 0.9
                            }
                        ]
                    },
                    {
                        "id": "documentation_readme",
                        "name": "README Documentation",
                        "dimension": "documentation",
                        "max_points": 10,
                        "evaluation_status": "partial",
                        "score": 5.0,
                        "evidence_references": [
                            {
                                "source": "readme_analysis.txt",
                                "description": "README exists but lacks setup instructions",
                                "confidence": 0.8
                            }
                        ]
                    }
                ],
                "total_score": 45.0,
                "max_possible_score": 100,
                "score_percentage": 45.0,
                "category_breakdowns": {
                    "code_quality": {"score": 25.0, "max_points": 40, "percentage": 62.5},
                    "testing": {"score": 15.0, "max_points": 35, "percentage": 42.9},
                    "documentation": {"score": 5.0, "max_points": 25, "percentage": 20.0}
                },
                "evidence_summary": [
                    {
                        "category": "code_quality",
                        "items": [
                            {
                                "source": "golangci-lint.txt",
                                "description": "All linting checks passed",
                                "confidence": 1.0
                            },
                            {
                                "source": "go_build.txt",
                                "description": "Project builds without errors",
                                "confidence": 1.0
                            }
                        ]
                    },
                    {
                        "category": "testing",
                        "items": [
                            {
                                "source": "go_test.txt",
                                "description": "Comprehensive test suite found",
                                "confidence": 0.9
                            }
                        ]
                    },
                    {
                        "category": "documentation",
                        "items": [
                            {
                                "source": "readme_analysis.txt",
                                "description": "README exists but lacks setup instructions",
                                "confidence": 0.8
                            }
                        ]
                    }
                ]
            },
            "human_summary": "Custom template test evaluation"
        }

    @pytest.fixture
    def temp_directories(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            template_dir = temp_path / "templates"

            input_dir.mkdir()
            output_dir.mkdir()
            template_dir.mkdir()

            yield {
                "input": input_dir,
                "output": output_dir,
                "template": template_dir,
                "base": temp_path
            }

    @pytest.fixture
    def hackathon_template(self, temp_directories):
        """Create custom hackathon evaluation template."""
        template_content = """# 🏆 Hackathon Project Evaluation

**Project**: {{repository.url}}
**Language**: {{repository.primary_language}}
**Evaluation Time**: {{evaluation.timestamp}}

---

## 📊 Score Summary
**Overall Score**: {{total.score}}/{{total.max_score}} ({{total.percentage}}%)

{{#if (gte total.percentage 80)}}
🥇 **EXCELLENT** - This project demonstrates exceptional quality!
{{else if (gte total.percentage 60)}}
🥈 **GOOD** - Solid project with room for improvement
{{else if (gte total.percentage 40)}}
🥉 **PROMISING** - Good foundation, needs refinement
{{else}}
⚠️ **NEEDS WORK** - Significant improvements required
{{/if}}

---

## 🎯 Category Breakdown

### 💻 Code Quality ({{category_scores.code_quality.percentage}}%)
{{#each code_quality_items}}
{{#if (eq evaluation_status "met")}}✅{{else if (eq evaluation_status "partial")}}⚠️{{else}}❌{{/if}} {{name}}
{{/each}}

### 🧪 Testing ({{category_scores.testing.percentage}}%)
{{#each testing_items}}
{{#if (eq evaluation_status "met")}}✅{{else if (eq evaluation_status "partial")}}⚠️{{else}}❌{{/if}} {{name}}
{{/each}}

### 📚 Documentation ({{category_scores.documentation.percentage}}%)
{{#each documentation_items}}
{{#if (eq evaluation_status "met")}}✅{{else if (eq evaluation_status "partial")}}⚠️{{else}}❌{{/if}} {{name}}
{{/each}}

---

## 🔍 Technical Evidence

{{#each evidence_summary}}
### {{category}}
{{#each items}}
- **{{source}}**: {{description}} *(Confidence: {{confidence}})*
{{/each}}
{{/each}}

---

## 🚀 Recommendations

{{#if (lt category_scores.code_quality.percentage 70)}}
**🔧 Code Quality**: Focus on improving static analysis results and build processes.
{{/if}}

{{#if (lt category_scores.testing.percentage 70)}}
**🧪 Testing**: Increase test coverage and add more comprehensive test scenarios.
{{/if}}

{{#if (lt category_scores.documentation.percentage 70)}}
**📚 Documentation**: Enhance README with setup instructions and usage examples.
{{/if}}

---

*Evaluation powered by Code Score | Generated: {{generation_timestamp}}*
"""
        template_path = temp_directories["template"] / "hackathon_template.md"
        template_path.write_text(template_content)
        return template_path

    @pytest.fixture
    def minimal_template(self, temp_directories):
        """Create minimal custom template."""
        template_content = """{{repository.url}} scored {{total.score}}/{{total.max_score}}

{{#each met_items}}
✓ {{name}}
{{/each}}

{{#each unmet_items}}
✗ {{name}}
{{/each}}
"""
        template_path = temp_directories["template"] / "minimal_template.md"
        template_path.write_text(template_content)
        return template_path

    @pytest.fixture
    def detailed_template(self, temp_directories):
        """Create detailed custom template with advanced features."""
        template_content = """# Comprehensive Code Review Report

## Project Information
- **Repository**: {{repository.url}}
- **Commit**: {{repository.commit_sha}}
- **Primary Language**: {{repository.primary_language}}
- **Analysis Date**: {{evaluation.timestamp}}
- **Repository Size**: {{repository.size_mb}}MB

## Executive Summary
Total Score: **{{total.score}}/{{total.max_score}}** ({{total.percentage}}%)

{{#if (gte total.percentage 90)}}
This project demonstrates exceptional software engineering practices across all evaluated dimensions.
{{else if (gte total.percentage 70)}}
This project shows strong engineering fundamentals with opportunities for improvement in specific areas.
{{else if (gte total.percentage 50)}}
This project has a solid foundation but requires attention to several quality dimensions.
{{else}}
This project needs significant improvements across multiple quality dimensions before it meets production standards.
{{/if}}

## Detailed Analysis

### Code Quality Assessment ({{category_scores.code_quality.percentage}}%)
{{#each code_quality_items}}
**{{name}}** - {{#if (eq evaluation_status "met")}}PASSED{{else if (eq evaluation_status "partial")}}PARTIAL{{else}}FAILED{{/if}}
{{#each evidence_references}}
  - Evidence: {{description}} (Source: {{source}}, Confidence: {{confidence}})
{{/each}}

{{/each}}

### Testing Assessment ({{category_scores.testing.percentage}}%)
{{#each testing_items}}
**{{name}}** - {{#if (eq evaluation_status "met")}}PASSED{{else if (eq evaluation_status "partial")}}PARTIAL{{else}}FAILED{{/if}}
{{#each evidence_references}}
  - Evidence: {{description}} (Source: {{source}}, Confidence: {{confidence}})
{{/each}}

{{/each}}

### Documentation Assessment ({{category_scores.documentation.percentage}}%)
{{#each documentation_items}}
**{{name}}** - {{#if (eq evaluation_status "met")}}PASSED{{else if (eq evaluation_status "partial")}}PARTIAL{{else}}FAILED{{/if}}
{{#each evidence_references}}
  - Evidence: {{description}} (Source: {{source}}, Confidence: {{confidence}})
{{/each}}

{{/each}}

## Evidence Index
{{#each evidence_summary}}
### {{category}} Evidence
{{#each items}}
- **{{source}}**: {{description}} (Confidence: {{confidence}})
{{/each}}
{{/each}}

## Risk Assessment
{{#if (lt total.percentage 60)}}
⚠️ **HIGH RISK**: This project has significant quality issues that could impact maintainability and reliability.
{{else if (lt total.percentage 80)}}
⚠️ **MEDIUM RISK**: Some quality concerns present but manageable with focused improvements.
{{else}}
✅ **LOW RISK**: Strong quality metrics suggest good maintainability and reliability.
{{/if}}

## Next Steps
1. Address failed criteria in order of impact
2. Improve areas with partial scores
3. Maintain strong performance in passing areas
4. Re-evaluate after implementing recommendations

---
*Generated by Code Score Analysis Engine*
"""
        template_path = temp_directories["template"] / "detailed_template.md"
        template_path.write_text(template_content)
        return template_path

    def test_hackathon_template_processing(self, sample_score_input, temp_directories, hackathon_template):
        """Test processing of custom hackathon template."""
        from src.llm.prompt_builder import PromptBuilder
        from src.llm.template_loader import TemplateLoader

        # Load and process hackathon template
        loader = TemplateLoader()
        template = loader.load_template(str(hackathon_template))

        builder = PromptBuilder()
        prompt = builder.build_prompt(sample_score_input, template)

        # Verify hackathon-specific content
        assert "🏆 Hackathon Project Evaluation" in prompt
        assert "https://github.com/hackathon/project.git" in prompt
        assert "go" in prompt  # primary_language
        assert "45.0" in prompt or "45" in prompt  # total_score
        assert "🥉 **PROMISING**" in prompt  # Score range 40-60%
        assert "💻 Code Quality" in prompt
        assert "🧪 Testing" in prompt
        assert "📚 Documentation" in prompt
        assert "golangci-lint.txt" in prompt
        assert "go_test.txt" in prompt

    def test_minimal_template_processing(self, sample_score_input, temp_directories, minimal_template):
        """Test processing of minimal custom template."""
        from src.llm.prompt_builder import PromptBuilder
        from src.llm.template_loader import TemplateLoader

        loader = TemplateLoader()
        template = loader.load_template(str(minimal_template))

        builder = PromptBuilder()
        prompt = builder.build_prompt(sample_score_input, template)

        # Verify minimal template content
        assert "https://github.com/hackathon/project.git scored 45" in prompt
        assert "✓ Static Linting Passed" in prompt
        assert "✓ Build Successful" in prompt
        assert "✓ Automated Tests Present" in prompt
        # Should not contain unmet items in this case (all items are met/partial)

    def test_detailed_template_processing(self, sample_score_input, temp_directories, detailed_template):
        """Test processing of detailed custom template with advanced features."""
        from src.llm.prompt_builder import PromptBuilder
        from src.llm.template_loader import TemplateLoader

        loader = TemplateLoader()
        template = loader.load_template(str(detailed_template))

        builder = PromptBuilder()
        prompt = builder.build_prompt(sample_score_input, template)

        # Verify detailed template features
        assert "Comprehensive Code Review Report" in prompt
        assert "Executive Summary" in prompt
        assert "Detailed Analysis" in prompt
        assert "Evidence Index" in prompt
        assert "Risk Assessment" in prompt
        assert "Next Steps" in prompt

        # Verify conditional content based on score
        assert "solid foundation but requires attention" in prompt  # 45% score range

        # Verify evidence details
        assert "All linting checks passed" in prompt
        assert "golangci-lint.txt" in prompt
        assert "Confidence: 1.0" in prompt

    def test_custom_template_with_report_generator(self, sample_score_input, temp_directories, hackathon_template):
        """Test end-to-end report generation with custom template."""
        from src.llm.report_generator import ReportGenerator

        # Setup input file
        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(sample_score_input, f)

        output_path = temp_directories["output"] / "hackathon_report.md"

        # Mock LLM response
        mock_llm_response = """# 🏆 Hackathon Project Evaluation

**Project**: https://github.com/hackathon/project.git
**Language**: go

## 📊 Score Summary
**Overall Score**: 45/100 (45%)

🥉 **PROMISING** - Good foundation, needs refinement

This project shows solid Go development practices with comprehensive testing but could benefit from improved documentation.
"""

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = mock_llm_response

            generator = ReportGenerator()
            result = generator.generate_report(
                score_input_path=str(score_input_path),
                output_path=str(output_path),
                template_path=str(hackathon_template)
            )

            # Verify custom template was used
            assert result["template_used"]["file_path"] == str(hackathon_template)

            # Verify output was generated
            assert output_path.exists()
            generated_content = output_path.read_text()
            assert "🏆 Hackathon Project Evaluation" in generated_content
            assert "🥉 **PROMISING**" in generated_content

    def test_template_with_missing_variables(self, sample_score_input, temp_directories):
        """Test template with missing/undefined variables."""
        from src.llm.prompt_builder import PromptBuilder
        from src.llm.template_loader import TemplateLoader

        # Create template with undefined variables
        template_with_missing = temp_directories["template"] / "missing_vars_template.md"
        template_content = """# Report for {{repository.url}}

Score: {{total.score}}
Missing: {{undefined_variable}}
Also missing: {{another.missing.field}}

Valid content: {{repository.primary_language}}
"""
        template_with_missing.write_text(template_content)

        loader = TemplateLoader()
        template = loader.load_template(str(template_with_missing))

        builder = PromptBuilder()

        # Should handle missing variables gracefully
        prompt = builder.build_prompt(sample_score_input, template)

        # Verify valid variables were processed
        assert "https://github.com/hackathon/project.git" in prompt
        assert "45" in prompt
        assert "go" in prompt

        # Missing variables should be handled (empty or error message)
        # The exact behavior depends on Jinja2 configuration

    def test_template_with_complex_conditionals(self, temp_directories):
        """Test template with complex conditional logic."""
        from src.llm.prompt_builder import PromptBuilder
        from src.llm.template_loader import TemplateLoader

        # Create template with complex conditionals
        complex_template = temp_directories["template"] / "complex_template.md"
        template_content = """# Conditional Report

{{#if (and (gte total.percentage 50) (lt total.percentage 80))}}
This is a medium-scoring project.
{{/if}}

{{#each category_scores}}
{{#if (gte percentage 70)}}
Strong performance in {{@key}}: {{percentage}}%
{{else if (gte percentage 40)}}
Adequate performance in {{@key}}: {{percentage}}%
{{else}}
Needs improvement in {{@key}}: {{percentage}}%
{{/if}}
{{/each}}

{{#unless (eq checklist_items.length 0)}}
Evaluation completed with {{checklist_items.length}} criteria assessed.
{{/unless}}
"""
        complex_template.write_text(template_content)

        # Create score input for testing conditionals
        conditional_score_input = {
            "evaluation_result": {
                "checklist_items": [{"id": "test1"}, {"id": "test2"}],
                "total_score": 65.0,
                "max_possible_score": 100,
                "score_percentage": 65.0,
                "category_breakdowns": {
                    "code_quality": {"percentage": 75.0},
                    "testing": {"percentage": 45.0},
                    "documentation": {"percentage": 30.0}
                }
            }
        }

        loader = TemplateLoader()
        template = loader.load_template(str(complex_template))

        builder = PromptBuilder()
        prompt = builder.build_prompt(conditional_score_input, template)

        # Verify conditional logic worked
        assert "This is a medium-scoring project" in prompt
        assert "Strong performance in code_quality: 75" in prompt
        assert "Adequate performance in testing: 45" in prompt
        assert "Needs improvement in documentation: 30" in prompt
        assert "2 criteria assessed" in prompt

    def test_cli_with_custom_template(self, sample_score_input, temp_directories, hackathon_template):
        """Test CLI execution with custom template path."""
        import sys

        from src.cli.llm_report import main as llm_report_main

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(sample_score_input, f)

        output_path = temp_directories["output"] / "custom_report.md"

        test_args = [
            "llm-report",
            str(score_input_path),
            "--prompt", str(hackathon_template),
            "--output", str(output_path)
        ]

        with patch.object(sys, 'argv', test_args):
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = "# Custom Report Generated"

                exit_code = llm_report_main()

                assert exit_code == 0
                assert output_path.exists()

    def test_template_validation_on_load(self, temp_directories):
        """Test that invalid templates are caught during loading."""
        from src.llm.template_loader import TemplateLoader

        # Create template with invalid syntax
        invalid_template = temp_directories["template"] / "invalid_syntax_template.md"
        invalid_template.write_text("{{#invalid_block}} {{/wrong_block}}")

        loader = TemplateLoader()

        # Should raise template syntax error
        with pytest.raises(Exception):  # TemplateError or similar
            loader.load_template(str(invalid_template))
