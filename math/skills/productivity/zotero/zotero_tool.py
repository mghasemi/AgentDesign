#!/usr/bin/env python3
"""CLI for Zotero bibliography management via pyzotero."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any


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


DEFAULT_LIBRARY_TYPE = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
DEFAULT_LIBRARY_ID = os.environ.get("ZOTERO_LIBRARY_ID", "ZOTERO_LIBRARY_ID")
DEFAULT_API_KEY = os.environ.get("ZOTERO_API_KEY", "")
DEFAULT_BIB_PATH = os.environ.get("ZOTERO_BIB_PATH", "")


def _require_pyzotero() -> Any:
    try:
        from pyzotero import zotero  # noqa: PLC0415
        return zotero
    except ImportError:
        _fail("pyzotero is not installed. Run: pip install pyzotero")


def _fail(message: str, fmt: str = "text") -> None:
    if fmt == "json":
        print(json.dumps({"success": False, "error": message}))
    else:
        print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def _get_client(zotero_mod: Any) -> Any:
    if not DEFAULT_LIBRARY_ID:
        _fail("ZOTERO_LIBRARY_ID is not set.")
    if not DEFAULT_API_KEY:
        _fail("ZOTERO_API_KEY is not set.")
    return zotero_mod.Zotero(DEFAULT_LIBRARY_ID, DEFAULT_LIBRARY_TYPE, DEFAULT_API_KEY)


def _item_to_summary(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data", {})
    creators = data.get("creators", [])
    authors = [
        f"{c.get('lastName', '')} {c.get('firstName', '')}".strip()
        for c in creators
        if c.get("creatorType") == "author"
    ]
    return {
        "key": item.get("key", ""),
        "title": data.get("title", ""),
        "authors": authors,
        "year": data.get("date", "")[:4] if data.get("date") else "",
        "doi": data.get("DOI", ""),
        "url": data.get("url", ""),
        "item_type": data.get("itemType", ""),
    }


def _bibtex_key(item_data: dict[str, Any]) -> str:
    creators = item_data.get("creators", [])
    last_name = ""
    for c in creators:
        if c.get("creatorType") == "author":
            last_name = c.get("lastName", "").lower().replace(" ", "")
            break
    year = (item_data.get("date") or "")[:4]
    title_words = (item_data.get("title") or "").split()
    first_word = title_words[0].lower() if title_words else "unknown"
    return f"{last_name}{year}{first_word}"


def _resolve_collection_key(zot: Any, collection: str) -> str:
    colls = zot.collections()
    exact: str | None = None
    partial: str | None = None

    for coll in colls:
        key = coll.get("key", "")
        name = coll.get("data", {}).get("name", "")
        if collection == key:
            return key
        if name == collection:
            exact = key
        if partial is None and collection.lower() in name.lower():
            partial = key

    if exact:
        return exact
    if partial:
        return partial
    raise RuntimeError(f"Collection '{collection}' not found.")


def cmd_add_paper(zotero_mod: Any, args: argparse.Namespace) -> dict[str, Any]:
    zot = _get_client(zotero_mod)

    template = zot.item_template("journalArticle")

    if args.arxiv:
        arxiv_id = args.arxiv.replace("arXiv:", "").strip()
        template["url"] = f"https://arxiv.org/abs/{arxiv_id}"
        template["title"] = f"arXiv:{arxiv_id}"
        template["archiveID"] = f"arXiv:{arxiv_id}"
        template["libraryCatalog"] = "arXiv"
    elif args.doi:
        template["DOI"] = args.doi
    else:
        _fail("Provide --arxiv or --doi.", args.format)

    if args.collection:
        coll_key = _resolve_collection_key(zot, args.collection)
        template["collections"] = [coll_key]

    resp = zot.create_items([template])
    created = resp.get("successful", {})
    if not created:
        return {"success": False, "error": "Zotero did not confirm item creation.", "command": "add-paper"}

    key = list(created.values())[0].get("key", "")
    item_data = list(created.values())[0].get("data", {})
    return {
        "command": "add-paper",
        "key": key,
        "title": item_data.get("title", ""),
        "bibtex_key": _bibtex_key(item_data),
        "success": True,
    }


def cmd_search(zotero_mod: Any, args: argparse.Namespace) -> dict[str, Any]:
    zot = _get_client(zotero_mod)
    items = zot.items(q=args.query, limit=20)
    results = [_item_to_summary(i) for i in items]
    return {"command": "search", "query": args.query, "count": len(results), "results": results, "success": True}


def cmd_export_bibtex(zotero_mod: Any, args: argparse.Namespace) -> dict[str, Any]:
    zot = _get_client(zotero_mod)
    if args.collection:
        coll_key = _resolve_collection_key(zot, args.collection)
        bibtex = zot.collection_items(coll_key, format="bibtex")
    else:
        bibtex = zot.items(format="bibtex")

    output_path = args.output or DEFAULT_BIB_PATH
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(bibtex)
    return {
        "command": "export-bibtex",
        "chars": len(bibtex),
        "output": output_path or "(stdout)",
        "bibtex": bibtex if not output_path else None,
        "success": True,
    }


def cmd_sync_bib(zotero_mod: Any, args: argparse.Namespace) -> dict[str, Any]:
    args.output = args.output or DEFAULT_BIB_PATH
    if not args.output:
        _fail("Provide --output or set ZOTERO_BIB_PATH.", args.format)
    return cmd_export_bibtex(zotero_mod, args)


def cmd_list_collections(zotero_mod: Any, args: argparse.Namespace) -> dict[str, Any]:
    zot = _get_client(zotero_mod)
    colls = zot.collections()
    results = []
    for coll in colls:
        data = coll.get("data", {})
        results.append(
            {
                "key": coll.get("key", ""),
                "name": data.get("name", ""),
                "parent": data.get("parentCollection") or "",
            }
        )
    return {"command": "list-collections", "count": len(results), "results": results, "success": True}


def cmd_create_collection(zotero_mod: Any, args: argparse.Namespace) -> dict[str, Any]:
    zot = _get_client(zotero_mod)
    payload: dict[str, Any] = {"name": args.name}
    if args.parent:
        payload["parentCollection"] = _resolve_collection_key(zot, args.parent)

    if hasattr(zot, "create_collections"):
        resp = zot.create_collections([payload])
    else:
        raise RuntimeError("Installed pyzotero version does not support create_collections")

    successful = resp.get("successful", {}) if isinstance(resp, dict) else {}
    if not successful:
        return {"command": "create-collection", "success": False, "error": "Collection creation not confirmed"}

    first = list(successful.values())[0]
    return {
        "command": "create-collection",
        "key": first.get("key", ""),
        "name": first.get("data", {}).get("name", args.name),
        "success": True,
    }


def cmd_add_to_collection(zotero_mod: Any, args: argparse.Namespace) -> dict[str, Any]:
    zot = _get_client(zotero_mod)
    coll_key = _resolve_collection_key(zot, args.collection)
    item = zot.item(args.item_key)
    if not item:
        raise RuntimeError(f"Item '{args.item_key}' not found")

    data = item.get("data", {})
    collections = data.get("collections", [])
    if coll_key not in collections:
        collections.append(coll_key)
        data["collections"] = collections

    if hasattr(zot, "update_item"):
        zot.update_item(item)
    else:
        raise RuntimeError("Installed pyzotero version does not support update_item")

    return {
        "command": "add-to-collection",
        "item_key": args.item_key,
        "collection_key": coll_key,
        "success": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Zotero bibliography management CLI")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add-paper", help="Add a paper by DOI or arXiv ID")
    p_add.add_argument("--doi", default=None)
    p_add.add_argument("--arxiv", default=None)
    p_add.add_argument("--collection", default=None)
    p_add.add_argument("--format", choices=["text", "json"], default="text")

    p_search = sub.add_parser("search", help="Search Zotero library")
    p_search.add_argument("query")
    p_search.add_argument("--format", choices=["text", "json"], default="text")

    p_export = sub.add_parser("export-bibtex", help="Export BibTeX from library or collection")
    p_export.add_argument("--collection", default=None)
    p_export.add_argument("--output", default=None, help="Output .bib file path")
    p_export.add_argument("--format", choices=["text", "json"], default="text")

    p_sync = sub.add_parser("sync-bib", help="Sync local .bib file")
    p_sync.add_argument("--collection", default=None)
    p_sync.add_argument("--output", default=None, help="Output .bib file path (overrides ZOTERO_BIB_PATH)")
    p_sync.add_argument("--format", choices=["text", "json"], default="text")

    p_list = sub.add_parser("list-collections", help="List library collections")
    p_list.add_argument("--format", choices=["text", "json"], default="text")

    p_create_collection = sub.add_parser("create-collection", help="Create a collection")
    p_create_collection.add_argument("--name", required=True)
    p_create_collection.add_argument("--parent", default=None, help="Parent collection name or key")
    p_create_collection.add_argument("--format", choices=["text", "json"], default="text")

    p_add_to_collection = sub.add_parser("add-to-collection", help="Attach an item to a collection")
    p_add_to_collection.add_argument("--item-key", required=True)
    p_add_to_collection.add_argument("--collection", required=True, help="Collection name or key")
    p_add_to_collection.add_argument("--format", choices=["text", "json"], default="text")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    fmt = getattr(args, "format", "text")
    zotero_mod = _require_pyzotero()

    dispatch = {
        "add-paper": cmd_add_paper,
        "search": cmd_search,
        "export-bibtex": cmd_export_bibtex,
        "sync-bib": cmd_sync_bib,
        "list-collections": cmd_list_collections,
        "create-collection": cmd_create_collection,
        "add-to-collection": cmd_add_to_collection,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        _fail(f"Unknown command: {args.command}", fmt)

    try:
        data = handler(zotero_mod, args)
    except Exception as exc:
        _fail(str(exc), fmt)
        return

    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if args.command == "search":
            for r in data.get("results", []):
                print(f"[{r['key']}] {r['title']} ({r['year']}) — {', '.join(r['authors'])}")
        elif args.command == "list-collections":
            for r in data.get("results", []):
                parent = f" parent={r['parent']}" if r.get("parent") else ""
                print(f"[{r['key']}] {r['name']}{parent}")
        elif args.command in ("export-bibtex", "sync-bib"):
            if data.get("bibtex"):
                print(data["bibtex"])
            else:
                print(f"Written to: {data.get('output')}")
        elif args.command == "create-collection":
            print(f"Created collection: key={data.get('key')} name={data.get('name')}")
        elif args.command == "add-to-collection":
            print(f"Added item {data.get('item_key')} to collection {data.get('collection_key')}")
        else:
            print(f"Added: key={data.get('key')} bibtex_key={data.get('bibtex_key')}")


if __name__ == "__main__":
    main()
