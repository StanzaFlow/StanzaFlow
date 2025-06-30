#!/usr/bin/env bash
# MIT License
# Copyright (c) 2025 StanzaFlow
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# -----------------------------------------------------------------------------
# tools/bootstrap_docs.sh
# -----------------------------------------------------------------------------
# Fetch and mirror external documentation sources referenced by StanzaFlow.
#
# Usage:
#   bash tools/bootstrap_docs.sh
# -----------------------------------------------------------------------------
set -euo pipefail

# Determine repository root. When executed inside a Git repository we
# prefer `git rev-parse --show-toplevel`; otherwise fall back to the parent
# directory of this script so the script also works in a plain directory
# checkout or a tarball.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$ROOT" ]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
DST="${ROOT}/docs_sources"
mkdir -p "$DST"

# ─────────────────────────────────────────────────────────────────────────────
info() { printf "\e[32m[+] %s\e[0m\n" "$1"; }
warn() { printf "\e[33m[!] %s\e[0m\n" "$1"; }

echo "StanzaFlow docs bootstrapper"

# 1. Local StanzaFlow spec / roadmap
cp docs/overview.md        "$DST/stanzaflow-overview.md"
cp docs/roadmap.md         "$DST/stanzaflow-roadmap.md"
cp docs/spec-v0.md         "$DST/stanzaflow-spec.md"    || warn "spec-v0.md not yet written"

# 2. Remote open-source references  (curl -fsSL URL > file)
fetch () {
  local url="$1" out="$2"
  if curl -fsSL "$url" -o "$out"; then
    info "fetched $(basename "$out")"
  else
    warn  "failed $url → $out"
    rm -f "$out"
  fi
}

fetch  https://raw.githubusercontent.com/lark-parser/lark/master/docs/guide.md \
       "$DST/lark-user-guide.md"

fetch  https://raw.githubusercontent.com/tiangolo/typer/master/docs/docs/index.md \
       "$DST/typer-docs.md"

fetch  https://raw.githubusercontent.com/astral-sh/uv/main/README.md \
       "$DST/uv-quickstart.md"

fetch  https://raw.githubusercontent.com/BerriAI/litellm/main/README.md \
       "$DST/litellm-reference.md"

fetch  https://raw.githubusercontent.com/mermaid-js/mermaid-cli/develop/README.md \
       "$DST/mermaid-cli.md"

fetch  https://raw.githubusercontent.com/mingrammer/diagrams/master/README.md \
       "$DST/graphviz-diagrams.md"

fetch  https://raw.githubusercontent.com/langchain-ai/langgraph/main/README.md \
       "$DST/langgraph-api-guide.md"

fetch  https://raw.githubusercontent.com/pytest-dev/pytest/main/README.rst \
       "$DST/pytest-patterns.md"

fetch  https://raw.githubusercontent.com/astral-sh/ruff/main/README.md \
       "$DST/ruff-rules.md"

# Sandbox cheat-sheet (static snippet)
cat > "$DST/sandboxing-notes.md" <<'EOF'
# Python safe_exec + seccomp cheat-sheet
* Use `subprocess.run([...], preexec_fn=seccomp_sandbox, ...)`
* Limit resources with `resource.setrlimit`.
EOF

# GHA recipes (static)
cat > "$DST/gha-uv-recipes.md" <<'EOF'
## GitHub Actions + uv
```yaml
- uses: actions/setup-python@v5
  with: { python-version: '3.12' }
- name: Cache uv
  uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('pyproject.toml') }}
- run: uv pip install -e ".[dev]"
```

EOF

echo ""
info "Docs synced to ${DST}"
ls -1 "${DST}" | wc -l | xargs -I{} echo "{} files in docs_sources/" 