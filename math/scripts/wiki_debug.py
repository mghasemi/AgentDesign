#!/usr/bin/env python3
"""Debug: check PocketBase auth and pending items."""

import urllib.request
import json

PB_BASE = "http://YOUR-HOST:8090"
TOKEN_FILE = "/home/YOUR-USER/.hermes/profiles/math/home/YOUR-USER.txt"

# Re-auth first
req = urllib.request.Request(
    f"{PB_BASE}/api/collections/_superusers/auth-with-password",
    data=json.dumps({"identity": "YOUR-EMAIL", "password": "BMW518@ibm"}).encode(),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read().decode())
    token = result["token"]

with open(TOKEN_FILE, "w") as f:
    f.write(token)

print(f"Auth OK. Token length: {len(token)}")

# Now query all records (not just pending) to see what's there
req2 = urllib.request.Request(
    f"{PB_BASE}/api/collections/wiki_ingestion/records?perPage=500"
)
req2.add_header("Authorization", token)
with urllib.request.urlopen(req2, timeout=15) as resp:
    data = json.loads(resp.read().decode())

items = data.get("items", [])
print(f"\nTotal records: {len(items)}")

pending = [i for i in items if not i.get("ingested")]
processed = [i for i in items if i.get("ingested")]
print(f"Pending (ingested=false): {len(pending)}")
print(f"Processed (ingested=true): {len(processed)}")

if pending:
    print("\n--- Pending items ---")
    for item in pending[:5]:
        print(f"  ID: {item['id']}, Title: {item.get('title','?')}, Type: {item.get('source_type','?')}, URL: {item.get('source_url','?')}")

if processed:
    print("\n--- Last 3 processed ---")
    for item in processed[-3:]:
        print(f"  ID: {item['id']}, Title: {item.get('title','?')}, Processed: {item.get('date_processed','?')}")
