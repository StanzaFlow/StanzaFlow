# Phase 1 TODO — Weeks 1-4  (MVP Kick-off)

Goal: any user can `pipx install stanzaflow`, compile the cheat-sheet
workflow to LangGraph, see a Mermaid DAG, and run the code in < 3 minutes.

---

## 1 Repo & CI
- [x] Create GitHub org + repo `stanzaflow/stanzaflow`
- [x] CI (`ci.yaml`) running black, ruff, pytest, coverage
- [x] Pre-commit hooks (ruff, black, mdformat)

## 2 Parser & IR
- [x] `core/stz_grammar.lark` (tiny spec)
- [x] `core/ast.py` + compiler → IR 0.2
- [x] JSON Schema `schemas/ir-0.2.json`
- [x] Golden fixture `simple_workflow_no_attrs.sf.md` working (full attribute parsing implemented)

## 3 LangGraph Adapter (sequential)
- [x] `adapters/langgraph/emit.py`
- [x] Lower primitives `agent`, `step`, `artifact`
- [x] Unsupported → `# TODO escape needed` comment
- [x] Unit test: compile & run hello-world LangGraph flow

## 4 CLI & Tooling
- [x] `stanzaflow` / **`stz`** entrypoints
- [x] `stanzaflow graph` → Mermaid CLI → SVG (fallback to Graphviz if no Node)
- [x] `stanzaflow compile --target langgraph`
- [x] `stanzaflow audit` flags TODOs
- [x] Implement `!env` secrets
- [x] Local artifact sink `./artifacts/<timestamp>/`

## 5 Docs & DX
- [ ] Finalise `README.md`