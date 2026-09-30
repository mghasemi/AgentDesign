#!/usr/bin/env python3
"""pb_ingest.py — Reliable wiki-ingestion record insertion into PocketBase.

Usage:
    pb_ingest.py [--title "Title"] <source_url> <source_type>

    source_type: pdf | arxiv | webpage | other

Examples:
    pb_ingest.py /path/to/paper.pdf pdf --title "A Great Paper"
    pb_ingest.py https://arxiv.org/abs/1234.56789 arxiv
    pb_ingest.py https://example.com/article webpage --title "Some Article"

Credentials: reads admin token from ~/.hermes/profiles/math/home/YOUR-USER.txt
or the PB_TOKEN environment variable.

Exit codes: 0=success, 1=connectivity/preflight, 2=validation, 3=insert error
"""

import json, os, sys, time, urllib.error, urllib.request
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────
PB_HOST = "YOUR-HOST"
PB_PORT = 8090
COLLECTION = "wiki_ingestion"
TOKEN_FILE = Path("/home/YOUR-USER/.hermes/profiles/math/home/YOUR-USER.txt")

VALID_TYPES = {"pdf", "arxiv", "webpage", "other"}


# ──────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────
def load_token():
    if os.environ.get("PB_TOKEN"):
        return os.environ["PB_TOKEN"].strip()
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None


def pb_url(path=""):
    return f"http://{PB_HOST}:{PB_PORT}/api/{path.lstrip('/')}"


def api_request(method, path, data=None, *, timeout=15):
    """Return (status, body_dict). Raise urllib.error.URLError on IO errors."""
    url = pb_url(path)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode() if e.fp else ""
        return e.code, json.loads(detail) if detail.strip() else {"error": detail}


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


# ──────────────────────────────────────────
#  Pre-flight checks
# ──────────────────────────────────────────
def preflight():
    """Verify connectivity, auth, and that the target collection exists."""
    # 1 - Connectivity
    print("→ Checking connectivity...", end=" ", flush=True)
    try:
        urllib.request.urlopen(pb_url("health"), timeout=5)
    except OSError as e:
        print("FAIL")
        die(f"PocketBase unreachable at {PB_HOST}:{PB_PORT} — {e}")
    print("OK")

    # 2 - Auth
    print("→ Checking auth...", end=" ", flush=True)
    status, body = api_request("GET", "collections")
    if status != 200:
        print("FAIL")
        die(f"Auth rejected (HTTP {status}): {body.get('message', body)}")
    print("OK")

    # 3 - Collection exists
    print(f"→ Checking collection '{COLLECTION}'...", end=" ", flush=True)
    status, body = api_request("GET", f"collections/{COLLECTION}")
    if status != 200:
        print("FAIL")
        die(f"Collection '{COLLECTION}' not found (HTTP {status}). "
            f"Run wiki-pipeline setup first.")
    print("OK")

    # 4 - Warn on suspicious flags
    sys_flag = body.get("system", False)
    if sys_flag:
        print(f"  ⚠  Collection '{COLLECTION}' has system=True — API writes may be blocked.")

    return body  # collection schema


# ──────────────────────────────────────────
#  Insertion
# ──────────────────────────────────────────
def insert_record(source_url: str, source_type: str, title: str = ""):
    """Insert one wiki_ingestion record. Returns the record dict on success."""
    data = {
        "source_url": source_url,
        "source_type": source_type,
        "title": title or "",
        "date_added": date.today().isoformat(),
        "ingested": False,
    }

    print(f"→ Inserting record...", end=" ", flush=True)
    status, body = api_request("POST", f"collections/{COLLECTION}/records", data)

    if status == 200:
        print("OK")
        return body

    # ── Parse error ──
    errors = body.get("data", {})
    messages = []

    if isinstance(errors, dict):
        for field, detail in errors.items():
            if isinstance(detail, dict):
                messages.append(f"{field}: {detail.get('message', detail)}")
            else:
                messages.append(f"{field}: {detail}")

    if not messages and body.get("message"):
        messages.append(body["message"])
    elif not messages:
        messages.append(f"HTTP {status}: {json.dumps(body)[:200]}")

    print("FAIL")
    die(" | ".join(messages), code=3 if status >= 400 else 2)


# ──────────────────────────────────────────
#  Main
# ──────────────────────────────────────────
def main():
    global TOKEN

    import argparse

    parser = argparse.ArgumentParser(
        description="Insert a wiki-ingestion record into PocketBase"
    )
    parser.add_argument("source_url", help="File path, arXiv URL, or webpage URL")
    parser.add_argument(
        "source_type",
        choices=sorted(VALID_TYPES),
        help="Source type",
    )
    parser.add_argument("--title", default="", help="Optional title for the record")
    args = parser.parse_args()

    # ── Validate source exists (for PDFs) ──
    if args.source_type == "pdf":
        p = Path(args.source_url)
        if not p.exists():
            die(f"PDF file not found: {args.source_url}")
        if p.suffix.lower() != ".pdf":
            die(f"Not a .pdf file: {args.source_url}")

    # ── Auth ──
    TOKEN = load_token()
    if not TOKEN:
        die(
            "No PB token found. Set PB_TOKEN env var "
            f"or place it at {TOKEN_FILE}"
        )

    # ── Run ──
    print(f"PB Ingest — {COLLECTION}")
    print(f"  source:  {args.source_url}")
    print(f"  type:    {args.source_type}")
    if args.title:
        print(f"  title:   {args.title}")

    preflight()
    record = insert_record(args.source_url, args.source_type, args.title)

    print(f"\n✓ Inserted record {record['id']}")
    print(f"  ingested: {record.get('ingested', False)}")
    print(f"  date_added: {record.get('date_added', '?')}")


if __name__ == "__main__":
    main()
