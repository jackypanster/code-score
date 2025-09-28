"""
Template loading and validation utilities.

This module provides functionality for loading, validating, and compiling
Jinja2 templates for LLM report generation with security sandboxing.
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template, TemplateSyntaxError, meta
from jinja2.sandbox import SandboxedEnvironment

from .models.report_template import ReportTemplate

logger = logging.getLogger(__name__)


class TemplateLoaderError(Exception):
    """Base exception for template loading errors."""
    pass


class TemplateValidationError(TemplateLoaderError):
    """Exception raised when template validation fails."""
    pass


class TemplateNotFoundException(TemplateLoaderError):
    """Exception raised when template file is not found."""
    pass


class TemplateLoader:
    """
    Template loading and validation utility for LLM report generation.

    This class handles loading Jinja2 templates with security sandboxing,
    validation, and compilation for use in report generation workflows.
    """

    def __init__(self, use_sandbox: bool = True, cache_templates: bool = True):
        """
        Initialize TemplateLoader.

        Args:
            use_sandbox: Whether to use Jinja2 sandboxed environment for security
            cache_templates: Whether to cache compiled templates in memory
        """
        self.use_sandbox = use_sandbox
        self.cache_templates = cache_templates
        self._template_cache: dict[str, Template] = {}
        self._environment: Environment | None = None

    def _get_environment(self, template_dir: str | None = None) -> Environment:
        """
        Get Jinja2 environment with appropriate configuration.

        Args:
            template_dir: Directory for FileSystemLoader (optional)

        Returns:
            Configured Jinja2 Environment
        """
        if self._environment is None or template_dir:
            if self.use_sandbox:
                if template_dir:
                    loader = FileSystemLoader(template_dir)
                    self._environment = SandboxedEnvironment(loader=loader)
                else:
                    self._environment = SandboxedEnvironment()
            else:
                if template_dir:
                    loader = FileSystemLoader(template_dir)
                    self._environment = Environment(loader=loader)
                else:
                    self._environment = Environment()

            # Configure environment settings
            self._environment.trim_blocks = True
            self._environment.lstrip_blocks = True

        return self._environment

    def load_template(self, template_path: str) -> ReportTemplate:
        """
        Load template configuration from file path.

        This method loads and validates a Jinja2 template file, extracting
        template variables and creating a ReportTemplate configuration
        object. It handles both absolute and relative paths, with relative
        paths resolved against the project root.

        Args:
            template_path: Path to template file (absolute or relative).
                Supported formats: .md, .j2, .jinja2
                Relative paths resolved from project root

        Returns:
            ReportTemplate instance with validated configuration including:
            - Extracted template variables for validation
            - Template metadata and description
            - Validated syntax and security checks

        Raises:
            TemplateNotFoundException: If template file not found at specified path
            TemplateValidationError: If template syntax is invalid or contains
                security issues (dangerous patterns, excessive nesting)
            PermissionError: If template file cannot be read due to permissions

        Examples:
            >>> loader = TemplateLoader()
            >>> template = loader.load_template("specs/prompts/custom.md")
            >>> print(f"Template: {template.name}")
            >>> print(f"Required fields: {template.required_fields}")
        """
        # Convert to absolute path
        path = Path(template_path)
        if not path.is_absolute():
            # Resolve relative to project root
            project_root = Path(__file__).parent.parent.parent
            path = project_root / template_path

        if not path.exists():
            raise TemplateNotFoundException(f"Template file not found: {path}")

        try:
            # Create ReportTemplate with basic configuration
            template_config = ReportTemplate(
                name=path.stem,
                file_path=str(path),
                description=f"Template loaded from {path.name}",
                required_fields=self._extract_template_variables(str(path))
            )

            # Validate template syntax
            template_config.validate_template_syntax()

            logger.info(f"Successfully loaded template: {template_config.name}")
            return template_config

        except Exception as e:
            raise TemplateValidationError(f"Failed to load template {path}: {e}")

    def compile_template(self, template_config: ReportTemplate) -> Template:
        """
        Compile Jinja2 template from configuration.

        Args:
            template_config: ReportTemplate configuration

        Returns:
            Compiled Jinja2 Template

        Raises:
            TemplateValidationError: If compilation fails
        """
        cache_key = template_config.file_path

        # Check cache first
        if self.cache_templates and cache_key in self._template_cache:
            logger.debug(f"Using cached template: {template_config.name}")
            return self._template_cache[cache_key]

        try:
            # Load template content
            template_content = template_config.load_template_content()

            # Get environment and compile
            env = self._get_environment()
            compiled_template = env.from_string(template_content)

            # Cache if enabled
            if self.cache_templates:
                self._template_cache[cache_key] = compiled_template

            logger.debug(f"Compiled template: {template_config.name}")
            return compiled_template

        except TemplateSyntaxError as e:
            raise TemplateValidationError(f"Template syntax error in {template_config.name}: {e}")
        except Exception as e:
            raise TemplateValidationError(f"Failed to compile template {template_config.name}: {e}")

    def _extract_template_variables(self, template_path: str) -> list[str]:
        """
        Extract template variables from Jinja2 template.

        Args:
            template_path: Path to template file

        Returns:
            List of variable names used in template
        """
        try:
            with open(template_path, encoding='utf-8') as f:
                template_content = f.read()

            # Parse template to extract variables
            env = self._get_environment()
            ast = env.parse(template_content)
            variables = meta.find_undeclared_variables(ast)

            return sorted(list(variables))

        except Exception as e:
            logger.warning(f"Could not extract variables from template {template_path}: {e}")
            return []

    def validate_template_fields(self, template_config: ReportTemplate,
                                available_fields: list[str]) -> list[str]:
        """
        Validate that template required fields are available.

        Args:
            template_config: Template configuration
            available_fields: Available field names for rendering

        Returns:
            List of missing required fields (empty if all present)
        """
        return template_config.check_required_fields(available_fields)

    def load_from_directory(self, template_dir: str, pattern: str = "*.md") -> list[ReportTemplate]:
        """
        Load all templates from a directory.

        Args:
            template_dir: Directory containing template files
            pattern: File pattern to match (default: *.md)

        Returns:
            List of loaded ReportTemplate configurations

        Raises:
            TemplateNotFoundException: If directory not found
        """
        dir_path = Path(template_dir)
        if not dir_path.exists():
            raise TemplateNotFoundException(f"Template directory not found: {dir_path}")

        templates = []
        template_files = dir_path.glob(pattern)

        for template_file in template_files:
            try:
                template_config = self.load_template(str(template_file))
                templates.append(template_config)
                logger.debug(f"Loaded template from directory: {template_file.name}")
            except Exception as e:
                logger.warning(f"Failed to load template {template_file}: {e}")

        logger.info(f"Loaded {len(templates)} templates from {template_dir}")
        return templates

    def get_default_template_path(self) -> str:
        """
        Get path to default template file.

        Returns:
            Path to default template
        """
        project_root = Path(__file__).parent.parent.parent
        default_path = project_root / "specs" / "prompts" / "llm_report.md"
        return str(default_path)

    def load_default_template(self) -> ReportTemplate:
        """
        Load the default template configuration.

        Returns:
            Default ReportTemplate configuration

        Raises:
            TemplateNotFoundException: If default template not found
        """
        default_path = self.get_default_template_path()
        return self.load_template(default_path)

    def create_template_from_string(self, template_content: str,
                                  name: str = "inline_template") -> Template:
        """
        Create compiled template from string content.

        Args:
            template_content: Template content as string
            name: Template name for identification

        Returns:
            Compiled Jinja2 Template

        Raises:
            TemplateValidationError: If template compilation fails
        """
        try:
            env = self._get_environment()
            template = env.from_string(template_content)
            logger.debug(f"Created template from string: {name}")
            return template

        except TemplateSyntaxError as e:
            raise TemplateValidationError(f"Template syntax error in {name}: {e}")
        except Exception as e:
            raise TemplateValidationError(f"Failed to create template {name}: {e}")

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()
        logger.debug("Template cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get template cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            'cache_enabled': self.cache_templates,
            'cached_templates': len(self._template_cache),
            'template_paths': list(self._template_cache.keys())
        }

    def validate_template_syntax_only(self, template_path: str) -> bool:
        """
        Validate template syntax without full loading.

        Args:
            template_path: Path to template file

        Returns:
            True if syntax is valid

        Raises:
            TemplateValidationError: If syntax validation fails
        """
        try:
            with open(template_path, encoding='utf-8') as f:
                template_content = f.read()

            # Security validation first
            self._validate_template_security(template_content)

            env = self._get_environment()
            env.parse(template_content)
            return True

        except TemplateSyntaxError as e:
            raise TemplateValidationError(f"Template syntax error: {e}")
        except FileNotFoundError:
            raise TemplateNotFoundException(f"Template file not found: {template_path}")
        except Exception as e:
            raise TemplateValidationError(f"Template validation failed: {e}")

    def _validate_template_security(self, template_content: str) -> None:
        """
        Validate template content for security issues.

        Args:
            template_content: Template content to validate

        Raises:
            TemplateValidationError: If security issues are found
        """
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            # File system access
            r'__file__', r'__import__', r'open\s*\(', r'file\s*\(',
            # Code execution
            r'eval\s*\(', r'exec\s*\(', r'compile\s*\(',
            # System access
            r'os\.', r'sys\.', r'subprocess', r'import\s',
            # Python builtins that could be dangerous
            r'globals\s*\(', r'locals\s*\(', r'vars\s*\(',
            r'getattr\s*\(', r'setattr\s*\(', r'delattr\s*\(',
            # Network access
            r'urllib', r'requests', r'socket', r'http',
        ]

        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, template_content, re.IGNORECASE):
                safe_pattern = pattern.replace('\\', '')
                raise TemplateValidationError(
                    f"Template contains potentially dangerous pattern: {safe_pattern}"
                )

        # Check template size
        if len(template_content) > 100_000:  # 100KB limit
            raise TemplateValidationError("Template file is too large (>100KB)")

        # Check for excessive nesting that could cause recursion issues
        max_nesting = 20
        current_nesting = 0
        max_found = 0

        for line in template_content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('{%') and not stripped.startswith('{%- end'):
                if any(keyword in stripped for keyword in ['if', 'for', 'with', 'block']):
                    current_nesting += 1
                    max_found = max(max_found, current_nesting)
            elif stripped.startswith('{%') and 'end' in stripped:
                current_nesting = max(0, current_nesting - 1)

        if max_found > max_nesting:
            raise TemplateValidationError(f"Template nesting too deep ({max_found} > {max_nesting})")

        # Check for unusual variable patterns that might indicate injection
        suspicious_vars = [
            r'\{\{\s*[^}]*\|\s*safe\s*\}\}',  # |safe filter usage
            r'\{\{\s*[^}]*__[^}]*\}\}',       # Double underscore variables
        ]

        for pattern in suspicious_vars:
            if re.search(pattern, template_content):
                logger.warning(f"Template contains potentially unsafe pattern: {pattern}")

    def validate_template_with_context(self, template_config: ReportTemplate,
                                     sample_context: dict[str, Any]) -> dict[str, Any]:
        """
        Validate template with sample context data.

        Args:
            template_config: Template configuration
            sample_context: Sample context data for testing

        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'security_passed': True,
            'render_test_passed': False
        }

        try:
            # Security validation
            template_content = template_config.load_template_content()
            self._validate_template_security(template_content)
            results['security_passed'] = True

        except TemplateValidationError as e:
            results['valid'] = False
            results['security_passed'] = False
            results['errors'].append(f"Security validation failed: {e}")
            return results

        try:
            # Render test with sandboxed environment
            compiled_template = self.compile_template(template_config)
            rendered = compiled_template.render(**sample_context)

            # Basic output validation
            if len(rendered.strip()) == 0:
                results['warnings'].append("Template renders to empty content")
            elif len(rendered) > 1_000_000:  # 1MB limit
                results['warnings'].append("Template output is very large (>1MB)")

            # Check for unrendered template syntax (indicates missing variables)
            import re
            unrendered_patterns = [
                r'\{\{[^}]+\}\}',  # Unrendered variables
                r'\{%[^%]+%\}',    # Unrendered tags
            ]

            for pattern in unrendered_patterns:
                matches = re.findall(pattern, rendered)
                if matches:
                    results['warnings'].append(f"Unrendered template syntax found: {matches[:3]}")

            results['render_test_passed'] = True

        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Render test failed: {e}")

        return results

    def get_available_templates(self) -> dict[str, str]:
        """
        Get available templates in the default template directory.

        Returns:
            Dictionary mapping template names to file paths
        """
        project_root = Path(__file__).parent.parent.parent
        template_dir = project_root / "specs" / "prompts"

        templates = {}
        if template_dir.exists():
            for template_file in template_dir.glob("*.md"):
                templates[template_file.stem] = str(template_file)

        return templates

    def render_template_preview(self, template_config: ReportTemplate,
                               sample_data: dict[str, Any],
                               max_length: int = 500) -> str:
        """
        Render template with sample data for preview.

        Args:
            template_config: Template configuration
            sample_data: Sample data for rendering
            max_length: Maximum preview length

        Returns:
            Rendered template preview (truncated if needed)
        """
        try:
            compiled_template = self.compile_template(template_config)
            rendered = compiled_template.render(**sample_data)

            if len(rendered) > max_length:
                rendered = rendered[:max_length] + "\n... [truncated]"

            return rendered

        except Exception as e:
            return f"Preview failed: {e}"
