#!/usr/bin/env python3
"""Build sanitized, ready-to-use profile packs for the AgentDesign document.

Copies the `math` and `librarian` Hermes profiles into AgentDesign/<profile>/,
keeping the Hermes profile directory structure and scrubbing every secret:

  * key-driven scrub of .env and config.yaml (keys matching TOKEN/KEY/SECRET/
    PASSWORD/APPID/API/ALLOWED_USERS/LIBRARY_ID -> REPLACE_ME)
  * URL host scrub (internal IPs and DDNS hostname -> YOUR-HOST / YOUR-DDNS-HOST)
  * local home path scrub (/home/<user> -> /home/YOUR-USER)
  * token-shape scrub (tk_/sk-/hf_/gh*/JWT/telegram bot tokens/slack/emails)
  * credential files inside skill and plugin trees -> key-preserving templates

Excluded on purpose: runtime state (state.db*, sessions, logs, caches,
state-snapshots, backups, sandbox home/, vault/, telemetry/, lock files),
__pycache__, curator backups/archive.

Usage:  python3 build_profile_packs.py [--dest DIR] [--source HERMES_DIR]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

SECRETISH = re.compile(
    r"(TOKEN|KEY|SECRET|PASSWORD|APPID|API|WEBHOOK|ALLOWED_USERS|LIBRARY_ID|CHAT_ID|EMAIL|PHONE)",
    re.I,
)
URLKEY = re.compile(r"(_URL|_BASE_URL|_ALT_URL|base_url)$", re.I)

PATTERNS = [
    (re.compile(r"192\.168\.[0-9]+\.[0-9]+"), "YOUR-HOST"),
    (re.compile(r"\b10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b"), "YOUR-HOST"),
    (re.compile(r"mghasemi\.ddns\.net", re.I), "YOUR-DDNS-HOST"),
    (re.compile(r"/home/[a-z][a-z0-9_-]{2,}"), "/home/YOUR-USER"),
    (re.compile(r"tk_[0-9a-fA-F]{16,}"), "REPLACE_ME"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "REPLACE_ME"),
    (re.compile(r"hf_[A-Za-z0-9]{20,}"), "REPLACE_ME"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "REPLACE_ME"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "REPLACE_ME"),
    (re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"), "REPLACE_ME"),
    (re.compile(r"[0-9]{8,12}:AA[A-Za-z0-9_\-]{30,}"), "REPLACE_ME"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"), "REPLACE_ME"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "YOUR-EMAIL"),
    # --- identity (usernames, handles, author metadata, author IDs).
    # Bibliographic citations of published papers are deliberately NOT touched:
    # they are public references and mangling them would corrupt the literature
    # content of the skills.
    (re.compile(r"\bmehdi\b", re.I), "YOUR-USER"),
    (re.compile(r"mghasemi/"), "YOUR-GITHUB/"),
    (re.compile(r"author Ghasemi\b"), "author YOUR-SURNAME"),
    (re.compile(r"author --id [0-9]{6,}"), "author --id YOUR-S2-AUTHOR-ID"),
]

ALLOW_TOP = {
    "config.yaml", ".env", "profile.yaml", "SOUL.md",
    "memories", "skills", "plugins", "scripts", "cron", "desktop-plugins", "hooks",
}
EXCL_DIRS = {".archive", ".curator_backups", ".locks", ".hub", "__pycache__", "output", "node_modules", ".git"}
EXCL_SUFFIX = (".pyc", ".pyo", ".lock", ".db", ".db-shm", ".db-wal", ".jsonl", ".tmp")

CRED_RELS = [
    "plugins/vikunja/dashboard/.emv",
    "skills/productivity/siyuan/.emv",
    "skills/semantic-scholar/.env",
]
# plugins bundled into the librarian pack so it is self-contained (live install
# resolves them from the shared pool ~/.hermes/plugins/)
BUNDLED_PLUGINS = ["vikunja", "wiki-browser"]


def host_scrub(value: str) -> str:
    for rx, repl in PATTERNS[:3]:
        value = rx.sub(repl, value)
    return value


def scrub_envfile(path: str) -> int:
    out, n = [], 0
    for line in open(path, encoding="utf-8", errors="surrogateescape"):
        raw = line.rstrip("\n")
        if not raw.strip() or raw.lstrip().startswith("#") or "=" not in raw:
            out.append(raw)
            continue
        key, _, val = raw.partition("=")
        if SECRETISH.search(key):
            quote = '"' if val.strip().startswith('"') else ""
            val = f"{quote}REPLACE_ME{quote}"
            n += 1
        elif URLKEY.search(key.strip()):
            val = host_scrub(val)
        out.append(f"{key}={val}")
    open(path, "w", encoding="utf-8", errors="surrogateescape").write("\n".join(out) + "\n")
    return n


def scrub_config(path: str) -> int:
    out, n = [], 0
    for line in open(path, encoding="utf-8", errors="surrogateescape"):
        raw = line.rstrip("\n")
        m = re.match(r"^(\s*)([A-Za-z_][\w-]*):(\s*)(\S.*?)(\s*)$", raw)
        if m:
            ind, key, sp, val, tail = m.groups()
            if SECRETISH.search(key):
                line = f"{ind}{key}:{sp}REPLACE_ME{tail}\n"
                n += 1
            elif URLKEY.search(key) or val.startswith("http"):
                line = f"{ind}{key}:{sp}{host_scrub(val)}{tail}\n"
        out.append(line)
    open(path, "w", encoding="utf-8", errors="surrogateescape").write("".join(out))
    return n


def scrub_patterns(root: str) -> int:
    n = 0
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            fp = os.path.join(dirpath, f)
            try:
                blob = open(fp, "rb").read()
            except OSError:
                continue
            text = blob.decode("latin-1")
            new = text
            for rx, repl in PATTERNS:
                new = rx.sub(repl, new)
            if new != text:
                open(fp, "wb").write(new.encode("latin-1"))
                n += 1
    return n


def collect_source_literals(source: str) -> set[str]:
    """Every literal secret value found in the source profile: .env values under
    secret-ish keys, config.yaml values under secret-ish keys, and every value in
    the credential files. URLs are excluded (host-scrubbed instead) and so are
    key names, which legitimately appear as text."""
    lits: set[str] = set()
    keynames: set[str] = set()

    def add(v: str) -> None:
        v = v.strip().strip('"').strip("'")
        if len(v) >= 6 and not v.startswith("http"):
            lits.add(v)

    for prof in ("math", "librarian"):
        env = os.path.join(source, "profiles", prof, ".env")
        if os.path.exists(env):
            for line in open(env, errors="ignore"):
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    keynames.add(k.strip())
                    if SECRETISH.search(k):
                        add(v)
        cfg = os.path.join(source, "profiles", prof, "config.yaml")
        if os.path.exists(cfg):
            for line in open(cfg, errors="ignore"):
                m = re.match(r"\s*([A-Za-z_]\w*):\s*(\S.*)$", line)
                if m:
                    keynames.add(m.group(1))
                    if SECRETISH.search(m.group(1)):
                        add(m.group(2))
        for rel in CRED_RELS:
            fp = os.path.join(source, "profiles", prof, rel)
            if not os.path.exists(fp):
                continue
            for line in open(fp, errors="ignore"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for sep in ("=", ":"):
                    if sep in line:
                        add(line.split(sep, 1)[1])
                        break
    return {v for v in lits if v not in keynames}


def scrub_literals(root: str, literals: set[str]) -> int:
    """Replace literal secret values wherever they appear (including inside
    documentation, which is where credentials often leak)."""
    n = 0
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            fp = os.path.join(dirpath, f)
            try:
                blob = open(fp, "rb").read()
            except OSError:
                continue
            text = blob.decode("latin-1")
            new = text
            for lit in literals:
                new = new.replace(lit, "REPLACE_ME")
            if new != text:
                open(fp, "wb").write(new.encode("latin-1"))
                n += 1
    return n


def template_credentials(root: str) -> list[str]:
    done = []
    for rel in CRED_RELS:
        fp = os.path.join(root, rel)
        if not os.path.exists(fp):
            continue
        out = []
        for line in open(fp, encoding="utf-8", errors="ignore"):
            st = line.rstrip("\n")
            if not st.strip() or st.lstrip().startswith("#"):
                out.append(st)
            elif "=" in st:
                out.append(f"{st.split('=', 1)[0]}=REPLACE_ME")
            elif ":" in st:
                out.append(f"{st.split(':', 1)[0]}: REPLACE_ME")
            else:
                out.append("REPLACE_ME")
        header = ("# Redacted for distribution: original key names preserved, values replaced.\n"
                  "# Fill in your own credentials before use.\n")
        open(fp, "w", encoding="utf-8").write(header + "\n".join(out) + "\n")
        done.append(rel)
    return done


def copy_profile(src: str, dst: str) -> int:
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    count = 0
    for top in sorted(ALLOW_TOP):
        sp = os.path.join(src, top)
        if not os.path.exists(sp):
            continue
        if os.path.isfile(sp):
            shutil.copy2(sp, os.path.join(dst, top))
            count += 1
            continue
        for dirpath, dirs, files in os.walk(sp):
            dirs[:] = [d for d in dirs if d not in EXCL_DIRS]
            rel = os.path.relpath(dirpath, src)
            # preserve empty directories too: the category shells are part of the
            # profile structure even when they hold no files
            os.makedirs(os.path.join(dst, rel), exist_ok=True)
            if rel.split(os.sep)[0] == "cron":
                files = [f for f in files if f == "jobs.json"]
            for f in files:
                if f.endswith(EXCL_SUFFIX):
                    continue
                tgt = os.path.join(dst, rel, f)
                os.makedirs(os.path.dirname(tgt), exist_ok=True)
                shutil.copy2(os.path.join(dirpath, f), tgt)
                count += 1
    return count


README = """# {prof} profile pack

Sanitized, ready-to-use copy of the **{prof}** Hermes profile, packaged with the
AgentDesign document. Directory structure follows a Hermes profile exactly, so the
folder can be copied straight into `~/.hermes/profiles/{prof}/`.

## Install

```bash
cp -r {prof}/ ~/.hermes/profiles/{prof}/
```

Then fill in every placeholder (nothing secret ships in this pack):

```bash
grep -rl 'REPLACE_ME\\|YOUR-HOST\\|YOUR-DDNS-HOST\\|YOUR-USER' ~/.hermes/profiles/{prof}/
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
| `plugins/` | {plugins} |
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
{extra}

## Note on scrubbing

Credentials, endpoints, hostnames, local paths and personal identity (name, handle,
author IDs) are replaced with placeholders throughout. Skill *names* are kept verbatim
(e.g. `ghasemi-latex-style`), because other files reference them by name — renaming one
would break the tree.

## Excluded on purpose

Runtime state and private data are **not** part of this pack: `state.db*`, `sessions/`,
`logs/`, `cache/`, `state-snapshots/`, `backups/`, `vault/`, `telemetry/`, lock files,
`__pycache__/`, curator backups, and the sandbox `home/` directory. Hermes recreates
the runtime state on first start.
"""

EXTRA_MATH = ("* the SageMath conda environment (`sage`), the Lean/elan toolchain, and the TeX Live "
              "installation\n* the toolchain sandbox at `home/` (installed on first use)")

PLUGINS_MATH = "`vikunja`, `wiki-browser`, `hermes-android` (last one disabled in config)"
PLUGINS_LIB = "`vikunja`, `wiki-browser` (bundled so the pack is self-contained)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--source", default=os.path.expanduser("~/.hermes"))
    args = ap.parse_args()
    dest, source = args.dest, args.source
    literals = collect_source_literals(source)
    print(f"collected {len(literals)} literal secret values from the source profiles")

    for prof in ("math", "librarian"):
        src = os.path.join(source, "profiles", prof)
        dst = os.path.join(dest, prof)
        n = copy_profile(src, dst)

        if prof == "librarian":
            for pl in BUNDLED_PLUGINS:
                sp = os.path.join(source, "plugins", pl)
                if os.path.isdir(sp):
                    shutil.copytree(
                        sp, os.path.join(dst, "plugins", pl), dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.lock", ".emv"),
                    )

        env_secrets = scrub_envfile(os.path.join(dst, ".env"))
        cfg_secrets = scrub_config(os.path.join(dst, "config.yaml"))
        lit_files = scrub_literals(dst, literals)
        patterned = scrub_patterns(dst)
        creds = template_credentials(dst)

        readme = README.format(
            prof=prof,
            plugins=PLUGINS_MATH if prof == "math" else PLUGINS_LIB,
            extra=EXTRA_MATH if prof == "math" else "",
        )
        open(os.path.join(dst, "README.md"), "w").write(readme)

        print(f"{prof:10s} files={n:4d}  .env-secrets={env_secrets:2d}  config-secrets={cfg_secrets:2d}  "
              f"literal-scrubbed-files={lit_files:3d}  pattern-files={patterned:3d}  credential-templates={len(creds)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())