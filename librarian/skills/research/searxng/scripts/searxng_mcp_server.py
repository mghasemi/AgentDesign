#!/usr/bin/env python3
"""MCP server for SearXNG — privacy-respecting metasearch via local instance.

Exposes SearXNG's JSON API as MCP tools so Hermes can call it natively
(tool names are prefixed ``mcp_searxng_*``). This is a real MCP stdio
server speaking JSON-RPC over stdin/stdout; it is NOT the argparse CLI
(``searxng.py``), which is kept for interactive terminal use.

Tools:
  search  — web search via the local SearXNG instance
"""

from __future__ import annotations

import json
import os
import sys
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

# ── reuse the search logic from the CLI companion script ──────────────────
# The script lives in the same directory as searxng.py; sys.path[0] is the
# script's own directory when run as a file, so a plain import works.
try:
    from searxng import search_searxng
except ImportError:  # pragma: no cover — defensive; same dir guaranteed
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from searxng import search_searxng

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://YOUR-HOST:5050")

CATEGORIES = ["general", "images", "videos", "news", "map", "music", "files", "it", "science"]


def _log(level: str, msg: str) -> None:
    print(f"[searxng-mcp] {level}: {msg}", file=sys.stderr, flush=True)


server = Server("searxng")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search",
            description=(
                f"Search the web using the local SearXNG instance at {SEARXNG_URL}. "
                "Returns JSON results (title, url, content, engines)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string"},
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (default 10)",
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "category": {
                        "type": "string",
                        "description": "Search category",
                        "enum": CATEGORIES,
                        "default": "general",
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (auto, en, de, fr, ...)",
                        "default": "auto",
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range filter",
                        "enum": ["day", "week", "month", "year"],
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    try:
        if name == "search":
            query = arguments["query"]
            limit = int(arguments.get("limit", 10))
            category = arguments.get("category", "general")
            language = arguments.get("language", "auto")
            time_range = arguments.get("time_range")

            if category not in CATEGORIES:
                raise ValueError(
                    f"Invalid category '{category}'. Allowed: {', '.join(CATEGORIES)}"
                )

            data = search_searxng(
                query=query,
                limit=limit,
                category=category,
                language=language,
                time_range=time_range,
                output_format="json",
            )
            payload = {
                "tool": name,
                "query": query,
                "limit": limit,
                "category": category,
                "language": language,
                "time_range": time_range,
                "url": f"{SEARXNG_URL}/search",
                **data,
            }
            return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as exc:
        _log("error", f"Tool {name} failed: {exc}")
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}, indent=2))]


# ── main entry point ────────────────────────────────────────────────────────
async def main() -> None:
    _log("info", f"Starting searxng-mcp server (SEARXNG_URL: {SEARXNG_URL})")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="searxng",
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
