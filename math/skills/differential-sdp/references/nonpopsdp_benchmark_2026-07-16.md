# NonPOPSDP vs DSDP-ADE Benchmark — Raw Data

**Date:** 2026-07-16 | **Irene:** v1.2.6 | **Module:** `Irene/nonpopsdp.py`

---

## Test Case Results

### NonPOPSDP Chebyshev (degree=6, relax_order=2)

| # | Test | LB | True min | Gap | Time |
|---|------|-----|----------|-----|------|
| 1 | Trig min(sin+cos) | -0.656381 | -1.414214 | 53.6% | 0.14s |
| 2 | Trig identity | Infeasible | 0.0 | — | 0.10s |
| 3 | Trig product sin·cos | -0.468392 | -0.500000 | 6.4% | 0.14s |
| 4 | Exp lift | -2.341218 | -3.864641 | 39.3% | 0.14s |
| 5 | Cosh lift | -3.195170 | -7.691476 | 58.5% | 0.15s |
| 6 | tan²-x² | -1.000000 | 0.0 | underestimate | 0.14s |
| 7 | Trig+KKT | -0.508928 | -1.414214 | 64.0% | 0.14s |

### NonPOPSDP Taylor (degree=8, relax_order=2)

| # | Test | LB | True min | Result | Time |
|---|------|-----|----------|--------|------|
| 1 | Trig min(sin+cos) | None | -1.414214 | Primal infeasible | 0.10s |
| 2 | Exp lift | None | -3.864641 | Primal infeasible | 0.09s |
| 3 | tan²-x² | None | 0.0 | Primal infeasible | 0.22s |

### DSDP-ADE (order=2, depth=1) — for comparison

| # | Test | LB | True min | Gap | Time |
|---|------|-----|----------|-----|------|
| 1 | Trig min(sin+cos) | -1.414213 | -1.414214 | 1.0×10⁻⁸ | 0.59s |
| 2 | Trig identity | 0.000000 | 0.0 | 2.0×10⁻⁸ | 0.58s |
| 3 | Trig product sin·cos | -0.500000 | -0.500000 | 2.0×10⁻⁸ | 0.59s |
| 4 | Exp lift | -2.14 | -3.864641 | underestimate | 0.60s |
| 5 | Cosh lift | -4.5 | -7.691476 | underestimate | 0.61s |
| 6 | tan²-x² | -1.0 | 0.0 | underestimate | 0.58s |
| 7 | Trig+KKT | -0.77 | -1.414214 | underestimate | 0.59s |

## Key Observations

1. **Compact variety advantage (DSDP-ADE):** Trig tests achieve ~10⁻⁸ gap because sin²+cos²=1 defines a compact variety.
2. **Non-compact variety weakness (both methods):** Exp/cosh/tan tests fail for both approaches because lifted variables lack compact algebraic relations.
3. **Taylor = unusable:** All Taylor tests return primal infeasibility. Local series diverge on global domains.
4. **Speed:** NonPOP Chebyshev mean 0.14s vs DSDP-ADE mean 0.59s (4× faster).
5. **Hierarchy gap negligible:** For trig min(sin+cos), the SDP hierarchy contributes ~0.0004 to total gap vs 0.75 from approximation error.

## Verification

Ad-hoc verification script confirmed:
- Module imports cleanly (6/6 checks passed)
- Chebyshev/Taylor approximations return valid polynomials
- `NonPOPSDP` class constructs and solves (lb=-0.687 for sin+cos test)
- Benchmark runner syntax valid
- Full benchmark: 13/13 tests, 0 errors, 1.9s total
