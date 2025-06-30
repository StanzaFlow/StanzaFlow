.PHONY: dev test lint format clean install build

# Development setup
dev:
	uv venv .venv
	uv pip install -e ".[dev]"
	pre-commit install

# Install package
install:
	uv pip install -e .

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=stanzaflow --cov-report=html --cov-report=term-missing

# Lint code
lint:
	ruff check .
	mypy .

# Format code
format:
	ruff --fix .
	black .

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

# Build package
build: clean
	uv build

# Run all checks
check: format lint test

# Quick test of CLI
demo:
	stz --version
	stz graph tests/fixtures/ticket_triage.sf.md
	stz compile tests/fixtures/ticket_triage.sf.md --target langgraph
	stz audit tests/fixtures/ticket_triage.sf.md 