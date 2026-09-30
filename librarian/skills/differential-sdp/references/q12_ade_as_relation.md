# Q12: ADE-as-Relation — Quotient Ring Encoding (2026-07-13)

## Problem
Legacy DSDP encodes ADE constraints as numerical KKT moment conditions. For `tan(x)` with $d_x(u) = 1+u^2$, this produced LB = -4.0 (box bound) because the differential equation was only enforced numerically.

## Solution
Encode ADE as algebraic relations in the quotient ring. Introduce derivative symbols $d\_g$ for each generator, add relation $d\_g - \text{expr} = 0$, and prepend derivatives to the generator list for correct lex Groebner ordering.

## Implementation
- **Method:** `build_ade_relations(diff_map, prefix="d")` in `DSDPRelaxations` (L140 of `dsdp.py`)
- **Returns:** `(derivative_syms, relations, new_gens)` tuple
- **Usage pattern:**
  ```python
  dsyms, rels, new_gens = dsdp.build_ade_relations({x: 1, u: 1 + u**2})
  dsdp2 = DSDPRelaxations(new_gens, relations=rels, box_size=2)
  dsdp2.SetObjective(x - u)
  lb = dsdp2.solve(order=2)  # → -3.0
  ```

## Critical Pitfalls Discovered
1. **Groebner ordering:** Derivatives MUST be first in generator list. If state variables lead, `ReduceExp()` returns wrong symbols.
2. **SageMath `lm()` API:** `poly.lm()` fails for multivariate polynomials — use `Poly(poly, *vars).LM()` instead.
3. **`ReduceExp` returns AuxSym space:** `ReduceExp(du)` returns `X4**2 + 1`, not `u**2 + 1`. Verification must compare against `dsdp.AuxSyms`.
4. **SDP solver tolerance:** LB = -2.999999965173494, not exact -3.0. Use `abs(lb - expected) < 1e-4` for assertions.

## Results
| Method | LB | Time | KKT count |
|--------|-----|------|-----------|
| Legacy KKT | -4.000 | — | 2 |
| ADE-as-relation | -3.000 | 0.69s | 0 |
| ADE-as-relation + KKT | -3.000 | 1.38s | 2 |

Full test suite: 133 passed, 6 skipped, 0 failed (40.26s).
