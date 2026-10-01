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
__pycache__, curator backups/archive, and the loader/curator/telemetry
bookkeeping files (.usage.json, .bundled_manifest, .curator_state,
.curator_suppressed, .curator_ledger.jsonl).

Usage:  python3 build_profile_packs.py [--dest DIR] [--source HERMES_DIR]
"""
from __future__ import annotations

import argparse
import glob
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
# Loader, curator and telemetry bookkeeping: per-installation runtime state, not
# design. Kept out of the packs (and out of version control) so a pack never
# ships one machine's usage counters, bundle manifest or curator ledger.
EXCL_FILES = {".usage.json", ".bundled_manifest", ".curator_state",
              ".curator_suppressed", ".curator_ledger.jsonl"}

# ------------------------------------------------------------ generalization
# A pack is a reusable template, so material tied to one user's research
# projects is dropped and the house LaTeX style is renamed to a neutral name.
# Paths are relative to the pack root.
EXCL_SKILL_PATHS = {
    "skills/differential-sdp",
    "skills/irene-rewrite-dev",
    "skills/mlops/dsdp-extension-workflow",
}
EXCL_REF_PATHS = {
    "skills/research/mathematical-research/references/irene-module-patterns.md",
    "skills/research/mathematical-research/references/project-state-survey.md",
    "skills/research/mathematical-research/references/differential-algebraic-optimization.md",
    "skills/research/literature-project-mapping/references/external-method-fit-assessment.md",
    "skills/research/wiki-maintenance/references/paper-ingestion-example.md",
    "skills/research/math-article-revision/references/sdp-to-formal-proof.md",
    "skills/research/scientific-coding/references/irene_benchmark_comparison.md",
}
EXCL_REF_GLOBS = ("skills/research/scientific-coding/references/ade_sdp_*.md",)
RENAME_SKILLS = {"skills/ghasemi-latex-style": "skills/user-latex-style"}
RENAMED_TERM = ("ghasemi-latex-style", "user-latex-style")
EXCL_MCP_SERVERS = {"hermes-irene"}
EXCL_SKILL_NAMES = {"differential-sdp", "irene-rewrite-dev", "dsdp-extension-workflow"}

# Sentence-level generalization applied to every text file in the pack. Each rule is
# (pattern, replacement); the patterns match material in the source profile, so a
# rebuild reproduces the shipped packs rather than reintroducing project prose.
GENERICIZE_RULES = [
    # --- the removed memory service ---------------------------------------
    (r"^export SIMPLERAG_[A-Z_]+ *=.*\n", ""),
    (r"^SIMPLERAG_[A-Z_]+ *=.*\n", ""),
    (r"simplerag-memory, ", ""),
    (r"^\s*- simplerag-memory$\n", ""),
    (r"^- `simplerag-memory`.*\n", ""),
    (r"^\| SimpleRAG (?:store|query) \|.*\n", ""),
    (r"^\| SimpleRAG\s*\|.*\n", ""),
    (r"^- \[ \] SimpleRAG healthy \(health endpoint\)\n", ""),
    (r"(?s)^4\. Log problem statement and decomposition to SimpleRAG:.*?(?=^6\. \*\*Hypothesis tree\*\*)", ""),
    (r"^6\. \*\*Hypothesis tree\*\*", "4. **Hypothesis tree**"),
    (r"(?s)^11\. Save report to SimpleRAG:.*?(?=^\*\*Gate\*\*)", ""),
    (r"(?s)^7\. Log all results to SimpleRAG:.*?(?=^\*\*Gate\*\*)", ""),
    (r"(?s)^2\. Store reflexion certificate to SimpleRAG:.*?(?=^4\. Close Vikunja project tasks)", ""),
    (r"^4\. Close Vikunja project tasks", "2. Close Vikunja project tasks"),
    (r"Query SimpleRAG `math-notation-glossary` group\.", "Query the shared notation glossary."),
    (r"\*\*Emit stage checkpoint\*\* to SimpleRAG group `stage-checkpoints`\.", "**Emit a stage checkpoint** to the project log."),
    (r"checked against the master glossary in SimpleRAG\.", "checked against the master notation glossary."),
    (r"master glossary stored in SimpleRAG\.", "master notation glossary."),
    (r"`LATEX_GLOSSARY_GROUP`: SimpleRAG group holding the master notation glossary\.",
     "`LATEX_GLOSSARY_GROUP`: group name of the master notation glossary."),
    (r"`SIMPLERAG_URL`: SimpleRAG endpoint for glossary retrieval\.",
     "`GLOSSARY_URL`: endpoint serving the notation glossary."),
    (r',?"SIMPLERAG_URL":\{"description":"[^"]*","default":"[^"]*","required":(?:true|false)\},?', ""),
    (r"^SIMPLERAG_URL = os\.environ\.get\(\"SIMPLERAG_URL\", \"http://YOUR-HOST:7000\"\)\n", ""),
    (r"\"description\":\"SimpleRAG group name", "\"description\":\"glossary group name"),
    (r"(records?|recorded|are recorded) failure context in SimpleRAG project groups",
     r"\1 failure context in the per-problem failure scratchpad"),
    (r"failures are recorded to SimpleRAG project groups", "failures are recorded to the per-problem failure scratchpad"),
    (r"error \+ code snippet are stored in SimpleRAG \(for example `project-<slug>-failures`\)\.",
     "the error and the code snippet are appended to the project's failure log."),
    (r"use siyuan or simplerag-memory\.", "use siyuan."),
    (r"related_skills: \[simplerag, ", "related_skills: ["),
    (r"academic-research-hub, simplerag-memory, calibre", "academic-research-hub, calibre"),
    (r"The `simplerag_client\.sh` helper additionally checks `SIMPLERAG_LOCAL_URL` \(loopback\)\nbefore failing\. The", "The"),
    (r'(?s)        ┌─────────┬─.*?web API\)',
     '''        ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐\n        │         │         │         │         │         │         │         │\n     :9621     :8899     :5050     :3456     :6806     :8080     :????\n    LightRAG   ZIMI    SearXNG   Vikunja   SiYuan   Calibre   Zotero\n    (graph    (offline  (meta-    (task     (notes)  (ebooks)  (bib,\n     RAG)      wiki)    search)   mgmt)                        web API)'''),
    # --- project names in prose -------------------------------------------
    (r"for concrete examples from the Irene \(MeansResearch\) and DiffSDP projects\.", "for concrete worked examples."),
    (r" — Concrete survey workflow using Irene \(MeansResearch\) and.*$", " — A concrete survey workflow, end to end."),
    (r"^- \[Irene Module Patterns\].*\n", ""),
    (r"served symmetric-algebras → MomentSheaf and jet/prolongation → DSDP\.",
     "served symmetric-algebras → one project and jet/prolongation → another."),
    (r"project \(MomentSheaf, Mean Polynomial, DSDP, …\)", "project (the workspace's active projects)"),
    (r"worked Irene ↔ Sum2d/BKM", "worked backend ↔ method"),
    (r"\(what Irene is and is not,", "(what the backend is and is not,"),
    (r"belongs in Irene or in a sibling project\.", "belongs in the backend package or in a sibling project."),
    (r"worked instance \(DSDP truncation theory, 4 repair passes in one session\)",
     "worked instance (a truncation-theory manuscript, 4 repair passes in one session)"),
    (r"lives in the `differential-sdp` skill's", "lives in the project's own notes:"),
    (r"relies on SDP decomposition \(Irene\) as the sole evidence", "relies on an SDP decomposition as the sole evidence"),
    (r"Workflow \(worked instance: DSDP", "Workflow (worked instance: a truncation-theory"),
    (r"Nie--Schweighofer bounds in DSDP / polynomial-optimization manuscripts\.",
     "Nie--Schweighofer bounds in polynomial-optimization manuscripts."),
    (r"\(DSDP truncation-theory", "(truncation-theory"),
    (r"connect to the user's active projects \(DSDP, Mean Polynomials, SOS hierarchies\) with s",
     "connect to the active projects (each with its own name) with s"),
    (r"worked example: Henrion et al\. arXiv:2305\.18768 PDF → wiki, with DSD.*$",
     "worked example: a paper PDF → wiki, end to end."),
    (r"implementation files under `Irene/`\) and `\.bib` bibliography files\.",
     "implementation files) and `.bib` bibliography files."),
    (r"`\.\./Irene/\.venv/bin/python script\.py`", "`../<package>/.venv/bin/python script.py`"),
    (r"from Irene\.mean_certificates import MeanCertificate", "from <package>.mean_certificates import MeanCertificate"),
    (r"\(e\.g\. `IreneRewrite/scripts/hermes_mcp_tool\.py` after merging into `Irene/`\)",
     "(e.g. a tool script inside a development worktree that was later merged into the main package)"),
    (r"Root AGENTS\.md\s+← workspace-level overview, active projects list, Irene API reference",
     "Root AGENTS.md                          ← workspace-level overview, active projects list"),
    (r"├── \./positivstellensatz/AGENTS\.md\s+← subproject context \(MP, DSDP, etc\.\)",
     "├── ./<project>/AGENTS.md                ← subproject context"),
    (r"├── \./Irene/doc/\*\.rst\s+← package API documentation",
     "├── ./<package>/doc/*.rst                ← package API documentation"),
    (r"(?s)^### Irene SDP benchmark comparison.*?(?=^### Research plan template)", ""),
    (r"Example: the `Eq\(diff, 0\)` fix had no effect on structural gaps \(P7, P8,\ntan ADE\) but needed documentation\. Added a \"Postscript: Eq Fix Numerical\nRerun\" section to `DSDP_Synthesis_Numerical_Experiments_2026-07-17\.md`\.",
     "Example: a symbolic-equality fix that changed no numerical result still needed\n"
     "documenting, so the verification was recorded as a short postscript to the\n"
     "existing report rather than as a rewrite."),
    (r"project codename \(e\.g\., \"DSDP\", \"Irene\", \"MP\"\) as the prefix\.", "project codename as the prefix."),
    (r"for YOUR-USER Ghasemi", "for YOUR-USER User"),
    (r"^# Ghasemi LaTeX Style Guide", "# User LaTeX Style Guide"),
    # --- links to the removed reference files -----------------------------
    (r"^.*(?:project-state-survey|differential-algebraic-optimization|external-method-fit-assessment"
     r"|paper-ingestion-example|sdp-to-formal-proof|irene-module-patterns|irene_benchmark_comparison"
     r"|ade_sdp_)[\w.-]*\.md.*\n", ""),
]
# Rules scoped to one file: runtime state that names the source projects.
FILE_RULES = {
    "memories/MEMORY.md": [(r"^.*\b(?:Irene|IreneRewrite|DSDP)\b.*\n", "")],
    "cron/jobs.json": [(r"the projects listed in 'projects\.csv'",
                        "the projects listed in the workspace project file")],
}
# Files whose design version is maintained here rather than derived by regex
# (the tool scripts whose failure log was re-pointed at the local scratchpad).
OVERRIDE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overrides")

GENERICIZE_EXTS = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".rst", ".tex"}


def generalize(dst: str) -> int:
    """Drop project-specific material from a freshly copied pack. Returns the count dropped."""
    dropped = 0
    for rel in sorted(EXCL_SKILL_PATHS | EXCL_REF_PATHS):
        p = os.path.join(dst, rel)
        if os.path.isdir(p):
            shutil.rmtree(p)
            dropped += 1
        elif os.path.exists(p):
            os.remove(p)
            dropped += 1
    for pattern in EXCL_REF_GLOBS:
        for p in glob.glob(os.path.join(dst, pattern)):
            os.remove(p)
            dropped += 1
    for old, new in RENAME_SKILLS.items():
        so, sn = os.path.join(dst, old), os.path.join(dst, new)
        if os.path.isdir(so):
            os.rename(so, sn)
    # the renamed style and the project prose are referenced from other files
    old_term, new_term = RENAMED_TERM
    rules = [(re.compile(pat, re.M), repl) for pat, repl in GENERICIZE_RULES]
    for dirpath, _dirs, files in os.walk(dst):
        for f in files:
            if f == "config.yaml" or os.path.splitext(f)[1] not in GENERICIZE_EXTS:
                continue
            p = os.path.join(dirpath, f)
            try:
                text = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            new = text.replace(old_term, new_term)
            for rx, repl in rules:
                new = rx.sub(repl, new)
            if new != text:
                open(p, "w", encoding="utf-8").write(new)
    # file-scoped rules, then the canonical versions of the rewritten tool scripts
    for suffix, scoped in FILE_RULES.items():
        for dirpath, _dirs, files in os.walk(dst):
            for f in files:
                fp = os.path.join(dirpath, f)
                if not fp.endswith(suffix):
                    continue
                text = open(fp, encoding="utf-8").read()
                new = text
                for pat, repl in scoped:
                    new = re.sub(pat, repl, new, flags=re.M)
                if new != text:
                    open(fp, "w", encoding="utf-8").write(new)
    if os.path.isdir(OVERRIDE_DIR):
        for dirpath, _dirs, files in os.walk(OVERRIDE_DIR):
            for f in files:
                rel = os.path.relpath(os.path.join(dirpath, f), OVERRIDE_DIR)
                out = os.path.join(dst, rel)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                shutil.copy2(os.path.join(dirpath, f), out)

    # config.yaml: drop the project-pinned MCP server and the removed skill names
    cfg_path = os.path.join(dst, "config.yaml")
    if os.path.exists(cfg_path):
        out, skip = [], False
        for line in open(cfg_path, encoding="utf-8").read().split("\n"):
            if re.match(r"^  (%s):\s*$" % "|".join(EXCL_MCP_SERVERS), line):
                skip = True
                dropped += 1
                continue
            if skip and re.match(r"^  \S", line):
                skip = False
            if skip:
                continue
            if line.strip().startswith("- ") and line.strip()[2:].strip() in EXCL_SKILL_NAMES:
                dropped += 1
                continue
            out.append(line)
        open(cfg_path, "w", encoding="utf-8").write("\n".join(out))
    return dropped

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
                if f in EXCL_FILES or f.endswith(EXCL_SUFFIX):
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
(e.g. `user-latex-style`), because other files reference them by name — renaming one
would break the tree.

## Excluded on purpose

Runtime state and private data are **not** part of this pack: `state.db*`, `sessions/`,
`logs/`, `cache/`, `state-snapshots/`, `backups/`, `vault/`, `telemetry/`, lock files,
`__pycache__/`, curator backups, and the sandbox `home/` directory. The loader, curator
and telemetry bookkeeping files are left out as well — `.usage.json`, `.bundled_manifest`,
`.curator_state`, `.curator_suppressed`, `.curator_ledger.jsonl` — since they record one
installation's history rather than the profile's design. Hermes recreates the runtime
state on first start.

This pack is also **generalized**: skills tied to one user's research projects, and the worked-example
notes that belonged to them, are not shipped; the project-pinned MCP
server registration is removed, and the house LaTeX style is renamed to
`user-latex-style`. Everything else — the configuration, the registrations, the
remaining skills — is as it stands in the source profile.
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
        dropped = generalize(dst)

        readme = README.format(
            prof=prof,
            plugins=PLUGINS_MATH if prof == "math" else PLUGINS_LIB,
            extra=EXTRA_MATH if prof == "math" else "",
        )
        open(os.path.join(dst, "README.md"), "w").write(readme)

        print(f"{prof:10s} files={n:4d}  .env-secrets={env_secrets:2d}  config-secrets={cfg_secrets:2d}  "
              f"literal-scrubbed-files={lit_files:3d}  pattern-files={patterned:3d}  credential-templates={len(creds)}  "
              f"generalized-dropped={dropped:2d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())