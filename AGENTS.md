# Repository Guidelines

## Project Structure & Module Organization
- `src/cli` drives CLI workflows; treat it as the orchestration layer for end-to-end runs.
- `src/metrics` houses signal computation and repository inspection utilities.
- `src/llm` manages prompt assembly and downstream LLM calls; keep API keys out of source.
- `tests/` mirrors the source tree with unit, integration, and contract suites; add new tests beside the code they cover.
- `specs/`, `docs/`, `scripts/`, and `output/` hold reference schemas, user docs, helper scripts, and generated artifacts respectively.

## Build, Test, and Development Commands
- `uv sync` — install project and dev dependencies pinned in `pyproject.toml`.
- `uv run python -m src.cli.main --help` — list available CLI workflows for quick discovery.
- `./scripts/run_metrics.sh https://github.com/user/repo.git [--generate-llm-report]` — execute the full scoring pipeline (add the flag to validate Gemini output).
- `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/` — lint and format code.
- `uv run mypy src/` — enforce typing contracts.
- `uv run pytest --cov=src` — run tests with coverage reporting.

## Coding Style & Naming Conventions
- Target Python 3.11 features, 4-space indentation, and Ruff’s 100-character line width.
- Prefer dataclasses and enums for structured payloads; keep module names `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Expose CLI flags in long-form kebab-case (for example, `--generate-llm-report`).
- Maintain concise docstrings that describe side effects and return values.

## Testing Guidelines
- Use pytest; organize files as `tests/<area>/test_*.py` with classes named `Test*`.
- Mark slow scenarios with `@pytest.mark.slow` and external integrations with `@pytest.mark.integration`.
- Maintain coverage at or above the current baseline in `htmlcov/index.html`; regenerate via `uv run pytest --cov=src`.
- For targeted runs, use `uv run pytest tests/unit/test_cli_main.py -k pattern`.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (e.g., `feat:`, `docs:`, `chore:scope`) for changelog clarity.
- Rebase feature branches before review; keep diffs focused and short-lived.
- PR descriptions should summarize impacts on metrics, checklist, and LLM pipelines, link related Linear issues, and attach relevant command outputs or screenshots.
- Confirm lint, type-check, and test runs in every PR summary before requesting merge.

## Agent Workflow Tips
- Store temporary artifacts in `output/` to keep the workspace clean.
- Avoid destructive git commands (`git reset --hard`) unless the user explicitly instructs otherwise.
- When unsure about repository conventions, inspect existing modules in `src/` for patterns before introducing new abstractions.
