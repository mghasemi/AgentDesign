#!/usr/bin/env python3
"""Mark article as ingested in PocketBase."""
import urllib.request, json
from datetime import date

TOKEN_FILE = "/home/YOUR-USER/.hermes/profiles/math/home/YOUR-USER.txt"
PB_BASE = "http://YOUR-HOST:8090/api"
RECORD_ID = "4upbb9hsu3hqhte"

with open(TOKEN_FILE) as f:
    token = f.read().strip()

data = {"ingested": True, "date_processed": str(date.today())}
req = urllib.request.Request(
    f"{PB_BASE}/collections/wiki_ingestion/records/{RECORD_ID}",
    data=json.dumps(data).encode(),
    method="PATCH"
)
req.add_header("Authorization", token)
req.add_header("Content-Type", "application/json")

with urllib.request.urlopen(req, timeout=15) as resp:
    result = resp.read().decode()[:300]
    print(f"PocketBase update: {result}")
