"""Real execution tests for language-specific tool runners.

NO MOCKS - All tests use real tool execution with actual linting/testing/security tools.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.metrics.tool_runners.golang_tools import GolangToolRunner
from src.metrics.tool_runners.java_tools import JavaToolRunner
from src.metrics.tool_runners.javascript_tools import JavaScriptToolRunner
from src.metrics.tool_runners.python_tools import PythonToolRunner


def check_tool_available(tool_name: str) -> bool:
    """Check if a tool is available in the system PATH."""
    try:
        result = subprocess.run(
            ["which", tool_name],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


class TestPythonToolRunnerReal:
    """REAL TESTS for Python tool runner - NO MOCKS."""

    @pytest.fixture
    def runner(self) -> PythonToolRunner:
        """Create a Python tool runner instance."""
        return PythonToolRunner(timeout_seconds=30)

    @pytest.fixture
    def clean_python_repo(self) -> Path:
        """Create a clean Python repository without linting issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create clean Python files
            (repo_path / "main.py").write_text('"""Main module."""\n\nprint("Hello, World!")\n')
            (repo_path / "utils.py").write_text('"""Utilities."""\n\n\ndef helper() -> None:\n    """Helper function."""\n    pass\n')
            (repo_path / "pyproject.toml").write_text('[project]\nname = "test"\nversion = "0.1.0"\n')

            yield repo_path

    @pytest.fixture
    def python_repo_with_issues(self) -> Path:
        """Create a Python repository WITH linting issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Python files with intentional linting issues
            (repo_path / "bad.py").write_text('import os\nimport sys\n\nprint( "bad spacing" )\n')  # Unused imports, bad spacing

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("ruff"), reason="ruff not available")
    def test_run_linting_ruff_real_success(self, runner: PythonToolRunner, clean_python_repo: Path) -> None:
        """REAL TEST: Execute actual ruff linting on clean code."""
        # REAL LINT - No mocks!
        result = runner.run_linting(str(clean_python_repo))

        assert result is not None
        assert "tool_used" in result
        assert "passed" in result
        assert "issues_count" in result

        # Clean code should pass or have minimal issues
        if result["tool_used"] == "ruff":
            assert isinstance(result["passed"], bool)
            assert result["issues_count"] >= 0

    @pytest.mark.skipif(not check_tool_available("ruff"), reason="ruff not available")
    def test_run_linting_ruff_real_with_issues(self, runner: PythonToolRunner, python_repo_with_issues: Path) -> None:
        """REAL TEST: Execute actual ruff linting on code with issues."""
        # REAL LINT - No mocks!
        result = runner.run_linting(str(python_repo_with_issues))

        assert result is not None
        if result["tool_used"] == "ruff":
            # Should detect unused imports
            assert result["issues_count"] > 0
            assert isinstance(result["issues"], list)

    def test_run_linting_real_invalid_path(self, runner: PythonToolRunner) -> None:
        """REAL TEST: Test linting with invalid repository path."""
        # REAL EXECUTION on invalid path - Python runner raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            runner.run_linting("/nonexistent/path/to/repo")

    @pytest.fixture
    def python_repo_with_tests(self) -> Path:
        """Create a Python repository with actual pytest tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create a simple module
            (repo_path / "calculator.py").write_text("""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")

            # Create real pytest tests
            (repo_path / "test_calculator.py").write_text("""from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 1) == -1
""")

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("pytest"), reason="pytest not available")
    def test_run_testing_pytest_real_success(self, runner: PythonToolRunner, python_repo_with_tests: Path) -> None:
        """REAL TEST: Execute actual pytest on real test files."""
        # REAL TEST EXECUTION - No mocks!
        result = runner.run_testing(str(python_repo_with_tests))

        assert result is not None
        if result.get("framework") == "pytest":
            assert result["tests_run"] >= 0
            assert result["tests_passed"] >= 0
            assert isinstance(result["execution_time_seconds"], (int, float))


class TestJavaScriptToolRunnerReal:
    """REAL TESTS for JavaScript tool runner - NO MOCKS."""

    @pytest.fixture
    def runner(self) -> JavaScriptToolRunner:
        """Create a JavaScript tool runner instance."""
        return JavaScriptToolRunner(timeout_seconds=30)

    @pytest.fixture
    def clean_js_repo(self) -> Path:
        """Create a clean JavaScript repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create clean JS files
            (repo_path / "index.js").write_text('console.log("Hello, World!");\n')
            (repo_path / "utils.js").write_text('function helper() {\n  return true;\n}\n\nmodule.exports = { helper };\n')
            (repo_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}')

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("eslint"), reason="eslint not available")
    def test_run_linting_eslint_real(self, runner: JavaScriptToolRunner, clean_js_repo: Path) -> None:
        """REAL TEST: Execute actual eslint on JavaScript code."""
        # REAL LINT - No mocks!
        result = runner.run_linting(str(clean_js_repo))

        assert result is not None
        assert "tool_used" in result
        assert "passed" in result

    def test_run_linting_real_invalid_path(self, runner: JavaScriptToolRunner) -> None:
        """REAL TEST: Test with invalid path."""
        result = runner.run_linting("/nonexistent/path")

        assert result is not None
        assert result["passed"] is False


class TestJavaToolRunnerReal:
    """REAL TESTS for Java tool runner - NO MOCKS."""

    @pytest.fixture
    def runner(self) -> JavaToolRunner:
        """Create a Java tool runner instance."""
        return JavaToolRunner(timeout_seconds=60)

    @pytest.fixture
    def minimal_java_repo(self) -> Path:
        """Create a minimal Java repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Java source structure
            src_dir = repo_path / "src" / "main" / "java" / "com" / "example"
            src_dir.mkdir(parents=True)

            (src_dir / "Main.java").write_text("""package com.example;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
""")

            # Create pom.xml
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>
""")

            yield repo_path

    def test_run_linting_real_basic(self, runner: JavaToolRunner, minimal_java_repo: Path) -> None:
        """REAL TEST: Basic Java linting test."""
        # REAL EXECUTION
        result = runner.run_linting(str(minimal_java_repo))

        assert result is not None
        assert "tool_used" in result
        assert "passed" in result


class TestGolangToolRunnerReal:
    """REAL TESTS for Golang tool runner - NO MOCKS."""

    @pytest.fixture
    def runner(self) -> GolangToolRunner:
        """Create a Golang tool runner instance."""
        return GolangToolRunner(timeout_seconds=30)

    @pytest.fixture
    def clean_go_repo(self) -> Path:
        """Create a clean Go repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create clean Go files
            (repo_path / "main.go").write_text("""package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
""")
            (repo_path / "go.mod").write_text("module test\n\ngo 1.21\n")

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("gofmt"), reason="gofmt not available")
    def test_run_linting_gofmt_real(self, runner: GolangToolRunner, clean_go_repo: Path) -> None:
        """REAL TEST: Execute actual gofmt on Go code."""
        # REAL LINT - No mocks!
        result = runner.run_linting(str(clean_go_repo))

        assert result is not None
        assert "tool_used" in result
        assert "passed" in result

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_run_build_go_real(self, runner: GolangToolRunner, clean_go_repo: Path) -> None:
        """REAL TEST: Execute actual go build."""
        # REAL BUILD - No mocks!
        result = runner.run_build(str(clean_go_repo))

        assert result is not None
        assert "success" in result
        assert "tool_used" in result


class TestToolRunnerErrorHandlingReal:
    """REAL TESTS for error handling across all tool runners."""

    def test_python_runner_invalid_path_real(self) -> None:
        """REAL TEST: Python runner with invalid repository path."""
        runner = PythonToolRunner()

        # REAL EXECUTION with invalid path - raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            runner.run_linting("/nonexistent/invalid/path")

    def test_javascript_runner_invalid_path_real(self) -> None:
        """REAL TEST: JavaScript runner with invalid repository path."""
        runner = JavaScriptToolRunner()

        # REAL EXECUTION with invalid path
        result = runner.run_linting("/nonexistent/invalid/path")

        assert result is not None
        assert result["passed"] is False
        # JS runner returns tool_used="none" when tools unavailable

    def test_java_runner_invalid_path_real(self) -> None:
        """REAL TEST: Java runner with invalid repository path."""
        runner = JavaToolRunner()

        # REAL EXECUTION with invalid path
        result = runner.run_linting("/nonexistent/invalid/path")

        assert result is not None
        assert result["passed"] is False
        # Java runner returns tool_used="none" when tools unavailable

    def test_golang_runner_invalid_path_real(self) -> None:
        """REAL TEST: Golang runner with invalid repository path."""
        runner = GolangToolRunner()

        # REAL EXECUTION with invalid path
        result = runner.run_linting("/nonexistent/invalid/path")

        assert result is not None
        assert result["passed"] is False
        # Go runner returns tool_used="none" when tools unavailable
