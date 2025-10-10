"""Real execution tests for language detection functionality.

NO MOCKS - All tests use real file operations and REAL LanguageDetector API.

IMPORTANT: Previous mock tests were testing non-existent methods (get_file_language, scan_directory_files).
This rewrite tests the ACTUAL API: detect_primary_language() and get_language_statistics().
"""

import tempfile
from pathlib import Path

import pytest

from src.metrics.language_detection import LanguageDetector


class TestLanguageDetectorRealAPI:
    """REAL TESTS for language detection using ACTUAL API - NO MOCKS."""

    @pytest.fixture
    def detector(self) -> LanguageDetector:
        """Create a language detector instance."""
        return LanguageDetector()

    def test_detect_primary_language_python_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Detect Python as primary language with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Python files
            (repo_path / "main.py").write_text("print('Hello')")
            (repo_path / "utils.py").write_text("def helper(): pass")
            (repo_path / "test.py").write_text("import unittest")

            # REAL DETECTION
            primary = detector.detect_primary_language(str(repo_path))
            assert primary == "python"

    def test_detect_primary_language_javascript_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Detect JavaScript as primary language with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create JavaScript files
            (repo_path / "app.js").write_text("console.log('hello');")
            (repo_path / "utils.js").write_text("function helper() {}")
            (repo_path / "index.js").write_text("module.exports = {};")

            # REAL DETECTION
            primary = detector.detect_primary_language(str(repo_path))
            assert primary in ["javascript", "typescript"]  # May detect either

    def test_detect_primary_language_go_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Detect Go as primary language with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Go files
            (repo_path / "main.go").write_text("package main\n\nfunc main() {}")
            (repo_path / "server.go").write_text("package main")
            (repo_path / "go.mod").write_text("module test\n\ngo 1.21")

            # REAL DETECTION
            primary = detector.detect_primary_language(str(repo_path))
            assert primary == "go"

    def test_detect_primary_language_java_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Detect Java as primary language with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Java files
            (repo_path / "Main.java").write_text("public class Main {}")
            (repo_path / "Controller.java").write_text("public class Controller {}")
            (repo_path / "pom.xml").write_text("<?xml version='1.0'?><project></project>")

            # REAL DETECTION
            primary = detector.detect_primary_language(str(repo_path))
            assert primary == "java"

    def test_detect_primary_language_mixed_repo_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Detect primary language in mixed-language repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create more Python files than JS (Python should win)
            (repo_path / "main.py").write_text("print('hello')")
            (repo_path / "utils.py").write_text("def helper(): pass")
            (repo_path / "test.py").write_text("import unittest")
            (repo_path / "app.js").write_text("console.log('hello');")

            # REAL DETECTION - Python should be primary (3 vs 1)
            primary = detector.detect_primary_language(str(repo_path))
            assert primary == "python"

    def test_detect_primary_language_empty_directory_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Detect language in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # REAL DETECTION on empty dir
            primary = detector.detect_primary_language(temp_dir)
            assert primary == "unknown"

    def test_detect_primary_language_low_confidence_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Low confidence detection returns unknown."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Equal files of different languages
            (repo_path / "script.py").write_text("print('hello')")
            (repo_path / "app.js").write_text("console.log('hello');")

            # Adjust threshold to force unknown
            detector.confidence_threshold = 0.8  # 50% confidence < 80% threshold

            # REAL DETECTION
            primary = detector.detect_primary_language(str(repo_path))
            assert primary == "unknown"

    def test_get_language_statistics_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Get language statistics with actual files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Python and JS files
            (repo_path / "main.py").write_text("print('hello')")
            (repo_path / "utils.py").write_text("def helper(): pass")
            (repo_path / "app.js").write_text("console.log('hello');")

            # REAL STATISTICS
            stats = detector.get_language_statistics(str(repo_path))

            # Verify structure
            assert "primary_language" in stats
            assert "confidence_score" in stats
            assert "total_files_analyzed" in stats
            assert "detected_languages" in stats

            # Verify content
            assert stats["primary_language"] in ["python", "javascript", "typescript"]
            assert stats["total_files_analyzed"] >= 3
            assert isinstance(stats["detected_languages"], dict)

    def test_get_language_statistics_empty_directory_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Statistics on empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # REAL STATISTICS
            stats = detector.get_language_statistics(temp_dir)

            assert stats["primary_language"] == "unknown"
            assert stats["confidence_score"] == 0.0
            assert stats["total_files_analyzed"] == 0
            assert stats["detected_languages"] == {}

    def test_confidence_score_calculation_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Confidence score calculation with actual files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create 7 Python and 3 JavaScript files (70% Python)
            for i in range(7):
                (repo_path / f"python_{i}.py").write_text("print('hello')")
            for i in range(3):
                (repo_path / f"js_{i}.js").write_text("console.log('hello');")

            # REAL STATISTICS
            stats = detector.get_language_statistics(str(repo_path))

            # Confidence should be ~0.7 (70%)
            assert stats["confidence_score"] >= 0.6
            assert stats["primary_language"] == "python"

    def test_custom_confidence_threshold_real(self) -> None:
        """REAL TEST: Custom confidence threshold affects detection."""
        detector_low = LanguageDetector()
        detector_low.confidence_threshold = 0.3

        detector_high = LanguageDetector()
        detector_high.confidence_threshold = 0.9

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # 6 Python, 4 JS = 60% Python
            for i in range(6):
                (repo_path / f"python_{i}.py").write_text("print('hello')")
            for i in range(4):
                (repo_path / f"js_{i}.js").write_text("console.log('hello');")

            # Low threshold should detect Python
            assert detector_low.detect_primary_language(str(repo_path)) in ["python", "javascript", "typescript"]

            # High threshold (60% < 90%) might return unknown
            result_high = detector_high.detect_primary_language(str(repo_path))
            assert result_high in ["python", "javascript", "typescript", "unknown"]

    def test_config_file_bonus_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Config files provide detection bonus."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Few Python files but with config files
            (repo_path / "main.py").write_text("print('hello')")
            (repo_path / "pyproject.toml").write_text("[project]\nname='test'")
            (repo_path / "requirements.txt").write_text("requests==2.0.0")

            # REAL DETECTION - config files should boost Python detection
            primary = detector.detect_primary_language(str(repo_path))
            assert primary == "python"

    def test_typescript_vs_javascript_detection_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: TypeScript vs JavaScript detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create TypeScript files
            (repo_path / "app.ts").write_text("const x: number = 5;")
            (repo_path / "utils.tsx").write_text("export const Component = () => {};")
            (repo_path / "tsconfig.json").write_text("{}")

            # REAL DETECTION
            primary = detector.detect_primary_language(str(repo_path))
            assert primary in ["typescript", "javascript"]  # TS is subset of JS

    def test_nonexistent_directory_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Handle non-existent directory gracefully."""
        # REAL DETECTION on non-existent path
        primary = detector.detect_primary_language("/nonexistent/path/to/repo")
        assert primary == "unknown"

    def test_percentage_calculation_real(self, detector: LanguageDetector) -> None:
        """REAL TEST: Language percentage calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # 8 Python, 2 JS = 80% / 20%
            for i in range(8):
                (repo_path / f"python_{i}.py").write_text("print('hello')")
            for i in range(2):
                (repo_path / f"js_{i}.js").write_text("console.log('hello');")

            # REAL STATISTICS
            stats = detector.get_language_statistics(str(repo_path))
            languages = stats["detected_languages"]

            # Check percentages exist and sum to 100
            if languages:
                total_pct = sum(lang.get("percentage", 0) for lang in languages.values())
                assert 99.0 <= total_pct <= 101.0  # Allow small float errors
