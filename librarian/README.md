# librarian profile pack

Sanitized, ready-to-use copy of the **librarian** Hermes profile, packaged with the
AgentDesign document. Directory structure follows a Hermes profile exactly, so the
folder can be copied straight into `~/.hermes/profiles/librarian/`.

## Install

```bash
cp -r librarian/ ~/.hermes/profiles/librarian/
```

Then fill in every placeholder (nothing secret ships in this pack):

```bash
grep -rl 'REPLACE_ME\|YOUR-HOST\|YOUR-DDNS-HOST\|YOUR-USER' ~/.hermes/profiles/librarian/
```

| Placeholder | Replace with |
|---|---|
| `REPLACE_ME` | your token / API key for that key name |
| `YOUR-HOST` | address of your self-hosted service plane |
| `YOUR-DDNS-HOST` | external fallback hostname (optional) |
| `/home/YOUR-USER` | your home directory path |

## Contents

| Path | Role |
|---|---|
| `config.yaml` | profile configuration, model settings, MCP server registrations |
| `.env` | service endpoints and credentials (all values placeholdered) |
| `profile.yaml` | profile description |
| `SOUL.md` | profile persona / operating instructions |
| `memories/` | persistent memory files (`MEMORY.md`, `USER.md`) |
| `skills/` | skill tree: SKILL.md units with their scripts and references |
| `plugins/` | `vikunja`, `wiki-browser` (bundled so the pack is self-contained) |
| `scripts/` | MCP CLI adapter and wiki pipeline helpers |
| `cron/` | scheduled jobs (`jobs.json`) |
| `desktop-plugins/` | desktop surfaces for the bundled plugins |

## External dependencies (not shipped)

These are shared infrastructure, expected to exist on the target machine:

* `~/.hermes/skills/` — shared skill pool (fallback for skills not in this tree)
* `~/.hermes/plugins/` — shared plugin installs
* `~/.hermes/mcp-servers/.venv/` — single Python environment all MCP servers run in
* the self-hosted service plane (Vikunja, LightRAG, SearXNG, ZIMI, SiYuan, Portainer,
  Honcho, LM Studio) plus SaaS APIs (Wolfram|Alpha, Zotero, Semantic Scholar)


## Note on scrubbing

Credentials, endpoints, hostnames, local paths and personal identity (name, handle,
author IDs) are replaced with placeholders throughout. Skill *names* are kept verbatim
(e.g. `ghasemi-latex-style`), because other files reference them by name — renaming one
would break the tree.

## Excluded on purpose

Runtime state and private data are **not** part of this pack: `state.db*`, `sessions/`,
`logs/`, `cache/`, `state-snapshots/`, `backups/`, `vault/`, `telemetry/`, lock files,
`__pycache__/`, curator backups, and the sandbox `home/` directory. The loader, curator
and telemetry bookkeeping files are left out as well — `.usage.json`, `.bundled_manifest`,
`.curator_state`, `.curator_suppressed`, `.curator_ledger.jsonl` — since they record one
installation's history rather than the profile's design. Hermes recreates the runtime
state on first start.
