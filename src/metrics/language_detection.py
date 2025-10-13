"""Language detection for Git repositories using file extension analysis."""

import os
from collections import defaultdict
from pathlib import Path


class LanguageDetector:
    """Detects primary programming language using GitHub Linguist patterns."""

    def __init__(self) -> None:
        """Initialize language detector with file extension mappings."""
        self.language_extensions = {
            "python": [".py", ".pyw", ".pyi"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx", ".cts", ".mts"],
            "java": [".java"],
            "go": [".go"],
        }

        self.config_files = {
            "python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile"],
            "javascript": [
                "package.json",
                "package-lock.json",
                ".eslintrc.js",
                "webpack.config.js",
            ],
            "typescript": ["tsconfig.json", "tslint.json"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "go": ["go.mod", "go.sum"],
        }

        self.detection_strategy = "file_extension_analysis"
        self.confidence_threshold = 0.6

    def detect_primary_language(self, repository_path: str) -> str:
        """Detect the primary programming language of a repository."""
        try:
            language_stats = self.get_language_statistics(repository_path)

            if not language_stats["detected_languages"]:
                return "unknown"

            primary_language = language_stats["primary_language"]
            confidence = language_stats["confidence_score"]

            if confidence < self.confidence_threshold:
                return "unknown"

            return primary_language

        except Exception:
            # Fail gracefully - return unknown if detection fails
            return "unknown"

    def get_language_statistics(self, repository_path: str) -> dict:
        """Get detailed language statistics for a repository."""
        language_counts = defaultdict(int)
        total_files = 0

        # Analyze file extensions
        for _root, dirs, files in os.walk(repository_path):
            # Skip common non-source directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["node_modules", "__pycache__", "target", "build"]
            ]

            for file in files:
                if file.startswith("."):
                    continue

                file_path = Path(file)
                extension = file_path.suffix.lower()

                # Count files by language
                for language, extensions in self.language_extensions.items():
                    if extension in extensions:
                        language_counts[language] += 1
                        total_files += 1
                        break

        # Boost confidence based on config files
        config_bonuses = self._calculate_config_bonuses(repository_path)

        # Calculate percentages and confidence
        detected_languages = {}
        for language, count in language_counts.items():
            percentage = (count / total_files * 100) if total_files > 0 else 0
            detected_languages[language] = {"file_count": count, "percentage": percentage}

        # Determine primary language
        primary_language = "unknown"
        confidence_score = 0.0

        if detected_languages:
            # Find language with highest file count
            primary_language = max(
                detected_languages.keys(), key=lambda lang: detected_languages[lang]["file_count"]
            )

            # Calculate confidence score
            primary_count = detected_languages[primary_language]["file_count"]
            base_confidence = primary_count / total_files if total_files > 0 else 0

            # Apply config file bonus
            config_bonus = config_bonuses.get(primary_language, 0)
            confidence_score = min(1.0, base_confidence + config_bonus)

        return {
            "detected_languages": detected_languages,
            "primary_language": primary_language,
            "confidence_score": confidence_score,
            "total_files_analyzed": total_files,
        }

    def get_languages_above_threshold(
        self, repository_path: str, threshold: float = 0.20
    ) -> dict[str, float]:
        """Get all languages with file count percentage above threshold.

        This method is used for multi-language repository analysis where multiple
        languages may coexist. Languages below the threshold are filtered out to
        avoid false positives from minor dependencies.

        Args:
            repository_path: Path to repository root
            threshold: Minimum percentage (0.0-1.0) for language to be included
                      Default is 0.20 (20%) per FR-004a

        Returns:
            Dictionary mapping language names to their percentages (0.0-1.0)
            Example: {"python": 0.65, "javascript": 0.25}

        Example:
            >>> detector = LanguageDetector()
            >>> languages = detector.get_languages_above_threshold("/path/to/repo")
            >>> languages
            {"python": 0.65, "javascript": 0.25}
        """
        stats = self.get_language_statistics(repository_path)
        detected = stats["detected_languages"]

        # Filter languages above threshold and convert percentage to 0.0-1.0 range
        return {
            lang: info["percentage"] / 100.0
            for lang, info in detected.items()
            if info["percentage"] >= (threshold * 100)
        }

    def _calculate_config_bonuses(self, repository_path: str) -> dict[str, float]:
        """Calculate confidence bonuses based on config files."""
        bonuses = {}
        repo_path = Path(repository_path)

        for language, config_files in self.config_files.items():
            bonus = 0.0
            for config_file in config_files:
                if (repo_path / config_file).exists():
                    bonus += 0.1  # 10% bonus per config file

            bonuses[language] = min(0.3, bonus)  # Cap at 30% bonus

        return bonuses
