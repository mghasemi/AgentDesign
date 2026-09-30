# PocketBase v0.39 Quirks — Session-Tested Recipes

Repository of errors, workarounds, and verified patterns for PB v0.39.4 at YOUR-HOST:8090.

## Pre-Flight Checklist (Before Inserting Records)

Always verify these in order — `scripts/pb_ingest.py` does this automatically:

| # | Check | Command/Python | Expected |
|---|-------|---------------|----------|
| 1 | Connectivity | `GET /api/health` | 200 |
| 2 | Auth | `GET /api/collections` | 200 with items array |
| 3 | Collection exists | `GET /api/collections/wiki_ingestion` | 200 with schema |
| 4 | `system=0` | Check response body | `"system": false` |
| 5 | `autogeneratePattern` | Check `id` field in schema | `"[a-z0-9]{15}"` (not empty) |

## Auth

**Correct endpoint** (used at our v0.39.4 instance):
```
POST /api/collections/_superusers/auth-with-password
Body: {"identity": "YOUR-EMAIL", "password": "..."}
```

**Dead endpoints** (return 404):
- `/api/admins/auth-with-password` — removed in v0.25+
- `/api/collections/superusers/auth-with-password` — missing underscore prefix

**Token file:** `/home/YOUR-USER/.hermes/profiles/math/home/YOUR-USER.txt`

## Collection Creation With Fields

### What DOES NOT work
- `POST /api/collections/{id}/fields` — 404 "The requested resource wasn't found."
- `POST /api/collections` with fields in body — silently drops fields, creates empty collection

### What DOES work
- `PATCH /api/collections/{id}` with full `fields:` array (verified 2026-07-30)

### Verified PATCH payload

```python
import urllib.request, json

with open("/home/YOUR-USER/.hermes/profiles/math/home/YOUR-USER.txt") as f:
    token = f.read().strip()

data = {"fields": [
    {"name": "source_url",     "type": "text",   "required": True,  "max": 1024, "min": None},
    {"name": "source_type",    "type": "select",  "required": True,  "values": ["pdf","arxiv","webpage","other"], "maxSelect": 1},
    {"name": "title",          "type": "text",    "required": False, "max": 512,  "min": None},
    {"name": "ingested",       "type": "bool",    "required": False},
    {"name": "date_added",     "type": "date",    "required": True,  "min": "", "max": ""},
    {"name": "date_processed", "type": "date",    "required": False, "min": "", "max": ""},
    {"name": "wiki_page",      "type": "text",    "required": False, "max": 256,  "min": None},
    {"name": "notes",          "type": "text",    "required": False, "max": 2048, "min": None},
]}

req = urllib.request.Request(f"http://YOUR-HOST:8090/api/collections/{coll_id}",
    data=json.dumps(data).encode(), method="PATCH",
    headers={"Authorization": token, "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    print(json.loads(resp.read().decode())["id"])
```

## Direct SQLite Fallback (When API Blocks)

Access the PB SQLite database via Docker on the host:

```bash
ssh -i /home/YOUR-USER/.hermes/profiles/math/home/.ssh/id_ed25519 YOUR-USER@YOUR-HOST \
  "docker exec -i pocketbase-inbox sqlite3 /pb_data/data.db \"SQL_STATEMENT\""
docker restart pocketbase-inbox
```

### Full SQL to create wiki_ingestion from scratch

```sql
DROP TABLE IF EXISTS wiki_ingestion;
DELETE FROM _collections WHERE name = 'wiki_ingestion';

INSERT INTO _collections (id, system, type, name, fields, indexes,
    listRule, viewRule, createRule, updateRule, deleteRule, options)
VALUES (
  'pbc_3156047781', 0, 'base', 'wiki_ingestion',
  '[
    {"id":"fld_src_url","name":"source_url","type":"text","required":true,"system":false,"max":1024},
    {"id":"fld_src_type","name":"source_type","type":"select","required":true,"system":false,
      "values":["pdf","arxiv","webpage","other"],"maxSelect":1},
    {"id":"fld_title","name":"title","type":"text","required":false,"system":false,"max":512},
    {"id":"fld_ingested","name":"ingested","type":"bool","required":false,"system":false},
    {"id":"fld_date_add","name":"date_added","type":"date","required":true,"system":false},
    {"id":"fld_date_proc","name":"date_processed","type":"date","required":false,"system":false},
    {"id":"fld_wiki_page","name":"wiki_page","type":"text","required":false,"system":false,"max":256},
    {"id":"fld_notes","name":"notes","type":"text","required":false,"system":false,"max":2048}
  ]',
  '[]', '', '', '', '', '', '{}'
);

CREATE TABLE wiki_ingestion (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(7)))),
  source_url TEXT NOT NULL,
  source_type TEXT NOT NULL,
  title TEXT,
  ingested INTEGER DEFAULT 0,
  date_added TEXT NOT NULL,
  date_processed TEXT,
  wiki_page TEXT,
  notes TEXT,
  created TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%fZ','now')),
  updated TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%fZ','now'))
);
```

### Verify After SQLite Setup

```bash
ssh ... "docker exec -i pocketbase-inbox sqlite3 /pb_data/data.db \
  \"SELECT name, system FROM _collections WHERE name='wiki_ingestion';\""
# Should return: wiki_ingestion|0
docker restart pocketbase-inbox
```

PB returns the `id` field as a system-managed field. The API response for items will include `collectionId`, `collectionName`, and user fields but NOT `id` as a regular key (it's embedded in PB's internal query layer).

### Fixing empty `autogeneratePattern` on `id` (400 "Cannot be blank" on create)

SQLite-created collections may have `"autogeneratePattern": ""` on the `id` field, causing `POST /api/collections/{name}/records` to return 400 with `"id":{"code":"validation_required","message":"Cannot be blank."}`. PB's Go binary container has no Python — use the copy-out/fix/copy-back approach:

```bash
ssh YOUR-USER@YOUR-HOST '
  docker cp pocketbase-inbox:/pb_data/data.db /tmp/pb_data_backup.db
  python3 -c "
import json, sqlite3
db = sqlite3.connect(\"/tmp/pb_data_backup.db\")
row = db.execute(\"SELECT fields FROM _collections WHERE name=?\", (\"wiki_ingestion\",)).fetchone()
fields = json.loads(row[0])
for f in fields:
    if f[\"name\"] == \"id\":
        f[\"autogeneratePattern\"] = \"[a-z0-9]{15}\"
        break
db.execute(\"UPDATE _collections SET fields=? WHERE name=?\", (json.dumps(fields), \"wiki_ingestion\"))
db.commit()
db.close()
"
  docker cp /tmp/pb_data_backup.db pocketbase-inbox:/pb_data/data.db
  docker restart pocketbase-inbox
'
```

Verify with: `python3 -c "import urllib.request... POST .../wiki_ingestion/records"` — the `id` should now be auto-generated (15-char lowercase alphanumeric).

## Error Reference

| Error | Context | Fix |
|-------|---------|-----|
| 404 "Missing or invalid collection context" | Auth to `/api/collections/superusers/...` (no underscore) | Add underscore prefix: `_superusers` |
| 404 "The requested resource wasn't found." | Auth to `/api/admins/...` | Use `/api/collections/_superusers/auth-with-password` instead |
| 400 `{"data":{},"message":"Failed to create record."}` | API write to collection with `system=1` | Set `system=0` in SQLite, restart |
| 400 `"source_type": {"code":"validation_invalid_value"}` | Select field values don't match options | Check field `values` array — must match exactly |
| 400 "Cannot be blank." on identity | Auth with `email` field instead of `identity` | Use `"identity"` not `"email"` |
| 400 `"id":{"code":"validation_required"}` | Empty `autogeneratePattern` on `id` field (SQLite artifact) | Set `autogeneratePattern` to `"[a-z0-9]{15}"` via SQLite JSON patch (see recipe above) |
| 400 `"id":{"code":"validation_invalid_format"}` | `id` value doesn't match `pattern:"^[a-z0-9]+$"` (e.g., UUID with hyphens) | Either omit `id` to trigger autogenerate, or provide a 15-char lowercase alphanumeric string |
| 204 (empty response) | DELETE on record/collection | Normal — no body returned |
| empty `data:{}` on record creation | Collection has `system=1` or field format wrong | Check `_collections.system` or use PATCH approach |
