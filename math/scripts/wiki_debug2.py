#!/usr/bin/env python3
"""Double-check pending items with alternate filter syntax."""

import urllib.request
import json

PB_BASE = "http://YOUR-HOST:8090"
TOKEN_FILE = "/home/YOUR-USER/.hermes/profiles/math/home/YOUR-USER.txt"

with open(TOKEN_FILE) as f:
    token = f.read().strip()

# Try alternate filter syntaxes for PocketBase v0.39+
filters = [
    "(ingested=False)",
    '(ingested="false")',
    "(ingested!=true)",
    "(ingested=null)",
]

for filt in filters:
    req = urllib.request.Request(
        f"{PB_BASE}/api/collections/wiki_ingestion/records?filter={filt}&perPage=500"
    )
    req.add_header("Authorization", token)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    items = data.get("items", [])
    print(f"Filter '{filt}' => {len(items)} results")

# Also check the raw record to see what ingested values look like
req2 = urllib.request.Request(
    f"{PB_BASE}/api/collections/wiki_ingestion/records?perPage=16&sort=-date_added"
)
req2.add_header("Authorization", token)
with urllib.request.urlopen(req2, timeout=15) as resp:
    data = json.loads(resp.read().decode())

for item in data.get("items", []):
    ingested_val = item.get("ingested")
    print(f"  ID={item['id'][:8]}... ingested={repr(ingested_val)} (type={type(ingested_val).__name__}) title={item.get('title','')[:60]}")
