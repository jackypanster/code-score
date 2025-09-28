"""
Integration test for error handling scenarios in LLM report generation.

This test validates proper error handling for various failure conditions
including missing files, invalid data, template errors, and LLM failures.

NOTE: These tests will FAIL initially as part of TDD approach until
implementation is complete.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import modules that don't exist yet - will fail until implementation
pytest.importorskip("src.llm.report_generator", reason="Implementation not ready")
pytest.importorskip("src.cli.llm_report", reason="Implementation not ready")


class TestErrorHandling:
    """Integration tests for error handling in LLM report generation."""

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
    def valid_score_input(self):
        """Valid score_input.json data for testing."""
        return {
            "schema_version": "1.0.0",
            "repository_info": {
                "url": "https://github.com/test/repo.git",
                "commit_sha": "abc123456",
                "primary_language": "python",
                "analysis_timestamp": "2025-09-27T15:00:00Z",
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
                    }
                ],
                "total_score": 15.0,
                "max_possible_score": 100,
                "score_percentage": 15.0,
                "category_breakdowns": {
                    "code_quality": {"score": 15.0, "max_points": 40, "percentage": 37.5},
                    "testing": {"score": 0.0, "max_points": 35, "percentage": 0.0},
                    "documentation": {"score": 0.0, "max_points": 25, "percentage": 0.0}
                },
                "evidence_summary": []
            },
            "human_summary": "Test evaluation"
        }

    @pytest.fixture
    def valid_template(self, temp_directories):
        """Create valid template file."""
        template_content = """# Report for {{repository.url}}
Score: {{total.score}}/{{total.max_score}}
"""
        template_path = temp_directories["template"] / "valid_template.md"
        template_path.write_text(template_content)
        return template_path

    def test_missing_score_input_file(self, temp_directories, valid_template):
        """Test error handling when score_input.json file is missing."""
        from src.llm.report_generator import ReportGenerator

        missing_path = temp_directories["input"] / "missing_file.json"
        output_path = temp_directories["output"] / "report.md"

        generator = ReportGenerator()

        with pytest.raises(FileNotFoundError) as exc_info:
            generator.generate_report(
                score_input_path=str(missing_path),
                output_path=str(output_path),
                template_path=str(valid_template)
            )

        # Verify error message is descriptive
        assert "score_input.json" in str(exc_info.value) or str(missing_path) in str(exc_info.value)

    def test_invalid_json_in_score_input(self, temp_directories, valid_template):
        """Test error handling when score_input.json contains invalid JSON."""
        from src.llm.report_generator import ReportGenerator

        invalid_json_path = temp_directories["input"] / "invalid.json"
        invalid_json_path.write_text("{ invalid json content")

        output_path = temp_directories["output"] / "report.md"
        generator = ReportGenerator()

        with pytest.raises(json.JSONDecodeError):
            generator.generate_report(
                score_input_path=str(invalid_json_path),
                output_path=str(output_path),
                template_path=str(valid_template)
            )

    def test_missing_template_file(self, temp_directories, valid_score_input):
        """Test error handling when template file is missing."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        missing_template = temp_directories["template"] / "missing_template.md"
        output_path = temp_directories["output"] / "report.md"

        generator = ReportGenerator()

        with pytest.raises(FileNotFoundError) as exc_info:
            generator.generate_report(
                score_input_path=str(score_input_path),
                output_path=str(output_path),
                template_path=str(missing_template)
            )

        assert str(missing_template) in str(exc_info.value)

    def test_invalid_template_syntax(self, temp_directories, valid_score_input):
        """Test error handling when template has invalid Jinja2 syntax."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        # Create template with invalid syntax
        invalid_template = temp_directories["template"] / "invalid_template.md"
        invalid_template.write_text("{{unclosed_variable}} {{#invalid_helper}} {{/wrong_close")

        output_path = temp_directories["output"] / "report.md"
        generator = ReportGenerator()

        # Should raise template parsing error
        with pytest.raises(Exception):  # Could be TemplateError, TemplateSyntaxError, etc.
            generator.generate_report(
                score_input_path=str(score_input_path),
                output_path=str(output_path),
                template_path=str(invalid_template)
            )

    def test_invalid_score_input_schema(self, temp_directories, valid_template):
        """Test error handling when score_input.json has invalid schema."""
        from src.llm.report_generator import ReportGenerator

        # Create score input missing required fields
        invalid_score_input = {
            "schema_version": "1.0.0",
            # Missing repository_info
            "evaluation_result": {}
            # Missing other required fields
        }

        score_input_path = temp_directories["input"] / "invalid_schema.json"
        with open(score_input_path, 'w') as f:
            json.dump(invalid_score_input, f)

        output_path = temp_directories["output"] / "report.md"
        generator = ReportGenerator()

        with pytest.raises(Exception):  # Could be ValidationError, KeyError, etc.
            generator.generate_report(
                score_input_path=str(score_input_path),
                output_path=str(output_path),
                template_path=str(valid_template)
            )

    def test_llm_process_failure(self, temp_directories, valid_score_input, valid_template):
        """Test error handling when LLM subprocess fails."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        output_path = temp_directories["output"] / "report.md"

        # Mock subprocess to simulate LLM failure
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 1  # Failure
            mock_subprocess.return_value.stderr = "LLM API Error: Rate limit exceeded"
            mock_subprocess.return_value.stdout = ""

            generator = ReportGenerator()

            with pytest.raises(subprocess.CalledProcessError):
                generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(valid_template),
                    provider="gemini"
                )

    def test_llm_timeout_handling(self, temp_directories, valid_score_input, valid_template):
        """Test error handling when LLM process times out."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        output_path = temp_directories["output"] / "report.md"

        # Mock subprocess to simulate timeout
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = subprocess.TimeoutExpired(
                cmd=["gemini", "prompt"], timeout=300
            )

            generator = ReportGenerator()

            with pytest.raises(subprocess.TimeoutExpired):
                generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(valid_template),
                    timeout=300
                )

    def test_output_directory_permissions(self, temp_directories, valid_score_input, valid_template):
        """Test error handling when output directory is not writable."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        # Create read-only output directory
        readonly_dir = temp_directories["base"] / "readonly"
        readonly_dir.mkdir(mode=0o444)  # Read-only permissions

        output_path = readonly_dir / "report.md"

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "# Generated Report"

            generator = ReportGenerator()

            with pytest.raises(PermissionError):
                generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(valid_template)
                )

    def test_cli_error_handling_missing_args(self):
        """Test CLI error handling when required arguments are missing."""
        import sys

        from src.cli.llm_report import main as llm_report_main

        # Test with missing required score_input_path argument
        test_args = ["llm-report"]

        with patch.object(sys, 'argv', test_args):
            # Should exit with error code for missing required argument
            with pytest.raises(SystemExit) as exc_info:
                llm_report_main()

            assert exc_info.value.code != 0  # Non-zero exit code

    def test_cli_error_handling_invalid_provider(self, temp_directories, valid_score_input, valid_template):
        """Test CLI error handling when invalid provider is specified."""
        import sys

        from src.cli.llm_report import main as llm_report_main

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        test_args = [
            "llm-report",
            str(score_input_path),
            "--prompt", str(valid_template),
            "--provider", "invalid_provider"
        ]

        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                llm_report_main()

            assert exc_info.value.code != 0

    def test_error_recovery_partial_success(self, temp_directories, valid_score_input, valid_template):
        """Test error recovery when some operations succeed and others fail."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        output_path = temp_directories["output"] / "report.md"

        # Mock partial failure: template loads but LLM fails
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 1
            mock_subprocess.return_value.stderr = "API quota exceeded"

            generator = ReportGenerator()

            # Should still provide meaningful error information
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(valid_template)
                )

            # Error should contain context about what failed
            error_msg = str(exc_info.value)
            assert "API quota exceeded" in error_msg or "returncode 1" in error_msg

    def test_cleanup_on_error(self, temp_directories, valid_score_input, valid_template):
        """Test that temporary resources are cleaned up when errors occur."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        output_path = temp_directories["output"] / "report.md"

        # Mock LLM failure after some processing
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["gemini", "prompt"]
            )

            generator = ReportGenerator()

            with pytest.raises(subprocess.CalledProcessError):
                generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(valid_template)
                )

            # Verify no partial output file was left behind
            assert not output_path.exists()

    def test_verbose_error_reporting(self, temp_directories, valid_score_input, valid_template):
        """Test that verbose mode provides detailed error information."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        output_path = temp_directories["output"] / "report.md"

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 1
            mock_subprocess.return_value.stderr = "Detailed error: Model not available"
            mock_subprocess.return_value.stdout = ""

            generator = ReportGenerator()

            # Even in error case, should be able to get detailed information
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                result = generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(valid_template),
                    verbose=True
                )

            # Error should contain verbose details
            assert "Model not available" in str(exc_info.value) or "returncode 1" in str(exc_info.value)

    def test_invalid_provider_configuration(self, temp_directories, valid_score_input, valid_template):
        """Test error handling for provider configuration issues."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        output_path = temp_directories["output"] / "report.md"

        # Test with provider that requires additional configuration
        generator = ReportGenerator()

        # Should handle gracefully when provider is not properly configured
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError("Provider CLI not found")

            with pytest.raises(FileNotFoundError) as exc_info:
                generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(valid_template),
                    provider="gemini"  # Test with primary supported provider
                )

            assert "Provider CLI not found" in str(exc_info.value)

    def test_large_template_error_handling(self, temp_directories, valid_score_input):
        """Test error handling when template is too large or complex."""
        from src.llm.report_generator import ReportGenerator

        score_input_path = temp_directories["input"] / "score_input.json"
        with open(score_input_path, 'w') as f:
            json.dump(valid_score_input, f)

        # Create extremely large template
        large_template = temp_directories["template"] / "large_template.md"
        large_content = "# Report\n" + "{{repository.url}}\n" * 10000  # Very large template
        large_template.write_text(large_content)

        output_path = temp_directories["output"] / "report.md"

        generator = ReportGenerator()

        # Should handle large templates gracefully (may truncate or error)
        try:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = "# Generated Report"

                result = generator.generate_report(
                    score_input_path=str(score_input_path),
                    output_path=str(output_path),
                    template_path=str(large_template)
                )

                # If it succeeds, should handle truncation properly
                if "truncation_applied" in result:
                    assert result["truncation_applied"]["template_truncated"] is True

        except Exception as e:
            # If it fails, should provide clear error message
            assert "template" in str(e).lower() or "size" in str(e).lower()
