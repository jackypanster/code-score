# Gemini Project Context: Code Score

## Project Overview

This project, named "Code Score," is a command-line tool for automated Git repository quality analysis. It analyzes a given public Git repository and generates comprehensive quality reports. The analysis is performed through a three-stage pipeline:

1.  **Metrics Collection:** Automated linting, testing, and security analysis for various languages (Python, JavaScript/TypeScript, Java, Go).
2.  **Checklist Evaluation:** A 11-item quality scoring system with evidence tracking.
3.  **LLM Report Generation:** AI-powered narrative reports via Gemini.

The project is written in Python 3.11+ and uses the `uv` package manager for dependency management. It is well-structured, with clear separation of concerns between the CLI, metrics pipeline, and LLM components.

## Building and Running

The project uses `uv` for dependency management and running scripts.

### Installation

To install the dependencies, run:

```bash
uv sync
```

### Running the Analysis

The main entry point is the `run_metrics.sh` script. To run a full analysis on a repository:

```bash
./scripts/run_metrics.sh <repository_url>
```

You can also specify a commit SHA:

```bash
./scripts/run_metrics.sh <repository_url> [commit_sha]
```

To generate an AI-powered report with Gemini:

```bash
./scripts/run_metrics.sh <repository_url> --generate-llm-report
```

### Running Tests

The project has a comprehensive test suite using `pytest`. To run all tests:

```bash
uv run pytest
```

To run tests with coverage:

```bash
uv run pytest --cov=src
```

## Development Conventions

### Code Style and Quality

*   **Linting:** The project uses `ruff` for linting. To check for linting errors, run:
    ```bash
    uv run ruff check src/ tests/
    ```
*   **Formatting:** `ruff` is also used for code formatting. To format the code, run:
    ```bash
    uv run ruff format src/ tests/
    ```
*   **Type Checking:** `mypy` is used for static type checking. To run the type checker, use:
    ```bash
    uv run mypy src/
    ```

### Project Structure

The project follows a standard Python project structure:

*   `src/`: Contains the main source code, divided into:
    *   `cli/`: Command-line interface logic.
    *   `metrics/`: The core analysis pipeline.
    *   `llm/`: LLM report generation components.
*   `tests/`: Contains unit, integration, and contract tests.
*   `specs/`: Contains data schemas, contracts, and prompt templates.
*   `scripts/`: Contains the main entry point shell script.

### Key Dependencies

*   `click`: For building the command-line interface.
*   `pydantic` & `jsonschema`: For data validation and schema enforcement.
*   `gitpython`: For interacting with Git repositories.
*   `jinja2`: For templating, likely for the LLM reports.
*   `pytest`, `ruff`, `mypy`: For testing, linting, and type checking.
