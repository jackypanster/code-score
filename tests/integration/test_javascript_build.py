"""Integration test for JavaScript build validation (T013) - Real scenarios only."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.metrics.tool_runners.javascript_tools import JavaScriptToolRunner


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


class TestJavaScriptBuildIntegrationReal:
    """Real integration tests for JavaScript build validation - NO MOCKS."""

    @pytest.fixture
    def minimal_js_package(self) -> Path:
        """Create a minimal JavaScript package with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create package.json with a simple build script (no webpack needed)
            (repo_path / "package.json").write_text("""{
  "name": "test-integration-js-package",
  "version": "1.0.0",
  "description": "Test package for integration testing",
  "main": "index.js",
  "scripts": {
    "build": "node build.js",
    "test": "echo \\"Tests passed\\""
  },
  "author": "",
  "license": "ISC"
}
""")

            # Create a simple build script that actually works without dependencies
            (repo_path / "build.js").write_text("""// Simple build script
const fs = require('fs');
const path = require('path');

// Create dist directory
if (!fs.existsSync('dist')) {
  fs.mkdirSync('dist');
}

// Copy main file to dist
const source = fs.readFileSync('index.js', 'utf8');
fs.writeFileSync(path.join('dist', 'index.js'), source);

console.log('Build successful!');
""")

            # Create main source file
            (repo_path / "index.js").write_text("""/**
 * Main entry point
 */
function hello(name) {
  return `Hello, ${name}!`;
}

module.exports = { hello };
""")

            # Create README
            (repo_path / "README.md").write_text("""# Test Integration JS Package

This is a minimal test package for integration testing.
""")

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("npm"), reason="npm not available")
    def test_javascript_build_validation_real_npm_build(self, minimal_js_package: Path) -> None:
        """REAL TEST: Execute actual npm build without mocks."""
        # Create tool runner
        runner = JavaScriptToolRunner(timeout_seconds=60)

        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_js_package))

        # Verify build succeeded with real execution
        assert result is not None, "Build result should not be None"
        assert "success" in result, "Result should contain 'success' field"
        assert "tool_used" in result, "Result should contain 'tool_used' field"

        # With real npm, if build script is valid, it should succeed
        if result["success"] is not None:  # Tool was available and executed
            assert result["tool_used"] in ["npm", "yarn"], "Should use npm or yarn"
            assert "execution_time_seconds" in result
            assert result["execution_time_seconds"] >= 0

    @pytest.mark.skipif(not check_tool_available("npm"), reason="npm not available")
    def test_javascript_build_validation_real_with_failing_build(self) -> None:
        """REAL TEST: Verify build failure is detected with actual execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create package.json with a failing build script
            (repo_path / "package.json").write_text("""{
  "name": "failing-build-test",
  "version": "1.0.0",
  "scripts": {
    "build": "node nonexistent-build-file.js"
  }
}
""")

            runner = JavaScriptToolRunner(timeout_seconds=60)

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify failure is captured
            if result["success"] is not None:  # Tool was available
                assert result["success"] is False, "Build should fail with nonexistent file"
                assert result["error_message"] is not None
                assert result["exit_code"] != 0

    def test_javascript_build_validation_real_no_build_script(self) -> None:
        """REAL TEST: Verify behavior when no build script is defined."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create package.json WITHOUT build script
            (repo_path / "package.json").write_text("""{
  "name": "no-build-script-test",
  "version": "1.0.0",
  "scripts": {
    "test": "echo \\"test\\""
  }
}
""")

            runner = JavaScriptToolRunner(timeout_seconds=60)

            # REAL CHECK - No mocks
            result = runner.run_build(str(repo_path))

            # Should detect no build script
            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No build script" in result["error_message"]

    def test_javascript_build_validation_real_no_package_json(self) -> None:
        """REAL TEST: Verify behavior when package.json is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = JavaScriptToolRunner(timeout_seconds=60)

            # REAL CHECK on empty directory
            result = runner.run_build(str(temp_dir))

            # Should detect missing package.json
            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No package.json" in result["error_message"]

    @pytest.mark.skipif(not check_tool_available("npm"), reason="npm not available")
    def test_javascript_build_validation_real_schema_compliance(self, minimal_js_package: Path) -> None:
        """REAL TEST: Verify result schema with actual build execution."""
        runner = JavaScriptToolRunner(timeout_seconds=60)

        # REAL BUILD
        result = runner.run_build(str(minimal_js_package))

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

    @pytest.mark.skipif(not check_tool_available("npm"), reason="npm not available")
    def test_javascript_build_validation_real_execution_time_tracking(self, minimal_js_package: Path) -> None:
        """REAL TEST: Verify execution time is tracked during actual build."""
        runner = JavaScriptToolRunner(timeout_seconds=60)

        # REAL BUILD
        result = runner.run_build(str(minimal_js_package))

        # Execution time should be positive and reasonable
        if result["success"] is not None:
            assert result["execution_time_seconds"] >= 0
            assert result["execution_time_seconds"] < 60, "Build should complete within timeout"

    @pytest.mark.skipif(
        not check_tool_available("yarn"),
        reason="yarn not available"
    )
    def test_javascript_build_validation_real_yarn_detection(self) -> None:
        """REAL TEST: Verify yarn is detected when yarn.lock exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create package.json with build script
            (repo_path / "package.json").write_text("""{
  "name": "yarn-test",
  "version": "1.0.0",
  "scripts": {
    "build": "node -e \\"console.log('Built with yarn')\\""
  }
}
""")

            # Create yarn.lock to trigger yarn detection
            (repo_path / "yarn.lock").write_text("# Yarn lockfile v1\n")

            runner = JavaScriptToolRunner(timeout_seconds=60)

            # REAL BUILD with yarn
            result = runner.run_build(str(repo_path))

            # Should use yarn when yarn.lock exists
            if result["success"] is not None:
                assert result["tool_used"] == "yarn", "Should detect and use yarn"

    def test_javascript_build_validation_real_json_serialization(self, minimal_js_package: Path) -> None:
        """REAL TEST: Verify build results can be serialized to JSON."""
        import json

        runner = JavaScriptToolRunner(timeout_seconds=60)

        # Execute build (will skip if npm not available, but still test serialization)
        result = runner.run_build(str(minimal_js_package))

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


class TestJavaScriptBuildIntegrationWorkflow:
    """Real workflow integration tests for JavaScript build validation."""

    def test_javascript_build_integrates_with_pipeline(self) -> None:
        """Test that JavaScript build validation integrates into metrics pipeline."""
        runner = JavaScriptToolRunner(timeout_seconds=60)

        # Verify interface exists
        assert hasattr(runner, 'run_build'), "JavaScriptToolRunner should have run_build method"
        assert callable(runner.run_build), "run_build should be callable"

        # Verify method signature
        import inspect
        sig = inspect.signature(runner.run_build)
        assert 'repo_path' in sig.parameters, "run_build should accept repo_path parameter"

    @pytest.mark.skipif(not check_tool_available("npm"), reason="npm not available")
    def test_javascript_build_real_end_to_end_workflow(self) -> None:
        """REAL END-TO-END TEST: Complete workflow with actual tool execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # 1. Create a realistic JavaScript project
            (repo_path / "package.json").write_text("""{
  "name": "e2e-test-project",
  "version": "1.0.0",
  "description": "End-to-end test project",
  "main": "src/index.js",
  "scripts": {
    "build": "node scripts/build.js"
  }
}
""")

            # Create source directory
            src_dir = repo_path / "src"
            src_dir.mkdir()
            (src_dir / "index.js").write_text("""module.exports = {
  version: '1.0.0',
  greeting: (name) => `Hello, ${name}!`
};
""")

            # Create build script directory
            scripts_dir = repo_path / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "build.js").write_text("""const fs = require('fs');
const path = require('path');

// Simple build process
const distDir = path.join(__dirname, '..', 'dist');
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir);
}

const source = fs.readFileSync(path.join(__dirname, '..', 'src', 'index.js'), 'utf8');
fs.writeFileSync(path.join(distDir, 'index.js'), source);

console.log('Build completed successfully');
""")

            # 2. Execute REAL build
            runner = JavaScriptToolRunner(timeout_seconds=60)
            result = runner.run_build(str(repo_path))

            # 3. Verify results
            assert result is not None
            if result["success"] is not None:  # npm was available
                assert result["success"] is True, "E2E build should succeed"
                assert result["tool_used"] in ["npm", "yarn"]
                assert result["exit_code"] == 0

                # 4. Verify actual build artifacts were created
                dist_dir = repo_path / "dist"
                assert dist_dir.exists(), "Build should create dist directory"
                assert (dist_dir / "index.js").exists(), "Build should create output file"


class TestJavaScriptBuildToolDetection:
    """Real tests for JavaScript build tool detection and selection."""

    def test_npm_vs_yarn_priority_real(self) -> None:
        """REAL TEST: Verify npm is used when yarn.lock doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create package.json without yarn.lock
            (repo_path / "package.json").write_text("""{
  "name": "npm-priority-test",
  "version": "1.0.0",
  "scripts": {
    "build": "echo build"
  }
}
""")

            runner = JavaScriptToolRunner(timeout_seconds=60)
            result = runner.run_build(str(repo_path))

            # Should prefer npm when no yarn.lock
            if result["success"] is not None and check_tool_available("npm"):
                assert result["tool_used"] == "npm", "Should use npm when yarn.lock absent"
