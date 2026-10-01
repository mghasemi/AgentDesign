---
name: wiki-maintenance
description: "Use when linting or maintaining a Karpathy-style LLM wiki."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wiki, lint, maintenance, frontmatter, vitepress, cross-reference]
    category: research
    related_skills: [llm-wiki]
---

# Wiki Maintenance & Linting

Validate, repair, and health-check a Karpathy-style LLM wiki (interlinked markdown KB with YAML frontmatter).

## When This Skill Activates

Use when the user asks to:
- Lint, audit, or health-check their wiki
- Fix frontmatter, broken links, or tag taxonomy issues
- Verify wiki consistency after ingestion or bulk edits
- Run a pre-commit or pre-publish check on the wiki

## Two-Phase Validation

A complete wiki lint requires **both** phases — they catch different error classes:

| Phase | Tool | Catches |
|-------|------|---------|
| 1 | Python linter script | Frontmatter validity, tag taxonomy, cross-references, index completeness, filename conventions |
| 2 | VitePress build (`npx vitepress build`) | Dead Markdown links `[text](file.md)`, rendering errors, config issues |

If `package.json` exists at the wiki root, the wiki is a VitePress instance — include phase 2.

## Phase 1: Python Linter

Write or run a Python linter that checks:

1. **Filename conventions** — lowercase, hyphens, no spaces
2. **YAML frontmatter** — exists, parses, contains all required fields (`title`, `created`, `updated`, `type`, `tags`, `sources`)
3. **Type validity** — one of `entity`, `concept`, `comparison`, `query`, `summary`
4. **Date validity** — handles both string `"YYYY-MM-DD"` and YAML-parsed `datetime.date` objects
5. **Tag taxonomy** — every tag appears in SCHEMA.md's taxonomy
6. **Source existence** — `sources:` entries resolve to files on disk
7. **Cross-references** — minimum 2 outbound links per page (count `[[wikilinks]]` in body + `related`/`contradictions` in frontmatter)
8. **Wikilink targets** — every `[[link]]` resolves to an existing page
9. **Index completeness** — every page listed in `index.md`, no phantom links
10. **Raw file frontmatter** — `source_url`, `ingested`, `sha256` present and valid

### Critical YAML Parsing Pitfalls

**Closing `---` is a document separator.** Including it in the parsed block causes `yaml.composer.ComposerError`. Strip it:

```python
stripped = text.lstrip()
end = stripped.index("---", 3)
fm_block = stripped[3:end].rstrip()  # Exclude closing ---
fm = yaml.safe_load(fm_block)
```

**YAML auto-parses dates to `datetime.date`.** A bare date `2026-07-29` becomes a `date` object, not a string. Validate:

```python
from datetime import datetime, date
if isinstance(val, str):
    datetime.strptime(val, "%Y-%m-%d")
elif not isinstance(val, (datetime, date)):
    # error: unexpected type
```

**Leading blank lines.** Always `lstrip()` before checking `startswith("---")`.

## Phase 2: VitePress Build

```bash
cd $WIKI && npx vitepress build 2>&1
```

- Dead links appear as `Found dead link ./wrong-path in file ...`
- The chunk-size warning (`Some chunks are larger than 500 kB`) is cosmetic — ignore it
- A clean build has zero `dead link` messages

## Repair Workflow

When lint finds issues:

1. **Read the broken files** in parallel (batch `read_file` calls)
2. **Classify errors** — frontmatter missing vs wrong vs filename convention vs broken link
3. **Apply fixes** via `patch` (frontmatter edits) or `terminal mv` (renames)
4. **Update SCHEMA.md tag taxonomy** if new tags are needed (add to schema FIRST, then use)
5. **Update index.md** to include newly created pages and remove references to deleted ones
6. **Re-run both phases** to confirm zero errors
7. **Append to log.md** with files changed

## Automated Ingestion via PocketBase Queue

For recurring ingestion (PDFs, arXiv links, webpages), use a PocketBase queue with a cron worker:

### Architecture

```
User adds article ──→ PocketBase wiki_ingestion collection ──→ Cron job (4am/4pm)
                                                                     ↓
                                                          Worker: extract → wiki pages → update index
                                                                     ↓
                                                          Mark ingested in PB
```

### PocketBase Setup (v0.39+)

**Auth:** PB v0.39+ uses `_superusers` (underscore prefix), NOT `/api/admins/`:
```bash
# Auth
curl -X POST "$PB_URL/api/collections/_superusers/auth-with-password" \
  -H "Content-Type: application/json" \
  -d '{"identity": "YOUR-EMAIL", "password": "..."}'
```

**Collection schema** for the queue (`wiki_ingestion`):
- `source_url` (text, required) — URL or local file path
- `source_type` (select) — values: `pdf`, `arxiv`, `webpage`, `other`
- `title` (text, optional)
- `ingested` (bool) — `false` = pending
- `date_added` (date, required) — when enqueued
- `date_processed` (date) — when ingested
- `wiki_page` (text) — slug of created raw page
- `notes` (text) — processing notes

**Field format for v0.39:** Values are flat at the field level, not nested:
```json
{
  "name": "source_type",
  "type": "select",
  "required": true,
  "values": ["pdf", "arxiv", "webpage", "other"],
  "maxSelect": 1
}
```

**Add fields to an existing collection** (PATCH, not `/api/collections/{id}/fields` which doesn't exist):
```python
api("PATCH", f"/api/collections/{coll_id}", {
    "fields": [
        {"name": "source_url", "type": "text", "required": True, "max": 1024},
        ...
    ]
})
```

### Cron Job Schedule

Two regular cron jobs:

1. **Ingestion worker** — every 12 hours (4am/4pm):
   ```bash
   cronjob action=create name="Wiki Ingestion Worker" schedule="0 4,16 * * *" \
     prompt="Pick one unprocessed article from PocketBase, extract content, create wiki pages, mark done" \
     workdir=/home/YOUR-USER/Code/wiki
   ```

2. **Lint/maintenance** — weekly/b-weekly (Sundays 3am):
   ```bash
   cronjob action=create name="Wiki Maintenance" schedule="0 3 * * 0" \
     prompt="Run linter, check duplicates, contradictions, stale pages" \
     workdir=/home/YOUR-USER/Code/wiki
   ```

### Ingestion Worker Steps

When the cron job fires:

1. **Auth in PB** — re-auth if token expired (`api/collections/_superusers/auth-with-password` with `identity`)
2. **Query oldest pending** — `filter=(ingested=False)&sort=date_added&perPage=1`
3. **Extract content** — PDF via pymupdf/pdftotext, arXiv via ar5iv, webpage via web_extract
4. **Create wiki pages** — `raw/` article + `entity/` page per SCHEMA.md conventions
5. **Update index.md** and **log.md**
6. **Mark ingested** — PATCH `ingested=True, date_processed=<today>` on the PB record
7. **Verify** — run the wiki linter (`python3 /home/YOUR-USER/.hermes/profiles/math/scripts/wiki_lint.py`)

### Linter Script

The standalone linter script lives at `~/.hermes/profiles/math/scripts/wiki_lint.py` and checks:
- Filename conventions (lowercase, hyphenated)
- Frontmatter validity (required fields, valid types)
- Tag taxonomy (tags must exist in SCHEMA.md)
- Cross-reference count (min 2 outbound links)
- Broken wikilinks and dead markdown links
- Index completeness (every content page in index.md)
- Page size (flag >200 lines)
- Contradictions/contested pages
- Stale content (>90 days outdated)

Run it after every ingestion to verify nothing broke:
```bash
python3 /home/YOUR-USER/.hermes/profiles/math/scripts/wiki_lint.py
```
The same script is available as `scripts/wiki_lint.py` inside this skill directory for reference.

### Pitfalls

- **system flag:** Collections created via direct SQL must have `system=0` for API writes
- **Date format:** PB v0.39 expects `"YYYY-MM-DD HH:MM:SS.000Z"`, not bare `"YYYY-MM-DD"`
- **Select field values** are flat — no `options` nesting in v0.39
- **Direct SQL fallback:** When the API blocks writes, modify `_collections` table via Docker: `docker exec -i pocketbase-inbox sqlite3 /pb_data/data.db "SQL" && docker restart pocketbase-inbox`
- **Token expiry:** PB tokens expire after `duration` configured in the collection (default 24h for superusers). Always re-auth at the start of each cron tick.
- **Bare date format:** `date.today()` returns `YYYY-MM-DD` which PB v0.39 may reject. Use `datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")` instead.

## Ingestion Workflow (PDF → Wiki) — Manual

When ingesting a PDF paper (arXiv, journal, etc.) into the wiki, follow this sequence:

### Phase 1: Extract & Compute

When ingesting a PDF paper (arXiv, journal, etc.) into the wiki, follow this sequence:

### Phase 1: Extract & Compute

```bash
# Extract with pdftotext (fast, preserves layout)
pdftotext -layout paper.pdf -

# Also extract with pymupdf for complex PDFs where pdftotext fails
python3 -c "
import pymupdf
doc = pymupdf.open('paper.pdf')
for page in doc: print(page.get_text())
"
```

Record the extraction as a temp file for reference during the subsequent steps.

### Phase 2: Create Raw Article

Write to `raw/articles/<slug>.md` with frontmatter:

```yaml
---
source_url: https://arxiv.org/abs/XXXX.XXXXX
ingested: YYYY-MM-DD
sha256: <hex digest of the body content below the frontmatter>
---
```

**Critical: SHA256 is of the body text (below the closing `---`), NOT of the frontmatter or the PDF binary.** Compute:

> **Math wiki actual convention (verified 2026-09):** the `/home/YOUR-USER/Code/wiki` raw
> files record `sha256` of the **source page HTML** — for arXiv, the live
> `https://arxiv.org/abs/<id>` page at ingest time (`curl -sL https://arxiv.org/abs/<id> | sha256sum`).
> Verified against two raw files: the `/abs/` HTML hash matched the recorded frontmatter
> value while the PDF, ar5iv/HTML-v1, and e-print hashes did NOT. The llm-wiki body-hash
> scheme applies to other wikis; for the math wiki, hash the source page.

```bash
python3 -c "
with open('file.md') as f:
    content = f.read()
# Find second ---
idx = content.index('---', 3)
body = content[idx+3:].lstrip('\n')
import hashlib
print(hashlib.sha256(body.encode()).hexdigest())
"
```

Strip page numbers, form feeds (`\f`), and excessive whitespace from the raw text for readability. Condense the extracted text into a clean summary of each section (introduction, main results, theorems, case study, numerical experiments, references, tables). Remove OCR-level layout artifacts (extra spaces, broken equations).

### Phase 3: Create Entity Page

Write to `entities/<slug>.md` with:

- Full YAML frontmatter (`title`, `created`, `updated`, `type: entity`, `tags`, `sources`, `confidence`)
- Authors, arXiv link, code URL if available
- **Summary** — 2–3 sentence overview
- **Structured breakdown** — use tables for sections/approach, bullet lists for theorems/results
- **Class of problem handled** — mathematical setting, assumptions, type of PDE/operator
- **Numerical results** — truncation degrees, accuracy, computation times
- **Relevance section** — connect to the active projects (each with its own name) with specific cross-references to their existing work
- **Open questions** listed from the paper

### Phase 4: Update Index & Log

1. **`index.md`** — Add a row to the Papers table:
   ```markdown
   | Title | Authors | Year | Key Concepts |
   ```
2. **`log.md`** — Append a row with date, source, type, key concepts added.

### Phase 5: Relevance mapping & uncited-prior-work cross-check (when requested)

When the user asks to "ingest this paper AND check whether it sheds light on the
open problems" (a recurring request for the math wiki — ingested papers are
usually YOUR-USER's own or closely tied to his active projects), the deliverable is
more than the raw + entity pages:

1. **File a `queries/` page** mapping each paper result → the specific open
   problem / manuscript section it addresses: a results table plus a "what the
   paper does NOT address" list. This is the durable home for the mapping; a
   one-off chat answer is re-derived from scratch next time.
2. **Add a `## Queries` section to `index.md` if absent** — the default index
   template has no Queries section, so `queries/` pages are invisible until one
   is added.
3. **Cross-check whether the paper is the user's OWN prior work that is UNCITED
   in an active manuscript.** For a researcher ingesting their own papers this is
   the single highest-value finding: an uncited self-reference in a current
   manuscript (e.g. a density/compactification result the manuscript states only
   loosely) is a concrete, actionable citation recommendation. Confirm with
   `grep -i` on the manuscript for the author surname + arXiv id before
   claiming "uncited".
4. **Fold the sharpest theorem into a concept page**, not just the entity: add
   the density criterion / support-shift result to the relevant `concepts/*.md`
   page (with a `^[raw/...]` provenance marker) so it compounds into the concept
   layer rather than sitting isolated on the entity page.

### Pitfalls

- **Patch tool table formatting.** When replacing content near Markdown table rows, the patch context can introduce extra `|` characters. Always verify the table renders correctly after patching. If patch mangling happens, re-read the file and fix with a second targeted patch.
- **SHA256 of the body.** The frontmatter's `sha256` field must hash only the content below the closing `---` of the frontmatter, not the whole file and not the PDF binary.
- **Entity page outbound links.** The SCHEMA.md requires minimum 2 outbound links per page. The entity page to the raw source counts as one. Add links to existing concept/entity pages for the other.
- **No concept-page creation by default.** A single paper usually warrants an entity page only. Only create concept pages when the paper introduces a genuinely new concept not already covered, or when the concept appears in 2+ sources (per SCHEMA.md thresholds).
- **Post-ingestion citation correction touches `raw/` too — recompute `sha256`.** The
  "raw is immutable" rule has one legitimate exception: correcting the bibliographic
  header after the user supplies the published venue/year (arXiv → journal). When you
  edit a raw body post-ingestion, recompute the frontmatter `sha256` over the new body
  and replace the stored value — otherwise the next lint flags a spurious "source drift"
  on a file you edited yourself. The same correction also propagates to the entity
  title/header, any index/query *display* titles (slugs may keep the old year), and any
  active manuscript's `\bibitem` + citation key (see math-article-revision §6b).
- **arXiv HTML-v1 rendering drops the bibliography and the author line.** The LaTeXML
  HTML (`arxiv.org/html/<id>v1`) renders `## References` as a broken `![[LOGO]][IMAGE]`
  placeholder with no `\bibitem`s, and often omits the author line entirely. Recover
  both from primary metadata, not the rendered page:
  - **Author/title/category/date** — the arXiv API:
    `curl -sL "http://export.arxiv.org/api/query?id_list=<id>"` (parse `<name>`, `<title>`, `<published>`, `<category>`). This is the authoritative source for the Citation Verification Gate, not model memory.
  - **Full reference list** — ar5iv: `curl -sL --max-time 60 "https://ar5iv.labs.arxiv.org/html/<id>" -o /tmp/a.html`, then parse the bibitems:
    `re.findall(r'ltx_bibitem[^>]*>(.*?)</li>', html, re.DOTALL)` and strip tags + `html.unescape`. The abs-page sha256 is still computed off the *abs* page (unchanged); ar5iv is only for recovering content the HTML-v1 lost.
- **Same-author-different-paper is the classic citation conflation.** Before claiming an
  ingested paper's bibliography "resolves" an open attribution in a project, confirm it is
  the SAME paper — same venue, volume, year, and title — not a same-author paper on an
  overlapping topic. Two distinct "Glicksberg on Bishop/Stone-Weierstrass" results exist
  (1963 strict-topology *Proc. AMS* vs 1962 antisymmetric-set *Trans. AMS*), and citing one
  as the other silently corrupts a project ledger. `grep` the project's `verified_sources.md`
  / `claims.md` for the author surname first: the attribution may already be resolved to a
  different paper, and the honest outcome is "distinct paper, worth a cross-reference" not
  "resolved".

## Math Wiki Link Linting (specific to `/home/YOUR-USER/Code/wiki/`)

The math wiki uses **standard Markdown relative links** `[Display Title](relative/path.md)` —
the old `[[wikilink]]` syntax (Obsidian/Notion-style) is **not supported** by standard
Markdown renderers and must be converted. Use this when the user asks to lint/validate/fix
links in the math wiki, or when adding new wiki pages that need cross-references verified.

### 1. Detect remaining wikilinks

```python
import os, re
wiki_root = "/home/YOUR-USER/Code/wiki"
wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')
for dirpath, _, filenames in os.walk(wiki_root):
    if 'node_modules' in dirpath or '__pycache__' in dirpath:
        continue
    for fn in filenames:
        if fn.endswith('.md'):
            path = os.path.join(dirpath, fn)
            with open(path) as f:
                content = f.read()
            matches = wikilink_pattern.findall(content)
            if matches:
                print(f"{os.path.relpath(path, wiki_root)}: {matches}")
```

### 2. Convert wikilinks to Markdown links

Build a slug-to-path map from all `.md` files, then for each `[[slug]]`:
- Look up the slug in the map
- Compute `os.path.relpath(target_path, source_dir)` for correct relative paths
- Replace with `[Display Title](relative/path.md)` using a human-readable title

**Title map** (slug → display title):
- `lifting-free-regularization` → Lifting-Free Regularization
- `quadratic-sum-of-squares-programming` → Quadratic Sum-Of-Squares Programming
- `sum-of-squares-programming` → Sum-Of-Squares Programming
- `solver-comparison-qsos` → Solver Comparison QSOS
- `hyperfield` → Hyperfield
- `real-hyperfield` → Real Hyperfield
- `tropical-hyperfield` → Tropical Hyperfield
- `real-spectrum` → Real Spectrum
- `formal-real-semiring` → Formal Real Semiring
- `multiring` → Multiring
- `marshall-quotient` → Marshall Quotient
- `boolean-real-semigroup` → Boolean Real Semigroup
- `real-reduced-hyperfield` → Real Reduced Hyperfield

### 3. Verify all links resolve

```python
import os, re
wiki_root = "/home/YOUR-USER/Code/wiki"
link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+\.md)\)')
for dirpath, _, filenames in os.walk(wiki_root):
    if 'node_modules' in dirpath or '__pycache__' in dirpath:
        continue
    for fn in filenames:
        if fn.endswith('.md'):
            path = os.path.join(dirpath, fn)
            with open(path) as f:
                content = f.read()
            for match in link_pattern.finditer(content):
                target = match.group(2)
                source_dir = os.path.dirname(path)
                resolved = os.path.normpath(os.path.join(source_dir, target))
                if not os.path.exists(resolved):
                    print(f"BROKEN: {os.path.relpath(path, wiki_root)} -> {target}")
```

### 4. Check documentation examples in SCHEMA.md

SCHEMA.md may contain example link syntax that the regex picks up as broken. Use prose
descriptions or backtick-wrapped examples instead of live links in schema/convention files.

### Math-wiki link pitfalls

- **Double `.md.md` extension**: When computing `os.path.relpath(target, source_dir)` where
  `target` already includes `.md`, do NOT append `.md` again. The slug map stores full
  relative paths including `.md`.
- **Cross-directory links**: Links between `concepts/` and `entities/` or `comparisons/`
  need `../` prefixes. `os.path.relpath` handles this correctly.
- **SCHEMA.md convention line**: Must describe the correct link format (Markdown relative
  links), not the old wikilink syntax.
- **Index files in subdirectories** (`comparisons/index.md`, `entities/index.md`,
  `queries/index.md`): These are auto-generated index stubs, not content pages — skip them
  for wikilink conversion.
- **`raw/` directory**: Contains raw paper ingestions; these typically don't have cross-links
  to other wiki pages. Skip unless they explicitly reference other concepts.
- **Mixed legacy syntax**: some older entity pages (e.g. `ghasemi-kuhlmann-marshall-jacobi-lmc-2012.md`)
  still carry `[[concepts/...|Title]]` wikilinks; new pages must use standard Markdown links
  `[Display](../concepts/x.md)`. The link-lint regex only checks `](...)` Markdown links, so
  copying the legacy `[[...]]` style silently skips verification — don't imitate old pages here.

**When to run:** after ingesting a new paper and creating concept/entity pages; after bulk
edits to wiki pages; when the user reports broken links; as part of any wiki maintenance workflow.

## Schema Drift Detection

If the linter's hardcoded `ALLOWED_TAGS` set differs from SCHEMA.md's taxonomy, the linter is stale. The fix is either:
- Update the linter's tag set to match SCHEMA.md, OR
- Parse SCHEMA.md at runtime to extract the taxonomy dynamically

The runtime-parse option is the durable fix: one `load_allowed_tags()` that reads the
`## Tag Taxonomy` section of SCHEMA.md and extracts tokens from each `- **Group:** a, b, c`
line (split on `:` first, then regex `[A-Za-z0-9][A-Za-z0-9-]*` — uppercase tags like
`CODF`/`Kolchin`/`differential-Galois` are legitimate). Linter and schema can then never
drift again.

## Lint False-Positive Audit (check the linter BEFORE fixing content)

A mass warning count (hundreds) is a red flag that the linter's assumptions don't match
the wiki's actual conventions — not that the wiki is broken. 2026-09 session:
`scripts/lint_wiki.py` reported 3 errors / 316 warnings; ~250 were linter bugs, not wiki
defects. Before editing content, verify each warning class against SCHEMA.md and the real
link syntax in use. Known link-form pitfalls, all hit in the math wiki:

- **Markdown links vs `[[wikilinks]]`:** if SCHEMA mandates `[text](target.md)` but the
  linter only parses `[[slug]]`, every page looks broken/not-indexed. `get_wikilinks` must
  consume BOTH forms and treat both as valid outbound links.
- **Hybrid links `[[text]](target.md)`:** the inner `[[text]]` leaks out of the markdown
  regex (double `]]` before `(`) and spawns a spurious wikilink (e.g. `[[Spectrahedron]]`
  failing a case check when the real page is `spectrahedron.md`). Consume markdown link
  spans FIRST (replace with a blank), then parse remaining bare wikilinks.
- **Piped wikilinks `[[path|Display]]`:** bare regex `\[\[([a-zA-Z0-9_\-./]+)\]\]`
  fails when `|Display` follows the path — extend the slug group with `(?:\|[^\]]*)?`.
- **`related:` frontmatter holds path-form targets** (`concepts/x.md`), not bare slugs —
  `page_exists` must split on '/' and strip '.md' before lookup, and check the raw root
  as a valid target.
- **LaTeX false positives:** `[[X]]` inside `\mathbb{R}[[X]]` and
  `f[\lambda_0,\dots](t-\lambda_0)` match link regexes. Filter out single-char slugs,
  targets containing backslashes, and targets starting with `http`/`mailto:`/`#`.
- **ALLOWED_TAGS drift:** see Schema Drift Detection above.

Worked example with the exact failing regexes and the 316→0 fix trajectory:
`references/lint-false-positive-audit-2026-09.md`.

## Related References

- `references/wiki-linting-pitfalls.md` — detailed YAML gotchas and lint script checklist

## Pitfalls

- **Never skip phase 2** — VitePress catches Markdown-style dead links that wikilink scanners miss
- **Always `lstrip()` before frontmatter parsing** — leading blank lines are common after `write_file`
- **Don't hardcode tag sets** — they drift from SCHEMA.md. Either parse SCHEMA.md at runtime or update the linter when SCHEMA.md changes
- **The `related:` frontmatter field is not in the SCHEMA.md template** but is widely used — count it as outbound links
- **VitePress reports dead links with relative paths** — the file path in the error message tells you exactly which file to fix
- **Raw files are immutable** — never edit `raw/` content. If a raw file's frontmatter is wrong, the fix is in the linter or the ingestion process, not the file itself
- **`read_file` may return stale/truncated content after context compaction** —
  re-reading a file that was first read pre-compaction can return "Duplicate tool output"
  or a truncated stub (e.g. a 22K `index.md` shown as 470 chars) even though disk is
  intact. Recover with python `open()`/`pathlib` inside `execute_code`, `terminal`
  `cat`/`sed`, or `search_files` with pattern `.*`/`^` — and verify with `wc -c` against
  the expected size before trusting any read of a compaction-touched file.
