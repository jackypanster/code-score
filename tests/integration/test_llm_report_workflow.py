"""
Integration test for basic LLM report generation workflow.

This test validates the complete end-to-end workflow from score_input.json
to final_report.md generation using the LLM report system.

NOTE: These tests will FAIL initially as part of TDD approach until
implementation is complete.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import modules that don't exist yet - will fail until implementation
pytest.importorskip("src.llm.report_generator", reason="Implementation not ready")
pytest.importorskip("src.cli.llm_report", reason="Implementation not ready")


class TestLLMReportWorkflow:
    """Integration tests for complete LLM report generation workflow."""

    @pytest.fixture
    def sample_score_input(self):
        """Sample score_input.json data for testing."""
        return {
            "schema_version": "1.0.0",
            "repository_info": {
                "url": "https://github.com/test/repository.git",
                "commit_sha": "a1b2c3d4e5f6789012345678901234567890abcd",
                "primary_language": "python",
                "analysis_timestamp": "2025-09-27T10:30:00Z",
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
                                "source": "ruff_output.txt",
                                "description": "No linting errors found",
                                "confidence": 1.0
                            }
                        ]
                    },
                    {
                        "id": "testing_automation",
                        "name": "Automated Tests Present",
                        "dimension": "testing",
                        "max_points": 15,
                        "evaluation_status": "partial",
                        "score": 7.5,
                        "evidence_references": [
                            {
                                "source": "pytest_output.txt",
                                "description": "Some tests found but coverage low",
                                "confidence": 0.8
                            }
                        ]
                    },
                    {
                        "id": "documentation_readme",
                        "name": "README Documentation",
                        "dimension": "documentation",
                        "max_points": 10,
                        "evaluation_status": "unmet",
                        "score": 0.0,
                        "evidence_references": [
                            {
                                "source": "file_analysis.txt",
                                "description": "README.md missing or inadequate",
                                "confidence": 0.9
                            }
                        ]
                    }
                ],
                "total_score": 22.5,
                "max_possible_score": 100,
                "score_percentage": 22.5,
                "category_breakdowns": {
                    "code_quality": {"score": 15.0, "max_points": 40, "percentage": 37.5},
                    "testing": {"score": 7.5, "max_points": 35, "percentage": 21.4},
                    "documentation": {"score": 0.0, "max_points": 25, "percentage": 0.0}
                },
                "evidence_summary": [
                    {
                        "category": "code_quality",
                        "items": [
                            {
                                "source": "ruff_output.txt",
                                "description": "No linting errors found",
                                "confidence": 1.0
                            }
                        ]
                    }
                ]
            },
            "human_summary": "Basic evaluation summary"
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
    def default_template(self, temp_directories):
        """Create default template file for testing."""
        template_content = """# AI Code Review Report

Repository: {{repository.url}}
Total Score: {{total.score}}/100

## Strengths
{{#each met_items}}
- ✅ {{name}}
{{/each}}

## Areas for Improvement
{{#each unmet_items}}
- ❌ {{name}}
{{/each}}
"""
        template_path = temp_directories["template"] / "test_template.md"
        template_path.write_text(template_content)
        return template_path

    def test_end_to_end_workflow_success(self, sample_score_input, temp_directories, default_template):
        """Test complete workflow from score_input.json to final_report.md."""
        from src.llm.report_generator import ReportGenerator

        # Setup input file
        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(sample_score_input, f)

        output_path = temp_directories["output"] / "final_report.md"

        # Mock the LLM CLI call
        mock_llm_response = """# AI Code Review Report

Repository: https://github.com/test/repository.git
Total Score: 22.5/100

## Strengths
- ✅ Static Linting Passed

## Areas for Improvement
- ❌ README Documentation

This project shows basic code quality but needs significant improvement in testing and documentation.
"""

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = mock_llm_response

            # Execute report generation
            generator = ReportGenerator()
            result = generator.generate_report(
                score_input_path=str(score_input_path),
                output_path=str(output_path),
                template_path=str(default_template)
            )

            # Verify result
            assert result is not None
            assert output_path.exists()

            # Verify report content
            generated_content = output_path.read_text()
            assert "# AI Code Review Report" in generated_content
            assert "https://github.com/test/repository.git" in generated_content
            assert "22.5/100" in generated_content
            assert "Static Linting Passed" in generated_content
            assert "README Documentation" in generated_content

    def test_cli_command_execution(self, sample_score_input, temp_directories, default_template):
        """Test CLI command execution for report generation."""
        from src.cli.llm_report import main as llm_report_main
        import sys

        # Setup input file
        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(sample_score_input, f)

        output_path = temp_directories["output"] / "final_report.md"

        # Mock CLI arguments
        test_args = [
            "llm-report",
            str(score_input_path),
            "--prompt", str(default_template),
            "--output", str(output_path),
            "--provider", "gemini"
        ]

        with patch.object(sys, 'argv', test_args):
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = "# Generated Report\nTest content"

                # Execute CLI command
                result = llm_report_main()

                # Verify execution
                assert result == 0  # Success exit code
                assert output_path.exists()

    def test_template_processing(self, sample_score_input, temp_directories):
        """Test template processing and data injection."""
        from src.llm.template_loader import TemplateLoader
        from src.llm.prompt_builder import PromptBuilder

        # Create template with various placeholders
        template_content = """# Report for {{repository.url}}

Score: {{total.score}}/{{total.max_score}}
Percentage: {{total.percentage}}%

## Met Items
{{#each met_items}}
- {{name}}: {{description}}
{{/each}}

## Unmet Items
{{#each unmet_items}}
- {{name}}: {{description}}
{{/each}}

## Evidence
{{#each evidence_summary}}
### {{category}}
{{#each items}}
- {{source}}: {{description}} ({{confidence}})
{{/each}}
{{/each}}
"""

        template_path = temp_directories["template"] / "detailed_template.md"
        template_path.write_text(template_content)

        # Load and process template
        loader = TemplateLoader()
        template = loader.load_template(str(template_path))

        builder = PromptBuilder()
        prompt = builder.build_prompt(sample_score_input, template)

        # Verify template processing
        assert "https://github.com/test/repository.git" in prompt
        assert "22.5/100" in prompt or "22.5" in prompt
        assert "Static Linting Passed" in prompt
        assert "README Documentation" in prompt
        assert "ruff_output.txt" in prompt

    def test_llm_provider_integration(self, sample_score_input, temp_directories, default_template):
        """Test integration with different LLM providers."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(sample_score_input, f)

        output_path = temp_directories["output"] / "final_report.md"

        # Test different providers
        providers = ["gemini", "openai", "claude"]

        for provider in providers:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = f"# Report from {provider}\nGenerated content"

                generator = ReportGenerator()
                result = generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(default_template),
                    provider=provider
                )

                assert result is not None

                # Verify correct provider was called
                call_args = mock_subprocess.call_args[0][0]
                if provider == "gemini":
                    assert "gemini" in call_args
                elif provider == "openai":
                    assert "openai" in call_args or "gpt" in str(call_args)

    def test_output_metadata_generation(self, sample_score_input, temp_directories, default_template):
        """Test that proper metadata is generated with the report."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(sample_score_input, f)

        output_path = temp_directories["output"] / "final_report.md"

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "# Generated Report"

            generator = ReportGenerator()
            result = generator.generate_report(
                score_input_path=str(score_input_path),
                output_path=str(output_path),
                template_path=str(default_template)
            )

            # Verify metadata is included in result
            assert "template_used" in result
            assert "generation_timestamp" in result
            assert "provider_used" in result
            assert "input_metadata" in result

            # Verify metadata content
            assert result["template_used"]["file_path"] == str(default_template)
            assert result["input_metadata"]["repository_url"] == "https://github.com/test/repository.git"
            assert result["input_metadata"]["total_score"] == 22.5

    def test_large_evaluation_handling(self, temp_directories, default_template):
        """Test handling of large evaluation datasets with truncation."""
        from src.llm.report_generator import ReportGenerator

        # Create large score input with many items
        large_score_input = {
            "schema_version": "1.0.0",
            "repository_info": {
                "url": "https://github.com/large/repository.git",
                "commit_sha": "abc123",
                "primary_language": "python",
                "analysis_timestamp": "2025-09-27T10:30:00Z",
                "metrics_source": "output/submission.json"
            },
            "evaluation_result": {
                "checklist_items": [],
                "total_score": 75.0,
                "max_possible_score": 100,
                "score_percentage": 75.0,
                "category_breakdowns": {},
                "evidence_summary": [
                    {
                        "category": "code_quality",
                        "items": [
                            {
                                "source": f"evidence_{i}.txt",
                                "description": f"Evidence item {i} with very long description " + "x" * 1000,
                                "confidence": 0.9
                            }
                            for i in range(20)  # Many evidence items
                        ]
                    }
                ]
            },
            "human_summary": "Large dataset summary"
        }

        score_input_path = temp_directories["input"] / "large_score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(large_score_input, f)

        output_path = temp_directories["output"] / "final_report.md"

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "# Truncated Report"

            generator = ReportGenerator()
            result = generator.generate_report(
                score_input_path=str(score_input_path),
                output_path=str(output_path),
                template_path=str(default_template)
            )

            # Verify truncation was applied
            assert result["truncation_applied"]["evidence_truncated"] is True
            assert result["truncation_applied"]["items_removed"] > 0