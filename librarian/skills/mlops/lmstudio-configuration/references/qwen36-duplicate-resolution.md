# Qwen3.6-27B Duplicate Model Resolution (2026-07-30)

## Problem

LM Studio registered the same GGUF file (`Qwen3.6-27B-Q4_K_M.gguf`, ~16.5 GB) under two model IDs simultaneously: `qwen/qwen3.8-27b` (hub, namespaced) and `qwen3.8-27b` (auto-discovered, bare). This caused two independent `llama-server` processes loading the identical file, consuming ~33 GB GPU memory.

## Root Cause

| Registration | Source | Path |
|---|---|---|
| `qwen/qwen3.8-27b` | Hub metadata (namespaced) | `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/hub/models/qwen/qwen3.8-27b/` |
| `qwen3.8-27b` | Auto-discovered user model | `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/lmstudio-community/Qwen3.6-27B-GGUF/` |

The hub directory contained only metadata (`manifest.json`, `model.yaml`) — no actual GGUF file. The GGUF was downloaded to the user models directory by LM Studio's hub downloader, and LM Studio's auto-indexer also discovered it there independently.

## Process Discovery

Two llama-server processes with the same model path but different ports and context sizes:

```
PID 2564561 — port 44595 — ctx-size 8192   (bare `qwen3.8-27b`)
PID 2589160 — port 44641 — ctx-size 94000  (namespaced `qwen/qwen3.8-27b`)
```

Both loaded: `Qwen3.6-27B-Q4_K_M.gguf`

## Resolution Steps

### 1. Diagnose duplicates

```bash
# Check running processes
ps aux | grep 'llama-server.*Qwen3.6' | grep -v grep

# Check model index cache
python3 -c "
import json
with open('/home/YOUR-USER/.var/app/ai.lmstudio.lm-studio/.lmstudio/.internal/model-index-cache.json') as f:
    data = json.load(f)
models = data.get('models', []) if isinstance(data, dict) else data
for m in models:
    if 'qwen3.6' in str(m.get('indexedModelIdentifier', '')).lower():
        print(f\"ID: {m.get('indexedModelIdentifier')}\")
        print(f\"  Source: {m.get('sourceDirectoryType')}\")
        print(f\"  Path: {m.get('containingDirAbsolutePath')}\")
"

# Check API
curl -s http://localhost:1234/v1/models | python3 -c "
import json, sys
for m in json.load(sys.stdin).get('data', []):
    if 'qwen' in m['id'].lower(): print(m['id'])
"
```

### 2. Move GGUF out of auto-discovered path

The GGUF was at a location that produced a bare-name ID. Moved it to a path organized under `qwen/`:

```bash
# Flatpak internal path
mkdir -p /home/YOUR-USER/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/qwen/qwen3.8-27b
mv /home/YOUR-USER/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/lmstudio-community/Qwen3.6-27B-GGUF/*.gguf \
   /home/YOUR-USER/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/qwen/qwen3.8-27b/
rmdir /home/YOUR-USER/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/lmstudio-community/Qwen3.6-27B-GGUF/
```

Note: Even after restructuring, the auto-discovered model ID is DERIVED FROM GGUF METADATA (internal model name), not the directory path. So the API still returned `qwen3.8-27b`, not a path-based identifier.

### 3. Remove hub metadata

```bash
rm -rf /home/YOUR-USER/.var/app/ai.lmstudio.lm-studio/.lmstudio/hub/models/qwen3.8-27b
```

This removes the namespaced `qwen3.8-27b` ID.

### 4. Clear model index cache

```bash
python3 -c "
import json
from pathlib import Path
cache = Path('/home/YOUR-USER/.var/app/ai.lmstudio.lm-studio/.lmstudio/.internal/model-index-cache.json')
data = json.loads(cache.read_text())
if isinstance(data, dict):
    models = data.get('models', [])
    data['models'] = [m for m in models if 'qwen3.6' not in str(m.get('indexedModelIdentifier', '')).lower()]
elif isinstance(data, list):
    data = [m for m in data if 'qwen3.6' not in str(m.get('indexedModelIdentifier', '')).lower()]
cache.write_text(json.dumps(data, indent=2))
"
```

### 5. Update all Hermes profiles

```bash
# Current profile (math)
hermes config set model.default qwen3.8-27b
hermes config set fallback_providers.0.model qwen3.8-27b

# Other profiles
hermes config set model.default qwen3.8-27b --profile advisor
hermes config set model.default qwen3.8-27b --profile coder
```

### 6. Update Honcho .env (remote Docker host)

```bash
ssh -i /home/YOUR-USER/.hermes/profiles/math/home/.ssh/id_ed25519 YOUR-USER@YOUR-HOST \
  "sed -i 's|qwen3.8-27b|qwen3.8-27b|g' /opt/docker/honcho/.env"
```

Note: `/opt/docker/honcho/.env` is owned by `YOUR-USER:YOUR-USER` with permissions `-rw-rw-r--` — no sudo needed.

### 7. Update cron job model pin

```bash
hermes cron edit bef55ae4c734 --model qwen3.8-27b --provider lmstudio
```

### 8. Restart Honcho

```bash
ssh -i /home/YOUR-USER/.hermes/profiles/math/home/.ssh/id_ed25519 YOUR-USER@YOUR-HOST \
  "docker restart honcho-api-1 honcho-deriver-1"
```

### 9. Verify

```bash
# Trigger model load
curl -s http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.8-27b","messages":[{"role":"user","content":"ok"}],"max_tokens":5}'

# Check only one process
ps aux | grep 'llama-server.*Qwen3.6' | grep -v grep | wc -l
# → 1
```

## Key Takeaways

- **Hub metadata contains NO GGUF files** — only JSON/YAML config files. Safe to delete.
- **Auto-discovered model ID comes from GGUF metadata**, not the filesystem path.
- **`hermes config set` must be used** to update Hermes config (file patching is blocked).
- **Cross-profile updates** use `--profile <name>` flag.
- **Cron jobs pin their own model snapshot** and must be updated separately via `hermes cron edit`.
- **Honcho .env is world-readable** and owned by the user — no sudo for editing.
- **Flatpak paths** are under `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/`, but hub manifests reference `~/.lmstudio/` (the bind-mount view inside the sandbox).
