# AgentDesign stack — the profiles' service plane

One `docker compose` project that brings up **the entire self-hosted stack the `math` and
`librarian` Hermes profiles depend on**: sixteen containers that on the live host
(the live host, reachable on the LAN as `http://YOUR-HOST/`) currently run as seven separate compose projects
under `/opt/docker/`.

```
stack/
├── docker-compose.yml        ← all sixteen services, one project
├── .env.example              ← every credential and port (copy to .env)
├── searxng/settings.yml      ← live SearXNG config, secret_key driven by ${SEARXNG_SECRET}
├── lightrag/.env.example     ← LLM / embedding / storage settings for the graph-RAG backend
├── honcho/.env.example       ← model levels for the research-memory service
└── paperflow/Dockerfile      ← PaperFlow + the PaddleOCR toolchain
```

## Quick start

```bash
cd stack
cp .env.example .env
$EDITOR .env                 # fill in every REPLACE_ME
cp lightrag/.env.example lightrag/.env
cp honcho/.env.example   honcho/.env
docker compose up -d
docker compose ps
```

Two services are built from source and need their upstream trees in place first:

| Path | Needed by | How to obtain |
|---|---|---|
| `stack/honcho/` | `honcho-api`, `honcho-deriver` | clone the Honcho repository here (it provides `Dockerfile`, `docker/entrypoint.sh`, `database/init.sql`) |
| `stack/paperflow/` | `paperflow` | nothing — the shipped `Dockerfile` builds from the published PaperFlow image |

`lightrag` uses the published image `ghcr.io/hkuds/lightrag:latest`. The live host instead
builds from a local LightRAG checkout; to reproduce that exactly, replace the `image:` line
with the commented `build:` block in `docker-compose.yml`.

## Service map

Every service below is reachable on the host at `http://YOUR-HOST:<port>`.

| Service | Image | Port | Role | Consumed by the profiles through |
|---|---|---|---|---|
| `npm` | nginx-proxy-manager | 80, 443, 81 | Edge reverse proxy | — (front door) |
| `portainer` | portainer-ce | 9000 | Container management | terminal + `PORTAINER_API_KEY` |
| `siyuan` | b3log/siyuan | 6806 | Block-level notes | `siyuan` MCP server + plugin |
| `vikunja` | vikunja/vikunja:2.3.0 | 3456 | Task ledger, hypothesis trees | `vikunja` MCP server + plugin |
| `searxng` | searxng/searxng | 5050 | Federated metasearch | `searxng` MCP server |
| `searxng-redis` | redis:7-alpine | — | SearXNG rate-limit/limiter store | internal |
| `zimi` | epheterson/zimi | 8899 | Offline encyclopedia (ZIM archives) | `zimi` MCP server |
| `lightrag` | ghcr.io/hkuds/lightrag | 9621 | Graph-RAG over the literature lake | `lightrag-query` MCP server |
| `neo4j` | neo4j:5.20.0 | 7474, 7687 | Graph store for LightRAG | internal |
| `qdrant` | qdrant/qdrant | 6333, 6334 | Vector store for LightRAG | internal |
| `paperflow` | built locally | 8000 | PDF → Markdown with OCR | `ocr-and-documents` skill |
| `pocketbase` | muchobien/pocketbase | 8090 | Wiki ingestion queue | `wiki-pipeline` skill |
| `honcho-api` | built locally | 8008 | Cross-session research memory | `memory.provider: honcho` |
| `honcho-deriver` | built locally | — | Background memory derivation | internal |
| `honcho-database` | pgvector/pgvector:pg15 | 127.0.0.1:5433 | Honcho storage | internal |
| `honcho-redis` | redis:8.2 | 127.0.0.1:6379 | Honcho cache | internal |

### Not in this stack

| Dependency | Where it lives | Why it is out of scope |
|---|---|---|
| LM Studio inference server | another machine (`:1234`) | model weights and GPU live outside Docker; both profiles and Honcho point at it |
| `calibre-server` | systemd service on the host | the profiles' Calibre skills call it over HTTP at `:9876` |
| Zotero, Wolfram\|Alpha, Semantic Scholar, arXiv, Crossref | SaaS APIs | no container; reached through skills and MCP tools |

## Data layout

Bind mounts resolve to `${STACK_DATA_DIR:-./data}/<service>/…`; Honcho's Postgres and Redis
use named volumes. To reuse the live data instead of starting empty, point `STACK_DATA_DIR`
at the existing tree and map the paths accordingly:

| Live path | Stack path |
|---|---|
| `/opt/docker/siyuan` | `${STACK_DATA_DIR}/siyuan` |
| `/opt/docker/vikunja/{files,db}` | `${STACK_DATA_DIR}/vikunja/{files,db}` |
| `/opt/docker/searxng/{data,redis}` | `stack/searxng` (config) and `${STACK_DATA_DIR}/searxng/redis` |
| `/opt/docker/zimi/zims` | `${STACK_DATA_DIR}/zimi/zims` |
| `/opt/docker/lightrag/data/{rag_storage,inputs,neo4j,qdrant_data}` | `${STACK_DATA_DIR}/lightrag/…` |
| `/opt/docker/paperflow/data` | `${STACK_DATA_DIR}/paperflow` |
| `/opt/docker/pocketbase/{pb_data,pb_public}` | `${STACK_DATA_DIR}/pocketbase/…` |
| `/opt/docker/{portainer/data,npm/data,npm/letsencrypt}` | `${STACK_DATA_DIR}/{portainer,npm}/…` |
| Honcho volumes `honcho_pgdata`, `honcho_redis-data` | same names (named volumes) |

The live data is substantial — the LightRAG store alone is ~11 GB and the ZIM archive set
~1.3 GB — so a fresh install and a migration are very different operations.

## Validation

```bash
docker compose config -q          # syntax + variable interpolation
docker compose up --dry-run       # resolve the full plan without touching anything
```

## Findings on the live deployment

These are recorded because the AgentDesign document is an architecture audit, not only a
build recipe. **None of them is reproduced in this stack's committed files.**

1. **One password, three services.** The live host reuses a single password for SiYuan's
   access code, Neo4j's `NEO4J_AUTH` and ZIMI's manage password. Compromise of any one
   grants the other two. Here each is an independent `${…}` variable.
2. **Credentials sit in plaintext in compose files.** Vikunja's service secret, its mailer
   password, the SearXNG `secret_key` and the LightRAG keys are literals in the live
   `/opt/docker/**/docker-compose.yml` and `.env` files. This stack keeps them in an
   untracked `.env`; `searxng/settings.yml` is driven by `${SEARXNG_SECRET}`.
3. **The reverse proxy has no proxy hosts.** NPM listens on 80/443 but
   `/data/nginx/proxy_host/` is empty, so `http://YOUR-HOST/` serves the NPM default
   page and every service is reached by its own port. Adding proxy hosts would give the
   stack real names (e.g. `vikunja.`, `notes.`) instead of port numbers.
4. **Both Honcho and the profiles depend on a machine that is not this host.** All model
   levels (`DERIVER`, `DIALECTIC_LEVELS__*`, `EMBEDDING_MODEL_CONFIG`) point at LM Studio
   on another machine; nothing in the stack degrades gracefully when it is down.
5. **`paperflow` is a derived image.** It is the upstream image plus a system-package and
   PaddleOCR layer; that layer is not pinned, so builds drift over time.

## Relationship to the rest of AgentDesign

`docker-compose.yml` here is the executable form of the service plane documented in
`../agent_design.tex` (Section "Tool Stack and Service Plane") and of the MCP bridge in
Table 3 there: each MCP server listed in the profiles' `config.yaml` resolves to one of
these containers, a host-level service, or a SaaS API.