#!/usr/bin/env python3
"""Generic MCP stdio server that wraps any argparse-based Hermes CLI tool.

Reads ``TOOL_SCRIPT`` (absolute path to a ``*_tool.py`` CLI script) and
``TOOL_SERVER_NAME`` (MCP server name) from the environment, imports the
module, introspects its argparse parser, and exposes every subcommand as
an MCP tool. Tool calls reconstruct the CLI argv and invoke the module's
own ``main()`` with stdout/stderr captured — so behaviour, env handling,
and error paths are exactly those of the CLI.

Tool naming: subcommand path flattened with '_' and hyphens -> underscores,
e.g. ``projects list`` -> ``projects_list``, ``create-block`` -> ``create_block``.
For tools with a ``--format`` choice of "json" the adapter injects
``--format json`` unless the caller supplied it, so responses are JSON.

Works with any tool following the project convention:
``build_parser()`` (or ``_build_parser()``) + ``main()`` that prints JSON.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import sys
from typing import Any

try:
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server import NotificationOptions, Server
    import mcp.server.stdio
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

TOOL_SCRIPT = os.getenv("TOOL_SCRIPT", "")
SERVER_NAME = os.getenv("TOOL_SERVER_NAME", "cli-tool")


def _log(level: str, msg: str) -> None:
    print(f"[{SERVER_NAME}-mcp] {level}: {msg}", file=sys.stderr, flush=True)


# ── import the wrapped tool module ─────────────────────────────────────────
if not TOOL_SCRIPT or not os.path.isfile(TOOL_SCRIPT):
    print(f"ERROR: TOOL_SCRIPT not set or not a file: {TOOL_SCRIPT!r}", file=sys.stderr)
    sys.exit(1)

_mod_name = "wrapped_" + SERVER_NAME.replace("-", "_")
_spec = importlib.util.spec_from_file_location(_mod_name, TOOL_SCRIPT)
if _spec is None or _spec.loader is None:
    print(f"ERROR: cannot load {TOOL_SCRIPT}", file=sys.stderr)
    sys.exit(1)
tool_mod = importlib.util.module_from_spec(_spec)
sys.modules[_mod_name] = tool_mod
_spec.loader.exec_module(tool_mod)

# Locate the parser builder (convention: build_parser / _build_parser)
_builder = getattr(tool_mod, "build_parser", None) or getattr(tool_mod, "_build_parser", None)
if _builder is None:
    print(f"ERROR: {TOOL_SCRIPT} has no build_parser()/_build_parser()", file=sys.stderr)
    sys.exit(1)
root_parser = _builder()
_main = getattr(tool_mod, "main", None)
if _main is None:
    print(f"ERROR: {TOOL_SCRIPT} has no main()", file=sys.stderr)
    sys.exit(1)


# ── parser introspection ───────────────────────────────────────────────────
class LeafSpec:
    __slots__ = ("path", "chain", "parser", "help_text")

    def __init__(self, path: list[str], chain: list[argparse.ArgumentParser], help_text: str):
        self.path = path          # subcommand token path, e.g. ["projects", "list"]
        self.chain = chain        # parser chain root -> ... -> leaf
        self.parser = chain[-1]
        self.help_text = help_text or " ".join(path)


def _is_subparsers(action: argparse.Action) -> bool:
    return isinstance(action, argparse._SubParsersAction)


def _collect_leaves(parser: argparse.ArgumentParser, path: list[str], chain: list[argparse.ArgumentParser], help_text: str) -> list[LeafSpec]:
    sub_action = next((a for a in parser._actions if _is_subparsers(a)), None)
    if sub_action is None:
        return [LeafSpec(path, chain, help_text)]
    leaves: list[LeafSpec] = []
    for name, sub in sub_action.choices.items():
        sub_help = getattr(sub, "description", None) or (sub._subparsers and "") or name
        leaves.extend(
            _collect_leaves(sub, path + [name], chain + [sub], sub_help or help_text)
        )
    return leaves


def _json_type(action: argparse.Action) -> str:
    t = action.type
    if t is int or t == int:
        return "integer"
    if t is float or t == float:
        return "number"
    return "string"


def _is_const_flag(action: argparse.Action) -> bool:
    return isinstance(action, argparse._StoreConstAction)


def _flag_pair(action: argparse.Action) -> list[str]:
    """Return [positive_flag, negative_flag_or_None] for boolean-ish actions."""
    opts = list(action.option_strings)
    neg = None
    if len(opts) >= 2:
        # BooleanOptionalAction: --foo / --no-foo
        for o in opts:
            if o.startswith("--no-"):
                neg = o
                opts.remove(o)
                break
    return [opts[0], neg]


def _action_schema(action: argparse.Action) -> tuple[str, dict, bool, bool, bool]:
    """Return (dest, property_schema, is_positional, is_const_flag, has_subparsers)."""
    if _is_subparsers(action):
        return (action.dest, {}, False, False, True)

    prop: dict[str, Any] = {"description": (action.help or "").replace("%", "%%")}
    is_positional = not action.option_strings
    is_const = _is_const_flag(action)

    if is_const:
        prop["type"] = "boolean"
    elif action.nargs in ("+", "*") or (isinstance(action.nargs, int) and action.nargs > 1):
        prop["type"] = "array"
        prop["items"] = {"type": _json_type(action)}
    else:
        prop["type"] = _json_type(action)
        if action.choices:
            prop["enum"] = list(action.choices)

    if action.choices and not is_const and action.nargs not in ("+", "*"):
        prop["enum"] = list(action.choices)

    # required
    required = bool(is_positional) or bool(action.required)
    if required:
        prop["description"] = (prop["description"] + " (required)").strip()

    # default (skip const flags and None defaults)
    if not is_const and action.default is not None and action.default is not argparse.SUPPRESS:
        d = action.default
        if isinstance(d, (str, int, float, bool, list)):
            prop["default"] = d

    return (action.dest, prop, is_positional, is_const, False)


def _leaf_schema(spec: LeafSpec) -> dict[str, Any]:
    """Build JSON schema for one leaf command (positionals then optionals)."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for parser in spec.chain:
        for action in parser._actions:
            if _is_subparsers(action):
                continue
            dest, prop, is_positional, is_const, _ = _action_schema(action)
            if dest == "help":
                continue
            if dest in properties:  # deeper parser wins
                continue
            properties[dest] = prop
            if (is_positional or action.required) and not is_const:
                required.append(dest)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _leaf_tool_name(spec: LeafSpec) -> str:
    return "_".join(spec.path).replace("-", "_")


# ── argv reconstruction ────────────────────────────────────────────────────
def _emit_optionals(parser: argparse.ArgumentParser, args: dict[str, Any], argv: list[str], format_json: bool) -> list[str]:
    for action in parser._actions:
        if _is_subparsers(action) or action.dest == "help" or action.dest not in args:
            continue
        dest = action.dest
        value = args[dest]
        if _is_const_flag(action):
            if value is True:
                pos, _neg = _flag_pair(action)
                argv.append(pos)
            elif value is False and _flag_pair(action)[1]:
                argv.append(_flag_pair(action)[1])
            continue
        flag = action.option_strings[0] if action.option_strings else None
        if flag is None:
            continue
        if isinstance(value, list):
            for v in value:
                argv += [flag, str(v)]
        else:
            argv += [flag, str(value)]
    if format_json and "--format" not in argv:
        argv += ["--format", "json"]
    return argv


def _emit_positionals(parser: argparse.ArgumentParser, args: dict[str, Any], argv: list[str]) -> list[str]:
    for action in parser._actions:
        if _is_subparsers(action) or action.dest == "help" or action.dest not in args:
            continue
        if action.option_strings:  # not a positional
            continue
        value = args[action.dest]
        if isinstance(value, list):
            argv += [str(v) for v in value]
        else:
            argv.append(str(value))
    return argv


def _has_json_format(parser: argparse.ArgumentParser) -> bool:
    for action in parser._actions:
        if action.dest == "format" and action.choices and "json" in action.choices:
            return True
    return False


def _build_argv(spec: LeafSpec, arguments: dict[str, Any]) -> list[str]:
    argv: list[str] = []
    # options of intermediate parsers must precede the next subcommand token;
    # the leaf's positionals must follow its token, then leaf optionals.
    for i, parser in enumerate(spec.chain):
        is_leaf = i == len(spec.chain) - 1
        format_json = not is_leaf and _has_json_format(parser) or (is_leaf and _has_json_format(parser) and "format" not in arguments)
        if not is_leaf:
            _emit_optionals(parser, arguments, argv, format_json)
            argv.append(spec.path[i])
        else:
            _emit_positionals(parser, arguments, argv)
            _emit_optionals(parser, arguments, argv, format_json)
    return argv


# ── MCP server ─────────────────────────────────────────────────────────────
server = Server(SERVER_NAME)

_all_leaves = _collect_leaves(root_parser, [], [root_parser], getattr(root_parser, "description", SERVER_NAME))


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    tools = []
    for spec in _all_leaves:
        tools.append(
            types.Tool(
                name=_leaf_tool_name(spec),
                description=spec.help_text,
                inputSchema=_leaf_schema(spec),
            )
        )
    return tools


@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    try:
        spec = next((s for s in _all_leaves if _leaf_tool_name(s) == name), None)
        if spec is None:
            raise ValueError(f"Unknown tool: {name}")

        argv = _build_argv(spec, arguments)

        old_argv = sys.argv
        out, err = io.StringIO(), io.StringIO()
        code = 0
        try:
            sys.argv = [TOOL_SCRIPT] + argv
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                ret = _main()
            if isinstance(ret, int):
                code = ret
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (1 if exc.code is not None else 0)
        finally:
            sys.argv = old_argv

        stdout, stderr = out.getvalue(), err.getvalue()

        # Try to surface the tool's JSON output directly; fall back to text.
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = {"output": stdout}

        if code != 0:
            payload = {"error": stderr.strip() or stdout.strip() or f"exit code {code}", "exit_code": code}

        return [types.TextContent(type="text", text=json.dumps(payload, indent=2, ensure_ascii=False))]

    except Exception as exc:
        _log("error", f"Tool {name} failed: {exc}")
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}, indent=2))]


async def main() -> None:
    _log("info", f"Starting {SERVER_NAME}-mcp adapter wrapping {TOOL_SCRIPT}")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
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
