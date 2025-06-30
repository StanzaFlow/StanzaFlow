# Contributing to StanzaFlow

Welcome to StanzaFlow! We're excited you want to contribute.

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Node.js (optional, for Mermaid CLI)

### Quick Start

```bash
git clone https://github.com/stanzaflow/stanzaflow
cd stanzaflow
make dev
```

This will:
1. Create a virtual environment with `uv venv .venv`
2. Install dependencies with `uv pip install -e ".[dev]"`
3. Set up pre-commit hooks

### Development Commands

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Lint and format code
make format
make lint

# Test the CLI (both aliases work)
stz --version
stanzaflow --version

# Quick demo
make demo
```

## Project Structure

```
stanzaflow/
├── stanzaflow/
│   ├── core/           # Parser, IR, exceptions
│   ├── adapters/       # Runtime adapters
│   │   └── langgraph/  # LangGraph adapter
│   └── cli/            # CLI commands
├── tests/
│   └── fixtures/       # Test .sf.md files
├── docs/               # Documentation
└── schemas/            # JSON schemas
```

## Code Style

- **Type hints**: Required for all functions
- **Docstrings**: Google-style for public functions
- **Formatting**: `black` + `ruff --fix`
- **Type checking**: `mypy --strict`

## Testing

- Place test files in `tests/`
- Use fixtures in `tests/fixtures/` for `.sf.md` samples
- Minimum 90% coverage for `core/` and `adapters/`
- Run `make test-cov` to check coverage

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run `make check` to ensure all tests pass
5. Commit with a clear message
6. Push and create a pull request

## Design Principles

- **Stay in flow**: Minimize context switches
- **Tiny spec**: Keep the DSL minimal
- **Escape, don't trap**: Use `%%escape` blocks for unsupported patterns
- **AI auto-patch**: Enable with `--ai-escapes` flag
- **Security first**: Sandbox all generated code

## Good First Issues

- Improve parser error messages
- Add more test fixtures
- Implement Graphviz fallback for `graph` command
- Add more examples to documentation

## Questions?

Join our Discord: [https://discord.gg/stanzaflow](https://discord.gg/stanzaflow)

---

> Remember: StanzaFlow keeps you in the story — the compiler chases the plumbing. 