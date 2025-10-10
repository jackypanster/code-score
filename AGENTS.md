# Repository Guidelines

## Project Structure & Module Organization
The core automation lives in `src/cli`, which exposes the command-line entry point and workflow drivers. Analysis logic is split between `src/metrics` for repository inspection and scoring, and `src/llm` for prompt orchestration. Reference schemas and templates sit under `specs/`, human-readable docs in `docs/`, and executable helpers in `scripts/` (notably `run_metrics.sh`). Keep generated artifacts in `output/`; temporary scratch work belongs there so the repository root stays tidy. Tests are organized in `tests/` with unit, integration, and contract coverage mirroring the module layout.

## Build, Test, and Development Commands
Use UV for all dependency workflows: `uv sync` installs project and dev requirements. Run the full pipeline locally with `./scripts/run_metrics.sh https://github.com/user/repo.git`; add `--generate-llm-report` when validating Gemini output. During development, `uv run python -m src.cli.main --help` is the quickest way to inspect CLI options. Quality gates are enforced via `uv run ruff check src/ tests/`, formatting with `uv run ruff format src/ tests/`, type safety with `uv run mypy src/`, and the primary test suite via `uv run pytest`.

## Coding Style & Naming Conventions
Python 3.11 features and typing are required; prefer dataclasses and enums when modeling structured results. Adhere to the Ruff configuration (100-character lines, selected lint rules) and run the formatter before submitting changes. Modules and packages use `snake_case`, classes `PascalCase`, and constants `UPPER_SNAKE_CASE`. CLI options follow long-form kebab-case flags to match existing commands. Keep public docstrings concise, describing side effects and return payloads.

## Testing Guidelines
All new code must land with tests; mirror the existing `Test*` class and `test_*` function patterns defined in `pyproject.toml`. Mark long-running scenarios with `@pytest.mark.slow` and integration boundaries with `@pytest.mark.integration` so the default suite stays fast. The project enforces coverage gathering via `--cov=src`; aim to keep line coverage at or above the current report shown in `htmlcov/index.html`. For focused debugging, `uv run pytest tests/unit/test_cli_main.py -k scenario` is the recommended pattern.

## Commit & Pull Request Guidelines
Follow the repository’s conventional commit history (`feat:`, `docs:`, `chore:`, optional scopes) so automated changelogs stay coherent. Each pull request should summarize the change, note affected pipelines (metrics, checklist, LLM), and link any tracked issues. Attach command outputs or screenshots when touching reporting templates, and confirm lint, type-check, and test passes in the description. Keep branches short-lived and prefer rebasing over merge commits before requesting review.
