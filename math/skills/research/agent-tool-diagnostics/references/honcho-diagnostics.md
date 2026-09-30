# Honcho Tool Diagnostics

## Symptom
All Honcho tools (`honcho_conclude`, `honcho_profile`, etc.) return `"Failed to save conclusion"`, `"An unexpected error occurred"`, or `"No profile facts available yet"` despite the server being reachable.

## Common Symptoms

| Symptom | Likely Root Cause |
|---------|------------------|
| All Honcho tools return "Failed to save conclusion" or "An unexpected error occurred" | SDK masks HTTP errors OR server-side LLM failure |
| API server won't start / healthcheck loops | Database vector dimension mismatch (see Category 5) |
| HTTP 500 on conclusion creation, non-LLM endpoints work | LLM/embedding misconfiguration (see Category 2) |
| Active config not reflected in container | `env_file` Docker Compose syntax issue (see Category 5) |

## Root Cause Categories

### Category 1: SDK masks HTTP errors behind generic messages
The Honcho SDK catches all HTTP errors and re-raises them as `honcho.http.exceptions.ServerError: An unexpected error occurred` — **regardless of the actual HTTP status code**. A 404, 500, or 422 all look identical to the plugin.

**Diagnostic:** Patch the SDK's HTTP client to expose the real URL and status:
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

### Category 2: Server-side LLM misconfiguration (HTTP 500)
**Most common cause for conclusion creation failures.** The server returns HTTP 500 on `POST /v3/workspaces/{id}/conclusions` when the LLM provider is misconfigured. Non-LLM operations (sessions, peer reads, workspace listing) work fine.

**Check:** On the Docker host, verify `.env`:
```bash
docker logs honcho-api-1 --tail 30 2>&1 | grep -i "error\|401\|key\|embed"
```

**Known failure modes:**

| Failure | Symptom in logs | Fix |
|---------|----------------|------|
| Placeholder API key | `Incorrect API key provided: your-api*****here` | `LLM_OPENAI_API_KEY=sk-local-dummy-key` |
| Missing `http://` scheme in base URL | HTTP client silently fails, generic 500 | `EMBEDDING_MODEL_CONFIG__OVERRIDES__BASE_URL=http://YOUR-HOST:1234/v1` |
| Embedding dimension mismatch | pgvector insert failure (silent) | `EMBEDDING_VECTOR_DIMENSIONS=768` (for nomic-embed-text-v1.5) |
| Missing API_KEY_ENV for embedding | Embedding hits `api.openai.com` not local LLM | `EMBEDDING_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=LLM_OPENAI_API_KEY` |

**Critical: OpenAI SDK API key format validation.** Even when pointed at a local LLM (LM Studio, Ollama), the OpenAI Python SDK validates that the API key starts with `sk-` before sending. LM Studio ignores the key value, but the SDK won't send the request without the `sk-` prefix. Always use `sk-local-dummy-key` or similar.

**Multiple modules need LLM config.** Setting only `DERIVER_MODEL_CONFIG__OVERRIDES__BASE_URL` is insufficient. Each module that uses LLM needs its own override:
- `DERIVER_MODEL_CONFIG__OVERRIDES__BASE_URL` — deriver (background reasoning)
- `DIALECTIC_LEVELS__*__MODEL_CONFIG__OVERRIDES__BASE_URL` — dialectic chat (all levels: minimal/low/medium/high/max)
- `EMBEDDING_MODEL_CONFIG__OVERRIDES__BASE_URL` — embeddings
- `SUMMARY_MODEL_CONFIG__OVERRIDES__BASE_URL` — message summarization
- `DREAM_DEDUCTION_MODEL_CONFIG__OVERRIDES__BASE_URL` — dream engine

Each also needs `__TRANSPORT=openai` and `__MODEL=model-name`.

**Workaround if no LLM available:** Disable LLM-dependent features in `.env`:
```bash
EMBED_MESSAGES=false
DERIVER_ENABLED=false
DREAM_ENABLED=false
SUMMARY_ENABLED=false
```
Then restart: `docker compose restart api deriver`

### Category 5: Docker Compose env_file syntax failure (env vars silently not loaded)

The expanded Docker Compose `env_file` syntax (`path: .env, required: false`) can silently fail to load env vars on some Docker Compose versions (including v5). The container starts without your `.env` configuration and uses whatever defaults are baked into the image (e.g., `LLM_OPENAI_API_KEY=your-api-key-here`).

**Symptom:** You inspect the container's env and see template defaults, not your values:
```bash
docker inspect honcho-api-1 | python3 -c "import json,sys; env=json.load(sys.stdin)[0]['Config']['Env']; [print(e) for e in env if 'LLM' in e or 'API_KEY' in e]"
# Shows: LLM_OPENAI_API_KEY=your-api-key-here   ← template default, NOT your .env value
```

**Fix:** Change the `env_file` directive in `docker-compose.yml` from the expanded syntax:
```yaml
    env_file:
      - path: .env
        required: false
```
to the simplified classic syntax:
```yaml
    env_file: .env
```
Then recreate the container: `docker compose up -d api --force-recreate`

**Check:** Verify env vars are loaded post-fix:
```bash
docker inspect honcho-api-1 | python3 -c "import json,sys; env=json.load(sys.stdin)[0]['Config']['Env']; [print(e) for e in sorted(env) if 'LLM' in e or 'EMBED' in e or 'DIALECT' in e or 'DERIVER' in e]"
```

### Category 6: Database vector dimension mismatch (startup failure)

When `EMBEDDING_VECTOR_DIMENSIONS` is changed after the initial deployment, the API server fails at startup because the pgvector columns were created with the original dimension:

```
StartupValidationError: public.documents.embedding dim (1536) does not match EMBEDDING_VECTOR_DIMENSIONS (768).
```

**Fix:** Run the migration script inside the Docker container. Because the API entrypoint (`entrypoint.sh`) always starts the FastAPI server, you must override the entrypoint:

```bash
cd /opt/docker/honcho
docker compose --env-file .env run --entrypoint /app/.venv/bin/python --rm api scripts/configure_embeddings.py --yes
```

Key details:
- `--env-file .env` goes **before** the `run` verb (not after: there is no `--env-file` flag for `docker compose run`)
- `--entrypoint /app/.venv/bin/python` overrides the entrypoint script so the script runs instead of `fastapi run`
- The script ALTERs pgvector columns with `USING NULL` — only works if no non-null embeddings exist yet

**Alternative:** If the table is already populated with non-null embeddings, you must re-embed into a fresh deployment and cut over, or restore the original `EMBEDDING_VECTOR_DIMENSIONS`.

### Category 3: Workspace ID mismatch
The plugin resolves `workspace_id` from `honcho.json`. If the workspace doesn't exist on the server, operations fail silently.

**Resolution chain** (first match wins):
1. Host block's `workspace` field: `hosts.hermes_math.workspace`
2. Root `workspace` field
3. Falls back to resolved host key (e.g., `hermes_math`)

**Check:** List server workspaces and compare:
```bash
curl -s -X POST "http://BASE_URL/v3/workspaces/list" -H "Content-Type: application/json" -d '{}'
```

### Category 4: Local deployment — no API key needed
For self-hosted Honcho on loopback/LAN IPs, the SDK auto-detects and injects `"local"` as a placeholder API key. **Do not set `HONCHO_API_KEY` for local deployments** — it's unnecessary and can confuse the resolver.

## Diagnostic Methodology (in order)

| Step | Command | What it proves |
|------|---------|----------------|
| 1 | `curl http://BASE_URL/health` | Server alive |
| 2 | `curl -s BASE_URL/openapi.json \| python3 -c "..."` | Extract actual endpoints |
| 3 | Reproduce SDK call via raw curl (same URL, same body) | Isolate SDK vs server |
| 4 | `docker logs honcho-api-1 --tail 30` (on Docker host) | See actual server-side error |
| 5 | Check Docker host `.env` for LLM config | Server-side LLM failure |

## SSH Setup for Remote Docker Debugging

When Honcho runs on a separate host and you need to debug beyond what's visible from the local machine:

### Generate and Deploy Key

```bash
# Generate key on the agent machine (one-time)
mkdir -p ~/.ssh && ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
# → share this with the user to add to ~/.ssh/authorized_keys on the Docker host
```

The user runs on the Docker host:
```bash
echo "ssh-ed25519 <PUBLIC_KEY>" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
```

### Connect

**Critical:** Hermes profiles may resolve `~` to the profile's home dir (e.g., `/home/YOUR-USER/.hermes/profiles/math/home/.ssh/`), but the generated key file is there. Specify the key explicitly:

```bash
ssh -i /home/YOUR-USER/.hermes/profiles/math/home/.ssh/id_ed25519 \
    -o StrictHostKeyChecking=no YOUR-USER@YOUR-HOST "command"
```

### Common Remote Docker Commands

```bash
# Check env vars actually loaded in the container
docker inspect honcho-api-1 | python3 -c "import json,sys; env=json.load(sys.stdin)[0]['Config']['Env']; [print(e) for e in sorted(env) if 'LLM' in e or 'EMBED' in e or 'DIALECT' in e or 'DERIVER' in e]"

# See server-side errors (the actual exception, not the masked response)
docker logs honcho-api-1 --tail 30 2>&1 | grep -i "error\|401\|trace\|embed\|warn"

# Run a migration script inside the container (overriding entrypoint)
cd /opt/docker/honcho
docker compose --env-file .env run --entrypoint /app/.venv/bin/python --rm api scripts/configure_embeddings.py --yes

# Full container restart after .env changes
docker compose up -d api --force-recreate
```

### Pitfall: SSH Key Path

The key file is at `/home/YOUR-USER/.hermes/profiles/math/home/.ssh/id_ed25519`, NOT at `/home/YOUR-USER/.ssh/id_ed25519`. Hermes profiles use a profile-isolated home directory, but `ssh` looks in the real `~/.ssh/` by default. Always use the `-i` flag to point to the correct path. Save the path to memory as a durable fact.\

## Entrypoint Override Pattern

When you need to run a one-off script inside a Docker container that has a custom entrypoint (like Honcho's `entrypoint.sh` which always starts the API server), you must:

1. **Override the entrypoint:** `--entrypoint /app/.venv/bin/python`
2. **Pass the env file at the compose level:** `docker compose --env-file .env run` (not `docker compose run --env-file .env`, which doesn't exist on Compose v5)
3. **Pass the script as the command:** `scripts/configure_embeddings.py --yes`

Full command:
```bash
cd /opt/docker/honcho && \
docker compose --env-file .env run \
    --entrypoint /app/.venv/bin/python \
    --rm api \
    scripts/configure_embeddings.py --yes
```

This pattern is necessary because Docker Compose ignores the `CMD` from the Dockerfile when a custom `entrypoint` is active.

## Quick Fix Checklist (new deployment)

When setting up Honcho with a local LLM (LM Studio on `YOUR-HOST:1234`):

```ini
# 1. API key — must start with sk- for SDK format validation
LLM_OPENAI_API_KEY=sk-local-dummy-key

# 2. Deriver (background reasoning)
DERIVER_MODEL_CONFIG__TRANSPORT=openai
DERIVER_MODEL_CONFIG__MODEL=qwen3.8-27b
DERIVER_MODEL_CONFIG__OVERRIDES__BASE_URL=http://YOUR-HOST:1234/v1

# 3. Embedding — nomic-embed-text-v1.5 = 768 dimensions
EMBED_MESSAGES=true
EMBEDDING_MODEL_CONFIG__TRANSPORT=openai
EMBEDDING_MODEL_CONFIG__MODEL=text-embedding-nomic-embed-text-v1.5
EMBEDDING_MODEL_CONFIG__OVERRIDES__BASE_URL=http://YOUR-HOST:1234/v1
EMBEDDING_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=LLM_OPENAI_API_KEY
EMBEDDING_VECTOR_DIMENSIONS=768

# 4. Dialectic (all reasoning levels)
DIALECTIC_LEVELS__minimal__MODEL_CONFIG__TRANSPORT=openai
DIALECTIC_LEVELS__minimal__MODEL_CONFIG__MODEL=qwen3.8-27b
DIALECTIC_LEVELS__minimal__MODEL_CONFIG__OVERRIDES__BASE_URL=http://YOUR-HOST:1234/v1
# ... repeat for low, medium, high, max levels
```

## Honcho Config Structure (`$HERMES_HOME/honcho.json`)

```json
{
  "baseUrl": "http://YOUR-HOST:8008/",
  "hosts": {
    "hermes_math": {
      "workspace": "hermes",
      "aiPeer": "hermes-math",
      "enabled": true
    }
  }
}
```

Key fields:
- `baseUrl` — self-hosted server URL (triggers local API key bypass)
- `hosts.<host_key>` — per-profile isolation; host key = `hermes_<profile_name>`
- `workspace` — which server workspace this host uses (default: host key itself)
- `aiPeer` — the AI peer ID on the server

## Notes
- Honcho profile card accumulates **passively** over many turns — not written directly by the agent
- Conclusions require explicit `honcho_conclude` calls — they don't auto-populate
- The `provider: honcho` line in `config.yaml` only selects Honcho as the memory backend; it does NOT configure credentials
- SDK package name: `honcho` (not `honcho-ai`), check with `pip show honcho`
- After changing `.env`, always run `docker compose restart api` (and `deriver` if applicable)
