#!/usr/bin/env python3
"""Wiki ingestion worker - fetches pending articles from PocketBase and processes them."""

import urllib.request
import json
import sys

TOKEN_FILE = "/home/YOUR-USER/.hermes/profiles/math/home/YOUR-USER.txt"
PB_BASE = "http://YOUR-HOST:8090"

def get_token():
    with open(TOKEN_FILE) as f:
        return f.read().strip()

def re_auth():
    req = urllib.request.Request(
        f"{PB_BASE}/api/collections/_superusers/auth-with-password",
        data=json.dumps({"identity": "YOUR-EMAIL", "password": "BMW518@ibm"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        token = json.loads(resp.read().decode())["token"]
    with open(TOKEN_FILE, "w") as f:
        f.write(token)
    return token

def fetch_pending(token):
    req = urllib.request.Request(
        f"{PB_BASE}/api/collections/wiki_ingestion/records?filter=(ingested=False)&sort=date_added&perPage=500"
    )
    req.add_header("Authorization", token)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return data.get("items", [])

if __name__ == "__main__":
    token = get_token()
    try:
        items = fetch_pending(token)
    except Exception as e:
        print(f"Fetch failed, re-authenticating... {e}")
        token = re_auth()
        items = fetch_pending(token)

    if not items:
        print("NO_PENDING")
        sys.exit(0)

    # Output the first item as JSON for downstream processing
    print(json.dumps(items[0], indent=2))
