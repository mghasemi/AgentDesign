# Lint False-Positive Audit — worked example (2026-09)

Wiki: `/home/YOUR-USER/Code/wiki` (math wiki). Linter: `scripts/lint_wiki.py`.

## Trajectory

| Run | Errors | Warnings | Notes |
|-----|--------|----------|-------|
| initial | 3 | 316 | 3 real frontmatter errors (see below) + ~250 linter bugs |
| after get_wikilinks + page_exists patches | 0 | 115 | 60 tag-taxonomy, 27 few-outbound, 14 broken, 8 not-indexed, 4 index→missing |
| after ALLOWED_TAGS sync with SCHEMA | 0 | 88 | 41 tag, 29 few-links, 18 broken/index |
| after raw-root + hybrid-link fixes | exit=1 empty | — | inline `consume` lambda broke on plain-link group |
| after plain-link-group fix + piped-wikilink regex | 0 | 54 | all remaining genuine |
| final (content fixes applied) | **0** | **0** | — |

## The 3 real errors (all in raw/ frontmatter)

1. `raw/articles/brouette-...2015.md`: `source:` instead of `source_url:`
2. Same file: truncated `sha256` (16 hex chars — the sha256 convention hashes the
   source page HTML, e.g. the live arXiv `/abs/` page, NOT the PDF or e-print; verify
   with `curl -sL https://arxiv.org/abs/<id> | sha256sum`)
3. `raw/articles/semidefinite-optimization-...-bpt-2012.md`: missing `ingested:`

## Linter bugs found (each removed dozens of false warnings)

1. **`get_wikilinks` only parsed bare `[[slug]]`** — but SCHEMA mandates Markdown links
   `[text](path.md)`. Every page looked "not listed in index" (92 warnings) and every
   markdown link looked broken.
2. **Hybrid links `[[text]](target.md)`** — the inner `[[text]]` leaked out of the
   markdown regex (double `]]` before `(`), e.g. `[[Spectrahedron]](spectrahedron.md)`
   produced a spurious `[[Spectrahedron]]` that failed the case check (real page is
   lowercase). Fix: consume markdown link spans first, then parse bare wikilinks on the
   remainder; for hybrids the markdown target is authoritative.
3. **Piped wikilinks `[[path|Display]]`** — bare regex `\[\[([a-zA-Z0-9_\-./]+)\]\]`
   missed them entirely (pages looked like they had 0 outbound links). Fix: slug group
   followed by optional `(?:\|[^\]]*)?`.
4. **`related:` frontmatter path-form targets** — `page_exists` treated
   `concepts/x.md` as a bare slug. Fix: split on '/', strip '.md', check content dirs
   AND raw root.
5. **LaTeX false positives** — `[[X]]` inside `\mathbb{R}[[X]]` and
   `f[\lambda_0,\dots](t-\lambda_0)` matched link regexes. Fix: drop single-char slugs,
   targets containing backslashes, and `http`/`mailto:`/`#` targets.
6. **Hardcoded `ALLOWED_TAGS` drifted from SCHEMA taxonomy** — 19 tags in SCHEMA were
   missing from the linter (jet-spaces, prolongation, differential-algebra,
   approximation-theory, …) and 25 used tags were missing from BOTH. Fix: parse the
   taxonomy from SCHEMA.md at runtime (`load_allowed_tags()`), so they can't drift.
7. **Index rows pointing to missing pages** — a concurrent writer's index row linked
   `entities/sos-moment-equivariant-...2008.md` (never existed); the real entity is
   `entities/cimpric-kuhlmann-scheiderer-equivariant-moment-2008.md`. Fix: correct the
   row, and where index referenced concept pages never created
   (`differential-galois-theory`, `invariant-theory`), retarget to existing pages in the
   same domain (e.g. `picard-vessiot-extensions.md`) or create the page.

## Genuine issues fixed in content (not linter)

- 3 raw frontmatter errors (above)
- `[[concepts/moment-hierarchy.md|Moment Hierarchy]]` → target page never created;
  retargeted to existing `entities/infinite-dimensional-moment-sos-hierarchy.md`
- `entities/infinite-dimensional-moment-sos-hierarchy.md` had 0 outbound links — added
  a Related Pages section (6 links to existing concept pages)
- 7 concept pages + 1 entity page missing from `index.md` — added under correct sections
- SCHEMA.md tag taxonomy extended with the 25 legitimately-used tags

## Procedure that works

1. Run the linter, capture full output to a file (`python3 scripts/lint_wiki.py > /tmp/lintN.txt 2>&1`).
2. **Classify warnings by cause BEFORE editing content** — most are linter bugs when the
   count is in the hundreds.
3. Derive the actual tag set in use (`grep -rh "^tags:" concepts/ entities/ | tr ',' '\n' | sort -u`)
   and diff against the taxonomy; extend SCHEMA.md first, linter reads it at runtime.
4. Fix linter → re-run → fix genuine content issues → re-run to 0/0.
5. Verify with `git status` and a final clean run.
