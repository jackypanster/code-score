"""Unit tests for tool registry structure and completeness.

This module validates the tool registry data structure, ensuring all languages
have proper tool definitions with valid URLs, no duplicates, and required tools.

Test Strategy:
- Validate registry structure and completeness
- Ensure all tools have valid doc URLs (HTTP/HTTPS)
- Check for duplicate tool names within languages
- Verify minimum required tools for each language
- Test get_tools_for_language function
- No mocking needed - tests validate static data
"""

import pytest

from src.metrics.tool_registry import (
    GLOBAL_TOOLS,
    PYTHON_TOOLS,
    JAVASCRIPT_TOOLS,
    GO_TOOLS,
    JAVA_TOOLS,
    TOOL_REQUIREMENTS,
    get_tools_for_language,
)


class TestRegistryStructure:
    """Tests for overall registry structure and completeness."""

    def test_all_languages_have_tools(self):
        """Test that all languages in registry have non-empty tool lists."""
        for language, tools in TOOL_REQUIREMENTS.items():
            assert len(tools) > 0, f"Language '{language}' has no tools defined"

    def test_tool_requirements_dict_structure(self):
        """Test that TOOL_REQUIREMENTS has expected language keys."""
        expected_languages = {"global", "python", "javascript", "typescript", "java", "go"}
        actual_languages = set(TOOL_REQUIREMENTS.keys())

        assert actual_languages == expected_languages, \
            f"Registry missing languages. Expected: {expected_languages}, Got: {actual_languages}"

    def test_global_tools_not_empty(self):
        """Test that global tools list is not empty."""
        assert len(GLOBAL_TOOLS) > 0, "GLOBAL_TOOLS should not be empty"

    def test_typescript_uses_javascript_tools(self):
        """Test that TypeScript uses the same tools as JavaScript."""
        assert TOOL_REQUIREMENTS["typescript"] is TOOL_REQUIREMENTS["javascript"], \
            "TypeScript should share the same tool list as JavaScript"


class TestToolURLs:
    """Tests for tool documentation URLs."""

    def test_all_tools_have_valid_urls(self):
        """Test that all tools have doc_url starting with http/https."""
        for language, tools in TOOL_REQUIREMENTS.items():
            for tool in tools:
                assert tool.doc_url.startswith(("http://", "https://")), \
                    f"Tool '{tool.name}' in '{language}' has invalid doc_url: {tool.doc_url}"

    def test_global_tools_have_https_urls(self):
        """Test that global tools use HTTPS URLs."""
        for tool in GLOBAL_TOOLS:
            assert tool.doc_url.startswith("https://"), \
                f"Global tool '{tool.name}' should use HTTPS: {tool.doc_url}"

    def test_python_tools_have_valid_urls(self):
        """Test that Python tools have valid documentation URLs."""
        for tool in PYTHON_TOOLS:
            assert tool.doc_url.startswith("https://"), \
                f"Python tool '{tool.name}' should have HTTPS URL: {tool.doc_url}"


class TestNoDuplicateTools:
    """Tests to ensure no duplicate tool names within languages."""

    def test_no_duplicate_global_tools(self):
        """Test that global tools have no duplicate names."""
        tool_names = [tool.name for tool in GLOBAL_TOOLS]
        assert len(tool_names) == len(set(tool_names)), \
            f"Duplicate global tool names found: {tool_names}"

    def test_no_duplicate_python_tools(self):
        """Test that Python tools have no duplicate names."""
        tool_names = [tool.name for tool in PYTHON_TOOLS]
        assert len(tool_names) == len(set(tool_names)), \
            f"Duplicate Python tool names found: {tool_names}"

    def test_no_duplicate_javascript_tools(self):
        """Test that JavaScript tools have no duplicate names."""
        tool_names = [tool.name for tool in JAVASCRIPT_TOOLS]
        assert len(tool_names) == len(set(tool_names)), \
            f"Duplicate JavaScript tool names found: {tool_names}"

    def test_no_duplicate_go_tools(self):
        """Test that Go tools have no duplicate names."""
        tool_names = [tool.name for tool in GO_TOOLS]
        assert len(tool_names) == len(set(tool_names)), \
            f"Duplicate Go tool names found: {tool_names}"

    def test_no_duplicate_java_tools(self):
        """Test that Java tools have no duplicate names."""
        tool_names = [tool.name for tool in JAVA_TOOLS]
        assert len(tool_names) == len(set(tool_names)), \
            f"Duplicate Java tool names found: {tool_names}"


class TestPythonTools:
    """Tests for Python-specific tool requirements."""

    def test_python_has_minimum_required_tools(self):
        """Test that Python has the minimum required set of tools."""
        tool_names = {tool.name for tool in PYTHON_TOOLS}
        required_tools = {"ruff", "pytest", "pip-audit", "python3"}

        assert required_tools.issubset(tool_names), \
            f"Python missing required tools. Expected at least: {required_tools}, Got: {tool_names}"

    def test_python_has_ruff_linter(self):
        """Test that Python includes ruff linter."""
        tool_names = [tool.name for tool in PYTHON_TOOLS]
        assert "ruff" in tool_names, "Python tools should include 'ruff' linter"

    def test_python_has_pytest(self):
        """Test that Python includes pytest."""
        tool_names = [tool.name for tool in PYTHON_TOOLS]
        assert "pytest" in tool_names, "Python tools should include 'pytest'"

    def test_python_has_pip_audit(self):
        """Test that Python includes pip-audit for security."""
        tool_names = [tool.name for tool in PYTHON_TOOLS]
        assert "pip-audit" in tool_names, "Python tools should include 'pip-audit'"

    def test_python3_has_min_version(self):
        """Test that python3 has minimum version requirement."""
        python3_tool = next((t for t in PYTHON_TOOLS if t.name == "python3"), None)
        assert python3_tool is not None, "python3 tool not found"
        assert python3_tool.min_version is not None, "python3 should have min_version"
        assert python3_tool.min_version == "3.11.0", "python3 min_version should be 3.11.0"


class TestJavaScriptTools:
    """Tests for JavaScript-specific tool requirements."""

    def test_javascript_has_npm(self):
        """Test that JavaScript includes npm."""
        tool_names = [tool.name for tool in JAVASCRIPT_TOOLS]
        assert "npm" in tool_names, "JavaScript tools should include 'npm'"

    def test_javascript_has_node(self):
        """Test that JavaScript includes node."""
        tool_names = [tool.name for tool in JAVASCRIPT_TOOLS]
        assert "node" in tool_names, "JavaScript tools should include 'node'"

    def test_javascript_has_eslint(self):
        """Test that JavaScript includes eslint."""
        tool_names = [tool.name for tool in JAVASCRIPT_TOOLS]
        assert "eslint" in tool_names, "JavaScript tools should include 'eslint'"

    def test_npm_has_min_version_8(self):
        """Test that npm has minimum version 8.0.0 (per FR-014)."""
        npm_tool = next((t for t in JAVASCRIPT_TOOLS if t.name == "npm"), None)
        assert npm_tool is not None, "npm tool not found"
        assert npm_tool.min_version == "8.0.0", "npm min_version should be 8.0.0 (FR-014)"


class TestGoTools:
    """Tests for Go-specific tool requirements."""

    def test_go_has_required_tools(self):
        """Test that Go has essential tools."""
        tool_names = {tool.name for tool in GO_TOOLS}
        required_tools = {"go", "golangci-lint"}

        assert required_tools.issubset(tool_names), \
            f"Go missing required tools. Expected at least: {required_tools}, Got: {tool_names}"

    def test_go_version_command_is_special(self):
        """Test that go tool uses 'version' command not '--version'."""
        go_tool = next((t for t in GO_TOOLS if t.name == "go"), None)
        assert go_tool is not None, "go tool not found"
        assert go_tool.version_command == "version", \
            "Go uses 'go version' not 'go --version'"


class TestJavaTools:
    """Tests for Java-specific tool requirements."""

    def test_java_has_build_tools(self):
        """Test that Java has build tools (maven or gradle)."""
        tool_names = {tool.name for tool in JAVA_TOOLS}
        build_tools = {"mvn", "gradle"}

        # Should have at least one build tool
        assert len(tool_names.intersection(build_tools)) > 0, \
            f"Java should have at least one build tool: {build_tools}"

    def test_java_has_min_version_17(self):
        """Test that Java has minimum version 17.0.0."""
        java_tool = next((t for t in JAVA_TOOLS if t.name == "java"), None)
        assert java_tool is not None, "java tool not found"
        assert java_tool.min_version == "17.0.0", "java min_version should be 17.0.0"


class TestGlobalTools:
    """Tests for global tools (required for all languages)."""

    def test_global_has_git(self):
        """Test that global tools include git."""
        tool_names = [tool.name for tool in GLOBAL_TOOLS]
        assert "git" in tool_names, "Global tools should include 'git'"

    def test_global_has_uv(self):
        """Test that global tools include uv."""
        tool_names = [tool.name for tool in GLOBAL_TOOLS]
        assert "uv" in tool_names, "Global tools should include 'uv'"

    def test_global_tools_count(self):
        """Test that global tools list has expected number of tools."""
        # Should have at least git and uv
        assert len(GLOBAL_TOOLS) >= 2, "Global tools should have at least 2 tools (git, uv)"


class TestGetToolsForLanguageFunction:
    """Tests for get_tools_for_language helper function."""

    def test_get_tools_for_python(self):
        """Test getting tools for Python includes global + Python tools."""
        tools = get_tools_for_language("python")

        tool_names = {tool.name for tool in tools}

        # Should include global tools
        assert "git" in tool_names, "Should include global tool 'git'"
        assert "uv" in tool_names, "Should include global tool 'uv'"

        # Should include Python tools
        assert "ruff" in tool_names, "Should include Python tool 'ruff'"
        assert "pytest" in tool_names, "Should include Python tool 'pytest'"

    def test_get_tools_for_javascript(self):
        """Test getting tools for JavaScript includes global + JS tools."""
        tools = get_tools_for_language("javascript")

        tool_names = {tool.name for tool in tools}

        # Should include global tools
        assert "git" in tool_names, "Should include global tool 'git'"

        # Should include JavaScript tools
        assert "npm" in tool_names, "Should include JavaScript tool 'npm'"
        assert "node" in tool_names, "Should include JavaScript tool 'node'"

    def test_get_tools_for_typescript(self):
        """Test getting tools for TypeScript (uses JavaScript tools)."""
        tools = get_tools_for_language("typescript")

        tool_names = {tool.name for tool in tools}

        # Should include global tools
        assert "git" in tool_names, "Should include global tool 'git'"

        # Should include JavaScript/TypeScript tools
        assert "npm" in tool_names, "Should include JavaScript tool 'npm'"
        assert "eslint" in tool_names, "Should include JavaScript tool 'eslint'"

    def test_get_tools_returns_combined_list(self):
        """Test that get_tools_for_language returns global + language tools."""
        python_tools = get_tools_for_language("python")

        # Count should be global tools + python-specific tools
        expected_count = len(GLOBAL_TOOLS) + len(PYTHON_TOOLS)
        assert len(python_tools) == expected_count, \
            f"Expected {expected_count} tools (global + python), got {len(python_tools)}"

    def test_get_tools_unsupported_language_raises_error(self):
        """Test that unsupported language raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_tools_for_language("ruby")

        assert "Unsupported language: ruby" in str(exc_info.value)
        assert "Supported languages:" in str(exc_info.value)

    def test_get_tools_error_message_lists_supported_languages(self):
        """Test that error message includes list of supported languages."""
        with pytest.raises(ValueError) as exc_info:
            get_tools_for_language("cobol")

        error_message = str(exc_info.value)
        # Should mention supported languages
        assert "python" in error_message.lower()
        assert "javascript" in error_message.lower()

    def test_get_tools_case_sensitive(self):
        """Test that language name is case-sensitive."""
        with pytest.raises(ValueError):
            get_tools_for_language("Python")  # Capital P should fail

        with pytest.raises(ValueError):
            get_tools_for_language("PYTHON")  # All caps should fail


class TestToolCategories:
    """Tests for tool category classifications."""

    def test_all_tools_have_categories(self):
        """Test that all tools have a category assigned."""
        for language, tools in TOOL_REQUIREMENTS.items():
            for tool in tools:
                assert tool.category is not None, \
                    f"Tool '{tool.name}' in '{language}' has no category"
                assert len(tool.category) > 0, \
                    f"Tool '{tool.name}' in '{language}' has empty category"

    def test_categories_are_valid(self):
        """Test that all categories are in expected set."""
        valid_categories = {"lint", "test", "security", "build"}

        for language, tools in TOOL_REQUIREMENTS.items():
            for tool in tools:
                assert tool.category in valid_categories, \
                    f"Tool '{tool.name}' has invalid category: {tool.category}"


class TestToolLanguageAttribute:
    """Tests for tool language attribute consistency."""

    def test_global_tools_have_global_language(self):
        """Test that all global tools have language='global'."""
        for tool in GLOBAL_TOOLS:
            assert tool.language == "global", \
                f"Global tool '{tool.name}' should have language='global', got '{tool.language}'"

    def test_python_tools_have_python_language(self):
        """Test that all Python tools have language='python'."""
        for tool in PYTHON_TOOLS:
            assert tool.language == "python", \
                f"Python tool '{tool.name}' should have language='python', got '{tool.language}'"

    def test_javascript_tools_have_javascript_language(self):
        """Test that all JavaScript tools have language='javascript'."""
        for tool in JAVASCRIPT_TOOLS:
            assert tool.language == "javascript", \
                f"JavaScript tool '{tool.name}' should have language='javascript', got '{tool.language}'"


class TestVersionCommands:
    """Tests for version command specifications."""

    def test_all_tools_have_version_commands(self):
        """Test that all tools have version_command specified."""
        for language, tools in TOOL_REQUIREMENTS.items():
            for tool in tools:
                assert tool.version_command is not None, \
                    f"Tool '{tool.name}' in '{language}' has no version_command"
                assert len(tool.version_command) > 0, \
                    f"Tool '{tool.name}' in '{language}' has empty version_command"

    def test_most_tools_use_version_flag(self):
        """Test that most tools use --version flag."""
        # Most tools should use --version
        version_flag_count = 0
        total_tools = 0

        for language, tools in TOOL_REQUIREMENTS.items():
            for tool in tools:
                total_tools += 1
                if tool.version_command == "--version":
                    version_flag_count += 1

        # At least 80% should use --version
        assert version_flag_count / total_tools >= 0.8, \
            f"Expected most tools to use '--version', but only {version_flag_count}/{total_tools} do"
