# CLAUDE.md

## Project

Django DataDog Logger — a Django package for DataDog JSON logging integration.
Package: `django_datadog_logger`. Version managed via `bump-my-version` in `pyproject.toml` and `django_datadog_logger/__init__.py`.

## Setup

```bash
uv sync --dev
```

## Common Commands

- **Lint**: `make lint` (runs `ruff check .` and `ruff format --check .`)
- **Test**: `make test` (runs `uv run pytest tests/ -v`)
- **Build**: `make dist` (runs `uv build`)
- **Clean**: `make clean`

## Testing

Tests use `pytest` with `pytest-django`. Test files live in `tests/`. Django settings configured in `pyproject.toml` under `[tool.pytest.ini_options]`.

## CI

GitHub Actions (`.github/workflows/build.yml`): lint job (ruff), test matrix of Python 3.10–3.14 × Django 4.2/5.2/6.0, build + publish on release.

## Code Style

- Linter & formatter: ruff (line-length 120, rules: E, F, I)
