# Project State Survey — Worked Examples

Examples of the Pass 1–5 survey protocol applied to real projects.

---

## Example 1: Irene / MeansResearch (Phase 4 — Complete)

### Pass 1 — Identity & Topology

- `README.rst` → Python package, Lasserre SDP hierarchy, global optimization on commutative algebras
- `Irene/__init__.py` → imports from `base`, `sdp`, `relaxations`, `grouprings`, `program`, `matrices`
- `setup.py` → depends on SymPy, NumPy, SDP solvers (cvxopt, dsdp, sdpa, csdp)
- Key directories: `Irene/` (core), `examples/` (20+ benchmarks), `tests/`, `doc/`

### Pass 2 — Execution State

- `MeansResearch/plan.md` → 9-step, 4-phase roadmap, fully executed
- `MeansResearch/theorem_ledger.md` → 7 theorems (L-T1..L-T7 proven), 3 conjectures (L-C1, L-C2, CX-2), 3 open problems (OP1 frozen, OP2/OP3 validated)
- `MeansResearch/phase2_remainder_plan.md` → Groups A–D executed and verified
- `MeansResearch/op1_escalation_decision_memo.md` → d=6 n≥4 L-C1 frozen as solver-ceiling deferment

### Pass 3 — Deliverables

- Manuscript: `mean_polynomials_main.tex` (1023 lines → trimmed to ~846 lines, §§6–7 deferred/fleshed out separately)
- PDF: 12 pages, compiles clean
- No reflexion certificates (typical for a paper that pre-dated the agent pipeline)

### Outcome

The MeansResearch project is Phase 4 complete: the cone-theory manuscript is frozen, the computational evidence is extensive (~50 JSONL experiment files), and the open problems are ranked and scoped.

---

## Example 2: DiffSDP (Stage 5 — Awaiting sign-off)

### Pass 1 — Identity & Topology

- `README.md` → 6-stage multi-agent system for extending Irene with differential semigroup stationarity
- `manuscript/draft.tex` → 277-line LaTeX, compiles clean
- `scripts/diff_semigroup_extension_probe.py` → single computational probe via Irene's SDPRelaxations

### Pass 2 — Execution State

- All stages 1–4 approved in Vikunja (tasks 339, 340, 341, 348)
- Stage 5 (Manuscript) awaiting human sign-off in task 349
- Key result: KKT stationarity can be encoded as quotient-algebra relations in Irene
- Key result: differential stationarity compresses SDP (quotient basis 9→2, moment matrix 5→2)

### Pass 3 — Deliverables

- `manuscript/stage6_signoff_checklist.txt` → all stages certified except Stage 5
- `manuscript/reflexion_stage5_certificate.txt` → WARN on citations (Zotero unconfigured)
- No blocking issues; citations the only remaining item

### Outcome

One blocking item (Zotero citation sync) preventing Stage 5 sign-off. Manuscript content is otherwise complete and compiles.

---

## Example 3: positivstellensatz (Stage 5 — Written, awaiting sign-off)

### Pass 1 — Identity & Topology

- Private repo at `https://github.com/YOUR-GITHUB/positivstellensatz`
- Extension of Irene/MeansResearch: provides full §§6–7 that MeansResearch deferred
- Core contribution: a Positivstellensatz for mean polynomials using Marshall's representation theorem

### Pass 2 — Execution State

- All 6 stages complete
- `stage_5_checkpoint.md` → manuscript written (26 pages), §§6–7 fully integrated, awaiting sign-off
- `stage_6_final_report.md` → final report exists

### Pass 3 — Deliverables

- Manuscript: `.github/Sources/mean_polynomials_main.tex` (26 pages, compiles)
- `Progress/writing/manuscript_stage5_source.tex` → copy, compiles
- PDF available at both locations

### Pass 4 — Technical Deep Dive

- Corrected definition: $P_{\text{mean},2d} = \{\sum t_i \cdot g_i^{2d} : t_i \in T_{\text{mean}}, g_i \in A\}$, not $\{\sum f_i^{2d} : f_i \in T_{\text{mean}}\}$
- Stage 3 found: $x^2 \notin P_{\text{mean},2}$ under the original (flawed) definition
- Section 4 computational content trimmed from ~460 lines to a clean theorem + proof + two open questions

### Key Insight

The Marshall paper cited as `{Marshall99}` (unpublished) was actually published as:
**M. Marshall, "A general representation theorem for partially ordered commutative rings", Math. Z. 242 (2002), 217–225.**

### Outcome

Manuscript written and compiling — awaiting human sign-off. Section 6 improved version exists at `section6_improved.tex` with expanded bibliography and generalization remarks.

---

## Cross-Project Patterns Identified

| Pattern | Irene/MeansResearch | DiffSDP | positivstellensatz |
|---------|---------------------|---------|-------------------|
| **Agent pipeline maturity** | Pre-pipeline (mixed) | Full 6-stage with gates | Full 6-stage with gates |
| **Manuscript state** | Frozen, 12pp | Draft, compiles | Written, 26pp, compiles |
| **Blocking item** | None | Zotero citations | Human sign-off |
| **Computational evidence** | Extensive (~50 JSONL) | 6 benchmarks | 3 Python verification scripts |
| **Formal verification** | Not applicable | Lean4 (3 theorems, 2 proven) | SymPy + WolframAlpha cross-check |
| **Relation to others** | Base paper | Extends with diff. stationarity | Extends with §§6–7 Positivstellensatz |
