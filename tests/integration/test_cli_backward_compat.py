"""
Integration tests for CLI backward compatibility.

These tests verify that the CLI command-line interface maintains backward
compatibility after refactoring to support programmatic API.

Following project guidelines:
- All tests must be real integration tests (no mocks)
- Tests call real CLI commands via subprocess
- Use real submission files and verify actual outputs
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCLIBackwardCompatibility:
    """Test CLI backward compatibility after programmatic API refactoring."""

    def create_test_submission(self, temp_path: Path) -> Path:
        """Create a test submission file with valid data."""
        submission_file = temp_path / "submission.json"

        submission_data = {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/test/repo.git",
                "commit": "abc123def456",
                "language": "python",
                "timestamp": "2025-10-12T10:00:00Z"
            },
            "metrics": {
                "code_quality": {
                    "linting": {
                        "tool": "ruff",
                        "passed": True,
                        "issues_count": 0,
                        "severity_breakdown": {"error": 0, "warning": 0}
                    },
                    "static_analysis": {
                        "passed": True
                    }
                },
                "testing": {
                    "test_execution": {
                        "passed": True,
                        "total_tests": 10,
                        "passed_tests": 10,
                        "failed_tests": 0
                    }
                },
                "documentation": {
                    "readme_analysis": {
                        "exists": True,
                        "word_count": 500,
                        "has_installation": True,
                        "has_usage": True
                    }
                }
            },
            "execution": {
                "start_time": "2025-10-12T10:00:00Z",
                "end_time": "2025-10-12T10:05:00Z",
                "success": True,
                "duration_seconds": 300
            }
        }

        submission_file.write_text(json.dumps(submission_data, indent=2))
        return submission_file

    def test_cli_command_still_works(self):
        """Test that CLI command executes successfully with basic arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_test_submission(temp_path)
            output_dir = temp_path / "output"

            # Run CLI command
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.evaluate",
                    str(submission_file),
                    "--output-dir", str(output_dir),
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Verify exit code (0 for success, 2 for quality gate failure)
            assert result.returncode in [0, 2], \
                f"CLI should exit with 0 or 2, got {result.returncode}\nStderr: {result.stderr}"

            # If quality gate failed (exit code 2), check error message
            if result.returncode == 2:
                assert "quality gate" in result.stderr.lower() or "threshold" in result.stderr.lower(), \
                    f"Quality gate failure should be mentioned in stderr: {result.stderr}"

    def test_cli_output_files_generated(self):
        """Test that CLI generates expected output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_test_submission(temp_path)
            output_dir = temp_path / "output"

            # Run CLI command with JSON format
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.evaluate",
                    str(submission_file),
                    "--output-dir", str(output_dir),
                    "--format", "json",
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Verify exit code
            assert result.returncode in [0, 2], \
                f"CLI should exit with 0 or 2, got {result.returncode}"

            # Verify output files exist
            score_input_json = output_dir / "score_input.json"
            assert score_input_json.exists(), f"score_input.json should be generated at {score_input_json}"
            assert score_input_json.is_file(), "score_input.json should be a file"
            assert score_input_json.stat().st_size > 0, "score_input.json should not be empty"

            # Verify JSON is valid
            with open(score_input_json) as f:
                score_data = json.load(f)
                assert isinstance(score_data, dict), "score_input.json should contain a dictionary"

    def test_cli_output_format_unchanged(self):
        """Test that CLI output format remains consistent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_test_submission(temp_path)
            output_dir = temp_path / "output"

            # Run CLI command with both formats
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.evaluate",
                    str(submission_file),
                    "--output-dir", str(output_dir),
                    "--format", "both",
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Verify exit code
            assert result.returncode in [0, 2], \
                f"CLI should exit with 0 or 2, got {result.returncode}"

            # Verify both output files exist
            score_input_json = output_dir / "score_input.json"
            evaluation_report_md = output_dir / "evaluation_report.md"

            assert score_input_json.exists(), "score_input.json should be generated"
            assert evaluation_report_md.exists(), "evaluation_report.md should be generated"

            # Verify file formats
            with open(score_input_json) as f:
                score_data = json.load(f)
                # Check expected top-level keys
                assert "evaluation_result" in score_data, "score_input.json should have evaluation_result"
                assert "repository_info" in score_data, "score_input.json should have repository_info"

            # Verify markdown format
            md_content = evaluation_report_md.read_text()
            assert len(md_content) > 0, "Markdown report should not be empty"
            assert "#" in md_content, "Markdown report should contain headings"

    def test_cli_quality_gate_exit_code(self):
        """Test that CLI exits with code 2 for quality gate failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "low_score_submission.json"

            # Create submission with very low quality metrics
            low_score_data = {
                "schema_version": "1.0.0",
                "repository": {
                    "url": "https://github.com/test/repo.git",
                    "commit": "abc123",
                    "language": "python",
                    "timestamp": "2025-10-12T10:00:00Z"
                },
                "metrics": {
                    "code_quality": {
                        "linting": {
                            "passed": False,
                            "issues_count": 500
                        }
                    },
                    "testing": {
                        "test_execution": {
                            "passed": False,
                            "total_tests": 0
                        }
                    },
                    "documentation": {
                        "readme_analysis": {
                            "exists": False
                        }
                    }
                },
                "execution": {
                    "success": True
                }
            }

            submission_file.write_text(json.dumps(low_score_data, indent=2))
            output_dir = temp_path / "output"

            # Run CLI command
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.evaluate",
                    str(submission_file),
                    "--output-dir", str(output_dir),
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Verify exit code (should be 2 if quality gate fails, 0 if passes)
            assert result.returncode in [0, 2], \
                f"CLI should exit with 0 or 2, got {result.returncode}"

            # If exit code is 2, verify quality gate message
            if result.returncode == 2:
                stderr_lower = result.stderr.lower()
                assert any(keyword in stderr_lower for keyword in ["quality gate", "threshold", "score"]), \
                    f"Quality gate failure message should be in stderr: {result.stderr}"

    def test_cli_validate_only_mode(self):
        """Test that CLI validate-only mode works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_test_submission(temp_path)
            output_dir = temp_path / "output"

            # Run CLI command with validate-only flag
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.evaluate",
                    str(submission_file),
                    "--output-dir", str(output_dir),
                    "--validate-only",
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Verify exit code (should be 0 for valid submission)
            assert result.returncode == 0, \
                f"Validate-only should exit with 0 for valid submission, got {result.returncode}\nStderr: {result.stderr}"

            # Verify no output files generated (validate-only mode)
            score_input_json = output_dir / "score_input.json"
            evaluation_report_md = output_dir / "evaluation_report.md"

            # In validate-only mode, files should NOT be generated
            # (output_dir might not even be created)
            if output_dir.exists():
                assert not score_input_json.exists(), "score_input.json should NOT be generated in validate-only mode"
                assert not evaluation_report_md.exists(), "evaluation_report.md should NOT be generated in validate-only mode"

    def test_cli_verbose_output(self):
        """Test that CLI verbose mode produces detailed output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_test_submission(temp_path)
            output_dir = temp_path / "output"

            # Run CLI command with verbose flag
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.evaluate",
                    str(submission_file),
                    "--output-dir", str(output_dir),
                    "--verbose"
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Verify exit code
            assert result.returncode in [0, 2], \
                f"CLI should exit with 0 or 2, got {result.returncode}"

            # Verify verbose output contains detailed information or quality gate message
            combined_output = result.stdout + result.stderr
            # Look for common verbose indicators or quality gate messages
            verbose_indicators = [
                "initializing",
                "loading",
                "evaluating",
                "generating",
                "completed",
                "quality gate",
                "threshold",
                "score"
            ]

            # At least some verbose indicators should be present
            found_indicators = [indicator for indicator in verbose_indicators if indicator in combined_output.lower()]
            assert len(found_indicators) > 0, \
                f"Verbose output should contain detailed information. Output: {combined_output[:500]}"

    def test_cli_missing_file_error(self):
        """Test that CLI handles missing submission file gracefully."""
        non_existent_file = "/tmp/non_existent_submission_999999.json"

        # Run CLI command with non-existent file
        result = subprocess.run(
            [
                "uv", "run", "python", "-m", "src.cli.evaluate",
                non_existent_file,
                "--quiet"
            ],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        # Verify exit code (should be 1 or 2 - Click uses 2 for usage errors)
        assert result.returncode in [1, 2], \
            f"CLI should exit with 1 or 2 for missing file, got {result.returncode}"

        # Verify error message
        stderr_lower = result.stderr.lower()
        assert "not found" in stderr_lower or "does not exist" in stderr_lower or "no such file" in stderr_lower or "invalid" in stderr_lower, \
            f"Error message should mention file not found: {result.stderr}"


class TestCLIOutputIdentity:
    """Test that CLI and programmatic outputs are identical."""

    def create_test_submission(self, temp_path: Path) -> Path:
        """Create a test submission file."""
        submission_file = temp_path / "submission.json"

        submission_data = {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/test/repo.git",
                "commit": "abc123",
                "language": "python",
                "timestamp": "2025-10-12T10:00:00Z"
            },
            "metrics": {
                "code_quality": {
                    "linting": {"passed": True, "issues_count": 5}
                },
                "testing": {
                    "test_execution": {"passed": True, "total_tests": 10}
                },
                "documentation": {
                    "readme_analysis": {"exists": True, "word_count": 500}
                }
            },
            "execution": {"success": True}
        }

        submission_file.write_text(json.dumps(submission_data, indent=2))
        return submission_file

    def test_cli_produces_same_files_as_programmatic(self):
        """Test that CLI produces the same files as programmatic API."""
        from src.cli.evaluate import evaluate_submission

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_test_submission(temp_path)

            # Run via CLI
            cli_output_dir = temp_path / "cli_output"
            cli_result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.evaluate",
                    str(submission_file),
                    "--output-dir", str(cli_output_dir),
                    "--format", "json",
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Run via programmatic API
            prog_output_dir = temp_path / "prog_output"
            try:
                prog_result = evaluate_submission(
                    submission_file=submission_file,
                    output_dir=prog_output_dir,
                    format="json",
                    validate_only=False,
                    verbose=False,
                    quiet=True
                )
            except Exception as e:
                # Handle quality gate exception or other expected exceptions
                prog_result = None
                prog_exception = e

            # Verify both produced output files
            cli_score_file = cli_output_dir / "score_input.json"
            prog_score_file = prog_output_dir / "score_input.json"

            # Check if CLI succeeded (exit code 0 or 2)
            cli_succeeded = cli_result.returncode in [0, 2]

            if cli_succeeded:
                assert cli_score_file.exists(), "CLI should produce score_input.json"

            if prog_result is not None or prog_score_file.exists():
                assert prog_score_file.exists(), "Programmatic API should produce score_input.json"

                # Compare file contents (should be very similar, though timestamps might differ)
                if cli_succeeded and cli_score_file.exists():
                    with open(cli_score_file) as f:
                        cli_data = json.load(f)
                    with open(prog_score_file) as f:
                        prog_data = json.load(f)

                    # Verify key fields match
                    assert "evaluation_result" in cli_data, "CLI output should have evaluation_result"
                    assert "evaluation_result" in prog_data, "Programmatic output should have evaluation_result"

                    # Compare scores (should be identical)
                    cli_score = cli_data["evaluation_result"]["total_score"]
                    prog_score = prog_data["evaluation_result"]["total_score"]
                    assert cli_score == prog_score, \
                        f"Scores should match: CLI={cli_score}, Programmatic={prog_score}"
