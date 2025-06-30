# StanzaFlow  
*Write workflows the way you write stanzas.*

<p align="center">
  <img alt="MIT" src="https://img.shields.io/badge/license-MIT-blue">
  <img alt="CI"  src="https://github.com/stanzaflow/stanzaflow/actions/workflows/ci.yaml/badge.svg">
  <img alt="LangGraph Adapter" src="https://img.shields.io/badge/adapter-langgraph-green">
</p>

**StanzaFlow** is a Markdown-style DSL that lets you narrate a multi-agent
workflow once and run it anywhere.  
When the compiler can't lower a construct, it can **ask an LLM to auto-patch**
the missing code, test it, and cache the fix.

---

## Why StanzaFlow?

| Pain | StanzaFlow fix |
|------|----------------|
| Context-switch chaos | One `.sf.md` file |
| Vendor lock-in | `stanzaflow compile --target <runtime>` |
| Plumbing fatigue | Compiler emits boilerplate |
| Broken creative flow | `stanzaflow graph` → live DAG (Mermaid CLI → Graphviz fallback) |
| Adapter gaps | `--ai-escapes on` autogenerates tested code |

---

## Quick Demo

```bash
pipx install stanzaflow

cat > triage.sf.md <<'SF'
# Workflow: Ticket Triage

## Agent: Bot
- Step: Hello
  artifact: hello.txt
SF

# primary CLI
stanzaflow graph triage.sf.md            # 📈 SVG DAG
stanzaflow compile --target langgraph    # 🏃 runnable code

# short alias works too
stz graph triage.sf.md
```

Enable AI auto-patch:

```bash
# supports OpenAI, OpenRouter, Ollama etc. via LiteLLM
export OPENAI_API_KEY=sk-...
stanzaflow compile triage.sf.md \
        --target langgraph \
        --ai-escapes on
```

The compiler prompts your model, injects a `%%escape langgraph` snippet,
runs unit tests, and caches the result in
`~/.stanzaflow/cache/escapes/`.

---

## How it Works

```
.sf.md ──▶ Lark parser ─▶ JSON IR 0.2 ─▶ adapter
                       │
                       └─ unsupported? → build prompt → LiteLLM → tests → cache %%escape
```

*CI builds with `--ai-escapes off`; nightly job turns it on to catch drift.*

---

## Roadmap (v0 snapshot)

| Phase        | Weeks | Highlights                                   |
| ------------ | ----- | -------------------------------------------- |
| 0 MVP        | 1-4   | Parser → IR, LangGraph adapter, `graph` cmd  |
| 1 Lossless   | 5-8   | Round-trip tests, audit cmd, escape TODOs    |
| 2 SDK + AI   | 9-11  | Adapter SDK, `ai_escape()`, security scanner |
| 3 Playground | 12-14 | Web demo with AI toggle                      |
| 4 Adapters+  | 15-20 | CrewAI / PromptFlow compile, parallel RFC    |
| 5 v0.5       | ≤24   | VS Code ext, steering group                  |

Full details → [`docs/roadmap.md`](docs/roadmap.md)

---

## Local or Cloud LLM?

| Backend            | How to enable                                                                         |
| ------------------ | ------------------------------------------------------------------------------------- |
| OpenAI             | `export OPENAI_API_KEY=...`                                                           |
| OpenRouter         | `export OPENAI_API_BASE=https://openrouter.ai/api/v1` + key                           |
| **Ollama (local)** | `export OLLAMA_BASE=http://localhost:11434`<br>`stanzaflow --model ollama/llama3 ...` |

All handled by **LiteLLM** — switch with a flag, no code changes.

---

## Contributing

### Development setup

```bash
# clone and enter repo
git clone https://github.com/stanzaflow/stanzaflow
cd stanzaflow

# create local env with uv (fast lock-free installer)
uv venv .venv
source .venv/bin/activate

# install dev extras (pytest, ruff, black, etc.)
uv pip install -e ".[dev]"

# run the full pre-commit stack once
pre-commit run --all-files

# run tests + coverage
pytest -q
```

Pre-commit hooks enforce Ruff, Black and Mdformat on every commit and will
auto-fix or block non-conforming code. Our GitHub Actions workflow replicates
this exact toolchain on Python 3.11 and 3.12.

Join us: **[https://discord.gg/stanzaflow](https://discord.gg/stanzaflow)**

---

## License

[MIT](LICENSE)

> StanzaFlow keeps you in the story — the compiler (and maybe an LLM) chases the plumbing. 