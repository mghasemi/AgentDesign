---
name: calibre-library-ingestion
description: Use when adding or fixing books in the Calibre library.
---

# Calibre library ingestion & metadata maintenance

Covers add books, correct metadata, attach formats, and restart `calibre-server`.

## Environment

| Thing | Value |
|---|---|
| Library (sshfs mount) | `/home/YOUR-USER/Documents/calibre` → `YOUR-USER@YOUR-HOST:/home/YOUR-USER/Documents/Calibre` |
| Content Server | `http://YOUR-HOST:9876/calibre` (runs on remote host `YOUR-USER-m5plus`) |
| Restart command | remote: `setsid nohup calibre-server --url-prefix /calibre --port 9876 > ~/.calibre-server.log 2>&1 < /dev/null &` |
| calibre package for db_api | `/home/YOUR-USER/.local/lib/python-calibre` (deb payload, 7.6) |
| Interpreter | `/home/YOUR-USER/Code/Python/tools/calibre-mcp/.venv/bin/python` (has `apsw`) |
| MCP env | `CALIBRE_LIBRARY_PATH=/home/YOUR-USER/Documents/calibre`, `CALIBRE_BASE_URL=http://YOUR-HOST:9876/calibre` |

- **Architecture: the MCP calibre tools & db_api point at a LOCAL half-empty library, NOT the real one.** `CALIBRE_LIBRARY_PATH=/home/YOUR-USER/Documents/calibre` (lowercase, a stale empty shell on the AMD machine, ~0 books) is what the MCP `add_book`/`search_books` and any `db("/home/YOUR-USER/Documents/calibre")` write to. The **real library** is `/home/YOUR-USER/Documents/Calibre` (capital C) on remote `YOUR-USER-m5plus` (YOUR-HOST), 2,147+ books, served on :9876. Writing via db_api/MCP silently creates a fresh empty local DB instead of hitting the remote one. For reliable ingestion, **write over SSH with remote `calibredb`** directly against `/home/YOUR-USER/Documents/Calibre`.
- **Remote `calibredb add` available** (9.14). Schema is legacy: books_authors_link cols = `id,book,author`; identifiers = `id,book,type,val`; languages_link = `id,book,lang_code,item_order`; series via books_series_link. Query with read-only `sqlite3.connect("file:.../metadata.db?mode=ro", uri=True)` after stopping the server.
- **Do NOT pass an `.opf` file to `calibredb add` expecting it to seed metadata.** It creates a junk book (title/author from the PDF *filename*, e.g. `book.pdf` → title `book`), and each subsequent identical basename is then rejected as a duplicate of that junk record. Instead: (1) `calibredb add --duplicates -t TITLE -a 'Last, First; …' -d YYYY-MM-DD --tags TAG -I type:value /path/file.pdf` to create the record, then (2) `calibredb set_metadata ID /path/metadata.opf` to overlay full metadata. Capture the new id from the `Added book ids: N` line.
- **`calibredb set_metadata` needs a full OPF *package*** exactly as `calibredb show_metadata ID --as-opf` emits (`<package …><metadata …>…`), NOT a bare `<metadata>` root. A root-only `<metadata>` silently results in title/author = `Unknown` with no error. In the package form use `<dc:identifier opf:scheme="arxiv">`, `<meta name="calibre:series">`, `<dc:language>eng</dc:language>; for Sum2d-style project tagging use `<dc:subject>Sum2d</dc:subject>`, plus `<meta name="calibre:series" content="Thesis"/>` + `<meta name="calibre:series_index" content="1"/>` for a series.
- **Verify from the remote DB, never trust `calibredb`'s `set_metadata` note output** (it echoes pre- or partial-state confusingly); re-query `books`/`authors`/`data`/`identifiers`/`books_languages_link` per new id and confirm each format file exists under `<lib>/<path>/<name>.pdf`.

## Rule 0 — duplicate check before any write

Search the library for title/author/DOI/ISBN first. Same-topic works are *not* duplicates (e.g. Aull's *Rings of Continuous Functions* vs Gillman–Jerison #943). A real duplicate means an existing row for the **same work** — attach a format to that row instead of creating a new book.

**Title search is not enough — confirm by content hash.** A staged file whose bytes already sit in the library must never produce a new row (the staging file legitimately stays behind after `add_books`, so "still in ToLib" ≠ "not ingested"). Hash every staged file and every library format file, then join:

```bash
cd /path/to/staging && md5sum *.pdf | awk '{h=$1; $1=""; sub(/^  /,""); n=$0; sub(/.*\//,"",n); print h"  "n}' > /tmp/stage_md5.txt
cd "$CALIBRE_LIBRARY_PATH" && sqlite3 metadata.db "select id||'|'||path from books;" | while IFS='|' read -r id path; do
  for f in "$path"/*.pdf; do [ -e "$f" ] || continue; md5sum "$f" | awk -v id="$id" '{print $1"|"id"|"$2}'; done
done > /tmp/lib_md5.txt
awk -F'|' 'NR==FNR{split($0,a,"  ");h[a[1]]=a[2];next}{if($1 in h) print h[$1], $2}' /tmp/stage_md5.txt /tmp/lib_md5.txt
```

Anna's Archive filenames embed the source md5 — a quick signal, but hash the file itself. Expect the common outcome: most of a batch is already present; only the residue gets added.

## Procedure

1. **Stop the server first.** A running `calibre-server` holds an in-memory cache; writes made under it can be silently overwritten. Verify: `ssh YOUR-USER@YOUR-HOST 'pgrep -a -f calibre-server; ss -ltn | grep 9876'`.
2. **Back up** `metadata.db`: `cp /home/YOUR-USER/Documents/calibre/metadata.db /home/YOUR-USER/backups/calibre/metadata.db.$(date +%Y%m%d_%H%M%S)`.
3. **Write via db_api**, not raw SQL. Bootstrap (calibre's launcher normally sets these `sys` attrs):
   ```python
   import sys, os
   lib = "/home/YOUR-USER/.local/lib/python-calibre"
   sys.path.insert(0, lib)
   sys.extensions_location = os.path.join(lib, "calibre", "plugins")
   sys.resources_location = "/home/YOUR-USER/.local/lib/python-calibre-resources"
   from calibre.library import db
   from calibre.ebooks.metadata.book.base import Metadata
   api = db("/home/YOUR-USER/Documents/calibre").new_api
   ```
   - Update one field: `api.set_field(name, {book_id: value})`
   - Add books: `api.add_books([(mi, {"PDF": path})])` → returns `(ids, duplicates)`
   - Attach a format: `api.add_format(book_id, "PDF", path)` → `True` on success
   - `api.author_sort_from_authors(authors)` for `mi.author_sort` (no module-level helper exists)
   - Use timezone-aware `datetime(..., tzinfo=timezone.utc)` for `pubdate`.
4. **Verify from the DB, not the API return value**: query `metadata.db` read-only for title/pubdate/series_index/identifiers/languages/publisher/tags and confirm each format file exists under `<library>/<path>/<name>.<fmt>`.
5. **Restart the server** on the remote host and confirm `curl -s -o /dev/null -w "%{http_code}" http://YOUR-HOST:9876/calibre/` → 200. The `mobile` and `/opds/newest` feeds are unreliable for this check; verify against the server's own search index instead: `curl -s "http://YOUR-HOST:9876/calibre/opds/search/<url+encoded+title>" | grep -c '<entry>'` → ≥ 1 per new book. The navigation feed `/calibre/opds/navcatalog/4f6e6577657374` (hex for `Newest`) also lists books but is not timestamp-ordered.

## Pitfalls

- **Field name is `languages`, not `language`.** `set_field('language', …)` raises `KeyError: 'language'`. Other settable names: `title`, `authors`, `series`, `series_index`, `pubdate`, `identifiers`, `publisher`, `tags`, `comments`, `rating`.
- `set_field` for `identifiers` takes a **dict** `{type: value}`; types in use: `isbn`, `amazon`, `google`, `doi`, `url`, `arxiv`, `mobi-asin`.
- Iterate `set_field` calls so one bad field name does not lose the earlier ones; a partially applied run is harmless to re-run (idempotent).
- The Content Server HTTP API is **read-only** for book data — no documented write endpoint. Writes go through `db_api` (or a running GUI).
- `add_books` copies the file into the library; the staging file (e.g. `~/Documents/ToLib/`) stays put.
- sshfs + sqlite is fine for a single writer, but concurrent GUI/server access is not — always stop the server.
- The server renders dates in the *client's* timezone, so a `1985-01-01 UTC` pubdate can display as `31 Dec 1984`. Cosmetic.
- **Quote non-ASCII paths with `shlex.quote`, never `json.dumps`.** `json.dumps` emits `\u0160`, which the shell does not expand → `pdftotext`/`pdfinfo` report "No such file or directory" for every path containing `–` or `Š`. Inside `execute_code`, wrap the path in `shell_quote(path)` / `shlex.quote(path)`.
- The `series` and `publisher` fields do **not** live on `books`; read them through `books_series_link`/`series` and `books_publishers_link`/`publishers`. `comments` is its own table keyed by `book`. The tags table column is `name`, not `tag`.
- Library legacy schema: link tables use singular columns (`book`, `author`, `tag`, `series`, `publisher`); `series_index` lives on `books`, identifiers in the separate `identifiers` table.

## Metadata conventions in this library

- Series: `Math` for books/monographs, `Paper` for articles (almost all at `series_index = 1.0`), plus `Thesis`, `Presentation`.
- Language: `eng` (row id 1 in `books_languages_link`).
- Tags are free-form mixed-case words/phrases reused across books.
- Record the **original edition's** identifiers when the scan is a later reissue (e.g. #804 stores the 1992 Dekker ISBN, not the 2019 CRC reprint ISBN).
