#!/usr/bin/env python3
"""CLI for SiYuan read/write operations used by MathAgent workflows."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


def _load_emv() -> None:
    current = Path(__file__).resolve().parent
    while True:
        emv_path = current / ".emv"
        if emv_path.is_file():
            for raw_line in emv_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[7:].strip()
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key not in os.environ or not os.environ.get(key):
                    os.environ[key] = value
            break
        if current.parent == current:
            break
        current = current.parent


_load_emv()


DEFAULT_URL = os.environ.get("SIYUAN_URL", "http://YOUR-HOST:6806")
DEFAULT_ALT_URL = os.environ.get("SIYUAN_ALT_URL", "")
DEFAULT_TOKEN = os.environ.get("SIYUAN_TOKEN", "")
DEFAULT_NOTEBOOK = os.environ.get("SIYUAN_NOTEBOOK", "")


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "note"


def _request(path: str, payload: dict[str, Any], token: str, urls: list[str]) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"

    errors: list[str] = []
    saw_unauthorized = False
    for base_url in urls:
        if not base_url:
            continue
        try:
            response = requests.post(f"{base_url}{path}", json=payload, headers=headers, timeout=15)
            if response.status_code in (401, 403):
                saw_unauthorized = True
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("code", 0) != 0:
                errors.append(f"{base_url}: {data.get('msg', 'unknown SiYuan API error')}")
                continue
            return data
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{base_url}: {exc}")

    if saw_unauthorized:
        raise RuntimeError(
            "SiYuan authentication failed (401/403). Set SIYUAN_TOKEN (or pass --token) with a valid API token. "
            + "Tried URLs: "
            + " | ".join(errors)
        )

    raise RuntimeError("Unable to reach SiYuan server. Tried URLs: " + " | ".join(errors))


def _list_notebooks(token: str, urls: list[str]) -> dict[str, Any]:
    return _request("/api/notebook/lsNotebooks", {}, token, urls)


def _resolve_notebook_id(explicit_notebook: str, token: str, urls: list[str]) -> str:
    if explicit_notebook:
        return explicit_notebook
    if DEFAULT_NOTEBOOK:
        return DEFAULT_NOTEBOOK

    data = _list_notebooks(token, urls)
    notebooks = data.get("data", {}).get("notebooks", [])
    if not notebooks:
        raise RuntimeError("No notebooks available in SiYuan. Provide --notebook explicitly.")

    for notebook in notebooks:
        if not notebook.get("closed", False):
            return notebook.get("id", "")
    return notebooks[0].get("id", "")


def search_notes(query: str, token: str, urls: list[str]) -> dict[str, Any]:
    # Use LIKE matching for document name/content lookup.
    safe_query = query.replace("'", "''")
    stmt = (
        "SELECT * FROM blocks "
        f"WHERE (content LIKE '%{safe_query}%' OR attribute LIKE '%{safe_query}%') "
        "AND type='d' LIMIT 10"
    )
    return _request("/api/query/sql", {"stmt": stmt}, token, urls)


def get_content(block_id: str, token: str, urls: list[str]) -> dict[str, Any]:
    return _request("/api/export/exportMdContent", {"id": block_id}, token, urls)


def create_doc_with_md(notebook: str, path: str, markdown: str, token: str, urls: list[str]) -> dict[str, Any]:
    payload = {"notebook": notebook, "path": path, "markdown": markdown}
    return _request("/api/filetree/createDocWithMd", payload, token, urls)


def append_block(parent_id: str, markdown: str, token: str, urls: list[str]) -> dict[str, Any]:
    payload = {"data": markdown, "dataType": "markdown", "parentID": parent_id}
    return _request("/api/block/appendBlock", payload, token, urls)


def update_block(block_id: str, markdown: str, token: str, urls: list[str]) -> dict[str, Any]:
    payload = {"dataType": "markdown", "data": markdown, "id": block_id}
    return _request("/api/block/updateBlock", payload, token, urls)


def create_block(title: str, content: str, notebook: str, token: str, urls: list[str]) -> dict[str, Any]:
    notebook_id = _resolve_notebook_id(notebook, token, urls)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = _safe_slug(title)
    path = f"/mathagent/{timestamp}-{slug}"
    markdown = f"# {title}\n\n{content}\n"
    return create_doc_with_md(notebook_id, path, markdown, token, urls)


def set_block_attrs(block_id: str, attrs: dict[str, str], token: str, urls: list[str]) -> dict[str, Any]:
    payload = {"id": block_id, "attrs": attrs}
    return _request("/api/attr/setBlockAttrs", payload, token, urls)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SiYuan CLI")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--alt-url", default=DEFAULT_ALT_URL)
    parser.add_argument("--token", default=DEFAULT_TOKEN)
    parser.add_argument("--format", choices=["json", "text"], default="json")

    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search notes by keyword")
    p_search.add_argument("query")

    p_get = sub.add_parser("get", help="Export markdown by block/doc id")
    p_get.add_argument("id")

    p_create_block = sub.add_parser("create-block", help="Create a report note from title/content")
    p_create_block.add_argument("--title", required=True)
    p_create_block.add_argument("--content", required=True)
    p_create_block.add_argument("--notebook", default="")

    p_create_doc = sub.add_parser("create-doc", help="Create document with markdown at path")
    p_create_doc.add_argument("--notebook", default="")
    p_create_doc.add_argument("--path", required=True)
    p_create_doc.add_argument("--markdown", required=True)

    p_append = sub.add_parser("append-block", help="Append markdown block under parent id")
    p_append.add_argument("--parent-id", required=True)
    p_append.add_argument("--content", required=True)

    p_update = sub.add_parser("update-block", help="Update a block markdown")
    p_update.add_argument("--id", required=True)
    p_update.add_argument("--content", required=True)

    p_attrs = sub.add_parser("set-attrs", help="Set custom attributes on a block")
    p_attrs.add_argument("--id", required=True)
    p_attrs.add_argument("--attrs", required=True, help='JSON object, e.g. {"custom-stage":"3"}')

    return parser


def _emit(data: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print(data)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    urls = [args.url, args.alt_url]

    try:
        if args.command == "search":
            data = search_notes(args.query, args.token, urls)
        elif args.command == "get":
            data = get_content(args.id, args.token, urls)
        elif args.command == "create-block":
            data = create_block(args.title, args.content, args.notebook, args.token, urls)
        elif args.command == "create-doc":
            notebook_id = _resolve_notebook_id(args.notebook, args.token, urls)
            data = create_doc_with_md(notebook_id, args.path, args.markdown, args.token, urls)
        elif args.command == "append-block":
            data = append_block(args.parent_id, args.content, args.token, urls)
        elif args.command == "update-block":
            data = update_block(args.id, args.content, args.token, urls)
        elif args.command == "set-attrs":
            attrs = json.loads(args.attrs)
            if not isinstance(attrs, dict):
                raise RuntimeError("--attrs must be a JSON object")
            data = set_block_attrs(args.id, attrs, args.token, urls)
        else:
            raise RuntimeError(f"Unsupported command: {args.command}")

        _emit(data, args.format)
    except Exception as exc:
        if args.format == "json":
            print(json.dumps({"success": False, "error": str(exc)}))
        else:
            print(f"ERROR: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
