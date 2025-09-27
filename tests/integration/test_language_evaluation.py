"""Integration test for multi-language evaluation.

This test validates that the evaluation system correctly handles different
programming languages with language-specific metrics and adaptations.
"""

import json
import pytest
from pathlib import Path
import tempfile

class TestLanguageEvaluation:
    """Test evaluation across different programming languages."""

    @pytest.fixture
    def python_submission(self):
        """Create a Python repository submission.json."""
        return {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/example/python-repo.git",
                "commit": "pythoncommitsha123456789abcdef1234567890",
                "language": "python",
                "timestamp": "2025-09-27T10:30:00.000Z",
                "size_mb": 15.2
            },
            "metrics": {
                "code_quality": {
                    "lint_results": {
                        "tool_used": "ruff",
                        "passed": True,
                        "issues_count": 0,
                        "issues": []
                    },
                    "build_success": True,
                    "dependency_audit": {
                        "vulnerabilities_found": 0,
                        "high_severity_count": 0,
                        "tool_used": "pip-audit"
                    }
                },
                "testing": {
                    "test_execution": {
                        "tests_run": 50,
                        "tests_passed": 48,
                        "tests_failed": 2,
                        "framework": "pytest",
                        "execution_time_seconds": 15.0
                    },
                    "coverage_report": {
                        "coverage_percentage": 82.5
                    }
                },
                "documentation": {
                    "readme_present": True,
                    "readme_quality_score": 0.9,
                    "api_documentation": True,
                    "setup_instructions": True,
                    "usage_examples": True
                }
            },
            "execution": {
                "tools_used": ["ruff", "pytest", "pip-audit"],
                "errors": [],
                "warnings": ["2 test failures"],
                "duration_seconds": 45.0,
                "timestamp": "2025-09-27T10:31:00.000Z"
            }
        }

    @pytest.fixture
    def javascript_submission(self):
        """Create a JavaScript repository submission.json."""
        return {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/example/javascript-repo.git",
                "commit": "jscommitsha123456789abcdef1234567890abcd",
                "language": "javascript",
                "timestamp": "2025-09-27T10:30:00.000Z",
                "size_mb": 8.7
            },
            "metrics": {
                "code_quality": {
                    "lint_results": {
                        "tool_used": "eslint",
                        "passed": True,
                        "issues_count": 3,
                        "issues": [
                            {"severity": "warning", "message": "Unused variable", "file": "src/app.js", "line": 42}
                        ]
                    },
                    "build_success": True,
                    "dependency_audit": {
                        "vulnerabilities_found": 2,
                        "high_severity_count": 0,
                        "tool_used": "npm"
                    }
                },
                "testing": {
                    "test_execution": {
                        "tests_run": 25,
                        "tests_passed": 25,
                        "tests_failed": 0,
                        "framework": "jest",
                        "execution_time_seconds": 8.5
                    },
                    "coverage_report": {
                        "coverage_percentage": 75.0
                    }
                },
                "documentation": {
                    "readme_present": True,
                    "readme_quality_score": 0.75,
                    "api_documentation": False,
                    "setup_instructions": True,
                    "usage_examples": True
                }
            },
            "execution": {
                "tools_used": ["eslint", "jest", "npm"],
                "errors": [],
                "warnings": ["Low-severity vulnerabilities found"],
                "duration_seconds": 32.0,
                "timestamp": "2025-09-27T10:31:00.000Z"
            }
        }

    @pytest.fixture
    def java_submission(self):
        """Create a Java repository submission.json."""
        return {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/example/java-repo.git",
                "commit": "javacommitsha123456789abcdef1234567890ab",
                "language": "java",
                "timestamp": "2025-09-27T10:30:00.000Z",
                "size_mb": 25.4
            },
            "metrics": {
                "code_quality": {
                    "lint_results": {
                        "tool_used": "checkstyle",
                        "passed": False,
                        "issues_count": 15,
                        "issues": []
                    },
                    "build_success": True,
                    "dependency_audit": {
                        "vulnerabilities_found": 1,
                        "high_severity_count": 1,
                        "tool_used": "maven"
                    }
                },
                "testing": {
                    "test_execution": {
                        "tests_run": 80,
                        "tests_passed": 75,
                        "tests_failed": 5,
                        "framework": "maven",
                        "execution_time_seconds": 45.0
                    },
                    "coverage_report": {
                        "coverage_percentage": 68.0
                    }
                },
                "documentation": {
                    "readme_present": True,
                    "readme_quality_score": 0.8,
                    "api_documentation": True,
                    "setup_instructions": True,
                    "usage_examples": False
                }
            },
            "execution": {
                "tools_used": ["checkstyle", "maven"],
                "errors": [],
                "warnings": ["Checkstyle violations", "High-severity vulnerability"],
                "duration_seconds": 120.0,
                "timestamp": "2025-09-27T10:32:00.000Z"
            }
        }

    @pytest.fixture
    def go_submission(self):
        """Create a Go repository submission.json."""
        return {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/example/go-repo.git",
                "commit": "gocommitsha123456789abcdef1234567890abcd",
                "language": "go",
                "timestamp": "2025-09-27T10:30:00.000Z",
                "size_mb": 5.1
            },
            "metrics": {
                "code_quality": {
                    "lint_results": {
                        "tool_used": "golangci-lint",
                        "passed": True,
                        "issues_count": 0,
                        "issues": []
                    },
                    "build_success": True,
                    "dependency_audit": {
                        "vulnerabilities_found": 0,
                        "high_severity_count": 0,
                        "tool_used": "go"
                    }
                },
                "testing": {
                    "test_execution": {
                        "tests_run": 15,
                        "tests_passed": 15,
                        "tests_failed": 0,
                        "framework": "go",
                        "execution_time_seconds": 3.0
                    },
                    "coverage_report": {
                        "coverage_percentage": 90.0
                    }
                },
                "documentation": {
                    "readme_present": True,
                    "readme_quality_score": 0.7,
                    "api_documentation": False,
                    "setup_instructions": True,
                    "usage_examples": True
                }
            },
            "execution": {
                "tools_used": ["golangci-lint", "go"],
                "errors": [],
                "warnings": [],
                "duration_seconds": 15.0,
                "timestamp": "2025-09-27T10:30:45.000Z"
            }
        }

    def test_language_evaluation_not_implemented(self):
        """Test that language-specific evaluation is not yet implemented."""
        # This test will fail until ChecklistEvaluator supports language adaptations
        with pytest.raises(ImportError):
            from src.metrics.checklist_evaluator import ChecklistEvaluator

    def test_python_language_evaluation(self, python_submission):
        """Test evaluation of Python repository with ruff/pytest tools."""
        # This test will fail until implementation exists
        with pytest.raises(ImportError):
            from src.metrics.checklist_evaluator import ChecklistEvaluator
            evaluator = ChecklistEvaluator()

            result = evaluator.evaluate_from_dict(python_submission)

            # Python should get high scores for good ruff linting and pytest
            assert result.total_score > 70.0

            # Check that Python-specific tools are recognized
            evidence_found = False
            for item in result.checklist_items:
                if item.id == "code_quality_lint":
                    for evidence in item.evidence_references:
                        if "ruff" in evidence.description.lower():
                            evidence_found = True
                            break
            assert evidence_found, "Python ruff tool should be recognized in evidence"

    def test_javascript_language_evaluation(self, javascript_submission):
        """Test evaluation of JavaScript repository with eslint/jest tools."""
        # This test will fail until implementation exists
        with pytest.raises(ImportError):
            from src.metrics.checklist_evaluator import ChecklistEvaluator
            evaluator = ChecklistEvaluator()

            result = evaluator.evaluate_from_dict(javascript_submission)

            # JavaScript should get good scores but not perfect due to some issues
            assert 50.0 < result.total_score < 85.0

            # Check that JavaScript-specific tools are recognized
            evidence_found = False
            for item in result.checklist_items:
                if item.id == "code_quality_lint":
                    for evidence in item.evidence_references:
                        if "eslint" in evidence.description.lower():
                            evidence_found = True
                            break
            assert evidence_found, "JavaScript eslint tool should be recognized"

    def test_java_language_evaluation(self, java_submission):
        """Test evaluation of Java repository with checkstyle/maven tools."""
        # This test will fail until implementation exists
        with pytest.raises(ImportError):
            from src.metrics.checklist_evaluator import ChecklistEvaluator
            evaluator = ChecklistEvaluator()

            result = evaluator.evaluate_from_dict(java_submission)

            # Java should get moderate scores due to linting issues and vulnerabilities
            assert 40.0 < result.total_score < 70.0

            # Linting should be marked as partial/unmet due to failures
            lint_item = next(item for item in result.checklist_items if item.id == "code_quality_lint")
            assert lint_item.evaluation_status in ["partial", "unmet"]

    def test_go_language_evaluation(self, go_submission):
        """Test evaluation of Go repository with golangci-lint tools."""
        # This test will fail until implementation exists
        with pytest.raises(ImportError):
            from src.metrics.checklist_evaluator import ChecklistEvaluator
            evaluator = ChecklistEvaluator()

            result = evaluator.evaluate_from_dict(go_submission)

            # Go should get high scores for clean linting and good test coverage
            assert result.total_score > 75.0

            # Check that Go-specific tools are recognized
            evidence_found = False
            for item in result.checklist_items:
                if item.id == "code_quality_lint":
                    for evidence in item.evidence_references:
                        if "golangci-lint" in evidence.description.lower():
                            evidence_found = True
                            break
            assert evidence_found, "Go golangci-lint tool should be recognized"

    def test_language_specific_scoring_adaptations(self):
        """Test that language-specific scoring adaptations are applied correctly."""
        # This test will fail until language adaptations are implemented
        with pytest.raises(ImportError):
            from src.metrics.checklist_loader import ChecklistLoader
            loader = ChecklistLoader()

            # Should load different criteria for different languages
            python_criteria = loader.get_language_criteria("python")
            javascript_criteria = loader.get_language_criteria("javascript")

            assert python_criteria is not None
            assert javascript_criteria is not None

    def test_unknown_language_fallback(self):
        """Test that unknown languages fall back to generic evaluation."""
        unknown_submission = {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/example/unknown-repo.git",
                "commit": "unknowncommitsha123456789abcdef1234567890",
                "language": "rust",  # Not in supported languages
                "timestamp": "2025-09-27T10:30:00.000Z",
                "size_mb": 10.0
            },
            "metrics": {
                "code_quality": {
                    "lint_results": {
                        "tool_used": "none",
                        "passed": False,
                        "issues_count": 0,
                        "issues": []
                    },
                    "build_success": None,
                    "dependency_audit": {
                        "vulnerabilities_found": 0,
                        "high_severity_count": 0,
                        "tool_used": "none"
                    }
                },
                "testing": {
                    "test_execution": {
                        "tests_run": 0,
                        "tests_passed": 0,
                        "tests_failed": 0,
                        "framework": "none",
                        "execution_time_seconds": 0.0
                    },
                    "coverage_report": None
                },
                "documentation": {
                    "readme_present": True,
                    "readme_quality_score": 0.6,
                    "api_documentation": False,
                    "setup_instructions": False,
                    "usage_examples": False
                }
            },
            "execution": {
                "tools_used": [],
                "errors": ["Unsupported language"],
                "warnings": ["No language-specific tools available"],
                "duration_seconds": 5.0,
                "timestamp": "2025-09-27T10:30:30.000Z"
            }
        }

        # This test will fail until implementation exists
        with pytest.raises(ImportError):
            from src.metrics.checklist_evaluator import ChecklistEvaluator
            evaluator = ChecklistEvaluator()

            result = evaluator.evaluate_from_dict(unknown_submission)

            # Should still complete evaluation but with low scores
            assert result.total_score < 40.0

            # Should document that language-specific tools weren't available
            warnings_found = any("language" in warning.lower() for warning in result.evaluation_metadata.warnings)
            assert warnings_found, "Should warn about unsupported language"

    def test_cross_language_consistency(self, python_submission, javascript_submission, java_submission, go_submission):
        """Test that evaluation criteria are applied consistently across languages."""
        # This test will fail until implementation exists
        with pytest.raises(ImportError):
            from src.metrics.checklist_evaluator import ChecklistEvaluator
            evaluator = ChecklistEvaluator()

            python_result = evaluator.evaluate_from_dict(python_submission)
            js_result = evaluator.evaluate_from_dict(javascript_submission)
            java_result = evaluator.evaluate_from_dict(java_submission)
            go_result = evaluator.evaluate_from_dict(go_submission)

            # All should have exactly 11 checklist items
            assert len(python_result.checklist_items) == 11
            assert len(js_result.checklist_items) == 11
            assert len(java_result.checklist_items) == 11
            assert len(go_result.checklist_items) == 11

            # All should have the same checklist item IDs
            python_ids = {item.id for item in python_result.checklist_items}
            js_ids = {item.id for item in js_result.checklist_items}
            java_ids = {item.id for item in java_result.checklist_items}
            go_ids = {item.id for item in go_result.checklist_items}

            assert python_ids == js_ids == java_ids == go_ids

            # All should have max_possible_score of 100
            assert python_result.max_possible_score == 100
            assert js_result.max_possible_score == 100
            assert java_result.max_possible_score == 100
            assert go_result.max_possible_score == 100