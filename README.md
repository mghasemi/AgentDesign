# AgentDesign — the math and librarian Hermes profiles

A design document for two Hermes agent profiles — a **mathematician** (`math`) and a **librarian** —
covering what each is made of, how they share one tool stack, and how that stack is deployed. It
ships with the two profiles as sanitized, ready-to-use packs and with the whole service plane as one
reproducible `docker-compose` project.

The document is `agent_design.pdf` (31 pp). Everything else in this repository either produces it or
is a distributable artifact it describes.

## What is here

| Path | What it is |
|---|---|
| `agent_design.tex` / `agent_design.pdf` | The document: 11 sections, three appendices, a sources note |
| `AGENTS.md` | Working notes for this repository — status, conventions, how the pieces stay in sync |
| `math/`, `librarian/` | Sanitized profile packs: copy into `~/.hermes/profiles/` and fill in the placeholders |
| `stack/` | The service plane as one compose project (16 containers), with its own `README.md` |
| `references/` | The scripts that extract, sanitize and rebuild everything above, plus the skill inventory |
| `data/profile_comparison.json` | Sanitized machine-readable extraction of both profiles |
| `cpistuff/` | The CPI LaTeX template the document is written in (`cpi.sty` and its logos) |
| `t1ggm.fd`, `ts1ggm.fd` | Garamond T1 font declarations — a compile prerequisite, see below |

## The document

| Part | Contents |
|---|---|
| 1–2 | Objectives, and the five-layer architecture from the Hermes core up to the service plane |
| 3–4 | The two profiles side by side; folder structure; what the packs ship and what they omit |
| 5 | The skill system as a design for general math projects, including how activation is expressed |
| 6 | The MCP bridge: naming, the native-versus-adapter split, credentials, registration |
| 7–8 | The tool stack and service plane, and the six-stage research workflow it serves |
| 9–10 | The couplings and defects found by inspection (Table 7), then the abstraction layer that would remove them |
| 11 | Roadmap for this documentation project itself |
| A | **The Self-Hosted Service Plane** — every component, its role, its dependencies, why it was chosen, what would replace it, and the hardware and model envelope it runs in |
| B | **The Model Context Protocol Bridge** — every server, its tool surface, and where the workflow spends it |
| C | **The Skill Surface** — the skills each stage invokes, then the complete catalog with per-profile activation |
| — | Sources and verification: how each claim was derived, and the redaction policy |

## Building the PDF

```bash
latexmk -pdf agent_design.tex          # writes agent_design.pdf
```

`agent_design.pdf` is committed on purpose — it is a deliverable, and the `.gitignore` deliberately
has no `*.pdf` rule. The build artifacts (`aux`, `log`, `fls`, `fdb_latexmk`, `toc`, …) are ignored.

**Prerequisite: the Garamond T1 fonts.** The template sets its body face in Garamond, which is not
part of a stock TeX Live installation. The fonts are installed per-user, with no root, under
`~/texmf/`: `ggm*.tfm` in `fonts/tfm/ggm/`, `ggm*.vf` in `fonts/vf/ggm/`, `ggm*.pfb` in
`fonts/type1/ggm/` and `ggm.map` in `fonts/map/pdftex/ggm/` (and `fonts/map/dvips/ggm/`), followed by
`mktexlsr ~/texmf`. The two `.fd` files in the repository root are the T1 declarations that go with
them. Without this the build fails with a missing-font error as soon as the body face is used.

## Using the profile packs

```bash
cp -r math ~/.hermes/profiles/          # or librarian
```

Each pack is a sanitized copy of a live profile: the same directory structure, configuration and
skill trees, with every credential, endpoint, hostname and personal path replaced by a placeholder.
Fill in the `REPLACE_ME` / `YOUR-*` values in `config.yaml`, `.env` and the co-located credential
files, and the profile is ready.

Each pack has its own `README.md` describing what is excluded and what to install. In short, the
loader, curator and telemetry bookkeeping files (`.usage.json`, `.bundled_manifest`,
`.curator_state`, `.curator_suppressed`) are runtime state and are not shipped — Hermes recreates
them on first start — while the credential templates (`.env`, `.emv`) *are* shipped, because they
document which keys each component needs. The math pack additionally expects the SageMath conda
environment, the Lean/elan toolchain and a TeX Live installation.

## Bringing up the service plane

```bash
cd stack
cp .env.example .env                    # fill in the placeholders
docker compose up -d
```

One compose project brings up all sixteen components: the edge and management layer, the note store,
the task ledger, retrieval (metasearch, offline archives, graph-RAG with its graph and vector
stores), the ingestion queue and conversion service, and the cross-session memory service. No
credential is stored in the compose file — every one is interpolated from the untracked `.env`.
`stack/README.md` has the service map, the data-migration notes and the deployment findings.

Every component is open source and has its own interface, and the plane is built for local deployment:
in practice it runs offline, with the inference server as the one piece the compose project does not
carry. The binding constraints are hardware, not subscriptions — the document's operating envelope
(§A.6) suggests 64 GB of system memory and 32 GB of accelerator memory, with `QWEN3.8-27B` at Q4 for
the main tasks, `QWEN3-8B` for the memory service and `text-embedding-nomic-embed-text-v1.5` for
embeddings. Online storage and compute remain available, at the cost of research privacy and token
spend.

## Reproducing the extraction

The document is derived from a live installation rather than from recollection, and the derivation is
reproducible:

```bash
python3 references/extract_profile_data.py       # read both profiles -> data/
python3 references/sanitize_extracted_data.py    # scrub the extracted data
python3 references/build_profile_packs.py        # rebuild math/ and librarian/ from a live ~/.hermes
```

`build_profile_packs.py` takes `--source` (default `~/.hermes`) and `--dest` (default this
directory). It applies the full redaction pass — key-driven, literal-value, pattern and credential
scrubbing — and preserves empty directories, so a rebuilt pack has the same structure as the live
profile. `references/skill_inventory.md` is the per-entry record of both skill catalogs.

## Redaction policy

No credential, endpoint, hostname or personal identifier appears in the document or in the packs.
Secrets become placeholders, internal hosts and paths are scrubbed, and the result is verified by a
residual-secret scan. Two deliberate exceptions: **skill names are kept verbatim** (other files
reference them by name, so renaming one would break the tree), and **bibliographic citations are kept
verbatim** (they are public references, and altering them would corrupt the literature record).

## Status

| | |
|---|---|
| Document | 31 pp; compiles with 0 errors, 0 undefined references, 0 missing glyphs, 0 overfull vertical boxes |
| Stack | Validated against the live installation non-destructively: the compose configuration resolves, the dry-run plan matches the running containers one for one — identical names and identical published host ports for all sixteen |
| Packs | Structure parity with the live profiles, 0 residual secrets after the redaction pass |
| Open work | The nine couplings of Section 9; the four one-line remediations of Section 10(F); the abstraction layer sketched in Section 10 |

See `AGENTS.md` for this repository's conventions and current status.