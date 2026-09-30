# Files-pane read path (source-level trace)

Local-mode read of the right-sidebar project tree, in call order. All paths are
relative to the hermes-agent source root (`~/.hermes/hermes-agent/apps/desktop`).

1. `src/app/right-sidebar/files/use-project-tree.ts` — `useProjectTree(cwd)`
   - `loadRoot(cwd)` → `readProjectDir(cwd, cwd)`.
   - `cwd` comes from the session's recorded launch cwd; on ENOENT it falls back
     to `sanitizeWorkspaceCwd` (default project dir).
2. `src/app/right-sidebar/files/ipc.ts` — `readProjectDir(dirPath, rootPath)`
   - `readDesktopDir(dirPath)`, then gitignore filter via `filterIgnored`.
   - Returns `{entries: [], error: 'no-bridge'}` if `window.hermesDesktop` is
     undefined (preload failed to load).
3. `src/lib/desktop-fs.ts` — `readDesktopDir(path)`
   - `isDesktopFsRemoteMode()` false → `bridge().readDir(path)` (Electron IPC).
   - remote → backend REST `/api/fs/list?path=…`.
4. `electron/preload.ts` — `readDir: dirPath => ipcRenderer.invoke('hermes:fs:readDir', dirPath)`
5. `electron/fs-ipc.ts` → `electron/fs-read-dir.ts` `readDirForIpc(dirPath)`
   - Filters `FS_READDIR_HIDDEN` (.git, .venv, node_modules, build, dist, …).
   - `resolveDirectoryForIpc` → `resolveRequestedPathForIpc` → `path.resolve` →
     `statForIpc` → `realpathForIpc` → `readdir`.
   - Any step throws an `ipcPathError` with `.code` (ENOENT / EACCES / ENOTDIR /
     `read-error`) that surfaces in the tree as `Unable to read (<code>)`.
6. Git-root / gitignore: `electron/git-root.ts` `gitRootForIpc` — pure fs walk
   (max 50 levels) for a `.git` dir; returns `null` for non-repos, so
   `filterIgnored` is a no-op and files show unfiltered.

Renderer-side hardening in `electron/hardening.ts`:
- `rejectUnsafePathSyntax` (NUL byte, `//?/`, Windows device paths).
- `rejectSensitiveFilePath` (`.env`, SSH keys, `.gnupg/`, `.aws/credentials`, …).
- `~` expansion for gateway-reported cwds (`~/...`).

Always-excluded names (renderer `src/lib/excluded-paths.ts`): `.git`, `.venv`,
`venv`, `env`, `node_modules`, `__pycache__`, `.pytest_cache`, `dist`, `build`,
`out`, `target`, … — note `.hermes` is NOT in this set, so a project-local
`.hermes/` dir shows in the tree.

## 2026-08-23 incident (worked example)

- `hermes update` completed ~10:55 MDT; `install-stamp.json` commit `f293e7206b`.
- `chrome-sandbox` was `not-root-not-setuid`; app could not auto-relaunch.
- After `sudo chown root:root && sudo chmod 4755`, `-rwsr-xr-x 1 root root`.
- Workspace `/home/YOUR-USER/Code/Python` is NOT a git repo (subprojects are), so
  `git rev-parse --show-toplevel` at the root is `fatal:` — expected, harmless.
