# Contributing Guide

Thank you for your interest in contributing to the Olist Text-to-SQL Agent!

## Getting Started

1. **Fork** the repository and clone your fork locally.
2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Set up environment variables** by copying the example file:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Project Structure

```
src/               Source package (agent logic, connectors, prompts, schema, LLM factory)
tests/             Test suite (unit + integration)
agent.py           Backward-compatibility shim re-exporting src.agent
app.py             Streamlit UI
eval/              Evaluation dashboard and benchmark data
scripts/           Data preparation scripts
docs/              Project documentation
```

## Running Tests

```bash
pytest tests/ -v
```

To run only unit tests (no real API key required):
```bash
pytest tests/unit/ -v
```

## Linting

```bash
ruff check src/ tests/
```

To auto-fix fixable issues:
```bash
ruff check --fix src/ tests/
```

## Code Style

- Follow **PEP 8** conventions.
- All public functions and classes must have docstrings.
- Type hints are required for all function signatures.
- Run `ruff check` before committing. CI will enforce it.

## Branching Strategy

- Branch off `main` for every feature or fix.
- Use descriptive branch names: `feat/add-postgres-connector`, `fix/timeout-handling`.
- Open a pull request against `main` and ensure all CI checks pass.

## Adding a New LLM Provider

1. Add the provider package to `requirements.txt`.
2. Update `src/llm/factory.py` to handle the new `provider` value.
3. Add unit tests in `tests/unit/` covering the new provider path.

## Adding a New Database Connector

1. Create a new module in `src/connectors/` implementing `DatabaseConnector`.
2. Export it from `src/connectors/__init__.py`.
3. Add unit tests in `tests/unit/`.

## Commit Messages

Use conventional commits:
```
feat: add PostgreSQL connector
fix: correct timeout error message
refactor: extract prompts to system_prompts.py
test: add routing unit tests
docs: update contributing guide
```
