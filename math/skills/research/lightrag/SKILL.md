---
name: lightrag
description: Use when searching or querying the LightRAG graph-RAG literature knowledge base. Query documents/entities/relationships (read-only). CLI tool + raw HTTP API.
version: 2.0.0
author: YOUR-USER
license: MIT
metadata:
  hermes:
    tags: [lightrag, rag, literature, knowledge-graph, graph-rag, academic, research]
    related_skills: [vikunja, arxiv, academic-research-hub, semantic-scholar]
---

# LightRAG — Graph-RAG Literature Knowledge Base

LightRAG is a graph-based RAG system that indexes curated academic literature into
a knowledge graph with entities, relationships, and vector chunks. It supports
multiple query modes: local (entity-focused), global (pattern analysis), hybrid,
naive (vector-only), mix (recommended), and bypass (LLM-only).

This skill covers **querying** the knowledge graph (read-only).

Two ways to drive it, pick per task:
1. **CLI tool** (recommended for routine work) — `lightrag_query_tool.py` lives
   in this skill's directory.
2. **Raw HTTP API** via `execute_code` — full control, no tool dependency.

## When to Use

- User asks to "search my papers", "query LightRAG", or "what's in my literature KB"
- User wants to find papers, entities, or concepts in their curated academic collection
- User asks for literature-backed answers that benefit from graph-RAG retrieval
- User wants to explore the knowledge graph (entities, labels, relationships)
- User mentions "LightRAG", "graph RAG", or "literature search"

## Environment Variables

| Variable | Example | Purpose |
|----------|---------|---------|
| `LIGHTRAG_URL` | `http://YOUR-HOST:9621` | Primary LightRAG endpoint |
| `LIGHTRAG_ALT_URL` | `http://YOUR-DDNS-HOST:9621` | Fallback if primary fails |
| `LIGHTRAG_TIMEOUT` | `20` | Query request timeout in seconds |
| `LIGHTRAG_API_KEY` | (empty) | API key if auth is enabled |

---

# Part 1 — CLI Tools (recommended)

Both tools live in this skill's directory (`{baseDir}`). They handle URL fallback,
timeouts, and JSON formatting for you.

## Query tool — `lightrag_query_tool.py`

### Query (recommended)

```bash
python3 {baseDir}/lightrag_query_tool.py query "What is the SDP hierarchy?" --mode mix
python3 {baseDir}/lightrag_query_tool.py query "Summarize SONC vs SOS" --mode hybrid --include-references --format json
```

### Structured retrieval only (no LLM)

```bash
python3 {baseDir}/lightrag_query_tool.py query-data "sdp hierarchy" --mode local --top-k 5 --format json
```

### Streaming query

```bash
python3 {baseDir}/lightrag_query_tool.py query-stream "Explain Moment-SOS relaxations" --mode mix
```

### Override URL and fallback

```bash
python3 {baseDir}/lightrag_query_tool.py --url http://YOUR-HOST:9621 --alt-url http://YOUR-DDNS-HOST:9621 query "sdp hierarchy"
```

Subcommands: `query` (LLM answer + refs), `query-data` (structured payload),
`query-stream` (NDJSON chunks). `--format json` for machine-readable output.

## CLI Pitfalls

- **Timeout is an environment variable, NOT a CLI flag.** Do NOT pass `--timeout 60`
  on the query subcommand (causes exit code 2). Set it via the env var instead:
  ```bash
  export LIGHTRAG_TIMEOUT=90
  python3 lightrag_query_tool.py query "..." --mode local
  ```
- **Timeout on complex/hybrid queries.** `--mode mix` and `--mode hybrid` often time
  out at the default 20s, especially with long or multi-topic query strings. Set
  `LIGHTRAG_TIMEOUT=90` (env var) for reliable responses. Shorter, focused query
  strings also help.
- **Server health check.** If queries consistently time out, first verify the server
  is up with `curl --max-time 5 <LIGHTRAG_URL>/health`. The server may be overloaded
  by slow LLM backends (e.g. the OpenRouter API gateway).
- **URL override disables fallback.** If you override the primary URL on the CLI with
  `--url`, fallback is disabled unless you also provide `--alt-url`.

---

# Part 2 — Raw HTTP API (via `execute_code`)

Use this when you need fine-grained control or the CLI isn't available.

## Connection & Auth

LightRAG may or may not require OAuth2 authentication depending on its config.
Check auth status first:

```
GET <base>/auth-status → {"auth_mode": "enabled"} or {"auth_mode": "disabled"}
```

If auth is enabled, authenticate via the `/login` endpoint. Otherwise, calls are
unauthenticated.

**Fallback pattern:** try `LIGHTRAG_URL` first. If unreachable, retry with
`LIGHTRAG_ALT_URL`.

```
GET <base>/health → 200 {"status": "healthy", ...} → ready
```

## API Reference

All paths are at the root of the base URL.

### Core Query Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/query` | Full RAG query — returns LLM-generated response + optional references |
| POST | `/query/data` | Pure data retrieval — returns entities, relationships, chunks (no LLM generation) |
| POST | `/query/stream` | Streaming RAG query |

### Discovery Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/documents` | List all documents |
| POST | `/documents/paginated` | Paginated doc list with status filter & sorting |
| GET | `/documents/status_counts` | Count of documents by processing status |
| GET | `/graphs` | Get knowledge graph subgraph (requires `label` param, optional `max_depth`, `max_nodes`) |
| GET | `/graph/label/list` | List all entity/relation labels in the knowledge graph |
| GET | `/graph/label/search` | Search labels by substring (`?q=...&limit=N`) |
| GET | `/graph/entity/exists` | Check if an entity name exists (`?name=...`) |

### Query Modes

| Mode | Behavior |
|------|----------|
| `local` | Entities + their direct relationships + related chunks |
| `global` | Pattern analysis across the full knowledge graph |
| `hybrid` | Combines local + global (comprehensive) |
| `naive` | Pure vector similarity search (no knowledge graph) |
| `mix` | Knowledge graph + vector search (**recommended default**) |
| `bypass` | Direct LLM query — ignores knowledge base entirely |

### QueryRequest Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | **yes** | The question or search prompt (min 3 chars) |
| `mode` | string | no | Query mode — default: `mix` |
| `response_type` | string | no | Format hint: `Multiple Paragraphs`, `Single Paragraph`, `Bullet Points` |
| `top_k` | integer | no | Number of top entities (local) or relationships (global) to retrieve |
| `chunk_top_k` | integer | no | Number of text chunks to retrieve initially, keep after reranking |
| `max_entity_tokens` | integer | no | Token budget for entity context |
| `max_relation_tokens` | integer | no | Token budget for relationship context |
| `max_total_tokens` | integer | no | Total token budget for the entire query context |
| `hl_keywords` | array | no | High-level keywords — provide to bypass initial LLM keyword extraction |
| `ll_keywords` | array | no | Low-level keywords — refine retrieval focus |
| `include_references` | boolean | no | Include source citations (only on `/query` — `/query/data` always includes them) |
| `include_chunk_content` | boolean | no | Include actual chunk text in references |
| `only_need_context` | boolean | no | Return only the retrieved context, no LLM response |
| `only_need_prompt` | boolean | no | Return only the generated prompt, no LLM response |
| `conversation_history` | array | no | Previous turns `[{role, content}]` — sent to LLM only, not used for retrieval |

### QueryResponse (from `/query`)

```json
{
  "response": "The generated answer...",
  "references": [
    {"reference_id": "1", "file_path": "/papers/example.pdf", "content": ["chunk text..."]}
  ]
}
```

### QueryDataResponse (from `/query/data`)

```json
{
  "status": "success",
  "message": "Query completed",
  "data": {
    "entities": [...],
    "relationships": [...],
    "chunks": [...],
    "references": [...]
  },
  "metadata": {
    "mode": "mix",
    "keywords": {"hl_keywords": [...], "ll_keywords": [...]},
    "processing": {...}
  }
}
```

## `execute_code` Recipes

### Helper: Resolve base URL + verify connection

```python
import urllib.request, urllib.error
import json, os

def resolve_base():
    """Try URLs in priority order, return first that responds to /health."""
    candidates = [
        os.environ.get("LIGHTRAG_URL", ""),
        os.environ.get("LIGHTRAG_ALT_URL", ""),
    ]
    for url in candidates:
        if not url:
            continue
        try:
            req = urllib.request.Request(f"{url}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.load(resp)
                    print(f"Connected: {url}")
                    print(f"  Version: {data.get('core_version', '?')}")
                    print(f"  Auth: {data.get('auth_mode', '?')}")
                    print(f"  Pipeline busy: {data.get('pipeline_busy', '?')}")
                    return url
        except Exception as e:
            print(f"Failed {url}: {e}")
    print("ERROR: Cannot reach LightRAG")
    return None
```

### Recipe: Query with LLM response (most common)

```python
def query_rag(base, query_text, mode="mix", response_type=None, top_k=None):
    import urllib.request, json
    body = {"query": query_text, "mode": mode}
    if response_type: body["response_type"] = response_type
    if top_k is not None: body["top_k"] = top_k
    body["include_references"] = True

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{base}/query",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)
        print(result["response"])
        if "references" in result and result["references"]:
            print(f"\n--- References ({len(result['references'])} sources) ---")
            for ref in result["references"]:
                print(f"  [{ref['reference_id']}] {ref['file_path']}")
        return result
```

### Recipe: Query raw data (no LLM)

```python
def query_data(base, query_text, mode="mix", top_k=10):
    import urllib.request, json
    body = {"query": query_text, "mode": mode, "top_k": top_k}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{base}/query/data",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)

    d = result.get("data", {})
    print(f"Entities: {len(d.get('entities', []))}")
    print(f"Relationships: {len(d.get('relationships', []))}")
    print(f"Chunks: {len(d.get('chunks', []))}")
    print(f"References: {len(d.get('references', []))}")

    # Print entities
    for e in d.get("entities", []):
        name = e.get("entity_name", e.get("name", "?"))
        desc = e.get("description", "")[:120]
        print(f"  Entity: {name} — {desc}")

    # Print top chunks
    for c in d.get("chunks", [])[:5]:
        chunk_id = c.get("chunk_id", "?")
        content = c.get("content", "")[:200]
        print(f"  Chunk {chunk_id}: {content}...")

    return result
```

### Recipe: Search labels / explore knowledge graph

```python
def search_labels(base, query, limit=20):
    import urllib.request, urllib.parse, json
    qs = urllib.parse.urlencode({"q": query, "limit": limit})
    with urllib.request.urlopen(f"{base}/graph/label/search?{qs}", timeout=10) as resp:
        data = json.load(resp)
    for label in data if isinstance(data, list) else data.get("labels", []):
        print(f"  {label}")
    return data

def get_graph(base, label, max_depth=2, max_nodes=30):
    import urllib.request, urllib.parse, json
    qs = urllib.parse.urlencode({"label": label, "max_depth": max_depth, "max_nodes": max_nodes})
    with urllib.request.urlopen(f"{base}/graphs?{qs}", timeout=10) as resp:
        data = json.load(resp)
    print(f"Graph nodes: {len(data.get('nodes', data))}")
    return data

def list_labels(base):
    import urllib.request, json
    with urllib.request.urlopen(f"{base}/graph/label/list", timeout=10) as resp:
        return json.load(resp)
```

### Recipe: List documents

```python
def list_documents(base):
    import urllib.request, json
    with urllib.request.urlopen(f"{base}/documents", timeout=10) as resp:
        data = json.load(resp)
    if isinstance(data, list):
        for d in data[:20]:
            print(f"  [{d.get('status','?')}] {d.get('id','?')}: {d.get('content_summary','')[:100]}")
        print(f"  ... ({len(data)} total)")
    return data
```

## Common Pitfalls

1. **Query must be ≥ 3 characters.** The API rejects shorter queries with a 400
   error. Always formulate a meaningful query string.

2. **Mode selection matters.** `mix` is the recommended default for most queries.
   Use `naive` for quick vector-only search. Use `local` when exploring specific
   entities. Use `global` for broad pattern questions. Avoid `bypass` unless you
   want to ignore the knowledge base entirely.

3. **`/query` vs `/query/data`.** `/query` returns an LLM-generated answer with
   optional references. `/query/data` returns the raw retrieval data (entities,
   relationships, chunks) without LLM generation — use for analysis or debugging.

4. **Auth may be disabled.** Check `GET /health` → `auth_mode`. If it's `disabled`,
   all calls are unauthenticated. If `enabled`, you'll need to authenticate via
   `/login` first.

5. **Providing keywords skips the initial LLM call.** If you pass `hl_keywords`
   and `ll_keywords`, LightRAG won't call the LLM to extract keywords from your
   query. This saves latency when you already know the precise terms to search for.

6. **Conversation history is LLM-only.** The `conversation_history` parameter
   only affects the LLM's response generation — it does not influence retrieval.

7. **References are optional on `/query`.** Set `include_references: true` to
   get source citations. On `/query/data`, references are always included.

8. **Timeout for complex queries.** Graph traversal queries (`global`, `hybrid`,
   `local`) can take longer than `naive`. Use the longer timeout (30s default
   in recipes) for these modes; for the CLI, raise `LIGHTRAG_TIMEOUT`.

## Verification Checklist

- [ ] `GET /health` returns `{"status":"healthy"}` on at least one URL
- [ ] `POST /query` with a simple query returns a response
- [ ] `POST /query/data` returns structured data (entities, chunks, references)
- [ ] `GET /documents` returns the document list
- [ ] `GET /graph/label/list` returns knowledge graph labels
- [ ] `GET /graph/label/search?q=test` works

