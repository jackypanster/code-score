"""JavaScript-specific tool runner for code analysis."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any


class JavaScriptToolRunner:
    """Executes JavaScript-specific analysis tools."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize JavaScript tool runner."""
        self.timeout_seconds = timeout_seconds
        self.tools_available = {}

    def run_linting(self, repo_path: str) -> dict[str, Any]:
        """Run JavaScript linting using ESLint."""
        result = {
            "tool_used": "eslint",
            "passed": False,
            "issues_count": 0,
            "issues": []
        }

        if not self._check_tool_available("eslint"):
            result["tool_used"] = "none"
            result["issues"] = [{"severity": "warning", "message": "ESLint not available", "file": "", "line": 0}]
            return result

        try:
            cmd_result = subprocess.run(
                ["npx", "eslint", ".", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            result["passed"] = cmd_result.returncode == 0

            if cmd_result.stdout:
                try:
                    lint_data = json.loads(cmd_result.stdout)
                    result["issues"] = self._format_eslint_issues(lint_data)
                    result["issues_count"] = len(result["issues"])
                except json.JSONDecodeError:
                    result["issues_count"] = 0

            return result

        except subprocess.TimeoutExpired:
            result["issues"] = [{"severity": "error", "message": "ESLint timed out", "file": "", "line": 0}]
            return result

        except Exception:
            return result

    def run_testing(self, repo_path: str) -> dict[str, Any]:
        """Analyze JavaScript test infrastructure using static analysis (Phase 1 + Phase 2).

        This method uses TestInfrastructureAnalyzer to perform two-phase analysis:
        - Phase 1: Static test file detection (0-25 points)
        - Phase 2: CI configuration analysis (0-13 points)
        - Combined: min(Phase 1 + Phase 2, 35) with score breakdown

        This implements FR-002 through FR-020 for JavaScript/TypeScript repositories.

        Args:
            repo_path: Path to the repository to analyze

        Returns:
            Dictionary with test_execution structure including:
            - test_files_detected: Count of detected test files (FR-017)
            - test_config_detected: Whether test framework config exists (FR-005)
            - coverage_config_detected: Whether coverage config exists (FR-006)
            - test_file_ratio: Ratio of test files to total files (FR-010)
            - calculated_score: Combined Phase 1+2 score 0-35 (FR-018, FR-020)
            - tests_run: 0 (static analysis, no execution)
            - tests_passed: 0 (static analysis, no execution)
            - tests_failed: 0 (static analysis, no execution)
            - framework: Inferred framework name
            - execution_time_seconds: 0.0 (static analysis is instant)
            - ci_platform: Detected CI platform (Phase 2)
            - ci_score: CI configuration contribution (Phase 2)
            - phase1_score: Static infrastructure contribution
            - phase2_score: CI configuration contribution
        """
        import logging
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        logger = logging.getLogger(__name__)

        try:
            # Use static analyzer for Phase 1 + Phase 2 analysis
            analyzer = TestInfrastructureAnalyzer(enable_ci_analysis=True)
            test_analysis = analyzer.analyze(repo_path, "javascript")

            # Log score breakdown at DEBUG level (per T024 requirement)
            logger.debug(
                f"Test analysis score breakdown for JavaScript repository at {repo_path}: "
                f"Phase1={test_analysis.score_breakdown.phase1_contribution}, "
                f"Phase2={test_analysis.score_breakdown.phase2_contribution}, "
                f"Combined={test_analysis.combined_score} "
                f"(raw_total={test_analysis.score_breakdown.raw_total}, "
                f"truncated={test_analysis.score_breakdown.truncated_points})"
            )

            # Extract Phase 1 (static infrastructure) fields
            static = test_analysis.static_infrastructure

            # Extract Phase 2 (CI configuration) fields
            ci_platform = None
            ci_score = 0
            if test_analysis.ci_configuration:
                ci_platform = test_analysis.ci_configuration.platform
                ci_score = test_analysis.ci_configuration.calculated_score

            # Map TestAnalysis to test_execution dict with combined_score
            # This enables checklist evaluator to use the capped 35-point score
            result = {
                # Phase 1 fields (FR-002 to FR-017)
                "test_files_detected": static.test_files_detected,  # FR-017
                "test_config_detected": static.test_config_detected,  # FR-005
                "coverage_config_detected": static.coverage_config_detected,  # FR-006
                "test_file_ratio": static.test_file_ratio,  # FR-010
                "framework": static.inferred_framework,
                # Phase 2 fields (FR-018 to FR-020)
                "ci_platform": ci_platform,  # FR-019
                "ci_score": ci_score,  # FR-020
                # Combined scoring
                "calculated_score": test_analysis.combined_score,  # FR-018 (capped at 35)
                "phase1_score": test_analysis.score_breakdown.phase1_contribution,
                "phase2_score": test_analysis.score_breakdown.phase2_contribution,
                # Static analysis metadata
                "tests_run": 0,  # Static analysis doesn't run tests
                "tests_passed": 0,  # Static analysis doesn't run tests
                "tests_failed": 0,  # Static analysis doesn't run tests
                "execution_time_seconds": 0.0,  # Static analysis is instant
            }

            return result

        except Exception as e:
            logger.error(f"Test analysis failed for JavaScript repository at {repo_path}: {e}")
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
                "ci_platform": None,
                "ci_score": 0,
                "phase1_score": 0,
                "phase2_score": 0,
            }

    def run_security_audit(self, repo_path: str) -> dict[str, Any]:
        """Run security audit using npm audit."""
        result = {
            "vulnerabilities_found": 0,
            "high_severity_count": 0,
            "tool_used": "npm"
        }

        # Check if package.json exists
        package_json = Path(repo_path) / "package.json"
        if not package_json.exists():
            result["tool_used"] = "none"
            return result

        try:
            cmd_result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            if cmd_result.stdout:
                try:
                    audit_data = json.loads(cmd_result.stdout)

                    # npm audit JSON format varies, handle both old and new formats
                    if "vulnerabilities" in audit_data:
                        # New format
                        vulnerabilities = audit_data["vulnerabilities"]
                        result["vulnerabilities_found"] = len(vulnerabilities)
                        result["high_severity_count"] = sum(
                            1 for vuln in vulnerabilities.values()
                            if vuln.get("severity", "").lower() in ["high", "critical"]
                        )
                    elif "advisories" in audit_data:
                        # Old format
                        advisories = audit_data["advisories"]
                        result["vulnerabilities_found"] = len(advisories)
                        result["high_severity_count"] = sum(
                            1 for advisory in advisories.values()
                            if advisory.get("severity", "").lower() in ["high", "critical"]
                        )

                except json.JSONDecodeError:
                    # If JSON parsing fails, check if there are vulnerabilities mentioned
                    if "vulnerabilities" in cmd_result.stdout.lower():
                        result["vulnerabilities_found"] = 1

            return result

        except subprocess.TimeoutExpired:
            return result

        except Exception:
            return result

    def run_formatting_check(self, repo_path: str) -> dict[str, Any]:
        """Check JavaScript code formatting using Prettier."""
        result = {
            "tool_used": "prettier",
            "compliant": True,
            "files_need_formatting": 0
        }

        if not self._check_tool_available("prettier"):
            result["tool_used"] = "none"
            return result

        try:
            cmd_result = subprocess.run(
                ["npx", "prettier", "--check", "**/*.js", "**/*.jsx"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            result["compliant"] = cmd_result.returncode == 0

            # Count files that need formatting
            if cmd_result.stderr:
                # Prettier outputs non-compliant files to stderr
                files = [line.strip() for line in cmd_result.stderr.split('\n') if line.strip()]
                result["files_need_formatting"] = len(files)

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
            # For npm tools, check if npx can find them or if they're in package.json
            if tool_name in ["eslint", "prettier"]:
                # First try npx which can find tools even without installation
                npx_result = subprocess.run(
                    ["npx", "--yes", tool_name, "--version"],
                    capture_output=True,
                    timeout=10,
                    text=True
                )
                available = npx_result.returncode == 0
            else:
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

    def _format_eslint_issues(self, lint_data: list[dict]) -> list[dict]:
        """Format ESLint issues to standard format."""
        formatted = []

        for file_result in lint_data:
            file_path = file_result.get("filePath", "")
            messages = file_result.get("messages", [])

            for message in messages:
                severity_map = {1: "warning", 2: "error"}
                severity = severity_map.get(message.get("severity", 1), "warning")

                formatted.append({
                    "severity": severity,
                    "message": message.get("message", ""),
                    "file": file_path,
                    "line": message.get("line", 0),
                    "column": message.get("column", 0)
                })

        return formatted

    def run_build(self, repo_path: str) -> dict[str, Any]:
        """
        Run JavaScript/TypeScript build validation using npm or yarn.

        Checks for build script in package.json and executes it using the appropriate
        package manager (yarn if yarn.lock exists, otherwise npm).

        Args:
            repo_path: Path to the repository to build

        Returns:
            Dictionary matching BuildValidationResult schema with keys:
            - success: bool | None (True=pass, False=fail, None=unavailable)
            - tool_used: str (name of build tool used: "npm", "yarn", or "none")
            - execution_time_seconds: float (build duration)
            - error_message: str | None (truncated to 1000 chars)
            - exit_code: int | None (process exit code)
        """
        start_time = time.time()

        # Check for package.json
        repo = Path(repo_path)
        package_json_path = repo / "package.json"

        if not package_json_path.exists():
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": "No package.json found",
                "exit_code": None
            }

        # Parse package.json to check for build script
        try:
            with open(package_json_path) as f:
                package_data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": f"Failed to parse package.json: {str(e)}",
                "exit_code": None
            }

        # Check if build script exists
        scripts = package_data.get("scripts", {})
        if "build" not in scripts:
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": "No build script defined in package.json",
                "exit_code": None
            }

        # Determine which package manager to use
        has_yarn_lock = (repo / "yarn.lock").exists()
        tool_cmd = ["yarn", "build"] if has_yarn_lock else ["npm", "run", "build", "--if-present"]
        tool_name = "yarn" if has_yarn_lock else "npm"

        # Check if tool is available
        tool_check_cmd = "yarn" if has_yarn_lock else "npm"
        if not self._check_tool_available(tool_check_cmd):
            return {
                "success": None,
                "tool_used": "none",
                "execution_time_seconds": time.time() - start_time,
                "error_message": f"{tool_name} not available in PATH",
                "exit_code": None
            }

        # Run build command
        try:
            cmd_result = subprocess.run(
                tool_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            execution_time = time.time() - start_time

            if cmd_result.returncode == 0:
                return {
                    "success": True,
                    "tool_used": tool_name,
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
                    "tool_used": tool_name,
                    "execution_time_seconds": execution_time,
                    "error_message": error_msg,
                    "exit_code": cmd_result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tool_used": tool_name,
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
