"""JavaScript-specific tool runner for code analysis."""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class JavaScriptToolRunner:
    """Executes JavaScript-specific analysis tools."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize JavaScript tool runner."""
        self.timeout_seconds = timeout_seconds
        self.tools_available = {}

    def run_linting(self, repo_path: str) -> Dict[str, Any]:
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

    def run_testing(self, repo_path: str) -> Dict[str, Any]:
        """Run JavaScript tests using npm test or available framework."""
        result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "npm",
            "execution_time_seconds": 0.0
        }

        # Check if package.json exists
        package_json = Path(repo_path) / "package.json"
        if not package_json.exists():
            result["framework"] = "none"
            return result

        try:
            # Try npm test first
            cmd_result = subprocess.run(
                ["npm", "test"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=repo_path
            )

            # Parse test output (basic parsing)
            output = cmd_result.stdout + cmd_result.stderr

            # Look for Jest output patterns
            if "jest" in output.lower():
                result["framework"] = "jest"
                # Try to extract test counts from Jest output
                lines = output.split('\n')
                for line in lines:
                    if "passed" in line and "total" in line:
                        try:
                            # Extract numbers from Jest summary
                            import re
                            numbers = re.findall(r'\d+', line)
                            if len(numbers) >= 2:
                                result["tests_passed"] = int(numbers[0])
                                result["tests_run"] = int(numbers[1])
                                result["tests_failed"] = result["tests_run"] - result["tests_passed"]
                        except (ValueError, IndexError):
                            pass

            # Look for Mocha output patterns
            elif "mocha" in output.lower():
                result["framework"] = "mocha"
                # Basic Mocha parsing
                if "passing" in output:
                    try:
                        import re
                        passing_match = re.search(r'(\d+) passing', output)
                        failing_match = re.search(r'(\d+) failing', output)

                        if passing_match:
                            result["tests_passed"] = int(passing_match.group(1))
                        if failing_match:
                            result["tests_failed"] = int(failing_match.group(1))

                        result["tests_run"] = result["tests_passed"] + result["tests_failed"]
                    except (ValueError, AttributeError):
                        pass

            return result

        except subprocess.TimeoutExpired:
            result["tests_failed"] = 1
            result["tests_run"] = 1
            return result

        except Exception:
            return result

    def run_security_audit(self, repo_path: str) -> Dict[str, Any]:
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

    def run_formatting_check(self, repo_path: str) -> Dict[str, Any]:
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

    def _format_eslint_issues(self, lint_data: List[Dict]) -> List[Dict]:
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