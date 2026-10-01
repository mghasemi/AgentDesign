# Service Endpoints & Credential Status

Last updated: 2026-05-19

## Topology

All services run on `YOUR-HOST` with DDNS fallback `YOUR-DDNS-HOST`.

```
                     ┌─────────────────────────────────────┐
                     │       YOUR-HOST (LAN)            │
                     │   YOUR-DDNS-HOST (WAN fallback)  │
                     └─────────────────────────────────────┘
                                      │
        ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
        │         │         │         │         │         │         │         │
     :9621     :8899     :5050     :3456     :6806     :8080     :????
    LightRAG   ZIMI    SearXNG   Vikunja   SiYuan   Calibre   Zotero
    (graph    (offline  (meta-    (task     (notes)  (ebooks)  (bib,
     RAG)      wiki)    search)   mgmt)                        web API)
```

## Service Status

| Service      | Port  | URL                                   | Auth      | Status |
|-------------|-------|---------------------------------------|-----------|--------|
| LightRAG    | 9621  | `http://YOUR-HOST:9621`           | optional  | ✅     |
| ZIMI        | 8899  | `http://YOUR-HOST:8899`           | none      | ✅     |
| SearXNG     | 5050  | `http://YOUR-HOST:5050/`          | none      | ✅     |
| Vikunja     | 3456  | `http://YOUR-HOST:3456`           | token     | ✅     |
| SiYuan      | 6806  | `http://YOUR-HOST:6806`           | token     | ✅     |
| Calibre     | 8080  | `http://YOUR-HOST:8080`           | none      | ⚠️     |
| Zotero      | web   | `api.zotero.org`                     | API key   | ✅     |

## Environment Variables Configured

All variables live in `~/.hermes/profiles/math/.env` (46 vars).
Credentials prefixed `(set)` have values; `(empty)` are placeholders.

```
VIKUNJA_URL       = http://YOUR-HOST:3456
VIKUNJA_ALT_URL   = http://YOUR-DDNS-HOST:3456
VIKUNJA_TOKEN     = (set)


LIGHTRAG_URL      = http://YOUR-HOST:9621
LIGHTRAG_ALT_URL  = http://YOUR-DDNS-HOST:9621
LIGHTRAG_API_KEY  = (empty)
LIGHTRAG_TIMEOUT  = 20
LIGHTRAG_INGEST_TIMEOUT = 60

ZIMI_URL          = http://YOUR-HOST:8899
ZIMI_ALT_URL      = http://YOUR-DDNS-HOST:8899

SEARXNG_URL       = http://YOUR-HOST:5050/
SEARXNG_ALT_URL   = http://YOUR-DDNS-HOST:5050

SIYUAN_URL        = http://YOUR-HOST:6806
SIYUAN_ALT_URL    = http://YOUR-DDNS-HOST:6806
SIYUAN_TOKEN      = (set)

ZOTERO_API_KEY    = (set)
ZOTERO_LIBRARY_ID = ZOTERO_LIBRARY_ID
ZOTERO_LIBRARY_TYPE = user

WOLFRAM_ALPHA_APPID = REPLACE_ME

CALIBRE_URL       = http://YOUR-HOST:8080
```

## Connection Fallback Strategy

Most tools implement a 3-tier fallback:
1. Primary URL (LAN IP)
2. Alt URL (DDNS)
3. Graceful failure (tool reports `success: false` instead of crashing)

The `zimi_tool.py` and `lightrag_query_tool.py` Python wrappers
fall back from primary to alt URL automatically.
