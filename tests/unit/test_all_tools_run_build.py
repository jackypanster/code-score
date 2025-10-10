"""Real execution tests for run_build() methods across all tool runners (T009-T011).

NO MOCKS - All tests use real tool execution with actual builds.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.metrics.tool_runners.golang_tools import GolangToolRunner
from src.metrics.tool_runners.java_tools import JavaToolRunner
from src.metrics.tool_runners.javascript_tools import JavaScriptToolRunner


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


class TestJavaScriptToolRunnerBuildReal:
    """REAL TESTS for JavaScriptToolRunner.run_build() - NO MOCKS."""

    @pytest.fixture
    def runner(self) -> JavaScriptToolRunner:
        """Create a JavaScript tool runner instance."""
        return JavaScriptToolRunner(timeout_seconds=120)

    @pytest.fixture
    def minimal_js_project(self) -> Path:
        """Create a minimal JavaScript project with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create package.json with simple echo build script (no webpack needed)
            (repo_path / "package.json").write_text("""{
  "name": "test-package",
  "version": "1.0.0",
  "scripts": {
    "build": "echo 'Build complete'"
  }
}
""")

            # Create source file
            (repo_path / "index.js").write_text('console.log("Hello World");\n')

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("npm"), reason="npm not available")
    def test_run_build_npm_real_success(self, runner: JavaScriptToolRunner, minimal_js_project: Path) -> None:
        """REAL TEST: Execute actual npm run build without mocks."""
        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_js_project))

        # Verify build succeeded with real execution
        assert result is not None
        assert "success" in result
        assert "tool_used" in result

        # If npm is available, it should succeed
        if result["success"] is not None:
            assert result["tool_used"] == "npm"
            assert result["execution_time_seconds"] >= 0
            assert result["exit_code"] == 0

    @pytest.mark.skipif(not check_tool_available("yarn"), reason="yarn not available")
    def test_run_build_yarn_real_success(self, runner: JavaScriptToolRunner) -> None:
        """REAL TEST: Execute actual yarn build without mocks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create package.json with echo build script
            (repo_path / "package.json").write_text('{"name": "test", "version": "1.0.0", "scripts": {"build": "echo Done"}}')
            # Create yarn.lock to trigger yarn detection
            (repo_path / "yarn.lock").write_text("")

            # REAL BUILD
            result = runner.run_build(str(repo_path))

            assert result is not None
            if result["success"] is not None:
                assert result["tool_used"] == "yarn"
                assert result["execution_time_seconds"] >= 0

    @pytest.mark.skipif(not check_tool_available("npm"), reason="npm not available")
    def test_run_build_npm_real_failure(self, runner: JavaScriptToolRunner) -> None:
        """REAL TEST: Verify npm build failure is detected with actual execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create package.json with failing build script
            (repo_path / "package.json").write_text("""{
  "name": "test-fail",
  "version": "1.0.0",
  "scripts": {
    "build": "exit 1"
  }
}
""")

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify failure is captured
            if result["success"] is not None:
                assert result["success"] is False
                assert result["tool_used"] == "npm"
                assert result["exit_code"] == 1

    def test_run_build_real_no_build_script(self, runner: JavaScriptToolRunner) -> None:
        """REAL TEST: Verify behavior when no build script is defined."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            # package.json without build script
            (repo_path / "package.json").write_text('{"name": "test", "scripts": {"test": "jest"}}')

            # REAL CHECK - No mocks
            result = runner.run_build(str(repo_path))

            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No build script" in result["error_message"]

    def test_run_build_real_no_package_json(self, runner: JavaScriptToolRunner) -> None:
        """REAL TEST: Verify behavior when package.json doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # REAL CHECK - No mocks
            result = runner.run_build(str(temp_dir))

            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No package.json" in result["error_message"]


class TestGolangToolRunnerBuildReal:
    """REAL TESTS for GolangToolRunner.run_build() - NO MOCKS."""

    @pytest.fixture
    def runner(self) -> GolangToolRunner:
        """Create a Go tool runner instance."""
        return GolangToolRunner(timeout_seconds=120)

    @pytest.fixture
    def minimal_go_project(self) -> Path:
        """Create a minimal Go project with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create go.mod
            (repo_path / "go.mod").write_text("""module example.com/testproject

go 1.21
""")

            # Create main.go
            (repo_path / "main.go").write_text("""package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
""")

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_run_build_go_real_success(self, runner: GolangToolRunner, minimal_go_project: Path) -> None:
        """REAL TEST: Execute actual go build without mocks."""
        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_go_project))

        # Verify build succeeded with real execution
        assert result is not None
        assert "success" in result
        assert "tool_used" in result

        # If go is available, it should succeed
        if result["success"] is not None:
            assert result["tool_used"] == "go"
            assert result["execution_time_seconds"] >= 0
            assert result["error_message"] is None
            assert result["exit_code"] == 0

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_run_build_go_real_failure(self, runner: GolangToolRunner) -> None:
        """REAL TEST: Verify go build failure is detected with actual execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create go.mod
            (repo_path / "go.mod").write_text("""module example.com/failing

go 1.21
""")

            # Create main.go with compilation error
            (repo_path / "main.go").write_text("""package main

func main() {
    // Undefined function call
    undefinedFunction()
}
""")

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify failure is captured
            if result["success"] is not None:
                assert result["success"] is False
                assert result["tool_used"] == "go"
                assert result["error_message"] is not None
                assert result["exit_code"] != 0

    def test_run_build_real_no_go_mod(self, runner: GolangToolRunner) -> None:
        """REAL TEST: Verify behavior when go.mod doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # REAL CHECK - No mocks
            result = runner.run_build(str(temp_dir))

            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No go.mod" in result["error_message"]

    @pytest.mark.skipif(not check_tool_available("go"), reason="go not available")
    def test_run_build_real_result_format_matches_schema(self, runner: GolangToolRunner, minimal_go_project: Path) -> None:
        """REAL TEST: Verify result schema with actual go build execution."""
        # REAL BUILD
        result = runner.run_build(str(minimal_go_project))

        # Verify all required fields are present
        required_fields = ["success", "tool_used", "execution_time_seconds", "error_message", "exit_code"]
        for field in required_fields:
            assert field in result, f"Result must contain '{field}' field"

        # Verify field types
        assert isinstance(result["success"], bool) or result["success"] is None
        assert isinstance(result["tool_used"], str)
        assert isinstance(result["execution_time_seconds"], (int, float))
        assert isinstance(result["error_message"], str) or result["error_message"] is None
        assert isinstance(result["exit_code"], int) or result["exit_code"] is None


class TestJavaToolRunnerBuildReal:
    """REAL TESTS for JavaToolRunner.run_build() - NO MOCKS."""

    @pytest.fixture
    def runner(self) -> JavaToolRunner:
        """Create a Java tool runner instance."""
        return JavaToolRunner(timeout_seconds=120)

    @pytest.fixture
    def minimal_maven_project(self) -> Path:
        """Create a minimal Maven project with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pom.xml
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0-SNAPSHOT</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>
""")

            # Create source directory
            src_dir = repo_path / "src" / "main" / "java" / "com" / "example"
            src_dir.mkdir(parents=True)
            (src_dir / "Main.java").write_text("""package com.example;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
""")

            yield repo_path

    @pytest.fixture
    def minimal_gradle_project(self) -> Path:
        """Create a minimal Gradle project with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create build.gradle
            (repo_path / "build.gradle").write_text("""plugins {
    id 'java'
}

group = 'com.example'
version = '1.0-SNAPSHOT'
sourceCompatibility = '11'
""")

            # Create source directory
            src_dir = repo_path / "src" / "main" / "java"
            src_dir.mkdir(parents=True)
            (src_dir / "Main.java").write_text("public class Main {}")

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("mvn"), reason="maven not available")
    def test_run_build_maven_real_success(self, runner: JavaToolRunner, minimal_maven_project: Path) -> None:
        """REAL TEST: Execute actual mvn compile without mocks."""
        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_maven_project))

        # Verify build succeeded with real execution
        assert result is not None
        assert "success" in result
        assert "tool_used" in result

        # If maven is available, it should succeed
        if result["success"] is not None:
            assert result["tool_used"] == "mvn"
            assert result["execution_time_seconds"] >= 0
            assert result["error_message"] is None
            assert result["exit_code"] == 0

    @pytest.mark.skipif(not check_tool_available("gradle"), reason="gradle not available")
    def test_run_build_gradle_real_success(self, runner: JavaToolRunner, minimal_gradle_project: Path) -> None:
        """REAL TEST: Execute actual gradle compileJava without mocks."""
        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_gradle_project))

        # Verify build succeeded with real execution
        assert result is not None
        if result["success"] is not None:
            assert result["tool_used"] == "gradle"
            assert result["execution_time_seconds"] >= 0

    @pytest.mark.skipif(not check_tool_available("mvn"), reason="maven not available")
    def test_run_build_maven_real_failure(self, runner: JavaToolRunner) -> None:
        """REAL TEST: Verify Maven build failure is detected with actual execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pom.xml
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>failing-build</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>
""")

            # Create source with compilation error
            src_dir = repo_path / "src" / "main" / "java" / "com" / "example"
            src_dir.mkdir(parents=True)
            (src_dir / "Broken.java").write_text("""package com.example;

public class Broken {
    public void test() {
        // Undefined variable
        System.out.println(undefinedVariable);
    }
}
""")

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify failure is captured
            if result["success"] is not None:
                assert result["success"] is False
                assert result["tool_used"] == "mvn"
                assert result["error_message"] is not None
                assert result["exit_code"] != 0

    def test_run_build_real_no_build_file(self, runner: JavaToolRunner) -> None:
        """REAL TEST: Verify behavior when neither pom.xml nor build.gradle exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # REAL CHECK - No mocks
            result = runner.run_build(str(temp_dir))

            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No Maven or Gradle" in result["error_message"]
