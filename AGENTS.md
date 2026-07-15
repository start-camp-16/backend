# Repository Guidelines

## Project Structure & Module Organization

Application code lives in `app/`. Keep domain behavior in its matching package, such as
`app/locations/`, `app/community/`, `app/chat/`, or `app/courses/`; shared configuration,
database setup, models, and error handling remain at the package root. Tests are split into
`tests/unit/`, `tests/integration/`, and `tests/contract/`. Alembic migrations belong in
`alembic/`, import and generation utilities in `scripts/`, source datasets in `data/`, and the
canonical API contract in `shared/openapi.yaml`.

## Build, Test, and Development Commands

- `uv sync --all-groups`: install runtime and development dependencies.
- `uv run alembic upgrade head`: apply database migrations.
- `uv run uvicorn app.main:app --reload`: run the local API server.
- `uv run pytest`: execute the complete test suite.
- `uv run ruff check .`: check imports and Python style.
- `uv run mypy app scripts`: run strict type checking.
- `uv build`: build the source distribution and wheel.

## Coding Style & Naming Conventions

Target Python 3.12, use four-space indentation, and keep lines within 100 characters. Add type
hints to public functions and preserve strict mypy compatibility. Use `snake_case` for modules,
functions, and variables; `PascalCase` for classes and Pydantic models; and descriptive router,
service, and repository names. Ruff is the formatting and linting authority.

## Testing Guidelines

Use pytest and name files and cases `test_*.py` and `test_<behavior>`. Add unit tests for pure
logic, integration tests for database or HTTP behavior, and contract tests when API schemas
change. A feature is not complete until pytest, Ruff, mypy, and the package build pass. Update
`shared/openapi.yaml` whenever an endpoint or public schema changes.

## Branch, Commit & Merge Workflow

Write and review the feature spec and implementation plan before creating a branch. Never stage
or commit files under `docs/superpowers/**`; treat them as local working documents. Create branches
as `feature/<kebab-case-feature>`, for example `feature/ranking-location-api`.

Implement and commit one functional unit at a time. Use concise Conventional Commit prefixes such
as `feat:`, `fix:`, `test:`, `docs:`, and `chore:`. After implementation, review the diff and run
all verification commands. Merge the feature branch into `master`, resolve and inspect conflicts,
then rerun verification on the merged result before pushing `master` to `origin`.

## Security & Configuration

Keep `.env`, database files, API keys, and credentials out of Git. Configure deployment secrets in
Render, especially `OPENAI_API_KEY`, and never include secret values in logs, fixtures, or errors.
