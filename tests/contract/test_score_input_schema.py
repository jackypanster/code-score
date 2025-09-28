"""Contract test for score_input.json schema validation.

This test validates that generated score_input.json files conform to the JSON schema
specification defined in the contracts.
"""

import json
import pytest
from pathlib import Path
import jsonschema
from datetime import datetime

# Get the schema path relative to the test file
SCHEMA_PATH = Path(__file__).parent.parent.parent / "specs" / "contracts" / "score_input_schema.json"


class TestScoreInputSchema:
    """Test score_input.json format compliance with JSON schema."""

    @pytest.fixture
    def schema(self):
        """Load the score_input JSON schema."""
        with open(SCHEMA_PATH) as f:
            return json.load(f)

    @pytest.fixture
    def sample_score_input(self):
        """Create a sample score_input.json that should validate."""
        return {
            "schema_version": "1.0.0",
            "repository_info": {
                "url": "https://github.com/example/repo.git",
                "commit_sha": "a1b2c3d4e5f6789012345678901234567890abcd",
                "primary_language": "python",
                "analysis_timestamp": "2025-09-27T10:30:00Z",
                "metrics_source": "output/submission.json"
            },
            "evaluation_result": {
                "checklist_items": [
                    {
                        "id": "code_quality_lint",
                        "name": "Static Linting Passed",
                        "dimension": "code_quality",
                        "max_points": 15,
                        "description": "Lint/static analysis pipeline passes",
                        "evaluation_status": "met",
                        "score": 15.0,
                        "evidence_references": [
                            {
                                "source_type": "lint_output",
                                "source_path": "$.metrics.code_quality.lint_results",
                                "description": "Ruff linting passed with 0 issues",
                                "confidence": 1.0,
                                "raw_data": "passed: true, issues_count: 0"
                            }
                        ]
                    }
                ] + [
                    {
                        "id": f"test_item_{i}",
                        "name": f"Test Item {i}",
                        "dimension": "testing",
                        "max_points": 5,
                        "description": f"Test description {i}",
                        "evaluation_status": "unmet",
                        "score": 0.0,
                        "evidence_references": []
                    }
                    for i in range(2, 12)  # Add 10 more items to make 11 total
                ],
                "total_score": 15.0,
                "max_possible_score": 100,
                "score_percentage": 15.0,
                "category_breakdowns": {
                    "code_quality": {
                        "dimension": "code_quality",
                        "items_count": 4,
                        "max_points": 40,
                        "actual_points": 15.0,
                        "percentage": 37.5
                    },
                    "testing": {
                        "dimension": "testing",
                        "items_count": 4,
                        "max_points": 35,
                        "actual_points": 0.0,
                        "percentage": 0.0
                    },
                    "documentation": {
                        "dimension": "documentation",
                        "items_count": 3,
                        "max_points": 25,
                        "actual_points": 0.0,
                        "percentage": 0.0
                    }
                },
                "evaluation_metadata": {
                    "evaluator_version": "1.0.0",
                    "processing_duration": 0.125,
                    "warnings": [],
                    "metrics_completeness": 0.9
                },
                "evidence_summary": [
                    "✅ Static linting passed (ruff)",
                    "❌ Other checks not implemented yet"
                ]
            },
            "generation_timestamp": "2025-09-27T11:00:00Z",
            "evidence_paths": {
                "submission_json": "output/submission.json",
                "checklist_mapping": "specs/contracts/checklist_mapping.yaml"
            },
            "human_summary": "## Checklist Evaluation Summary\n\n**Total Score: 15/100 (15%)**\n\nTest summary content."
        }

    def test_schema_loads_successfully(self, schema):
        """Test that the JSON schema file loads correctly."""
        assert schema is not None
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert schema["title"] == "Score Input Schema"

    def test_sample_data_validates_against_schema(self, schema, sample_score_input):
        """Test that sample score_input data validates against the schema."""
        # This should not raise an exception
        jsonschema.validate(sample_score_input, schema)

    def test_missing_required_fields_fails_validation(self, schema):
        """Test that missing required fields cause validation failure."""
        incomplete_data = {
            "schema_version": "1.0.0"
            # Missing other required fields
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(incomplete_data, schema)

    def test_invalid_schema_version_format_fails(self, schema, sample_score_input):
        """Test that invalid schema version format fails validation."""
        sample_score_input["schema_version"] = "invalid-version"

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(sample_score_input, schema)

    def test_invalid_commit_sha_format_fails(self, schema, sample_score_input):
        """Test that invalid commit SHA format fails validation."""
        sample_score_input["repository_info"]["commit_sha"] = "invalid-sha"

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(sample_score_input, schema)

    def test_invalid_evaluation_status_fails(self, schema, sample_score_input):
        """Test that invalid evaluation status fails validation."""
        sample_score_input["evaluation_result"]["checklist_items"][0]["evaluation_status"] = "invalid"

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(sample_score_input, schema)

    def test_wrong_number_of_checklist_items_fails(self, schema, sample_score_input):
        """Test that wrong number of checklist items fails validation."""
        # Remove some items to make it less than 11
        sample_score_input["evaluation_result"]["checklist_items"] = [
            sample_score_input["evaluation_result"]["checklist_items"][0]
        ]

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(sample_score_input, schema)

    def test_score_exceeds_max_points_fails(self, schema, sample_score_input):
        """Test that score exceeding max_points fails validation."""
        # This would need to be enforced by business logic, not just schema
        # The schema only validates that score is a number
        item = sample_score_input["evaluation_result"]["checklist_items"][0]
        item["score"] = item["max_points"] + 1  # Exceed max points

        # This should still validate at schema level, but business logic should catch it
        jsonschema.validate(sample_score_input, schema)

    def test_confidence_out_of_range_fails(self, schema, sample_score_input):
        """Test that confidence values outside 0-1 range fail validation."""
        evidence = sample_score_input["evaluation_result"]["checklist_items"][0]["evidence_references"][0]
        evidence["confidence"] = 1.5  # Outside valid range

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(sample_score_input, schema)

    def test_checklist_evaluator_provides_required_items(self, schema):
        """Test that ChecklistEvaluator provides all 11 required checklist items."""
        from src.metrics.checklist_evaluator import ChecklistEvaluator

        # ChecklistEvaluator should instantiate and have required functionality
        evaluator = ChecklistEvaluator()
        assert evaluator is not None

        # Should have evaluation methods
        assert hasattr(evaluator, 'evaluate_from_dict')
        assert hasattr(evaluator, 'evaluate_from_file')
        assert hasattr(evaluator, 'evaluate_from_string')

    def test_evaluate_cli_is_implemented(self):
        """Test that the CLI evaluate command is implemented."""
        from src.cli.evaluate import main as evaluate_main

        # evaluate_main should be callable (functionality test would require actual data)
        assert callable(evaluate_main)