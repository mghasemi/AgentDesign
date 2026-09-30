# Feature-Parity Audit: Original Irene vs IreneRewrite

Methodology used 2026-08-09 to answer "no feature from Irene is missing in the
IreneRewrite" — reusable whenever the two trees diverge further or a new phase
lands.

## 1. Module inventory (fast triage)

```bash
ls Irene/Irene/          # original modules
ls IreneRewrite/Irene/   # rewrite modules
```

Then classify every original module:
- **present with same name** → API diff (step 2)
- **renamed** (e.g. `correlative_sparsity.py` → `sparsity.py`) → functional diff
- **missing** (`nonpopsdp.py`, `unified_reductions.py`) → gap; check whether
  functionality was superseded by a rewrite module before declaring a gap
  (`unified_reductions.py` was superseded by `relaxation_api.py` +
  `sparsity.py` + `newton_polytope.py` + `border_basis.py`; `nonpopsdp.py` was a
  real gap).

## 2. API inventory diff (systematic)

`benchmarks/api_inventory.py` introspects a package in ITS OWN venv and dumps
every public class/function + method signatures to JSON:

```bash
Irene/.venv/bin/python3 IreneRewrite/benchmarks/api_inventory.py Irene/  results/api_original.json
IreneRewrite/.venv/bin/python3 IreneRewrite/benchmarks/api_inventory.py IreneRewrite/ results/api_rewrite.json
```

Diff programmatically: missing/new classes per module, missing/new functions,
then **method-level diff on shared classes** (the big find: `build_ade_relations`
was missing from all three DSDP classes in the rewrite).

## 3. Top-level export parity — easy to miss

Module presence is not enough. Compare `Irene/__init__.py` re-exports: the
rewrite had `DSDPRelaxations/DSDPMeanRelaxation/DSDPKKTRelaxation` importable
from `Irene.dsdp` but NOT re-exported at top level (original exported them).
`from Irene import DSDPRelaxations` is a user-visible API surface — check it.

## 4. Examples: byte-identical is NOT "up-to-date"

- `diff -rq Irene/examples IreneRewrite/examples` returned identical — but the
  rewrite docs pointed at `benchmarks/*.py` paths that don't exist (scripts live
  in `examples/`). Docs must be audited against the actual tree.
- **Cross-version trap:** examples hardcode
  `sys.path.append(os.path.join(os.path.dirname(__file__), '..'))`, so running
  `Irene/.venv/bin/python3 IreneRewrite/examples/X.py` silently runs the REWRITE
  code. To test the original, run the original tree's own copy:
  `Irene/.venv/bin/python3 Irene/examples/X.py`.
- Distinguish environment failures (Example01 requests CSDP binary not installed)
  and pre-existing example bugs (Rosenbrock calls undefined `minimize_constrained`)
  from rewrite regressions — verify by running the original's copy first.

## 5. Docs audit

- README.rst was byte-identical to the original ("depends on SymPy") — stale
  after the SymEngine migration.
- Check every `automodule::` / `:mod:` reference resolves to a real module, and
  every path in examples/tutorial pages matches the tree.

## 6. Benchmark for the comparison

`benchmarks/benchmark_backends.py` runs 10 feature sections (incl. the
`quotient_basis` Groebner-vs-BorderBasis section) in 3 modes
(original / rewrite-symengine / rewrite-sympy); `compare_backends_report.py`
emits the markdown report.

- **Serialize the modes** — concurrent runs skew wall-clock timings (killed a
  concurrent run mid-session for rigor).
- Resolve `--output` to an absolute path BEFORE the script's `os.chdir()`
  (setup_mode), or files land in `IreneRewrite/IreneRewrite/...`.
- The `@timed` decorator injects `elapsed_s`/`status` keys into section dicts —
  report generators must filter those keys when iterating "problems".
- Mode-adaptive APIs differ (original `BorderBasis(polynomials, variables,
  max_degree)` vs rewrite `BorderBasis(variables, generators, degree)`) — use
  each tree's own API and note the difference in the report, don't force one call
  shape.

## 7. Closing small gaps is cheaper than porting

- `build_ade_relations` was restored with a faithful port (~40 lines) + docstring
  example from the original, plus `__init__.py` exports — both high-value, low
  risk.
- Document remaining API-shape differences (border-basis `roots/dimension`,
  sparsity chordal-cliques vs UnionFind) rather than porting 17 KB modules
  unrequested; leave the big port (`nonpopsdp.py`) as a recommendation.
