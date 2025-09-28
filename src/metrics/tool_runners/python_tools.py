"""Python-specific tool runner for code analysis."""

import json
import subprocess
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
        """Run Python tests using pytest."""
        result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "pytest",
            "execution_time_seconds": 0.0
        }

        if not self._check_tool_available("pytest"):
            result["framework"] = "none"
            return result

        try:
            # Run pytest with JSON output
            cmd_result = subprocess.run(
                ["python", "-m", "pytest", "--tb=short", "-v"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            # Parse pytest output
            output_lines = cmd_result.stdout.split('\n')
            for line in output_lines:
                if "passed" in line and "failed" in line:
                    # Extract test counts from summary line
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed":
                            try:
                                result["tests_passed"] = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                        elif part == "failed":
                            try:
                                result["tests_failed"] = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass

            result["tests_run"] = result["tests_passed"] + result["tests_failed"]

            return result

        except subprocess.TimeoutExpired:
            result["tests_failed"] = 1
            result["tests_run"] = 1
            return result

        except Exception:
            return result

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
