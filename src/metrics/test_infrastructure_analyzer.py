"""Static test infrastructure analyzer for code quality evaluation.

This module implements static analysis of test infrastructure across multiple
programming languages without executing any code. It detects test files,
configuration files, and calculates scoring based on FR-001 through FR-013.

Constitutional Compliance:
- Principle II (KISS): Simple file globbing, no AST parsing
- Principle III (Transparency): Clear logging and method documentation
"""

import logging
from pathlib import Path

from src.metrics.config_parsers import json_parser, makefile_parser, toml_parser, xml_parser
from src.metrics.models.test_infrastructure import TestInfrastructureResult

logger = logging.getLogger(__name__)


class TestInfrastructureAnalyzer:
    """Analyzer for static test infrastructure detection.

    This class implements pattern-based detection of test files and
    configuration files across Python, JavaScript, Go, and Java repositories.
    """

    def __init__(self) -> None:
        """Initialize the analyzer."""
        self.test_patterns = {
            "python": {
                "directories": ["tests"],
                "file_patterns": ["test_*.py", "*_test.py"],
            },
            "javascript": {
                "directories": ["__tests__"],
                "file_patterns": ["*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"],
            },
            "go": {"directories": [], "file_patterns": ["*_test.go"]},
            "java": {"directories": ["src/test/java"], "file_patterns": ["*.java"]},
        }

    def analyze(self, repo_path: str, language: str | list[str]) -> TestInfrastructureResult:
        """Analyze test infrastructure for a repository.

        Supports both single-language and multi-language analysis:
        - Single language: Analyze for that language only
        - Multiple languages: Analyze each independently, return result with highest score

        Args:
            repo_path: Absolute path to repository root
            language: Primary language or list of languages (python, javascript, go, java)

        Returns:
            TestInfrastructureResult with detected infrastructure and calculated score

        Example:
            >>> analyzer = TestInfrastructureAnalyzer()
            >>> # Single language
            >>> result = analyzer.analyze("/path/to/repo", "python")
            >>> result.calculated_score
            20
            >>> # Multi-language (returns max score)
            >>> result = analyzer.analyze("/path/to/repo", ["python", "javascript"])
            >>> result.calculated_score
            25
        """
        # Handle multi-language case (FR-004a, Clarification 2)
        if isinstance(language, list):
            return self._analyze_multi_language(repo_path, language)

        # Single language analysis
        return self._analyze_single_language(repo_path, language)

    def _analyze_single_language(self, repo_path: str, language: str) -> TestInfrastructureResult:
        """Analyze test infrastructure for a single language.

        Args:
            repo_path: Absolute path to repository root
            language: Programming language (python, javascript, go, java)

        Returns:
            TestInfrastructureResult with detected infrastructure and calculated score
        """
        repo = Path(repo_path)
        logger.info(f"Analyzing test infrastructure for {language} repo at {repo_path}")

        # Detect test files (FR-001 through FR-004)
        test_files = self._detect_test_files(repo, language)
        test_files_detected = len(test_files)
        logger.info(f"Detected {test_files_detected} test files")

        # Detect test configuration (FR-005)
        test_config_detected = self._detect_test_config(repo, language)
        logger.info(f"Test config detected: {test_config_detected}")

        # Detect coverage configuration (FR-006)
        coverage_config_detected = self._detect_coverage_config(repo, language)
        logger.info(f"Coverage config detected: {coverage_config_detected}")

        # Calculate test file ratio (FR-010)
        test_file_ratio = self._calculate_test_ratio(repo, language, test_files_detected)
        logger.info(f"Test file ratio: {test_file_ratio:.2%}")

        # Infer framework
        inferred_framework = self._infer_framework(language, test_config_detected)

        # Calculate score (FR-007 through FR-013)
        calculated_score = self._calculate_score(
            test_files_detected, test_config_detected, coverage_config_detected, test_file_ratio
        )
        logger.info(f"Calculated score: {calculated_score}/25")

        return TestInfrastructureResult(
            test_files_detected=test_files_detected,
            test_config_detected=test_config_detected,
            coverage_config_detected=coverage_config_detected,
            test_file_ratio=test_file_ratio,
            calculated_score=calculated_score,
            inferred_framework=inferred_framework,
        )

    def _analyze_multi_language(
        self, repo_path: str, languages: list[str]
    ) -> TestInfrastructureResult:
        """Analyze test infrastructure for multiple languages, return max score.

        Strategy (per FR-004a and Clarification 2):
        1. Run detection independently for each language
        2. Return the result with the highest calculated_score
        3. This ensures multi-language repos get fair scoring

        Args:
            repo_path: Absolute path to repository root
            languages: List of programming languages to analyze

        Returns:
            TestInfrastructureResult with highest score among all languages
        """
        logger.info(
            f"Multi-language analysis for {len(languages)} languages: {', '.join(languages)}"
        )

        results = []
        for lang in languages:
            logger.info(f"Analyzing {lang}...")
            result = self._analyze_single_language(repo_path, lang)
            results.append((lang, result))
            logger.info(f"{lang} score: {result.calculated_score}/25")

        # Return result with highest score (max score strategy)
        best_lang, best_result = max(results, key=lambda x: x[1].calculated_score)
        logger.info(
            f"Multi-language analysis complete. Best: {best_lang} "
            f"with {best_result.calculated_score}/25"
        )

        return best_result

    def _detect_test_files(self, repo: Path, language: str) -> list[Path]:
        """Detect test files using language-specific patterns (FR-001 through FR-004).

        Args:
            repo: Repository root path
            language: Programming language

        Returns:
            List of detected test file paths
        """
        if language == "python":
            return self._detect_python_tests(repo)
        elif language == "javascript":
            return self._detect_javascript_tests(repo)
        elif language == "go":
            return self._detect_go_tests(repo)
        elif language == "java":
            return self._detect_java_tests(repo)
        else:
            logger.warning(f"Unknown language: {language}")
            return []

    def _detect_python_tests(self, repo: Path) -> list[Path]:
        """Detect Python test files (FR-001).

        Patterns:
        - tests/ directory
        - test_*.py files
        - *_test.py files

        Args:
            repo: Repository root path

        Returns:
            List of detected Python test files
        """
        test_files = []

        # Pattern 1: tests/ directory
        tests_dir = repo / "tests"
        if tests_dir.exists() and tests_dir.is_dir():
            test_files.extend(tests_dir.rglob("*.py"))

        # Pattern 2: test_*.py anywhere
        test_files.extend(repo.rglob("test_*.py"))

        # Pattern 3: *_test.py anywhere
        test_files.extend(repo.rglob("*_test.py"))

        # Remove duplicates
        return list(set(test_files))

    def _detect_javascript_tests(self, repo: Path) -> list[Path]:
        """Detect JavaScript/TypeScript test files (FR-002).

        Patterns:
        - __tests__/ directory
        - *.test.js, *.spec.js files
        - *.test.ts, *.spec.ts files (TypeScript)

        Args:
            repo: Repository root path

        Returns:
            List of detected JavaScript/TypeScript test files
        """
        test_files = []

        # Pattern 1: __tests__/ directory
        tests_dir = repo / "__tests__"
        if tests_dir.exists() and tests_dir.is_dir():
            test_files.extend(tests_dir.rglob("*.js"))
            test_files.extend(tests_dir.rglob("*.ts"))

        # Pattern 2: *.test.js, *.spec.js
        test_files.extend(repo.rglob("*.test.js"))
        test_files.extend(repo.rglob("*.spec.js"))

        # Pattern 3: TypeScript variants
        test_files.extend(repo.rglob("*.test.ts"))
        test_files.extend(repo.rglob("*.spec.ts"))

        # Remove duplicates
        return list(set(test_files))

    def _detect_go_tests(self, repo: Path) -> list[Path]:
        """Detect Go test files (FR-003).

        Pattern:
        - *_test.go files

        Args:
            repo: Repository root path

        Returns:
            List of detected Go test files
        """
        # Pattern: *_test.go anywhere
        return list(repo.rglob("*_test.go"))

    def _detect_java_tests(self, repo: Path) -> list[Path]:
        """Detect Java test files (FR-004).

        Pattern:
        - src/test/java/ directory

        Args:
            repo: Repository root path

        Returns:
            List of detected Java test files
        """
        test_files = []

        # Pattern: src/test/java/ directory
        test_dir = repo / "src" / "test" / "java"
        if test_dir.exists() and test_dir.is_dir():
            test_files.extend(test_dir.rglob("*.java"))

        return test_files

    def _detect_test_config(self, repo: Path, language: str) -> bool:
        """Detect test framework configuration (FR-005).

        Args:
            repo: Repository root path
            language: Programming language

        Returns:
            True if valid test configuration detected, False otherwise
        """
        if language == "python":
            # Check pytest.ini, pyproject.toml, tox.ini
            config_files = [
                repo / "pytest.ini",
                repo / "pyproject.toml",
                repo / "tox.ini",
            ]
            for config_file in config_files:
                if config_file.exists():
                    verified, _ = toml_parser.verify_pytest_section(config_file)
                    if verified:
                        return True

        elif language == "javascript":
            # Check package.json, jest.config.js
            config_files = [repo / "package.json", repo / "jest.config.js"]
            for config_file in config_files:
                if config_file.exists():
                    verified, _ = json_parser.verify_test_script(config_file)
                    if verified:
                        return True

        elif language == "go":
            # go.mod presence combined with test files indicates test setup
            if (repo / "go.mod").exists():
                return True

        elif language == "java":
            # Check pom.xml, build.gradle
            config_files = [repo / "pom.xml", repo / "build.gradle"]
            for config_file in config_files:
                if config_file.exists():
                    verified, _ = xml_parser.verify_surefire_plugin(config_file)
                    if verified:
                        return True

        return False

    def _detect_coverage_config(self, repo: Path, language: str) -> bool:
        """Detect coverage configuration (FR-006).

        Args:
            repo: Repository root path
            language: Programming language

        Returns:
            True if valid coverage configuration detected, False otherwise
        """
        if language == "python":
            # Check .coveragerc, pyproject.toml
            config_files = [repo / ".coveragerc", repo / "pyproject.toml"]
            for config_file in config_files:
                if config_file.exists():
                    verified, _ = toml_parser.verify_coverage_section(config_file)
                    if verified:
                        return True

        elif language == "javascript":
            # Check jest.config.json
            config_file = repo / "jest.config.json"
            if config_file.exists():
                verified, _ = json_parser.verify_coverage_threshold(config_file)
                if verified:
                    return True

        elif language == "go":
            # Check Makefile for coverage flags
            makefile = repo / "Makefile"
            if makefile.exists():
                verified, _ = makefile_parser.verify_coverage_flags(makefile)
                if verified:
                    return True

        elif language == "java":
            # Check pom.xml, build.gradle for jacoco
            config_files = [repo / "pom.xml", repo / "build.gradle"]
            for config_file in config_files:
                if config_file.exists():
                    verified, _ = xml_parser.verify_jacoco_plugin(config_file)
                    if verified:
                        return True

        return False

    def _calculate_test_ratio(self, repo: Path, language: str, test_count: int) -> float:
        """Calculate test file ratio (FR-010).

        Formula: test_count / (source_count - test_count - docs - configs)

        Args:
            repo: Repository root path
            language: Programming language
            test_count: Number of test files detected

        Returns:
            Test file ratio (0.0 to 1.0)
        """
        if test_count == 0:
            return 0.0

        # Count source files for the language
        extensions = {
            "python": [".py"],
            "javascript": [".js", ".ts", ".jsx", ".tsx"],
            "go": [".go"],
            "java": [".java"],
        }

        lang_extensions = extensions.get(language, [])
        all_source_files = []
        for ext in lang_extensions:
            all_source_files.extend(repo.rglob(f"*{ext}"))

        # Exclude docs, configs, and other non-source files
        exclude_patterns = [
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".xml",
            ".ini",
            ".cfg",
        ]

        source_files = [
            f
            for f in all_source_files
            if not any(f.name.endswith(pattern) for pattern in exclude_patterns)
        ]

        source_count = len(source_files)

        # Calculate ratio (test files / non-test source files)
        # Denominator: source_count - test_count (exclude test files)
        denominator = source_count - test_count
        if denominator <= 0:
            return 0.0

        ratio = test_count / denominator
        return min(ratio, 1.0)  # Cap at 1.0

    def _calculate_score(
        self,
        test_files_detected: int,
        test_config_detected: bool,
        coverage_config_detected: bool,
        test_file_ratio: float,
    ) -> int:
        """Calculate static analysis score (FR-007 through FR-013).

        Scoring breakdown:
        - 5 points: test files present (FR-007)
        - 5 points: test config detected (FR-008)
        - 5 points: coverage config detected (FR-009)
        - 5 points: test ratio 10-30% (FR-012)
        - 10 points: test ratio >30% (FR-011)
        Max: 25 points (FR-013)

        Args:
            test_files_detected: Number of test files found
            test_config_detected: Whether test config found
            coverage_config_detected: Whether coverage config found
            test_file_ratio: Test file ratio

        Returns:
            Calculated score (0-25)
        """
        score = 0

        # FR-007: 5 points for test files present
        if test_files_detected > 0:
            score += 5

        # FR-008: 5 points for test config
        if test_config_detected:
            score += 5

        # FR-009: 5 points for coverage config
        if coverage_config_detected:
            score += 5

        # FR-011 and FR-012: Ratio-based bonus points
        if test_file_ratio > 0.30:  # >30%
            score += 10  # FR-011
        elif test_file_ratio >= 0.10:  # 10-30%
            score += 5  # FR-012

        # FR-013: Cap at 25 points
        return min(score, 25)

    def _infer_framework(self, language: str, test_config_detected: bool) -> str:
        """Infer test framework from language and config.

        Args:
            language: Programming language
            test_config_detected: Whether test config was found

        Returns:
            Framework name (e.g., "pytest", "jest", "go test", "junit", "none")
        """
        if not test_config_detected:
            return "none"

        framework_map = {
            "python": "pytest",
            "javascript": "jest",
            "go": "go test",
            "java": "junit",
        }

        return framework_map.get(language, "none")
