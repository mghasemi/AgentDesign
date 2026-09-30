# AGENTS.md — AgentDesign Project

## Goal

Document the complete design architecture of the **math** and **librarian** Hermes profiles,
their shared tool stack, designated skills for general math-related projects, MCP servers,
plugins, and end-to-end workflow. Produce a reusable design document that serves as
both a project architecture record and a template for creating new math-focused Hermes
profiles. The document ships together with sanitized, ready-to-use copies of both profiles.

`README.md` is the entry point for anyone opening this repository: it carries the layout, the
build and deployment instructions, the reproducibility commands and the redaction policy. Keep it
in sync when the layout, the page count or the status changes — the same-commit rule that applies
to this file.

## Status

Active — Phase I (exploration) and Phase II (documentation + packs) complete; Phases III–V open.
The design document is `agent_design.tex` → `agent_design.pdf` (31 pp, compiles clean), and the
profile packs are `math/` and `librarian/`. Three appendices carry the enumerations: Appendix A the
service plane (`stack/`) component by component, including why each component was selected and what
would replace it; Appendix B the MCP bridge server by server (tool surface and place in the
workflow); and Appendix C the skill surface — the workflow's designated skills by stage, then the
complete catalog with each entry's activation in both profiles.

## Working Directory

```
/home/mehdi/Code/Professional/AgentDesign/
```

## Key References

| Resource | Path |
|---|---|
| LaTeX template | `/home/mehdi/Code/Professional/Proposal/Template/Template.tex` |
| Math profile config | `~/.hermes/profiles/math/config.yaml` |
| Librarian profile config | `~/.hermes/profiles/librarian/config.yaml` |
| Math-research-workflow skill | `~/.hermes/profiles/math/skills/research/math-research-workflow/SKILL.md` |
| MCP CLI adapter | `~/.hermes/profiles/math/scripts/mcp_cli_adapter.py` |
| Profile data (extracted, sanitized) | `data/profile_comparison.json` |

## Folder Structure

```
AgentDesign/
├── AGENTS.md                        ← this file
├── agent_design.tex / .pdf          ← main LaTeX documentation (cpistuff/cpi template)
├── cpistuff/, t1ggm.fd, ts1ggm.fd   ← template style package + Garamond font descriptors
├── math/                            ← sanitized, ready-to-use math profile pack
├── librarian/                       ← sanitized, ready-to-use librarian profile pack
├── stack/                           ← the profiles' service plane as one docker compose project
│   ├── docker-compose.yml           ← 16 containers (edge, notes, ledger, retrieval, ingestion, memory)
│   ├── .env.example                 ← every credential/port placeholder (real .env is git-ignored)
│   ├── searxng/settings.yml         ← live SearXNG config, secret_key from ${SEARXNG_SECRET}
│   ├── lightrag/.env.example, honcho/.env.example, paperflow/Dockerfile
│   └── README.md                    ← deploy guide, service map, live-deployment findings
├── data/
│   └── profile_comparison.json      ← extracted configuration data (sanitized)
└── references/
    ├── extract_profile_data.py      ← reads the live profiles → data/
    ├── build_profile_packs.py       ← builds math/ and librarian/ (copies + scrubs)
    ├── sanitize_extracted_data.py   ← scrubs data/ with the builder's rule set
    └── skill_inventory.md           ← per-entry skill inventory
```

## Profile Packs

`math/` and `librarian/` mirror the Hermes profile layout (config.yaml, .env, profile.yaml,
SOUL.md, skills/, plugins/, scripts/, cron/, memories/, desktop-plugins/, hooks/). They are
rebuilt from a live installation with:

```bash
python3 references/build_profile_packs.py
```

Placeholder policy: credentials, endpoints, hostnames, local paths and personal identity are
replaced with `REPLACE_ME` / `YOUR-*` placeholders; skill *names* are kept verbatim because other
files reference them by name. Runtime state (sessions, logs, caches, sandbox homes, vaults,
telemetry) is excluded. Verification after a build: no source literal survives in either pack,
the pattern scan is clean, and both `config.yaml` files parse as YAML.

## The service plane (`stack/`)

`stack/docker-compose.yml` unifies the seven compose projects that run on the live host
(`/opt/docker/{docker,honcho,lightrag,vikunja,zimi,pocketbase,paperflow}`) into one stack of
sixteen containers. It was validated on the host with `docker compose config -q` and
`docker compose up --dry-run`, and its plan was diffed against the live `docker ps`:
identical container names and identical published host ports for all sixteen services.
Four images differ on purpose — `honcho-api`, `honcho-deriver` and `paperflow` are local
builds (build contexts supplied), and `lightrag` uses the published upstream image instead
of the host's local build (documented in the stack README).

Secrets never enter this folder: `docker-compose.yml` interpolates everything from `.env`,
which is git-ignored, and `.env.example` carries the placeholders.

## LaTeX Compilation

```bash
cd /home/mehdi/Code/Professional/AgentDesign/
latexmk -pdf agent_design.tex
```

Uses the `cpistuff/cpi` style package from the Proposal Template directory, with Garamond fonts
installed per-user under `~/texmf` (`ggm*.tfm` → `fonts/tfm/ggm/`, `ggm*.vf` → `fonts/vf/ggm/`,
`ggm*.pfb` → `fonts/type1/ggm/`, `ggm.map` → `fonts/map/{pdftex,dvips}/ggm/`, then `mktexlsr ~/texmf`).
Expected result: 0 errors, 0 undefined references, 0 missing glyphs.