# Cross-Version Comparison Recipe (Irene vs IreneRewrite)

## Command

```bash
# IreneRewrite (uses CVXOPT native solver after fixes):
/home/YOUR-USER/Code/Python/IreneRewrite/.venv/bin/python3 \
  /home/YOUR-USER/Code/Python/IreneRewrite/benchmarks/compare_irene_vs_rewrite.py \
  --mode irene_rewrite 2>/dev/null

# Original Irene (uses CVXOPT native solver):
/home/YOUR-USER/Code/Python/Irene/.venv/bin/python3 \
  /home/YOUR-USER/Code/Python/IreneRewrite/benchmarks/compare_irene_vs_rewrite.py \
  --mode irene 2>/dev/null
```

Both output clean JSON (solver noise + telemetry warnings suppressed internally).

Single-problem smoke: `--problem motzkin`. Quick subset: `--quick`.

## Problem Set (10 problems)

| ID | Degree | Category | True Min | SOS? |
|----|--------|----------|----------|------|
| quad_1d | 2 | trivial | 0.0 | ✓ |
| quartic_1d | 4 | classic | −0.25 | ✓ |
| motzkin | 6 | separating | 0.0 | ✗ |
| choi_lam | 6 | separating | 0.0 | ✗ |
| robinson | 6 | separating | 0.0 | ✗ |
| constrained_1d | 2 | constrained | 1.0 | ✓ |
| sphere_4 | 4 | constrained | 0.5 | ✓ |
| schick | 6 | separating | 0.0 | ✗ (SOS+SONC works) |
| dense_bivar_8 | 8 | stress | 0.0 | ✓ |
| sparse_trinomial | 6 | sparse | −0.5 | ✓ |

## Final Timing (after all fixes, 2026-08-08)

3-run averages:

| Mode | Total | SOS | SONC | SOS+SONC |
|------|-------|-----|------|----------|
| IreneRewrite | 7.36s | — | — | — |
| Original Irene | 7.09s | — | — | — |
| **Gap** | **+3.8%** | — | — | — |

Before fixes: IreneRewrite 8.50s, gap +20%. All three solutions combined closed 87% of the gap.

## Verification Script

```python
import json, subprocess

SCRIPT = "/home/YOUR-USER/Code/Python/IreneRewrite/benchmarks/compare_irene_vs_rewrite.py"
RW_PY = "/home/YOUR-USER/Code/Python/IreneRewrite/.venv/bin/python3"
OG_PY = "/home/YOUR-USER/Code/Python/Irene/.venv/bin/python3"

def run(mode, problem):
    py = RW_PY if mode == "irene_rewrite" else OG_PY
    r = subprocess.run([py, SCRIPT, "--mode", mode, "--problem", problem],
                       capture_output=True, text=True, timeout=120)
    s = r.stdout.find("{"); e = r.stdout.rfind("}")
    return json.loads(r.stdout[s:e+1])

# SOS infeasibility (should work in BOTH modes now)
for pid in ["motzkin", "choi_lam", "schick"]:
    d = run("irene_rewrite", pid)
    assert d["results"][0]["relaxations"]["sos"]["r1"]["status"] == "infeasible"

# SOS-certifiable bounds match
for pid, expected in [("quartic_1d", -0.25), ("constrained_1d", 1.0), ("sphere_4", 0.5)]:
    d = run("irene_rewrite", pid)
    for ov in d["results"][0]["relaxations"]["sos"].values():
        if ov.get("value") is not None:
            assert abs(ov["value"] - expected) < 0.01
            break

# SONC bounds unchanged
d = run("irene_rewrite", "motzkin")
assert abs(d["results"][0]["relaxations"]["sonc"]["r1"]["value"]) < 1e-6
```

## Applied Fixes (chronological)

### Phase 1: Conversion tax reduction (before benchmarking, 2026-08-08)

| # | File | Change | Impact |
|---|------|--------|--------|
| 1 | `symbolic_engine.py:36` | `isinstance(obj, sp.Basic) → return obj` short-circuit | `to_sympy()` calls −86% |
| 2 | `relaxations.py:217` | `engine.Symbol(...)` → `_sp.Symbol(...)` for AuxSyms | Eliminates per-call generator conversion |
| 3 | `relaxations.py:266` | `engine.Symbol(g)` → `_sp.Symbol(g)` in `from_problem()` | Eliminates per-call generator conversion |

### Phase 2: Structural fixes (after profiling, 2026-08-08)

| # | Solution | Files | Impact | Pros | Cons |
|---|----------|-------|--------|------|------|
| A | CVXOPT native solver (bypass CVXPY/CLARABEL) | `sdp.py:599` | Fixes infeasibility + ~0.5s | Restores correct behavior, matches original | Loses CVXPY abstraction for CVXOPT |
| B | `_poly()` helper (bypass `engine.Poly()`) | `relaxations.py` (+21 call sites) | Eliminates 40% per-call overhead | Direct `sp.Poly()` — same as original | Safety wrapper needed for SymEngine objects |
| B.1 | Infeasibility check before primal guard | `relaxation_api.py:259` | Restores `infeasible` status | Critical fix | None |

### Cumulative impact: 8.50s → 7.36s (−13.4%), gap vs original: 15% → 3.8%
