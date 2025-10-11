"""Toolchain validation orchestrator.

This module provides the ToolchainManager class that coordinates
validation of all required tools for a programming language.
"""

from datetime import datetime

from .error_handling import ToolchainValidationError
from .models.validation_report import ValidationReport
from .models.validation_result import ValidationResult
from .tool_detector import ToolDetector
from .tool_registry import get_tools_for_language
from .toolchain_messages import ValidationMessages


class ToolchainManager:
    """High-level orchestrator for toolchain validation.

    This class coordinates the validation of all required CLI tools for a
    given programming language. It loads tool requirements from the registry,
    checks each tool using ToolDetector, and generates a comprehensive
    validation report.

    Usage:
        manager = ToolchainManager()
        try:
            report = manager.validate_for_language("python")
            print(f"✓ Validation passed: {len(report.checked_tools)} tools checked")
        except ToolchainValidationError as e:
            print(e.message, file=sys.stderr)
            sys.exit(1)
    """

    def __init__(self):
        """Initialize ToolchainManager with a ToolDetector instance."""
        self.detector = ToolDetector()

    def validate_for_language(self, language: str) -> ValidationReport:
        """Validate all required tools for a specific language.

        This is the main entry point for toolchain validation. It:
        1. Loads tool requirements from the registry (global + language-specific)
        2. For each tool, checks availability, version, and permissions
        3. Collects all ValidationResult instances
        4. Groups errors by category (FR-017)
        5. Creates and returns a ValidationReport
        6. Raises ToolchainValidationError if any tool fails validation

        Args:
            language: Programming language name (e.g., "python", "javascript")

        Returns:
            ValidationReport with passed=True and empty errors_by_category

        Raises:
            ToolchainValidationError: If any tool fails validation (missing, outdated, permission error)
            ValueError: If language is not supported

        Examples:
            >>> manager = ToolchainManager()
            >>> report = manager.validate_for_language("python")  # doctest: +SKIP
            >>> report.passed
            True
            >>> len(report.checked_tools) > 0
            True
        """
        # Load tool requirements for the language (includes global tools)
        tool_requirements = get_tools_for_language(language)

        # Collect validation results for all tools
        results: list[ValidationResult] = []
        for tool_req in tool_requirements:
            result = self._validate_single_tool(tool_req)
            results.append(result)

        # Group errors by category (FR-017)
        errors_by_category: dict[str, list[ValidationResult]] = {}
        for result in results:
            if not result.is_valid():
                category = result.error_category or "other"
                if category not in errors_by_category:
                    errors_by_category[category] = []
                errors_by_category[category].append(result)

        # Determine overall validation status
        passed = len(errors_by_category) == 0

        # Create validation report
        report = ValidationReport(
            passed=passed,
            language=language,
            checked_tools=[tool_req.name for tool_req in tool_requirements],
            errors_by_category=errors_by_category,
            timestamp=datetime.utcnow()
        )

        # Raise exception if validation failed (FR-003: immediate failure)
        if not passed:
            raise ToolchainValidationError(report)

        return report

    def _validate_single_tool(self, tool_req) -> ValidationResult:
        """Validate a single tool against its requirements.

        This method performs the complete validation workflow for one tool:
        1. Check if tool is in PATH (shutil.which)
        2. If found, check execute permissions
        3. If found, get version and compare to minimum requirement
        4. Create ValidationResult with appropriate error_category

        Args:
            tool_req: ToolRequirement instance

        Returns:
            ValidationResult with validation outcome
        """

        # Check tool availability (step 1: PATH detection)
        tool_path = self.detector.check_availability(tool_req.name)

        if tool_path is None:
            # Tool not found in PATH (error category: missing)
            error_message = ValidationMessages.format_missing(
                tool_name=tool_req.name,
                doc_url=tool_req.doc_url
            )
            return ValidationResult(
                tool_name=tool_req.name,
                found=False,
                error_category="missing",
                error_details=error_message
            )

        # Tool found - check permissions (step 2)
        has_execute, permissions = self.detector.check_permissions(tool_path)
        if not has_execute:
            # Tool exists but not executable (error category: permission)
            error_message = ValidationMessages.format_permission(
                tool_name=tool_req.name,
                path=tool_path,
                permissions=permissions
            )
            return ValidationResult(
                tool_name=tool_req.name,
                found=True,
                path=tool_path,
                permissions=permissions,
                version_ok=False,
                error_category="permission",
                error_details=error_message
            )

        # Tool found and executable - check version (step 3)
        version = None
        version_ok = True  # Default: assume OK if no version requirement

        if tool_req.min_version is not None:
            # Get version from tool
            version = self.detector.get_version(tool_path, tool_req.version_command)

            if version is None:
                # Version detection failed (error category: other)
                error_message = f"无法获取 {tool_req.name} 版本信息。请确认工具安装正确（参考 {tool_req.doc_url}）"
                return ValidationResult(
                    tool_name=tool_req.name,
                    found=True,
                    path=tool_path,
                    version=None,
                    version_ok=False,
                    error_category="other",
                    error_details=error_message
                )

            # Compare versions
            version_ok = self.detector.compare_versions(version, tool_req.min_version)

            if not version_ok:
                # Version too old (error category: outdated)
                error_message = ValidationMessages.format_outdated(
                    tool_name=tool_req.name,
                    current=version,
                    minimum=tool_req.min_version,
                    doc_url=tool_req.doc_url
                )
                return ValidationResult(
                    tool_name=tool_req.name,
                    found=True,
                    path=tool_path,
                    version=version,
                    version_ok=False,
                    error_category="outdated",
                    error_details=error_message
                )

        # All checks passed - tool is valid
        return ValidationResult(
            tool_name=tool_req.name,
            found=True,
            path=tool_path,
            version=version,
            version_ok=True,
            error_category=None,
            error_details=None
        )
