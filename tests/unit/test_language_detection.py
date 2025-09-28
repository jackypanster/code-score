"""Unit tests for language detection functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.metrics.language_detection import LanguageDetector


class TestLanguageDetector:
    """Test language detection logic."""

    @pytest.fixture
    def detector(self) -> LanguageDetector:
        """Create a language detector instance."""
        return LanguageDetector(confidence_threshold=0.6)

    @pytest.fixture
    def temp_repo(self) -> Path:
        """Create a temporary repository with various files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Python files
            (repo_path / "main.py").write_text("print('Hello, World!')")
            (repo_path / "utils.py").write_text("def helper(): pass")
            (repo_path / "tests" / "test_main.py").write_text("import unittest")

            # Create JavaScript files
            (repo_path / "index.js").write_text("console.log('Hello');")

            # Create other files
            (repo_path / "README.md").write_text("# Project")
            (repo_path / "requirements.txt").write_text("requests==2.28.0")

            # Ensure directories exist
            (repo_path / "tests").mkdir(exist_ok=True)

            yield repo_path

    def test_get_file_language_python(self, detector: LanguageDetector) -> None:
        """Test Python file detection."""
        assert detector.get_file_language("script.py") == "python"
        assert detector.get_file_language("test_module.py") == "python"
        assert detector.get_file_language("__init__.py") == "python"

    def test_get_file_language_javascript(self, detector: LanguageDetector) -> None:
        """Test JavaScript/TypeScript file detection."""
        assert detector.get_file_language("app.js") == "javascript"
        assert detector.get_file_language("component.jsx") == "javascript"
        assert detector.get_file_language("types.ts") == "javascript"
        assert detector.get_file_language("component.tsx") == "javascript"

    def test_get_file_language_java(self, detector: LanguageDetector) -> None:
        """Test Java file detection."""
        assert detector.get_file_language("Main.java") == "java"
        assert detector.get_file_language("Controller.java") == "java"

    def test_get_file_language_go(self, detector: LanguageDetector) -> None:
        """Test Go file detection."""
        assert detector.get_file_language("main.go") == "go"
        assert detector.get_file_language("server.go") == "go"

    def test_get_file_language_unknown(self, detector: LanguageDetector) -> None:
        """Test unknown file type detection."""
        assert detector.get_file_language("README.md") == "unknown"
        assert detector.get_file_language("config.xml") == "unknown"
        assert detector.get_file_language("data.json") == "unknown"
        assert detector.get_file_language("no_extension") == "unknown"

    def test_scan_directory_files(self, detector: LanguageDetector, temp_repo: Path) -> None:
        """Test directory scanning for code files."""
        files = detector.scan_directory_files(str(temp_repo))

        # Should find all code files
        assert len(files) >= 4  # At least main.py, utils.py, test_main.py, index.js

        # Check specific files are found
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "index.js" in file_names

        # Should not include non-code files
        assert "README.md" not in file_names
        assert "requirements.txt" not in file_names

    def test_get_language_statistics(self, detector: LanguageDetector, temp_repo: Path) -> None:
        """Test language statistics calculation."""
        stats = detector.get_language_statistics(str(temp_repo))

        # Verify structure
        assert "primary_language" in stats
        assert "confidence_score" in stats
        assert "total_files_analyzed" in stats
        assert "detected_languages" in stats

        # Should detect Python as primary (3 files vs 1 JS)
        assert stats["primary_language"] == "python"
        assert stats["confidence_score"] > 0.6
        assert stats["total_files_analyzed"] >= 4

        # Check language breakdown
        languages = stats["detected_languages"]
        assert "python" in languages
        assert "javascript" in languages
        assert languages["python"]["file_count"] == 3
        assert languages["javascript"]["file_count"] == 1

    def test_detect_primary_language_confident(self, detector: LanguageDetector, temp_repo: Path) -> None:
        """Test primary language detection with high confidence."""
        primary = detector.detect_primary_language(str(temp_repo))
        assert primary == "python"

    def test_detect_primary_language_low_confidence(self, detector: LanguageDetector) -> None:
        """Test primary language detection with low confidence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create equal number of different language files
            (repo_path / "script.py").write_text("print('hello')")
            (repo_path / "app.js").write_text("console.log('hello')")

            # Low confidence should return "unknown"
            detector_strict = LanguageDetector(confidence_threshold=0.8)
            primary = detector_strict.detect_primary_language(str(repo_path))
            assert primary == "unknown"

    def test_detect_primary_language_empty_directory(self, detector: LanguageDetector) -> None:
        """Test primary language detection on empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            primary = detector.detect_primary_language(temp_dir)
            assert primary == "unknown"

    def test_get_language_statistics_empty_directory(self, detector: LanguageDetector) -> None:
        """Test language statistics on empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats = detector.get_language_statistics(temp_dir)

            assert stats["primary_language"] == "unknown"
            assert stats["confidence_score"] == 0.0
            assert stats["total_files_analyzed"] == 0
            assert stats["detected_languages"] == {}

    def test_scan_directory_files_nonexistent(self, detector: LanguageDetector) -> None:
        """Test scanning non-existent directory."""
        files = detector.scan_directory_files("/nonexistent/path")
        assert files == []

    def test_confidence_score_calculation(self, detector: LanguageDetector) -> None:
        """Test confidence score calculation logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create 7 Python files and 3 JavaScript files (70% Python)
            for i in range(7):
                (repo_path / f"python_{i}.py").write_text("print('hello')")
            for i in range(3):
                (repo_path / f"js_{i}.js").write_text("console.log('hello')")

            stats = detector.get_language_statistics(str(repo_path))

            # Should be exactly 0.7 confidence (70%)
            assert abs(stats["confidence_score"] - 0.7) < 0.01
            assert stats["primary_language"] == "python"

    def test_file_extensions_mapping(self, detector: LanguageDetector) -> None:
        """Test all supported file extensions are mapped correctly."""
        # Python extensions
        python_extensions = [".py", ".pyw", ".py3"]
        for ext in python_extensions:
            assert detector.get_file_language(f"test{ext}") == "python"

        # JavaScript/TypeScript extensions
        js_extensions = [".js", ".jsx", ".ts", ".tsx", ".mjs"]
        for ext in js_extensions:
            assert detector.get_file_language(f"test{ext}") == "javascript"

        # Java extensions
        assert detector.get_file_language("Test.java") == "java"

        # Go extensions
        assert detector.get_file_language("main.go") == "go"

    def test_custom_confidence_threshold(self) -> None:
        """Test custom confidence threshold setting."""
        detector_low = LanguageDetector(confidence_threshold=0.3)
        detector_high = LanguageDetector(confidence_threshold=0.9)

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create 6 Python and 4 JavaScript files (60% Python)
            for i in range(6):
                (repo_path / f"python_{i}.py").write_text("print('hello')")
            for i in range(4):
                (repo_path / f"js_{i}.js").write_text("console.log('hello')")

            # Low threshold should detect Python
            assert detector_low.detect_primary_language(str(repo_path)) == "python"

            # High threshold should return unknown (60% < 90%)
            assert detector_high.detect_primary_language(str(repo_path)) == "unknown"

    @patch('src.metrics.language_detection.Path.iterdir')
    def test_scan_directory_files_with_exception(self, mock_iterdir: MagicMock, detector: LanguageDetector) -> None:
        """Test handling of exceptions during directory scanning."""
        mock_iterdir.side_effect = PermissionError("Access denied")

        files = detector.scan_directory_files("/some/path")
        assert files == []

    def test_percentage_calculation_in_statistics(self, detector: LanguageDetector) -> None:
        """Test percentage calculation in language statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create 8 Python files and 2 JavaScript files
            for i in range(8):
                (repo_path / f"python_{i}.py").write_text("print('hello')")
            for i in range(2):
                (repo_path / f"js_{i}.js").write_text("console.log('hello')")

            stats = detector.get_language_statistics(str(repo_path))
            languages = stats["detected_languages"]

            # Check percentages
            assert languages["python"]["percentage"] == 80.0
            assert languages["javascript"]["percentage"] == 20.0

            # Verify percentages sum to 100
            total_percentage = sum(lang["percentage"] for lang in languages.values())
            assert abs(total_percentage - 100.0) < 0.01
