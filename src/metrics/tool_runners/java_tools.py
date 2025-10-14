"""Java-specific tool runner for code analysis."""

import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class JavaToolRunner:
    """Executes Java-specific analysis tools."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize Java tool runner."""
        self.timeout_seconds = timeout_seconds
        self.tools_available = {}

    def run_linting(self, repo_path: str) -> dict[str, Any]:
        """Run Java linting using Checkstyle or SpotBugs."""
        result = {
            "tool_used": None,
            "passed": False,
            "issues_count": 0,
            "issues": []
        }

        # Try Checkstyle first
        if self._has_maven(repo_path) and self._check_tool_available("mvn"):
            try:
                cmd_result = subprocess.run(
                    ["mvn", "checkstyle:check", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                result["tool_used"] = "checkstyle"
                result["passed"] = cmd_result.returncode == 0

                # Parse Checkstyle output
                if cmd_result.stdout:
                    result["issues"] = self._parse_checkstyle_output(cmd_result.stdout)
                    result["issues_count"] = len(result["issues"])

                return result

            except subprocess.TimeoutExpired:
                result["tool_used"] = "checkstyle"
                result["issues"] = [{"severity": "error", "message": "Checkstyle timed out", "file": "", "line": 0}]
                return result

        # Try Gradle with Checkstyle
        elif self._has_gradle(repo_path) and self._check_tool_available("gradle"):
            try:
                cmd_result = subprocess.run(
                    ["gradle", "check", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                result["tool_used"] = "gradle-checkstyle"
                result["passed"] = cmd_result.returncode == 0

                # Basic parsing of Gradle output
                if cmd_result.stderr:
                    result["issues"] = self._parse_gradle_output(cmd_result.stderr)
                    result["issues_count"] = len(result["issues"])

                return result

            except subprocess.TimeoutExpired:
                result["tool_used"] = "gradle-checkstyle"
                result["issues"] = [{"severity": "error", "message": "Gradle check timed out", "file": "", "line": 0}]
                return result

        # No tools available
        result["tool_used"] = "none"
        result["issues"] = [{"severity": "warning", "message": "No Java linting tools available", "file": "", "line": 0}]
        return result

    def run_testing(self, repo_path: str) -> dict[str, Any]:
        """Analyze Java test infrastructure using static analysis (Phase 1 + Phase 2).

        This method uses TestInfrastructureAnalyzer to perform two-phase analysis:
        - Phase 1: Static test file detection (0-25 points)
        - Phase 2: CI configuration analysis (0-13 points)
        - Combined: min(Phase 1 + Phase 2, 35) with score breakdown

        This implements FR-004 through FR-020 for Java repositories.

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
            test_analysis = analyzer.analyze(repo_path, "java")

            # Log score breakdown at DEBUG level (per T026 requirement)
            logger.debug(
                f"Test analysis score breakdown for Java repository at {repo_path}: "
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
                # Phase 1 fields (FR-004 to FR-017)
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
            logger.error(f"Test analysis failed for Java repository at {repo_path}: {e}")
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

    def run_build(self, repo_path: str) -> dict[str, Any]:
        """
        Run Java build validation using Maven or Gradle.

        Detects Maven (pom.xml) or Gradle (build.gradle) and compiles the project.

        Args:
            repo_path: Path to the repository to build

        Returns:
            Dictionary matching BuildValidationResult schema with keys:
            - success: bool | None (True=pass, False=fail, None=unavailable)
            - tool_used: str (name of build tool: "mvn", "gradle", or "none")
            - execution_time_seconds: float (build duration)
            - error_message: str | None (truncated to 1000 chars)
            - exit_code: int | None (process exit code)
        """
        start_time = time.time()

        # Try Maven build
        if self._has_maven(repo_path):
            if not self._check_tool_available("mvn"):
                return {
                    "success": None,
                    "tool_used": "none",
                    "execution_time_seconds": time.time() - start_time,
                    "error_message": "Maven not available in PATH (pom.xml found)",
                    "exit_code": None
                }

            try:
                cmd_result = subprocess.run(
                    ["mvn", "compile", "-q", "-DskipTests"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                execution_time = time.time() - start_time

                if cmd_result.returncode == 0:
                    return {
                        "success": True,
                        "tool_used": "mvn",
                        "execution_time_seconds": execution_time,
                        "error_message": None,
                        "exit_code": 0
                    }
                else:
                    # Build failed - capture error
                    error_msg = cmd_result.stderr or cmd_result.stdout or "Maven compile failed"
                    # Truncate to 1000 chars (NFR-002)
                    if len(error_msg) > 1000:
                        error_msg = error_msg[:997] + "..."

                    return {
                        "success": False,
                        "tool_used": "mvn",
                        "execution_time_seconds": execution_time,
                        "error_message": error_msg,
                        "exit_code": cmd_result.returncode
                    }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "tool_used": "mvn",
                    "execution_time_seconds": time.time() - start_time,
                    "error_message": "Build timed out (exceeded timeout limit)",
                    "exit_code": None
                }

        # Try Gradle build
        elif self._has_gradle(repo_path):
            if not self._check_tool_available("gradle"):
                return {
                    "success": None,
                    "tool_used": "none",
                    "execution_time_seconds": time.time() - start_time,
                    "error_message": "Gradle not available in PATH (build.gradle found)",
                    "exit_code": None
                }

            try:
                cmd_result = subprocess.run(
                    ["gradle", "compileJava", "--console=plain", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                execution_time = time.time() - start_time

                if cmd_result.returncode == 0:
                    return {
                        "success": True,
                        "tool_used": "gradle",
                        "execution_time_seconds": execution_time,
                        "error_message": None,
                        "exit_code": 0
                    }
                else:
                    # Build failed - capture error
                    error_msg = cmd_result.stderr or cmd_result.stdout or "Gradle compile failed"
                    # Truncate to 1000 chars (NFR-002)
                    if len(error_msg) > 1000:
                        error_msg = error_msg[:997] + "..."

                    return {
                        "success": False,
                        "tool_used": "gradle",
                        "execution_time_seconds": execution_time,
                        "error_message": error_msg,
                        "exit_code": cmd_result.returncode
                    }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "tool_used": "gradle",
                    "execution_time_seconds": time.time() - start_time,
                    "error_message": "Build timed out (exceeded timeout limit)",
                    "exit_code": None
                }

        # No build configuration found
        return {
            "success": None,
            "tool_used": "none",
            "execution_time_seconds": time.time() - start_time,
            "error_message": "No Maven or Gradle configuration found (pom.xml or build.gradle)",
            "exit_code": None
        }

    def run_security_audit(self, repo_path: str) -> dict[str, Any]:
        """Run security audit using OWASP dependency check."""
        result = {
            "vulnerabilities_found": 0,
            "high_severity_count": 0,
            "tool_used": "owasp"
        }

        # Try OWASP dependency check with Maven
        if self._has_maven(repo_path) and self._check_tool_available("mvn"):
            try:
                cmd_result = subprocess.run(
                    ["mvn", "org.owasp:dependency-check-maven:check", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                # Look for dependency check report
                report_path = Path(repo_path) / "target" / "dependency-check-report.xml"
                if report_path.exists():
                    result.update(self._parse_owasp_report(str(report_path)))

                return result

            except subprocess.TimeoutExpired:
                return result

        result["tool_used"] = "none"
        return result

    def _has_maven(self, repo_path: str) -> bool:
        """Check if repository has Maven configuration."""
        return (Path(repo_path) / "pom.xml").exists()

    def _has_gradle(self, repo_path: str) -> bool:
        """Check if repository has Gradle configuration."""
        return (Path(repo_path) / "build.gradle").exists() or (Path(repo_path) / "build.gradle.kts").exists()

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

    def _parse_checkstyle_output(self, output: str) -> list[dict]:
        """Parse Checkstyle output to standard format."""
        issues = []
        lines = output.split('\n')

        for line in lines:
            if ":" in line and ("[ERROR]" in line or "[WARN]" in line):
                parts = line.split(":")
                if len(parts) >= 3:
                    try:
                        file_path = parts[0].strip()
                        line_num = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                        message = ":".join(parts[2:]).strip()

                        severity = "error" if "[ERROR]" in line else "warning"

                        issues.append({
                            "severity": severity,
                            "message": message,
                            "file": file_path,
                            "line": line_num,
                            "column": 0
                        })
                    except (ValueError, IndexError):
                        continue

        return issues

    def _parse_gradle_output(self, output: str) -> list[dict]:
        """Parse Gradle output to standard format."""
        issues = []
        lines = output.split('\n')

        for line in lines:
            if "error:" in line.lower() or "warning:" in line.lower():
                issues.append({
                    "severity": "error" if "error:" in line.lower() else "warning",
                    "message": line.strip(),
                    "file": "",
                    "line": 0,
                    "column": 0
                })

        return issues

    def _parse_maven_test_output(self, output: str) -> dict[str, Any]:
        """Parse Maven test output."""
        result = {"tests_run": 0, "tests_passed": 0, "tests_failed": 0}

        import re
        # Look for Maven Surefire summary
        summary_pattern = r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)"
        match = re.search(summary_pattern, output)

        if match:
            tests_run = int(match.group(1))
            failures = int(match.group(2))
            errors = int(match.group(3))

            result["tests_run"] = tests_run
            result["tests_failed"] = failures + errors
            result["tests_passed"] = tests_run - result["tests_failed"]

        return result

    def _parse_gradle_test_output(self, output: str) -> dict[str, Any]:
        """Parse Gradle test output."""
        result = {"tests_run": 0, "tests_passed": 0, "tests_failed": 0}

        # Basic parsing for Gradle test results
        if "BUILD SUCCESSFUL" in output:
            # Assume tests passed if build was successful
            result["tests_passed"] = 1
            result["tests_run"] = 1
        elif "BUILD FAILED" in output:
            result["tests_failed"] = 1
            result["tests_run"] = 1

        return result

    def _parse_compilation_errors(self, stderr: str) -> list[str]:
        """Parse compilation errors from stderr."""
        errors = []
        lines = stderr.split('\n')

        for line in lines:
            if "error:" in line.lower() or "ERROR" in line:
                errors.append(line.strip())

        return errors[:10]  # Limit to first 10 errors

    def _parse_owasp_report(self, report_path: str) -> dict[str, Any]:
        """Parse OWASP dependency check XML report."""
        result = {"vulnerabilities_found": 0, "high_severity_count": 0}

        try:
            tree = ET.parse(report_path)
            root = tree.getroot()

            vulnerabilities = root.findall(".//vulnerability")
            result["vulnerabilities_found"] = len(vulnerabilities)

            high_severity = 0
            for vuln in vulnerabilities:
                cvss_score = vuln.find(".//cvssScore")
                if cvss_score is not None:
                    try:
                        score = float(cvss_score.text)
                        if score >= 7.0:  # High/Critical severity
                            high_severity += 1
                    except (ValueError, AttributeError):
                        pass

            result["high_severity_count"] = high_severity

        except Exception:
            # If parsing fails, return defaults
            pass

        return result
