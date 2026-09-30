# Verifying Hermes' Internals (source read → scratch-home probe)

Use when the user asks what Hermes itself does (side effects, defaults, storage,
which code path runs) and a wrong guess would be acted on. The answer is always
**call chain (`file:line`) + raw probe output**, never a recalled behavior.

## Where the code is

| Thing | Path |
|---|---|
| Installed source | `~/.hermes/hermes-agent` (repo; `git log -1` gives its HEAD) |
| Profile home | `$HERMES_HOME` → `~/.hermes/profiles/<name>/` |
| Interpreter that has the deps | `~/.hermes/hermes-agent/venv/bin/python` |
| Desktop app main process | `apps/desktop/electron/*.ts`, built → `apps/desktop/dist/electron-main.mjs` (and `release/*/resources/app.asar.unpacked/dist/`) |
| Per-profile stores | `projects.db` (Projects), `state.db` (sessions), `kanban.db`, `config.yaml` |

`search_files` returns 0 for anything under `~/.hermes/**` — grep in the shell:

```bash
grep -rn "SYMBOL" --include=*.py --include=*.ts ~/.hermes/hermes-agent | grep -v /tests/ | head -40
```

## Probe recipe

1. `write_file` a small script (heredocs get mangled — see the SKILL.md pitfall).
2. Set `HERMES_HOME` to a scratch dir **before** importing any `hermes_*` module;
   paths resolve at import time.
3. Call the exact function the tool/RPC handler calls, not a re-implementation.
4. Assert on filesystem / DB state, print it raw, `rm -rf` the scratch tree.

```bash
HERMES_HOME=/tmp/hproj/home ~/.hermes/hermes-agent/venv/bin/python /tmp/probe.py
```

Never probe against the live profile: it writes rows into `projects.db`/`state.db`,
and `desktop_project` re-anchors the current session's workspace as a side effect.

## Projects ↔ git: what actually inits a repo

A Project is a `projects.db` row (`projects` + `project_folders`) plus an active
pointer. **Project creation never runs git.**

| Surface | Entry point | `git init`? |
|---|---|---|
| `desktop_project` tool (create) | `tools/project_tools.py` → `hermes_cli/projects_db.py::create_project` | no |
| Gateway RPC `projects.create` | `tui_gateway/methods_projects.py` | no |
| Desktop "new project" UI | `apps/desktop/src/store/projects.ts` (RPC only) | no |
| Repo auto-discovery / sidebar promotion | `tui_gateway/methods_projects.py` (`_repo_discovery_policy`, `_is_repo_junk`) | no — discovers *existing* git roots only |
| Worktree creation (desktop) | `apps/desktop/electron/git-worktree-ops.ts::addWorktree` → `ensureGitRepo` | **yes, lazily** |
| Worktree creation (web/TUI) | `hermes_cli/web_git.py::worktree_add` → `_ensure_repo` | **yes, lazily** |
| `hermes init` | `hermes_cli/commands.py` | no — AGENTS.md generator |

Lazy-init contract (both implementations, kept in sync):

- not inside a work tree → `git init`, then an **empty seed commit**
  (`-c user.email=hermes@localhost -c user.name=Hermes commit --allow-empty -m "Initial commit"`)
  so `git worktree add` has a HEAD to branch from;
- repo without commits → seed commit only, never re-init;
- committed repo → no-op; **never** inits a dir already inside a repo, never touches user files.
- `create_project` on a path already owned by a project is idempotent: it re-activates
  the existing project instead of minting a duplicate.

Probe that produced this map: `create_project` on an empty dir → `.git` absent, dir
listing empty; then `web_git.worktree_add(dir, {"name": "task-1"})` → `.git` present,
`git log` shows `Initial commit`, branch `hermes/task-1` created.
