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

