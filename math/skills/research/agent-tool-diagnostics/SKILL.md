---
name: agent-tool-diagnostics
description: "Diagnose why an agent tool (MCP server, plugin, or custom tool) appears available in the runtime but fails silently on invocation."
version: 1.0.0
author: YOUR-USER
tags: [hermes, troubleshooting, mcp, connectivity, diagnostics]
---

# Agent Tool Diagnostics

When an agent tool appears available in the runtime (the tool shows up in `hermes tools list` or is callable via its function name) but fails silently on invocation — no error message, just a generic failure — this skill provides a systematic diagnostic methodology.

## Triggers

Use this when:
- A tool returns an empty result without explanation (`honcho_conclude` failed 3 times silently)
- `hermes tools list` shows the toolset as enabled but invocations produce no useful output
- The tool seems to "exist" in the runtime surface but produces only null/empty responses
- Connectivity appears OK from the outside (the server responds) but the agent can't interact with it

## Diagnostic Methodology

### Step 1: Direct Server Probe

Before assuming it's a runtime/tool issue, verify the underlying server is actually responding on its configured base URL.

```bash
curl -s http://<BASE_URL>/ | head -50
# If JSON "Not Found" or similar → server IS up but endpoint mismatch
# If connection refused/timeout → server is down; report to user
```

**Key insight:** A server returning `{"detail":"Not Found"}` for `/` means it's alive — the problem is endpoint shape, not connectivity.

### Step 2: Discover Actual API Shape

If the server responds, inspect its OpenAPI spec to see what endpoints actually exist:

```bash
curl -s http://<BASE_URL>/openapi.json | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'{m.upper()} {p}') for p,ops in d.get('paths',{}).items() for m in ops]"
# Or for Swagger UI:
curl -s http://<BASE_URL>/docs
```

**Compare:** Expected endpoint paths (from tool definitions) vs actual endpoints (from server spec). Mismatches here are the most common root cause of silent failures.

### Step 3: Test with Raw HTTP

If endpoints differ from expectations, test directly via curl using correct paths and methods:

```bash
curl -s http://<BASE_URL>/v3/workspaces -X POST -H "Content-Type: application/json" -d '{"id":"test"}'
```

If the raw HTTP call succeeds but the tool still fails → the issue is in how Hermes's runtime exposes the tool (tool schema, function mapping, or provider configuration), not server-side.

### Step 4: Check Tool Registration vs Server API

If steps 1-3 reveal a mismatch between what the tool expects and what the server provides:
- Report the discrepancy to the user with both sets of endpoints
- Do NOT try to "work around" by inventing endpoint paths that don't exist on the server
- Suggest the user update the tool's configuration or the server's API if possible

## Pitfalls

| Pitfall | Why It Bites |
|---------|-------------|
| Assuming silent failure = server down | Server may be alive but endpoints mismatched — always curl first |
| Inventing endpoint paths that match expected tool schemas | If `honcho_conclude` fails, the actual path is `/v3/workspaces/{workspace_id}/conclusions`, not `/api/conclusions`. Don't guess. |
| Capturing environment-dependent failures as durable rules | Base URLs, tokens, and ports change with user reconfiguration. Capture the diagnostic methodology, not the specific values. |
| Assuming a patched tool script is live | MCP adapter servers import the tool module ONCE at startup; a file edit does not hot-reload. Verify the fix by running the tool CLI directly (fresh process), then kill the stale adapter process (`pgrep -f mcp_cli_adapter.py` + check `/proc/<pid>/environ` for `TOOL_SERVER_NAME=...`) — the watchdog respawns it with the new code. |
| Endpoint probes that 404 burn the full timeout | A handler that tries dead endpoints wastes DEFAULT_TIMEOUT per miss (plus each miss also tries the slow ALT/DDNS URL). Probe the healthiest endpoint first (`/health`), never last. |
| Raw `/dev/tcp` port probes report live services as closed | `bash -c "exec 3<>/dev/tcp/host:port"` returned false negatives for ports that curl reached fine in the same session — treat it as unreliable here; probe with `curl -s -o /dev/null -w '%{http_code}' <url>` and read codes, not reachability. |
| Reading an HTTP status as 'down' | 3xx/401/404 on a probed endpoint means the SERVER IS UP (redirect, auth-gated, or path-mismatch) — only connection failure / `000` / timeout means down. Classify each probed service in exactly one of: up · up-auth · up-pathcheck · down. |
| Dead script path after project merge/rename | MCP config references a Python script in a folder that was deleted during repo consolidation (e.g. a tool script inside a development worktree that was later merged into the main package). The server exits immediately with "Connection closed" because the interpreter can't find the entry point. Diagnose by checking `ls <script_path>` from config — if missing, either restore from archive or disable the MCP entry (`enabled: false`) |
| Config write protection blocks automated fixes | Profile config files (`~/.hermes/profiles/<profile>/config.yaml`) refuse agent writes via `patch`/`write_file`. The fix requires user action: edit manually or use `hermes config set <key> <value>` from the terminal. Report the exact line and change needed; do not retry writing |

## Verification Steps

After diagnosing:
1. Confirm server responds on base URL (`curl` to root or health endpoint)
2. Confirm expected endpoints exist in `/openapi.json` (or equivalent spec)
3. If mismatch found → report both sets of paths clearly with a table comparison
4. If no mismatch but tool still fails → the issue is in Hermes's tool registration, not server-side

## When to Escalate

- Server returns `Connection refused` or `Timeout` → server may be down; ask user to check service status
- OpenAPI spec exists but has zero paths → server crashed mid-startup or misconfigured deployment
- Multiple tools fail simultaneously → likely a shared infrastructure issue (network, proxy, port) rather than individual tool bugs
- **Honcho tools specifically fail** → see `references/honcho-diagnostics.md` (SDK error masking, server-side LLM failures, workspace mismatch, local bypass)

## Critical: SDK Error Masking

The Honcho SDK (and potentially other plugins) catches ALL HTTP errors and re-raises them as a generic `ServerError: An unexpected error occurred` — regardless of actual status code. A 404, 500, or 422 all look identical.

**Always patch the SDK HTTP client** to see the real URL and error before concluding anything:
```python
import honcho.http.client as hc
orig = hc.HonchoHTTPClient.request
def patched(self, *a, **k):
    try: return orig(self, *a, **k)
    except Exception as e:
        print(f'URL: {a[0] if a else k.get("url","?")}, Error: {e}')
        raise
hc.HonchoHTTPClient.request = patched
```

**Most common Honcho failure:** Server-side LLM misconfiguration. The `.env` on the Docker host has a placeholder `LLM_OPENAI_API_KEY`, causing HTTP 500 on conclusion creation. Non-LLM endpoints (sessions, peers) work fine. Fix: set a real key or point to a local LLM in `.env`.
