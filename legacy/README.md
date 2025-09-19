# Legacy Packaging Artifacts

This directory contains the historical `setup.py` and `requirements.txt` that were
used before VGGT-MPS adopted a PEP 621 `pyproject.toml` build. They are retained for
contributors who still rely on classic `pip install -r legacy/requirements.txt` or
`python legacy/setup.py install` flows.

These files are no longer updated and will eventually be removed. Prefer the modern
workflow:

```bash
uv pip install -e .
```

Or, if you only have `pip`:

```bash
pip install .
```

Use the legacy assets only if you know you need them.
