---
name: dsdp-extension-workflow
description: Extend or modify DSDPRelaxations in the Irene package safely — 7-touch-point method chain, multi-derivation symbol naming, backward-compat patterns, verification workflow.
version: 0.4.0
author: Hermes
metadata:
  hermes:
    tags: [DSDP, Irene, SDP, ADE, differential-algebra, polynomial-optimization]
---

# DSDP Extension Workflow

Extend the `DSDPRelaxations` class in the Irene polynomial optimization framework while
maintaining backward compatibility. Covers adding new constructor kwargs, modifying
derivation/differentiation APIs, updating Groebner-aware ADE relation builders, the
7-touch-point method chain, multi-derivation symbol naming, and propagating changes to
the RST theory documentation. Does NOT cover solver backends (CVXOPT, SDPA) or the
SemigroupAlgebra layer.

## When to Use

- Adding a new kwarg or feature to `DSDPRelaxations.__init__`
- Changing the derivation map storage (e.g. `diff_map` → `diff_maps`)
- Modifying `build_ade_relations`, `differentiate`, `_leibniz_diff`
- Updating KKT injection methods (`_build_diff_kkt_moments`, `_build_kkt_stationarity`)
- Propagating API changes to `DSDPMeanRelaxation` or `DSDPKKTRelaxation`

## Prerequisites

- Irene project at `~/Code/Python/Irene/` with `Irene/` package directory
- `.venv/bin/python3` for non-SageMath DSDP work; sage conda env for SageMath-dependent code
- pytest installed in the active environment

## How to Run

Read the implementation plan (usually in `~/Code/Python/Reports/`) with `read_file`, then
apply changes to `Irene/Irene/dsdp.py` with the `patch` tool. Run the test suite via
`terminal` and verify new features with a `/tmp/hermes-verify-*.py` script.

## Quick Reference

| File | Role |
|---|---|
| `Irene/Irene/dsdp.py` | Primary implementation — `DSDPRelaxations` and subclasses |
| `Irene/Irene/relaxations.py` | Parent class `SDPRelaxations` |
| `Irene/Irene/sdp.py` | SDP solver wrapper |
| `Irene/Irene/base.py` | Base class |
| `Irene/tests/test_dsdp_mean.py` | Test suite (56 tests, 1 pre-existing draft failure) |
| `doc/source/dsdp.rst` | Theory documentation for Sphinx/ReadTheDocs |
| `~/Code/Python/Reports/` | Implementation plans |

## The 7-Touch-Point Method Chain

Every extension touching the derivation pipeline must check all 7 touch points (in call
order). Missing any one creates silent inconsistencies where new parameters are not
forwarded through the full call chain.

| # | Method | Role | What to update |
|---|---|---|---|
| 1 | `__init__` | Registers derivations, initializes state | New kwargs, backward-compat routing |
| 2 | `set_derivation` | Stores a derivation map | New parameters, validation |
| 3 | `build_ade_relations` | Creates derivative symbols + relations | Symbol naming, prefix logic |
| 4 | `differentiate` | Leibniz differentiation | Parameter forwarding to `_leibniz_diff` |
| 5 | `_leibniz_diff` | Core Leibniz rule implementation | Base cases (map lookup, product/power/sum rules) |
| 6 | `_build_diff_kkt_moments` | KKT constraint generation | Parameter forwarding to `differentiate` |
| 7 | `DSDPKKTRelaxation._build_kkt_stationarity` | Lagrangian KKT (subclass) | Same `wrt` forwarding |

Condensed per-method signature changes for a multi-derivation refactor:

```
__init__          → self.diff_maps = {}, route diff_map→diff_maps, accept diff_maps kwarg
set_derivation    → wrt param, store in self.diff_maps[wrt]
build_ade_relations → wrt param, prefix = f"{prefix}{wrt}_"
differentiate     → wrt param, dm = self.diff_maps.get(wrt, {})
_leibniz_diff     → dm param instead of self.diff_map
_build_diff_kkt_moments → wrt param, forwarded to differentiate
DSDPKKTRelaxation._build_kkt_stationarity → wrt param, same pattern
```

## Multi-Derivation Symbol Naming

Architecture change: `self.diff_map = {x:1, y:y}` (single flat dict) →
`self.diff_maps = {'x': {x:1, y:y}, 'y': {y:1, L:v, v:-v**2}}` (dict of dicts).

| Derivation | Prefix | Example |
|---|---|---|
| `D_x` | `dx_` | `dx_x, dx_s, dx_c` |
| `D_y` | `dy_` | `dy_y, dy_L, dy_v` |
| default (wrt=None) | `d_` | `d_x, d_s, d_c` |

Key: `dx_y` ≠ `dy_y` — distinct symbols prevent Groebner cross-contamination.

Backward compatibility:
- `diff_map={x:1, y:y}` → `diff_maps[str(Generators[0])] = {x:1, y:y}`
- `build_ade_relations(dm)` without `wrt` → `d_` prefix (unchanged)
- `differentiate(expr, var)` without `wrt` → `wrt = next(iter(self.diff_maps))`
- `_leibniz_diff(expr, var)` without `dm` → `dm = next(iter(self.diff_maps.values()))`

## Procedure

### 1. Read the plan and all relevant source

```
read_file(path='~/Code/Python/Reports/<plan_file>.md')
read_file(path='~/Code/Python/Irene/Irene/dsdp.py')
read_file(path='~/Code/Python/Irene/tests/test_dsdp_mean.py')
```

### 2. Apply changes incrementally with `patch`

Use `patch` (mode="replace") for each logical change. Order:
constructor → set_derivation → build_ade_relations → differentiate →
_leibniz_diff → KKT methods → subclasses. Check LSP diagnostics after each patch.

### 3. Maintain backward compatibility

When replacing a single-value attribute with a collection, add a compat path:

```python
# Backward compat: single diff_map kwarg → default derivation
raw_diff_map = kwargs.get('diff_map', {})
if raw_diff_map:
    default_wrt = str(self.Generators[0]) if self.Generators else 'x'
    self.set_derivation(raw_diff_map, wrt=default_wrt)
```

Give new parameters a default of `None` that falls through to the old behavior.
Never rename public methods — only add new optional parameters.
When reading an attribute that could be `None` explicitly, guard with `or`:
`order = getattr(self, 'kkt_order', 1) or 1`.

A property `diff_map` is NOT needed if `grep -r "\.diff_map\b"` across the codebase
returns zero external hits.

### 4. Run the test suite after every change batch

```bash
cd ~/Code/Python/Irene && python -m pytest tests/test_dsdp_mean.py -v --tb=short
```

All 55+ committed tests must pass. Use `git stash && pytest && git stash pop`
to isolate pre-existing failures in uncommitted drafts.

### 5. Write a focused smoke test

Exercise every new code path with a short inline script. Verify: backward compat,
new feature, edge case (empty state), subclass integration.

### 6. Update documentation (three layers)

- **Module docstring** (`Irene/dsdp.py` top): theory motivation, 10-15 lines.
- **Class docstring** (`DSDPRelaxations`): math notation, usage examples, parameter docs.
- **`doc/source/dsdp.rst`**: full theory reference with API, holonomic example, ADE table.

Docstrings use `r"""..."""` raw strings with `.. math::` blocks for LaTeX.
Verify RST: balanced backticks, proper section underlines, matching code-block languages.

### 7. Verify with a named temp script and clean up

Create `/tmp/hermes-verify-<feature>.py`. Structure: import → exercise all code paths →
print pass/fail → `sys.exit(0 if failures == 0 else 1)`. Include the test suite as
the last check. `rm` the script after the run.

### 8. Higher-order KKT (when applicable)

```python
order = getattr(self, 'kkt_order', 1) or 1  # guard explicit None
# After first-order diff_term:
higher = diff_term
for _ in range(2, order + 1):
    higher = self.differentiate(higher, sym, wrt=wrt)
    if higher != 0:
        reduced_k = self.ReduceExp(higher)
        constraints.append([reduced_k, 0])
```

For pure polynomial problems with identity derivations, order-N adds N× constraints.
For ADE-lifted systems, kkt_order≥2 causes primal infeasibility because the lifts
only encode first-order differential structure.

### 9. Multi-derivation KKT in `solve()`

The `solve()` method must iterate over all `diff_maps` when `use_diff_kkt=True`:

```python
diff_kkt = []
if self.diff_maps:
    for wrt_key in self.diff_maps:
        diff_kkt.extend(self._build_diff_kkt_moments(wrt=wrt_key))
else:
    diff_kkt = self._build_diff_kkt_moments()
```

This injects D_x(obj)=0 and D_y(obj)=0 as moment constraints without adding
derivative symbols to the generator list — avoiding Groebner explosion entirely.
On P8: 947%→617% (D_x only)→100% (D_x+D_y) gap reduction.

## Verification Checklist

- [ ] Backward compat: `diff_map` kwarg → `diff_maps['x']`
- [ ] Multi: `diff_maps` kwarg → multiple registered derivations
- [ ] `build_ade_relations(wrt='x')` → `dx_` prefix
- [ ] `build_ade_relations(wrt='y')` → `dy_` prefix, no collision
- [ ] `differentiate(expr, var, wrt='x')` → correct diff_map
- [ ] `differentiate(expr, var, wrt='y')` → correct diff_map
- [ ] Product rule: `D_v(u*v) = D_v(u)*v + u*D_v(v)`
- [ ] Sympy fallback when no diff_maps registered
- [ ] `DSDPKKTRelaxation` backward compat with `diff_map`
- [ ] Holonomic round-trip: sin/cos D_x + log D_y

## Pitfalls

- **LSP diagnostics after a partial patch are expected.** They resolve when all
  patches are applied.
- **Don't search for `.diff_map` with `search_files`** — use `terminal` grep instead.
- **`DSDPKKTRelaxation.__init__` handles `diff_map` AFTER `super().__init__`** —
  changes to the constructor must account for this two-phase init.
- **Test `test_10d_kkt_tightening` is an uncommitted draft** — expect 55/56 pass.
- **The `sage` conda env requires `unset CONDA_SHLVL CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_PYTHON_EXE`**
  before `conda run`.
- **Groebner basis explodes past ~14 generators.** Primary remedy: KKT injection
  without derivative generators. Other mitigations: grlex monomial order, polynomial
  shortcuts, minimal algebraic invariants only.
- **Higher-order KKT (kkt_order ≥ 2) causes primal infeasibility on ADE-lifted
  systems.** The ADE lifts (s²+c²=1, y·v=1) only encode first-order differential
  structure. D² on lifted variables doesn't equal the true second derivative.
  Restrict to kkt_order=1 on ADE systems.
- **Use `.venv/bin/python3` for non-SageMath DSDP work** — faster and avoids
  the `unset CONDA_*` dance.
- **Verification scripts must be named `/tmp/hermes-verify-*.py`** — Hermes tracks
  these as canonical evidence. Always `rm` after the run.
- **`.venv` scripts may need `timeout 300`** for heavy SDP solves. Use
  `Parallel=True` for performance.
- **Derivative symbol ordering**: `build_ade_relations` MUST prepend derivative symbols
  to the generator list (they become leading terms in lex-ordered Groebner basis).
  Without this, `ReduceExp()` cannot substitute them back to polynomial expressions.
- **KKT space mismatch**: differentiate ORIGINAL expressions (generator space) before
  Groebner reduction. Differentiating AuxSym-space expressions yields zero (AuxSyms
  are never in `diff_map`).
- **Archimedean boxing**: only box `original_gens`, never derivative symbols. Boxing
  `d_u` produces `1 + u^2 <= B` — a box artifact, not a domain constraint.
- **Parallel scripts**: never run concurrent `Parallel=True` DSDP scripts. They
  compete for CPU cores and produce nondeterministic results.

## Verification

```bash
cd ~/Code/Python/Irene && python -m pytest tests/test_dsdp_mean.py -q --tb=line 2>&1 | grep -E 'passed|failed'
```

Expected: `55 passed, 1 failed` (the pre-existing uncommitted draft). Any other
count indicates a regression.

## Related Skills

- `scientific-coding` — Python experiment patterns in SageMath
- `irene-rewrite-dev` — benchmarking IreneRewrite modules
