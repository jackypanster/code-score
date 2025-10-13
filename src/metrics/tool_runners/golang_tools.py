"""Go-specific tool runner for code analysis."""

import json
import subprocess
import time
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
        """Analyze Go test infrastructure using static analysis.

        This method uses TestInfrastructureAnalyzer to detect test files,
        configuration, and calculate a score without executing tests.
        This implements FR-003 through FR-017 for Go repositories.

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
            analysis_result = analyzer.analyze(repo_path, "go")

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

    def run_build(self, repo_path: str) -> dict[str, Any]:
        """
        Run Go build validation using go build.

        Checks for go.mod and attempts to build all packages in the module.

        Args:
            repo_path: Path to the repository to build

        Returns:
            Dictionary matching BuildValidationResult schema with keys:
            - success: bool | None (True=pass, False=fail, None=unavailable)
            - tool_used: str (name of build tool used: "go" or "none")
            - execution_time_seconds: float (build duration)
            - error_message: str | None (truncated to 1000 chars)
            - exit_code: int | None (process exit code)
        """
        start_time = time.time()

        # Check for go.mod
        if not self._has_go_module(repo_path):
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": "No go.mod file found",
                "exit_code": None
            }

        # Check if go is available
        if not self._check_tool_available("go"):
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": "Go toolchain not available in PATH",
                "exit_code": None
            }

        # Run go build
        try:
            cmd_result = subprocess.run(
                ["go", "build", "./..."],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            execution_time = time.time() - start_time

            if cmd_result.returncode == 0:
                return {
                    "success": True,
                    "tool_used": "go",
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
                    "tool_used": "go",
                    "execution_time_seconds": execution_time,
                    "error_message": error_msg,
                    "exit_code": cmd_result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tool_used": "go",
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
