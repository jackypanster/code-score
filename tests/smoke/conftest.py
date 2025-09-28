"""
Pytest configuration and fixtures for smoke tests.

This module provides shared fixtures and configuration for the smoke test suite.
"""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def output_directory(project_root: Path) -> Path:
    """Get the output directory for pipeline results."""
    return project_root / "output"


@pytest.fixture(scope="function")
def temp_output_directory() -> Generator[Path, None, None]:
    """
    Create a temporary output directory for testing.

    This fixture provides an isolated output directory for tests
    that need to avoid interfering with real pipeline outputs.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="function")
def clean_output_directory(output_directory: Path) -> Generator[Path, None, None]:
    """
    Provide a clean output directory, restored after test.

    This fixture backs up any existing output files, provides a clean
    directory for testing, and restores the original state afterward.
    """
    # Backup existing files
    backup_dir = None
    if output_directory.exists():
        backup_files = list(output_directory.glob("*"))
        if backup_files:
            backup_dir = tempfile.mkdtemp()
            for file_path in backup_files:
                if file_path.is_file():
                    shutil.copy2(file_path, backup_dir)

    # Ensure clean output directory
    output_directory.mkdir(exist_ok=True)
    for file_path in output_directory.glob("*"):
        if file_path.is_file():
            file_path.unlink()

    try:
        yield output_directory
    finally:
        # Restore backup files
        if backup_dir:
            for file_path in Path(backup_dir).glob("*"):
                if file_path.is_file():
                    shutil.copy2(file_path, output_directory)
            shutil.rmtree(backup_dir)


@pytest.fixture(scope="session")
def target_repository() -> str:
    """Get the target repository URL for testing."""
    return "git@github.com:AIGCInnovatorSpace/code-walker.git"


@pytest.fixture(scope="session")
def expected_output_files() -> list[str]:
    """Get the list of expected output files from the pipeline."""
    return [
        "submission.json",
        "score_input.json",
        "evaluation_report.md"
    ]


@pytest.fixture(scope="function")
def sample_submission_json(temp_output_directory: Path) -> Path:
    """Create a sample submission.json file for testing."""
    content = {
        "schema_version": "1.0.0",
        "repository": {
            "url": "git@github.com:AIGCInnovatorSpace/code-walker.git",
            "commit": "main",
            "language": "python"
        },
        "metrics": {
            "code_quality": {
                "linting_passed": True,
                "issues_count": 0
            },
            "testing": {
                "tests_run": 10,
                "tests_passed": 10
            }
        },
        "execution": {
            "start_time": "2025-09-28T10:00:00Z",
            "end_time": "2025-09-28T10:05:00Z",
            "duration_seconds": 300
        }
    }

    import json
    file_path = temp_output_directory / "submission.json"
    with open(file_path, 'w') as f:
        json.dump(content, f, indent=2)

    return file_path


@pytest.fixture(scope="function")
def sample_score_input_json(temp_output_directory: Path) -> Path:
    """Create a sample score_input.json file for testing."""
    content = {
        "evaluation_result": {
            "total_score": 85,
            "max_score": 100,
            "items": [
                {
                    "id": "code_quality_1",
                    "description": "Code follows linting standards",
                    "score": 10,
                    "max_score": 10,
                    "status": "met"
                }
            ]
        },
        "repository_info": {
            "url": "git@github.com:AIGCInnovatorSpace/code-walker.git",
            "language": "python"
        }
    }

    import json
    file_path = temp_output_directory / "score_input.json"
    with open(file_path, 'w') as f:
        json.dump(content, f, indent=2)

    return file_path


@pytest.fixture(scope="function")
def sample_evaluation_report_md(temp_output_directory: Path) -> Path:
    """Create a sample evaluation_report.md file for testing."""
    content = """# Code Quality Evaluation Report

## Summary
- **Total Score**: 85/100
- **Repository**: git@github.com:AIGCInnovatorSpace/code-walker.git
- **Language**: Python

## Results
- Code Quality: PASS
- Testing: PASS
- Documentation: PARTIAL

## Recommendations
- Improve documentation coverage
- Add more integration tests
"""

    file_path = temp_output_directory / "evaluation_report.md"
    file_path.write_text(content)

    return file_path


@pytest.fixture(scope="function")
def all_sample_files(
    sample_submission_json: Path,
    sample_score_input_json: Path,
    sample_evaluation_report_md: Path
) -> list[Path]:
    """Get all sample output files together."""
    return [
        sample_submission_json,
        sample_score_input_json,
        sample_evaluation_report_md
    ]


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take several minutes)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "contract: marks tests as contract validation tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle slow tests."""
    import pytest

    # Add slow marker to tests that take a long time
    for item in items:
        if "pipeline_execution" in item.name or "timeout" in item.name:
            item.add_marker(pytest.mark.slow)

        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        if "contract" in str(item.fspath):
            item.add_marker(pytest.mark.contract)
