---
name: math-research-workflow
description: "Use when the user asks to perform deep mathematical research, prove a conjecture, investigate a theorem, analyze a mathematical problem rigorously, or conduct a literature-backed mathematical investigation. Triggers: prove this, investigate, research this problem, deep dive, formal verification, mathematical analysis. Implements a 6-stage single-agent pipeline adapted from the MathAgent multi-agent system with Graph-of-Agents (GoA) deterministic message passing and Reflexion quality gates."
version: 1.6.0
author: YOUR-USER
license: MIT
metadata:
  hermes:
    tags: [math, research, pipeline, verification, GoA, reflexion, literature, proof]
    related_skills: [user-latex-style, lightrag, sympy-mcp, sagemath-mcp, wolfram-alpha, lean4, scientific-coding, academic-research-hub, semantic-scholar, zimi, searxng, zotero, calibre, siyuan, vikunja, latex-manuscript, ocr-and-documents]
---

# Mathematical Research Workflow (Single-Agent Adaptation)

## Overview

This skill implements a rigorous 6-stage mathematical research pipeline as a
**single-agent workflow**. It is adapted from the MathAgent multi-agent system.
The same principles apply — deterministic-first computation, source-priority
routing, and quality gates — but stages are executed sequentially by one agent
rather than delegated to specialist sub-agents.

Every stage output must satisfy a 5-check **Reflexion Gate** before advancing.
Human approval is required at each stage boundary for non-trivial research.

**Supporting references:**
- `references/service-endpoints.md` — service topology, URLs, credentials status
- `references/venv-setup.md` — Python venv creation, package installation, PATH config
- `references/mcp-servers.md` — MCP server registration, tool naming, terminal vs MCP guidance
- `references/verified-sources-registry.md` — **per-project dedup cache**: format + check-before-verify / check-before-download procedure for citations and source files
- `scripts/literature_source.py` — lookup + download helper for the registry

## When to Use

- User asks to "prove", "investigate", "research", "analyze" a mathematical
  theorem, conjecture, or problem
- User requests a literature-backed mathematical investigation
- User wants formal verification of a claim
- User asks for a manuscript-ready research output
- User asks to "audit", "assess", or "check the status" of a manuscript
  (".tex" file) — use the lightweight Manuscript Status Audit
- Any task that would benefit from the full GoA pipeline

Do NOT use for simple computations (use sympy-mcp or wolfram-alpha directly),
quick fact-checks, or tasks completable in a single tool call.

## MCP Tool Availability

Many tools are registered as Hermes native MCP servers (see
`references/mcp-servers.md`). These are callable as first-class tools
via `mcp_<server>_<action>` — no terminal process needed. Prefer MCP
for single-call operations (solve, verify, search, create). Fall back to
terminal commands when you need multi-step workflows, tools not registered
as MCP, or stderr inspection during debugging.

Registered MCP servers: vikunja, wolfram-alpha, lightrag,
siyuan, zimi, searxng, sympy-mcp, zotero,
latex-manuscript, scientific-coding.
Not registered: lean4 (no binary), sagemath-mcp (no binary),
academic-research-hub, semantic-scholar, calibre,
ocr-and-documents (terminal-only).

## Core Principles

### GoA (Graph-of-Agents) Deterministic Flow
Deterministic tool outputs (SymPy, SageMath, Wolfram|Alpha, Lean4) are passed
as **hard context** into all subsequent steps. Never re-query, re-infer, or
re-compute a value that a tool already produced. This prevents hallucination of
different values across stages.

### Source-Priority Routing (Literature Stage)
For literature gathering, query sources in this exact order:
1. **LightRAG query** (hybrid mode) — graph-RAG over curated papers
2. **academic-research-hub** — arXiv + quick multi-source search
3. **semantic-scholar** — S2 citation-graph layer (`s2.py`): citation/reference traversal, recommendations, TLDR triage, OA-PDF discovery, bulk batch metadata (≤500 IDs/request). Use when the question is about paper *relationships* or *influence*, not just existence.
4. **SearXNG** — broad web sweep
5. **`web_search`** — targeted internet search for niche papers, theses, lecture notes not indexed by standard APIs
6. **`web_extract` on academic PDFs** — extract full text from thesis/paper PDFs, lecture slides (CIRM), arxiv PDFs. The tool parses PDF URLs into clean markdown. **Important:** extracted content is cached at `~/.hermes/profiles/math/cache/web/` — reuse cached content via `read_file` on the cache path instead of re-extracting. **Also save the source file** into the project's `Sources/` folder
   (`scripts/literature_source.py fetch`) so the source artifact, not just the
   extracted text, is kept locally — see `references/verified-sources-registry.md`.
7. **ZIMI** — offline encyclopedia for canonical definitions
8. **Zotero** — bibliography-level lookup
9. **Calibre** — local library search

**PDF extraction pattern:** For academic theses and papers found via `web_search`, use `web_extract` on the PDF URL directly (e.g., `https://agif.umons.ac.be/Brouette/Thesis.pdf`). The tool handles PDF→markdown conversion. For large theses, extract in stages: first the Table of Contents to locate the target chapter, then re-extract with higher `char_limit` focused on that section.

**Cached content reuse:** After extraction, the full text is stored as markdown in the cache. To continue reading a long document across sessions, use `read_file` on the cache path (e.g., `/home/YOUR-USER/.hermes/profiles/math/cache/web/<domain>-<hash>.md`) with `offset` and `limit` for pagination — avoids redundant network calls and preserves the session state across turns.

Stop early only after ≥2 distinct prioritized sources produce ≥1 directly
relevant claim each AND ≥3 total source-backed claims are collected. If
threshold unmet, continue through remaining sources, then fall back to
general web tools.

### Reflexion Gate (5 Checks)
After every stage, self-audit the output against these checks:

1. **Logical Consistency** — Every claim consistent with Wolfram|Alpha and/or
   Lean4 verification. No contradictions.
2. **Notation Consistency** — All symbols used as defined. No drift in meaning
   across sections. Query the shared notation glossary.
3. **Originality** — No section is pure restatement of a known source without
   synthesis or attribution. Query LightRAG for >80% overlap checks.
4. **Citation Completeness & Verification** — Every factual claim has a source.
   Every `\cite{}` key resolvable in Zotero or local bib, AND every recorded
   citation (authors, venue, volume, pages, year) verified against primary
   metadata via the Stage 2 Citation Verification Gate — never transcribed from
   model memory.
5. **Assumption/Definition Impact** — If any assumption changed during the
   workflow, downstream artifacts re-evaluated.

Verdict: **PASS** (all 5 OK) → advance. **WARN** (advisory notes) → advance
with documented warnings. **FAIL** (blocking issue) → fix and re-audit; do
NOT advance.

---

## The 6-Stage Pipeline

### Stage 1 — Problem Decomposition & Planning

**Goal**: Decompose the research question into bite-sized tasks, create
tracking infrastructure.

**Actions**:
1. Restate the research question precisely
2. Identify: knowns, unknowns, hypotheses, required lemmas
3. Create Vikunja project and tasks:
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/vikunja/vikunja_tool.py projects create --title "MathAgent: <project name>"
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/vikunja/vikunja_tool.py tasks create --project-id <id> --title "Stage 1: Problem decomposition"
   ```
4. **Hypothesis tree** (when the problem admits multiple attack routes):
   structure it in Vikunja — parent task = the conjecture/question, one
   child task per attack branch. Each branch carries an explicit status in
   its description: `open` / `active` / `dead (reason)` / `resolved (result)`.
   Failed branches are closed with the reason, never deleted; link the
   branch to its scratchpad folder. Branches may run in parallel
   (`delegate_task`), but only verified survivors feed Stage 4 — dead ends
   feed the Failure Scratchpad.

**Gate**: Reflexion check on the decomposition. Is the problem well-posed?
Are assumptions explicit? **Human sign-off required** before Stage 2.

---

### Stage 2 — Literature Synthesis

**Goal**: Build a grounded, multi-source literature foundation.

**Actions** (in GoA priority order):
1. **LightRAG query** (hybrid mode):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/lightrag/lightrag_query_tool.py query "<research question>" --mode hybrid --include-references
   ```
2. **academic-research-hub** (arXiv + Semantic Scholar):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/academic-research-hub/scripts/research.py arxiv "<query>" --max-results 10 --format json
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/academic-research-hub/scripts/research.py semantic "<query>" --max-results 10 --format json
   ```
   For citation-graph work (who cites whom, influence, OA PDFs, bulk metadata), use the dedicated **semantic-scholar** skill:
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/semantic-scholar/scripts/s2.py search "<query>" --sort citations --limit 10
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/semantic-scholar/scripts/s2.py citations <paper_id> --limit 50 --json
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/semantic-scholar/scripts/s2.py recommend <paper_id> --limit 10
   ```
3. For each highly relevant paper (top 5):
   - Ingest into LightRAG:
     ```
     python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/lightrag/lightrag_ingest_tool.py ingest-arxiv <arxiv_id>
     ```
   - Add to Zotero:
     ```
     python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/zotero/zotero_tool.py add-paper --arxiv <arxiv_id>
     ```
4. **SearXNG** (if prior sources insufficient):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/searxng/scripts/searxng.py search "<query>" -n 8 --format json
   ```
5. **Web search for thesis/lecture PDFs** — for niche results not indexed by standard APIs:
   - Use `web_search` with targeted queries (author name + "thesis" + topic keywords)
   - For each promising PDF URL, use `web_extract` to parse into markdown
   - **Thesis PDF pattern:** `web_extract(char_limit=30000)` on the full PDF; then use `read_file` on the cached extraction to navigate sections by offset
   - **Cached content path:** `~/.hermes/profiles/math/cache/web/<domain>-<hash>.md` — read via `read_file` with `offset`/`limit` for multi-turn traversal
6. **ZIMI** (for canonical definitions/theorems):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/zimi/zimi_tool.py retrieve "<term>"
   ```
7. **Zotero** (bibliography search):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/zotero/zotero_tool.py search "<query>"
   ```
8. **Calibre** (local library):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/calibre/calibre_tool.py "<query>"
   ```
9. **Threshold check**: ≥2 sources with ≥1 claim each + ≥3 total claims?
   If not, use fallback web tools and label as fallback.
10. **Synthesize** into structured report:
   ```
   ## LITERATURE SYNTHESIS REPORT
   ### Consensus
   ### Contradictions
   ### Open Questions
   ### Key Theorems/Definitions
   ### Papers Ingested into LightRAG
   ### Follow-up Questions for Stage 3
   ```
**Gate**: Reflexion check — are all claims source-backed? Any contradictions
unresolved? Run the Citation Verification Gate below. **Human sign-off required
before Stage 3.**

#### Citation Verification Gate (mandatory)

No bib entry, literature note, report reference, or `AGENTS.md` citation may be
written from model memory. Before a citation is recorded anywhere:

0. **Check the project's Verified-Sources Registry first** —
   `<project>/literature/verified_sources.md`. See
   `references/verified-sources-registry.md` for the format and full procedure.
   - If the source has a row with `Method` set and a recent `Check date`, copy
     the verified citation verbatim and STOP — do not re-query primary
     sources, even later in the same session.
   - If its `Local copy` column is non-`—`, read the stored file under the
     project's `Sources/` instead of re-downloading.
   - Quick lookup: `scripts/literature_source.py show <project_dir> <query>`
     (exit 0 = verified row / stored copy exists).
   - Append a full row only after a genuine first-time verification; never
     write a citation string from model memory.

1. (First-time verification only) Resolve the paper's identifier (arXiv ID or
   DOI).
2. Verify against primary metadata — at least one of:
   - **arXiv API**: `curl "https://export.arxiv.org/api/query?id_list=<id>"` → title, authors, `<published>`, `arxiv:journal_ref`.
   - **Crossref**: `curl "https://api.crossref.org/works/<DOI>"` → container-title, volume, pages, issued date.
   - **Semantic Scholar** (throttle ≥1.5 s): `python3 .../semantic-scholar/scripts/s2.py get <paper_id>`.
3. Record only the *verified* venue/volume/pages/year/authors. A mismatch between memory and primary metadata is a hard error — fix at the source, then propagate to every derived file (literature notes, reports, `AGENTS.md`) in the same commit.
4. Append the source row to `<project>/literature/verified_sources.md`
   (Key | verified citation | ID | check date | Method | Local copy | Notes).
   If the PDF was downloaded, save it into the project's `Sources/` folder via
   `scripts/literature_source.py fetch` and fill the `Local copy` cell so the
   file is never re-downloaded.

**Verified-Sources Registry = the dedup layer.** It is consulted before every
citation check and every download, in every session. Without it, the gate
described here would re-run identically on already-checked papers.

#### Downloads → keep a local copy

Store every downloaded article/PDF/source under the project's **`Sources/`**
folder (the same folder that holds AI-compiled source docs). Do NOT leave
fetched sources only in the `web_extract` text cache
(`~/.hermes/profiles/math/cache/web/`) — that cache holds extracted text, not
the source artifact, and is not a durable per-project record.

```
python3 .../math-research-workflow/scripts/literature_source.py fetch <project_dir> <url> <filename>
# => <project_dir>/Sources/<filename>   (skips the download if the file already exists)
```

Observed failure mode this gate prevents: fabricated venues (a real paper recorded as "JFA 267(5), 1398–1410" when it was actually *Canad. Math. Bull.* 57(2)), wrong co-author names, and wrong first initials — all of which propagate silently across reports once written into a single literature note.

---

### Error-Feedback Loop (binding retry protocol)

Any generate → execute/compile → fail sequence (Lean proofs, symbolic
computation, experiment scripts) must follow this loop. A retry without new
feedback information is wasted compute and is forbidden.

1. **Generate** an attempt (proof, script, expression).
2. **Execute** it via the relevant tool — compile, run, evaluate.
3. **Capture the exact error output** (compiler diagnostics on *stdout* for
   lake/lean; full exception text for Python) — never a paraphrase.
4. **Feed back**: the next attempt MUST include the prior error text as hard
   context and change the approach accordingly (same mistake with new tokens
   is not a new attempt).
5. **Retry budget: 3.** After 3 failed feedback-informed attempts on one
   goal, stop, record the failures in the Failure Scratchpad, and switch
   tool/model or escalate.
6. A retry carrying new error feedback is a **new call**, not a loop
   repetition — the loop-detection rule ("never call the same tool with
   identical arguments >3 times") forbids only *blind* re-runs, never
   feedback-informed retries.

### Failure Scratchpad (per-problem failure memory)

Location: `~/.hermes/profiles/math/scratchpad/<problem-slug>/failures.md`.
Plain markdown on purpose — exact-path reads/writes via native tools, no
network or token dependency.

- **Open** the file at the first failed attempt of a new problem
  (`mkdir -p` the folder, `write_file` the first entry).
- **Entry format** (one line per failed attempt):
  `[HH:MM] attempt: <strategy> | error: <exact message> | next: <changed approach>`
- **Read before any retry** and before resuming a problem from a prior
  session — the record of what failed prevents repeating it.
- **Close** with `RESOLVED: <what worked>` once solved; stop updating.
- **Cross-problem recall**: `search_files` over the scratchpad root for
  recurring error signatures and tool-specific failure patterns.
- **Promotion criterion** (scratchpad → durable memory, checked at Stage 6
  reflection): promote a failure if it (a) recurs across ≥2 problems
  (`search_files` the scratchpad root for the error signature), or (b)
  exhausted the full retry budget. Target: tool/infra failure → Pitfalls
  section of the relevant skill; domain/mathematical failure → project
  report or `AGENTS.md` failure entry. Promotion replaces recurrence
  warnings, not per-problem logs.

---

### Stage 3 — Computation & Empirical Validation

**Goal**: Symbolic verification followed by empirical experiments.

**Actions** (GoA order — symbolic FIRST, then empirical):

1. **SymPy** (exact symbolic computation):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/sympy-mcp/sympy_tool.py solve "<equation>"
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/sympy-mcp/sympy_tool.py integrate "<expression>" --var x
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/sympy-mcp/sympy_tool.py diff "<expression>" --var x
   ```
2. **SageMath** (if installed — advanced algebra, arbitrary precision):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/sagemath-mcp/sagemath_tool.py ring-ops "<sage code>"
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/sagemath-mcp/sagemath_tool.py matrix "<sage code>"
   ```
   Falls back to SymPy if SageMath not installed.
3. **Wolfram|Alpha** (cross-validate symbolic results):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/wolfram-alpha/wolfram_alpha_tool.py verify "<claim>" --profile symbolic
   ```
4. **Inject symbolic results** as hard context before empirical steps
   (GoA principle — do NOT re-query, do NOT re-infer).
5. **Scientific Coding sandbox** (empirical experiments):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/scientific-coding/scientific_coding_tool.py run --code "<python code>" --label "<experiment name>"
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/scientific-coding/scientific_coding_tool.py failures --recent 10
   ```
6. Any failed computation follows the **Error-Feedback Loop**: capture exact
   error, feed back as hard context, budget 3 retries, then record in the
   **Failure Scratchpad** and switch tool or escalate.
**Gate**: Reflexion check — do symbolic and empirical results agree? Any
numerical contradictions? **Human sign-off required** before Stage 4.

---

### Stage 4 — Formal Verification

**Goal**: Machine-checked proofs where possible; rigorous reasoning otherwise.
A clean compile is a *necessary* condition, not a correctness proof — every
theorem gets an explicit status in the project **claims ledger**.

**Actions**:
1. **Lean verification pipeline** (when Lean 4 + Mathlib are available):
   - Stage A — formalize: translate each target theorem/lemma into Lean; run `lean4_check` with an **explicit `project_dir`** pointing at a Lake project that has Mathlib (e.g. `positivstellensatz/VerifySection4`). Without it, checks run silently against *no* Mathlib context and "verified" means nothing.
   - Stage B — compile gate: fix diagnostics recursively via the **Error-Feedback Loop** (exact error text as hard context, changed approach each round, budget 3 — including **one recovery round-trip** for local-formalizer syntax drops before re-deriving the statement from scratch). Failed rounds are recorded in the **Failure Scratchpad**.
   - Stage C — statement-fidelity gate: diff the **final** verified Lean statement against the informal claim — quantifier structure, hypotheses, types (`ℕ` vs `ℝ`), strict vs non-strict, no silently dropped or weakened assumptions (vacuous formalization). The intake-time formalizer check does NOT cover drift introduced during retry loops. A proof of a different statement is not verification.
   - Only after all three stages pass may a theorem be labeled *formally verified*.
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/lean4/lean4_tool.py prove "<theorem statement>"
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/lean4/lean4_tool.py check --project-dir /path/to/Mathlib-project
   ```
2. **Claims ledger**: maintain `claims.md` (or a table in the project `AGENTS.md`) mapping every numbered theorem/proposition/conjecture to one of:
   `proven & Lean-verified` · `proven (informal)` · `conjecture` · `framework / possible`.
   Speculative content (spectral sequences, cohomological interpretations, etc.) must carry its label **in the manuscript body**, not only internally — a reader must never be able to mistake a framework for an established theorem. Keep the ledger's strongest proven results visibly distinct from speculative sections.
   **Artifact pointers**: each `proven & Lean-verified` entry records its `.lean` file path; partially formalized theorems record their partial-proof file at their true status. The ledger doubles as the Lean-artifact reuse index. Paths live in the ledger only — never in the manuscript body.
3. If Lean4 is NOT available: perform rigorous manual proof analysis; cross-check key steps with Wolfram|Alpha and document gaps explicitly in the ledger.
4. For numerical claims, cross-check with Wolfram|Alpha:
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/research/wolfram-alpha/wolfram_alpha_tool.py verify "<numerical claim>" --profile symbolic
   ```

**Gate**: Reflexion check — every theorem has a proof, an explicit open status in the ledger, or a Lean verification (with recorded `project_dir` and statement-fidelity check) plus its artifact pointer in the ledger. **Human sign-off required** before Stage 5.

---

### Stage 5 — Manuscript Production

**Goal**: Produce a compilable, well-structured LaTeX manuscript.

**Actions** (3-persona pipeline):

**Persona 1 — Drafter**:
1. Collect all verified inputs: literature report, symbolic results,
   empirical report, proof certificates
2. Sync Zotero bib:
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/zotero/zotero_tool.py sync-bib --output refs.bib
   ```
3. Generate `.tex` following the conventions in `user-latex-style`:
   ```latex
   \documentclass{amsart}
   \usepackage{amsmath, amssymb, mathrsfs, verbatim}
   \definecolor{DarkBlue}{rgb}{0,0.2,0.6}
   \definecolor{PinkPurple}{rgb}{0.8,0.3,0.3}
   \usepackage[pdftex, ..., linkcolor=DarkBlue, citecolor=PinkPurple, colorlinks=true]{hyperref}
   \newtheorem{thm}{Theorem}[section]
   \newtheorem{lemma}[thm]{Lemma}
   \newtheorem{prop}[thm]{Proposition}
   \newtheorem{crl}[thm]{Corollary}
   \theoremstyle{definition}
   \newtheorem{exm}[thm]{Example}
   \newtheorem{rem}[thm]{Remark}
   \numberwithin{equation}{section}
   \begin{document}
   \title[...]{...}\author{...}\date{}\maketitle
   \begin{abstract}...\end{abstract}
   \section{introduction}
   ...
   \begin{thebibliography}{99}
   \bibitem{key} Author, \emph{Title}, Journal \textbf{Vol} (pages), year.
   \end{thebibliography}
   \end{document}
   ```
4. **Compile gate** (if pdflatex installed):
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/latex-manuscript/latex_tool.py compile paper.tex
   ```
   Fix ALL errors before advancing.

**Persona 2 — Enhancer**:
1. Rewrite for scholarly clarity (paragraph by paragraph)
2. Run notation audit:
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/latex-manuscript/latex_tool.py notation-audit paper.tex
   ```
3. Gate: `errors: []` AND `drift_count: 0`

**Persona 3 — Reviewer**:
1. Check every `\cite{{key}}` against `.bib` file
2. Verify every theorem has proof or Lean4 cross-reference
3. Check originality via LightRAG
4. Produce numbered issues list

**Gate**: All blocking issues resolved. **Human sign-off required**.

---

### Manuscript Status Audit (Lightweight)

**Goal**: Rapidly assess what remains to be done on an in-progress manuscript —
without the overhead of the full Stage 6 Reflexion gate. Use this when the
user asks "what's the status of X.tex?", "what remains?", or "audit this
manuscript."

**Actions** (8-step checklist — see `references/manuscript-audit-checklist.md`):

1. **Read the full `.tex` file** — use `read_file` with pagination for files
   >500 lines. Do not skip sections.
2. **Compile** — run `pdflatex -interaction=nonstopmode` twice. The first pass
   produces undefined-reference warnings (expected); the second pass should
   resolve them. Count remaining warnings.
3. **Search for TODOs/placeholders** — grep for `TODO`, `FIXME`, `XXX`,
   `placeholder`, `\input{...}` references to non-existent files.
4. **Verify citations** — extract all `\cite{KEY}` keys, check each has a
   `\bibitem{KEY}` entry. Flag unused bib entries (in bibliography but never
   cited). Flag non-standard `\cite[...]{...}` syntax (commas in optional
   arguments can break parsing).
5. **Verify cross-references** — check that all `\ref{LABEL}` and
   `\eqref{LABEL}` keys correspond to `\label{LABEL}` definitions. The second
   compilation pass resolves this — grep for `Reference.*undefined` in the
   `.log` file.
6. **Check supporting files** — if the manuscript claims formal verification
   (Lean4, Coq, etc.), locate the claimed verification file and attempt to
   run it. Flag if the verifier is not executable (missing toolchain,
   missing dependencies like Mathlib).
7. **Compare against progress reports** — if `Progress/` or `Sources/`
   directories exist, check the latest reports for claimed status vs.
   actual file content. Watch for: old file paths, outdated theoretical
   approaches, resolved placeholders that reports still list as open.
8. **Categorize findings** — produce a table with columns: severity (🔴🟡🟢),
   location (line number), issue description, and suggested fix.

**Output format**: A markdown table of issues grouped by severity, preceded
by a one-line compilation status (✅/⚠️) and a note on theoretical correctness
if version drift was detected.

**Gate**: Lighter than full Reflexion — output the categorized table and
let the user decide which issues to fix. Do NOT block on Lean4/Mathlib
unavailability (flag it, don't halt).

---

### Stage 6 — Final Reflection & Sign-off

**Goal**: Certify the complete pipeline output and extract reusable insights.

**Actions**:
1. Run full 5-check Reflexion audit on the complete manuscript
2. Close Vikunja project tasks — and convert every open review finding lacking a disposition into an *open* Vikunja task:
   ```
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/vikunja/vikunja_tool.py tasks complete <task_id>
   python3 /home/YOUR-USER/.hermes/profiles/math/skills/productivity/vikunja/vikunja_tool.py tasks create --project-id <id> --title "<open finding>"
   ```
5. **Failure promotion check** (see Failure Scratchpad): apply the promotion
   criterion — failures recurring across ≥2 problems or budget-exhausting
   failures move from the scratchpad to skill Pitfalls (tool/infra) or the
   project report / `AGENTS.md` (domain).
6. **Status sync (same commit)**: if a phase completed, update the project `README.md` status section and its `AGENTS.md` in the *same commit* as the completion — tracking layers must never drift.
7. **Review disposition**: every review file (`review*.md`, `*_Review_*.md`) ends with a **Disposition** table mapping each finding → fixed / accepted-risk (with reason) / deferred. Undispositioned findings are pipeline debt, not closure. Report placement follows DOX.md: centralized `/home/YOUR-USER/Code/Python/Reports/[project]_[timestamp].md` for cross-project synthesis; per-project `reports/` for project-internal session reports — pick one per project and record the choice in that project's `AGENTS.md`.
8. Produce final synthesis:
   - Direct answer with stage provenance
   - 3–6 key points
   - Source-backed evidence list
   - Stage certificates
   - 1–3 follow-up questions

---

## Human Checkpoints

At every stage boundary, the agent MUST:
1. Present the stage output
2. Present the self-audited reflexion verdict (PASS/WARN/FAIL)
3. **Halt and wait for explicit human approval** before proceeding to the
   next stage

The user can override and skip a gate, but the agent must surface the gate
explicitly.

---

## Tool Reference (Absolute Paths)

All tools live under `/home/YOUR-USER/.hermes/profiles/math/skills`. Replace `/home/YOUR-USER/.hermes/profiles/math/skills` with the skill directory
root at runtime.

### Literature & Knowledge
| Tool | Command | MCP (prefer for single calls) |
|------|---------|------|
| LightRAG query | `python3 .../lightrag_query_tool.py query "<q>" --mode hybrid` | `mcp_lightrag_query` |
| LightRAG ingest | `python3 .../lightrag_ingest_tool.py ingest-arxiv <id>` | `mcp_lightrag_ingest-arxiv` |
| Academic hub (arXiv) | `python3 .../academic-research-hub/scripts/research.py arxiv "<q>" --max-results 10` | terminal-only |
| Academic hub (Semantic) | `python3 .../academic-research-hub/scripts/research.py semantic "<q>" --max-results 10` | terminal-only |
| Semantic Scholar (S2 graph) | `python3 .../semantic-scholar/scripts/s2.py <search|get|citations|references|batch|recommend|traverse> ...` | terminal-only |
| SearXNG | `python3 .../searxng/scripts/searxng.py search "<q>" -n 8 --format json` | `mcp_searxng_search` |
| ZIMI | `python3 .../zimi/zimi_tool.py retrieve "<term>"` | `mcp_zimi_retrieve` |
| Zotero | `python3 .../zotero/zotero_tool.py search "<q>"` | `mcp_zotero_search` |
| Calibre | `python3 .../calibre/calibre_tool.py "<q>"` | terminal-only |
| Web search | `web_search("<q>")` | Hermes built-in |
| Web extract (PDFs) | `web_extract(["<url>"])` | Hermes built-in (handles PDF→markdown) |

### Computation & Verification
| Tool | Command | MCP (prefer for single calls) |
|------|---------|------|
| SymPy | `python3 .../sympy-mcp/sympy_tool.py solve "<expr>"` | `mcp_sympy-mcp_solve` |
| SageMath | `python3 .../sagemath-mcp/sagemath_tool.py ring-ops "<code>"` | terminal-only (no binary) |
| Wolfram\|Alpha | `python3 .../wolfram-alpha/wolfram_alpha_tool.py verify "<claim>" --profile symbolic` | `mcp_wolfram-alpha_verify` |
| Lean4 | `python3 .../lean4/lean4_tool.py prove "<theorem>"` | terminal-only (no binary) |
| Scientific coding | `python3 .../scientific-coding/scientific_coding_tool.py run --code "<code>"` | `mcp_scientific-coding_run` |
| PDF extract | `python3 .../ocr-and-documents/pdf_extract_tool.py extract-pdf <file>` | terminal-only |

### Infrastructure
| Tool | Command | MCP (prefer for single calls) |
|------|---------|------|
| Vikunja create project | `python3 .../vikunja/vikunja_tool.py projects create --title "<name>"` | `mcp_vikunja_projects_create` |
| Vikunja create task | `python3 .../vikunja/vikunja_tool.py tasks create --project-id <id> --title "<title>"` | `mcp_vikunja_tasks_create` |
| LaTeX compile | `python3 .../latex-manuscript/latex_tool.py compile <file>` | `mcp_latex-manuscript_compile` |
| LaTeX notation audit | `python3 .../latex-manuscript/latex_tool.py notation-audit <file>` | `mcp_latex-manuscript_notation-audit` |
| SiYuan search | `python3 .../siyuan/siyuan_tool.py search "<q>"` | `mcp_siyuan_search` |

---

## Environment Variables Required

Copy these from the default `.env` or set them in the math profile `.env`:

```bash
# Core services (already in default .env)
export LIGHTRAG_URL="http://YOUR-HOST:9621"
export LIGHTRAG_ALT_URL="http://YOUR-DDNS-HOST:9621"
export LIGHTRAG_TIMEOUT="20"
export SEARXNG_URL="http://YOUR-HOST:5050/"
export WOLFRAM_ALPHA_APPID="<your-appid>"
export VIKUNJA_URL="http://YOUR-HOST:3456"
export VIKUNJA_ALT_URL="http://YOUR-DDNS-HOST:3456"
export VIKUNJA_TOKEN="<your-token>"

# Optional / missing from default .env
export ZIMI_URL="http://YOUR-HOST:8899"
export ZIMI_ALT_URL="http://YOUR-DDNS-HOST:8899"
export ZOTERO_API_KEY="<your-zotero-api-key>"
export ZOTERO_LIBRARY_ID="<your-zotero-library-id>"
export ZOTERO_BIB_PATH="/path/to/refs.bib"
export SIYUAN_URL="http://YOUR-HOST:6806"
export SIYUAN_TOKEN="<your-siyuan-token>"
```

---

## Local Dependencies

**CRITICAL**: This system uses PEP 668 (externally-managed Python environment).
Do NOT run bare `pip install` — it will fail. Use the math profile venv.
See `references/venv-setup.md` for full instructions.

```bash
# The venv already exists at ~/.hermes/profiles/math/venv/
# It is configured in the math profile .env via PATH prepend + VIRTUAL_ENV.
# All tool invocations using 'python3' will resolve to the venv Python.

# Already installed (2026-05-19):
#   sympy 1.14.0, pyzotero 1.11.1, arxiv 4.0.0, scholarly 1.7.11

# Optional but not yet installed:
sudo apt install sagemath        # or: conda install -c conda-forge sage
sudo apt install texlive-latex-base  # for LaTeX compilation

# Lean4 (via elan)
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
```

---

## Constraints

- Never fabricate citations. Every claim must trace to a tool output, and every
  recorded citation passes the Stage 2 Citation Verification Gate (primary
  metadata only — arXiv API / Crossref / S2 — never model memory).
- Never advance a stage past FAIL on reflexion check without human override.
- Never re-query a deterministic result (GoA principle).
- Never call the same tool with identical arguments >3 times (loop detection).
  This forbids only blind re-runs — a retry carrying new error feedback is
  a legitimate new call (see Error-Feedback Loop).
- Never retry a failed attempt without the prior exact error text in context.
- Prefer deterministic tool outputs over speculative LLM completions.
- If a required service is unreachable, document the gap and proceed with
  available tools; do not silently skip.
