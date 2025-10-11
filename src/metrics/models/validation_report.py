"""Validation report dataclass for comprehensive toolchain validation results.

This module defines the ValidationReport dataclass that aggregates all tool
validation results and generates Chinese error messages per data-model.md and FR-013/FR-017.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .validation_result import ValidationResult


@dataclass
class ValidationReport:
    """Comprehensive report of toolchain validation results.

    This dataclass aggregates validation results for all tools in a language-specific
    toolchain and provides methods for error formatting and analysis.

    Attributes:
        passed: Overall validation status (True if all tools valid)
        language: Target language being validated (e.g., "python", "javascript")
        checked_tools: List of tool names that were validated
        errors_by_category: Dict mapping error categories to lists of failed ValidationResults
                          Categories: "missing", "outdated", "permission", "other"
        timestamp: When validation was performed (UTC)

    Error Categorization (FR-017):
        Errors are grouped by category for clear reporting:
        {
            "missing": [ValidationResult(tool_name="pytest", found=False, ...)],
            "outdated": [ValidationResult(tool_name="npm", version="7.5.0", ...)],
            "permission": [ValidationResult(tool_name="ruff", permissions="-rw-r--r--", ...)]
        }

    Examples:
        >>> # All tools pass
        >>> report = ValidationReport(
        ...     passed=True,
        ...     language="python",
        ...     checked_tools=["ruff", "pytest", "pip-audit"],
        ...     errors_by_category={},
        ...     timestamp=datetime.utcnow()
        ... )

        >>> # Multiple errors grouped
        >>> report = ValidationReport(
        ...     passed=False,
        ...     language="python",
        ...     checked_tools=["ruff", "pytest", "npm"],
        ...     errors_by_category={
        ...         "missing": [ValidationResult(tool_name="pytest", found=False, ...)],
        ...         "outdated": [ValidationResult(tool_name="npm", version="7.5.0", ...)],
        ...         "permission": [ValidationResult(tool_name="ruff", permissions="-rw-r--r--", ...)]
        ...     },
        ...     timestamp=datetime.utcnow()
        ... )
    """

    passed: bool
    language: str
    checked_tools: list[str]
    errors_by_category: dict[str, list[ValidationResult]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def format_error_message(self) -> str:
        """Generate Chinese error message grouped by category (FR-013, FR-017).

        This method creates a multi-line formatted error message with categorized
        errors. If validation passed, returns a success message.

        Returns:
            Multi-line string with categorized errors in Chinese:

            工具链验证失败，发现以下问题：

            【缺少工具】
            - 缺少工具 pytest。请在评分主机安装后重试（参考 https://docs.pytest.org）

            【版本过旧】
            - 工具 npm 版本过旧（当前: 7.5.0，最低要求: 8.0.0）。请升级后重试（参考 https://docs.npmjs.com）

            【权限不足】
            - 工具 ruff 位于 /usr/bin/ruff 但权限不足（当前: -rw-r--r--）。请修复权限后重试。

        Examples:
            >>> # Success message
            >>> report = ValidationReport(passed=True, language="python", checked_tools=["ruff"])
            >>> print(report.format_error_message())
            ✓ 工具链验证通过 (语言: python，检查工具: 1个)

            >>> # Error message with categorization
            >>> report = ValidationReport(
            ...     passed=False,
            ...     language="python",
            ...     checked_tools=["pytest", "ruff"],
            ...     errors_by_category={
            ...         "missing": [ValidationResult(
            ...             tool_name="pytest",
            ...             found=False,
            ...             error_category="missing",
            ...             error_details="缺少工具 pytest。请在评分主机安装后重试（参考 https://docs.pytest.org）"
            ...         )]
            ...     }
            ... )
            >>> print(report.format_error_message())
            工具链验证失败，发现以下问题：
            <BLANKLINE>
            【缺少工具】
            - 缺少工具 pytest。请在评分主机安装后重试（参考 https://docs.pytest.org）
        """
        from ..toolchain_messages import ValidationMessages

        # Success message
        if self.passed:
            return f"✓ 工具链验证通过 (语言: {self.language}，检查工具: {len(self.checked_tools)}个)"

        # Build error message with categorized sections
        lines = [ValidationMessages.VALIDATION_FAILED_HEADER]

        # Missing tools section (FR-017)
        if "missing" in self.errors_by_category:
            lines.append(ValidationMessages.CATEGORY_MISSING_HEADER)
            for result in self.errors_by_category["missing"]:
                lines.append(f"- {result.error_details}")

        # Outdated tools section (FR-017)
        if "outdated" in self.errors_by_category:
            lines.append(ValidationMessages.CATEGORY_OUTDATED_HEADER)
            for result in self.errors_by_category["outdated"]:
                lines.append(f"- {result.error_details}")

        # Permission errors section (FR-017)
        if "permission" in self.errors_by_category:
            lines.append(ValidationMessages.CATEGORY_PERMISSION_HEADER)
            for result in self.errors_by_category["permission"]:
                lines.append(f"- {result.error_details}")

        # Other errors section (FR-017)
        if "other" in self.errors_by_category:
            lines.append("\n【其他错误】")
            for result in self.errors_by_category["other"]:
                lines.append(f"- {result.tool_name}: {result.error_details}")

        return "\n".join(lines)

    def get_failed_tools(self) -> list[str]:
        """Return list of tool names that failed validation.

        Returns:
            List of tool names from all error categories

        Examples:
            >>> report = ValidationReport(
            ...     passed=False,
            ...     language="python",
            ...     checked_tools=["pytest", "npm"],
            ...     errors_by_category={
            ...         "missing": [ValidationResult(tool_name="pytest", found=False)],
            ...         "outdated": [ValidationResult(tool_name="npm", found=True, version_ok=False)]
            ...     }
            ... )
            >>> report.get_failed_tools()
            ['pytest', 'npm']
        """
        failed = []
        for results in self.errors_by_category.values():
            failed.extend(r.tool_name for r in results)
        return failed

    def get_error_count(self) -> int:
        """Return total number of validation errors.

        Returns:
            Integer count of all errors across all categories

        Examples:
            >>> report = ValidationReport(
            ...     passed=False,
            ...     language="python",
            ...     checked_tools=["pytest", "npm"],
            ...     errors_by_category={
            ...         "missing": [ValidationResult(tool_name="pytest", found=False)],
            ...         "outdated": [ValidationResult(tool_name="npm", found=True, version_ok=False)]
            ...     }
            ... )
            >>> report.get_error_count()
            2
        """
        return sum(len(results) for results in self.errors_by_category.values())
