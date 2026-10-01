# CLAUDE.md - AI Agent Instructions for firewatch

## Project Overview

Firewatch is a Python CLI tool (v2.0.0) for monitoring OpenShift CI job results and automatically
reporting pod or test failures to Jira. It parses JUnit XML results and CI artifacts, matches
failures against configurable rules, and creates or updates Jira issues with detailed failure
information. It also supports Slack notifications and Jira escalation workflows.

## Architecture

- **CLI entry point**: `src/cli.py` (uses Click)
- **Commands**: `src/commands/` — `report`, `jira_escalation`, `jira_config_gen`
- **Core logic**: `src/report/report.py` — failure detection, rule matching, Jira filing
- **Escalation**: `src/escalation/` — Jira escalation workflows
- **Config generation**: `src/jira_config_gen/` — Jira configuration generator
- **Domain objects**: `src/objects/` — `job`, `failure`, `rule`, `failure_rule`, `configuration`,
  `jira_base`, `jira_adf`, `slack_base`
- **Tests**: `tests/unittests/` — pytest unit tests with fixtures in `conftest.py`

## Build and Setup

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Build the package
uv build

# Full dev environment setup
make dev-environment
```

## Running Tests

```bash
# Run full test suite via tox (recommended)
make test
# Or directly:
uv run --with tox-uv tox

# Run a specific test file
uv run pytest tests/unittests/functions/report/test_firewatch_functions_report.py -v

# Run with coverage report
uv run pytest --verbose --cov=src --cov-report=html:./tests/unittests/coverage --cov-fail-under=60
```

## Linting and Formatting

```bash
# Run all pre-commit hooks
make pre-commit
# Or directly:
pre-commit run --all-files

# Single-file checks
ruff check path/to/file.py
ruff format --check path/to/file.py
mypy path/to/file.py
```

## Code Style and Conventions

- **Linter/Formatter**: ruff (line-length 120, preview mode enabled, auto-fix on)
- **Type checker**: mypy (strict mode — disallow untyped defs, no implicit optional)
- **Additional linting**: flake8 with RedHatQE plugins, detect-secrets
- **Markdown**: markdownlint-cli2 with project `.markdownlint.json`
- **Python**: >=3.12 required
- **Dependency management**: uv with `pyproject.toml` and `uv.lock`
- **Test coverage**: minimum 60% required (enforced by pytest-cov)
- **Test framework**: pytest with fixtures in `conftest.py` files

## Directory Layout

```text
src/                    # Main source code
  cli.py                # Click CLI entry point
  commands/             # CLI command implementations
  report/               # Core reporting logic
  escalation/           # Jira escalation logic
  jira_config_gen/      # Jira config generation
  objects/              # Domain model classes
tests/
  unittests/            # Unit tests (pytest)
    functions/          # Functional test modules
    resources/          # Test fixtures and data
docs/                   # MkDocs documentation source
scripts/                # Utility scripts
development/            # Development environment configs
catalog/                # Service catalog definitions
```

## Key Dependencies

- `click` — CLI framework
- `jira` — Jira API client
- `junitparser` — JUnit XML parsing
- `google-cloud-storage` — GCS artifact access
- `slack-sdk` — Slack notifications
- `jinja2` — Template rendering

## CI/CD

- GitHub Actions workflow: `.github/workflows/pr-verification.yml`
- Runs unit tests via tox on pull requests to `main`
- Container build: `make container-build` (uses Podman or Docker)
