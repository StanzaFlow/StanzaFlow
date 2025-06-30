# StanzaFlow — Project Overview  
*"Write workflows the way you write stanzas."*

---

## North-Star Goal  
Authors stay in **flow-state**: one Markdown stanza → instant DAG →
runtime code. Unsupported edges? the compiler can **auto-patch** with an LLM,
test, and cache.

---

## Immutable Design Principles (v0.x)

| Principle | Praxis |
|-----------|--------|
| **Tiny Spec** | `agent · step · branch · finally · artifact` (+ `retry`, `timeout`, `on_error`) |
| **Markdown Mental Model** | `.sf.md` + GitHub render |
| **Compiler-grade IR** | JSON (`ir_version: 0.2`) via Lark parser |
| **Escape, not Trap** | `%%escape <rt>` blocks; AI can generate them |
| **Secret-first** | `!env VAR` at compile-time |
| **AI Auto-Patch** | `--ai-escapes on` → LiteLLM → sandboxed tests; off in CI |
| **Flow-first Tooling** | `stanzaflow graph` (Mermaid → Graphviz fallback) • `stanzaflow audit` |
| **Open & Neutral** | MIT, RFCs, 5-seat steering group |

---

## Pipeline

```
.sf.md → Lark → IR → adapter
└─ if unsupported:
prompt(LLM) → code → tests → cache → %%escape
```

Nightly CI builds with AI-escapes on to reveal drift; main CI off for reproducibility.

---

## Security & Determinism

* Jailed subprocess (`seccomp`) for escape code  
* Static AST scan blocks `os.system`, `subprocess`, etc.  
* Cache keyed by IR-hash; CI locks model + temperature.

---

## Risks & Mitigations (excerpt)

| Risk | Mitigation |
|------|------------|
| Spec missing parallelism | Parallel primitive RFC shipped Phase 4 |
| Over-reliance on AI | `audit` fails if escape lines >20 %; badge yellow |
| Nondeterminism | Hash cache + locked params in CI | 