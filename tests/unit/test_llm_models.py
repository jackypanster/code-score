"""
Unit tests for LLM data models.

This module tests all Pydantic models in the src/llm/models/ package including
validation, field constraints, computed fields, and model methods.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

from pydantic import ValidationError

# Import the models to test
from src.llm.models.llm_provider_config import LLMProviderConfig
from src.llm.models.report_template import ReportTemplate
from src.llm.models.generated_report import (
    GeneratedReport,
    TruncationInfo,
    ProviderMetadata,
    TemplateMetadata,
    InputMetadata
)
from src.llm.models.template_context import (
    TemplateContext,
    RepositoryInfo,
    ScoreContext,
    CategoryScore,
    ChecklistItemContext,
    EvidenceSummary
)


class TestLLMProviderConfig:
    """Unit tests for LLMProviderConfig model."""

    def test_valid_configuration(self):
        """Test creating valid LLMProviderConfig."""
        config = LLMProviderConfig(
            provider_name="gemini",
            cli_command=["gemini", "--api-key", "${GEMINI_API_KEY}"],
            model_name="gemini-1.5-pro",
            timeout_seconds=30,
            max_tokens=2048,
            temperature=0.7
        )

        assert config.provider_name == "gemini"
        assert config.cli_command == ["gemini", "--api-key", "${GEMINI_API_KEY}"]
        assert config.model_name == "gemini-1.5-pro"
        assert config.timeout_seconds == 30
        assert config.max_tokens == 2048
        assert config.temperature == 0.7

    def test_minimal_configuration(self):
        """Test creating minimal valid configuration."""
        config = LLMProviderConfig(
            provider_name="simple",
            cli_command=["echo", "test"]
        )

        assert config.provider_name == "simple"
        assert config.cli_command == ["echo", "test"]
        assert config.timeout_seconds == 30  # Default value
        assert config.model_name is None
        assert config.max_tokens is None
        assert config.temperature is None

    def test_invalid_provider_name(self):
        """Test validation of provider name format."""
        with pytest.raises(ValidationError) as exc_info:
            LLMProviderConfig(
                provider_name="Invalid-Name",
                cli_command=["test"]
            )

        assert "String should match pattern" in str(exc_info.value)

    def test_empty_cli_command(self):
        """Test validation of empty CLI command."""
        with pytest.raises(ValidationError) as exc_info:
            LLMProviderConfig(
                provider_name="test",
                cli_command=[]
            )

        assert "List should have at least 1 item" in str(exc_info.value)

    def test_invalid_timeout_range(self):
        """Test validation of timeout range."""
        # Too low
        with pytest.raises(ValidationError) as exc_info:
            LLMProviderConfig(
                provider_name="test",
                cli_command=["test"],
                timeout_seconds=5
            )

        assert "greater than or equal to 10" in str(exc_info.value)

        # Too high
        with pytest.raises(ValidationError) as exc_info:
            LLMProviderConfig(
                provider_name="test",
                cli_command=["test"],
                timeout_seconds=400
            )

        assert "less than or equal to 300" in str(exc_info.value)

    def test_invalid_max_tokens(self):
        """Test validation of max_tokens."""
        with pytest.raises(ValidationError) as exc_info:
            LLMProviderConfig(
                provider_name="test",
                cli_command=["test"],
                max_tokens=0
            )

        assert "greater than 0" in str(exc_info.value)

    def test_invalid_temperature_range(self):
        """Test validation of temperature range."""
        # Too low
        with pytest.raises(ValidationError) as exc_info:
            LLMProviderConfig(
                provider_name="test",
                cli_command=["test"],
                temperature=-0.1
            )

        assert "greater than or equal to 0" in str(exc_info.value)

        # Too high
        with pytest.raises(ValidationError) as exc_info:
            LLMProviderConfig(
                provider_name="test",
                cli_command=["test"],
                temperature=2.1
            )

        assert "less than or equal to 2" in str(exc_info.value)

    def test_get_default_configs(self):
        """Test getting default provider configurations."""
        configs = LLMProviderConfig.get_default_configs()

        assert isinstance(configs, dict)
        assert "gemini" in configs
        assert isinstance(configs["gemini"], LLMProviderConfig)

    def test_validate_environment_no_variables(self):
        """Test environment validation with no required variables."""
        config = LLMProviderConfig(
            provider_name="test",
            cli_command=["echo", "hello"]
        )

        missing = config.validate_environment()
        assert missing == []

    @patch.dict('os.environ', {'TEST_API_KEY': 'secret'})
    def test_validate_environment_variables_present(self):
        """Test environment validation when variables are present."""
        config = LLMProviderConfig(
            provider_name="test",
            cli_command=["test_cli", "--key", "${TEST_API_KEY}"],
            required_env_vars=["TEST_API_KEY"]
        )

        missing = config.validate_environment()
        assert missing == []

    @patch.dict('os.environ', {}, clear=True)
    def test_validate_environment_variables_missing(self):
        """Test environment validation when variables are missing."""
        config = LLMProviderConfig(
            provider_name="test",
            cli_command=["test_cli", "--key", "${MISSING_KEY}"],
            required_env_vars=["MISSING_KEY"]
        )

        missing = config.validate_environment()
        assert "MISSING_KEY" in missing

    def test_build_cli_command_simple(self):
        """Test building CLI command without prompt integration."""
        config = LLMProviderConfig(
            provider_name="test",
            cli_command=["echo", "hello"]
        )

        cmd = config.build_cli_command("test prompt")
        assert cmd == ["echo", "hello", "test prompt"]

    def test_build_cli_command_with_prompt_placeholder(self):
        """Test building CLI command with prompt placeholder."""
        config = LLMProviderConfig(
            provider_name="test",
            cli_command=["llm", "--prompt", "{prompt}", "--model", "test"]
        )

        cmd = config.build_cli_command("test prompt")
        assert cmd == ["llm", "--prompt", "test prompt", "--model", "test"]


class TestReportTemplate:
    """Unit tests for ReportTemplate model."""

    def test_valid_template(self):
        """Test creating valid ReportTemplate."""
        template = ReportTemplate(
            name="test_template",
            file_path="/path/to/template.md",
            description="Test template for unit tests",
            required_fields=["repository", "total", "items"],
            content_limits={"max_evidence_items": 5}
        )

        assert template.name == "test_template"
        assert template.file_path == "/path/to/template.md"
        assert template.description == "Test template for unit tests"
        assert template.required_fields == ["repository", "total", "items"]
        assert template.content_limits["max_evidence_items"] == 5

    def test_minimal_template(self):
        """Test creating minimal valid template."""
        template = ReportTemplate(
            name="minimal",
            file_path="/path/to/minimal.md",
            description="Minimal template"
        )

        assert template.name == "minimal"
        assert template.required_fields == []
        assert "max_evidence_items" in template.content_limits  # Default values

    def test_invalid_name_length(self):
        """Test validation of template name length."""
        # Empty name
        with pytest.raises(ValidationError) as exc_info:
            ReportTemplate(
                name="",
                file_path="/path/to/template.md",
                description="Test"
            )

        assert "at least 1 character" in str(exc_info.value)

        # Too long name
        with pytest.raises(ValidationError) as exc_info:
            ReportTemplate(
                name="x" * 101,
                file_path="/path/to/template.md",
                description="Test"
            )

        assert "at most 100 characters" in str(exc_info.value)

    def test_invalid_description_length(self):
        """Test validation of description length."""
        # Empty description
        with pytest.raises(ValidationError) as exc_info:
            ReportTemplate(
                name="test",
                file_path="/path/to/template.md",
                description=""
            )

        assert "at least 1 character" in str(exc_info.value)

        # Too long description
        with pytest.raises(ValidationError) as exc_info:
            ReportTemplate(
                name="test",
                file_path="/path/to/template.md",
                description="x" * 501
            )

        assert "at most 500 characters" in str(exc_info.value)

    def test_template_type_inference(self):
        """Test automatic template type inference."""
        template = ReportTemplate(
            name="test",
            file_path="/path/to/template.md",
            description="Test template"
        )

        assert template.template_type == "markdown"

        template_jinja = ReportTemplate(
            name="test",
            file_path="/path/to/template.j2",
            description="Test template"
        )

        assert template_jinja.template_type == "jinja2"

    @patch('builtins.open', new_callable=mock_open, read_data="# Template\n{{repository.url}}")
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_template_content(self, mock_exists, mock_file):
        """Test loading template content from file."""
        template = ReportTemplate(
            name="test",
            file_path="/path/to/template.md",
            description="Test template"
        )

        content = template.load_template_content()

        assert content == "# Template\n{{repository.url}}"
        mock_file.assert_called_once_with("/path/to/template.md", 'r', encoding='utf-8')

    @patch('pathlib.Path.exists', return_value=False)
    def test_load_template_content_file_not_found(self, mock_exists):
        """Test loading template content when file doesn't exist."""
        template = ReportTemplate(
            name="test",
            file_path="/nonexistent/template.md",
            description="Test template"
        )

        with pytest.raises(FileNotFoundError):
            template.load_template_content()

    @patch('builtins.open', new_callable=mock_open, read_data="# Template\n{{repository.url}}")
    @patch('pathlib.Path.exists', return_value=True)
    def test_validate_template_syntax_valid(self, mock_exists, mock_file):
        """Test template syntax validation with valid template."""
        template = ReportTemplate(
            name="test",
            file_path="/path/to/template.md",
            description="Test template"
        )

        # Should not raise exception
        template.validate_template_syntax()

    def test_check_required_fields_all_present(self):
        """Test checking required fields when all are present."""
        template = ReportTemplate(
            name="test",
            file_path="/path/to/template.md",
            description="Test template",
            required_fields=["repository", "total"]
        )

        available_fields = ["repository", "total", "extra"]
        missing = template.check_required_fields(available_fields)

        assert missing == []

    def test_check_required_fields_some_missing(self):
        """Test checking required fields when some are missing."""
        template = ReportTemplate(
            name="test",
            file_path="/path/to/template.md",
            description="Test template",
            required_fields=["repository", "total", "missing"]
        )

        available_fields = ["repository", "total"]
        missing = template.check_required_fields(available_fields)

        assert missing == ["missing"]


class TestGeneratedReport:
    """Unit tests for GeneratedReport and related models."""

    @pytest.fixture
    def sample_template_metadata(self):
        """Sample TemplateMetadata for testing."""
        return TemplateMetadata(
            file_path="/path/to/template.md",
            template_name="test_template",
            template_type="markdown",
            required_fields_used=["repository", "total"]
        )

    @pytest.fixture
    def sample_provider_metadata(self):
        """Sample ProviderMetadata for testing."""
        return ProviderMetadata(
            provider_name="test_provider",
            model_name="test-model",
            temperature=0.7,
            max_tokens=2048,
            response_time_seconds=5.2
        )

    @pytest.fixture
    def sample_input_metadata(self):
        """Sample InputMetadata for testing."""
        return InputMetadata(
            repository_url="https://github.com/test/repo.git",
            commit_sha="abc123",
            primary_language="python",
            total_score=75.5,
            max_possible_score=100,
            checklist_items_count=10,
            evidence_items_count=25
        )

    def test_truncation_info_creation(self):
        """Test creating TruncationInfo."""
        info = TruncationInfo(
            evidence_truncated=True,
            items_removed=5,
            original_length=10000,
            final_length=5000,
            truncation_reason="context_limit"
        )

        assert info.evidence_truncated is True
        assert info.items_removed == 5
        assert info.original_length == 10000
        assert info.final_length == 5000
        assert info.truncation_reason == "context_limit"

    def test_truncation_info_defaults(self):
        """Test TruncationInfo with default values."""
        info = TruncationInfo()

        assert info.evidence_truncated is False
        assert info.items_removed == 0
        assert info.original_length == 0
        assert info.final_length == 0
        assert info.truncation_reason is None

    def test_provider_metadata_creation(self, sample_provider_metadata):
        """Test creating ProviderMetadata."""
        assert sample_provider_metadata.provider_name == "test_provider"
        assert sample_provider_metadata.model_name == "test-model"
        assert sample_provider_metadata.temperature == 0.7
        assert sample_provider_metadata.response_time_seconds == 5.2

    def test_template_metadata_creation(self, sample_template_metadata):
        """Test creating TemplateMetadata."""
        assert sample_template_metadata.file_path == "/path/to/template.md"
        assert sample_template_metadata.template_name == "test_template"
        assert sample_template_metadata.template_type == "markdown"
        assert sample_template_metadata.required_fields_used == ["repository", "total"]

    def test_input_metadata_creation(self, sample_input_metadata):
        """Test creating InputMetadata."""
        assert sample_input_metadata.repository_url == "https://github.com/test/repo.git"
        assert sample_input_metadata.total_score == 75.5
        assert sample_input_metadata.checklist_items_count == 10

    def test_generated_report_creation(self, sample_template_metadata,
                                     sample_provider_metadata, sample_input_metadata):
        """Test creating GeneratedReport."""
        content = "# Test Report\n\nGenerated content here."

        report = GeneratedReport(
            content=content,
            template_used=sample_template_metadata,
            provider_used=sample_provider_metadata,
            input_metadata=sample_input_metadata
        )

        assert report.content == content
        assert report.template_used == sample_template_metadata
        assert report.provider_used == sample_provider_metadata
        assert report.input_metadata == sample_input_metadata

    def test_generated_report_calculate_derived_fields(self, sample_template_metadata,
                                                       sample_provider_metadata, sample_input_metadata):
        """Test calculation of derived fields."""
        content = "# Test Report\n\nThis is a test report with multiple words."

        report = GeneratedReport(
            content=content,
            template_used=sample_template_metadata,
            provider_used=sample_provider_metadata,
            input_metadata=sample_input_metadata
        )

        report.calculate_derived_fields()

        assert report.word_count > 0
        assert report.character_count == len(content)
        assert isinstance(report.generation_timestamp, datetime)

    def test_generated_report_validate_markdown_valid(self, sample_template_metadata,
                                                     sample_provider_metadata, sample_input_metadata):
        """Test markdown validation with valid content."""
        content = "# Valid Report\n\n## Section\n\nValid markdown content."

        report = GeneratedReport(
            content=content,
            template_used=sample_template_metadata,
            provider_used=sample_provider_metadata,
            input_metadata=sample_input_metadata
        )

        issues = report.validate_markdown_structure()

        assert issues == []

    def test_generated_report_validate_markdown_invalid(self, sample_template_metadata,
                                                       sample_provider_metadata, sample_input_metadata):
        """Test markdown validation with invalid content."""
        content = "No heading\nJust plain text."

        report = GeneratedReport(
            content=content,
            template_used=sample_template_metadata,
            provider_used=sample_provider_metadata,
            input_metadata=sample_input_metadata
        )

        issues = report.validate_markdown_structure()

        assert len(issues) > 0
        assert any("No H1 heading found" in issue for issue in issues)

    def test_generated_report_add_warning(self, sample_template_metadata,
                                        sample_provider_metadata, sample_input_metadata):
        """Test adding warnings to generated report."""
        report = GeneratedReport(
            content="Test content",
            template_used=sample_template_metadata,
            provider_used=sample_provider_metadata,
            input_metadata=sample_input_metadata
        )

        report.add_warning("Test warning message")

        assert "Test warning message" in report.generation_warnings

    def test_generated_report_to_file_content(self, sample_template_metadata,
                                            sample_provider_metadata, sample_input_metadata):
        """Test converting report to file content with metadata."""
        content = "# Test Report\n\nReport content"

        report = GeneratedReport(
            content=content,
            template_used=sample_template_metadata,
            provider_used=sample_provider_metadata,
            input_metadata=sample_input_metadata
        )

        file_content = report.to_file_content()

        assert content in file_content
        assert "Generated by" in file_content
        assert sample_provider_metadata.provider_name in file_content


class TestTemplateContext:
    """Unit tests for TemplateContext and related models."""

    @pytest.fixture
    def sample_score_input(self):
        """Sample score_input.json data for testing."""
        return {
            "repository_info": {
                "url": "https://github.com/test/repository.git",
                "commit_sha": "abc123",
                "primary_language": "python",
                "analysis_timestamp": "2025-09-27T10:30:00Z"
            },
            "evaluation_result": {
                "checklist_items": [
                    {
                        "id": "item1",
                        "name": "Test Item 1",
                        "evaluation_status": "met",
                        "score": 10.0,
                        "actual_points": 10.0,
                        "max_points": 10,
                        "description": "Test description"
                    },
                    {
                        "id": "item2",
                        "name": "Test Item 2",
                        "evaluation_status": "partial",
                        "score": 5.0,
                        "actual_points": 5.0,
                        "max_points": 10,
                        "description": "Partial test"
                    }
                ],
                "total_score": 15.0,
                "max_possible_score": 20,
                "score_percentage": 75.0,
                "category_breakdowns": {
                    "code_quality": {
                        "score": 10.0,
                        "actual_points": 10.0,
                        "max_points": 10,
                        "percentage": 100.0
                    },
                    "testing": {
                        "score": 5.0,
                        "actual_points": 5.0,
                        "max_points": 10,
                        "percentage": 50.0
                    }
                }
            }
        }

    def test_repository_info_creation(self):
        """Test creating RepositoryInfo."""
        repo = RepositoryInfo(
            url="https://github.com/test/repo.git",
            commit_sha="abc123",
            primary_language="python"
        )

        assert repo.url == "https://github.com/test/repo.git"
        assert repo.commit_sha == "abc123"
        assert repo.primary_language == "python"

    def test_category_score_creation(self):
        """Test creating CategoryScore."""
        score = CategoryScore(
            score=75.5,
            max_points=100,
            percentage=75.5
        )

        assert score.score == 75.5
        assert score.max_points == 100
        assert score.percentage == 75.5

    def test_category_score_grade_calculation(self):
        """Test grade letter calculation for CategoryScore."""
        # Test A grade
        score_a = CategoryScore(score=95, max_points=100, percentage=95.0)
        assert score_a.grade_letter == "A"

        # Test B grade
        score_b = CategoryScore(score=85, max_points=100, percentage=85.0)
        assert score_b.grade_letter == "B"

        # Test C grade
        score_c = CategoryScore(score=75, max_points=100, percentage=75.0)
        assert score_c.grade_letter == "C"

        # Test D grade
        score_d = CategoryScore(score=65, max_points=100, percentage=65.0)
        assert score_d.grade_letter == "D"

        # Test F grade
        score_f = CategoryScore(score=55, max_points=100, percentage=55.0)
        assert score_f.grade_letter == "F"

    def test_category_score_status(self):
        """Test status determination for CategoryScore."""
        # Test excellent
        score_excellent = CategoryScore(score=95, max_points=100, percentage=95.0)
        assert score_excellent.status == "excellent"

        # Test good
        score_good = CategoryScore(score=85, max_points=100, percentage=85.0)
        assert score_good.status == "good"

        # Test satisfactory
        score_satisfactory = CategoryScore(score=75, max_points=100, percentage=75.0)
        assert score_satisfactory.status == "satisfactory"

        # Test needs_improvement
        score_needs_improvement = CategoryScore(score=65, max_points=100, percentage=65.0)
        assert score_needs_improvement.status == "needs_improvement"

        # Test poor
        score_poor = CategoryScore(score=45, max_points=100, percentage=45.0)
        assert score_poor.status == "poor"

    def test_score_context_creation(self):
        """Test creating ScoreContext."""
        score = ScoreContext(
            score=85.5,
            max_points=100,
            percentage=85.5
        )

        assert score.score == 85.5
        assert score.percentage == 85.5
        assert score.grade_letter == "B"

    def test_checklist_item_context_creation(self):
        """Test creating ChecklistItemContext."""
        item = ChecklistItemContext(
            id="test_item",
            name="Test Item",
            status="met",
            score=10.0,
            max_points=10,
            description="Test description"
        )

        assert item.id == "test_item"
        assert item.name == "Test Item"
        assert item.status == "met"
        assert item.score == 10.0

    def test_evidence_summary_creation(self):
        """Test creating EvidenceSummary."""
        evidence = EvidenceSummary(
            category="code_quality",
            items=[
                {
                    "source": "test.txt",
                    "description": "Test evidence",
                    "confidence": 0.9
                }
            ],
            truncated=False
        )

        assert evidence.category == "code_quality"
        assert len(evidence.items) == 1
        assert evidence.truncated is False

    def test_template_context_from_score_input(self, sample_score_input):
        """Test creating TemplateContext from score input data."""
        context = TemplateContext.from_score_input(sample_score_input)

        assert isinstance(context.repository, RepositoryInfo)
        assert context.repository.url == "https://github.com/test/repository.git"

        assert isinstance(context.total, ScoreContext)
        assert context.total.score == 15.0

        assert len(context.met_items) == 1
        assert len(context.partial_items) == 1
        assert len(context.unmet_items) == 0

    def test_template_context_get_all_items(self, sample_score_input):
        """Test getting all checklist items from context."""
        context = TemplateContext.from_score_input(sample_score_input)

        all_items = context.get_all_items()

        assert len(all_items) == 2
        assert all(isinstance(item, ChecklistItemContext) for item in all_items)

    def test_template_context_apply_content_limits(self, sample_score_input):
        """Test applying content limits to context."""
        context = TemplateContext.from_score_input(sample_score_input)

        limits = {
            "max_evidence_items": 1,
            "max_description_length": 50
        }

        context.apply_content_limits(limits)

        # Should not raise exception and should apply limits internally

    def test_template_context_add_warning(self, sample_score_input):
        """Test adding warnings to template context."""
        context = TemplateContext.from_score_input(sample_score_input)

        context.add_warning("Test warning")

        assert "Test warning" in context.warnings

    def test_template_context_to_jinja_dict(self, sample_score_input):
        """Test converting context to Jinja2 dictionary."""
        context = TemplateContext.from_score_input(sample_score_input)

        jinja_dict = context.to_jinja_dict()

        assert "repository" in jinja_dict
        assert "total" in jinja_dict
        assert "met_items" in jinja_dict
        assert "partial_items" in jinja_dict
        assert "unmet_items" in jinja_dict
        assert "warnings" in jinja_dict

    def test_template_context_backward_compatibility(self):
        """Test backward compatibility with 'score' vs 'actual_points' keys."""
        # Test data with both 'score' and 'actual_points' keys
        data_mixed = {
            "repository_info": {
                "url": "https://github.com/test/repo.git",
                "commit_sha": "abc123",
                "primary_language": "python"
            },
            "evaluation_result": {
                "checklist_items": [],
                "total_score": 50.0,
                "max_possible_score": 100,
                "score_percentage": 50.0,
                "category_breakdowns": {
                    "old_format": {
                        "score": 25.0,  # Old format
                        "max_points": 50,
                        "percentage": 50.0
                    },
                    "new_format": {
                        "actual_points": 25.0,  # New format
                        "max_points": 50,
                        "percentage": 50.0
                    }
                }
            }
        }

        # Should handle both formats without error
        context = TemplateContext.from_score_input(data_mixed)

        assert "old_format" in context.category_scores
        assert "new_format" in context.category_scores
        assert context.category_scores["old_format"].score == 25.0
        assert context.category_scores["new_format"].score == 25.0

    @pytest.mark.parametrize("status,expected_list", [
        ("met", "met_items"),
        ("partial", "partial_items"),
        ("unmet", "unmet_items"),
        ("unknown", "unmet_items")  # Default case
    ])
    def test_template_context_item_categorization(self, status, expected_list):
        """Test that checklist items are categorized correctly by status."""
        data = {
            "repository_info": {
                "url": "https://github.com/test/repo.git",
                "commit_sha": "abc123",
                "primary_language": "python"
            },
            "evaluation_result": {
                "checklist_items": [
                    {
                        "id": "test_item",
                        "name": "Test Item",
                        "evaluation_status": status,
                        "score": 10.0,
                        "max_points": 10
                    }
                ],
                "total_score": 10.0,
                "max_possible_score": 10,
                "score_percentage": 100.0,
                "category_breakdowns": {}
            }
        }

        context = TemplateContext.from_score_input(data)

        if expected_list == "met_items":
            assert len(context.met_items) == 1
            assert len(context.partial_items) == 0
            assert len(context.unmet_items) == 0
        elif expected_list == "partial_items":
            assert len(context.met_items) == 0
            assert len(context.partial_items) == 1
            assert len(context.unmet_items) == 0
        else:  # unmet_items
            assert len(context.met_items) == 0
            assert len(context.partial_items) == 0
            assert len(context.unmet_items) == 1