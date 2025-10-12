"""
Contract tests for the programmatic evaluation API.

Validates that the evaluate_submission() function in src/cli/evaluate.py complies
with the contract specification defined in specs/003-tests-integration-test/contracts/programmatic_api.py.

These tests verify:
- Function signature and parameter types
- Return type contracts (ValidationResult vs EvaluationResult)
- Exception contracts (what exceptions are raised when)

NOTE: These tests will FAIL until T008-T011 are complete (function extraction).
"""

import inspect
from pathlib import Path
from typing import Literal, get_args, get_origin

import pytest

from src.cli.models import EvaluationResult, ValidationResult


class TestProgrammaticAPIContract:
    """Contract tests for evaluate_submission() function."""

    def test_evaluate_submission_function_exists(self):
        """Verify evaluate_submission() function can be imported."""
        # This test will FAIL until T008 completes (function extraction)
        try:
            from src.cli.evaluate import evaluate_submission

            assert callable(evaluate_submission)
        except ImportError as e:
            pytest.fail(
                f"Cannot import evaluate_submission: {e}. "
                "This is expected until T008 (function extraction) completes."
            )

    def test_function_signature(self):
        """Verify function signature matches contract specification."""
        # This test will FAIL until T008 completes
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted (T008 not complete)")

        sig = inspect.signature(evaluate_submission)

        # Verify parameter names
        expected_params = [
            "submission_file",
            "output_dir",
            "format",
            "checklist_config",
            "evidence_dir",
            "validate_only",
            "verbose",
            "quiet",
        ]
        actual_params = list(sig.parameters.keys())
        assert (
            actual_params == expected_params
        ), f"Expected params {expected_params}, got {actual_params}"

        # Verify parameter types
        params = sig.parameters

        # submission_file: str | Path (required, no default)
        assert params["submission_file"].default == inspect.Parameter.empty
        submission_file_annotation = params["submission_file"].annotation
        # Type should be str | Path or Union[str, Path]
        assert (
            "str" in str(submission_file_annotation)
            and "Path" in str(submission_file_annotation)
        ) or submission_file_annotation in (str, Path)

        # output_dir: str | Path = "output"
        assert params["output_dir"].default == "output"

        # format: Literal["json", "markdown", "both"] = "both"
        assert params["format"].default == "both"

        # checklist_config: str | Path | None = None
        assert params["checklist_config"].default is None

        # evidence_dir: str | Path = "evidence"
        assert params["evidence_dir"].default == "evidence"

        # validate_only: bool = False
        assert params["validate_only"].default is False
        assert params["validate_only"].annotation == bool

        # verbose: bool = False
        assert params["verbose"].default is False
        assert params["verbose"].annotation == bool

        # quiet: bool = False
        assert params["quiet"].default is False
        assert params["quiet"].annotation == bool

    def test_validate_only_returns_validation_result(self):
        """Verify validate_only=True returns ValidationResult type."""
        # This test will FAIL until T011 completes (return object construction)
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted (T008 not complete)")

        # Check return type annotation
        sig = inspect.signature(evaluate_submission)
        return_annotation = sig.return_annotation

        # Return type should be ValidationResult | EvaluationResult
        # or Union[ValidationResult, EvaluationResult]
        assert (
            "ValidationResult" in str(return_annotation)
            and "EvaluationResult" in str(return_annotation)
        )

        # NOTE: Actual runtime behavior will be tested in integration tests (T017)
        # This contract test only verifies the type signature

    def test_normal_mode_returns_evaluation_result(self):
        """Verify validate_only=False returns EvaluationResult type."""
        # This test will FAIL until T011 completes (return object construction)
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted (T008 not complete)")

        # Check return type annotation
        sig = inspect.signature(evaluate_submission)
        return_annotation = sig.return_annotation

        # Return type should include EvaluationResult
        assert "EvaluationResult" in str(return_annotation)

        # NOTE: Actual runtime behavior will be tested in integration tests (T017)
        # This contract test only verifies the type signature

    def test_exception_types_importable(self):
        """Verify custom exceptions can be imported."""
        from src.cli.exceptions import (
            EvaluationFileSystemError,
            QualityGateException,
        )

        # Verify exceptions exist
        assert QualityGateException is not None
        assert EvaluationFileSystemError is not None

        # Verify inheritance
        assert issubclass(QualityGateException, Exception)
        assert issubclass(EvaluationFileSystemError, Exception)

    def test_return_models_importable(self):
        """Verify return models can be imported."""
        from src.cli.models import EvaluationResult, ValidationResult

        # Verify models exist
        assert ValidationResult is not None
        assert EvaluationResult is not None

        # Verify they are Pydantic models (have model_validate method)
        assert hasattr(ValidationResult, "model_validate")
        assert hasattr(EvaluationResult, "model_validate")


class TestParameterContracts:
    """Additional contract tests for parameter handling."""

    def test_submission_file_accepts_string_and_path(self):
        """Verify submission_file parameter accepts both str and Path."""
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted")

        sig = inspect.signature(evaluate_submission)
        param = sig.parameters["submission_file"]

        # Verify annotation includes both str and Path
        annotation_str = str(param.annotation)
        assert "str" in annotation_str or "Path" in annotation_str

    def test_format_parameter_is_literal(self):
        """Verify format parameter uses Literal type hint."""
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted")

        sig = inspect.signature(evaluate_submission)
        param = sig.parameters["format"]

        # Verify annotation mentions Literal or has valid default
        assert param.default in ["json", "markdown", "both"]

    def test_optional_parameters_have_defaults(self):
        """Verify optional parameters have appropriate defaults."""
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted")

        sig = inspect.signature(evaluate_submission)

        # These should have defaults
        params_with_defaults = {
            "output_dir": "output",
            "format": "both",
            "checklist_config": None,
            "evidence_dir": "evidence",
            "validate_only": False,
            "verbose": False,
            "quiet": False,
        }

        for param_name, expected_default in params_with_defaults.items():
            actual_default = sig.parameters[param_name].default
            assert (
                actual_default == expected_default
            ), f"Parameter {param_name}: expected default {expected_default}, got {actual_default}"

    def test_submission_file_is_required(self):
        """Verify submission_file parameter has no default (required)."""
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted")

        sig = inspect.signature(evaluate_submission)
        param = sig.parameters["submission_file"]

        # Verify no default value
        assert param.default == inspect.Parameter.empty


class TestDocstringContract:
    """Contract tests for function documentation."""

    def test_function_has_docstring(self):
        """Verify evaluate_submission() has comprehensive docstring."""
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted")

        assert evaluate_submission.__doc__ is not None
        assert len(evaluate_submission.__doc__) > 100

        docstring = evaluate_submission.__doc__

        # Verify key sections exist
        assert "Args:" in docstring or "Parameters:" in docstring
        assert "Returns:" in docstring
        assert "Raises:" in docstring

        # Verify exception types documented
        assert "QualityGateException" in docstring
        assert "EvaluationFileSystemError" in docstring
        assert "FileNotFoundError" in docstring
        assert "ValueError" in docstring

    def test_docstring_documents_return_types(self):
        """Verify docstring documents both return types."""
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted")

        docstring = evaluate_submission.__doc__

        # Verify both return types documented
        assert "ValidationResult" in docstring
        assert "EvaluationResult" in docstring
        assert "validate_only" in docstring

    def test_docstring_includes_examples(self):
        """Verify docstring includes usage examples."""
        try:
            from src.cli.evaluate import evaluate_submission
        except ImportError:
            pytest.skip("Function not yet extracted")

        docstring = evaluate_submission.__doc__

        # Verify examples section exists
        assert "Example" in docstring or ">>>" in docstring
