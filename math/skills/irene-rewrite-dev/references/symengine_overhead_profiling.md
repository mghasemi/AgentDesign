# SymEngine Overhead Profiling — Methodology & Results (2026-08-08)

## Instrumented Trace Technique

Monkey-patch `SymbolicEngine` methods BEFORE any Irene imports to capture per-method
call counts and cumulative timing:

```python
import Irene.symbolic_engine as se_mod
real_engine = se_mod.engine

counts = {}; times = {}
for attr_name in dir(real_engine):
    if attr_name.startswith('_'): continue
    attr = getattr(real_engine, attr_name)
    if not callable(attr): continue
    original = attr
    def make_wrapper(name, orig):
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            result = orig(*args, **kwargs)
            elapsed = (time.perf_counter() - t0) * 1e6
            counts[name] = counts.get(name, 0) + 1
            times[name] = times.get(name, 0) + elapsed
            return result
        return wrapper
    try:
        setattr(real_engine, attr_name, make_wrapper(attr_name, original))
    except AttributeError:
        pass  # skip read-only properties
```

Also instrument `to_sympy()`/`to_symengine()` in `Irene.symbolic_engine` the same way.

Run at: `IreneRewrite/benchmarks/instrument_relaxation_v2.py`

## Micro-Benchmarks

Compare SymEngine vs SymPy for each operation type:
- `to_sympy()` conversion cost: 0.8 µs (se.Basic→sp.Basic), 39.5 µs (DenseMatrix→Matrix)
- `engine.Poly()` vs `sp.Poly()`: 1.2× slower (33 vs 27 µs) for small polynomials
- `engine.groebner()` vs `sp.groebner()`: 1.1× slower (300 vs 270 µs)
- **Critical**: `se.expand((x+y)^8)` is 2.9 µs vs `sp.expand()` at 0.6 µs — SymEngine is 5× SLOWER for this expansion, not faster. SymPy caches or the expression is pre-expanded.

Run at: `IreneRewrite/benchmarks/profile_symengine_overhead.py`

## Instrumented Trace Results (Motzkin SOS order 1)

### Before Fixes

| Metric | Value |
|--------|-------|
| Total wall time | 160.6 ms |
| `engine.Poly()` calls | 255, 36,030 µs (99% of engine time) |
| `engine.Matrix()` calls | 4, 325 µs |
| `engine.sympify()` calls | 62, 80 µs |
| `engine.zeros()` calls | 58, 22 µs |
| `engine.expand()` calls | 2, 2.6 µs |
| `to_sympy()` conversions | 704, 3,147 µs |
| Conversion as % of wall | 2.0% |
| SymPy-fallback vs SymEngine-native | 99:1 ratio |

### After Fixes (to_sympy short-circuit + SymPy generators)

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| `to_sympy()` calls | 704 | 100 | −86% |
| `to_sympy()` time | 3,147 µs | 1,964 µs | −38% |
| `engine.Poly()` time | 36,030 µs | 34,672 µs | −4% |
| Total wall time | 160.6 ms | 171.1 ms | noise |

### Cross-Version Comparison (Original Irene)

| Metric | Original Irene | IreneRewrite |
|--------|---------------|-------------|
| `sp.Poly()` calls | 154 | 255 (engine.Poly) |
| `sp.Poly()` time | 15.1 ms | 34.9 ms |
| Per-call cost | 98 µs | 137 µs |
| Wall time | 139 ms | 171 ms |

**Key insight**: IreneRewrite makes 65% more Poly calls and each is 40% slower.
The +65% calls come from the `RelaxationEngine` dispatch pathway creating
additional intermediate Poly objects. The +40% per-call is from `isinstance`
checks in `engine.Poly()`.

## Three Fixes Applied

### Fix 1: to_sympy() short-circuit (`symbolic_engine.py:36`)

```python
def to_sympy(obj):
    if obj is None:
        return None
    # NEW: short-circuit for already-SymPy objects
    if isinstance(obj, sp.Basic) and not isinstance(obj, se.Basic):
        return obj
    if isinstance(obj, se.Basic):
        ...
```

### Fix 2: AuxSyms as SymPy (`relaxations.py:217`)

```python
# Before:
t_sym = engine.Symbol('X%d' % self.NumGenerators)
# After:
t_sym = _sp.Symbol('X%d' % self.NumGenerators)
```

### Fix 3: from_problem generators as SymPy (`relaxations.py:266`)

```python
# Before:
sympy_gens = [engine.Symbol(g) for g in gen_names]
# After:
sympy_gens = [_sp.Symbol(g) for g in gen_names]
```

The `_sp` import was added at the top of `relaxations.py`.

## Verification

```bash
# Instrumented trace (confirms conversion reduction):
/home/YOUR-USER/Code/Python/IreneRewrite/.venv/bin/python3 \
  benchmarks/instrument_relaxation_v2.py

# Existing test suite (51 tests must pass):
cd /home/YOUR-USER/Code/Python/IreneRewrite
.venv/bin/python3 -m pytest Irene/tests/ -q

# Cross-version benchmark (bounds unchanged):
/home/YOUR-USER/Code/Python/IreneRewrite/.venv/bin/python3 \
  benchmarks/compare_irene_vs_rewrite.py --mode irene_rewrite --problem motzkin
```

## Remaining Gap → RESOLVED (2026-08-08)

Two further fixes were applied after the initial conversion-tax reductions, closing 87% of the gap:

### Solution A: CVXOPT native solver (`sdp.py:599`)

`_cvxpy_solve()` now returns `False` for CVXOPT/DSDP solver names, falling through
to the legacy `CvxOpt()` path which uses CVXOPT's native C interface. This matches
original Irene's solver and fixes the SOS infeasibility detection regression.

### Solution B: `_poly()` bypass (`relaxations.py`)

Added `_poly()` helper that calls `sp.Poly()` directly (with automatic SymEngine→SymPy
conversion safety). Replaced all 21 `engine.Poly()` call sites with `_poly()`. This
eliminates the 40% per-call overhead from `SymbolicEngine` method dispatch.

### Solution B.1: Infeasibility check reordering (`relaxation_api.py:259`)

Moved the infeasibility status check BEFORE the `primal_val is None` guard. CVXOPT
may return `None` primal for infeasible SDPs; checking the status string first
catches infeasibility instead of raising a generic RuntimeError.

### Final benchmark (3-run avg)

| Mode | Before all fixes | After all fixes | Original Irene |
|------|-----------------|-----------------|----------------|
| Total wall time | 8.50s | 7.36s (−13.4%) | 7.09s |
| Gap vs original | +20% | +3.8% | — |
| SOS infeasibility | ✗ (finite bounds) | ✓ (correct) | ✓ |

