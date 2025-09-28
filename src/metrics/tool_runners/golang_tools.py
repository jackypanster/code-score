"""Go-specific tool runner for code analysis."""

import json
import subprocess
from pathlib import Path
from typing import Any


class GolangToolRunner:
    """Executes Go-specific analysis tools."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize Go tool runner."""
        self.timeout_seconds = timeout_seconds
        self.tools_available = {}

    def run_linting(self, repo_path: str) -> dict[str, Any]:
        """Run Go linting using golangci-lint."""
        result = {
            "tool_used": "golangci-lint",
            "passed": False,
            "issues_count": 0,
            "issues": []
        }

        if not self._check_tool_available("golangci-lint"):
            result["tool_used"] = "none"
            result["issues"] = [{"severity": "warning", "message": "golangci-lint not available", "file": "", "line": 0}]
            return result

        try:
            cmd_result = subprocess.run(
                ["golangci-lint", "run", "--out-format", "json"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            result["passed"] = cmd_result.returncode == 0

            if cmd_result.stdout:
                try:
                    lint_data = json.loads(cmd_result.stdout)
                    result["issues"] = self._format_golangci_issues(lint_data.get("Issues", []))
                    result["issues_count"] = len(result["issues"])
                except json.JSONDecodeError:
                    result["issues_count"] = 0

            return result

        except subprocess.TimeoutExpired:
            result["issues"] = [{"severity": "error", "message": "golangci-lint timed out", "file": "", "line": 0}]
            return result

        except Exception:
            return result

    def run_testing(self, repo_path: str) -> dict[str, Any]:
        """Run Go tests using go test."""
        result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "go",
            "execution_time_seconds": 0.0
        }

        if not self._has_go_module(repo_path) or not self._check_tool_available("go"):
            result["framework"] = "none"
            return result

        try:
            # Run go test with JSON output
            cmd_result = subprocess.run(
                ["go", "test", "-json", "./..."],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            # Parse JSON test output
            output_lines = cmd_result.stdout.strip().split('\n')
            test_events = []

            for line in output_lines:
                if line.strip():
                    try:
                        event = json.loads(line)
                        test_events.append(event)
                    except json.JSONDecodeError:
                        continue

            result.update(self._parse_go_test_events(test_events))

            return result

        except subprocess.TimeoutExpired:
            result["tests_failed"] = 1
            result["tests_run"] = 1
            return result

        except Exception:
            return result

    def run_security_audit(self, repo_path: str) -> dict[str, Any]:
        """Run security audit using osv-scanner."""
        result = {
            "vulnerabilities_found": 0,
            "high_severity_count": 0,
            "tool_used": "osv-scanner"
        }

        if not self._check_tool_available("osv-scanner"):
            result["tool_used"] = "none"
            return result

        try:
            cmd_result = subprocess.run(
                ["osv-scanner", "--format", "json", repo_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            if cmd_result.stdout:
                try:
                    scan_data = json.loads(cmd_result.stdout)
                    vulnerabilities = scan_data.get("results", [])

                    total_vulns = 0
                    high_severity = 0

                    for vuln_result in vulnerabilities:
                        packages = vuln_result.get("packages", [])
                        for package in packages:
                            vulns = package.get("vulnerabilities", [])
                            total_vulns += len(vulns)

                            for vuln in vulns:
                                severity = vuln.get("database_specific", {}).get("severity", "").lower()
                                if severity in ["high", "critical"]:
                                    high_severity += 1

                    result["vulnerabilities_found"] = total_vulns
                    result["high_severity_count"] = high_severity

                except json.JSONDecodeError:
                    pass

            return result

        except subprocess.TimeoutExpired:
            return result

        except Exception:
            return result

    def run_formatting_check(self, repo_path: str) -> dict[str, Any]:
        """Check Go code formatting using gofmt."""
        result = {
            "tool_used": "gofmt",
            "compliant": True,
            "files_need_formatting": 0
        }

        if not self._check_tool_available("gofmt"):
            result["tool_used"] = "none"
            return result

        try:
            # Use gofmt -l to list files that need formatting
            cmd_result = subprocess.run(
                ["gofmt", "-l", "."],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            # Files that need formatting are listed in stdout
            if cmd_result.stdout.strip():
                files = [f.strip() for f in cmd_result.stdout.split('\n') if f.strip()]
                result["files_need_formatting"] = len(files)
                result["compliant"] = False
            else:
                result["compliant"] = True

            return result

        except subprocess.TimeoutExpired:
            result["compliant"] = False
            return result

        except Exception:
            return result

    def run_build_check(self, repo_path: str) -> dict[str, Any]:
        """Check if Go code builds successfully."""
        result = {
            "build_success": False,
            "compilation_errors": []
        }

        if not self._has_go_module(repo_path) or not self._check_tool_available("go"):
            return result

        try:
            cmd_result = subprocess.run(
                ["go", "build", "./..."],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            result["build_success"] = cmd_result.returncode == 0

            if cmd_result.stderr:
                # Parse build errors
                errors = [line.strip() for line in cmd_result.stderr.split('\n') if line.strip()]
                result["compilation_errors"] = errors[:10]  # Limit to first 10 errors

            return result

        except subprocess.TimeoutExpired:
            result["compilation_errors"] = ["Build timed out"]
            return result

        except Exception:
            return result

    def _has_go_module(self, repo_path: str) -> bool:
        """Check if repository has Go module configuration."""
        return (Path(repo_path) / "go.mod").exists()

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

    def _format_golangci_issues(self, issues: list[dict]) -> list[dict]:
        """Format golangci-lint issues to standard format."""
        formatted = []

        for issue in issues:
            # Map golangci-lint severity to standard format
            severity = "warning"  # golangci-lint mostly reports warnings
            if issue.get("Severity", "").lower() == "error":
                severity = "error"

            formatted.append({
                "severity": severity,
                "message": issue.get("Text", ""),
                "file": issue.get("Pos", {}).get("Filename", ""),
                "line": issue.get("Pos", {}).get("Line", 0),
                "column": issue.get("Pos", {}).get("Column", 0)
            })

        return formatted

    def _parse_go_test_events(self, events: list[dict]) -> dict[str, Any]:
        """Parse Go test JSON events."""
        result = {"tests_run": 0, "tests_passed": 0, "tests_failed": 0}

        test_results = {}

        for event in events:
            action = event.get("Action", "")
            test_name = event.get("Test", "")

            if action == "run" and test_name:
                test_results[test_name] = "running"
            elif action == "pass" and test_name:
                test_results[test_name] = "passed"
            elif action == "fail" and test_name:
                test_results[test_name] = "failed"

        # Count results
        passed_tests = sum(1 for status in test_results.values() if status == "passed")
        failed_tests = sum(1 for status in test_results.values() if status == "failed")

        result["tests_passed"] = passed_tests
        result["tests_failed"] = failed_tests
        result["tests_run"] = passed_tests + failed_tests

        return result
