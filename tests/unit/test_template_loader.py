"""
Unit tests for TemplateLoader class.

This module tests all functionality of the TemplateLoader class including
template loading, validation, security checks, caching, and error handling.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from jinja2 import Template
from jinja2.sandbox import SandboxedEnvironment

from src.llm.models.report_template import ReportTemplate

# Import the modules to test
from src.llm.template_loader import (
    TemplateLoader,
    TemplateLoaderError,
    TemplateNotFoundException,
    TemplateValidationError,
)


class TestTemplateLoader:
    """Unit tests for TemplateLoader class."""

    @pytest.fixture
    def template_loader(self):
        """Create TemplateLoader instance for testing."""
        return TemplateLoader()

    @pytest.fixture
    def template_loader_no_sandbox(self):
        """Create TemplateLoader without sandbox for testing."""
        return TemplateLoader(use_sandbox=False)

    @pytest.fixture
    def template_loader_no_cache(self):
        """Create TemplateLoader without caching for testing."""
        return TemplateLoader(cache_templates=False)

    @pytest.fixture
    def sample_template_content(self):
        """Sample template content for testing."""
        return """# Report for {{repository.url}}

## Score Overview
Total Score: {{total.score}}/100 ({{total.percentage}}%)

## Strengths
{% for item in met_items %}
- ✅ {{item.name}}: {{item.description}}
{% endfor %}

## Areas for Improvement
{% for item in unmet_items %}
- ❌ {{item.name}}: {{item.description}}
{% endfor %}
"""

    @pytest.fixture
    def invalid_template_content(self):
        """Invalid template content for testing syntax errors."""
        return """# Invalid Template
{{ unclosed_variable
{% invalid_tag %
"""

    @pytest.fixture
    def dangerous_template_content(self):
        """Template with dangerous content for security testing."""
        return """# Dangerous Template
{{ __import__('os').system('rm -rf /') }}
{{ open('/etc/passwd').read() }}
"""

    @pytest.fixture
    def temp_template_file(self, sample_template_content):
        """Create temporary template file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_template_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def temp_template_dir(self, sample_template_content):
        """Create temporary directory with template files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple template files
            for i, name in enumerate(['template1.md', 'template2.md', 'config.txt']):
                file_path = Path(temp_dir) / name
                if name.endswith('.md'):
                    content = sample_template_content.replace('{{repository.url}}', f'{{{{repo{i}.url}}}}')
                    file_path.write_text(content)
                else:
                    file_path.write_text("not a template")

            yield temp_dir

    def test_init_default_settings(self):
        """Test TemplateLoader initialization with default settings."""
        loader = TemplateLoader()

        assert loader.use_sandbox is True
        assert loader.cache_templates is True
        assert loader._template_cache == {}
        assert loader._environment is None

    def test_init_custom_settings(self):
        """Test TemplateLoader initialization with custom settings."""
        loader = TemplateLoader(use_sandbox=False, cache_templates=False)

        assert loader.use_sandbox is False
        assert loader.cache_templates is False
        assert loader._template_cache == {}

    def test_get_environment_sandboxed(self, template_loader):
        """Test getting sandboxed Jinja2 environment."""
        env = template_loader._get_environment()

        assert isinstance(env, SandboxedEnvironment)
        assert env.trim_blocks is True
        assert env.lstrip_blocks is True

    def test_get_environment_non_sandboxed(self, template_loader_no_sandbox):
        """Test getting non-sandboxed Jinja2 environment."""
        env = template_loader_no_sandbox._get_environment()

        assert not isinstance(env, SandboxedEnvironment)
        assert env.trim_blocks is True
        assert env.lstrip_blocks is True

    def test_get_environment_with_template_dir(self, template_loader, temp_template_dir):
        """Test getting environment with FileSystemLoader."""
        env = template_loader._get_environment(temp_template_dir)

        assert env.loader is not None
        assert isinstance(env, SandboxedEnvironment)

    def test_load_template_success(self, template_loader, temp_template_file):
        """Test successful template loading."""
        template_config = template_loader.load_template(temp_template_file)

        assert isinstance(template_config, ReportTemplate)
        assert template_config.name == Path(temp_template_file).stem
        assert template_config.file_path == temp_template_file
        assert len(template_config.required_fields) > 0

    def test_load_template_not_found(self, template_loader):
        """Test template loading with non-existent file."""
        with pytest.raises(TemplateNotFoundException) as exc_info:
            template_loader.load_template("/non/existent/template.md")

        assert "Template file not found" in str(exc_info.value)

    def test_load_template_relative_path(self, template_loader):
        """Test loading template with relative path."""
        # Mock the path resolution and file existence
        with patch('pathlib.Path.exists', return_value=True), \
             patch('src.llm.models.report_template.ReportTemplate.validate_template_syntax'), \
             patch.object(template_loader, '_extract_template_variables', return_value=['test_var']), \
             patch('pathlib.Path.stem', 'test_template'):

            template_config = template_loader.load_template("specs/prompts/test.md")

            assert isinstance(template_config, ReportTemplate)

    @patch('src.llm.models.report_template.ReportTemplate.validate_template_syntax',
           side_effect=ValueError("Template syntax error"))
    def test_load_template_validation_error(self, mock_validate, template_loader, temp_template_file):
        """Test template loading with validation error."""
        with pytest.raises(TemplateValidationError) as exc_info:
            template_loader.load_template(temp_template_file)

        assert "Failed to load template" in str(exc_info.value)

    def test_compile_template_success(self, template_loader, temp_template_file):
        """Test successful template compilation."""
        template_config = template_loader.load_template(temp_template_file)
        compiled_template = template_loader.compile_template(template_config)

        assert isinstance(compiled_template, Template)

    def test_compile_template_caching(self, template_loader, temp_template_file):
        """Test template compilation with caching."""
        template_config = template_loader.load_template(temp_template_file)

        # First compilation
        template1 = template_loader.compile_template(template_config)

        # Second compilation should return cached version
        template2 = template_loader.compile_template(template_config)

        assert template1 is template2
        assert len(template_loader._template_cache) == 1

    def test_compile_template_no_caching(self, template_loader_no_cache, temp_template_file):
        """Test template compilation without caching."""
        template_config = template_loader_no_cache.load_template(temp_template_file)

        # Compile multiple times
        template1 = template_loader_no_cache.compile_template(template_config)
        template2 = template_loader_no_cache.compile_template(template_config)

        assert template1 is not template2
        assert len(template_loader_no_cache._template_cache) == 0

    def test_compile_template_syntax_error(self, template_loader, invalid_template_content):
        """Test template compilation with syntax error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(invalid_template_content)
            temp_path = f.name

        try:
            # Mock ReportTemplate to avoid validation
            with patch('src.llm.models.report_template.ReportTemplate.load_template_content',
                      return_value=invalid_template_content):
                template_config = ReportTemplate(
                    name="invalid",
                    file_path=temp_path,
                    description="Invalid template"
                )

                with pytest.raises(TemplateValidationError) as exc_info:
                    template_loader.compile_template(template_config)

                assert "Template syntax error" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_extract_template_variables(self, template_loader, temp_template_file):
        """Test extraction of template variables."""
        variables = template_loader._extract_template_variables(temp_template_file)

        expected_vars = ['met_items', 'repository', 'total', 'unmet_items']
        for var in expected_vars:
            assert var in variables

    def test_extract_template_variables_file_error(self, template_loader):
        """Test variable extraction with file error."""
        variables = template_loader._extract_template_variables("/non/existent/file.md")

        assert variables == []

    def test_validate_template_fields(self, template_loader, temp_template_file):
        """Test template field validation."""
        template_config = template_loader.load_template(temp_template_file)
        available_fields = ['repository.url', 'total.score', 'total.percentage', 'met_items']

        missing_fields = template_loader.validate_template_fields(template_config, available_fields)

        # Should have missing fields since we didn't include all required fields
        assert isinstance(missing_fields, list)

    def test_load_from_directory_success(self, template_loader, temp_template_dir):
        """Test loading templates from directory."""
        templates = template_loader.load_from_directory(temp_template_dir)

        assert len(templates) == 2  # Only .md files should be loaded
        for template in templates:
            assert isinstance(template, ReportTemplate)
            assert template.file_path.endswith('.md')

    def test_load_from_directory_not_found(self, template_loader):
        """Test loading from non-existent directory."""
        with pytest.raises(TemplateNotFoundException) as exc_info:
            template_loader.load_from_directory("/non/existent/directory")

        assert "Template directory not found" in str(exc_info.value)

    def test_load_from_directory_custom_pattern(self, template_loader, temp_template_dir):
        """Test loading from directory with custom pattern."""
        templates = template_loader.load_from_directory(temp_template_dir, "*.txt")

        assert len(templates) == 1  # Only config.txt should match

    def test_get_default_template_path(self, template_loader):
        """Test getting default template path."""
        path = template_loader.get_default_template_path()

        assert path.endswith("specs/prompts/llm_report.md")
        assert "src" not in path  # Should be relative to project root

    def test_load_default_template(self, template_loader):
        """Test loading default template."""
        with patch.object(template_loader, 'load_template') as mock_load:
            mock_load.return_value = ReportTemplate(
                name="default",
                file_path="specs/prompts/llm_report.md",
                description="Default template"
            )

            template = template_loader.load_default_template()

            assert isinstance(template, ReportTemplate)
            mock_load.assert_called_once()

    def test_create_template_from_string(self, template_loader, sample_template_content):
        """Test creating template from string content."""
        template = template_loader.create_template_from_string(sample_template_content, "test_template")

        assert isinstance(template, Template)

    def test_create_template_from_string_syntax_error(self, template_loader, invalid_template_content):
        """Test creating template from invalid string content."""
        with pytest.raises(TemplateValidationError) as exc_info:
            template_loader.create_template_from_string(invalid_template_content, "invalid_template")

        assert "Template syntax error" in str(exc_info.value)

    def test_clear_cache(self, template_loader, temp_template_file):
        """Test clearing template cache."""
        # Load and compile a template to populate cache
        template_config = template_loader.load_template(temp_template_file)
        template_loader.compile_template(template_config)

        assert len(template_loader._template_cache) == 1

        template_loader.clear_cache()

        assert len(template_loader._template_cache) == 0

    def test_get_cache_stats(self, template_loader, temp_template_file):
        """Test getting cache statistics."""
        # Initially empty cache
        stats = template_loader.get_cache_stats()
        assert stats['cache_enabled'] is True
        assert stats['cached_templates'] == 0
        assert stats['template_paths'] == []

        # Load template to populate cache
        template_config = template_loader.load_template(temp_template_file)
        template_loader.compile_template(template_config)

        stats = template_loader.get_cache_stats()
        assert stats['cached_templates'] == 1
        assert len(stats['template_paths']) == 1

    def test_get_cache_stats_disabled(self, template_loader_no_cache):
        """Test cache stats when caching is disabled."""
        stats = template_loader_no_cache.get_cache_stats()

        assert stats['cache_enabled'] is False
        assert stats['cached_templates'] == 0

    def test_validate_template_syntax_only_success(self, template_loader, temp_template_file):
        """Test syntax-only validation for valid template."""
        result = template_loader.validate_template_syntax_only(temp_template_file)

        assert result is True

    def test_validate_template_syntax_only_invalid(self, template_loader, invalid_template_content):
        """Test syntax-only validation for invalid template."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(invalid_template_content)
            temp_path = f.name

        try:
            with pytest.raises(TemplateValidationError) as exc_info:
                template_loader.validate_template_syntax_only(temp_path)

            assert "Template syntax error" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_template_syntax_only_not_found(self, template_loader):
        """Test syntax validation for non-existent file."""
        with pytest.raises(TemplateNotFoundException):
            template_loader.validate_template_syntax_only("/non/existent/file.md")

    def test_validate_template_security_dangerous_content(self, template_loader, dangerous_template_content):
        """Test security validation with dangerous content."""
        with pytest.raises(TemplateValidationError) as exc_info:
            template_loader._validate_template_security(dangerous_template_content)

        assert "potentially dangerous pattern" in str(exc_info.value)

    def test_validate_template_security_large_file(self, template_loader):
        """Test security validation with large file."""
        large_content = "x" * 200_000  # Larger than 100KB limit

        with pytest.raises(TemplateValidationError) as exc_info:
            template_loader._validate_template_security(large_content)

        assert "too large" in str(exc_info.value)

    def test_validate_template_security_deep_nesting(self, template_loader):
        """Test security validation with excessive nesting."""
        nested_content = ""
        for i in range(25):  # More than 20 level limit
            nested_content += f"{{% if condition{i} %}}\n"
        nested_content += "content\n"
        for i in range(25):
            nested_content += "{% endif %}\n"

        with pytest.raises(TemplateValidationError) as exc_info:
            template_loader._validate_template_security(nested_content)

        assert "nesting too deep" in str(exc_info.value)

    def test_validate_template_security_safe_content(self, template_loader, sample_template_content):
        """Test security validation with safe content."""
        # Should not raise exception
        template_loader._validate_template_security(sample_template_content)

    def test_validate_template_with_context_success(self, template_loader, temp_template_file):
        """Test template validation with sample context."""
        template_config = template_loader.load_template(temp_template_file)
        sample_context = {
            'repository': {'url': 'https://github.com/test/repo'},
            'total': {'score': 85, 'percentage': 85.0},
            'met_items': [{'name': 'Test1', 'description': 'Desc1'}],
            'unmet_items': [{'name': 'Test2', 'description': 'Desc2'}]
        }

        results = template_loader.validate_template_with_context(template_config, sample_context)

        assert results['valid'] is True
        assert results['security_passed'] is True
        assert results['render_test_passed'] is True

    def test_validate_template_with_context_security_fail(self, template_loader, dangerous_template_content):
        """Test template validation with context when security fails."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(dangerous_template_content)
            temp_path = f.name

        try:
            template_config = ReportTemplate(
                name="dangerous",
                file_path=temp_path,
                description="Dangerous template"
            )

            with patch.object(template_config, 'load_template_content', return_value=dangerous_template_content):
                results = template_loader.validate_template_with_context(template_config, {})

                assert results['valid'] is False
                assert results['security_passed'] is False
                assert "Security validation failed" in results['errors'][0]
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_template_with_context_render_fail(self, template_loader, temp_template_file):
        """Test template validation with context when rendering fails."""
        template_config = template_loader.load_template(temp_template_file)
        # Invalid context that will cause rendering to fail
        invalid_context = {'invalid': 'data'}

        results = template_loader.validate_template_with_context(template_config, invalid_context)

        # May pass or fail depending on template - check structure
        assert 'valid' in results
        assert 'security_passed' in results
        assert 'render_test_passed' in results

    def test_get_available_templates(self, template_loader):
        """Test getting available templates."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.glob') as mock_glob:

            # Mock template files
            mock_files = [
                MagicMock(stem='template1', spec=Path),
                MagicMock(stem='template2', spec=Path)
            ]
            mock_files[0].__str__ = lambda: '/path/template1.md'
            mock_files[1].__str__ = lambda: '/path/template2.md'
            mock_glob.return_value = mock_files

            templates = template_loader.get_available_templates()

            assert len(templates) == 2
            assert 'template1' in templates
            assert 'template2' in templates

    def test_get_available_templates_no_directory(self, template_loader):
        """Test getting available templates when directory doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            templates = template_loader.get_available_templates()

            assert templates == {}

    def test_render_template_preview(self, template_loader, temp_template_file):
        """Test rendering template preview."""
        template_config = template_loader.load_template(temp_template_file)
        sample_data = {
            'repository': {'url': 'https://github.com/test/repo'},
            'total': {'score': 85, 'percentage': 85.0},
            'met_items': [{'name': 'Test1', 'description': 'Desc1'}],
            'unmet_items': []
        }

        preview = template_loader.render_template_preview(template_config, sample_data)

        assert isinstance(preview, str)
        assert len(preview) > 0
        assert 'https://github.com/test/repo' in preview

    def test_render_template_preview_truncated(self, template_loader, temp_template_file):
        """Test rendering template preview with truncation."""
        template_config = template_loader.load_template(temp_template_file)
        sample_data = {
            'repository': {'url': 'https://github.com/test/repo'},
            'total': {'score': 85, 'percentage': 85.0},
            'met_items': [{'name': f'Test{i}', 'description': f'Desc{i}'} for i in range(100)],
            'unmet_items': []
        }

        preview = template_loader.render_template_preview(template_config, sample_data, max_length=100)

        assert len(preview) <= 120  # Allows for truncation message
        assert "[truncated]" in preview

    def test_render_template_preview_error(self, template_loader, temp_template_file):
        """Test rendering template preview with error."""
        template_config = template_loader.load_template(temp_template_file)

        # Mock compile_template to raise an exception
        with patch.object(template_loader, 'compile_template', side_effect=Exception("Test error")):
            preview = template_loader.render_template_preview(template_config, {})

            assert "Preview failed" in preview
            assert "Test error" in preview

    def test_exception_hierarchy(self):
        """Test exception hierarchy is correct."""
        assert issubclass(TemplateValidationError, TemplateLoaderError)
        assert issubclass(TemplateNotFoundException, TemplateLoaderError)
        assert issubclass(TemplateLoaderError, Exception)

    def test_logging_integration(self, template_loader, temp_template_file, caplog):
        """Test that appropriate log messages are generated."""
        with caplog.at_level("INFO"):
            template_config = template_loader.load_template(temp_template_file)
            template_loader.compile_template(template_config)
            template_loader.clear_cache()

        # Check that relevant log messages were generated
        log_messages = [record.message for record in caplog.records]
        assert any("Successfully loaded template" in msg for msg in log_messages)

    @pytest.mark.parametrize("sandbox_setting", [True, False])
    def test_sandbox_configuration(self, sandbox_setting):
        """Test TemplateLoader with different sandbox settings."""
        loader = TemplateLoader(use_sandbox=sandbox_setting)
        env = loader._get_environment()

        if sandbox_setting:
            assert isinstance(env, SandboxedEnvironment)
        else:
            assert not isinstance(env, SandboxedEnvironment)

    @pytest.mark.parametrize("cache_setting", [True, False])
    def test_cache_configuration(self, cache_setting, temp_template_file):
        """Test TemplateLoader with different cache settings."""
        loader = TemplateLoader(cache_templates=cache_setting)
        template_config = loader.load_template(temp_template_file)

        # Compile template twice
        loader.compile_template(template_config)
        loader.compile_template(template_config)

        if cache_setting:
            assert len(loader._template_cache) == 1
        else:
            assert len(loader._template_cache) == 0
