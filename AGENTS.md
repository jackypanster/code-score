# Repository Guidelines

## Project Structure & Module Organization
- `src/cli` orchestrates the CLI entry point and workflow drivers.
- `src/metrics` inspects repositories and computes scoring signals.
- `src/llm` manages prompt composition and downstream LLM interactions.
- `specs/` contains reference schemas and templated inputs.
- `docs/` hosts user-facing documentation and playbooks.
- `scripts/` offers runnable helpers such as `run_metrics.sh`.
- `output/` stores generated artifacts; keep transient files here.
- `tests/` mirrors the module layout with unit, integration, and contract suites.

## Build, Test, and Development Commands
- `uv sync` installs project and development dependencies.
- `uv run python -m src.cli.main --help` lists available CLI workflows.
- `./scripts/run_metrics.sh https://github.com/user/repo.git` runs the end-to-end pipeline; add `--generate-llm-report` to validate Gemini output.
- `uv run ruff check src/ tests/` enforces lint rules.
- `uv run ruff format src/ tests/` applies repository formatting.
- `uv run mypy src/` validates typing.
- `uv run pytest --cov=src` executes the test suite with coverage.

## Coding Style & Naming Conventions
- Target Python 3.11 features, static typing, and Ruff’s 100-character line limit.
- Prefer dataclasses and enums when representing structured outcomes.
- Name modules and packages with `snake_case`, classes with `PascalCase`, constants with `UPPER_SNAKE_CASE`.
- Expose CLI flags in long-form kebab-case (for example, `--generate-llm-report`).
- Keep public docstrings concise while explaining side effects and returned payloads.

## Testing Guidelines
- Use pytest; organize tests under `tests/` to mirror source modules.
- Name files `test_*.py` and classes `Test*` to satisfy discovery.
- Label extended scenarios with `@pytest.mark.slow`; mark cross-service flows with `@pytest.mark.integration`.
- Run targeted slices with `uv run pytest tests/unit/test_cli_main.py -k pattern`.
- Maintain coverage at or above the current baseline reported in `htmlcov/index.html`.

## Commit & Pull Request Guidelines
- Follow conventional commits (`feat:`, `docs:`, `chore:scope`) to keep changelogs consistent.
- Keep branches short-lived and rebase before requesting review.
- Summarize PR impact on metrics, checklist, and LLM pipelines; link any tracked issues.
- Attach command outputs or screenshots when touching reporting templates.
- Confirm lint, type-check, and test runs in the PR description before merge.
