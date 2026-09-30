---
name: mathematical-research
description: "Use when conducting mathematical research: formulating conjectures, literature review, symbolic computation, formal proof verification, empirical experiments, or manuscript production. Triggers on requests involving theorem proving, mathematical discovery, research pipelines, or formal verification workflows."
version: 1.1.0
author: YOUR-USER
license: MIT
metadata:
  hermes:
    tags: [mathematics, research, formal-verification, symbolic-computation, lean4, pipeline]
    related_skills:
      - sympy-mcp
      - sagemath-mcp
      - wolfram-alpha
      - lean4
      - scientific-coding
      - academic-research-hub
      - lightrag
      - simplerag-memory
      - zimi
      - zotero
      - calibre
      - latex-manuscript
      - vikunja
      - siyuan
      - project-bib
      - searxng
      - notebooklm-py
---

# Mathematical Research Pipeline

A 6-stage research pipeline with mandatory reflexion gates between each stage. Built on the Graph-of-Agents (GoA) principle: **deterministic computation results inform and constrain language-model tasks, not the reverse.**

## Research Project Survey (Reconnaissance Mode)

Use this mode when the user asks to **summarize, review, or report on the state** of a research project — not to conduct new research but to survey an existing one.

### When to use
- User asks "summarize the state of research in @ProjectName"
- User asks "what's the status of X, what files exist, what's next?"
- User wants a comparative overview of multiple research projects
- Onboarding to an unfamiliar codebase or manuscript repo

### Survey Protocol (multi-pass, increasing depth)

Execute passes in order. Stop when the user's question is answered at sufficient depth.

**Pass 1 — Identity & Topology** (always do this first)
1. `README.md` or `README.rst` — project purpose, authors, dependencies
2. `AGENT_WORKFLOW_MANUAL.md` or similar pipeline docs (if present)
3. `setup.py` / `pyproject.toml` — package structure, entry points
4. Top-level directory listing (`find -type f | head -60`)

**Pass 2 — Execution State**
1. **Plan/roadmap** (`plan.md`, `roadmap.md`, `phaseN_plan.md`) — current phase, completed items, in-progress items
2. **Theorem/conjecture ledger** (`theorem_ledger.md`, `claim_matrix.md`) — proven vs conjectural items, dependencies, next actions
3. **Phase remainder plans** (`phase2_remainder_plan.md`, etc.) — detailed close-out checklists
4. **Decision memos** (`*_decision_memo.md`) — key architectural trade-offs

**Pass 3 — Deliverables State**
1. **Manuscript** (`manuscript/draft.tex`, `*.tex`) — completeness, compilation status, abstract
2. **Reflexion certificates** (`*_reflexion_certificate.txt`) — stage-level pass/warn/fail verdicts
3. **Sign-off checklists** (`*_signoff_checklist.txt`) — which stages are approved, blocking items
4. **Reviewer reports** (`*_reviewer_report.txt`) — flagged issues

**Pass 4 — Technical Deep Dive** (if asked for specifics)
1. Core source code (`sdp.py`, `relaxations.py`, `sonc.py`, etc.) — architecture, lines of code
2. Experiment data (`results/*.jsonl`, `results/*.csv`) — number of runs, key metrics
3. Scripts (`scripts/*.py`) — benchmark runners, data pipelines
4. Test files (`tests/*.py`) — regression anchors

**Pass 5 — Comparative Synthesis** (for multi-project answers)
1. Build a comparison table across dimensions: maturity, evidence level, blocking items, next actions
2. Identify cross-project dependencies or shared methodology
3. Produce ranked open problems per project

### Output Conventions

Use these formatting rules for survey reports:

- **Files listing** — group by function (code, manuscript, notes, results) using a table with Purpose column
- **State tables** — use markdown tables with columns: Status/OP/Type | Statement | Status tag | Next action
- **Stage-wise summary** — table with: Stage | Status (✅/⏳/❌) | Key outputs
- **Comparative overview** — table with one row per project across common dimensions
- **Blocking items** — bold with explicit "blocking" label
- **Open problems** — numbered, with each entry's current status and recommended next action

### Common pitfalls

- **Missing project files**: If the user references `@ProjectName` and nothing is found, search the user's primary workspace (`/home/YOUR-USER/Code/Python/`) explicitly with `find -type d -name '*ProjectName*'` before concluding it doesn't exist.
- **Asking vs. reading**: Do not ask the user "what files are there" — read the directory structure yourself from Pass 1.
- **Constraint system analysis**: When analyzing mathematical constraint systems, always verify consistency mathematically first. Inconsistent systems (like $dy/dx = y$ and $dy/dx = 1/y$) must be handled by either refining constraints or solving as standard optimization.: When analyzing mathematical constraint systems, always verify consistency mathematically first. Inconsistent systems (like $dy/dx = y$ and $dy/dx = 1/y$) must be handled by either refining constraints or solving as standard optimization.: Always complete at least Pass 1 and Pass 2 before reporting. A "summary" that only lists directory names without state information is a stub, not a survey.

### Worked examples

See `references/project-state-survey.md` for concrete examples from the Irene (MeansResearch) and DiffSDP projects.

---

## Core Principles

### Graph-of-Agents (GoA) Message Passing
Deterministic tool outputs (SymPy, SageMath, Wolfram|Alpha, Lean4) are injected as **hard context** into all downstream tool calls in the same stage. Results are passed directly — never re-queried. This prevents different agents from independently hallucinating different values.

### Stage-Boundary Gate Protocol
At the end of every stage, run these steps in order:

1. **Collect the stage output** — all tool results, agent reports, computed artifacts.
2. **Run the 5 reflexion checks** (see below).
3. **Decision on verdict**:
   - **PASS** (all 5 checks clear) → save certificate, proceed to next stage with human approval.
   - **WARN** (advisory issues, none blocking) → save certificate with warnings, proceed.
   - **FAIL** (blocking issue) → save failure report, route back to responsible agent with exact remediation. Do NOT advance.
4. **Emit stage checkpoint** to SimpleRAG group `stage-checkpoints`.
5. **Create Vikunja gate task** `"Stage N complete — awaiting human sign-off"` with `priority: high`.
6. **Halt for human approval** before beginning the next stage.

### Reflexion Checks (run in order)

1. **Logical Consistency** — Every mathematical claim checked against Lean4 proof state or Wolfram|Alpha. Claim X but prover says ¬X → FAIL.
2. **Notation Consistency** — All symbols checked against the master glossary in SimpleRAG. Symbol used differently from its definition → FAIL.
3. **Originality** — Key claims checked against LightRAG. Section is >80% verbatim overlap with a single source without attribution → FAIL.
4. **Citation Completeness** — Every `\cite{key}` verified in Zotero. Missing key → FAIL.
5. **Assumption/Definition Impact** — If any tracked assumption changed during the project, verify all downstream artifacts were re-evaluated. Stale artifact → FAIL.

### Loop Detection
Track call count per (tool, argument_hash) pair. Same call > 3 times → log warning to SiYuan, create Vikunja critical task, surface to human, halt.

## Literature Source Priority

Query sources in this exact order. Stop early only after **≥ 2 distinct prioritized sources** each provide at least 1 directly relevant claim with a locator, AND **≥ 3 total source-backed claims** are collected across prioritized sources.

| Priority | Source | What It Provides |
|----------|--------|------------------|
| 1 | **LightRAG** (hybrid mode) | Relational graph depth — theorems, proofs, author networks |
| 2 | **NotebookLM** | Focused analysis of reference documents |
| 3 | **Academic Research Hub** (arXiv + Semantic Scholar) | Cutting-edge preprints, citation metrics |
| 4 | **SearXNG** | Broad web sweep for recent developments |
| 5 | **ZIMI** | Offline encyclopedic definitions and canonical statements |
| 6 | **Zotero** | Bibliography-level lookup and citation metadata |
| 7 | **Calibre** | Local library search by topic/title/author |

If threshold not met after all 7, proceed to fallback tools and label them as fallback.

Reconcile contradictions explicitly. Prefer sources with stronger technical grounding. Track provenance: source name + identifier/path for every key claim.

## Assumption/Definition Change Protocol

If any assumption or definition changes after Stage 1:

1. Determine rerun mode: default = targeted rerun of impacted artifacts; force full downstream rerun for high-risk triggers or explicit human override.
2. Create/refresh Vikunja rerun tasks from the impact report.
3. Resume stage progression only after impacted stages are re-certified and human-approved.

## Tool-to-Stage Mapping

### Stage 2 (Literature)
- `lightrag`: `query "<q>" --mode hybrid --include-references`
- `academic-research-hub`: `arxiv "<q>" --max-results 10 --format json`
- `lightrag`: `ingest-arxiv <id>` (after finding papers)
- `zotero`: `add-paper --arxiv <id>` (add to bibliography)
- `zimi`: `retrieve "<term>"`
- `calibre`: search by keyword/author
- `searxng`: `search "<q>" -n 8 --format json`

### Stage 3 (Computation)
- `sympy-mcp`: `solve`, `diff`, `integrate`, `dsolve`, `simplify`, `factor`, `expand`, `latex`
- `sagemath-mcp`: `ring-ops`, `matrix`, `precision-arith`, `number-field`, `run-script`
- `wolfram-alpha`: `verify "<claim>" --profile symbolic`, `answer`, `validate`
- `scientific-coding`: `run --file <path>` or `run --code "<code>"`, `test --file <path>`

### Stage 4 (Verification)
- `lean4`: `check`, `search`, `repl`, `prove`

### Stage 5 (Manuscript)
- `latex-manuscript`: `compile`, `ast-check`, `notation-audit`, `auto-glossary`, `diff-patch`
- `zotero`: `sync-bib --output refs.bib`
- `project-bib`: `init`, `add-entry`, `lint-bib`, `sync-mirror`

### Cross-Stage Infrastructure
- `vikunja`: projects/tasks for planning, gate tasks, and human checkpoints
- `siyuan`: structured notes, reflexion certificates, experiment logs
- `simplerag-memory`: stage checkpoints, shared insights, failure logs, notation glossary

## Manuscript Persona Pipeline (Stage 5 Detail)

### Persona 1: Drafter
Generate initial `.tex` from verified research outputs. **Gate**: `latex_tool.py compile` — advance only if `errors: []`.

Required input: Lean4 proof certificates, symbolic results, experiment reports, literature synthesis, Zotero `.bib`.

### Persona 2: Enhancer
Rewrite for scholarly tone and logical flow. No structural changes. **Gate**: compile passes AND `notation-audit` returns `drift_count: 0`.

### Persona 3: Reviewer
Segment-level critique. Check citation completeness, theorem-proof correspondence, notation consistency, originality. **Gate**: all blocking issues resolved, human sign-off on advisory issues.

## Verification Checklist

Before beginning research:
- [ ] Vikunja accessible (`vikunja_tool.py projects list`)
- [ ] SiYuan accessible (`siyuan_tool.py search "test"`)
- [ ] SimpleRAG healthy (health endpoint)
- [ ] LightRAG healthy (health endpoint)
- [ ] Zotero API key configured
- [ ] Wolfram|Alpha AppID configured
- [ ] Lean4 tool path + project directory configured
- [ ] LaTeX compiler (`pdflatex` or `lualatex`) on PATH
- [ ] SymPy and SageMath Python packages available

## References

- [MathAgent Agent Definitions](references/mathagent-agents.md) — Full agent roster, routing policy, service endpoints, STITCH framework.
- [Project State Survey Worked Examples](references/project-state-survey.md) — Concrete survey workflow using Irene (MeansResearch) and DiffSDP as worked illustrations.
- [GPkit Gotchas](references/gpkit-gotchas.md) — GPkit pitfalls: variable bounds, constant terms, constraint format, SignomialsEnabled.
- [Differential-Algebraic Optimization](references/differential-algebraic-optimization.md) — Key theoretical insights from Curto et al. for SDP exactness conditions and numerical verification
- [Theorem Verification Workflow](references/theorem-verification-workflow.md) — Cross-checking formulas against paper examples, catching incorrect inequality chains, proof simplification, definition relaxation.
- [Irene Module Patterns](references/irene-module-patterns.md) — Authoring new Irene modules: OptimizationProblem setup, result containers, wrapping SDP/SONC, test conventions.

## Related Skills

All tool skills are in the math profile under `research/` and `productivity/`. See the `metadata.hermes.related_skills` list in the frontmatter for the full roster.
