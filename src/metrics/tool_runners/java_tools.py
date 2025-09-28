"""Java-specific tool runner for code analysis."""

import subprocess
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
        """Run Java tests using Maven or Gradle."""
        result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": None,
            "execution_time_seconds": 0.0
        }

        # Try Maven first
        if self._has_maven(repo_path) and self._check_tool_available("mvn"):
            result["framework"] = "maven"
            try:
                cmd_result = subprocess.run(
                    ["mvn", "test", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                # Parse Maven Surefire output
                output = cmd_result.stdout + cmd_result.stderr
                result.update(self._parse_maven_test_output(output))

                return result

            except subprocess.TimeoutExpired:
                result["tests_failed"] = 1
                result["tests_run"] = 1
                return result

        # Try Gradle
        elif self._has_gradle(repo_path) and self._check_tool_available("gradle"):
            result["framework"] = "gradle"
            try:
                cmd_result = subprocess.run(
                    ["gradle", "test", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                # Parse Gradle test output
                output = cmd_result.stdout + cmd_result.stderr
                result.update(self._parse_gradle_test_output(output))

                return result

            except subprocess.TimeoutExpired:
                result["tests_failed"] = 1
                result["tests_run"] = 1
                return result

        # No build tools available
        result["framework"] = "none"
        return result

    def run_build(self, repo_path: str) -> dict[str, Any]:
        """Run Java build to verify compilation."""
        result = {
            "build_success": False,
            "build_tool": None,
            "compilation_errors": []
        }

        # Try Maven build
        if self._has_maven(repo_path) and self._check_tool_available("mvn"):
            result["build_tool"] = "maven"
            try:
                cmd_result = subprocess.run(
                    ["mvn", "compile", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                result["build_success"] = cmd_result.returncode == 0

                if cmd_result.stderr:
                    result["compilation_errors"] = self._parse_compilation_errors(cmd_result.stderr)

                return result

            except subprocess.TimeoutExpired:
                result["compilation_errors"] = ["Build timed out"]
                return result

        # Try Gradle build
        elif self._has_gradle(repo_path) and self._check_tool_available("gradle"):
            result["build_tool"] = "gradle"
            try:
                cmd_result = subprocess.run(
                    ["gradle", "compileJava", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=repo_path
                )

                result["build_success"] = cmd_result.returncode == 0

                if cmd_result.stderr:
                    result["compilation_errors"] = self._parse_compilation_errors(cmd_result.stderr)

                return result

            except subprocess.TimeoutExpired:
                result["compilation_errors"] = ["Build timed out"]
                return result

        # No build tools available
        result["build_tool"] = "none"
        return result

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
