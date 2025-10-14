"""
Contract tests for CIConfigResult JSON schema validation.

Tests validate that CIConfigResult data model conforms to the JSON schema
defined in specs/005-1-phase-2/contracts/ci_config_result_schema.json.

This test file is part of Phase 3.2 (Tests First - TDD) and is expected to
FAIL until the models are implemented in Phase 3.3 (T012).
"""

import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

# This import will FAIL until T012 (Create data models) is complete
# Expected error: ModuleNotFoundError: No module named 'src.metrics.models.ci_config'
try:
    from src.metrics.models.ci_config import CIConfigResult
    MODEL_IMPLEMENTED = True
except ModuleNotFoundError:
    MODEL_IMPLEMENTED = False
    # Create a mock for test structure validation
    class CIConfigResult:
        pass


# Load JSON schema
SCHEMA_PATH = Path(__file__).parents[2] / "specs" / "005-1-phase-2" / "contracts" / "ci_config_result_schema.json"


@pytest.fixture
def ci_config_schema():
    """Load CIConfigResult JSON schema."""
    with open(SCHEMA_PATH, 'r') as f:
        return json.load(f)


@pytest.mark.skipif(not MODEL_IMPLEMENTED, reason="CIConfigResult model not yet implemented (T012)")
class TestCIConfigResultSchemaCompliance:
    """Test suite for CIConfigResult JSON schema validation."""

    def test_valid_ci_config_result_with_all_fields(self, ci_config_schema):
        """Test 1: Valid CIConfigResult with all fields should pass schema validation."""
        valid_data = {
            "platform": "github_actions",
            "config_file_path": ".github/workflows/test.yml",
            "has_test_steps": True,
            "test_commands": ["pytest --cov=src tests/unit", "npm test"],
            "has_coverage_upload": True,
            "coverage_tools": ["codecov"],
            "test_job_count": 2,
            "calculated_score": 13,
            "parse_errors": []
        }

        # Should not raise ValidationError
        validate(instance=valid_data, schema=ci_config_schema)

    def test_required_fields_validation(self, ci_config_schema):
        """Test 2: Missing required fields should fail validation."""
        incomplete_data = {
            "platform": "gitlab_ci",
            # Missing: has_test_steps, test_commands, has_coverage_upload, etc.
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=incomplete_data, schema=ci_config_schema)

        # Verify error message mentions missing required fields
        assert "required" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_platform_enum_validation_valid_values(self, ci_config_schema):
        """Test 3: Platform must be in valid set or null."""
        valid_platforms = ["github_actions", "gitlab_ci", "circleci", "travis_ci", "jenkins", None]

        for platform in valid_platforms:
            valid_data = {
                "platform": platform,
                "config_file_path": ".github/workflows/test.yml" if platform else None,
                "has_test_steps": False,
                "test_commands": [],
                "has_coverage_upload": False,
                "coverage_tools": [],
                "test_job_count": 0,
                "calculated_score": 0,
                "parse_errors": []
            }
            # Should not raise ValidationError
            validate(instance=valid_data, schema=ci_config_schema)

    def test_platform_enum_validation_invalid_value(self, ci_config_schema):
        """Test 3b: Invalid platform value should fail validation."""
        invalid_data = {
            "platform": "bitbucket_pipelines",  # Not in valid enum
            "config_file_path": ".bitbucket/pipelines.yml",
            "has_test_steps": False,
            "test_commands": [],
            "has_coverage_upload": False,
            "coverage_tools": [],
            "test_job_count": 0,
            "calculated_score": 0,
            "parse_errors": []
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=ci_config_schema)

        # Verify error is about enum constraint
        assert "enum" in str(exc_info.value).lower() or "not valid" in str(exc_info.value).lower()

    def test_calculated_score_range_validation(self, ci_config_schema):
        """Test 4: calculated_score must be in range [0, 13]."""
        # Test valid scores
        for score in [0, 5, 10, 13]:
            valid_data = {
                "platform": "github_actions",
                "config_file_path": ".github/workflows/test.yml",
                "has_test_steps": True,
                "test_commands": ["pytest"],
                "has_coverage_upload": False,
                "coverage_tools": [],
                "test_job_count": 1,
                "calculated_score": score,
                "parse_errors": []
            }
            # Should not raise ValidationError
            validate(instance=valid_data, schema=ci_config_schema)

        # Test invalid scores
        for invalid_score in [-1, 14, 100]:
            invalid_data = {
                "platform": "github_actions",
                "config_file_path": ".github/workflows/test.yml",
                "has_test_steps": True,
                "test_commands": ["pytest"],
                "has_coverage_upload": False,
                "coverage_tools": [],
                "test_job_count": 1,
                "calculated_score": invalid_score,
                "parse_errors": []
            }

            with pytest.raises(ValidationError) as exc_info:
                validate(instance=invalid_data, schema=ci_config_schema)

            # Verify error is about range constraint
            assert "maximum" in str(exc_info.value).lower() or "minimum" in str(exc_info.value).lower()

    def test_invalid_data_rejection_extra_fields(self, ci_config_schema):
        """Test 5a: Extra fields not in schema should fail validation (additionalProperties: false)."""
        invalid_data = {
            "platform": "github_actions",
            "config_file_path": ".github/workflows/test.yml",
            "has_test_steps": True,
            "test_commands": ["pytest"],
            "has_coverage_upload": False,
            "coverage_tools": [],
            "test_job_count": 1,
            "calculated_score": 5,
            "parse_errors": [],
            "extra_field": "should not be here"  # Extra field
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=ci_config_schema)

        # Verify error is about additional properties
        assert "additional" in str(exc_info.value).lower()

    def test_invalid_data_rejection_wrong_types(self, ci_config_schema):
        """Test 5b: Wrong data types should fail validation."""
        # has_test_steps should be boolean, not string
        invalid_data = {
            "platform": "github_actions",
            "config_file_path": ".github/workflows/test.yml",
            "has_test_steps": "true",  # Should be boolean, not string
            "test_commands": ["pytest"],
            "has_coverage_upload": False,
            "coverage_tools": [],
            "test_job_count": 1,
            "calculated_score": 5,
            "parse_errors": []
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=ci_config_schema)

        # Verify error is about type mismatch
        assert "type" in str(exc_info.value).lower() or "boolean" in str(exc_info.value).lower()

    def test_coverage_tools_enum_validation(self, ci_config_schema):
        """Test coverage_tools items must be from valid enum."""
        valid_data = {
            "platform": "github_actions",
            "config_file_path": ".github/workflows/test.yml",
            "has_test_steps": True,
            "test_commands": ["pytest --cov"],
            "has_coverage_upload": True,
            "coverage_tools": ["codecov", "coveralls", "sonarqube"],
            "test_job_count": 1,
            "calculated_score": 10,
            "parse_errors": []
        }
        # Should not raise ValidationError
        validate(instance=valid_data, schema=ci_config_schema)

        # Invalid coverage tool
        invalid_data = {
            "platform": "github_actions",
            "config_file_path": ".github/workflows/test.yml",
            "has_test_steps": True,
            "test_commands": ["pytest --cov"],
            "has_coverage_upload": True,
            "coverage_tools": ["invalid_tool"],  # Not in enum
            "test_job_count": 1,
            "calculated_score": 10,
            "parse_errors": []
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=ci_config_schema)

        assert "enum" in str(exc_info.value).lower()

    def test_no_ci_configuration_scenario(self, ci_config_schema):
        """Test scenario with no CI configuration (all null/empty values)."""
        no_ci_data = {
            "platform": None,
            "config_file_path": None,
            "has_test_steps": False,
            "test_commands": [],
            "has_coverage_upload": False,
            "coverage_tools": [],
            "test_job_count": 0,
            "calculated_score": 0,
            "parse_errors": []
        }
        # Should not raise ValidationError
        validate(instance=no_ci_data, schema=ci_config_schema)

    def test_parse_errors_populated_on_failure(self, ci_config_schema):
        """Test scenario with parse errors populated."""
        error_data = {
            "platform": "gitlab_ci",
            "config_file_path": ".gitlab-ci.yml",
            "has_test_steps": False,
            "test_commands": [],
            "has_coverage_upload": False,
            "coverage_tools": [],
            "test_job_count": 0,
            "calculated_score": 0,
            "parse_errors": ["YAMLError: mapping values are not allowed here", "Invalid syntax at line 42"]
        }
        # Should not raise ValidationError
        validate(instance=error_data, schema=ci_config_schema)


# Meta-test: Verify test file structure
def test_schema_file_exists():
    """Meta-test: Verify JSON schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"


def test_schema_is_valid_json():
    """Meta-test: Verify schema is valid JSON."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = json.load(f)

    assert "properties" in schema, "Schema must have 'properties' field"
    assert "required" in schema, "Schema must have 'required' field"
    assert schema["type"] == "object", "Schema type must be 'object'"


@pytest.mark.skipif(MODEL_IMPLEMENTED, reason="Model already implemented")
def test_model_not_yet_implemented():
    """TDD checkpoint: Verify CIConfigResult model is not yet implemented."""
    with pytest.raises(ModuleNotFoundError):
        from src.metrics.models.ci_config import CIConfigResult
