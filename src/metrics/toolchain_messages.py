"""Chinese message templates for toolchain validation.

This module provides standardized error messages for toolchain validation failures.
All messages are in Chinese per FR-013 requirements. The design allows for future
internationalization by keeping message templates as class constants.

Usage:
    from metrics.toolchain_messages import ValidationMessages

    # Format missing tool error
    msg = ValidationMessages.format_missing("ruff", "https://docs.astral.sh/ruff")

    # Format outdated tool error
    msg = ValidationMessages.format_outdated("npm", "7.5.0", "8.0.0", "https://docs.npmjs.com")

    # Format permission error
    msg = ValidationMessages.format_permission("ruff", "/usr/bin/ruff", "-rw-r--r--")
"""


class ValidationMessages:
    """Chinese error message templates for toolchain validation.

    This class contains all error message templates and category headers used
    throughout the toolchain validation system. All messages follow the format
    specified in FR-013.

    Attributes:
        TOOL_MISSING: Template for missing tool errors
        TOOL_OUTDATED: Template for outdated version errors
        TOOL_PERMISSION_ERROR: Template for permission errors
        VALIDATION_FAILED_HEADER: Header for validation failure reports
        CATEGORY_MISSING_HEADER: Section header for missing tools
        CATEGORY_OUTDATED_HEADER: Section header for outdated tools
        CATEGORY_PERMISSION_HEADER: Section header for permission errors
    """

    # Core error message templates
    TOOL_MISSING = "缺少工具 {tool_name}。请在评分主机安装后重试（参考 {doc_url}）"

    TOOL_OUTDATED = "工具 {tool_name} 版本过旧（当前: {current_version}，最低要求: {minimum_version}）。请升级后重试（参考 {doc_url}）"

    TOOL_PERMISSION_ERROR = "工具 {tool_name} 位于 {path} 但权限不足（当前: {permissions}）。请修复权限后重试。"

    # Validation report headers
    VALIDATION_FAILED_HEADER = "工具链验证失败，发现以下问题：\n"

    # Category section headers (FR-017: errors grouped by category)
    CATEGORY_MISSING_HEADER = "\n【缺少工具】"
    CATEGORY_OUTDATED_HEADER = "\n【版本过旧】"
    CATEGORY_PERMISSION_HEADER = "\n【权限不足】"

    @staticmethod
    def format_missing(tool_name: str, doc_url: str) -> str:
        """Format missing tool error message.

        Args:
            tool_name: Name of the missing tool (e.g., "ruff", "npm")
            doc_url: Official documentation URL for the tool

        Returns:
            Formatted Chinese error message following FR-013 format

        Example:
            >>> ValidationMessages.format_missing("ruff", "https://docs.astral.sh/ruff")
            '缺少工具 ruff。请在评分主机安装后重试（参考 https://docs.astral.sh/ruff）'
        """
        return ValidationMessages.TOOL_MISSING.format(
            tool_name=tool_name, doc_url=doc_url
        )

    @staticmethod
    def format_outdated(tool_name: str, current: str, minimum: str, doc_url: str) -> str:
        """Format outdated tool version error message.

        Args:
            tool_name: Name of the tool with outdated version
            current: Currently installed version (e.g., "7.5.0")
            minimum: Minimum required version (e.g., "8.0.0")
            doc_url: Official documentation URL for upgrade instructions

        Returns:
            Formatted Chinese error message with version comparison

        Example:
            >>> ValidationMessages.format_outdated("npm", "7.5.0", "8.0.0", "https://docs.npmjs.com")
            '工具 npm 版本过旧（当前: 7.5.0，最低要求: 8.0.0）。请升级后重试（参考 https://docs.npmjs.com）'
        """
        return ValidationMessages.TOOL_OUTDATED.format(
            tool_name=tool_name,
            current_version=current,
            minimum_version=minimum,
            doc_url=doc_url
        )

    @staticmethod
    def format_permission(tool_name: str, path: str, permissions: str) -> str:
        """Format tool permission error message.

        Args:
            tool_name: Name of the tool with permission issues
            path: Absolute path to the tool executable
            permissions: Unix-style permission string (e.g., "-rw-r--r--")

        Returns:
            Formatted Chinese error message with path and permission details

        Example:
            >>> ValidationMessages.format_permission("ruff", "/usr/bin/ruff", "-rw-r--r--")
            '工具 ruff 位于 /usr/bin/ruff 但权限不足（当前: -rw-r--r--）。请修复权限后重试。'
        """
        return ValidationMessages.TOOL_PERMISSION_ERROR.format(
            tool_name=tool_name, path=path, permissions=permissions
        )
