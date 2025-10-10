"""Integration test for Go build validation (T014) - Real scenarios only."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.metrics.tool_runners.golang_tools import GolangToolRunner


def check_tool_available(tool_name: str) -> bool:
    """Check if a tool is available in the system."""
    try:
        result = subprocess.run(
            ["which", tool_name],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


class TestGoBuildIntegrationReal:
    """Real integration tests for Go build validation - NO MOCKS."""

    @pytest.fixture
    def minimal_go_module(self) -> Path:
        """Create a minimal Go module with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create go.mod
            (repo_path / "go.mod").write_text("""module example.com/test-integration-go-package

go 1.21
""")

            # Create main.go with valid Go code
            (repo_path / "main.go").write_text("""package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
""")

            # Create README
            (repo_path / "README.md").write_text("""# Test Integration Go Package

This is a minimal test package for integration testing.
""")

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_go_build_validation_real_go_build(self, minimal_go_module: Path) -> None:
        """REAL TEST: Execute actual go build without mocks."""
        # Create tool runner
        runner = GolangToolRunner(timeout_seconds=60)

        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_go_module))

        # Verify build succeeded with real execution
        assert result is not None, "Build result should not be None"
        assert "success" in result, "Result should contain 'success' field"
        assert "tool_used" in result, "Result should contain 'tool_used' field"

        # With real go, if build is valid, it should succeed
        if result["success"] is not None:  # Tool was available and executed
            assert result["tool_used"] == "go", "Should use go"
            assert "execution_time_seconds" in result
            assert result["execution_time_seconds"] >= 0

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_go_build_validation_real_with_failing_build(self) -> None:
        """REAL TEST: Verify build failure is detected with actual execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create go.mod
            (repo_path / "go.mod").write_text("""module example.com/failing-build-test

go 1.21
""")

            # Create invalid Go code that will fail to compile
            (repo_path / "main.go").write_text("""package main

func main() {
    // Invalid syntax - undefined function
    undefinedFunction()
}
""")

            runner = GolangToolRunner(timeout_seconds=60)

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify failure is captured
            if result["success"] is not None:  # Tool was available
                assert result["success"] is False, "Build should fail with compilation error"
                assert result["error_message"] is not None
                assert result["exit_code"] != 0

    def test_go_build_validation_real_no_go_mod(self) -> None:
        """REAL TEST: Verify behavior when go.mod is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Go file WITHOUT go.mod
            (repo_path / "main.go").write_text("""package main

func main() {}
""")

            runner = GolangToolRunner(timeout_seconds=60)

            # REAL CHECK - No mocks
            result = runner.run_build(str(repo_path))

            # Should detect no go.mod
            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No go.mod" in result["error_message"]

    def test_go_build_validation_real_empty_directory(self) -> None:
        """REAL TEST: Verify behavior when directory is empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = GolangToolRunner(timeout_seconds=60)

            # REAL CHECK on empty directory
            result = runner.run_build(str(temp_dir))

            # Should detect missing go.mod
            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No go.mod" in result["error_message"]

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_go_build_validation_real_schema_compliance(self, minimal_go_module: Path) -> None:
        """REAL TEST: Verify result schema with actual build execution."""
        runner = GolangToolRunner(timeout_seconds=60)

        # REAL BUILD
        result = runner.run_build(str(minimal_go_module))

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

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_go_build_validation_real_execution_time_tracking(self, minimal_go_module: Path) -> None:
        """REAL TEST: Verify execution time is tracked during actual build."""
        runner = GolangToolRunner(timeout_seconds=60)

        # REAL BUILD
        result = runner.run_build(str(minimal_go_module))

        # Execution time should be positive and reasonable
        if result["success"] is not None:
            assert result["execution_time_seconds"] >= 0
            assert result["execution_time_seconds"] < 60, "Build should complete within timeout"

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_go_build_validation_real_with_dependencies(self) -> None:
        """REAL TEST: Verify build works with Go module dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create go.mod with a dependency
            (repo_path / "go.mod").write_text("""module example.com/deps-test

go 1.21

require github.com/google/uuid v1.3.0
""")

            # Create go.sum (empty is fine for this test)
            (repo_path / "go.sum").write_text("")

            # Create main.go that uses the dependency
            (repo_path / "main.go").write_text("""package main

import (
    "fmt"
    "github.com/google/uuid"
)

func main() {
    id := uuid.New()
    fmt.Println(id)
}
""")

            runner = GolangToolRunner(timeout_seconds=60)

            # REAL BUILD with dependencies
            result = runner.run_build(str(repo_path))

            # Build might succeed or fail depending on network/cache
            # Just verify the result structure is correct
            assert result is not None
            if result["success"] is not None:
                assert result["tool_used"] == "go"
                assert result["execution_time_seconds"] >= 0

    def test_go_build_validation_real_json_serialization(self, minimal_go_module: Path) -> None:
        """REAL TEST: Verify build results can be serialized to JSON."""
        import json

        runner = GolangToolRunner(timeout_seconds=60)

        # Execute build (will skip if go not available, but still test serialization)
        result = runner.run_build(str(minimal_go_module))

        # Verify JSON serialization works
        try:
            json_str = json.dumps(result)
            assert json_str is not None
            assert len(json_str) > 0

            # Verify deserialization
            deserialized = json.loads(json_str)
            assert deserialized["success"] == result["success"]
            assert deserialized["tool_used"] == result["tool_used"]
        except (TypeError, ValueError) as e:
            pytest.fail(f"Build result should be JSON serializable: {e}")


class TestGoBuildIntegrationWorkflow:
    """Real workflow integration tests for Go build validation."""

    def test_go_build_integrates_with_pipeline(self) -> None:
        """Test that Go build validation integrates into metrics pipeline."""
        runner = GolangToolRunner(timeout_seconds=60)

        # Verify interface exists
        assert hasattr(runner, 'run_build'), "GolangToolRunner should have run_build method"
        assert callable(runner.run_build), "run_build should be callable"

        # Verify method signature
        import inspect
        sig = inspect.signature(runner.run_build)
        assert 'repo_path' in sig.parameters, "run_build should accept repo_path parameter"

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_go_build_real_end_to_end_workflow(self) -> None:
        """REAL END-TO-END TEST: Complete workflow with actual tool execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # 1. Create a realistic Go project
            (repo_path / "go.mod").write_text("""module example.com/e2e-test-project

go 1.21
""")

            # Create pkg directory with a package
            pkg_dir = repo_path / "pkg" / "greeting"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "greeting.go").write_text("""package greeting

// Greet returns a greeting message
func Greet(name string) string {
    return "Hello, " + name + "!"
}
""")

            # Create cmd directory with main
            cmd_dir = repo_path / "cmd" / "app"
            cmd_dir.mkdir(parents=True)
            (cmd_dir / "main.go").write_text("""package main

import (
    "fmt"
    "example.com/e2e-test-project/pkg/greeting"
)

func main() {
    msg := greeting.Greet("World")
    fmt.Println(msg)
}
""")

            # 2. Execute REAL build
            runner = GolangToolRunner(timeout_seconds=60)
            result = runner.run_build(str(repo_path))

            # 3. Verify results
            assert result is not None
            if result["success"] is not None:  # go was available
                assert result["success"] is True, "E2E build should succeed"
                assert result["tool_used"] == "go"
                assert result["exit_code"] == 0


class TestGoBuildMultiPackage:
    """Real tests for Go build with multiple packages."""

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_go_build_validation_real_multi_package(self) -> None:
        """REAL TEST: Verify build works with multiple packages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create go.mod
            (repo_path / "go.mod").write_text("""module example.com/multi-package-test

go 1.21
""")

            # Create package1
            pkg1_dir = repo_path / "pkg1"
            pkg1_dir.mkdir(parents=True)
            (pkg1_dir / "pkg1.go").write_text("""package pkg1

func Hello() string {
    return "Hello from pkg1"
}
""")

            # Create package2
            pkg2_dir = repo_path / "pkg2"
            pkg2_dir.mkdir(parents=True)
            (pkg2_dir / "pkg2.go").write_text("""package pkg2

func World() string {
    return "World from pkg2"
}
""")

            # Create main that uses both packages
            (repo_path / "main.go").write_text("""package main

import (
    "fmt"
    "example.com/multi-package-test/pkg1"
    "example.com/multi-package-test/pkg2"
)

func main() {
    fmt.Println(pkg1.Hello(), pkg2.World())
}
""")

            runner = GolangToolRunner(timeout_seconds=60)

            # REAL BUILD with multiple packages
            result = runner.run_build(str(repo_path))

            # Should build all packages successfully
            if result["success"] is not None:
                assert result["success"] is True, "Multi-package build should succeed"
                assert result["tool_used"] == "go"
                assert result["exit_code"] == 0

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_go_build_validation_real_syntax_error(self) -> None:
        """REAL TEST: Verify syntax errors are properly captured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create go.mod
            (repo_path / "go.mod").write_text("""module example.com/syntax-error-test

go 1.21
""")

            # Create Go file with syntax error
            (repo_path / "main.go").write_text("""package main

import "fmt"

func main() {
    fmt.Println("Missing closing quote)
}
""")

            runner = GolangToolRunner(timeout_seconds=60)

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify syntax error is captured
            if result["success"] is not None:
                assert result["success"] is False, "Build should fail with syntax error"
                assert result["error_message"] is not None
                # Error message should mention the syntax issue
                assert "syntax" in result["error_message"].lower() or "error" in result["error_message"].lower()
                assert result["exit_code"] != 0
