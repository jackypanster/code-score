"""Tool execution coordinator for managing language-specific analysis."""

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from .language_detection import LanguageDetector
from .models.metrics_collection import (
    MetricsCollection,
)
from .tool_runners.golang_tools import GolangToolRunner
from .tool_runners.java_tools import JavaToolRunner
from .tool_runners.javascript_tools import JavaScriptToolRunner
from .tool_runners.python_tools import PythonToolRunner


class ToolExecutor:
    """Coordinates execution of language-specific analysis tools."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize tool executor with timeout configuration."""
        self.timeout_seconds = timeout_seconds
        self.language_detector = LanguageDetector()

        # Performance optimization settings
        self.max_file_size_mb = 500  # Skip repos larger than 500MB
        self.max_files_to_analyze = 10000  # Limit file count for analysis
        self.individual_tool_timeout = min(timeout_seconds // 3, 120)  # Max 2 minutes per tool

        # Tool runner registry
        self.tool_runners = {
            "python": PythonToolRunner,
            "javascript": JavaScriptToolRunner,
            "typescript": JavaScriptToolRunner,  # Use JS runner for TS
            "java": JavaToolRunner,
            "go": GolangToolRunner
        }

        # Tool execution attributes for contract compliance
        self.tool_name = ""
        self.tool_version = ""
        self.execution_command = ""
        self.exit_code = 0
        self.stdout = ""
        self.stderr = ""
        self.execution_time_seconds = 0.0

    def execute_tools(self, language: str, repo_path: str) -> MetricsCollection:
        """Execute all appropriate tools for the detected language."""
        start_time = time.time()

        # Initialize metrics collection
        metrics = MetricsCollection(
            repository_id=repo_path,
            collection_timestamp=datetime.utcnow()
        )

        # Early performance checks
        if not self._is_repository_analyzable(repo_path, metrics):
            metrics.execution_metadata.duration_seconds = time.time() - start_time
            return metrics

        # Get appropriate tool runner
        runner_class = self.tool_runners.get(language)
        if not runner_class:
            # Unknown language - create minimal metrics
            metrics.execution_metadata.errors.append(f"No tools available for language: {language}")
            metrics.execution_metadata.duration_seconds = time.time() - start_time
            return metrics

        runner = runner_class(timeout_seconds=self.individual_tool_timeout)

        # Execute tools in parallel where safe
        parallel_tasks = []
        sequential_tasks = []

        # Parallel tasks (independent operations)
        parallel_tasks.extend([
            ("linting", self._run_linting),
            ("security_audit", self._run_security_audit),
            ("build_validation", self._run_build_validation),
        ])

        # Sequential tasks (may modify files or have dependencies)
        sequential_tasks.extend([
            ("testing", self._run_testing),
            ("documentation", self._analyze_documentation_optimized),
        ])

        # Execute parallel tasks with timeout
        results = {}
        remaining_time = self.timeout_seconds - (time.time() - start_time)

        if remaining_time > 0:
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_task = {
                    executor.submit(task_func, runner, repo_path): task_name
                    for task_name, task_func in parallel_tasks
                }

                try:
                    for future in as_completed(future_to_task, timeout=remaining_time):
                        task_name = future_to_task[future]
                        try:
                            results[task_name] = future.result()
                        except Exception as e:
                            results[task_name] = {"error": str(e)}
                            metrics.execution_metadata.errors.append(f"{task_name} failed: {str(e)}")
                except TimeoutError:
                    metrics.execution_metadata.errors.append("Parallel tasks timed out")
                    # Cancel remaining futures
                    for future in future_to_task:
                        future.cancel()

        # Execute sequential tasks with remaining time
        for task_name, task_func in sequential_tasks:
            remaining_time = self.timeout_seconds - (time.time() - start_time)
            if remaining_time <= 0:
                metrics.execution_metadata.warnings.append(f"Skipped {task_name} due to timeout")
                continue

            try:
                results[task_name] = task_func(runner, repo_path)
            except Exception as e:
                results[task_name] = {"error": str(e)}
                metrics.execution_metadata.errors.append(f"{task_name} failed: {str(e)}")

        # Populate metrics from results
        self._populate_metrics(metrics, results, language)

        # Update execution metadata
        metrics.execution_metadata.duration_seconds = time.time() - start_time
        metrics.execution_metadata.tools_used = self._get_tools_used(results)

        return metrics

    def _run_linting(self, runner: Any, repo_path: str) -> dict[str, Any]:
        """Run linting analysis."""
        if hasattr(runner, 'run_linting'):
            return runner.run_linting(repo_path)
        return {"tool_used": "none", "passed": False, "issues_count": 0, "issues": []}

    def _run_security_audit(self, runner: Any, repo_path: str) -> dict[str, Any]:
        """Run security audit."""
        if hasattr(runner, 'run_security_audit'):
            return runner.run_security_audit(repo_path)
        return {"vulnerabilities_found": 0, "high_severity_count": 0, "tool_used": "none"}

    def _run_build_validation(self, runner: Any, repo_path: str) -> dict[str, Any]:
        """Run build validation if the runner supports it."""
        if hasattr(runner, "run_build"):
            try:
                return runner.run_build(repo_path)
            except Exception as e:
                return {
                    "success": None,
                    "tool_used": "none",
                    "execution_time_seconds": 0.0,
                    "error_message": f"Build validation failed: {str(e)}",
                    "exit_code": None
                }
        return {
            "success": None,
            "tool_used": "none",
            "execution_time_seconds": 0.0,
            "error_message": "Build validation not supported for this language",
            "exit_code": None
        }

    def _run_testing(self, runner: Any, repo_path: str) -> dict[str, Any]:
        """Run testing analysis."""
        if hasattr(runner, 'run_testing'):
            return runner.run_testing(repo_path)
        return {"tests_run": 0, "tests_passed": 0, "tests_failed": 0, "framework": "none"}

    def _analyze_documentation(self, runner: Any, repo_path: str) -> dict[str, Any]:
        """Analyze documentation quality."""
        from pathlib import Path

        repo = Path(repo_path)
        result = {
            "readme_present": False,
            "readme_quality_score": 0.0,
            "api_documentation": False,
            "setup_instructions": False,
            "usage_examples": False
        }

        # Check for README
        readme_files = ["README.md", "README.rst", "README.txt", "readme.md"]
        readme_content = ""

        for readme_file in readme_files:
            readme_path = repo / readme_file
            if readme_path.exists():
                result["readme_present"] = True
                try:
                    readme_content = readme_path.read_text(encoding='utf-8')
                    break
                except Exception:
                    continue

        if readme_content:
            # Analyze README quality
            result["readme_quality_score"] = self._calculate_readme_quality(readme_content)

            # Check for setup instructions
            setup_keywords = ["install", "setup", "getting started", "dependencies", "requirements"]
            result["setup_instructions"] = any(keyword in readme_content.lower() for keyword in setup_keywords)

            # Check for usage examples
            example_keywords = ["example", "usage", "how to use", "tutorial", "demo"]
            result["usage_examples"] = any(keyword in readme_content.lower() for keyword in example_keywords)

        # Check for API documentation
        api_docs = ["docs/", "doc/", "api/", "swagger.json", "openapi.json"]
        result["api_documentation"] = any((repo / doc_path).exists() for doc_path in api_docs)

        return result

    def _calculate_readme_quality(self, content: str) -> float:
        """Calculate README quality score (0-1)."""
        score = 0.0
        content_lower = content.lower()

        # Basic content checks (each worth 0.2)
        checks = [
            len(content) > 100,  # Minimum length
            "install" in content_lower or "setup" in content_lower,  # Installation instructions
            "usage" in content_lower or "example" in content_lower,  # Usage examples
            "license" in content_lower,  # License information
            content.count("#") >= 2  # Multiple sections
        ]

        score = sum(checks) * 0.2
        return min(1.0, score)

    def _populate_metrics(self, metrics: MetricsCollection, results: dict[str, Any], language: str) -> None:
        """Populate metrics collection from tool results."""
        # Code quality metrics
        if "linting" in results:
            lint_result = results["linting"]
            if "error" not in lint_result:
                metrics.code_quality.lint_results = lint_result

        if "security_audit" in results:
            security_result = results["security_audit"]
            if "error" not in security_result:
                metrics.code_quality.dependency_audit = security_result

        # Build validation results
        if "build_validation" in results:
            build_result = results["build_validation"]
            if "error" not in build_result:
                # Map BuildValidationResult to CodeQualityMetrics
                from .models.build_validation import BuildValidationResult

                metrics.code_quality.build_success = build_result.get("success")

                # Create BuildValidationResult instance for build_details
                try:
                    build_details = BuildValidationResult(**build_result)
                    metrics.code_quality.build_details = build_details
                except Exception:
                    # If validation fails, still record build_success
                    pass

        # Testing metrics
        if "testing" in results:
            test_result = results["testing"]
            if "error" not in test_result:
                metrics.testing_metrics.test_execution = test_result

        # Documentation metrics
        if "documentation" in results:
            doc_result = results["documentation"]
            if "error" not in doc_result:
                metrics.documentation_metrics.readme_present = doc_result.get("readme_present", False)
                metrics.documentation_metrics.readme_quality_score = doc_result.get("readme_quality_score", 0.0)
                metrics.documentation_metrics.api_documentation = doc_result.get("api_documentation", False)
                metrics.documentation_metrics.setup_instructions = doc_result.get("setup_instructions", False)
                metrics.documentation_metrics.usage_examples = doc_result.get("usage_examples", False)

    def _get_tools_used(self, results: dict[str, Any]) -> list[str]:
        """Extract list of tools that were actually used."""
        tools = []

        # Extract tool names from results
        if "linting" in results and "tool_used" in results["linting"]:
            tool = results["linting"]["tool_used"]
            if tool and tool != "none":
                tools.append(tool)

        if "security_audit" in results and "tool_used" in results["security_audit"]:
            tool = results["security_audit"]["tool_used"]
            if tool and tool != "none":
                tools.append(tool)

        if "testing" in results and "framework" in results["testing"]:
            framework = results["testing"]["framework"]
            if framework and framework != "none":
                tools.append(framework)

        return tools

    def _is_repository_analyzable(self, repo_path: str, metrics: MetricsCollection) -> bool:
        """Check if repository is suitable for analysis based on size and file count."""
        try:
            repo = Path(repo_path)
            if not repo.exists():
                metrics.execution_metadata.errors.append(f"Repository path does not exist: {repo_path}")
                return False

            # Calculate repository size
            total_size = 0
            file_count = 0

            for file_path in repo.rglob("*"):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                        file_count += 1

                        # Early termination if too many files
                        if file_count > self.max_files_to_analyze:
                            metrics.execution_metadata.warnings.append(
                                f"Repository has {file_count}+ files, analysis may be slow or incomplete"
                            )
                            return True  # Still analyzable but warn user

                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue

            size_mb = total_size / (1024 * 1024)

            # Check if repository is too large
            if size_mb > self.max_file_size_mb:
                metrics.execution_metadata.errors.append(
                    f"Repository size ({size_mb:.1f} MB) exceeds maximum ({self.max_file_size_mb} MB)"
                )
                return False

            # Add performance metadata
            metrics.execution_metadata.warnings.append(
                f"Repository size: {size_mb:.1f} MB, Files: {file_count}"
            )

            return True

        except Exception as e:
            metrics.execution_metadata.errors.append(f"Failed to analyze repository size: {str(e)}")
            return True  # Assume analyzable if we can't determine size

    def _analyze_documentation_optimized(self, runner: Any, repo_path: str) -> dict[str, Any]:
        """Optimized documentation analysis with file count limits."""
        repo = Path(repo_path)
        result = {
            "readme_present": False,
            "readme_quality_score": 0.0,
            "api_documentation": False,
            "setup_instructions": False,
            "usage_examples": False
        }

        # Check for README (limit search to top-level and common directories)
        readme_locations = [
            repo,  # Root directory
            repo / "docs",
            repo / "doc"
        ]

        readme_files = ["README.md", "README.rst", "README.txt", "readme.md", "Readme.md"]
        readme_content = ""

        for location in readme_locations:
            if not location.exists() or not location.is_dir():
                continue

            for readme_file in readme_files:
                readme_path = location / readme_file
                if readme_path.exists() and readme_path.is_file():
                    result["readme_present"] = True
                    try:
                        # Limit README size to prevent memory issues
                        with open(readme_path, encoding='utf-8') as f:
                            readme_content = f.read(50000)  # Max 50KB
                        break
                    except Exception:
                        continue

            if readme_content:
                break

        if readme_content:
            # Analyze README quality
            result["readme_quality_score"] = self._calculate_readme_quality(readme_content)

            # Check for setup instructions
            setup_keywords = ["install", "setup", "getting started", "dependencies", "requirements"]
            result["setup_instructions"] = any(keyword in readme_content.lower() for keyword in setup_keywords)

            # Check for usage examples
            example_keywords = ["example", "usage", "how to use", "tutorial", "demo"]
            result["usage_examples"] = any(keyword in readme_content.lower() for keyword in example_keywords)

        # Check for API documentation (limit directory depth)
        api_docs = [
            "docs/", "doc/", "api/", "swagger.json", "openapi.json",
            "docs/api/", "documentation/", ".github/", "wiki/"
        ]

        for doc_path in api_docs:
            full_path = repo / doc_path
            if full_path.exists():
                result["api_documentation"] = True
                break

        return result
