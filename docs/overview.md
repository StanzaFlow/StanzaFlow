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

## AI Escape System

### What are AI Escapes?

AI escapes are StanzaFlow's solution for handling workflow patterns that aren't directly supported by a target runtime adapter. Instead of failing compilation, StanzaFlow can automatically generate code patches using LLMs.

### How They Work

1. **Pattern Detection**: When the compiler encounters unsupported attributes or patterns, it marks them with `TODO[escape]` comments
2. **AI Generation**: With `--ai-escapes` enabled, StanzaFlow sends the unsupported pattern to an LLM with context about the target runtime
3. **Code Injection**: Generated code is injected into the workflow and marked with `TODO[escape]` tags
4. **Validation**: Generated code undergoes basic validation and is cached for future use

### Usage

```bash
# Compile with AI escapes disabled (default, deterministic)
stz compile workflow.sf.md --target langgraph

# Enable AI escapes (experimental, requires API key)
stz compile workflow.sf.md --target langgraph --ai-escapes --model gpt-4

# Audit will show which patterns need escapes
stz audit workflow.sf.md --target langgraph
```

### When to Use AI Escapes

**✅ Good for:**
- Prototyping with unsupported attributes
- Bridging gaps until official adapter support
- Learning what patterns are possible

**⚠️ Be careful with:**
- Production workflows (not yet stable)
- CI/CD pipelines (non-deterministic)
- Complex branching logic (may generate incorrect code)

**❌ Avoid for:**
- Mission-critical workflows
- When deterministic builds are required

### Security & Determinism

- Generated code runs in sandboxed subprocess with `seccomp` restrictions
- Cache keyed by IR hash for reproducible builds
- Static analysis blocks dangerous operations (`os.system`, etc.)
- CI should run with `--no-ai-escapes` for reproducible builds

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