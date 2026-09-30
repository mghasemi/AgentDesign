# Python venv Setup for Math Tools

## Why a venv is required

This system uses Ubuntu 24.04 with Python 3.12.3 under PEP 668
(externally-managed environment). Bare `pip install` fails with:

```
error: externally-managed-environment
hint: See PEP 668 for the detailed specification.
```

A dedicated venv at `~/.hermes/profiles/math/venv/` isolates the math
tool dependencies from the system Python.

## Current state (2026-05-19)

```
Location:  ~/.hermes/profiles/math/venv/
Python:    3.12.3
PATH:      prepended in ~/.hermes/profiles/math/.env
VIRTUAL_ENV: set in ~/.hermes/profiles/math/.env
```

### Installed packages

```
sympy       1.14.0    — symbolic math (solve, diff, integrate, LaTeX)
mpmath      1.3.0     — arbitrary-precision arithmetic (sympy dep)
pyzotero    1.11.1    — Zotero Web API client
arxiv       4.0.0     — arXiv API wrapper
scholarly   1.7.11    — Google Scholar scraper
mcp         1.27.1    — MCP SDK (for Hermes native MCP client)
pyjwt       2.12.1    — JWT (mcp dep)
pydantic    2.13.4    — data validation (mcp dep)
httpx       0.28.1    — HTTP client (pyzotero dep)
uvicorn     0.47.0    — ASGI server (mcp dep)
```

## How PATH works

The math profile `.env` contains:

```bash
PATH=/home/YOUR-USER/.hermes/profiles/math/venv/bin:$PATH
VIRTUAL_ENV=/home/YOUR-USER/.hermes/profiles/math/venv
```

When Hermes sources `.env`, `python3` resolves to the venv Python.
All tool scripts invoked via `python3 /path/to/tool.py` automatically
use the venv Python and its installed packages.

## Adding packages

```bash
/home/YOUR-USER/.hermes/profiles/math/venv/bin/pip install <package>
```

Do NOT use `pip install --break-system-packages` or `sudo pip install`.

## Verification

```bash
# Check venv Python is first in PATH
which python3
# Expected: /home/YOUR-USER/.hermes/profiles/math/venv/bin/python3

# Verify sympy works
python3 -c "import sympy; print(sympy.__version__)"
# Expected: 1.14.0

# Verify tool scripts find dependencies
python3 ~/.hermes/profiles/math/skills/research/sympy-mcp/sympy_tool.py solve "x**2 - 4"
# Expected: [-2, 2]
```
