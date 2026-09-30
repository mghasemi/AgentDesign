# Verified-Sources Registry (per-project dedup cache)

**Purpose.** Eliminate repeated citation verification and repeated downloads.
Before running the Stage 2 Citation Verification Gate on *any* source, or
before downloading *any* article, check the project's registry first. If the
source is already there with a verified row, reuse it — do not re-verify and
do not re-download. After a genuine first-time verification, append a row.

**Location.** `literature/verified_sources.md` inside the project folder. One
registry per project (no shared/cross-project file) — mirrors the project's
own `.bib`/Zotero scope. Created on first use if absent.

## Schema

One Markdown table, columns in this exact order:

```
| Key | Citation (verified) | ID | Check date | Method | Local copy | Notes |
```

| Column | Content |
|--------|---------|
| `Key` | citation key used in project files, e.g. `[GMW 2014]` |
| `Citation (verified)` | full authors, title, journal **vol**(issue):pages, year — the primary-source-verified string |
| `ID` | arXiv ID *or* DOI (the identifier actually verified) — never both unless both were checked |
| `Check date` | `YYYY-MM-DD` of the last primary-source check |
| `Method` | `arXiv API` \| `Crossref` \| `S2` \| `Numdam` \| `MSP` — which primary source confirmed it |
| `Local copy` | path to the stored file under the project's `Sources/` (or `—` if none). A non-`—` value means: do NOT re-download |
| `Notes` | corrections applied (e.g. "draft venue was wrong"), retractions, unresolved items |

Registry rows are **append-mostly**. A row is added only after passing the
Citation Verification Gate against primary metadata — never transcribed from
model memory.

## Procedure

### 1. Check-before-verify (every time, every session)

Before querying arXiv/Crossref/S2 for a source:

```
search_files pattern="<author> <year>|<title-word>|arXiv ID|DOI" \
  path="<project>/literature/verified_sources.md"
```

- **Hit with `Method` set and `Check date` recent** → copy the verified
  citation string verbatim. Do NOT re-query primary sources. Done.
- **Hit but row incomplete / `Method` empty** → re-verify once and complete
  the row.
- **Miss** → proceed through the gate, then append a full row.

### 2. Check-before-download

A `Local copy` column value other than `—` means the file is already stored.
Before `web_extract`/`curl`/Zotero-PDF-fetch of an article:

```
read_file the path in the `Local copy` cell (confirm it still exists)
```

If present, read/use the local file and skip the network fetch. `web_extract`
cache under `~/.hermes/profiles/math/cache/web/` is a *text* cache and does not
count as the source copy.

### 3. Store + append on first-time verification

1. Save the downloaded file into the project's **existing `Sources/`** folder
   (same folder that holds AI-compiled sources), name `ShortKey-<ext>` or
   `AuthorYear.<ext>`. If the project has no `Sources/`, create one.
2. Run the Citation Verification Gate (arXiv API / Crossref / S2 / Numdam).
3. Append the registry row with the verified citation, `ID`, `Check date`,
   `Method`, and the `Local copy` path.
4. `[Chore: verify-source] <Key>` commit in the project repo.

### 4. Correction / retraction

If a later primary check contradicts a stored row, fix the row in place,
strike through the old value, and note the change under `Notes`. Propagate the
correction to every derived file (literature notes, reports, AGENTS.md) in the
same commit. Do NOT silently leave two conflicting entries.

## Seeding from pre-existing verified content

When adopting the registry in an existing project, seed it from reference
tables already marked verified in the project's `AGENTS.md` / `claims.md` /
literature notes (their `Check date`/`Method` were recorded when verified).
Rows not yet primary-verified are left OUT until they pass the gate.

## What NOT to put here

- Model-memory citation strings (unverified) — the very thing this file
  prevents.
- Reading notes / synthesis — those belong in `literature/*.md` notes.
- Text-cache pointers to `~/.hermes/profiles/math/cache/web/`.
