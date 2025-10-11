"""Tool registry defining required tools for each programming language.

This module contains the centralized registry of all CLI tools required
for code analysis, organized by programming language and category.
"""


from .models.tool_requirement import ToolRequirement

# Global tools - required for ALL languages (FR-014)
GLOBAL_TOOLS: list[ToolRequirement] = [
    ToolRequirement(
        name="git",
        language="global",
        category="build",
        doc_url="https://git-scm.com/doc",
        min_version=None,  # Any version acceptable
        version_command="--version"
    ),
    ToolRequirement(
        name="uv",
        language="global",
        category="build",
        doc_url="https://docs.astral.sh/uv/",
        min_version=None,
        version_command="--version"
    ),
]


# Python tools
PYTHON_TOOLS: list[ToolRequirement] = [
    ToolRequirement(
        name="ruff",
        language="python",
        category="lint",
        doc_url="https://docs.astral.sh/ruff",
        min_version="0.1.0",
        version_command="--version"
    ),
    ToolRequirement(
        name="pytest",
        language="python",
        category="test",
        doc_url="https://docs.pytest.org",
        min_version=None,
        version_command="--version"
    ),
    ToolRequirement(
        name="pip-audit",
        language="python",
        category="security",
        doc_url="https://pypi.org/project/pip-audit/",
        min_version=None,
        version_command="--version"
    ),
    ToolRequirement(
        name="python3",
        language="python",
        category="build",
        doc_url="https://www.python.org/downloads/",
        min_version="3.11.0",
        version_command="--version"
    ),
]


# JavaScript/TypeScript tools (shared toolchain)
JAVASCRIPT_TOOLS: list[ToolRequirement] = [
    ToolRequirement(
        name="node",
        language="javascript",
        category="build",
        doc_url="https://nodejs.org/docs",
        min_version=None,
        version_command="--version"
    ),
    ToolRequirement(
        name="npm",
        language="javascript",
        category="build",
        doc_url="https://docs.npmjs.com",
        min_version="8.0.0",
        version_command="--version"
    ),
    ToolRequirement(
        name="eslint",
        language="javascript",
        category="lint",
        doc_url="https://eslint.org/docs",
        min_version=None,
        version_command="--version"
    ),
]


# Go tools
GO_TOOLS: list[ToolRequirement] = [
    ToolRequirement(
        name="go",
        language="go",
        category="build",
        doc_url="https://go.dev/doc/",
        min_version=None,
        version_command="version"  # Note: Go uses "go version" not "go --version"
    ),
    ToolRequirement(
        name="golangci-lint",
        language="go",
        category="lint",
        doc_url="https://golangci-lint.run/",
        min_version=None,
        version_command="--version"
    ),
    ToolRequirement(
        name="osv-scanner",
        language="go",
        category="security",
        doc_url="https://github.com/google/osv-scanner",
        min_version=None,
        version_command="--version"
    ),
]


# Java tools
JAVA_TOOLS: list[ToolRequirement] = [
    ToolRequirement(
        name="java",
        language="java",
        category="build",
        doc_url="https://docs.oracle.com/javase/17/",
        min_version="17.0.0",
        version_command="--version"
    ),
    ToolRequirement(
        name="mvn",
        language="java",
        category="build",
        doc_url="https://maven.apache.org/guides/",
        min_version=None,
        version_command="--version"
    ),
    ToolRequirement(
        name="gradle",
        language="java",
        category="build",
        doc_url="https://docs.gradle.org/",
        min_version=None,
        version_command="--version"
    ),
]


# Master registry: maps language names to tool requirements
# Includes "global" tools for all languages (FR-014)
TOOL_REQUIREMENTS: dict[str, list[ToolRequirement]] = {
    "global": GLOBAL_TOOLS,
    "python": PYTHON_TOOLS,
    "javascript": JAVASCRIPT_TOOLS,
    "typescript": JAVASCRIPT_TOOLS,  # TypeScript uses same tools as JavaScript
    "java": JAVA_TOOLS,
    "go": GO_TOOLS,
}


def get_tools_for_language(language: str) -> list[ToolRequirement]:
    """Get all required tools for a specific language.

    This function returns both global tools (required for all languages)
    and language-specific tools.

    Args:
        language: Programming language name (e.g., "python", "javascript")

    Returns:
        List of ToolRequirement instances (global + language-specific)

    Raises:
        ValueError: If language is not supported

    Examples:
        >>> tools = get_tools_for_language("python")
        >>> len(tools)  # Global tools + Python tools
        6
        >>> tool_names = [t.name for t in tools]
        >>> "git" in tool_names  # Global tool
        True
        >>> "ruff" in tool_names  # Python-specific tool
        True
    """
    if language not in TOOL_REQUIREMENTS:
        supported_languages = sorted(set(TOOL_REQUIREMENTS.keys()) - {"global"})
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported languages: {supported_languages}"
        )

    # Return global tools + language-specific tools
    global_tools = TOOL_REQUIREMENTS["global"]
    language_tools = TOOL_REQUIREMENTS[language]

    return global_tools + language_tools
