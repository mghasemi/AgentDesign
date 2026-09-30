---
name: irene-rewrite-dev
description: "Use when working with the merged Irene package (post-IreneRewrite merge)."
category: software-development
tags: [irene, polynomial-optimization, reduction, benchmarking]
---

# Irene Development (Post-Merge)

**IreneRewrite was merged into Irene on 2026-09-18.** The `rewrite` branch has been deleted, the worktree folder removed, and all features are now in the main `master` branch of `/home/YOUR-USER/Code/Python/Irene/`. All experiments run via `Irene/.venv/bin/python3` (Irene 2.0.0.dev0).

## Trigger

When working with the Irene package — developing modules, running benchmarks, editing Sphinx RST documentation, or debugging relaxation/solver issues.

## Scope Boundary — What Irene Is (and Is Not)

Irene is a **convex-relaxation engine**: SOS/SONC/SDP hierarchies over moment
matrices, plus the quotient-ring, sparsity and Newton-polytope reductions that
shrink them. Judge every proposed feature against that identity before editing
code.

- **Two senses of "decomposition" coexist in the repo; only one is Irene's.**
  `SDPRelaxations.Decompose()` (`relaxations.py`) returns the SOS multipliers
  $\sigma_i$ via a Cholesky factorisation of the Gram blocks, from
  $f-f_*=\sum_i\sigma_i g_i$ — a convex factorisation of an already-solved
  relaxation. It is NOT a Waring / rank / tensor decomposition of a polynomial;
  never extend it to be one.
- **Solution extraction is Lasserre–Henrion, not atom recovery on a variety.**
  `ExtractSolutionLH` takes the moment matrix's SVD, truncates at
  `NumericalRank()`, builds multiplication matrices and reads support points off
  a Schur decomposition. Atoms live in the ambient variable space; there is no
  variety-parameterised variant.
- **Absent from the package entirely:** apolarity / catalecticants, Waring rank,
  rational-variety or Veronese parameterizations, polynomial-system solvers.
  Confirm before assuming:
  `grep -rn -i "apolar\|catalecticant\|veronese\|waring" Irene/*.py` returns
  nothing. A request to "decompose a tensor into powers of forms" is therefore an
  **architecture addition, not a bug fix** — scope it explicitly instead of
  reaching for an existing module.
- **What extends Irene without new theory:** a moment matrix re-indexed by a
  q-graded basis (variety-supported relaxation), the flatness test
  $\operatorname{rank}(H_0)=\operatorname{rank}(H)$ as a pre-extraction guard, and
  Hilbert-function / surjectivity preconditions read off the existing
  `BorderBasis` quotient data. Anything that must *construct* atoms of a
  non-convex decomposition belongs in a sibling project and is imported as a
  reference oracle for cross-validation, not vendored.

For the layered fit-assessment procedure for candidate external methods or
packages, and the worked Irene ↔ Sum2d/BKM boundary, see the
`literature-project-mapping` skill's `references/external-method-fit-assessment.md`.

### Archived Projects
- `Archive/IreneRewrite_20260918/` — pre-merge codebase snapshot (3.4 GB)
- `Archive/MeanDeltaSONC_20260918/` — mean-vs-SONC gap analysis project
- `Archive/IreneComparison_20260918/` — cross-version comparison harness

## Project Layout

```
Irene/
├── Irene/                      ← package (all Rewrite features merged)
│   ├── border_basis.py         ← BorderBasis(variables, generators, degree)
│   ├── sparsity.py             ← CorrelativeSparsity + UnionFind
│   ├── newton_polytope.py      ← NewtonPruner + Minkowski sum
│   ├── relaxation_api.py       ← RelaxationEngine + relax()/compare_all()
│   ├── symbolic_engine.py      ← user-selectable SymEngine/SymPy backend
│   ├── cvxpy_solver.py         ← CVXPY DCP solver layer
│   ├── dsdp.py                 ← DSDP mean relaxation (SymEngine-bridged)
│   ├── nonpopsdp.py            ← Non-POP SDP pipeline
│   ├── relaxations.py          ← main relaxation pipeline
│   └── tests/                  ← per-module test suites
├── doc/                        ← Sphinx RST documentation
│   ├── index.rst               ← master toctree — 6 caption groups
│   ├── optim.rst               ← theoretical foundations (~240 lines)
│   ├── border_basis.rst        ← admissible term-order pivot formalization
│   └── ... (see doc/ for full list)
├── benchmarks/
│   ├── gallery.yaml            ← 12 benchmark problems (5 categories)
│   ├── run_gallery.py          ← full gallery runner
│   ├── results/                ← JSON benchmark output
│   └── archive/                ← obsolete cross-version benchmarks (archived 2026-09-18)
├── .venv/                      ← active venv (Irene 2.0.0.dev0)
└── tests/                      ← integration test suite
```

## Git Layout — Single repo, single branch

`Irene/` is a standalone git repo (`origin = https://github.com/YOUR-GITHUB/Irene.git`,
branch `master`). The former worktree `IreneRewrite/` on branch `rewrite` was merged
and deleted on 2026-09-18.

```bash
cd /home/YOUR-USER/Code/Python/Irene
git add -A && git commit -m "[WIP] ..."
git push https://<PAT>@github.com/YOUR-GITHUB/Irene.git master
```

**PITFALL — Nested git repos in the workspace.** `/home/YOUR-USER/Code/Python/` is NOT a
git repo — it's a directory containing independent repos. Each subproject pushes to
its own GitHub remote. Never `git init` at the parent level.

- SDPA-backed tests regenerate solver scratch files (`out.res`, `prg.dat`,
  `param.sdpa`, `prg.dat-s`) at the repo root; they are tracked but pure noise —
  `git checkout -- out.res prg.dat param.sdpa prg.dat-s` before committing.

**PITFALL — Nested git repos in the workspace.**  `/home/YOUR-USER/Code/Python/`
is NOT a git repo — it's a directory containing independent repos.  The git
layout is:

```
Code/Python/
├── Irene/                    ← main repo (remote: YOUR-GITHUB/Irene.git)
│   └── .git/worktrees/IreneRewrite
├── IreneRewrite/             ← worktree of Irene (branch: rewrite, same remote)
├── positvstellensatz/        ← SEPARATE repo (remote: YOUR-GITHUB/positivstellensatz.git, branch: main)
├── MomentSheaf/              ← SEPARATE repo
├── TinyRAG/                  ← SEPARATE repo
└── ... (no top-level .git)
```

When committing changes in `positvstellensatz/` (DSDP articles, mean polynomial
manuscript, beamer slides), `cd` into that directory and use its own `origin`.
The parent `Code/Python/` directory should never have a `.git` — do not `git init`
there.  Each subproject pushes to its own GitHub remote.

## Symbolic Backend Selection (SymPy ↔ SymEngine)

The `SymbolicEngine` in `Irene/symbolic_engine.py` is user-selectable:

```python
from Irene.symbolic_engine import engine, set_symbolic_backend, get_symbolic_backend
set_symbolic_backend('symengine')   # or 'sympy' / 'auto'
# or env var: IRENE_SYMBOLIC_BACKEND=sympy python3 my_script.py
```

- `symengine` (default when installed) — C++ expand/Matrix/zeros, SymPy fallback for groebner/Poly/lambdify.
- `sympy` — pure SymPy everywhere; no SymEngine objects created.
- `auto` — prefer SymEngine when installed.
- `symengine` is an optional extra (`pip install .[symengine]`); without it the engine auto-runs SymPy.
- **All modules** (relaxations, dsdp, matrices, ...) call through the `engine` singleton, so the switch needs no per-module changes.
- Full suite (169 tests) must pass under BOTH backends — verify with:
  `IRENE_SYMBOLIC_BACKEND=sympy .venv/bin/python3 -m pytest Irene/tests/ tests/ -q`

### Backend benchmark

```bash
cd /home/YOUR-USER/Code/Python/Irene
.venv/bin/python3 benchmarks/benchmark_backends.py --mode irene \
    --output benchmarks/results/backend_irene.json
```

Sections: SOS/SONC/SOSONC, GP, DSDP mean, DSDP KKT, ADE relations, border basis,
sparsity, Newton pruning, symbolic micro-benchmarks, quotient-basis (10 total).
`--sections` accepts a subset.

**Note:** The old 3-mode cross-version benchmark scripts (`compare_irene_vs_rewrite.py`,
`benchmark_backends.py` multi-mode) have been archived to `benchmarks/archive/` since
the rewrite branch no longer exists.

# PITFALL — `AddConstraint` vs `add_constraints`:** `SDPRelaxations` (and DSDP
classes) expose the singular `AddConstraint(expr)` — the plural
`add_constraints([...])` exists only on `OptimizationProblem`. Cross-version
benchmark scripts that call `rlx.add_constraints([...])` fail with
`AttributeError`; use `AddConstraint` on relaxation objects.

**PITFALL — equality constraints go in `relations=`, never as `Mom(g)==0` or
`AddConstraint(Eq)`:** standing user rule (2026-09-26, restated; Sum2d Phase III):
any equality holding identically on the feasible set is passed as a constructor
relation, `SDPRelaxations(gens, relations=[...])`, for exact Groebner quotient
reduction; only genuine inequalities go through `AddConstraint`.

```python
rlx = SDPRelaxations([x, y], relations=[x + y - 1])   # ✓ exact quotient algebra
rlx.AddConstraint(B**2 - x**2 >= 0)                   # ✓ genuine inequality
rlx.MomentConstraint(Mom(x + y - 1) == 0)             # ✗ only E[g]=0, not g≡0
rlx.AddConstraint(sp.Eq(x + y, 1))                    # ✗ two ±ErrorTolerance blocks
```

`Mom`/`MomentConstraint` constrains the moment sequence (a scalar E[g]=rhs, plus
±`ErrorTolerance` for the `eq` branch), not the feasible set — it forgoes the
quotient reduction, so the SDP is larger and looser. Rationale, verified costs and
caveat in `references/sdp_relaxations_pitfalls.md` §5.

**PITFALL — compare constraint encodings by STRUCTURAL ACCOUNTING, not by bound
gaps:** when checking whether an encoding is right (e.g. `relations=` vs
`Mom(g)==0`), do not expect the wrong route to hand you a visibly wrong number.
The moment-matrix PSD already encodes the Jensen / Cauchy–Schwarz inequalities
that hold on the variety, so naive bound-gap probes come out coincidentally
tight; and a degenerate probe model (an objective unbounded below in the
relation-free relaxation) makes `Minimize()` report `Infeasible`, which hides the
effect entirely. Discriminate on `len(rlx.ReducedMonomialBase(2*order))`,
`len(rlx.Constraints)`, `len(rlx.MomConst)`, `rlx.Info['status']`. Ready-made
probe: `scripts/probe_relations_vs_mom.py`.

**PITFALL — `status='Infeasible'` on a quotient-algebra relaxation is
UN-DIAGNOSED, not proof of infeasibility:** a relation-reduced relaxation with a
known feasible point can still come back `Infeasible` at low orders; before
concluding non-feasibility, verify the truncation against an explicit feasible
measure (e.g. the point mass at the known optimum) rather than trusting the
status string.

**PITFALL — pytest `-q` eats the summary line:** in non-tty output the progress
bar uses `\r`, and the final `N passed` summary can be overwritten/lost, so
`grep passed` finds nothing even on a green run. Get definitive counts with
`--junitxml` and parse the XML instead:
```bash
.venv/bin/python3 -m pytest Irene/tests/ tests/ -q --tb=short --junitxml=/tmp/j.xml > /dev/null 2>&1; echo "EXIT=$?"
.venv/bin/python3 -c "import xml.etree.ElementTree as ET; s=ET.parse('/tmp/j.xml').getroot().find('testsuite'); print(s.get('tests'), s.get('failures'), s.get('errors'), s.get('skipped'))"
```

**PITFALL — sparsity `is_sparse` type differs between versions:** original
`CorrelativeSparsity.is_sparse()` is a METHOD; rewrite `CorrelativeSparsity.is_sparse`
is a BOOL ATTRIBUTE (set by `detect_sparsity_from_polys`). Cross-version code must use
`cs.is_sparse if isinstance(cs.is_sparse, bool) else cs.is_sparse()`.

**PITFALL — output paths in benchmark scripts:** `benchmark_backends.py` calls
`os.chdir()` (in `setup_mode`) so `--output` must be resolved to an absolute path
BEFORE the chdir, or files land in `IreneRewrite/IreneRewrite/...`.

### DSDP ADE relations

`DSDPRelaxations.build_ade_relations(diff_map, prefix="d", wrt=None)` was restored in
2026-08-09 (feature-parity audit). Returns `(derivative_syms, relations, new_gens)`
with derivative symbols PREPENDED to the generator list (leading terms in the
lex-ordered Groebner basis). Supports multi-derivation via `wrt=` (e.g. `dy_y`).

### Quotient-Basis Option (Groebner vs BorderBasis) — added 2026-08-09

`RelaxationConfig.quotient_basis` selects the quotient-ring reduction engine used
by `SDPRelaxations.ReduceExp` and `ReducedMonomialBase`:

- `'groebner'` (default): SymPy `sp.reduced` — original Irene behavior.
- `'border'`: `BorderBasis` multiplication-table reduction (numeric, float coefficients).

Env var: `IRENE_QUOTIENT_BASIS=groebner|border` (honoured by `_default_config()` in
`relaxations.py`; also used by `RelaxationEngine`).

```python
from Irene.relaxations import RelaxationConfig, SDPRelaxations
rlx = SDPRelaxations([x, y], relations=[x**2 + y**2 - 1],
                     config=RelaxationConfig(quotient_basis='border'))
```

Benchmark: `benchmark_backends.py` section `quotient_basis` (2 problems × both
modes); results in `benchmarks/results/backend_comparison_report.md` §11. Verified:
circle-relations problem gives identical bound (1.000000) and basis size (5) in
both modes.

**PITFALL — BorderBasis QR pivot tie-break (fixed 2026-08-09):** `BorderBasis._compute_basis`
uses rank-revealing QR with degree-weighted columns; same-degree monomials tied and
scipy picked by column order, which could leave the generator's OWN leading monomial
in the basis (e.g. y² instead of x² for ⟨x²+y²−1⟩), producing wrong quotients and
`reduce()` tables that drop terms. The weights now carry an ascending-lex
perturbation `10^(2·sum) * (1 + eps·lex_rank)` so the lex-larger monomial pivots
first. When the basis looks wrong, verify against theoretical standard monomials
of the truncated quotient.

**PITFALL — BorderBasis can build but be NUMERICALLY WRONG (silent wrong-answer):**
for zero-dimensional ideals with higher-degree complementarity relations — e.g. the
NYZ copositivity ideal ⟨Σx−1, x_i·p_i⟩ with cubic p_i — `BorderBasis` constructs in
seconds yet the QR-pivot basis is inconsistent with the true quotient: `0/N`
relations reduce to zero and `bb.reduce` leaves degree-2k terms unreduced, so the
SDP is garbage. The `_get_border_basis` "reduce all relations to zero" guard does
NOT reliably trip (a basis that *builds* but is *wrong* can pass it). Before
trusting `IRENE_QUOTIENT_BASIS=border` on a new ideal, verify yourself: reduce EVERY
relation and check the residual is ~0, and reduce a degree-2k monomial and confirm it
lands in the quotient basis. Note `SetMonoOrd` always computes the Groebner basis
when `FreeRelations` is set — even in border mode — so border does NOT skip the GB;
it only swaps the per-entry reduction engine.

### NonPOPSDP — ported 2026-08-09 (was the last original-only module)

`Irene/nonpopsdp.py`: Taylor/Chebyshev approximation → POP → `SDPRelaxations`.
API: `taylor_approx`, `chebyshev_approx`, `TranscendentalApproximator`, `NonPOPSDP`,
`NonPOPSDP_Multi`. Functions are referenced by BARE SYMBOLS named after them
(`symbols('sin')`), NOT `sp.sin(x)` — `substitute` replaces `Symbol(name)`.

**PITFALL — original approximation numerics were broken (fixed in port):** the
original Chebyshev extraction (raw FFT scaling) gave maxerr ~61.5 for exp deg-6 on
[-2,2] (true ~5e-4) and had an off-by-one error grid (`fine_t = 2(x-mid)/(b-a) - 1`
maps [a,b] onto [-2,0]); the original Taylor used naive finite differences (err
~1e36 at deg 6). Port uses `numpy.polynomial.chebyshev.chebfit` + `cheb2poly` and a
high-order central stencil with Richardson extrapolation (`_mp_derivative`, mpmath
60 dps). `mpmath.diff` itself is UNRELIABLE for float callables (returns 0.0 for
exp derivatives) — use `_mp_derivative`.

### Phase 3 Reduction Benchmarks

```bash
cd /home/YOUR-USER/Code/Python/Irene
.venv/bin/python3 bench_phase3_reductions.py
```

Output: `benchmarks/results/phase3_benchmarks.json` with four sections:
- `sparsity`: 12 gallery problems (component sizes, reduction factors per degree)
- `newton_pruning`: 12 gallery problems (basis sizes, reduction ratios per relaxation order)
- `border_basis`: 5 test ideals (BB vs Gröbner conditioning, timing)
- `scaling`: 4 synthetic 6-var cases (sparsity rf + Newton reduction combined)

### Newton Pruning API

The correct return keys from `NewtonPruner.moment_matrix_dimension_reduction()`:
```python
{
    'full_basis_size': int,       # all monomials up to max_degree
    'pruned_basis_size': int,     # monomials inside scaled Newton polytope
    'reduction_ratio': float,     # pruned / full
    'matrix_entry_reduction': float,
    'entries_saved': int,
}
```

**Note:** There are NO `full_moment_matrix_size` or `pruned_moment_matrix_size` keys. Compute moment matrix entries manually:
```python
full_mm = n_full * (n_full + 1) // 2    # symmetric matrix entries
pruned_mm = n_pruned * (n_pruned + 1) // 2
```

### Integration helpers

```python
from Irene.sparsity import detect_sparsity_from_polys
from Irene.newton_polytope import prune_basis_from_polys

# Sparsity: pass list of SymPy expressions + number of variables
sp = detect_sparsity_from_polys([x**2 + 1, y**3 - y], num_vars=2)
sp.is_sparse          # bool
sp.components         # list of sets of variable indices
sp.reduction_factor(deg=2)  # float, estimated moment matrix size fraction

# Newton pruning: pass polynomials, variable count, and max degree (usually 2*relaxation_order)
pruner = prune_basis_from_polys([x**4*y**2 + x**2*y**4 + 1 - 3*x**2*y**2],
                                 num_vars=2, max_degree=4)
info = pruner.moment_matrix_dimension_reduction()
```

### Sparsity component structure

`CorrelativeSparsity.components` is a list of **integer sets** (variable indices), not variable-name sets. `summary()` returns `component_sizes` (list of ints) and `component_vars` (list of lists of names). Use `summary()` for report generation, `.components` for programmatic use.

### Border Basis Conditioning

`BorderBasis` computes multiplication tables via iterative generator reduction (not least-squares pseudoinverse). When building conditioning comparison matrices:
- For monomial ideals ($\langle x^2, y^2 \rangle$, $\langle x^3, y^3 \rangle$): multiplication table matrix may be empty/rank-deficient → `cond = inf`. This is **normal** — the border elements reduce cleanly to zero or basis elements.
- For non-monomial ideals ($\langle x^2+y^2-1 \rangle$, $\langle xy-1 \rangle$): tables are well-conditioned ($\kappa \approx 1.0$) at low degrees.
- Real conditioning benefits appear at degree $\geq 6$ with near-singular polynomial systems — not visible at low-degree test ideals.

## Documentation Editing (Sphinx RST)

The `doc/` directory contains 29 RST files structured as a Sphinx manual with 6
toctree caption groups.  When editing RST files, follow these patterns.

### RST Editing Pitfalls

**PITFALL — `patch` on partially-read files.** If a file was previously read with
`read_file(offset=N, limit=M)` (partial view), the `patch` tool's fuzzy matching
may fail with "Could not find a match for old_string" even when the content is
correct. **Fix:** re-read the full file with `read_file(limit=2000)` (no offset)
before attempting any patch.  For very large replacements (100+ lines), prefer
`write_file` over `patch`.

**PITFALL — RST math escaping.** Inside `.. math::` blocks and `:math:` roles,
backslashes must be doubled compared to LaTeX: use `\\` for control sequences,
`\\\\` for literal backslashes.  Inline `:math:` roles inside table cells and
admonitions are particularly sensitive.

**PITFALL — RST table formatting.** `.. list-table::` directives need explicit
column widths (`:widths:`), a `:header-rows: 1` line, and blank lines between
the directive header and the `* -` row entries.

**PITFALL — Prefer `.. list-table::` over grid/simple tables.** Grid tables
(`+----+----+`) and simple tables (`===` / `---` rules) require every column to
line up to the exact character width, which hand-counting and `patch`-based
edits get wrong (a single misaligned `+` or a data row that is 1 char short
breaks the whole table, and a naive "detect the table end" regex often stops at
the first data row, leaving a malformed table with a second table spliced
inside it). If you must generate a grid table, compute the column widths
programmatically from the widest cell per column — never by eye. When in doubt,
use `.. list-table::` with `:widths:`; it is alignment-free and robust to edits.

**PITFALL — Section underlines must be at least as long as the title.** A
section heading's underline (`===`, `---`, `**`, etc.) must be at least as long
as the title text, or docutils/Sphinx raises a `Title overline / underline too
short` error. When you rename or lengthen a section title, re-lengthen the
underline to match (programmatically: `underline = '=' * len(title)`).

**PITFALL — `sphinxcontrib.theorem` is NOT installed in IreneRewrite's `doc/`.**
`doc/conf.py` does not list it in `extensions` and it is not importable in the
venv, so `.. theorem::` / `.. definition::` / `.. proposition::` directives will
break the Sphinx build. The existing docs state theorems as a **plain
subsection heading + a bold one-line statement** (e.g. "Two-Stage Hybrid
Monoid-Graph Reduction Theorem"). Match that style — never introduce a
`.. theorem::` directive. Before using any non-core directive, grep `doc/` for
prior usage and check `doc/conf.py` `extensions`.

**PITFALL — Source vs. PDF rendering artifacts.** When a reviewer or user reports
errors in the compiled PDF (garbled formulas, missing symbols, \"pnined\" for
\"pruned\", \"771\" for Σ, minus signs disappearing in code), the RST source files
are almost always correct.  The Sphinx → LaTeX → pdflatex pipeline introduces
rendering artifacts:\n
- Sans-serif admonition fonts can ligature \"ru\" into \"ni\" (so
  ``\\text{pruned}`` renders as \"pnined\" in theorem boxes)\n
- Unicode math symbols (≥, ≤, ⪰, ·, ∩, ⊆) in literal/code blocks crash pdflatex\n
- Verbatim code-to-LaTeX conversion can drop minus signs, substitute quotes, and
  garble multiplicative operators\n
- Greek letters and special operators (Σ, Δ, ≺) may be substituted by font
  encoding fallback characters\n
- Math-mode constructs in ``.. admonition::`` boxes use a different font than
  normal math, amping rendering differences\n

**Diagnosis workflow:** (1) read_file the RST source to confirm it's correct;
(2) check what rendered with `pdftotext -f N -l N IreneRewrite.pdf -` (pymupdf
is NOT installed in the venv — see "Building the PDF"); (3) if source is
correct
but PDF is wrong, the issue is a pipeline artifact — do NOT modify the RST.
Fix pipeline issues via `conf.py` preamble (add `lmodern`, `textcomp`, `upquote`
to `latex_elements['preamble']` — see `references/sphinx_pdf_artifacts.md` for the
full recipe and why xelatex/lualatex were attempted but didn't work on this system).
Do NOT modify correct RST source to work around LaTeX rendering quirks.

### Building the PDF

```bash
cd /home/YOUR-USER/Code/Python/IreneRewrite/doc
make latexpdf   # runs sphinx-build → pdflatex (3 passes via latexmk)
# Output: doc/_build/latex/IreneRewrite.pdf
# Copy to doc root for easy access:
cp _build/latex/IreneRewrite.pdf IreneRewrite.pdf
```

The build produces one file `_build/latex/IreneRewrite.pdf` (typically
170–200 pages).  The existing `Irene.pdf` in `doc/` is a legacy snapshot;
`IreneRewrite.pdf` is the current build output.

**PITFALL — pymupdf is NOT installed in IreneRewrite's venv.** `import pymupdf`
fails in `.venv` (and in the system python), so do not rely on `fitz` for
verification. Use poppler-utils (available at /usr/bin):

```bash
pdfinfo IreneRewrite.pdf | grep -E "Pages|Page size"
pdftotext IreneRewrite.pdf - | grep -n "<section title>"   # locate a section
pdftotext -f 108 -l 108 IreneRewrite.pdf - | head -30      # dump one page
```

**PITFALL — TOC page numbers are PRINTED page numbers, not physical PDF pages.**
Front matter (title, TOC, ...) offsets the two by ~6 pages: a TOC entry
"p. 102" lands on physical PDF page 108. To confirm a TOC entry is correct,
check the printed page number in the page footer —
`pdftotext -f N -l N IreneRewrite.pdf - | grep -E "^[0-9]+$"` — not the
physical index. Do not "fix" a TOC/body mismatch that is just this offset.

**Clean rebuild:** inside `doc/_build/latex/`, run
`latexmk -C IreneRewrite && latexmk -pdf -interaction=nonstopmode IreneRewrite.tex`
(latexmk is at /usr/bin/latexmk; the Makefile's `latexpdf` target uses it when
present). Running bare `pdflatex` by hand does not converge cross-references
the way latexmk does.

### Key documentation chapters and their content

| File | Content | Notable sections added |
|---|---|---|
| `index.rst` | Master toctree, 6 caption groups | Restructured 2026-08: Transcendental & Differential Algebraic Optimization group |
| `migration.rst` | Legacy → modern API mapping (created 2026-08) | Complete table-driven mapping |
| `optim.rst` | Theoretical foundations (~240 lines) | Stripped of legacy code; now theory-only with modern API quick reference |
| `algebra.rst` | Group-ring foundations + Lie prolongations | Formal multi-derivation operator semigroup Θ |
| `border_basis.rst` | Border basis theory + admissible term orders | Formal QR pivot weight scheme w_α |
| `sparsity.rst` | Correlative sparsity + UnionFind | — |
| `newton_polytope.rst` | Newton polytope pruning | — |
| `relaxation_api.rst` | RelaxationEngine + RelaxationConfig | Two-Stage Hybrid Reduction Theorem |
| `cvxpy_solver.rst` | CVXPY solver layer | Putinar duality guide + tolerance parameter table |
| `dsdp_mean.rst` | Differential SDP and mean relaxations | CGIK framework, Archimedean boxing, Stochel's theorem |
| `nonpopsdp.rst` | Non-POP SDP (Taylor/Chebyshev surrogates) | Port documentation with numerical fix notes |
| `appendix.rst` | Global Notation Index (22 symbols) + pyOpt reference | Notation table added 2026-08 |
| `code.rst` | Autodoc + doctest integration guide | Doctest setup instructions added 2026-08 |

### Verifying RST changes

RST syntax errors surface at Sphinx build time. A bare `publish_doctree`
one-liner **fails on `.. math::` blocks** (the `math` role/directive is not
registered outside Sphinx), so it is useless for any file containing math. Use
this harness instead — it registers a stub `math` directive, parses, and
reports only *real* errors (filtering the stub's own "no content permitted"
false positives) and the table count:

```python
import docutils.core
from docutils.parsers.rst import directives
from docutils import nodes

def math_directive(name, arguments, options, content, lineno,
                   content_block, block_text, state, state_machine):
    return [nodes.literal_block('')]
directives.register_directive('math', math_directive)

src = open('doc/<file>.rst').read()
doc = docutils.core.publish_doctree(
    src, settings_overrides={'report_level': 1, 'halt_level': 5})
real_err, warns = [], []
for node in doc.findall(nodes.system_message):
    sev = node.get('level', 0)
    txt = node.astext().strip()
    if 'no content permitted' in txt:      # stub-math false positive
        continue
    (real_err if sev >= 30 else warns).append(txt)
print('real_errors=%d non_math_warnings=%d tables=%d' %
      (len(real_err), len(warns), len(list(doc.findall(nodes.table)))))
```

Run it with the venv interpreter:
`.venv/bin/python3 -c "<paste the block above, with the file path filled in>" 2>/dev/null`

A clean file reports `real_errors=0 non_math_warnings=0` with `tables=N`
matching the number of tables you expect. If `real_errors>0`, the message text
names the line. Full Sphinx build (requires `make html` in `doc/` with a
configured `conf.py`) is the authoritative check.

### Standalone DSDP article

The companion journal article synthesizing all DSDP experimental reports lives
at `../positivstellensatz/dsdp_synthesis_article.tex` (11 pages, 19 bib entries,
`amsart` class).  It covers the ADE lifting principle, CGIK framework, two-stage
hybrid reduction, dual-ADE encoding, rational parameterization, and the three
convergence regimes.  Commit/push from the `positivstellensatz/` repo (separate
remote: `YOUR-GITHUB/positivstellensatz.git`, branch `main`).

To rebuild: `cd ../positivstellensatz && pdflatex dsdp_synthesis_article.tex`
(3 passes).

## Pitfalls

### Newton Polytope Pitfalls — ✅ FIXED (2026-08-08)

Two bugs discovered and fixed in this session. Full details: `references/newton_polytope_pitfalls.md`.

1. **Origin bug (Choi-Lam → empty basis):** `combined_newton_polytope()` now always includes $(0,\ldots,0)$ before scaling. Added empty-basis safety guard in `compute_pruned_basis()`.

2. **Minkowski sum dimension mismatch (chain/star crash):** `prune_basis_from_polys()` now passes canonical `vars_list=symbols('x0:n')` through to `combined_newton_polytope()`.

### Benchmarks Require IreneRewrite Venv

All benchmarks and tests MUST use `/home/YOUR-USER/Code/Python/IreneRewrite/.venv/bin/python3`. The sandbox interpreter (`execute_code`) has incompatible NumPy/SymPy versions and cannot import Irene modules.

### SymEngine Overhead: Full Diagnosis + Fixes — RESOLVED (2026-08-08)

IreneRewrite migrated to SymEngine expecting speed gains but was 15% slower.
Instrumented trace revealed the root cause and three solution classes were applied.

**Root cause**: 99% of `symbolic_engine` calls in `relaxations.py` are `Poly`, `groebner`,
`reduced`, `sympify` — all of which ALWAYS fall back to SymPy because SymEngine lacks
the full Poly API (`.as_dict()`, `.total_degree()`, Groebner basis). Meanwhile
`engine.expand()` (SymEngine's actual strength) is only 2 of 87 calls.

**Instrumented trace** (Motzkin SOS order 1):
- `engine.Poly()`: 255 calls, 35 ms — 99% of engine time, all SymPy fallback
- `engine.expand()`: 2 calls, 3 µs — SymEngine native (negligible)
- `to_sympy()` conversions: 704 calls, 3.15 ms
- Original Irene comparison: 154 `sp.Poly()` calls at 98 µs/call = 15 ms

**Fixes applied** (all three, cumulative impact: 8.50s → 7.36s, closing 87% of gap):

| # | Solution | Files Changed | Impact | Pros | Cons |
|---|----------|--------------|--------|------|------|
| 1 | `to_sympy()` short-circuit | `symbolic_engine.py:36` | −86% conversions | One-liner, safe, eliminates redundant tree walks | Doesn't fix Poly dispatch overhead |
| 2 | SymPy generators (not SymEngine) | `relaxations.py:217,266` | Eliminates per-call gen conversion | Prevents the root cause (SymEngine objects entering hot path) | None — generators carry no benefit as SymEngine |
| A | CVXOPT native solver (bypass CLARABEL) | `sdp.py:599` | Fixes infeasibility + ~0.5s timing | Restores correct SOS behavior, matches original Irene | Loses CVXPY abstraction for CVXOPT backend |
| B | `_poly()` helper (bypass `engine.Poly()`) | `relaxations.py:27-39`, 21 call sites | Eliminates 40% per-call overhead + dispatch | Direct `sp.Poly()` — same as original Irene | Loses automatic SymEngine→SymPy conversion (safety wrapper retained) |
| B.1 | Infeasibility check before primal guard | `relaxation_api.py:259` | Restores `infeasible` status for non-SOS polys | Critical for Mean Polynomial workflow | None |

**Final benchmark** (3-run avg): IreneRewrite 7.36s, Original Irene 7.09s, gap +3.8%.

Full profiling scripts: `benchmarks/profile_symengine_overhead.py` (micro-benchmarks)
and `benchmarks/instrument_relaxation_v2.py` (call-count trace).
Methodology writeup: `references/symengine_overhead_profiling.md`.

### CLARABEL vs CVXOPT Infeasibility Detection — FIXED (2026-08-08)

IreneRewrite originally routed CVXOPT solver requests through CLARABEL (via CVXPY),
which interprets primal-infeasible SDPs differently: CLARABEL returns finite weak
bounds (−526, −10.4, −79.7) with status `optimal` for non-SOS polynomials, while
CVXOPT correctly reports `infeasible`. This is critical for the Mean Polynomial
workflow which relies on infeasibility to distinguish SOS from non-SOS forms.

**Fix** (`sdp.py:599`): `_cvxpy_solve()` now returns `False` for CVXOPT/DSDP solver
names, falling through to the legacy `CvxOpt()` path which uses CVXOPT's native
C interface. This restores identical behavior to the original Irene.

**Additional fix** (`relaxation_api.py:259`): Infeasibility check moved BEFORE the
`primal_val is None` guard. CVXOPT may return `None` primal for infeasible SDPs;
checking the status string first catches infeasibility instead of raising a generic
`RuntimeError`.

Post-fix: Motzkin, Choi-Lam, Schick all correctly report SOS `infeasible`.

### Groebner LM() Access Pattern — CORRECTED 2026-09-27 (the basis does NOT carry the order)

`GB.polys[i].order` is **None** (defaults to **lex**) even when the GroebnerBasis
was computed under grevlex — the per-poly `Poly` objects do NOT inherit the basis's
monomial order. So `GB.polys[i].monoms()[0]` is the **lex** leading monomial, NOT the
basis's (grevlex/grlex) leading monomial. The correct grevlex LM is computed by
hand from the exponent dict:

```python
d = GB.polys[i].as_dict()
# grevlex: max by (total degree, then reverse-lex with smaller LAST-variable exp larger)
lm_exp = max(d.keys(), key=lambda e: (sum(e), tuple(-v for v in reversed(e))))
lc     = d[lm_exp]
```
`Poly(g, *vars).LM()` and `as_dict()` use the DEFAULT **lex** order, so they are also
lex — never trust them for a non-lex basis.

### `engine.reduced` reduces under LEX regardless of the GB order — a real correctness bug

`symbolic_engine.py:281–285` does `sp_gb = [to_sympy(g) for g in groebner_basis]`
then `sp.reduced(sp_expr, sp_gb)`. Iterating a `GroebnerBasis` yields `Poly`s with
`order=None` → `sp.reduced` reads **lex** leading monomials even when the basis was
computed under **grevlex** (`SetMonoOrd('grevlex')`). Lex-reduction of a grevlex-GB
is NOT a valid quotient map: it fails to annihilate the ideal's generators (measured
6/8 relations annihilated vs 8/8 for a grevlex-consistent reducer on the NYZ
copositivity ideal), and it is the source of the degree-6→degree-15 normal-form term
blow-up that makes `InitSDP` crawl. Passing the `GroebnerBasis` object directly to
`sp.reduced` does NOT fix it (still lex — `order=None` on the stored polys).

**Verify ANY quotient reducer (library or hand-rolled) against the three quotient-map
axioms before trusting its SDP values:** (1) NF(relation)=0 for every generator
relation; (2) idempotence NF(NF(m))=NF(m); (3) ring-hom
NF(x_i·NF(m))=NF(x_i·m). A reducer that merely *matches `sp.reduced` output* is
proving it reproduced the same lex-vs-grevlex bug, not that it is correct.

**Fast exact reducer (the fix):** index the monic GB by grevlex-LM, memoize
`nf(exp)` (peel one LM division, subtract the monic GB element's non-LM tail,
recursively reduce each shifted tail monomial through a `nf_cache`), precompute every
deg-≤2k monomial's normal form ONCE, and prebuild SymPy `Expr` objects in an
`expr_cache` so `ReduceExp` is an O(1) `Rational(coeff)*expr_of(exp)` lookup. For the
7-var NYZ ideal this turns 7260 reductions from ~9h into ~16s of precompute.

### GB normal-form reduction cost — term count, not coefficient magnitude

`engine.reduced` (pure SymPy, no SymEngine fast path) reduces one monomial against
the whole basis per call, and the moment-matrix build calls `ReduceExp` once per
upper-triangular entry — O(basis²) calls at order k. When `InitSDP` hangs, measure
the per-monomial cost FIRST, before blaming the SDP solver:

- A non-reduced GB carries ~10¹⁴-coefficient degree-6 elements. Forcing
  `domain=QQ`/`field=True` collapses them to ~200 but does NOT speed up `sp.reduced`
  — the cost is the **number of terms in the normal forms** (~269 at degree 4 for a
  7-var copositivity ideal), not big-integer arithmetic.
- The fix is to share work: precompute each distinct monomial's normal form ONCE and
  look it up, or build a true multiplication-table (quotient-algebra) reducer. Naive
  memoization over degree-≤d monomials does NOT help — reducing a degree-d monomial
  spawns degree-(d+1)+ intermediates that miss the cache.
- SymPy API facts: `sp.groebner` has NO `reduced=` kwarg (`OptionError`);
  `GroebnerBasis.reduce(expr)` reduces an *expression* against the basis, it does not
  self-reduce the basis.

## SONC Membership Testing (via IreneRewrite)

Testing whether a polynomial is SONC requires converting from SymPy to Irene's
`SemigroupAlgebra` → `OptimizationProblem` → `SONCRelaxations`. Two critical
pitfalls govern this conversion.

### PITFALL — `SemigroupAlgebra` is NOT callable

`SemigroupAlgebra` has `__getitem__` (`SA['x']`) but NOT `__call__`. Do NOT write
`SA(0)` or `SA(coeff)` — it raises `'SemigroupAlgebra' object is not callable`.
Instead, use Python's built-in arithmetic on `AtomicSGElement` objects:

```python
SA = SemigroupAlgebra(SG)
# ✓ correct
x_sa = SA['x']
term = 2.0 * (x_sa ** 3)                # 2.0 * x^3 → SemigroupAlgebraElement
result = 2.0 * x_sa**4 + (-3.0) * x_sa**2 + 1.0

# ✗ wrong
SA(0)                                    # TypeError: not callable
SA(float(coeff))                         # TypeError: not callable
```

### PITFALL — SymPy `.subs()` breaks on AtomicSGElement

Using `sympy_expr.subs({sympy_symbol: sa_element})` triggers a chain of
`sympy.Pow.__new__` → `sympify()` calls on `AtomicSGElement`, raising
`SympifyError`. The correct approach extracts monomials from `Poly.as_dict()`
and builds `SemigroupAlgebraElement` terms directly:

```python
from sympy import Poly, expand

def sympy_to_sa(expr, var_symbols, SA, var_names):
    """Convert sympy polynomial → SemigroupAlgebraElement."""
    poly = Poly(expand(expr), *var_symbols)
    result = None
    for monom, coeff in poly.as_dict().items():
        mono_term = float(coeff)
        for var_idx, exp in enumerate(monom):
            if exp > 0:
                mono_term = mono_term * (SA[var_names[var_idx]] ** exp)
        result = mono_term if result is None else result + mono_term
    return result if result is not None else 0.0
```

Full recipe with `OptimizationProblem` construction in `references/mean_delta_sonc.md`.

### SONC Feasibility vs Membership

`SONCRelaxations.solve()` returns a lower bound. When interpreting results:

| GP Status | Lower bound | Interpretation |
|-----------|-------------|----------------|
| Feasible | lb ≥ 0 | Strong evidence polynomial IS SONC (certificate proves nonnegativity) |
| Feasible | lb < 0 | SONC certificate found but loose; does NOT prove non-SONC |
| Infeasible | — | Strong evidence polynomial is NOT SONC, BUT rule out AM-GM boundary false negative first (see `references/mean_delta_sonc.md`) |
| Solver error | — | Indeterminate — numerical issue, not proof of non-SONC |

For gap analysis (showing a polynomial is nonnegative but not SONC), prefer
GP-infeasible cases **after ruling out** the AM-GM boundary pitfall.
Solver-error cases may be genuine gaps masked by numerical issues; try simpler
(q,p) pairs or lower-degree monomials first.

## Mean Polynomial Development (MeanDeltaSONC)

**Project archived to `Archive/MeanDeltaSONC_20260918/` on 2026-09-18.**
See `references/mean_delta_sonc.md` for full findings.

### Normalization Bug in `DSDPMeanRelaxation._build_mean_pair()`

At `Irene/dsdp.py:358-405`, `_build_mean_pair()` originally computed the
**unnormalized** form — $(∑ w_i y_i^q)^{c/q} - (∑ w_i y_i^p)^{c/p}$ — which
can be negative, violating the power-mean inequality.

Two iterations were needed to get the fix right:

1. **First attempt (wrong)**: applied separate $W^{c-c/q}$ and $W^{c-c/p}$ factors
   to Q and P, over-scaling by $W^c$. User caught this: coefficients were 256× too large.

2. **Correct fix**: multiply the power-mean inequality by $W^{\max(c/q, c/p)} = W^{c/p}$
   (since $q>p \implies c/q < c/p$). Only Q gets a $W$ factor:

   $$M_{q,p} = W^{\,c/p - c/q}\!\left(\sum w_i y_i^q\right)^{\!c/q}
             - \left(\sum w_i y_i^p\right)^{\!c/p}$$

   This is the **minimal** integer-coefficient polynomial that is provably
   nonnegative. The $p=0$ case (P=1) is left unchanged.

Full derivation and verification in `references/mean_delta_sonc.md`.

### Key Gap Finding

**$M_{4,2}((x,x^3),(1,1))$ IS a circuit polynomial** (AM-GM holds with equality).
The earlier SONC-GP infeasibility was a false negative at the AM-GM boundary
(see `references/mean_delta_sonc.md`).

**Genuine gap candidates**: $M_{q,q-1}((x,y),(1,1))$ for $q \geq 3$ — SONC GP
reports infeasible. All exponents are collinear ($e_x+e_y = \deg$), so the Newton
polytope is 1-dimensional. A 2D circuit requires 3 affinely independent vertices
(a triangle) — impossible with collinear support. Any SONC decomposition would
need off-line "lifting vertices" whose positive coefficients cannot cancel. This
is the **collinear-support non-SONC theorem** (proved via SageMath; see
`references/mean_delta_sonc.md` §3).

**Sweep results** ($M_{q,q-1}((x,y),(1,1))$, uniform weights):

| $q$ | deg | terms | Globally NN? | SOS? | SONC? | Mechanism |
|-----|-----|-------|-------------|------|-------|-----------|
| 2 | 2 | 3 | ✓ | ✓ | ✓ | $(x-y)^2$, single circuit |
| 3 | 6 | 5 | ✗ | ✗ | ✗ | Not globally NN ($c/p$ odd) |
| 4 | 12 | 7 | ✓ | ✓ | ✗ | Collinear support, SOS by Hilbert |
| 5 | 20 | 9 | ✗ | ✗ | ✗ | Not globally NN |
| 6 | 30 | 11 | ✓ | ✓ | ✗ | Collinear support, SOS by Hilbert |

**Global nonnegativity condition**: $M_{q,q-1}$ is globally NN iff $q$ is even
(so $c/p = q$ is even, making the $P$-term a perfect $q$-th power with even
outer exponent). When $q$ is odd, $M_{q,q-1}$ is only NN on $\mathbb{R}_{\geq 0}^n$.

### Mean-SOS Conjecture (2026-08-11)

**Computational evidence**: $M_{q,q-1}(x_1,\ldots,x_n)$ with even $q$ is SOS for
all tested configurations — 3-var up to $q=8$, 4-var $q=4$, non-uniform weights
$(1,2,3)$ through $(1,10,1)$. All SDP relaxations are feasible at order
$\lceil \deg/2 \rceil$ with gap $< 10^{-8}$.

**Proof sketch** (see `references/mean_delta_sonc.md` §5):

1. **$q=2$ (proved)**: $M_{2,1} = \sum_{i<j} w_i w_j (x_i-x_j)^2$, explicit SOS.
2. **$n=2$ (proved)**: $M_{q,q-1}$ is a nonnegative binary form → SOS by Hilbert.
3. **$n \geq 3$ (conjectured)**: Decompose as $\sum_{i<j} w_i w_j (x_i^{q-1}-x_j^{q-1})^2 \cdot R_{ij}$
   where each $R_{ij}$ is SOS. This reduces the general case to the bivariate case.

The unique gap is Lemma 2 (pairwise decomposition for $n \geq 3$).
In 2 variables, PSD = SOS (Hilbert), so PSD-but-not-SOS mean polynomials
cannot exist in 2 vars — the search must use $\geq 3$ variables.

## Verification

After any change to `symbolic_engine.py`, `relaxations.py`, `sdp.py`, or `relaxation_api.py`:

```bash
cd /home/YOUR-USER/Code/Python/Irene

# 1. Unit tests (80 must pass — includes 23 symbolic_engine backend tests)
.venv/bin/python3 -m pytest Irene/tests/ -q

# 2. Full integration test suite (169 must pass)
.venv/bin/python3 -m pytest Irene/tests/ tests/ -q --junitxml=/tmp/j.xml > /dev/null 2>&1
.venv/bin/python3 -c "import xml.etree.ElementTree as ET; s=ET.parse('/tmp/j.xml').getroot().find('testsuite'); print(s.get('tests'), s.get('failures'), s.get('errors'), s.get('skipped'))"

# 3. CI solver modes (simulate GitHub Actions matrix)
IRENE_CI_SOLVER=CLARABEL .venv/bin/python3 -m pytest tests/test_solver_routing.py -q
IRENE_CI_SOLVER=SCS .venv/bin/python3 -m pytest tests/test_solver_routing.py -q
# Expected: 9 passed for each

# 4. Benchmark gallery quick-mode
.venv/bin/python3 benchmarks/run_gallery.py --quick --timeout 120 --output-dir benchmarks/results/
# Expected: BENCHMARK SUMMARY with 3-4 passed
```

**PITFALL — pytest `-q` eats the summary line:** in non-tty output the progress bar uses `\r`, and the final `N passed` summary can be overwritten/lost. Get definitive counts via `--junitxml` and parse the XML.

### CI-Specific Verification

After solver routing changes, tests may fail under CI that pass locally because
the CI matrix exercises different solver backends via `IRENE_CI_SOLVER`. Always
run the CI-simulated modes above (step 3). For the full CI fix pattern covering
solver-name assertion updates, convergence-sensitive test pinning, and env-var
wiring, see `references/ci_fix_pattern.md`.

## References

- `references/feature_parity_audit.md` — full Irene-vs-IreneRewrite parity audit methodology: api_inventory diff, `__init__.py` export check, examples cross-version trap, docs audit, serialized 3-mode benchmarking (2026-08-09)
- `references/phase3_benchmark_results.md` — Detailed benchmark results from P3.6 run (2026-08-08)
- `references/newton_polytope_pitfalls.md` — Origin bug and Minkowski sum fixes
- `references/cross_version_comparison.md` — Irene vs IreneRewrite comparison recipe, known findings, and verification pattern (2026-08-08)
- `references/symengine_overhead_profiling.md` — Full instrumented-trace methodology, micro-benchmarks, and root cause analysis (2026-08-08)
- `references/ci_fix_pattern.md` — CI fix pattern for solver-routing-related test failures: solver-name assertions, convergence-sensitive test pinning, IRENE_CI_SOLVER fixture wiring (2026-08-08)
- `references/sphinx_pdf_artifacts.md` — Catalog of Sphinx → LaTeX → PDF rendering artifacts: font ligatures, Unicode substitution, verbatim code corruption, and diagnostic workflow (2026-08-09)
- `references/mean_delta_sonc.md` — MeanDeltaSONC project: normalization bug in DSDPMeanRelaxation, SONC membership testing patterns, gap examples (2026-08-11)
- `references/sdpa_file_format.md` — SDPA direct file format conventions, ncpol2sdpa quirks, and cross-solver comparison patterns for Irene/ncpol/reference solvers
- `scripts/probe_relations_vs_mom.py` — deterministic probe comparing `relations=` against `MomentConstraint(Mom(g)==0)` by structural accounting (basis size, localizing blocks, status); run with `Irene/.venv/bin/python3`
