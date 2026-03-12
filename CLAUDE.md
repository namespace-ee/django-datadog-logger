# CLAUDE.md

## Project

Django DataDog Logger — a Django package for DataDog JSON logging integration.
Package: `django_datadog_logger`. Version managed via `bump2version` in `pyproject.toml` and `django_datadog_logger/__init__.py`.

## Setup

```bash
uv sync --dev
```

## Common Commands

- **Lint**: `make lint` (runs flake8)
- **Test**: `make test` (runs `DJANGO_SETTINGS_MODULE=tests.settings uv run python -m unittest discover`)
- **Build**: `make dist` (runs `uv build`)
- **Clean**: `make clean`

## Testing

Tests use `unittest` (not pytest). Test files live in `tests/`. Django settings: `tests/settings.py`.

## CI

GitHub Actions (`.github/workflows/pr-checks.yml`): matrix of Python 3.10–3.14 × Django 4/5, then build on Python 3.12. Black formatting checked via `black.yml`.

## Code Style

- Formatter: Black (line-length 120)
- Linter: flake8 (max-line-length 120, config in `setup.cfg`)
