# StanzaFlow Roadmap (v0 Series)

| Phase | Weeks | Deliverables | Flow Value |
|-------|-------|-------------|------------|
| **0 MVP** | 1-4 | Lark parser → IR 0.2 • LangGraph adapter (sequential) • `stanzaflow graph` (Mermaid w/ Graphviz fallback) • secret + artifact store | First "wow": Markdown → DAG → runnable code in < 3 m |
| **1 Lossless** | 5-8 | Round-trip harness ≥ 95 % • error attrs • escape TODOs • `stanzaflow audit` | Trust & gap visibility |
| **2 SDK + AI** | 9-11 | Adapter SDK + docs • `ai_escape()` via LiteLLM • security scanner • certification tests | Community adapters & auto-patch groundwork |
| **3 Playground** | 12-14 | StackBlitz web demo (paste `.sf.md`, see DAG+code) • AI toggle • 3-Q flow survey | Viral sharing & telemetry |
| **4 Adapters + Parallel** | 15-20 | CrewAI & PromptFlow compile (read-only) • Parallel primitive RFC • AI-escapes default-on for LangGraph | Cross-vendor promise & richer spec |
| **5 v0.5 Sprint** | ≤ 24 | ≥ 3 runtimes 90 % green • VS Code ext (syntax + inline DAG) • Steering group election | Ecosystem flywheel |

*Sheet Bridge deferred to enterprise "StanzaFlow Cloud" track.*

### KPIs

| Metric | Target |
|--------|--------|
| Install → DAG | < 3 m |
| LangGraph tests | ≥ 95 % |
| Escape lines in demos | < 10 % |
| Flow survey | ≥ 70 % report fewer context switches |
| External adapters | ≥ 2 by month 6 | 