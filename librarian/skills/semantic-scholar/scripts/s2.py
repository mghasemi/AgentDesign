#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Scholar Academic Graph API CLI — research tool for the math profile.

Auth: S2_API_KEY env var, else the skill's .env file (scripts/../.env).
Rate limits: 1 req/s cumulative across ALL endpoints. This client throttles
to >=1.2 s between requests and retries HTTP 429 with exponential backoff
(honouring Retry-After). 429s still happen under mixed traffic — always retry.

Stdlib only. MCP-adapter-ready (mcp-server-playbook Pattern A): exposes
build_parser() and main(); every subcommand accepts --json / --format json.
"""

import argparse
import json
import os
import random
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.semanticscholar.org"
THROTTLE_S = 1.5
MAX_RETRIES = 5
BATCH_CHUNK = 500

# Shared timestamp file: paces requests across PROCESSES, not just within one
# run (the agent invokes s2.py as fresh processes in quick succession).
_uid = os.getuid() if hasattr(os, "getuid") else 0
THROTTLE_FILE = os.path.join(tempfile.gettempdir(), f"s2_throttle_{_uid}.ts")

DEFAULT_FIELDS = ("title,authors,year,venue,publicationTypes,externalIds,abstract,"
                  "citationCount,influentialCitationCount,openAccessPdf")
RECOMMEND_FIELDS = ("title,authors,year,venue,citationCount,externalIds,"
                    "abstract,openAccessPdf")

_last_request = 0.0


def load_key():
    key = os.environ.get("S2_API_KEY", "").strip()
    if key:
        return key
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            os.pardir, ".env")
    try:
        with open(env_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("S2_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def _throttle():
    global _last_request
    wait = THROTTLE_S - (time.monotonic() - _last_request)
    try:
        cross = THROTTLE_S - (time.time() - os.path.getmtime(THROTTLE_FILE))
        wait = max(wait, cross)
    except OSError:
        pass
    if wait > 0:
        time.sleep(wait)


def _mark_request():
    global _last_request
    _last_request = time.monotonic()
    try:
        with open(THROTTLE_FILE, "a"):
            os.utime(THROTTLE_FILE, None)
    except OSError:
        pass


def api_get(path, method="GET", body=None, timeout=45):
    """One API call with global throttle + 429/connection retry."""
    global _last_request
    url = BASE + path
    headers = {}
    key = load_key()
    if key:
        headers["x-api-key"] = key
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    for attempt in range(MAX_RETRIES):
        _throttle()
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            _mark_request()  # pace from COMPLETION, not start
            return payload
        except urllib.error.HTTPError as exc:
            _mark_request()
            if exc.code == 404:
                sys.stderr.write(f"[s2] not found: {path}\n")
                return None
            if exc.code == 429 and attempt < MAX_RETRIES - 1:
                delay = 2 ** attempt + 1.0 + random.uniform(0.0, 1.0)  # jitter
                try:
                    delay = max(delay, float(exc.headers.get("Retry-After", 0)))
                except (TypeError, ValueError):
                    pass
                sys.stderr.write(
                    f"[s2] 429 rate-limited — retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{MAX_RETRIES - 1})\n")
                time.sleep(delay)
                continue
            try:
                detail = exc.read().decode("utf-8", "replace")[:300]
            except Exception:
                detail = ""
            sys.stderr.write(f"[s2] HTTP {exc.code} on {path}: {detail}\n")
            return None
        except (urllib.error.URLError, TimeoutError) as exc:
            _mark_request()
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            sys.stderr.write(f"[s2] connection error: {exc}\n")
            return None
    return None


def qs(**params):
    clean = {k: v for k, v in params.items() if v is not None and v != ""}
    return urllib.parse.urlencode(clean)


def paper_brief(p):
    if not isinstance(p, dict):
        return None
    authors = ", ".join(a.get("name", "?") for a in (p.get("authors") or [])[:6])
    if len(p.get("authors") or []) > 6:
        authors += " et al."
    ext = p.get("externalIds") or {}
    oa = (p.get("openAccessPdf") or {}).get("url")
    tldr = (p.get("tldr") or {}).get("text")
    return {
        "title": p.get("title"),
        "year": p.get("year"),
        "venue": p.get("venue") or (p.get("journal") or {}).get("name"),
        "publicationTypes": p.get("publicationTypes"),
        "authors": authors,
        "paperId": p.get("paperId"),
        "externalIds": ext,
        "citationCount": p.get("citationCount"),
        "influentialCitationCount": p.get("influentialCitationCount"),
        "referenceCount": p.get("referenceCount"),
        "openAccessPdf": oa,
        "tldr": tldr,
        "abstract": (p.get("abstract") or "")[:400],
        "url": p.get("url"),
    }


def render_paper(i, p):
    b = paper_brief(p)
    if not b:
        return ["(entry unavailable)"]
    lines = [f"[{i}] {b['title']}"]
    meta = []
    if b["year"]:
        meta.append(str(b["year"]))
    if b["venue"]:
        meta.append(b["venue"])
    if b["publicationTypes"]:
        meta.append("/".join(b["publicationTypes"]))
    if b["citationCount"] is not None:
        meta.append(f"cites: {b['citationCount']}")
    lines.append("    " + " | ".join(meta))
    if b["authors"]:
        lines.append(f"    Authors: {b['authors']}")
    ids = []
    if b["externalIds"].get("ArXiv"):
        ids.append("arXiv:" + b["externalIds"]["ArXiv"])
    if b["externalIds"].get("DOI"):
        ids.append("DOI:" + b["externalIds"]["DOI"])
    if ids:
        lines.append("    " + " | ".join(ids))
    if b["openAccessPdf"]:
        lines.append(f"    OA PDF: {b['openAccessPdf']}")
    if b["tldr"]:
        lines.append(f"    TLDR: {b['tldr']}")
    if b["abstract"]:
        lines.append(f"    Abstract: {b['abstract']}...")
    return lines


# ---------------------------------------------------------------- commands

def cmd_search(args):
    params = dict(query=args.query, limit=args.limit, offset=args.offset,
                  fields=args.fields or DEFAULT_FIELDS + ",tldr")
    if args.year:
        params["year"] = args.year
    if args.venue:
        params["venue"] = args.venue
    if args.min_citations is not None:
        params["minCitationCount"] = args.min_citations
    if args.open_access:
        params["openAccessPdf"] = "true"
    if args.sort == "citations":
        params["sort"] = "citationCount"
    elif args.sort == "date":
        params["sort"] = "publicationDate"
    d = api_get("/graph/v1/paper/search?" + qs(**params))
    if d is None:
        return 1
    if args.json:
        print(json.dumps(d, indent=2))
        return 0
    print(f"query: {args.query} — total hits: {d.get('total')}, "
          f"showing {len(d.get('data') or [])}")
    for i, p in enumerate(d.get("data") or [], 1):
        print("\n".join(render_paper(i, p)))
    return 0


def cmd_get(args):
    fields = args.fields or (DEFAULT_FIELDS + ",tldr,referenceCount")
    if args.bibtex:
        fields = "citationStyles"
    d = api_get("/graph/v1/paper/" + urllib.parse.quote(args.paper_id)
                + "?" + qs(fields=fields))
    if d is None:
        return 1
    if args.bibtex:
        bib = (d.get("citationStyles") or {}).get("bibtex")
        print(bib if bib else "(no BibTeX available)")
        return 0
    if args.json:
        print(json.dumps(d, indent=2))
        return 0
    print("\n".join(render_paper(1, d)))
    return 0


def _graph_edges(kind, args):
    d = api_get("/graph/v1/paper/" + urllib.parse.quote(args.paper_id)
                + f"/{kind}?" + qs(fields=args.fields or DEFAULT_FIELDS,
                                   limit=args.limit, offset=args.offset))
    if d is None:
        return 1
    key = "citingPaper" if kind == "citations" else "citedPaper"
    rows = d.get("data") or []
    if args.json:
        print(json.dumps(d, indent=2))
        return 0
    nxt = f" (next offset: {d.get('next')})" if d.get("next") else ""
    print(f"{kind} of {args.paper_id}: {len(rows)} shown{nxt}")
    for i, r in enumerate(rows, 1):
        lines = render_paper(i, r.get(key))
        if kind == "citations" and r.get("contexts"):
            ctx = " ... ".join(r["contexts"][:2])
            if ctx:
                lines.append(f"    Contexts: {ctx[:300]}")
        print("\n".join(lines))
    return 0


def cmd_authors_of(args):
    d = api_get("/graph/v1/paper/" + urllib.parse.quote(args.paper_id)
                + "/authors?" + qs(fields="name,authorId,affiliations,hIndex,"
                                         "paperCount,citationCount"))
    if d is None:
        return 1
    if args.json:
        print(json.dumps(d, indent=2))
        return 0
    print(f"authors of {args.paper_id}:")
    for i, a in enumerate(d.get("data") or [], 1):
        print(f"  {i}. {a.get('name')} (id {a.get('authorId')}) | "
              f"hIndex: {a.get('hIndex')} | papers: {a.get('paperCount')}")
    return 0


def cmd_author(args):
    if args.author_id:
        a = api_get("/graph/v1/author/" + urllib.parse.quote(args.author_id)
                    + "?" + qs(fields="name,affiliations,hIndex,paperCount,"
                                       "citationCount,url"))
        if a is None:
            return 1
        rows = None
        if args.papers:
            rows = api_get("/graph/v1/author/"
                           + urllib.parse.quote(str(a.get("authorId")))
                           + "/papers?" + qs(fields=DEFAULT_FIELDS,
                                             limit=args.limit))
        if args.json:
            print(json.dumps({"author": a, "papers": rows}, indent=2))
            return 0
        print(f"{a.get('name')} | hIndex: {a.get('hIndex')} | "
              f"papers: {a.get('paperCount')} | cites: {a.get('citationCount')}")
        if rows:
            for i, p in enumerate(rows.get("data") or [], 1):
                print("\n".join(render_paper(i, p)))
        return 0
    d = api_get("/graph/v1/author/search?"
                + qs(query=args.query,
                     fields="name,affiliations,hIndex,paperCount,citationCount"))
    if d is None:
        return 1
    if args.json:
        print(json.dumps(d, indent=2))
        return 0
    print(f"author search '{args.query}': {d.get('total')} hits")
    for i, a in enumerate((d.get("data") or [])[:10], 1):
        affs = "; ".join(a.get("affiliations") or [])[:60]
        print(f"  {i}. {a.get('name')} (id {a.get('authorId')}) | "
              f"hIndex: {a.get('hIndex')} | papers: {a.get('paperCount')} | "
              f"{affs}")
    return 0


def cmd_batch(args):
    ids = []
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                ids.extend(ln.strip() for ln in fh
                           if ln.strip() and not ln.startswith("#"))
        except OSError as exc:
            sys.stderr.write(f"[s2] cannot read {args.file}: {exc}\n")
            return 1
    for tok in args.ids or []:
        ids.extend(t for t in tok.split(",") if t)
    if not ids:
        sys.stderr.write("[s2] no IDs given (pass IDs, or --file with one per line)\n")
        return 1
    fields = args.fields or DEFAULT_FIELDS
    out = []
    for i in range(0, len(ids), BATCH_CHUNK):
        chunk = ids[i:i + BATCH_CHUNK]
        sys.stderr.write(f"[s2] batch chunk {i // BATCH_CHUNK + 1}: "
                         f"{len(chunk)} IDs\n")
        d = api_get("/graph/v1/paper/batch?" + qs(fields=fields),
                    method="POST", body={"ids": chunk})
        if d is not None:
            out.extend(d)
    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    print(f"batch: {len(ids)} IDs requested, {len(out)} resolved")
    for i, p in enumerate(out, 1):
        print("\n".join(render_paper(i, p)))
    return 0


def cmd_recommend(args):
    d = api_get("/recommendations/v1/papers/forpaper/"
                + urllib.parse.quote(args.paper_id)
                + "?" + qs(fields=args.fields or RECOMMEND_FIELDS,
                           limit=args.limit))
    if d is None:
        return 1
    if args.json:
        print(json.dumps(d, indent=2))
        return 0
    rows = d.get("recommendedPapers") or []
    print(f"recommendations for {args.paper_id}: {len(rows)}")
    for i, p in enumerate(rows, 1):
        print("\n".join(render_paper(i, p)))
    return 0


def cmd_traverse(args):
    dirs = {"forward": ["citations"], "backward": ["references"],
            "both": ["citations", "references"]}[args.direction]
    nodes, edges, budget = {}, [], args.max_total
    start = args.paper_id
    nodes[start] = api_get("/graph/v1/paper/" + urllib.parse.quote(start)
                           + "?" + qs(fields=DEFAULT_FIELDS))
    budget -= 1
    frontier = [start]
    for depth in range(1, args.depth + 1):
        nxt = []
        for pid in frontier:
            if budget <= 0:
                break
            for kind in dirs:
                if budget <= 0:
                    break
                d = api_get("/graph/v1/paper/" + urllib.parse.quote(pid)
                            + f"/{kind}?" + qs(fields=DEFAULT_FIELDS,
                                               limit=args.fanout))
                budget -= 1
                if not d:
                    continue
                key = "citingPaper" if kind == "citations" else "citedPaper"
                for r in d.get("data") or []:
                    child = r.get(key) or {}
                    cid = (child.get("paperId")
                           or (child.get("externalIds") or {}).get("CorpusId")
                           or child.get("title"))
                    if cid is None:
                        continue
                    if cid not in nodes:
                        nodes[cid] = child
                        nxt.append(cid)
                    edges.append({"from": pid, "to": cid, "type": kind,
                                  "year": child.get("year"),
                                  "cites": child.get("citationCount")})
        frontier = nxt
        sys.stderr.write(f"[s2] depth {depth}: {len(nodes)} nodes, "
                         f"{len(edges)} edges, budget {budget}\n")
    if args.json:
        print(json.dumps({"nodes": nodes, "edges": edges}, indent=2))
        return 0
    print(f"traverse {start} ({args.direction}, depth {args.depth}, "
          f"fanout {args.fanout}): {len(nodes)} nodes, {len(edges)} edges")
    ranked = sorted((p for p in nodes.values() if isinstance(p, dict)),
                    key=lambda p: -(p.get("citationCount") or 0))[:15]
    for i, p in enumerate(ranked, 1):
        b = paper_brief(p)
        arx = b["externalIds"].get("ArXiv") or "-"
        print(f"  {i}. {b['title']} ({b['year']}) cites:{b['citationCount']} "
              f"arXiv:{arx}")
    return 0


# ------------------------------------------------------------------ parser

def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", dest="json",
                        help="machine-readable JSON output")
    common.add_argument("--format", choices=["text", "json"], default=None,
                        dest="format", help="output format (MCP adapter compat)")

    p = argparse.ArgumentParser(
        prog="s2",
        description="Semantic Scholar Academic Graph API CLI (1 rps, throttled)")
    p.add_argument("--json", action="store_true", dest="json")
    p.add_argument("--format", choices=["text", "json"], default=None,
                   dest="format")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("search", parents=[common],
                        help="relevance search across all venues")
    sp.add_argument("query")
    sp.add_argument("--limit", type=int, default=10)
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--year", help="publication year or range 2010-2020")
    sp.add_argument("--venue")
    sp.add_argument("--min-citations", type=int)
    sp.add_argument("--open-access", action="store_true")
    sp.add_argument("--sort", choices=["relevance", "citations", "date"],
                    default="relevance")
    sp.add_argument("--fields")
    sp.set_defaults(func=cmd_search)

    gp = sub.add_parser("get", parents=[common], help="fetch one paper by ID")
    gp.add_argument("paper_id",
                    help="S2 ID, DOI:..., arXiv:..., CorpusId:n, PMID:..., ACL:...")
    gp.add_argument("--fields")
    gp.add_argument("--bibtex", action="store_true",
                    help="print BibTeX via citationStyles")
    gp.set_defaults(func=cmd_get)

    cp = sub.add_parser("citations", parents=[common],
                        help="papers citing this paper (forward graph)")
    cp.add_argument("paper_id")
    cp.add_argument("--limit", type=int, default=20)
    cp.add_argument("--offset", type=int, default=0)
    cp.add_argument("--fields")
    cp.set_defaults(func=lambda a: _graph_edges("citations", a))

    rp = sub.add_parser("references", parents=[common],
                        help="papers cited by this paper (backward graph)")
    rp.add_argument("paper_id")
    rp.add_argument("--limit", type=int, default=20)
    rp.add_argument("--offset", type=int, default=0)
    rp.add_argument("--fields")
    rp.set_defaults(func=lambda a: _graph_edges("references", a))

    ap = sub.add_parser("authors-of", parents=[common],
                        help="authors of a paper")
    ap.add_argument("paper_id")
    ap.set_defaults(func=cmd_authors_of)

    au = sub.add_parser("author", parents=[common],
                        help="author lookup by name (or profile by --id)")
    au.add_argument("query", nargs="?",
                    help="name to search (single surname works best)")
    au.add_argument("--id", dest="author_id", help="authorId for direct profile")
    au.add_argument("--papers", action="store_true", help="also list papers")
    au.add_argument("--limit", type=int, default=20)
    au.set_defaults(func=cmd_author)

    bp = sub.add_parser("batch", parents=[common],
                        help="bulk metadata, <=500 IDs per request (auto-chunked)")
    bp.add_argument("ids", nargs="*", help="IDs, comma- or space-separated")
    bp.add_argument("--file", help="read IDs from file (one per line, # comments)")
    bp.add_argument("--fields")
    bp.set_defaults(func=cmd_batch)

    rc = sub.add_parser("recommend", parents=[common],
                        help="'papers like this' recommendations")
    rc.add_argument("paper_id")
    rc.add_argument("--limit", type=int, default=10)
    rc.add_argument("--fields")
    rc.set_defaults(func=cmd_recommend)

    tp = sub.add_parser("traverse", parents=[common],
                        help="multi-hop citation graph walk (throttled)")
    tp.add_argument("paper_id")
    tp.add_argument("--direction", choices=["forward", "backward", "both"],
                    default="both")
    tp.add_argument("--depth", type=int, default=2)
    tp.add_argument("--fanout", type=int, default=10)
    tp.add_argument("--max-total", type=int, default=60,
                    help="max API requests (rate budget)")
    tp.add_argument("--fields")
    tp.set_defaults(func=cmd_traverse)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if getattr(args, "format", None) == "json":
        args.json = True
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
