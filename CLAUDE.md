# CLAUDE.md

## Project

Django DataDog Logger — a Django package for DataDog JSON logging integration.
Package: `django_datadog_logger`. Version managed via `bump2version` in `setup.py` and `django_datadog_logger/__init__.py`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements_dev.txt
```

## Common Commands

- **Lint**: `make lint` (runs flake8)
- **Test**: `make test` (runs `DJANGO_SETTINGS_MODULE=tests.settings python -m unittest discover`)
- **Build**: `make dist` (sdist + bdist_wheel)
- **Clean**: `make clean`

## Testing

Tests use `unittest` (not pytest). Test files live in `tests/`. Django settings: `tests/settings.py`.

## CI

GitHub Actions (`.github/workflows/pr-checks.yml`): matrix of Python 3.7–3.11 × Django 4/5, then build on Python 3.11. Black formatting checked via `black.yml`.

## Code Style

- Formatter: Black (line-length 120, targets py37/py38)
- Linter: flake8 (max-line-length 120)