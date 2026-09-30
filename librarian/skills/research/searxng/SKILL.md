---
name: searxng
description: Privacy-respecting metasearch using your local SearXNG instance. Search the web, images, news, and more without external API dependencies.
author: Avinash Venkatswamy
version: 1.0.1
homepage: https://searxng.org
triggers:
  - "search for"
  - "search web"
  - "find information"
  - "look up"
metadata: {"clawdbot":{"emoji":"🔍","requires":{"bins":["python3"]},"config":{"env":{"SEARXNG_URL":{"description":"SearXNG instance URL","default":"http://YOUR-HOST:5050/","required":true}}}}}
---
# SearXNG Search

Search the web using your local SearXNG instance - a privacy-respecting metasearch engine.

## Commands

### Web Search

```bash
uv run {baseDir}/scripts/searxng.py search "query"              # Top 10 results
uv run {baseDir}/scripts/searxng.py search "query" -n 20        # Top 20 results
uv run {baseDir}/scripts/searxng.py search "query" --format json # JSON output
```

### Category Search

```bash
uv run {baseDir}/scripts/searxng.py search "query" --category images
uv run {baseDir}/scripts/searxng.py search "query" --category news
uv run {baseDir}/scripts/searxng.py search "query" --category videos
```

### Advanced Options

```bash
uv run {baseDir}/scripts/searxng.py search "query" --language en
uv run {baseDir}/scripts/searxng.py search "query" --time-range day
```

## Configuration

**Required:** Set the `SEARXNG_URL` environment variable to your SearXNG instance:

```bash
export SEARXNG_URL=http://YOUR-HOST:5050/
```

Or configure in your Clawdbot config:

```json
{
  "env": {
    "SEARXNG_URL": "http://YOUR-HOST:5050/"
  }
}
```

Default (if not set): http://YOUR-HOST:5050/

## MCP Server (Hermes native)

The Hermes MCP entry `mcp_servers.searxng` must point at
`scripts/searxng_mcp_server.py` (a real MCP stdio server), NOT at
`searxng.py` (argparse CLI — that fails the MCP handshake with
"Connection closed"). Verify with:

```bash
hermes mcp test searxng   # expect: ✓ Connected, Tools discovered: 1 (search)
```

The MCP tool registers as `mcp_searxng_search` (query, limit, category,
language, time_range).

## Engine suspensions & the `general` category (fixed 2026-08-31)

Instance at `YOUR-HOST:5050`: fixed on 2026-08-31 via Docker host (Portainer
`YOUR-HOST:9000`, endpoint id 3, `X-API-Key` header):

- `search.suspended_times` reduced from 86400s/1296000s to 300s/3600s — engines
  no longer stay banned for days; they retry within 5 minutes.
- Enabled lenient general engines: **mojeek**, **qwant**, **presearch**,
  **mwmbl**, **stract** (were `disabled: true`).
- `outgoing.request_timeout` raised 3.0 → 8.0s (mwmbl/presearch were timing
  out at 5s; with 8s they answer reliably).
- Container restarted; old suspensions cleared. Verified 2026-08-31: 4/4
  general queries returned results (mwmbl is the workhorse; brave adds more
  when not rate-limited).

Remaining IP-level blocks (external, not fixable from config): duckduckgo
(`CAPTCHA`/`access denied`), startpage (`CAPTCHA`), qwant (`access denied`).
They retry every 300s and only add `unresponsive_engines` noise.

If `general` returns zero results again (e.g. after another engine block wave):

1. Check `unresponsive_engines` in the JSON response for which engines fail.
2. Retry with a category that has healthy engines: `it`, `news`, `images`,
   `science`.
3. For general web queries, fall back to the built-in `web_search` tool
   (firecrawl backend) — it is not affected by these engine blocks.
4. If suspensions are stuck long-term again, check `search.suspended_times`
   on the host settings.yml (`/opt/docker/searxng/data/settings.yml`) and
   restart the searxng container via Portainer (creds: `PORTAINER_URL` /
   `PORTAINER_API_KEY` / `PORTAINER_ENDPOINT_ID` in the math profile `.env`;
   send the key as `X-API-Key` header).

## Features

- 🔒 Privacy-focused (uses your local instance)
- 🌐 Multi-engine aggregation
- 📰 Multiple search categories
- 🎨 Rich formatted output
- 🚀 Fast JSON mode for programmatic use

## API

Uses your local SearXNG JSON API endpoint (no authentication required by default).
