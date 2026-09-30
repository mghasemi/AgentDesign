---
name: lean4
description: "Use when checking Lean4 files, searching Mathlib lemmas, exploring goal states, or attempting machine-checked proofs in a Lean project."
metadata: {"clawdbot":{"emoji":"\u03bb","requires":{"bins":["python3"]},"config":{"env":{"LEAN4_PROJECT_DIR":{"description":"Default Lean project directory. Used when --project-dir is not provided.","default":"","required":false},"LEAN4_TIMEOUT":{"description":"Lean command timeout in seconds","default":"60","required":false},"LEAN4_STRICT_PROJECT":{"description":"Require a Lake/Lean project for commands that import Mathlib","default":"false","required":false},"LEAN4_ALLOW_SCRATCH":{"description":"Allow auto-creation of a scratch Lake+Mathlib project when no project is found","default":"true","required":false},"LEAN4_SCRATCH_ROOT":{"description":"Root folder used for the auto-created scratch project","default":"~/.cache/lean4_tool","required":false},"LEAN4_PROGRESS":{"description":"Emit progress logs to stderr during scratch initialization and routing","default":"true","required":false}}}}}
---
# Lean4 Verification And Proof Support

Use this skill for repository-agnostic Lean4 workflows. This skill does not encode domain-specific theorem families.

## When to Use

- Check whether Lean files compile.
- Search for candidate Mathlib lemmas for a target statement.
- Probe a Lean goal and inspect tactic suggestions.
- Attempt a first-pass proof with standard automation tactics.

## Commands

Run the tool directly from this skill folder.

### Check a file or project

```bash
python3 {baseDir}/lean4_tool.py check --project-dir /path/to/project
python3 {baseDir}/lean4_tool.py check Theorems/L_T1.lean --project-dir /path/to/project
```

### Run ad hoc Lean code

```bash
python3 {baseDir}/lean4_tool.py repl "#check Nat.succ"
python3 {baseDir}/lean4_tool.py repl "example : 2 + 2 = 4 := by decide" --mathlib
```

### Search for lemma candidates

```bash
python3 {baseDir}/lean4_tool.py search "forall x : R, x * x >= 0"
python3 {baseDir}/lean4_tool.py search "Nat.succ"
python3 {baseDir}/lean4_tool.py search "forall a b : Nat, a + b = b + a" --allow-scratch
```

### Attempt an automated proof sketch

```bash
python3 {baseDir}/lean4_tool.py prove "forall x : \u211d, x^2 >= 0"
python3 {baseDir}/lean4_tool.py prove "forall a b : \u211d, a + b = b + a"
```

## Output

- Commands return structured JSON by default.
- Use `--format text` for a compact human-readable summary.
- JSON payload includes the resolved project directory, command, exit code, stdout, stderr, and a simple status label.
- JSON payload also includes `phases`, a machine-readable list of lifecycle events (for example project resolution, scratch init/cache/build, and readiness state).

## MCP Server (Recommended)

An MCP server at `lean4_mcp_server.py` provides 4 native tools
(`lean4_repl`, `lean4_check`, `lean4_search`, `lean4_prove`) via
the MCP protocol. Tools appear automatically in new sessions as
`mcp_lean4_*`.

Registered in the math profile — already added via `hermes mcp add`.

### Testing after install

```bash
hermes mcp test lean4
```

## CLI Tool (Legacy)

For situations where MCP is not available, use the CLI tool directly.
**Note argument order:** global flags go BEFORE the subcommand.

```bash
HOME=/home/YOUR-USER/.hermes/profiles/math/home python3 {baseDir}/lean4_tool.py \
  --project-dir /tmp repl --no-mathlib "#check Nat.succ"
```

Use `--no-mathlib` for basic Lean checks that don't need Mathlib;
omit it (or pass `--mathlib`) for `import Mathlib`-dependent code.

## Configuration

- `LEAN4_PROJECT_DIR`: optional default project path.
- `LEAN4_TIMEOUT`: command timeout in seconds (default `60`).
- `LEAN4_STRICT_PROJECT`: when `true`, commands requiring project context fail if no project root is found.
- `LEAN4_ALLOW_SCRATCH`: when `true`, `search`/`prove` create and use a scratch Lean+Mathlib project when needed.
- `LEAN4_SCRATCH_ROOT`: root directory for the scratch project (default `~/.cache/lean4_tool`).
- `LEAN4_PROGRESS`: when `true`, emits phase logs to stderr (`init`, `cache`, `build`, and project resolution).

## Notes

- The skill is designed to be reusable across repos.
- Domain-specific routing should live in prompts/agents, not in this tool.
- The MCP server `lean4` is configured with `PATH` env to find the elan
  toolchain under the profile home AND `HOME` set to the profile home
  so that `lean` (the elan proxy) can locate `settings.toml`.
  Without `HOME`, `lean` will report `no default toolchain configured`.

## Environment Setup Pitfalls

When running Lean4 under Hermes profiles, the following environmental issues frequently arise:

- **HOME mismatch.** Hermes profiles set `HOME` to `~/.hermes/profiles/<name>/home/`, which is not the user's real home. elan installs toolchains under this profile-specific HOME. Always prefix commands with `HOME=/home/YOUR-USER/.hermes/profiles/math/home` (or the appropriate profile HOME) when invoking `lean` or `lake`. Failing to do so will show `no default toolchain configured`.
- **`elan default stable` triggers downloads.** The `stable` channel points to the latest release, which may differ from the installed version and trigger a large download on every invocation. Pin the default toolchain to the installed version: `elan default leanprover/lean4:v4.30.0`. Check installed toolchains with `ls ~/.elan/toolchains/`.
- **Git not in elan's PATH.** `lake update` (to fetch Mathlib) needs `git`. elan's environment may not inherit the system path. Use `export PATH="/usr/bin:$PATH"` before `lake update`.
- **Mathlib4 clone size.** Mathlib4 is approximately 7 GB decompressed and takes 5--10 minutes to clone over a typical connection. Do not set tight timeouts on `lake update` operations. Expect 15--40 minutes total for `lake update` + `lake build`.
- **lakefile target names.** In `lakefile.toml`, the `defaultTargets` must match the `[[lean_lib]]` name, not the project name. A `name = "lean_verify"` with `defaultTargets = ["lean_verify"]` will fail if the lib is `LeanVerify`.

## Mathlib Installation (Current State)

`~/.cache/lean4_tool/Lean4MCP_scratch/` is a **symlink** to the working Mathlib project:

| Property | Value |
|----------|-------|
| Target | `/home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4` (symlink, recreated 2026-08-28) |
| Lean version | v4.31.0 |
| Mathlib revision | `fabf563` (pre-built oleans in `.lake/packages/mathlib`) |
| Toolchains | Installed under both `/home/YOUR-USER/.elan` and the profile home's elan — either HOME works |

The original v4.30.0 scratch install (`c5ea003`, 2026-06-18) was deleted; do not let `_resolve_scratch()` re-create it from zero (a `lake new` + Mathlib clone is ~7 GB and its recovery path crashes if the parent dir `~/.cache/lean4_tool` is missing). If the symlink disappears again:

```bash
mkdir -p ~/.cache/lean4_tool && ln -sfn /home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4 ~/.cache/lean4_tool/Lean4MCP_scratch
```

### Verifying Mathlib-dependent files

For `.lean` files that `import Mathlib`, do NOT run `lean <file>` directly — it won't find Mathlib. Instead, use `lake env` from the Mathlib project directory:

```bash
HOME=/home/YOUR-USER PATH="/home/YOUR-USER/.elan/bin:/usr/bin:$PATH" \
  lake env lean /path/to/file.lean
```

with `workdir` set to `/home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4`.

The MCP `lean4_check` tool with `project_dir` set to the Mathlib project achieves the same (for files outside a project, always pass `project_dir`). The `lean4_repl`, `lean4_search`, and `lean4_prove` MCP tools require Mathlib and will auto-use the scratch project via `_resolve_scratch()`.
