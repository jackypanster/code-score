"""Python-specific tool runner for code analysis."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any


class PythonToolRunner:
    """Executes Python-specific analysis tools."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize Python tool runner."""
        self.timeout_seconds = timeout_seconds
        self.tools_available = {}

    def run_linting(self, repo_path: str) -> dict[str, Any]:
        """Run Python linting tools (Ruff preferred, Flake8 fallback)."""
        result = {
            "tool_used": None,
            "passed": False,
            "issues_count": 0,
            "issues": []
        }

        # Try Ruff first
        if self._check_tool_available("ruff"):
            try:
                cmd_result = subprocess.run(
                    ["ruff", "check", "--output-format", "json", repo_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                result["tool_used"] = "ruff"
                result["passed"] = cmd_result.returncode == 0

                if cmd_result.stdout:
                    try:
                        issues = json.loads(cmd_result.stdout)
                        result["issues"] = self._format_ruff_issues(issues)
                        result["issues_count"] = len(result["issues"])
                    except json.JSONDecodeError:
                        result["issues_count"] = 0

                return result

            except subprocess.TimeoutExpired:
                result["tool_used"] = "ruff"
                result["issues"] = [{"severity": "error", "message": "Linting timed out", "file": "", "line": 0}]
                return result

        # Fallback to Flake8
        if self._check_tool_available("flake8"):
            try:
                cmd_result = subprocess.run(
                    ["flake8", "--format=json", repo_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                result["tool_used"] = "flake8"
                result["passed"] = cmd_result.returncode == 0

                if cmd_result.stdout:
                    try:
                        issues = json.loads(cmd_result.stdout)
                        result["issues"] = self._format_flake8_issues(issues)
                        result["issues_count"] = len(result["issues"])
                    except json.JSONDecodeError:
                        result["issues_count"] = 0

                return result

            except subprocess.TimeoutExpired:
                result["tool_used"] = "flake8"
                result["issues"] = [{"severity": "error", "message": "Linting timed out", "file": "", "line": 0}]
                return result

        # No tools available
        result["tool_used"] = "none"
        result["issues"] = [{"severity": "warning", "message": "No Python linting tools available", "file": "", "line": 0}]
        return result

    def run_testing(self, repo_path: str) -> dict[str, Any]:
        """Analyze Python test infrastructure using static analysis.

        This method uses TestInfrastructureAnalyzer to detect test files,
        configuration, and calculate a score without executing tests.
        This implements FR-001 through FR-017 for Python repositories.

        Args:
            repo_path: Path to the repository to analyze

        Returns:
            Dictionary with test_execution structure including:
            - test_files_detected: Count of detected test files (FR-017)
            - test_config_detected: Whether test framework config exists (FR-005)
            - coverage_config_detected: Whether coverage config exists (FR-006)
            - test_file_ratio: Ratio of test files to total files (FR-010)
            - calculated_score: Static analysis score 0-25 (FR-018)
            - tests_run: 0 (static analysis, no execution)
            - tests_passed: 0 (static analysis, no execution)
            - tests_failed: 0 (static analysis, no execution)
            - framework: Inferred framework name
            - execution_time_seconds: 0.0 (static analysis is instant)
        """
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        try:
            # Use static analyzer instead of running tests
            analyzer = TestInfrastructureAnalyzer()
            analysis_result = analyzer.analyze(repo_path, "python")

            # Map ALL TestInfrastructureResult fields to test_execution dict
            # This enables checklist evaluator to award partial credit (T037)
            result = {
                "test_files_detected": analysis_result.test_files_detected,  # FR-017
                "test_config_detected": analysis_result.test_config_detected,  # FR-005
                "coverage_config_detected": analysis_result.coverage_config_detected,  # FR-006
                "test_file_ratio": analysis_result.test_file_ratio,  # FR-010
                "calculated_score": analysis_result.calculated_score,  # FR-018
                "tests_run": 0,  # Static analysis doesn't run tests
                "tests_passed": 0,  # Static analysis doesn't run tests
                "tests_failed": 0,  # Static analysis doesn't run tests
                "framework": analysis_result.inferred_framework,
                "execution_time_seconds": 0.0,  # Static analysis is instant
            }

            return result

        except Exception as e:
            # Graceful error handling (NFR-001)
            return {
                "test_files_detected": 0,
                "test_config_detected": False,
                "coverage_config_detected": False,
                "test_file_ratio": 0.0,
                "calculated_score": 0,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "framework": "none",
                "execution_time_seconds": 0.0,
            }

    def run_security_audit(self, repo_path: str) -> dict[str, Any]:
        """Run security audit using pip-audit."""
        result = {
            "vulnerabilities_found": 0,
            "high_severity_count": 0,
            "tool_used": "pip-audit"
        }

        if not self._check_tool_available("pip-audit"):
            result["tool_used"] = "none"
            return result

        try:
            cmd_result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            if cmd_result.stdout:
                try:
                    audit_data = json.loads(cmd_result.stdout)
                    if isinstance(audit_data, list):
                        result["vulnerabilities_found"] = len(audit_data)
                        result["high_severity_count"] = sum(
                            1 for vuln in audit_data
                            if vuln.get("severity", "").lower() in ["high", "critical"]
                        )
                except json.JSONDecodeError:
                    pass

            return result

        except subprocess.TimeoutExpired:
            return result

        except Exception:
            return result

    def run_formatting_check(self, repo_path: str) -> dict[str, Any]:
        """Check Python code formatting using Black."""
        result = {
            "tool_used": "black",
            "compliant": True,
            "files_need_formatting": 0
        }

        if not self._check_tool_available("black"):
            result["tool_used"] = "none"
            return result

        try:
            cmd_result = subprocess.run(
                ["black", "--check", "--diff", repo_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            result["compliant"] = cmd_result.returncode == 0

            # Count files that need formatting
            if cmd_result.stdout:
                diff_lines = cmd_result.stdout.split('\n')
                file_count = len([line for line in diff_lines if line.startswith('--- ')])
                result["files_need_formatting"] = file_count

            return result

        except subprocess.TimeoutExpired:
            result["compliant"] = False
            return result

        except Exception:
            return result

    def _check_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available in the system."""
        if tool_name in self.tools_available:
            return self.tools_available[tool_name]

        try:
            result = subprocess.run(
                ["which", tool_name],
                capture_output=True,
                timeout=5
            )
            available = result.returncode == 0

        except Exception:
            available = False

        self.tools_available[tool_name] = available
        return available

    def _format_ruff_issues(self, issues: list[dict]) -> list[dict]:
        """Format Ruff issues to standard format."""
        formatted = []
        for issue in issues:
            formatted.append({
                "severity": "error" if issue.get("type") == "error" else "warning",
                "message": issue.get("message", ""),
                "file": issue.get("filename", ""),
                "line": issue.get("location", {}).get("row", 0),
                "column": issue.get("location", {}).get("column", 0)
            })
        return formatted

    def _format_flake8_issues(self, issues: list[dict]) -> list[dict]:
        """Format Flake8 issues to standard format."""
        formatted = []
        for issue in issues:
            formatted.append({
                "severity": "warning",  # Flake8 mostly reports warnings
                "message": issue.get("message", ""),
                "file": issue.get("filename", ""),
                "line": issue.get("line_number", 0),
                "column": issue.get("column_number", 0)
            })
        return formatted

    def run_build(self, repo_path: str) -> dict[str, Any]:
        """
        Run Python build validation using uv build (preferred) or python -m build (fallback).
        
        Constitutional Principle I: UV-based dependency management - prioritize uv build.
        
        Args:
            repo_path: Path to the repository to build
            
        Returns:
            Dictionary matching BuildValidationResult schema with keys:
            - success: bool | None (True=pass, False=fail, None=unavailable)
            - tool_used: str (name of build tool used)
            - execution_time_seconds: float (build duration)
            - error_message: str | None (truncated to 1000 chars)
            - exit_code: int | None (process exit code)
        """
        start_time = time.time()
        
        # Check for build configuration files
        repo = Path(repo_path)
        has_pyproject = (repo / "pyproject.toml").exists()
        has_setup_py = (repo / "setup.py").exists()
        has_setup_cfg = (repo / "setup.cfg").exists()
        
        if not (has_pyproject or has_setup_py or has_setup_cfg):
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": "No Python build configuration found (pyproject.toml, setup.py, or setup.cfg)",
                "exit_code": None
            }
        
        # Try uv build first (Constitutional Principle I: UV-based dependency management)
        if self._check_tool_available("uv"):
            try:
                cmd_result = subprocess.run(
                    ["uv", "build"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )
                
                execution_time = time.time() - start_time
                
                if cmd_result.returncode == 0:
                    return {
                        "success": True,
                        "tool_used": "uv",
                        "execution_time_seconds": execution_time,
                        "error_message": None,
                        "exit_code": 0
                    }
                else:
                    # Build failed - capture error
                    error_msg = cmd_result.stderr or cmd_result.stdout or "Build failed"
                    # Truncate to 1000 chars (NFR-002)
                    if len(error_msg) > 1000:
                        error_msg = error_msg[:997] + "..."
                    
                    return {
                        "success": False,
                        "tool_used": "uv",
                        "execution_time_seconds": execution_time,
                        "error_message": error_msg,
                        "exit_code": cmd_result.returncode
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "tool_used": "uv",
                    "execution_time_seconds": time.time() - start_time,
                    "error_message": "Build timed out (exceeded timeout limit)",
                    "exit_code": None
                }
            except Exception as e:
                # Fall through to python -m build
                pass
        
        # Fallback to python -m build
        # Check if build module is available
        try:
            check_build = subprocess.run(
                ["python3", "-c", "import build"],
                capture_output=True,
                timeout=5
            )
            build_available = check_build.returncode == 0
        except Exception:
            build_available = False
        
        if not build_available:
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": "Neither uv nor python build module available",
                "exit_code": None
            }
        
        # Run python -m build
        try:
            cmd_result = subprocess.run(
                ["python3", "-m", "build", "--no-isolation"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )
            
            execution_time = time.time() - start_time
            
            if cmd_result.returncode == 0:
                return {
                    "success": True,
                    "tool_used": "build",
                    "execution_time_seconds": execution_time,
                    "error_message": None,
                    "exit_code": 0
                }
            else:
                # Build failed - capture error
                error_msg = cmd_result.stderr or cmd_result.stdout or "Build failed"
                # Truncate to 1000 chars (NFR-002)
                if len(error_msg) > 1000:
                    error_msg = error_msg[:997] + "..."
                
                return {
                    "success": False,
                    "tool_used": "build",
                    "execution_time_seconds": execution_time,
                    "error_message": error_msg,
                    "exit_code": cmd_result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tool_used": "build",
                "execution_time_seconds": time.time() - start_time,
                "error_message": "Build timed out (exceeded timeout limit)",
                "exit_code": None
            }
        except Exception as e:
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": f"Unexpected error during build: {str(e)}",
                "exit_code": None
            }
