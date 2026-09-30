#!/usr/bin/env python3
"""MCP server for Lean4 verification and proof support.

Provides Lean4 REPL, search, and proof tools via the MCP protocol.
Communicates over stdio using JSON-RPC (MCP stdio transport).

Requires: mcp, lean/lake on PATH (with HOME set for elan toolchains).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# ── try importing the MCP SDK ──────────────────────────────────────────────
try:
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server import NotificationOptions, Server
    import mcp.server.stdio
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# ── resolve lean/lake binaries ─────────────────────────────────────────────
LEAN_BIN = shutil.which("lean")
LAKE_BIN = shutil.which("lake")
if not LEAN_BIN:
    print("ERROR: 'lean' binary not found on PATH. Install elan and lean.", file=sys.stderr)
    sys.exit(1)

DEFAULT_TIMEOUT = 60.0
SCRATCH_ROOT = Path.home() / ".cache" / "lean4_tool"
SCRATCH_PROJECT_NAME = "Lean4MCP_scratch"


def _resolve_scratch() -> Path:
    """Ensure a Mathlib-enabled scratch project exists, creating it if needed."""
    scratch_dir = SCRATCH_ROOT / SCRATCH_PROJECT_NAME
    if not scratch_dir.exists():
        _log("info", f"Creating scratch project at {scratch_dir}")
        subprocess.run(
            [LAKE_BIN or "lake", "new", SCRATCH_PROJECT_NAME],
            cwd=SCRATCH_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # verify project dir was created
        if not scratch_dir.exists():
            raise RuntimeError(f"Failed to create scratch project at {scratch_dir}")

        # add Mathlib requirement to lakefile.toml
        lakefile = scratch_dir / "lakefile.toml"
        if lakefile.exists():
            content = lakefile.read_text()
            if "mathlib" not in content:
                new_content = content + '\n[[require]]\nname = "mathlib"\nrepo = "https://github.com/leanprover-community/mathlib4.git"\n'
                lakefile.write_text(new_content)
        else:
            lakefile.write_text(
                'name = "Lean4MCP_scratch"\n'
                '[[require]]\nname = "mathlib"\n'
                'repo = "https://github.com/leanprover-community/mathlib4.git"\n'
            )

        # fetch mathlib
        _log("info", "Fetching Mathlib (this may take several minutes on first run)...")
        subprocess.run(
            [LAKE_BIN or "lake", "update"],
            cwd=str(scratch_dir),
            capture_output=True,
            text=True,
            timeout=600,
        )
    # build if not already built (check for build dir)
    build_dir = scratch_dir / "build"
    if not build_dir.exists() or not any(build_dir.iterdir()):
        _log("info", "Building scratch project...")
        subprocess.run(
            [LAKE_BIN or "lake", "build"],
            cwd=str(scratch_dir),
            capture_output=True,
            text=True,
            timeout=600,
        )
    return scratch_dir


def _log(level: str, msg: str) -> None:
    """Log to stderr so MCP JSON-RPC on stdout stays clean."""
    print(f"[lean4-mcp] {level}: {msg}", file=sys.stderr, flush=True)


def _result(name: str, stdout: str, stderr: str, exit_code: int) -> dict[str, Any]:
    return {
        "tool": name,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "success": exit_code == 0,
    }


# ── Server instance ────────────────────────────────────────────────────────
server = Server("lean4")


# ── tool: lean4_repl ───────────────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="lean4_repl",
            description="Run ad-hoc Lean4 code. Prepends `import Mathlib` by default. Set mathlib=false to skip it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Lean code snippet to evaluate"},
                    "mathlib": {
                        "type": "boolean",
                        "description": "Prepend 'import Mathlib' (default: true)",
                        "default": True,
                    },
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="lean4_check",
            description="Check a Lean source file for errors",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to .lean file"},
                    "project_dir": {
                        "type": "string",
                        "description": "Optional Lake project root for project-aware checking",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="lean4_search",
            description="Search Mathlib for lemmas matching a proposition pattern. Requires Mathlib-enabled project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Proposition pattern to search for, e.g. 'forall a b : Nat, a + b = b + a'",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="lean4_prove",
            description="Attempt an automated proof of a proposition using common tactic batteries",
            inputSchema={
                "type": "object",
                "properties": {
                    "statement": {
                        "type": "string",
                        "description": "Proposition to prove, e.g. '∀ x : ℝ, x² ≥ 0'",
                    },
                },
                "required": ["statement"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    try:
        if name == "lean4_repl":
            return await _repl(arguments)
        elif name == "lean4_check":
            return await _check(arguments)
        elif name == "lean4_search":
            return await _search(arguments)
        elif name == "lean4_prove":
            return await _prove(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as exc:
        _log("error", f"Tool {name} failed: {exc}")
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}, indent=2))]


async def _repl(args: dict) -> list[types.TextContent]:
    code = args["code"]
    use_mathlib = args.get("mathlib", True)
    content = f"import Mathlib\n\n{code}" if use_mathlib else code

    tmp_dir = Path(tempfile.mkdtemp())
    tmp_path = tmp_dir / "session.lean"
    tmp_path.write_text(content)

    try:
        if use_mathlib:
            # we need a Mathlib-enabled project
            scratch = _resolve_scratch()
            cmd = [LAKE_BIN or "lake", "env", LEAN_BIN, str(tmp_path)]
            proc = subprocess.run(
                cmd,
                cwd=str(scratch),
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )
        else:
            cmd = [LEAN_BIN, str(tmp_path)]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)

        out = _result("lean4_repl", proc.stdout, proc.stderr, proc.returncode)
        return [types.TextContent(type="text", text=json.dumps(out, indent=2))]
    finally:
        # cleanup temp files
        for f in tmp_dir.iterdir():
            f.unlink(missing_ok=True)
        tmp_dir.rmdir()


async def _check(args: dict) -> list[types.TextContent]:
    path = Path(args["path"]).expanduser().resolve()
    if not path.exists():
        return [types.TextContent(type="text", text=json.dumps({"error": f"File not found: {path}"}, indent=2))]

    project_dir = args.get("project_dir")
    if project_dir:
        proj_path = Path(project_dir).expanduser().resolve()
        cmd = [LAKE_BIN or "lake", "env", LEAN_BIN, str(path)]
        proc = subprocess.run(cmd, cwd=str(proj_path), capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)
    else:
        cmd = [LEAN_BIN, str(path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)

    result = _result("lean4_check", proc.stdout, proc.stderr, proc.returncode)
    result["file"] = str(path)
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def _search(args: dict) -> list[types.TextContent]:
    query = args["query"]
    scratch = _resolve_scratch()

    snippet = "\n".join([
        "import Mathlib",
        "",
        f"#check {query}",
        "",
        f"example : {query} := by",
        "  exact?",
        "",
        f"example : {query} := by",
        "  apply?",
    ])

    tmp_path = scratch / ".lean4_tmp" / "search_temp.lean"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(snippet)

    cmd = [LAKE_BIN or "lake", "env", LEAN_BIN, str(tmp_path)]
    proc = subprocess.run(cmd, cwd=str(scratch), capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)

    result = _result("lean4_search", proc.stdout, proc.stderr, proc.returncode)
    result["query"] = query
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def _prove(args: dict) -> list[types.TextContent]:
    statement = args["statement"]
    scratch = _resolve_scratch()

    snippet = "\n".join([
        "import Mathlib",
        "",
        f"example : {statement} := by",
        "  first",
        "  | exact?",
        "  | aesop?",
        "  | simp",
        "  | norm_num",
        "  | ring",
        "  | linarith",
        "  | nlinarith",
        "  | positivity",
        "  | omega",
    ])

    tmp_path = scratch / ".lean4_tmp" / "prove_temp.lean"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(snippet)

    cmd = [LAKE_BIN or "lake", "env", LEAN_BIN, str(tmp_path)]
    proc = subprocess.run(cmd, cwd=str(scratch), capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)

    result = _result("lean4_prove", proc.stdout, proc.stderr, proc.returncode)
    result["statement"] = statement
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


# ── main entry point ────────────────────────────────────────────────────────
async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="lean4",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
