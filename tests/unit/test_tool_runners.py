"""Unit tests for language-specific tool runners."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.metrics.tool_runners.golang_tools import GolangToolRunner
from src.metrics.tool_runners.java_tools import JavaToolRunner
from src.metrics.tool_runners.javascript_tools import JavaScriptToolRunner
from src.metrics.tool_runners.python_tools import PythonToolRunner


class TestPythonToolRunner:
    """Test Python tool runner functionality."""

    @pytest.fixture
    def runner(self) -> PythonToolRunner:
        """Create a Python tool runner instance."""
        return PythonToolRunner(timeout_seconds=30)

    @pytest.fixture
    def temp_python_repo(self) -> Path:
        """Create a temporary Python repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Python files
            (repo_path / "main.py").write_text("print('Hello, World!')\n")
            (repo_path / "utils.py").write_text("def helper():\n    pass\n")
            (repo_path / "requirements.txt").write_text("requests==2.28.0\n")
            (repo_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

            yield repo_path

    @patch('subprocess.run')
    def test_run_linting_with_ruff_success(self, mock_run: MagicMock, runner: PythonToolRunner, temp_python_repo: Path) -> None:
        """Test successful linting with Ruff."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="All checks passed!",
            stderr=""
        )

        result = runner.run_linting(str(temp_python_repo))

        assert result["tool_used"] == "ruff"
        assert result["passed"] is True
        assert result["issues_count"] == 0
        assert result["issues"] == []

        # Verify ruff was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ruff" in args
        assert "check" in args

    @patch('subprocess.run')
    def test_run_linting_with_ruff_issues(self, mock_run: MagicMock, runner: PythonToolRunner, temp_python_repo: Path) -> None:
        """Test linting with Ruff finding issues."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="main.py:1:1: F401 'os' imported but unused\nutils.py:2:5: E302 expected 2 blank lines",
            stderr=""
        )

        result = runner.run_linting(str(temp_python_repo))

        assert result["tool_used"] == "ruff"
        assert result["passed"] is False
        assert result["issues_count"] == 2
        assert len(result["issues"]) == 2
        assert "F401" in result["issues"][0]
        assert "E302" in result["issues"][1]

    @patch('subprocess.run')
    def test_run_linting_ruff_not_available_fallback_flake8(self, mock_run: MagicMock, runner: PythonToolRunner, temp_python_repo: Path) -> None:
        """Test fallback to Flake8 when Ruff is not available."""
        # First call (ruff) fails, second call (flake8) succeeds
        mock_run.side_effect = [
            MagicMock(returncode=127, stdout="", stderr="ruff: command not found"),  # Ruff not found
            MagicMock(returncode=0, stdout="", stderr="")  # Flake8 success
        ]

        result = runner.run_linting(str(temp_python_repo))

        assert result["tool_used"] == "flake8"
        assert result["passed"] is True
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_run_testing_pytest_success(self, mock_run: MagicMock, runner: PythonToolRunner, temp_python_repo: Path) -> None:
        """Test successful pytest execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="==== 5 passed in 2.34s ====",
            stderr=""
        )

        result = runner.run_testing(str(temp_python_repo))

        assert result["framework"] == "pytest"
        assert result["tests_run"] == 5
        assert result["tests_passed"] == 5
        assert result["tests_failed"] == 0
        assert result["execution_time_seconds"] == 2.34

    @patch('subprocess.run')
    def test_run_testing_pytest_with_failures(self, mock_run: MagicMock, runner: PythonToolRunner, temp_python_repo: Path) -> None:
        """Test pytest execution with failures."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="==== 3 failed, 7 passed in 4.56s ====",
            stderr=""
        )

        result = runner.run_testing(str(temp_python_repo))

        assert result["tests_run"] == 10
        assert result["tests_passed"] == 7
        assert result["tests_failed"] == 3
        assert result["execution_time_seconds"] == 4.56

    @patch('subprocess.run')
    def test_run_security_audit_success(self, mock_run: MagicMock, runner: PythonToolRunner, temp_python_repo: Path) -> None:
        """Test successful security audit."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="No known vulnerabilities found",
            stderr=""
        )

        result = runner.run_security_audit(str(temp_python_repo))

        assert result["tool_used"] == "pip-audit"
        assert result["vulnerabilities_found"] == 0
        assert result["high_severity_count"] == 0

    @patch('subprocess.run')
    def test_run_build_success(self, mock_run: MagicMock, runner: PythonToolRunner, temp_python_repo: Path) -> None:
        """Test successful build."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.run_build(str(temp_python_repo))

        assert result["success"] is True
        assert result["tool_used"] == "python -m py_compile"

    def test_timeout_handling(self, runner: PythonToolRunner, temp_python_repo: Path) -> None:
        """Test timeout handling in tool execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ruff", 30)

            result = runner.run_linting(str(temp_python_repo))

            assert result["tool_used"] == "ruff"
            assert result["passed"] is False
            assert "timeout" in result["error"].lower()


class TestJavaScriptToolRunner:
    """Test JavaScript tool runner functionality."""

    @pytest.fixture
    def runner(self) -> JavaScriptToolRunner:
        """Create a JavaScript tool runner instance."""
        return JavaScriptToolRunner(timeout_seconds=30)

    @pytest.fixture
    def temp_js_repo(self) -> Path:
        """Create a temporary JavaScript repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create JS files
            (repo_path / "index.js").write_text("console.log('Hello, World!');\n")
            (repo_path / "utils.js").write_text("function helper() {}\n")
            (repo_path / "package.json").write_text('{"name": "test", "scripts": {"test": "jest"}}')

            yield repo_path

    @patch('subprocess.run')
    def test_run_linting_eslint_success(self, mock_run: MagicMock, runner: JavaScriptToolRunner, temp_js_repo: Path) -> None:
        """Test successful linting with ESLint."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.run_linting(str(temp_js_repo))

        assert result["tool_used"] == "eslint"
        assert result["passed"] is True

    @patch('subprocess.run')
    def test_run_testing_jest_success(self, mock_run: MagicMock, runner: JavaScriptToolRunner, temp_js_repo: Path) -> None:
        """Test successful testing with Jest."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Test Suites: 3 passed, 3 total\nTests: 12 passed, 12 total\nTime: 3.45 s",
            stderr=""
        )

        result = runner.run_testing(str(temp_js_repo))

        assert result["framework"] == "jest"
        assert result["tests_run"] == 12
        assert result["tests_passed"] == 12
        assert result["tests_failed"] == 0

    @patch('subprocess.run')
    def test_run_security_audit_npm(self, mock_run: MagicMock, runner: JavaScriptToolRunner, temp_js_repo: Path) -> None:
        """Test security audit with npm."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="found 0 vulnerabilities",
            stderr=""
        )

        result = runner.run_security_audit(str(temp_js_repo))

        assert result["tool_used"] == "npm audit"
        assert result["vulnerabilities_found"] == 0

    @patch('subprocess.run')
    def test_run_build_npm_success(self, mock_run: MagicMock, runner: JavaScriptToolRunner, temp_js_repo: Path) -> None:
        """Test successful build with npm."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.run_build(str(temp_js_repo))

        assert result["success"] is True
        assert result["tool_used"] == "npm run build"


class TestJavaToolRunner:
    """Test Java tool runner functionality."""

    @pytest.fixture
    def runner(self) -> JavaToolRunner:
        """Create a Java tool runner instance."""
        return JavaToolRunner(timeout_seconds=30)

    @pytest.fixture
    def temp_java_repo(self) -> Path:
        """Create a temporary Java repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Java files
            (repo_path / "src" / "main" / "java" / "Main.java").write_text("public class Main {}")
            (repo_path / "pom.xml").write_text("<?xml version='1.0'?><project></project>")

            # Ensure directories exist
            (repo_path / "src" / "main" / "java").mkdir(parents=True, exist_ok=True)

            yield repo_path

    @patch('subprocess.run')
    def test_run_linting_checkstyle_success(self, mock_run: MagicMock, runner: JavaToolRunner, temp_java_repo: Path) -> None:
        """Test successful linting with Checkstyle."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.run_linting(str(temp_java_repo))

        assert result["tool_used"] == "checkstyle"
        assert result["passed"] is True

    @patch('subprocess.run')
    def test_run_testing_maven_success(self, mock_run: MagicMock, runner: JavaToolRunner, temp_java_repo: Path) -> None:
        """Test successful testing with Maven."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Tests run: 8, Failures: 0, Errors: 0, Skipped: 0",
            stderr=""
        )

        result = runner.run_testing(str(temp_java_repo))

        assert result["framework"] == "maven"
        assert result["tests_run"] == 8
        assert result["tests_passed"] == 8
        assert result["tests_failed"] == 0

    @patch('subprocess.run')
    def test_run_build_maven_success(self, mock_run: MagicMock, runner: JavaToolRunner, temp_java_repo: Path) -> None:
        """Test successful build with Maven."""
        mock_run.return_value = MagicMock(returncode=0, stdout="BUILD SUCCESS", stderr="")

        result = runner.run_build(str(temp_java_repo))

        assert result["success"] is True
        assert result["tool_used"] == "mvn compile"


class TestGolangToolRunner:
    """Test Golang tool runner functionality."""

    @pytest.fixture
    def runner(self) -> GolangToolRunner:
        """Create a Golang tool runner instance."""
        return GolangToolRunner(timeout_seconds=30)

    @pytest.fixture
    def temp_go_repo(self) -> Path:
        """Create a temporary Go repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Go files
            (repo_path / "main.go").write_text("package main\n\nfunc main() {}\n")
            (repo_path / "go.mod").write_text("module test\n\ngo 1.19\n")

            yield repo_path

    @patch('subprocess.run')
    def test_run_linting_golangci_success(self, mock_run: MagicMock, runner: GolangToolRunner, temp_go_repo: Path) -> None:
        """Test successful linting with golangci-lint."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.run_linting(str(temp_go_repo))

        assert result["tool_used"] == "golangci-lint"
        assert result["passed"] is True

    @patch('subprocess.run')
    def test_run_testing_go_test_success(self, mock_run: MagicMock, runner: GolangToolRunner, temp_go_repo: Path) -> None:
        """Test successful testing with go test."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ok  	test	0.123s",
            stderr=""
        )

        result = runner.run_testing(str(temp_go_repo))

        assert result["framework"] == "go test"
        assert result["tests_passed"] > 0

    @patch('subprocess.run')
    def test_run_security_audit_gosec_success(self, mock_run: MagicMock, runner: GolangToolRunner, temp_go_repo: Path) -> None:
        """Test successful security audit with gosec."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Summary: Issues: 0",
            stderr=""
        )

        result = runner.run_security_audit(str(temp_go_repo))

        assert result["tool_used"] == "gosec"
        assert result["vulnerabilities_found"] == 0

    @patch('subprocess.run')
    def test_run_build_go_build_success(self, mock_run: MagicMock, runner: GolangToolRunner, temp_go_repo: Path) -> None:
        """Test successful build with go build."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.run_build(str(temp_go_repo))

        assert result["success"] is True
        assert result["tool_used"] == "go build"

    @patch('subprocess.run')
    def test_run_linting_fallback_to_gofmt(self, mock_run: MagicMock, runner: GolangToolRunner, temp_go_repo: Path) -> None:
        """Test fallback to gofmt when golangci-lint is not available."""
        # First call (golangci-lint) fails, second call (gofmt) succeeds
        mock_run.side_effect = [
            MagicMock(returncode=127, stdout="", stderr="golangci-lint: command not found"),
            MagicMock(returncode=0, stdout="", stderr="")
        ]

        result = runner.run_linting(str(temp_go_repo))

        assert result["tool_used"] == "gofmt"
        assert result["passed"] is True
        assert mock_run.call_count == 2


class TestToolRunnerErrorHandling:
    """Test error handling across all tool runners."""

    def test_python_runner_invalid_path(self) -> None:
        """Test Python runner with invalid repository path."""
        runner = PythonToolRunner()
        result = runner.run_linting("/nonexistent/path")

        assert result["tool_used"] == "ruff"
        assert result["passed"] is False
        assert "error" in result

    def test_javascript_runner_invalid_path(self) -> None:
        """Test JavaScript runner with invalid repository path."""
        runner = JavaScriptToolRunner()
        result = runner.run_linting("/nonexistent/path")

        assert result["tool_used"] == "eslint"
        assert result["passed"] is False
        assert "error" in result

    def test_java_runner_invalid_path(self) -> None:
        """Test Java runner with invalid repository path."""
        runner = JavaToolRunner()
        result = runner.run_linting("/nonexistent/path")

        assert result["tool_used"] == "checkstyle"
        assert result["passed"] is False
        assert "error" in result

    def test_golang_runner_invalid_path(self) -> None:
        """Test Golang runner with invalid repository path."""
        runner = GolangToolRunner()
        result = runner.run_linting("/nonexistent/path")

        assert result["tool_used"] == "golangci-lint"
        assert result["passed"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_subprocess_exception_handling(self, mock_run: MagicMock) -> None:
        """Test handling of subprocess exceptions."""
        mock_run.side_effect = FileNotFoundError("Tool not found")

        runner = PythonToolRunner()
        result = runner.run_linting("/some/path")

        assert result["passed"] is False
        assert "error" in result
        assert "Tool not found" in result["error"]
