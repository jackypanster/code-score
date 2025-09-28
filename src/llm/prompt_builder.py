"""
Prompt building and data filtering utilities.

This module provides functionality for building LLM prompts from evaluation data
with proper content truncation and context management for optimal generation.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from jinja2 import Template

from .models.template_context import TemplateContext
from .models.report_template import ReportTemplate
from .template_loader import TemplateLoader

logger = logging.getLogger(__name__)


class PromptBuilderError(Exception):
    """Base exception for prompt building errors."""
    pass


class ContextLimitExceededError(PromptBuilderError):
    """Exception raised when content exceeds context limits."""
    pass


class PromptBuilder:
    """
    Prompt construction and data filtering for LLM report generation.

    This class handles converting evaluation data into properly formatted
    prompts with content truncation and context management for LLM APIs.
    """

    def __init__(self, template_loader: Optional[TemplateLoader] = None):
        """
        Initialize PromptBuilder.

        Args:
            template_loader: TemplateLoader instance (creates new if None)
        """
        self.template_loader = template_loader or TemplateLoader()
        self._context_limits = {
            'max_evidence_items': 3,
            'max_checklist_items': 20,
            'max_description_length': 200,
            'max_prompt_length': 32000  # characters
        }

    def build_prompt(self, score_input_data: Dict[str, Any],
                    template_config: ReportTemplate,
                    custom_limits: Optional[Dict[str, int]] = None) -> str:
        """
        Build complete LLM prompt from evaluation data and template.

        This method converts structured evaluation data into a properly formatted
        prompt by applying template rendering with automatic content truncation
        to respect LLM context limits. It handles data filtering, template
        compilation, and prompt optimization for Gemini.

        Args:
            score_input_data: Loaded score_input.json data containing:
                - repository_info: Repository metadata
                - evaluation_result: Checklist evaluation results with scores
                - evidence_summary: Supporting evidence for evaluation decisions
            template_config: Template configuration with rendering instructions
            custom_limits: Custom content limits override (optional), e.g.:
                {"max_evidence_items": 5, "max_description_length": 300}

        Returns:
            Formatted prompt string ready for LLM processing, with:
            - Rendered template content with evaluation data
            - Applied content truncation based on limits
            - Generation metadata and helper variables
            - Cleaned formatting for optimal LLM consumption

        Raises:
            PromptBuilderError: If template rendering or data processing fails
            ContextLimitExceededError: If content exceeds maximum limits after truncation
            TemplateValidationError: If template syntax is invalid

        Examples:
            >>> builder = PromptBuilder()
            >>> prompt = builder.build_prompt(
            ...     score_input_data=evaluation_data,
            ...     template_config=template,
            ...     custom_limits={"max_evidence_items": 5}
            ... )
            >>> print(f"Prompt length: {len(prompt)} characters")
            >>> # Use prompt with LLM service
        """
        try:
            # Create template context from score input
            context = TemplateContext.from_score_input(score_input_data)

            # Apply content limits
            limits = self._context_limits.copy()
            if custom_limits:
                limits.update(custom_limits)

            if template_config.content_limits:
                limits.update(template_config.content_limits)

            context.apply_content_limits(limits)

            # Compile template
            compiled_template = self.template_loader.compile_template(template_config)

            # Render prompt
            prompt = self._render_prompt(compiled_template, context)

            # Validate prompt length
            if len(prompt) > limits.get('max_prompt_length', 32000):
                context.add_warning(f"Prompt length ({len(prompt)}) exceeds limit")
                prompt = self._truncate_prompt(prompt, limits.get('max_prompt_length', 32000))

            logger.info(f"Built prompt: {len(prompt)} characters, "
                       f"{len(context.warnings)} warnings")

            return prompt

        except Exception as e:
            raise PromptBuilderError(f"Failed to build prompt: {e}")

    def _render_prompt(self, template: Template, context: TemplateContext) -> str:
        """
        Render template with context data.

        Args:
            template: Compiled Jinja2 template
            context: Template context data

        Returns:
            Rendered prompt string
        """
        try:
            # Convert context to dictionary for Jinja2
            template_data = context.to_jinja_dict()

            # Add additional helper data
            template_data.update({
                'generation_time': datetime.utcnow().isoformat(),
                'has_warnings': len(context.warnings) > 0,
                'warning_count': len(context.warnings)
            })

            # Render template
            rendered = template.render(**template_data)

            # Clean up extra whitespace
            rendered = self._clean_prompt_text(rendered)

            return rendered

        except Exception as e:
            raise PromptBuilderError(f"Template rendering failed: {e}")

    def _clean_prompt_text(self, text: str) -> str:
        """
        Clean up prompt text formatting.

        Args:
            text: Raw rendered text

        Returns:
            Cleaned text
        """
        # Remove excessive blank lines
        lines = text.split('\n')
        cleaned_lines = []
        consecutive_blank = 0

        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                consecutive_blank = 0
            else:
                consecutive_blank += 1
                if consecutive_blank <= 2:  # Allow max 2 consecutive blank lines
                    cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def _truncate_prompt(self, prompt: str, max_length: int) -> str:
        """
        Truncate prompt to fit within length limits.

        Args:
            prompt: Full prompt text
            max_length: Maximum allowed length

        Returns:
            Truncated prompt with truncation notice
        """
        if len(prompt) <= max_length:
            return prompt

        # Find a good truncation point (end of a line)
        truncate_at = max_length - 200  # Leave space for notice
        while truncate_at > 0 and prompt[truncate_at] != '\n':
            truncate_at -= 1

        if truncate_at <= 0:
            truncate_at = max_length - 200

        truncated = prompt[:truncate_at]
        truncation_notice = "\n\n[Content truncated due to length limits]"

        return truncated + truncation_notice


    def validate_context_data(self, score_input_data: Dict[str, Any]) -> List[str]:
        """
        Validate score input data for prompt building.

        Args:
            score_input_data: Score input data to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        try:
            # Check required top-level fields
            required_fields = ['repository_info', 'evaluation_result']
            for field in required_fields:
                if field not in score_input_data:
                    issues.append(f"Missing required field: {field}")

            # Check repository info
            if 'repository_info' in score_input_data:
                repo_info = score_input_data['repository_info']
                repo_required = ['url', 'commit_sha', 'primary_language']
                for field in repo_required:
                    if field not in repo_info:
                        issues.append(f"Missing repository_info.{field}")

            # Check evaluation result
            if 'evaluation_result' in score_input_data:
                eval_result = score_input_data['evaluation_result']
                eval_required = ['checklist_items', 'total_score', 'category_breakdowns']
                for field in eval_required:
                    if field not in eval_result:
                        issues.append(f"Missing evaluation_result.{field}")

                # Validate checklist items structure
                if 'checklist_items' in eval_result:
                    for i, item in enumerate(eval_result['checklist_items']):
                        item_required = ['id', 'name', 'evaluation_status', 'score']
                        for field in item_required:
                            if field not in item:
                                issues.append(f"Missing checklist_items[{i}].{field}")

        except Exception as e:
            issues.append(f"Validation error: {e}")

        return issues

    def estimate_token_usage(self, prompt: str) -> Dict[str, Union[int, float]]:
        """
        Estimate token usage for Gemini LLM provider.

        Args:
            prompt: Prompt text

        Returns:
            Dictionary with token estimates
        """
        # Rough estimation: ~4 characters per token for Gemini
        char_count = len(prompt)
        estimated_tokens = char_count // 4

        return {
            'character_count': char_count,
            'estimated_tokens': estimated_tokens,
            'estimated_tokens_conservative': char_count // 3,  # Conservative estimate
            'estimated_cost_gemini': estimated_tokens * 0.0000125,  # $0.0125 per 1K tokens
        }

    def optimize_context_for_gemini(self, context: TemplateContext) -> TemplateContext:
        """
        Optimize context data for Gemini LLM provider.

        Args:
            context: Template context to optimize

        Returns:
            Optimized template context for Gemini
        """
        # Gemini-specific optimization settings
        gemini_limits = {
            'max_evidence_items': 3,
            'max_description_length': 150,
            'prefer_structured': True
        }

        # Apply Gemini-specific limits
        context.apply_content_limits(gemini_limits)

        # Add Gemini-specific context
        context.generation_metadata['optimized_for'] = 'gemini'
        context.generation_metadata['optimization_applied'] = list(gemini_limits.keys())

        return context

    def get_context_statistics(self, context: TemplateContext) -> Dict[str, Any]:
        """
        Get detailed statistics about template context.

        Args:
            context: Template context

        Returns:
            Dictionary with context statistics
        """
        return {
            'items': {
                'total': len(context.get_all_items()),
                'met': len(context.met_items),
                'partial': len(context.partial_items),
                'unmet': len(context.unmet_items)
            },
            'evidence': {
                'categories': len(context.evidence_summary),
                'total_items': sum(len(es.items) for es in context.evidence_summary),
                'truncated_categories': sum(1 for es in context.evidence_summary if es.truncated)
            },
            'repository': {
                'url': context.repository.url,
                'language': context.repository.primary_language,
                'commit': context.repository.commit_sha
            },
            'scores': {
                'total': context.total.score,
                'percentage': context.total.percentage,
                'grade': context.total.grade_letter
            },
            'warnings': len(context.warnings),
            'metadata_keys': list(context.generation_metadata.keys())
        }

    def set_context_limits(self, limits: Dict[str, int]) -> None:
        """
        Update default context limits.

        Args:
            limits: Dictionary of limit values
        """
        self._context_limits.update(limits)
        logger.debug(f"Updated context limits: {limits}")

    def get_context_limits(self) -> Dict[str, int]:
        """
        Get current context limits.

        Returns:
            Dictionary of current limits
        """
        return self._context_limits.copy()