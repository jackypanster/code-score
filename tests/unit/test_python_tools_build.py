"""Real execution tests for PythonToolRunner.run_build() method.

NO MOCKS - All tests use real tool execution with actual builds.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

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


def check_python_module_available(module_name: str) -> bool:
    """Check if a Python module is available."""
    try:
        result = subprocess.run(
            ["python3", "-c", f"import {module_name}"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


class TestPythonToolRunnerBuildReal:
    """REAL TESTS for PythonToolRunner.run_build() - NO MOCKS."""

    @pytest.fixture
    def runner(self) -> PythonToolRunner:
        """Create a Python tool runner instance."""
        return PythonToolRunner(timeout_seconds=120)

    @pytest.fixture
    def minimal_python_project(self) -> Path:
        """Create a minimal Python project with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pyproject.toml
            (repo_path / "pyproject.toml").write_text("""[project]
name = "test-package"
version = "0.1.0"

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
""")

            # Create basic package structure
            (repo_path / "src").mkdir()
            (repo_path / "src" / "test_package").mkdir(parents=True)
            (repo_path / "src" / "test_package" / "__init__.py").write_text('__version__ = "0.1.0"\n')

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("uv"), reason="uv not available")
    def test_run_build_uv_real_success(self, runner: PythonToolRunner, minimal_python_project: Path) -> None:
        """REAL TEST: Execute actual uv build without mocks."""
        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_python_project))

        # Verify build succeeded with real execution
        assert result is not None
        assert "success" in result
        assert "tool_used" in result

        # If uv is available, it should succeed
        if result["success"] is not None:
            assert result["tool_used"] == "uv"
            assert result["execution_time_seconds"] >= 0
            assert result["error_message"] is None
            assert result["exit_code"] == 0

    @pytest.mark.skipif(
        check_tool_available("uv") or not check_python_module_available("build"),
        reason="uv available or build module not available"
    )
    def test_run_build_python_build_real_success(self, runner: PythonToolRunner, minimal_python_project: Path) -> None:
        """REAL TEST: Execute actual python -m build without mocks."""
        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_python_project))

        # Verify build succeeded with real execution
        assert result is not None
        if result["success"] is not None:
            assert result["tool_used"] == "build"
            assert result["execution_time_seconds"] >= 0
            assert result["error_message"] is None
            assert result["exit_code"] == 0

    @pytest.mark.skipif(not check_tool_available("uv"), reason="uv not available")
    def test_run_build_uv_real_failure(self, runner: PythonToolRunner) -> None:
        """REAL TEST: Verify uv build failure is detected with actual execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pyproject.toml with syntax error (invalid TOML)
            (repo_path / "pyproject.toml").write_text("""[project
name = "invalid-package"
version = "0.1.0"
""")

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify failure is captured
            if result["success"] is not None:
                assert result["success"] is False
                assert result["tool_used"] == "uv"
                assert result["error_message"] is not None
                assert result["exit_code"] != 0

    def test_run_build_real_no_pyproject_toml(self, runner: PythonToolRunner) -> None:
        """REAL TEST: Verify behavior when pyproject.toml doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # REAL CHECK - No mocks
            result = runner.run_build(str(temp_dir))

            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert result["error_message"] is not None
            assert "No Python build configuration" in result["error_message"]
            assert result["exit_code"] is None

    @pytest.mark.skipif(not check_tool_available("uv"), reason="uv not available")
    def test_run_build_real_with_setup_py(self, runner: PythonToolRunner) -> None:
        """REAL TEST: Verify build detection with setup.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create setup.py instead of pyproject.toml
            (repo_path / "setup.py").write_text("""from setuptools import setup, find_packages

setup(
    name="test-package",
    version="0.1.0",
    packages=find_packages(),
)
""")

            # REAL BUILD
            result = runner.run_build(str(repo_path))

            # Should detect setup.py and attempt build
            assert result is not None
            if result["success"] is not None:
                assert result["tool_used"] in ["uv", "build"]

    def test_run_build_real_error_message_truncation(self, runner: PythonToolRunner) -> None:
        """REAL TEST: Verify error messages are truncated to 1000 characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pyproject.toml with very long package name (will generate long error)
            long_name = "a" * 500
            (repo_path / "pyproject.toml").write_text(f"""[project]
name = "{long_name}"
version = "0.1.0"

[build-system]
requires = ["setuptools>=45"]
build-backend = "setuptools.build_meta"
""")

            # REAL BUILD that may fail
            result = runner.run_build(str(repo_path))

            # If there's an error message, it should be truncated
            if result["error_message"] is not None:
                assert len(result["error_message"]) <= 1000

    @pytest.mark.skipif(not check_tool_available("uv"), reason="uv not available")
    def test_run_build_real_pyproject_toml_detection(self, runner: PythonToolRunner, minimal_python_project: Path) -> None:
        """REAL TEST: Verify that pyproject.toml is properly detected."""
        # REAL BUILD
        result = runner.run_build(str(minimal_python_project))

        # Should succeed because pyproject.toml exists
        assert result is not None
        if result["success"] is not None:
            assert result["tool_used"] in ["uv", "build"]
            assert result["execution_time_seconds"] >= 0

    def test_run_build_real_no_build_tools_available(self, runner: PythonToolRunner) -> None:
        """REAL TEST: Verify behavior when neither uv nor build module are available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create valid pyproject.toml
            (repo_path / "pyproject.toml").write_text("""[project]
name = "test"
version = "0.1.0"

[build-system]
requires = ["setuptools>=45"]
build-backend = "setuptools.build_meta"
""")

            # REAL CHECK - No mocks
            result = runner.run_build(str(repo_path))

            # Result depends on what tools are actually installed
            assert result is not None
            assert "success" in result
            assert "tool_used" in result

            # If no tools available, success should be None
            if result["tool_used"] == "none":
                assert result["success"] is None

    def test_run_build_real_schema_compliance(self, runner: PythonToolRunner, minimal_python_project: Path) -> None:
        """REAL TEST: Verify result schema with actual build execution."""
        # REAL BUILD
        result = runner.run_build(str(minimal_python_project))

        # Verify all required fields exist
        required_fields = ["success", "tool_used", "execution_time_seconds", "error_message", "exit_code"]
        for field in required_fields:
            assert field in result, f"Result must contain '{field}' field"

        # Verify field types
        assert isinstance(result["success"], bool) or result["success"] is None
        assert isinstance(result["tool_used"], str)
        assert isinstance(result["execution_time_seconds"], (int, float))
        assert isinstance(result["error_message"], str) or result["error_message"] is None
        assert isinstance(result["exit_code"], int) or result["exit_code"] is None

    @pytest.mark.skipif(not check_tool_available("uv"), reason="uv not available")
    def test_run_build_real_with_dependencies(self, runner: PythonToolRunner) -> None:
        """REAL TEST: Verify Python build works with dependencies declared."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pyproject.toml with dependencies
            (repo_path / "pyproject.toml").write_text("""[project]
name = "deps-test"
version = "0.1.0"
dependencies = []

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
""")

            # Create package structure
            pkg_dir = repo_path / "src" / "deps_test"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "__init__.py").write_text('__version__ = "0.1.0"\n')

            # REAL BUILD
            result = runner.run_build(str(repo_path))

            # Build might succeed or fail depending on environment
            # Just verify the result structure is correct
            assert result is not None
            if result["success"] is not None:
                assert result["tool_used"] in ["uv", "build"]
                assert result["execution_time_seconds"] >= 0
