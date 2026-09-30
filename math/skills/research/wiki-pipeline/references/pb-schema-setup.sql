-- PocketBase v0.39+ schema setup for wiki_ingestion collection
-- PB v0.39 doesn't support adding fields via API (no /api/collections/{id}/fields endpoint).
-- The API also silently drops user-defined fields from the collection POST body.
-- Workaround: create the collection shell via API, then add fields + table via SQLite.
--
-- Usage:
--   scp this.sql YOUR-USER@YOUR-HOST:/tmp/
--   ssh YOUR-USER@YOUR-HOST "docker exec -i pocketbase-inbox sqlite3 /pb_data/data.db < /tmp/this.sql"
--   ssh YOUR-USER@YOUR-HOST "docker restart pocketbase-inbox"

-- Remove any leftover empty collection shell
DELETE FROM _collections WHERE name = 'wiki_ingestion';

-- Create collection record with proper fields JSON.
-- The fields array MUST match the CREATE TABLE columns below.
INSERT INTO _collections (
  id, system, type, name, fields, indexes,
  listRule, viewRule, createRule, updateRule, deleteRule, options
) VALUES (
  'pbc_wiki_ingest', 1, 'base', 'wiki_ingestion',
  '[
    {"id":"fld_src_url","name":"source_url","type":"text","required":true,"system":false,"max":1024},
    {"id":"fld_src_type","name":"source_type","type":"select","required":true,"system":false,
     "options":{"values":["pdf","arxiv","webpage","other"],"maxSelect":1}},
    {"id":"fld_title","name":"title","type":"text","required":false,"system":false,"max":512},
    {"id":"fld_ingested","name":"ingested","type":"bool","required":false,"system":false},
    {"id":"fld_date_add","name":"date_added","type":"date","required":true,"system":false},
    {"id":"fld_date_proc","name":"date_processed","type":"date","required":false,"system":false},
    {"id":"fld_wiki_page","name":"wiki_page","type":"text","required":false,"system":false,"max":256},
    {"id":"fld_notes","name":"notes","type":"text","required":false,"system":false,"max":2048}
  ]',
  '[]',
  '', '', '', '', '',
  '{}'
);

-- Create the actual SQLite table with columns matching the fields JSON.
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
