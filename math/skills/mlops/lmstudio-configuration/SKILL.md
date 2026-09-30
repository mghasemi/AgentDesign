---
name: lmstudio-configuration
description: Troubleshoot LM Studio model duplicates and Flatpak paths.
version: 1.1.0
author: Orchestra Research
license: MIT
platforms: [linux]
references:
  - references/qwen36-duplicate-resolution.md
metadata:
  hermes:
    tags: [lm-studio, flatpak, gguf, model-registration, duplicate-models, llama-server]
---

# LM Studio Configuration

Use this skill when working with LM Studio — troubleshooting duplicate model registration, managing the Flatpak sandbox filesystem, understanding hub vs auto-discovered models, or fixing two llama-server processes for the same GGUF.

## Flatpak Sandbox Filesystem

LM Studio runs as a Flatpak. The actual filesystem path inside the sandbox differs from what LM Studio's UI and manifest report:

| Path reported by LM Studio | Actual Flatpak path |
|---|---|
| `~/.lmstudio/` | `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/` |
| `~/.lmstudio/models/` | `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/` |
| `~/.lmstudio/hub/` | `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/hub/` |

LM Studio creates a bind mount so that inside the Flatpak sandbox the path `~/.lmstudio/` resolves correctly, but from the host (outside the Flatpak) you must use the full `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/` path.

## Model Registration Architecture

LM Studio registers GGUF files in **two independent ways**, causing duplicate model IDs:

### 1. Hub Metadata (`hub/models/`)

When you download a model via the Hub (the "Download Model" button in LM Studio):
- Metadata is stored at `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/hub/models/<org>/<model>/`
- Contains `manifest.json` (file path + download key) and `model.yaml` (config, chat template)
- The GGUF file itself is downloaded to `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/<org>/<repo>/`
- **The hub directory contains ONLY metadata — NO actual GGUF files**
- Registered ID: Namespaced (e.g. `qwen3.8-27b`)

### 2. User Auto-Discovery (`models/`)

LM Studio **auto-scans** all subdirectories of `~/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/` for GGUF files:
- Any `.gguf` file found in any subdirectory is registered as a model
- The model ID is derived from the GGUF's internal metadata (the model name in the file header), NOT from the directory path
- Registered ID: Bare (e.g. `qwen3.8-27b`), derived from GGUF metadata
- This auto-discovery cannot be disabled through settings

### The Duplicate Problem

When a model is downloaded via the Hub:
1. Hub metadata registers it as `org/model` (namespaced)
2. Auto-discovery finds the same GGUF in `models/` and registers it as `modelname` (bare)
3. LM Studio starts **two separate `llama-server` processes** loading the same ~16GB file
4. GPU memory is doubled (~33GB for one model)

## Diagnosing Duplicate Registrations

### Check running llama-server processes

```bash
ps aux | grep 'llama-server' | grep -v grep
```

Two processes with the same `--model` path means duplicates.

### Check model index cache

```bash
python3 -c "
import json
from pathlib import Path
cache = Path('~/.var/app/ai.lmstudio.lm-studio/.lmstudio/.internal/model-index-cache.json').expanduser()
data = json.loads(cache.read_text())
models = data.get('models', []) if isinstance(data, dict) else data
for m in models:
    iid = m.get('indexedModelIdentifier', '?')
    src = m.get('sourceDirectoryType', '?')
    pth = m.get('containingDirAbsolutePath', '?')
    if 'qwen' in iid.lower():
        print(f'ID: {iid}')
        print(f'  Source: {src}')
        print(f'  Path: {pth}')
        print()
"
```

### Check LM Studio API

```bash
curl -s http://localhost:1234/v1/models | python3 -m json.tool | grep -i '"id"'
```

## Fix: Remove Duplicate Registration

### Step 1: Kill duplicate llama-server processes

```bash
# Kill specific PID
kill <PID>

# Or kill all for the model
pkill -f 'llama-server.*Qwen3.6'
```

### Step 2: Remove one registration source

**Option A: Remove hub metadata** (removes namespaced ID)

```bash
rm -rf ~/.var/app/ai.lmstudio.lm-studio/.lmstudio/hub/models/<org>/<model>/
```

After deletion, the auto-discovered entry in `models/` remains the only registration. Update downstream configs to use the bare model ID.

**Option B: Restructure user models directory** (to prevent auto-discovery as bare name)

```bash
rm ~/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/<org>/<old-repo>/  # empty after moving GGUF
mv ~/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/<org>/<old-repo>/ \
   ~/.var/app/ai.lmstudio.lm-studio/.lmstudio/models/<new-org>/<new-model>/
```

Note: The auto-discovered model ID is ALWAYS derived from GGUF metadata (not the directory path), so restructuring alone may not change the API-reported ID.

### Step 3: Clear model index cache

```bash
python3 -c "
import json
from pathlib import Path
cache = Path('~/.var/app/ai.lmstudio.lm-studio/.lmstudio/.internal/model-index-cache.json').expanduser()
data = json.loads(cache.read_text())
if isinstance(data, dict):
    models = data.get('models', [])
    data['models'] = [m for m in models if '<target-model-name>' not in str(m.get('indexedModelIdentifier', '')).lower()]
elif isinstance(data, list):
    data = [m for m in data if '<target-model-name>' not in str(m.get('indexedModelIdentifier', '')).lower()]
cache.write_text(json.dumps(data, indent=2))
"
```

## Update downstream configs

After removing one registration, update all services that reference the old model ID:

| Config | How to update |
|--------|---------------|
| Hermes config.yaml (current profile) | `hermes config set model.default <new-id>` |
| Hermes fallback (current profile) | `hermes config set fallback_providers.0.model <new-id>` |
| Hermes (other profiles) | `hermes config set model.default <new-id> --profile <name>` — repeat for `advisor`, `coder`, and any other active profiles |
| Honcho .env | SSH to host, `sed -i 's|old-id|new-id|g' /opt/docker/honcho/.env` (file is world-readable, owned by YOUR-USER — no sudo needed) |

### Step 5: Update pinned model on cron jobs

When you change the default model, cron jobs that have a `model_snapshot` pinned to the old ID will fail closed on their next run. Update them with:

```bash
hermes cron edit <job-id> --model <new-id> --provider <provider>
```

### Step 6: Restart affected services

```bash
# Honcho
docker restart honcho-api-1 honcho-deriver-1
```

## Verification

Check that only one llama-server process runs after making a request:

```bash
# Trigger model load
curl -s http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model-id>","messages":[{"role":"user","content":"ok"}],"max_tokens":5}'

# Verify single process
ps aux | grep 'llama-server' | grep -v grep | wc -l
# Should be 1
```

## Pitfalls

- **`~` expansion in SSH commands**: When SSHing to the remote host, `~` does NOT expand to the user's home directory if there's a tilde in the path. Always use absolute paths.
- **Sudo passwords with special characters**: When using `sudo -S`, special characters (`$`, `#`, `@`) in the password may be interpreted by the shell. Use single-quoting and escaping strategically.
- **Hub metadata deletion is safe**: The hub directory has NO GGUF files — only `manifest.json` and `model.yaml`. Deleting it does not delete the actual model.
- **Model ID derived from GGUF metadata**: Even if you move the file to a namespaced path, LM Studio's auto-discovery derives the ID from the GGUF file's internal model name (not the directory). To get a specific ID, use hub metadata.
- **Model index cache is ephemeral**: LM Studio regenerates it from filesystem scan. Removing cache entries alone is not permanent — the source (hub metadata or file location) must also be addressed.
- **Qwen3 thinking-mode GGUFs + Hermes stale watchdog** (2026-09-01, math profile): Qwen3-family GGUFs (e.g. `Qwen3.8-27B-UD-Q4_K_S.gguf`) enable chain-of-thought in their chat template. LM Studio **ignores** `enable_thinking` and `chat_template_kwargs`, but **honors top-level `reasoning_effort`** (`none` disables thinking entirely — verified: `reasoning_content: ""`, `reasoning_tokens: 0`; valid values none|minimal|low|medium|high|xhigh). On agent workloads with ~50k-token context, prefill + CoT exceeded Hermes's 180s non-streaming stale detector → connection killed → retry with growing context → agent appeared "stuck / overthinks / loops" (cron `Math Projects Worker` failed 2026-09-01). Fixes (math profile, 2026-09-01; **user decision: reasoning stays MEDIUM** — anti-loop = timeout + bounded persistence, NOT disabling thought):
  1. `hermes config set 'providers.lmstudio.models.qwen3\.8-27b.stale_timeout_seconds' 900` — Hermes honors explicit per-model config over its built-in 180s reasoning floor (`get_provider_stale_timeout`, `agent/reasoning_timeouts.py`). This stops the kill/retry loop.
  2. `hermes config set 'agent.reasoning_overrides.qwen3\.8-27b' medium` — reasoning kept at medium by design (global `agent.reasoning_effort: medium` would apply anyway). To ever disable thinking for speed: set the override to `false` (YAML bool ⇒ `{'enabled': False}` ⇒ Hermes sends `reasoning_effort: "none"` — verified `reasoning_tokens: 0`). `reasoning_effort` is the ONLY API knob LM Studio honors for this; `enable_thinking`/`chat_template_kwargs` are ignored.
  3. SOUL.md Calculation Mandate bounded (stop after 2–3 failed attempts / no-new-info) to limit tool-call loops.
  Verify with: `HERMES_HOME=... hermes-agent/venv/bin/python -c "from hermes_constants import resolve_reasoning_config; import yaml; print(resolve_reasoning_config(yaml.safe_load(open('config.yaml')), 'qwen3.8-27b'))"` → expect `{'enabled': True, 'effort': 'medium'}`.
