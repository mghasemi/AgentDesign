---
name: semantic-scholar
description: "Use Semantic Scholar Academic Graph API: search papers, citation/reference traversal, recommendations, author profiles, batch metadata (≤500 IDs/req), BibTeX. Authenticated (x-api-key), client-throttled to 1 rps with 429 retry."
version: 1.0.0
author: YOUR-USER
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Literature, Citations, SemanticScholar, Papers, Academic, API, Graph]
    related_skills: [arxiv, academic-research-hub, zotero, project-bib, math-research-workflow, lightrag, wiki-pipeline]
---

# Semantic Scholar — Citation-Graph Layer

Complement to the `arxiv` skill (feed layer). arXiv tells you what exists;
Semantic Scholar tells you **how the literature is connected**: who cites
whom, what is influential, where the open-access PDF is, and what comes next.

## When to Use

| Need | Tool |
|------|------|
| New papers on a topic (preprints) | `arxiv` skill |
| Who cites paper X (forward graph) | `s2.py citations` |
| What does paper X cite (backward graph) | `s2.py references` |
| Relevance search incl. journal postprints | `s2.py search` |
| Is X influential? (cite counts) | `s2.py get` |
| Papers like X (new-area expansion) | `s2.py recommend` |
| Enrich many wiki/PocketBase entries at once | `s2.py batch` |
| BibTeX for a manuscript | `s2.py get --bibtex` |
| Multi-hop citation landscape | `s2.py traverse` |
| Track an author's output | `s2.py author` |

All commands: `python3 /home/YOUR-USER/.hermes/profiles/math/skills/semantic-scholar/scripts/s2.py <command> ...`
(alias the path in shell or use the absolute path; `--json` / `--format json`
gives machine-readable output.)

## Quick Reference

| Command | Example |
|---------|---------|
| Search | `s2.py search "sum of squares certificates nonnegative polynomials" --limit 10 --sort citations` |
| Get paper | `s2.py get arXiv:2304.12145` |
| Citations | `s2.py citations DOI:10.1016/j.jfa.2023.109999 --limit 25` |
| References | `s2.py references arXiv:2304.12145 --limit 25` |
| Authors of | `s2.py authors-of arXiv:2304.12145` |
| Author | `s2.py author YOUR-SURNAME` / `s2.py author --id YOUR-S2-AUTHOR-ID --papers` |
| Batch | `s2.py batch arXiv:2304.12145,DOI:10.1007/... --json` or `--file ids.txt` |
| Recommend | `s2.py recommend arXiv:2304.12145 --limit 10` |
| BibTeX | `s2.py get arXiv:2304.12145 --bibtex` |
| Traverse | `s2.py traverse arXiv:2304.12145 --direction forward --depth 2 --fanout 10` |

## Authentication & Key

- API key lives in `~/.hermes/profiles/math/skills/semantic-scholar/.env`
  (`S2_API_KEY=...`, chmod 600). `S2_API_KEY` env var overrides it.
- Sent as `x-api-key` header on every request.
- **Never** commit the key or print it into reports/summaries.

## Rate Limits (critical)

- **1 request/second cumulative across ALL endpoints** — the strictest of any
  API in the stack. Even mixed traffic (docs fetches, other tools using the
  same key) counts.
- **Observed (2026-08-18): this key gets 429s even for a single isolated
  request after 30 s of silence — something else consumes the key
  concurrently** (browser, another tool/machine). The client grinds through
  with retries (2–19 s per collision). If collisions are frequent, find and
  stop the other consumer; the key is single-user by design.
- The client enforces **≥1.5 s between requests** (completion-anchored,
  shared across processes via a timestamp file) and retries HTTP 429 with
  jittered exponential backoff (honouring `Retry-After`) up to 5 attempts.
- **Batch endpoint**: `POST /graph/v1/paper/batch` accepts **≤500 IDs per
  request**. Bulk enrichment of the wiki/PocketBase queue costs 1 request
  per 500 papers. `batch --file ids.txt` auto-chunks.
- `traverse` is bounded by `--max-total` (default 60 requests) to keep
  multi-hop walks finite.

## Paper ID Formats

`arXiv:2304.12145`, `DOI:10.xxxx/...`, `CorpusId:12345678`,
`PMID:...`, `ACL:...`, or the raw 40-hex S2 paperId. All interchangeable
wherever a `paper_id` argument appears.

## Field Cheat-Sheet

| Field | Meaning |
|-------|---------|
| `title,authors,year,venue,publicationTypes` | basics + journal/conf type |
| `abstract` | abstract text |
| `tldr` | one-sentence model summary (triage aid) |
| `externalIds` | ArXiv, DOI, CorpusId, PMID, ACL, DBLP, MAG |
| `citationCount,influentialCitationCount` | impact signals |
| `referenceCount` | size of backward graph |
| `isOpenAccess,openAccessPdf` | OA flag + direct PDF URL |
| `fieldsOfStudy,s2FieldsOfStudy` | subject classification |
| `citationStyles` | `bibtex`, `apa`, `mla`, `chicago` |
| `embedding` | S2 SPECTER vector (heavy — rarely needed) |
| `contexts` (citations) | sentences citing the paper |

Default fields are tuned for math research (title, authors, year, venue,
types, ids, abstract, counts, OA PDF). Override with `--fields`.

## Workflows

### 1. Literature discovery (Stage 2 of math-research-workflow)
```
s2.py search "<topic>" --sort relevance --limit 15
s2.py search "<topic>" --sort citations --min-citations 50 --limit 15   # established work
s2.py search "<topic>" --sort date --year 2024-2026 --limit 15          # recent work
```
Cross-venue: catches journal postprints (Math. Program., SIAM J. Optim.,
J. Symbolic Comput., ...) that arXiv-only search misses.

### 2. Forward sweep — "what happened after paper X"
```
s2.py citations arXiv:2304.12145 --limit 100 --json > citing.json
```
Sort clientside by citationCount to find the influential follow-ups.
Pitfall: high-cited classics have thousands of citers — paginate with
`--offset`, or use `traverse --direction forward --depth 1 --fanout 50`.

### 3. Backward sweep — reconstruct the foundations of X
```
s2.py references arXiv:2304.12145 --limit 100 --json > refs.json
```

### 4. Bulk enrichment of the wiki / PocketBase queue
The wiki ingestion pipeline (PocketBase arxiv entries) benefits most:
```
# ids.txt: one paper ID per line (# comments allowed)
s2.py batch --file ids.txt --json > enriched.json
```
1 request per 500 IDs → citation counts, venue, OA PDF link, publication
types. Feed `enriched.json` into the PocketBase/wiki enrichment step.

### 5. BibTeX for manuscripts
```
s2.py get arXiv:2304.12145 --bibtex >> refs.bib
```
Cross-check against `project-bib` conventions; S2 BibTeX is decent but
verify journal/volume fields against Zotero for published articles.

### 6. New-area expansion (recommendations)
```
s2.py recommend arXiv:2304.12145 --limit 20
```
Use when entering an adjacent field (e.g. from moment problems to sheaf
theory): recommendations surface the canonical neighbors.

### 7. Multi-hop landscape
```
s2.py traverse arXiv:2304.12145 --direction both --depth 2 --fanout 10 --max-total 60
```
Bounded BFS over the citation graph; text mode ranks discovered nodes by
citation count, `--json` emits `{nodes, edges}` for graph analysis.

## Deployment Note (skill, not MCP)

Deployed as a **terminal skill**, not an MCP server:
- S2 is stateless REST and the 1 rps cap rewards **batch-style calls**
  (one script run per research step) over many fine-grained tool calls —
  the natural shape of a skill.
- Consistent with the literature-tool precedent (`arxiv`,
  `academic-research-hub`, `calibre` are terminal skills).
- Cron-compatible (e.g. weekly citation sweeps of project papers).
- **Upgrade path exists**: `s2.py` exposes `build_parser()` + `main()` and
  accepts `--format json`, so `hermes-mcp-tool` Pattern A (generic
  argparse adapter) can register it as an MCP server in ~3 config lines if
  interactive tool-calling is ever wanted. Not needed now.

## Pitfalls

- **429s are normal** under mixed traffic; the client retries up to 5× and
  paces requests across processes via a shared timestamp file
  (`/tmp/s2_throttle_<uid>.ts`) — sequential CLI invocations self-pace.
  If `[s2] HTTP 429` still repeats, another machine/process shares the key.
- `openAccessPdf` is `null` for paywalled papers; `isOpenAccess` is the
  better filter flag.
- `tldr` is absent for some (especially older) papers — never treat its
  absence as paper absence.
- Batch returns `null` entries for IDs S2 cannot resolve — count resolved
  vs. requested.
- Author search: use a single surname (`Ghasemi`, not "Ghasemi Curto");
  multi-word queries often return 0 hits. Disambiguate via `--id` +
  affiliations.
- Citation counts lag reality (months behind) and undercount citations in
  venues S2 indexes poorly; treat as a lower bound.
- S2 paper records for arXiv-only preprints can merge badly with journal
  versions — check `venue` and `publicationTypes` to spot the version.
