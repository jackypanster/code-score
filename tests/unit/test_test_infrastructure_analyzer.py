"""Unit tests for TestInfrastructureAnalyzer pattern matching logic.

These tests validate that the analyzer correctly detects test files for
different programming languages using file patterns.

Test Coverage (FR-001 through FR-004):
- Python: tests/ directory, test_*.py, *_test.py (FR-001)
- JavaScript/TypeScript: __tests__/ directory, *.test.js, *.spec.js (FR-002)
- Go: *_test.go pattern (FR-003)
- Java: src/test/java/ directory (FR-004)

Expected Status: FAIL until TestInfrastructureAnalyzer is implemented (T021-T025).
"""

import tempfile
from pathlib import Path

import pytest


@pytest.mark.unit
class TestPythonTestFileDetection:
    """Unit tests for Python test file pattern matching (FR-001)."""

    @pytest.fixture
    def python_repo_structure(self, tmp_path: Path) -> Path:
        """Create synthetic Python repo structure for testing."""
        # Create tests/ directory with pytest files
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        (tests_dir / "test_module.py").write_text("# test file")
        (tests_dir / "test_another.py").write_text("# test file")
        (tests_dir / "utils_test.py").write_text("# test file")

        # Create non-test Python files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# source file")
        (tmp_path / "src" / "helper.py").write_text("# source file")

        # Create non-Python files (should be ignored)
        (tmp_path / "README.md").write_text("# README")

        return tmp_path

    def test_detects_tests_directory_files(self, python_repo_structure: Path):
        """Test detection of test files in tests/ directory (FR-001)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(python_repo_structure), "python")

        # Should detect 3 test files
        assert result.static_infrastructure.test_files_detected == 3, "Should detect all 3 test files"

    def test_matches_test_prefix_pattern(self, python_repo_structure: Path):
        """Test that test_*.py pattern is matched (FR-001)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        # Analyzer should internally match test_module.py and test_another.py
        result = analyzer.analyze(str(python_repo_structure), "python")

        assert result.static_infrastructure.test_files_detected >= 2, "Should detect test_*.py files"

    def test_matches_test_suffix_pattern(self, python_repo_structure: Path):
        """Test that *_test.py pattern is matched (FR-001)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        # Analyzer should match utils_test.py
        result = analyzer.analyze(str(python_repo_structure), "python")

        assert result.static_infrastructure.test_files_detected >= 1, "Should detect *_test.py files"

    def test_ignores_non_test_files(self, python_repo_structure: Path):
        """Test that non-test Python files are not counted as tests."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(python_repo_structure), "python")

        # Should not count main.py and helper.py as test files
        assert result.static_infrastructure.test_files_detected == 3, "Should only count test files, not source files"


@pytest.mark.unit
class TestJavaScriptTestFileDetection:
    """Unit tests for JavaScript/TypeScript test file pattern matching (FR-002)."""

    @pytest.fixture
    def javascript_repo_structure(self, tmp_path: Path) -> Path:
        """Create synthetic JavaScript repo structure for testing."""
        # Create __tests__/ directory
        tests_dir = tmp_path / "__tests__"
        tests_dir.mkdir()
        (tests_dir / "app.test.js").write_text("// test file")

        # Create spec files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "component.spec.js").write_text("// spec file")
        (tmp_path / "src" / "utils.test.ts").write_text("// TypeScript test")

        # Create non-test files
        (tmp_path / "src" / "main.js").write_text("// source file")
        (tmp_path / "package.json").write_text("{}")

        return tmp_path

    def test_detects_tests_directory_files(self, javascript_repo_structure: Path):
        """Test detection of test files in __tests__/ directory (FR-002)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(javascript_repo_structure), "javascript")

        assert result.static_infrastructure.test_files_detected >= 1, "Should detect files in __tests__/ directory"

    def test_matches_test_js_pattern(self, javascript_repo_structure: Path):
        """Test that *.test.js pattern is matched (FR-002)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(javascript_repo_structure), "javascript")

        # Should detect app.test.js and utils.test.ts
        assert result.static_infrastructure.test_files_detected >= 2, "Should detect *.test.js files"

    def test_matches_spec_js_pattern(self, javascript_repo_structure: Path):
        """Test that *.spec.js pattern is matched (FR-002)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(javascript_repo_structure), "javascript")

        # Should detect component.spec.js
        assert result.static_infrastructure.test_files_detected >= 1, "Should detect *.spec.js files"

    def test_handles_typescript_variants(self, javascript_repo_structure: Path):
        """Test that TypeScript .ts variants are detected (FR-002)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(javascript_repo_structure), "javascript")

        # Should detect utils.test.ts
        assert result.static_infrastructure.test_files_detected == 3, "Should detect TypeScript test files"


@pytest.mark.unit
class TestGoTestFileDetection:
    """Unit tests for Go test file pattern matching (FR-003)."""

    @pytest.fixture
    def go_repo_structure(self, tmp_path: Path) -> Path:
        """Create synthetic Go repo structure for testing."""
        # Create Go test files
        (tmp_path / "main_test.go").write_text("package main")
        (tmp_path / "utils_test.go").write_text("package main")

        # Create non-test Go files
        (tmp_path / "main.go").write_text("package main")
        (tmp_path / "helper.go").write_text("package main")

        # Create go.mod
        (tmp_path / "go.mod").write_text("module example")

        return tmp_path

    def test_matches_test_go_pattern(self, go_repo_structure: Path):
        """Test that *_test.go pattern is matched (FR-003)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(go_repo_structure), "go")

        # Should detect main_test.go and utils_test.go
        assert result.static_infrastructure.test_files_detected == 2, "Should detect *_test.go files"

    def test_ignores_non_test_go_files(self, go_repo_structure: Path):
        """Test that non-test Go files are not counted as tests."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(go_repo_structure), "go")

        # Should not count main.go and helper.go
        assert result.static_infrastructure.test_files_detected == 2, "Should only count test files"


@pytest.mark.unit
class TestJavaTestFileDetection:
    """Unit tests for Java test file pattern matching (FR-004)."""

    @pytest.fixture
    def java_repo_structure(self, tmp_path: Path) -> Path:
        """Create synthetic Java repo structure for testing."""
        # Create src/test/java/ directory
        test_dir = tmp_path / "src" / "test" / "java" / "com" / "example"
        test_dir.mkdir(parents=True)

        (test_dir / "AppTest.java").write_text("// test class")
        (test_dir / "UtilsTest.java").write_text("// test class")

        # Create non-test Java files
        main_dir = tmp_path / "src" / "main" / "java" / "com" / "example"
        main_dir.mkdir(parents=True)
        (main_dir / "App.java").write_text("// main class")

        # Create pom.xml
        (tmp_path / "pom.xml").write_text("<project></project>")

        return tmp_path

    def test_detects_src_test_java_directory(self, java_repo_structure: Path):
        """Test detection of files in src/test/java/ directory (FR-004)."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(java_repo_structure), "java")

        # Should detect AppTest.java and UtilsTest.java
        assert result.static_infrastructure.test_files_detected == 2, "Should detect files in src/test/java/ directory"

    def test_counts_java_files_in_test_directory(self, java_repo_structure: Path):
        """Test that .java files in test directory are counted."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(java_repo_structure), "java")

        assert result.static_infrastructure.test_files_detected == 2, "Should count .java files in test dir"

    def test_ignores_main_java_files(self, java_repo_structure: Path):
        """Test that files in src/main/java/ are not counted as tests."""
        from src.metrics.test_infrastructure_analyzer import TestInfrastructureAnalyzer

        analyzer = TestInfrastructureAnalyzer()
        result = analyzer.analyze(str(java_repo_structure), "java")

        # Should not count App.java from src/main/java/
        assert result.static_infrastructure.test_files_detected == 2, "Should only count test files, not main files"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
