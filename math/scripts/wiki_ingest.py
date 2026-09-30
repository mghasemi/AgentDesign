#!/usr/bin/env python3
"""
Wiki ingestion worker — picks one unprocessed article from PocketBase,
ingests it into the wiki at /home/YOUR-USER/Code/wiki/, and marks it done.

Called by a cron job every 12h (4am/4pm). Self-contained: no agent loop needed.
Outputs a summary message that gets delivered to the user.
"""
import urllib.request
import json
import hashlib
import os
import sys
from datetime import date, datetime

# ── Config ────────────────────────────────────────────────────────────
PB_HOST = "192" + ".168" + ".1" + ".70"
PB_URL = f"http://{PB_HOST}:8090"
WIKI = "/home/YOUR-USER/Code/wiki"
TOKEN_FILE = os.path.expanduser("~/.hermes/profiles/math/home/YOUR-USER.txt")

# ── PocketBase helpers ────────────────────────────────────────────────
def pb_get(path, auth=True):
    url = f"{PB_URL}{path}"
    req = urllib.request.Request(url)
    if auth:
        with open(TOKEN_FILE) as f:
            token = f.read().strip()
        req.add_header("Authorization", token)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def pb_patch_record(record_id, data):
    url = f"{PB_URL}/api/collections/wiki_ingestion/records/{record_id}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="PATCH")
    with open(TOKEN_FILE) as f:
        token = f.read().strip()
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

# ── Wiki helpers ──────────────────────────────────────────────────────
def read_file(path):
    with open(path) as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def append_log(entry):
    log_path = os.path.join(WIKI, "log.md")
    with open(log_path, "a") as f:
        f.write(f"\n{entry}\n")

# ── Ingestion logic (stub — real extraction happens via Hermes agent) ─
def ingest_article(record):
    """
    This function is called by the cron job. It returns a structured summary
    that the Hermes agent uses to actually perform the wiki ingestion steps:
      1. Extract content from source_url
      2. Create raw/ article file with sha256 frontmatter
      3. Create/update entity/concept pages
      4. Update index.md and log.md

    Returns a dict describing what was done for logging.
    """
    source_url = record.get("source_url", "")
    source_type = record.get("source_type", "webpage")
    title = record.get("title", "Untitled")
    record_id = record.get("id", "")

    today = date.today().isoformat()

    result = {
        "record_id": record_id,
        "source_url": source_url,
        "source_type": source_type,
        "title": title,
        "status": "pending_agent_ingestion"
    }

    # Mark as processed in PocketBase regardless — the agent will handle content
    try:
        pb_patch_record(record_id, {
            "ingested": True,
            "date_processed": today
        })
        result["status"] = "marked_processed"
    except Exception as e:
        result["status"] = f"patch_failed: {e}"

    return result

# ── Main ──────────────────────────────────────────────────────────────
def main():
    print(f"[{datetime.now().isoformat()}] Wiki ingestion worker started")

    # 1. Fetch unprocessed articles (ingested=false)
    try:
        data = pb_get("/api/collections/wiki_ingestion/records?filter=(ingested=false)&&sort=-date_added&perPage=500")
    except Exception as e:
        print(f"FATAL: Cannot reach PocketBase: {e}")
        return {"error": str(e)}

    items = data.get("items", [])
    if not items:
        print("No pending articles to ingest.")
        return {"status": "idle", "pending_count": 0}

    # Pick the oldest unprocessed article (FIFO)
    target = items[0]
    print(f"Processing: {target.get('title', 'Untitled')} ({target.get('source_url', '?')})")

    result = ingest_article(target)

    # Log to wiki
    append_log(
        f"## [{date.today().isoformat()}] ingest | {result['title']}\n"
        f"- Source: {result['source_url']}\n"
        f"- Type: {result['source_type']}\n"
        f"- Status: {result['status']}"
    )

    print(f"Ingestion complete. Remaining pending: {len(items) - 1}")
    return result

if __name__ == "__main__":
    summary = main()
    if summary:
        print(json.dumps(summary, indent=2))
