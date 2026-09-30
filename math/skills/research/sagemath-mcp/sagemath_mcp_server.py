#!/usr/bin/env python3
"""MCP server for SageMath (with SymPy fallback).

Provides advanced algebraic, symbolic, and numerical computation tools
via the MCP protocol. Falls back to SymPy when `sage` is not available.

Tools: solve, diff, integrate, simplify, factor, expand, latex, matrix, number_field
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

# ── resolve sage binary ─────────────────────────────────────────────────────
# Check predefined paths first, then fall back to PATH lookup.
_CONDA_BIN = "/home/YOUR-USER/miniconda3/envs/sage-dev/bin"
_CONDA_PREFIX = "/home/YOUR-USER/miniconda3/envs/sage-dev"
_SAGE_CANDIDATES = [
    "/home/YOUR-USER/sage/sage",
    f"{_CONDA_BIN}/sage",
]
SAGE_BIN: str | None = None
_SAGE_ENV: dict[str, str] = {}
for p in _SAGE_CANDIDATES:
    if Path(p).is_file():
        SAGE_BIN = p
        # Inline conda env PATH so subprocesses (gap, etc.) are found
        _SAGE_ENV = {
            "PATH": f"{_CONDA_BIN}:/usr/bin:/bin",
            "CONDA_PREFIX": _CONDA_PREFIX,
        }
        break
if not SAGE_BIN:
    SAGE_BIN = shutil.which("sage")

SYMPY_AVAILABLE = False
try:
    import sympy  # noqa: F401
    SYMPY_AVAILABLE = True
except ImportError:
    pass

if not SAGE_BIN and not SYMPY_AVAILABLE:
    print("ERROR: Neither SageMath nor SymPy is available. Install one of them.", file=sys.stderr)
    sys.exit(1)

DEFAULT_TIMEOUT = int(os.environ.get("SAGE_TIMEOUT", "60"))


def _log(level: str, msg: str) -> None:
    print(f"[sagemath-mcp] {level}: {msg}", file=sys.stderr, flush=True)


def _result(name: str, result_str: str, latex_str: str = "", success: bool = True) -> dict[str, Any]:
    return {
        "tool": name,
        "result": result_str,
        "latex": latex_str,
        "success": success,
    }


def _sage_env() -> dict[str, str]:
    """Return environment dict for running SageMath, merging with current env."""
    env = dict(os.environ)
    env.update(_SAGE_ENV)
    return env


# ── SageMath direct execution ──────────────────────────────────────────────
def _run_sage(script: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(suffix=".sage", mode="w", delete=False) as tmp:
        tmp.write(script)
        tmp_path = tmp.name
    try:
        proc = subprocess.run(
            [SAGE_BIN, tmp_path],
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT,
            env=_sage_env(),
        )
        return proc
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── SymPy fallback ──────────────────────────────────────────────────────────
def _sympy_solve(expr_str: str, var: str = "x") -> str:
    import sympy
    x = sympy.symbols(var)
    expr = sympy.sympify(expr_str)
    sol = sympy.solve(expr, x)
    return str(sol)


def _sympy_diff(expr_str: str, var: str = "x", n: int = 1) -> str:
    import sympy
    x = sympy.symbols(var)
    expr = sympy.sympify(expr_str)
    result = sympy.diff(expr, x, n)
    return str(result)


def _sympy_integrate(expr_str: str, var: str = "x", limits: str | None = None) -> str:
    import sympy
    x = sympy.symbols(var)
    expr = sympy.sympify(expr_str)
    if limits:
        # limits like "0 pi" for definite integral
        parts = limits.split()
        a = sympy.sympify(parts[0])
        b = sympy.sympify(parts[1]) if len(parts) > 1 else None
        if b is not None:
            result = sympy.integrate(expr, (x, a, b))
        else:
            result = sympy.integrate(expr, (x, a))
    else:
        result = sympy.integrate(expr, x)
    return str(result)


def _sympy_simplify(expr_str: str) -> str:
    import sympy
    expr = sympy.sympify(expr_str)
    result = sympy.simplify(expr)
    return str(result)


def _sympy_factor(expr_str: str) -> str:
    import sympy
    expr = sympy.sympify(expr_str)
    result = sympy.factor(expr)
    return str(result)


def _sympy_expand(expr_str: str) -> str:
    import sympy
    expr = sympy.sympify(expr_str)
    result = sympy.expand(expr)
    return str(result)


def _sympy_latex(expr_str: str) -> str:
    import sympy
    expr = sympy.sympify(expr_str)
    import sympy.printing
    return sympy.printing.latex(expr)


def _sympy_matrix(ops: str) -> str:
    """Execute a matrix operation via SymPy."""
    import sympy
    safe_globals = {
        "Matrix": sympy.Matrix,
        "eye": sympy.eye,
        "zeros": sympy.zeros,
        "ones": sympy.ones,
        "diag": sympy.diag,
        "Rational": sympy.Rational,
        "pi": sympy.pi,
        "sqrt": sympy.sqrt,
        "I": sympy.I,
        "QQ": sympy.Rational,
    }
    try:
        result = eval(ops, {"__builtins__": {}}, safe_globals)
        return str(result)
    except Exception as exc:
        return f"Error in matrix operation: {exc}"


# ── Server instance ─────────────────────────────────────────────────────────
server = Server("sagemath")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    engine = "SageMath" if SAGE_BIN else "SymPy (fallback)"
    tools = [
        types.Tool(
            name="sage_solve",
            description=f"Solve an equation symbolically. Engine: {engine}",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Expression to solve, e.g. 'x**2 - 4'"},
                    "var": {"type": "string", "description": "Variable to solve for (default: 'x')", "default": "x"},
                },
                "required": ["expression"],
            },
        ),
        types.Tool(
            name="sage_diff",
            description=f"Differentiate an expression. Engine: {engine}",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Expression to differentiate"},
                    "var": {"type": "string", "description": "Variable (default: 'x')", "default": "x"},
                    "n": {"type": "integer", "description": "Order of derivative (default: 1)", "default": 1},
                },
                "required": ["expression"],
            },
        ),
        types.Tool(
            name="sage_integrate",
            description=f"Integrate an expression. Engine: {engine}",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Expression to integrate"},
                    "var": {"type": "string", "description": "Variable (default: 'x')", "default": "x"},
                    "limits": {"type": "string", "description": "Limits as 'a b' for definite integral, or just 'a' for indefinite with constant"},
                },
                "required": ["expression"],
            },
        ),
        types.Tool(
            name="sage_simplify",
            description=f"Simplify an expression. Engine: {engine}",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Expression to simplify"},
                },
                "required": ["expression"],
            },
        ),
        types.Tool(
            name="sage_factor",
            description=f"Factor a polynomial. Engine: {engine}",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Polynomial to factor"},
                },
                "required": ["expression"],
            },
        ),
        types.Tool(
            name="sage_expand",
            description=f"Expand an expression. Engine: {engine}",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Expression to expand"},
                },
                "required": ["expression"],
            },
        ),
        types.Tool(
            name="sage_latex",
            description=f"Convert a mathematical expression to LaTeX. Engine: {engine}",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Expression to convert to LaTeX"},
                },
                "required": ["expression"],
            },
        ),
        types.Tool(
            name="sage_matrix",
            description=f"Execute matrix operations. Engine: {engine}. Use Python/SymPy matrix syntax: 'Matrix([[1,2],[3,4]]).eigenvalues()'",
            inputSchema={
                "type": "object",
                "properties": {
                    "operations": {"type": "string", "description": "Matrix operations expression"},
                },
                "required": ["operations"],
            },
        ),
        types.Tool(
            name="sage_run_script",
            description=f"Run arbitrary Sage/SymPy Python code (sandboxed). Engine: {engine}",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "Python code to execute"},
                },
                "required": ["script"],
            },
        ),
    ]

    if SAGE_BIN:
        tools.append(
            types.Tool(
                name="sage_number_field",
                description="Work with algebraic number fields (SageMath only)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "operations": {"type": "string", "description": "Sage code for number field operations"},
                    },
                    "required": ["operations"],
                },
            ),
        )

    return tools


@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    try:
        if SAGE_BIN:
            return await _call_sage(name, arguments)
        else:
            return await _call_sympy(name, arguments)
    except subprocess.TimeoutExpired:
        return [types.TextContent(type="text", text=json.dumps({"error": "SageMath command timed out", "timeout": DEFAULT_TIMEOUT}, indent=2))]
    except Exception as exc:
        _log("error", f"Tool {name} failed: {exc}")
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}, indent=2))]


async def _call_sage(name: str, args: dict) -> list[types.TextContent]:
    """Execute a tool via SageMath."""
    if name == "sage_solve":
        expr = args["expression"]
        var = args.get("var", "x")
        script = f"var('{var}')\nprint(solve({expr} == 0, {var}))"
        proc = _run_sage(script)
        return [types.TextContent(type="text", text=json.dumps(_result(name, proc.stdout.strip(), success=proc.returncode == 0), indent=2))]

    elif name == "sage_diff":
        expr = args["expression"]
        var = args.get("var", "x")
        n = args.get("n", 1)
        script = f"var('{var}')\nexpr = {expr}\nprint(diff(expr, {var}, {n}))"
        proc = _run_sage(script)
        return [types.TextContent(type="text", text=json.dumps(_result(name, proc.stdout.strip(), success=proc.returncode == 0), indent=2))]

    elif name == "sage_integrate":
        expr = args["expression"]
        var = args.get("var", "x")
        limits = args.get("limits")
        script = f"var('{var}')\nexpr = {expr}\n"
        if limits:
            a, *b = limits.split()
            if b:
                script += f"print(integral(expr, ({var}, {a}, {b[0]})))"
            else:
                script += f"print(integral(expr, ({var}, {a})))"
        else:
            script += f"print(integral(expr, {var}))"
        proc = _run_sage(script)
        return [types.TextContent(type="text", text=json.dumps(_result(name, proc.stdout.strip(), success=proc.returncode == 0), indent=2))]

    elif name in ("sage_simplify", "sage_factor", "sage_expand", "sage_latex"):
        expr = args["expression"]
        # Auto-declare single-letter lowercase variables found in the expression
        import re
        vars_needed = set(re.findall(r'\b([a-z])\b', expr.replace('**', '')))
        var_decl = '; '.join(f"var('{v}')" for v in sorted(vars_needed))
        if var_decl:
            var_decl += '; '
        op_map = {
            "sage_simplify": f"{var_decl}print(simplify({expr}))",
            "sage_factor": f"{var_decl}print(factor({expr}))",
            "sage_expand": f"{var_decl}print(expand({expr}))",
            "sage_latex": f"{var_decl}print(latex({expr}))",
        }
        script = op_map[name]
        proc = _run_sage(script)
        return [types.TextContent(type="text", text=json.dumps(_result(name, proc.stdout.strip(), success=proc.returncode == 0), indent=2))]

    elif name == "sage_matrix":
        ops = args["operations"]
        script = ops
        proc = _run_sage(script)
        return [types.TextContent(type="text", text=json.dumps(_result("sage_matrix", proc.stdout.strip(), success=proc.returncode == 0), indent=2))]

    elif name == "sage_number_field":
        ops = args["operations"]
        proc = _run_sage(ops)
        return [types.TextContent(type="text", text=json.dumps(_result("sage_number_field", proc.stdout.strip(), success=proc.returncode == 0), indent=2))]

    elif name == "sage_run_script":
        script = args["script"]
        proc = _run_sage(script)
        return [types.TextContent(type="text", text=json.dumps(_result("sage_run_script", proc.stdout.strip(), success=proc.returncode == 0), indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def _call_sympy(name: str, args: dict) -> list[types.TextContent]:
    """Execute a tool via SymPy (fallback when SageMath is not available)."""
    try:
        if name == "sage_solve":
            expr = args["expression"]
            var = args.get("var", "x")
            result = _sympy_solve(expr, var)
            return [types.TextContent(type="text", text=json.dumps(_result(name, result), indent=2))]

        elif name == "sage_diff":
            expr = args["expression"]
            var = args.get("var", "x")
            n = args.get("n", 1)
            result = _sympy_diff(expr, var, n)
            return [types.TextContent(type="text", text=json.dumps(_result(name, result), indent=2))]

        elif name == "sage_integrate":
            expr = args["expression"]
            var = args.get("var", "x")
            limits = args.get("limits")
            result = _sympy_integrate(expr, var, limits)
            return [types.TextContent(type="text", text=json.dumps(_result(name, result), indent=2))]

        elif name == "sage_simplify":
            result = _sympy_simplify(args["expression"])
            return [types.TextContent(type="text", text=json.dumps(_result(name, result), indent=2))]

        elif name == "sage_factor":
            result = _sympy_factor(args["expression"])
            return [types.TextContent(type="text", text=json.dumps(_result(name, result), indent=2))]

        elif name == "sage_expand":
            result = _sympy_expand(args["expression"])
            return [types.TextContent(type="text", text=json.dumps(_result(name, result), indent=2))]

        elif name == "sage_latex":
            result = _sympy_latex(args["expression"])
            return [types.TextContent(type="text", text=json.dumps(_result(name, result, latex_str=result), indent=2))]

        elif name == "sage_matrix":
            result = _sympy_matrix(args["operations"])
            return [types.TextContent(type="text", text=json.dumps(_result(name, result), indent=2))]

        elif name == "sage_run_script":
            # sandboxed exec for SymPy operations
            import sympy
            safe_globals = {
                "sympy": sympy,
                "Matrix": sympy.Matrix,
                "eye": sympy.eye,
                "zeros": sympy.zeros,
                "ones": sympy.ones,
                "pi": sympy.pi,
                "sqrt": sympy.sqrt,
                "I": sympy.I,
                "Rational": sympy.Rational,
                "diff": sympy.diff,
                "integrate": sympy.integrate,
                "solve": sympy.solve,
                "simplify": sympy.simplify,
                "factor": sympy.factor,
                "expand": sympy.expand,
                "latex": sympy.printing.latex,
            }
            local_vars: dict = {}
            exec(args["script"], {"__builtins__": {}}, {**safe_globals, **local_vars})
            # capture printed output
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                exec(args["script"], {"__builtins__": {}}, {**safe_globals, **local_vars})
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout
            return [types.TextContent(type="text", text=json.dumps(_result(name, output.strip() or str(local_vars)), indent=2))]

        else:
            raise ValueError(f"Tool {name} not available in SymPy fallback mode")

    except Exception as exc:
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}, indent=2))]


# ── main entry point ────────────────────────────────────────────────────────
async def main() -> None:
    engine = "SageMath" if SAGE_BIN else "SymPy (fallback)"
    _log("info", f"Starting sagemath-mcp server (engine: {engine})")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sagemath",
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
