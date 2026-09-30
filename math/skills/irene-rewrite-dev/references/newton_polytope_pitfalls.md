# Newton Polytope Pruning — Pitfalls & Fixes

Discovered during IreneRewrite Phase 3 (2026-08-08), confirmed fixed.
Module: `/home/YOUR-USER/Code/Python/IreneRewrite/Irene/newton_polytope.py` (~360 lines after fixes).

## Bug 1: Missing origin in combined Newton polytope

**Symptom:** `prune_basis_from_polys()` returns `pruned_basis_size=0` for polynomials
without a constant term (e.g., Choi-Lam: $2x^4 y^2 + 2x^2 y^4 - x^2 y^2$).
All monomials get pruned — the basis collapses to empty.

**Root cause:** `combined_newton_polytope()` computes the Minkowski sum of individual
Newton polytopes then scales by 2. When no polynomial has a constant term,
the combined polytope lacks the origin $(0,\ldots,0)$. The constant monomial
$x^0 = 1$ — which is always in the moment matrix basis — falls outside the hull.

**Fix applied** (`combined_newton_polytope`, after Minkowski sum, before scaling):
```python
ncols = result.shape[1]
include_origin = True
for row in result:
    if np.all(row == 0):
        include_origin = False
        break
if include_origin:
    origin = np.zeros((1, ncols), dtype=int)
    result = np.vstack([result, origin])

# Then scale by 2
result = scale_polytope(result, 2)
```

**Verification:** Choi-Lam went from 0/0/0 (broken) to 6→2 / 15→5 / 28→10
(matching Motzkin's 66.7% reduction pattern).

## Bug 2: Minkowski sum dimension mismatch

**Symptom:** `ValueError: operands could not be broadcast together with shapes (6,) (2,)`
when pruning multi-polynomial problems (chain/star 6-var tests).
Different polynomials reference different subsets of variables → polytopes
have incompatible column counts.

**Root cause:** `prune_basis_from_polys()` called `combined_newton_polytope(polynomials)`
without passing `vars_list`. Each `newton_polytope()` call inferred its own
variable list from `Poly().gens`, producing polytopes with mismatched dimensions.

**Fix applied** (`prune_basis_from_polys`):
```python
from sympy import symbols
canonical_vars = symbols(f'x0:{num_vars}')
vertices = combined_newton_polytope(polynomials, vars_list=canonical_vars)
```

## Safety net: empty pruned basis guard

**Fix applied** (`compute_pruned_basis`): if pruning produces 0 monomials,
fall back to the full unpruned basis:
```python
if self.pruned_basis_size == 0 and self.full_basis_size > 0:
    self.pruned_basis_size = self.full_basis_size
    self.reduction_ratio = 1.0
    pruned = [tuple(np.array(e, dtype=int)) for e in all_monos]
```

## Verification Recipe

After any change to `newton_polytope.py`:

```bash
cd /home/YOUR-USER/Code/Python/IreneRewrite

# 1. Full test suite
.venv/bin/python3 -m pytest Irene/tests/test_newton_polytope.py -v
# Expected: 13 passed

# 2. Choi-Lam sanity (pruned_basis > 0 at all orders)
.venv/bin/python3 -c "
from sympy import symbols, expand
from Irene.newton_polytope import prune_basis_from_polys
x,y = symbols('x y')
p = expand(x**4*y**2 + x**2*y**4 + x**2*y**2*(x**2 + y**2 - 1))
for d in [1,2,3]:
    pr = prune_basis_from_polys([p], num_vars=2, max_degree=2*d)
    i = pr.moment_matrix_dimension_reduction()
    assert i['pruned_basis_size'] > 0, f'Choi-Lam d={2*d} pruned to 0!'
    print(f'PASS: d={2*d}: {i[\"full_basis_size\"]}->{i[\"pruned_basis_size\"]}')
"

# 3. Chain/Star no-crash (6-var multi-polynomial)
.venv/bin/python3 -c "
from sympy import symbols
from Irene.newton_polytope import prune_basis_from_polys
xv = [symbols(f'x{i}') for i in range(6)]
for label,polys in [
  ('chain',[xv[i]**2+xv[i+1]**2+xv[i]*xv[i+1] for i in range(5)]),
  ('star',[xv[0]**2+xv[i]**2+xv[0]*xv[i] for i in range(1,6)]),
]:
    pr = prune_basis_from_polys(polys, num_vars=6, max_degree=4)
    i = pr.moment_matrix_dimension_reduction()
    print(f'PASS: {label} {i[\"full_basis_size\"]}->{i[\"pruned_basis_size\"]}')
"

# 4. Full Phase 3 suite (51 tests)
.venv/bin/python3 -m pytest \
  Irene/tests/test_border_basis.py \
  Irene/tests/test_sparsity.py \
  Irene/tests/test_newton_polytope.py \
  Irene/tests/test_relaxation_api.py -q
# Expected: 51 passed in ~1.3s
```

## Expected Behavior (post-fix)

| Polynomial | d=2 | d=4 | d=6 |
|---|---|---|---|
| Motzkin | 6→2 | 15→5 | 28→10 |
| Choi-Lam | 6→2 | 15→5 | 28→10 |
| Robinson | 6→0 | 15→5 | 28→18 |
| Sparse trinomial | 6→6 | 15→15 | 28→28 |
| Chain 6-var | 210→210 | — | — |
| Star 6-var | 210→210 | — | — |

Choi-Lam now matches Motzkin's pattern (the fix ensures the origin is always
in the polytope). Robinson shows different behavior because its Newton polytope
naturally contains the origin from the $x^4 + y^4$ pure terms.
