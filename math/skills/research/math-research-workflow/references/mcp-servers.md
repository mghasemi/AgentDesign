# MCP Server Configuration for Math Tools

## Overview

11 MathAgent tool scripts are registered as Hermes native MCP servers in
`~/.hermes/profiles/math/config.yaml` (under `mcp_servers`). This makes
them available as first-class tools (`mcp_<server>_<tool>`) callable
directly by the LLM without spawning a terminal process.

## Source

Adapted from the MathAgent's `.mcp.json` at
`/home/YOUR-USER/Code/Python/MathAgent/MathAgent/.mcp.json`.

Key adaptations for Hermes:
- Absolute paths replace repo-relative paths
- Math profile venv Python replaces bare `python3`
- `uv` uses its absolute path for searxng
- Environment variables passed explicitly per server (Hermes filters
  subprocess environments by default)

## Registered Servers

| MCP Server      | Python Script                                  | Status |
|-----------------|------------------------------------------------|--------|
| vikunja         | `productivity/vikunja/vikunja_tool.py`        | ✅     |
| wolfram-alpha   | `research/wolfram-alpha/wolfram_alpha_tool.py`| ✅     |
| lightrag-query  | `research/lightrag-query/lightrag_query_tool.py`| ✅   |
| lightrag-ingest | `research/lightrag-ingest/lightrag_ingest_tool.py`| ✅  |
| siyuan          | `productivity/siyuan/siyuan_tool.py`          | ✅     |
| zimi            | `research/zimi/zimi_tool.py`                  | ✅     |
| searxng         | `research/searxng/scripts/searxng.py` (via uv)| ✅     |
| sympy-mcp       | `research/sympy-mcp/sympy_tool.py`            | ✅     |
| zotero          | `productivity/zotero/zotero_tool.py`          | ✅     |
| latex-manuscript| `productivity/latex-manuscript/latex_tool.py` | ⚠️¹   |
| scientific-coding| `research/scientific-coding/scientific_coding_tool.py`| ✅ |
| sagemath-mcp     | `research/sagemath-mcp/sagemath_mcp_server.py`      | ⚠️¹  |

¹ LaTeX compilation requires `pdflatex` (not installed).
   SageMath MCP is registered but can time out on long numerical work;
   fall back to `terminal` + `conda run` (see §SageMath below).

## Not Registered (missing binaries)

| Server        | Reason                          |
|---------------|---------------------------------|
| lean4         | `lean` binary not installed     |

## SageMath: MCP Available, Terminal Fallback

`mcp_sagemath_sage_run_script` is now registered as a Hermes native tool.
However, it can return empty output or time out on multi-step numerical work
(adaptive quadrature, minimize_scalar with many evaluations). When this
happens, fall back to `terminal` with the conda environment:

```bash
unset CONDA_SHLVL CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_PYTHON_EXE
conda run -n sage python3 /path/to/script.py
```

The `unset` preamble is required because the terminal session inherits
`CONDA_SHLVL=1` which breaks `conda run` activation. Write scripts to
`.py` files — heredocs piped into `conda run` produce no output.

NumPy in the `sage` conda env is ≥2.0 — use `np.trapezoid`, not `np.trapz`.

## Tool Naming

MCP tools follow the pattern `mcp_{server_name}_{tool_name}`.
The tool scripts expose multiple subcommands — each becomes a separate
MCP tool. Examples:

- `mcp_sympy-mcp_solve` → `sympy_tool.py solve "x**2 - 4"`
- `mcp_wolfram-alpha_verify` → `wolfram_alpha_tool.py verify "claim"`
- `mcp_lightrag-query_query` → `lightrag_query_tool.py query "q" --mode hybrid`
- `mcp_vikunja_projects_create` → `vikunja_tool.py projects create --title "..."

## When to use MCP vs Terminal

**Prefer MCP** for simple, single-call operations (solve, verify, search, create).
MCP calls are faster and don't spawn a shell.

**Prefer terminal** for:
- Multi-step workflows where you need to inspect intermediate output
- Tools not registered as MCP (academic-research-hub, calibre, pdf-extract-lite)
- Debugging failed calls (terminal shows raw stderr)

## Config Location

`~/.hermes/profiles/math/config.yaml` under `mcp_servers:`.

To add a new MCP server, append an entry following the pattern:

```yaml
mcp_servers:
  new-server-name:
    command: "/home/YOUR-USER/.hermes/profiles/math/venv/bin/python"
    args: ["/home/YOUR-USER/.hermes/profiles/math/skills/category/name/tool.py"]
    env:
      REQUIRED_VAR: "value"
    timeout: 30
```

MCP servers take effect on next session start (`/reset` or fresh `hermes` invocation).
