---
name: hermes-desktop-troubleshooting
description: "Diagnose Hermes desktop app issues: Files pane, updates."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, desktop, electron, troubleshooting, files-pane, self-update, sandbox]
    related_skills: [inspecting-hermes-desktop-dom, hermes-plugin-management]
---

# Hermes Desktop Troubleshooting

Diagnose and fix the Hermes native desktop app when it misbehaves: the Files
pane won't populate, the app won't relaunch after `hermes update`, or a profile
backend won't spawn. Complements the bundled `hermes-agent` skill (which routes
gateway / agent-core / provider issues) — this one owns the **Electron desktop
layer**.

## Key file map

| Path | What it tells you |
|---|---|
| `~/.config/Hermes/project-dir.json` | Default project dir the Files pane roots at (Electron `userData`). `{"dir": "..."}`; `null`/missing → falls back to the resolve chain. |
| `~/.config/Hermes/connections.json` | `primary` / `launchMode` / `lastUsed` — whether the active connection is `local` or `remote`. |
| `~/.config/Hermes/connection.json` | `{"mode": "local"|"remote", ...}`. |
| `~/.config/Hermes/backend-ownership.json` | Per-profile `hermes serve` backends the desktop spawned (pid, profile, command). |
| `~/.hermes/hermes-agent/apps/desktop/release/linux-unpacked/` | The packaged build. `resources/install-stamp.json` (commit/builtAt) + `chrome-sandbox`. |
| `~/.hermes/logs/desktop.log` | Main-process log: `[updates]`, `[boot]`, `[renderer console:main]` lines. |
| `~/.hermes/profiles/<name>/logs/{agent,errors,gui}.log` | Per-profile backend + gateway logs. |

## Symptom: Files pane empty / won't load workspace files

Triage in order — each is a fast, decisive check.

1. **Files actually there?** `ls -la <workspace>`. Empty/unreadable → a
   filesystem/permissions problem, not the app.
2. **Default project dir correct?** `project-dir.json` must point at an existing
   dir. The pane's cwd resolves through
   `readDefaultProjectDir() → HERMES_DESKTOP_CWD → process.cwd() → home`.
3. **Local or remote?** In `local` mode the pane reads via Electron IPC
   `hermes:fs:readDir` (direct fs). In `remote` mode it reads via backend REST
   `/api/fs/list` — a different, often-failing path. Confirm `connections.json`
   before chasing IPC.
4. **Bundle skew?** If `resources/install-stamp.json` commit != source HEAD, the
   renderer predates the runtime and desktop features (incl. the file tree) can
   silently miss. Compare `install-stamp.json` `commit` vs `git rev-parse HEAD`
   under `~/.hermes/hermes-agent`.
5. **Botched self-update?** See the sandbox section below — the single most
   common cause of a degraded desktop after `hermes update`.

If 1–4 are clean and the pane still won't load, you need the exact symptom
(empty / spinner / "Unable to read (`<code>`)" / wrong folder) to go further;
`<code>` maps to a readDir error (EACCES, ENOENT, ENOTDIR, `no-bridge`). See
`references/files-pane-read-path.md` for the full source-level read path.

## Recurring: self-update breaks the Linux SUID sandbox

`hermes update` rebuilds the packaged app in place. On Linux it re-writes
`chrome-sandbox` WITHOUT root ownership/setuid, so Electron can't relaunch:

```
[updates] sandbox preflight: not launchable (not-root-not-setuid) at …/chrome-sandbox; fallback=none
[updates] detached update finished with manual action: … sandbox helper needs root ownership). Reopen Hermes to finish.
```

The app then comes up **degraded** (empty Files pane, broken IPC, failed
MCP/backend spawns) because it was manually reopened over a torn build. Fix:

```bash
SAND=$HOME/.hermes/hermes-agent/apps/desktop/release/linux-unpacked/chrome-sandbox
sudo chown root:root "$SAND" && sudo chmod 4755 "$SAND"
# verify: stat -c '%a %U:%G' "$SAND"  →  4755 root:root  (-rwsr-xr-x)
```

Then **fully quit** the app (⌘Q / right-click → Quit — not just close the
window) and relaunch `hermes desktop`. Confirm the updater reports "Already up
to date" so it won't re-break the sandbox on the way back up.

This recurs on every `hermes update` for this user — check the sandbox mode
before assuming anything else is wrong.

## Symptom: a custom pane (e.g. Wiki) vanished after nothing touched the plugin files

Profile-scoped discovery trap — `localPluginsRoot()` in `electron/fs-ipc.ts`
is profile-aware: for any active profile ≠ default it scans
`<HERMES_HOME>/profiles/<name>/desktop-plugins/`, NOT the global root (and a
second scan root is `<profile>/plugins/<name>/desktop/plugin.js`). A pane built
only on one named profile's plugin vanishes when `~/.config/Hermes/
active-profile.json` flips to another profile — even if a mirror of the plugin
dir exists elsewhere and its backing server (e.g. VitePress) keeps running.
Diagnose: compare mtime of `active-profile.json` against symptom time; check
whether `<activeProfile>/desktop-plugins/<name>/plugin.js` (or the unified-package
half) exists. Known deployment (2026-09-06): wiki-browser is fanned out to ALL
profiles — python package under each `profiles/<p>/plugins/wiki-browser/` +
frontend door under each `profiles/<p>/desktop-plugins/wiki-browser/plugin.js`
(sha256 51a664a0…, api b868fb7d…; canonical = math's copies) plus the global
roots for default, and every profile's config.yaml lists it in
`plugins.enabled`. If a pane vanishes again after profile drift, diff those
copies/entries against this baseline first. Fix = switch back to that profile in-app or via the json + full app
restart — never kill/restart the app yourself.

**Unified-package `desktop/*.tsx` is NOT loadable by the 2026-09 build.** The renderer's disk loader scans only for
plain-ESM `<name>/plugin.js` doors (no TS/TSX compile step, no bare-specifier rewrites except
`@hermes/plugin-sdk` → `@hermes/plugin-sdk/runtime` and react). A plugin shipped as a unified package with
`desktop/plugin.tsx` (e.g. vikunja) silently never appears in any profile — backend discovery works (python half is
fine), the frontend door just can't exist. Fix pattern (done for vikunja 2026-09-06): hand-compile a plain-ESM
door from the .tsx (`import { jsx, useState } from "react"` + `register(ctx)` with `panes` /
`statusBar.right` / palette contributions; module contract = `default.id` string + `typeof register === 'function'`,
validated in runtime-loader.ts ~line 141), and fan it out to every profile's
`desktop-plugins/<name>/plugin.js` + the global root. Bare imports like `lucide-react` must be replaced with
unicode/text glyphs — any bare specifier outside react/SDK fails module resolution. Baseline: vikunja doors sha256
f09bbf55be84… in all 6 roots; backend package present under every profile's `plugins/vikunja/`; every config.yaml
lists it in `plugins.enabled`. Dashboard token lives in the package's `dashboard/.emv` (per-profile copy carries its
own).

## Pitfalls

- **Never kill or relaunch the user's desktop app yourself.** You are running
  *inside* it; killing it drops the very session you're answering from. Get
  explicit go-ahead before any restart.
- **Packaged builds have CDP disabled.** `127.0.0.1:9222` is closed on the
  release build, so `inspecting-hermes-desktop-dom`'s DOM-reading approach does
  NOT work on the production app — diagnose from logs + source + filesystem.
- **Backend plugin missing top-level `__init__.py`** → gateway log shows
  `Failed to load plugin '<name>': No __init__.py in .../plugins/<name>` and the
  dashboard API never mounts; the pane then shows its own error (e.g. "Failed to
  load Vikunja projects") even though frontend discovery succeeded. Fix: add a
  one-line `__init__.py` to every copy (global + per-profile). Verify with the
  venv python: import `dashboard/plugin_api.py` by path for each profile.
- **Dashboard API routes mount ONCE at web-server startup**
  (`web_server_dashboard.py::_mount_plugin_api_routes`, no hot-reload) — any
  backend-plugin file fix requires a full app relaunch before the pane can load
  data. Frontend disk doors are likewise scanned at Electron startup.
- **Dashboard manifest must live in `dashboard/manifest.json`** (fixed for vikunja
  2026-09-07). `_discover_dashboard_plugins()` scans ONLY `<pkg>/dashboard/manifest.json`
  and resolves the `api` field relative to `dashboard/`. A top-level package manifest
  (`"api": "dashboard/plugin_api.py"`) is invisible — plugin silently never mounts, no log
  line at all. The agent-plugin loader's separate warning (e.g. `Plugin 'vikunja' has no
  register() function` / `No __init__.py`) comes from a DIFFERENT code path and does not
  block mounting; dashboard-only plugins have no `register()` and still mount fine.
  Fix: `{"name": "<x>", "api": "plugin_api.py"}` in every copy's `dashboard/manifest.json`.
  Verify offline (no relaunch needed): venv python → `_discover_dashboard_plugins()` must
  return the plugin with `has_api=True` and api file present. Unauthenticated probes can't
  discriminate: ALL `/api/*` routes answer 401 to bare curl (session-token gate), so use the
  log's `Mounted plugin API routes:` lines as ground truth.
- **Creating a Project does not make it a git repo.** A Project is only a
  `projects.db` row; the folder gets `git init` + an empty seed commit *lazily*,
  on first worktree creation (`electron/git-worktree-ops.ts::addWorktree` →
  `ensureGitRepo`, and the Python twin `hermes_cli/web_git.py::worktree_add` →
  `_ensure_repo`). Already-committed repos are a no-op, and a dir inside an
  existing repo is never re-inited. Full call-chain map and the scratch-`HERMES_HOME`
  probe recipe: `hermes-tool-edge-cases` → `references/hermes-internals-verification.md`.
- **`git rev-parse` at the workspace root can be `fatal: not a git repository`**
  even when subprojects are repos. That is normal: the pane's `gitRootForIpc` is
  a pure fs `.git`-presence walk (max 50 levels) and returns null fast — it is
  not a hang cause.
