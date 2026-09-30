# SDPA File Format & Cross-Solver Comparison

Conventions, quirks, and encoding patterns for generating SDPA files directly (not via ncpol2sdpa) and comparing results across Irene, IreneRewrite, ncpol2sdpa, and independent reference solvers.

## SDPA Sparse File Format Conventions

### Objective row
- SDPA minimizes `c · x` as-written.
- The objective row has exactly N entries (one per variable), **NO** leading constant slot.
- Variable k=0 corresponds to the moment entry y_(0,0) (the "1" monomial).

### Block format
- Only one triangle (upper) per block; lower triangle is implicit.
- Row/col fields are 1-based matrix indices: `row = i+1`, `col = j+1` where i,j index into the moment matrix rows/columns.
- **NOT** sequential upper-triangle numbering.

### k=0 sign flip (critical)
- SDPA internally flips the sign of entries in row/col 0 (the k=0 variable).
- Writing `-1` at position k=0 gives effective `+y_(0,0)`; writing `+1` gives effective `-y_(0,0)`.
- This applies to ALL blocks that touch k=0: moment matrix normalization AND localizing matrices for equalities and inequalities.

## Encoding Patterns

### Moment matrix normalization (mass = 1)
```python
# Write -1 at k=0 → effective +y_(0,0) = 1
entries[(0, 0)] = -1.0
```

### Equality constraints: two-sided PSD localizing matrices
For equality `h(x) = 0`, encode as both `+L(h) >= 0` and `-L(h) >= 0`:
```python
# +L(h): negate k=0 entry (SDPA flip)
for beta, hb in h_data:
    key = moment_key(beta)
    if key == (0, 0):
        entries[key] = -float(hb)   # SDPA flips → effective +hb * y_beta
    else:
        entries[key] = float(hb)

# -L(h): flip all signs relative to +L(h)
for beta, hb in h_data:
    key = moment_key(beta)
    if key == (0, 0):
        entries[key] = float(hb)    # SDPA flips → effective -hb * y_beta
    else:
        entries[key] = -float(hb)
```
This matches ncpol2sdpa's Block 2/3 pattern.

### Inequality constraints: one-sided PSD localizing matrices
For inequality `g(x) >= 0`, encode as `L(g) >= 0`:
```python
# k=0 rows get SDPA sign flip, so negate to get effective +g_0 * y_(0,0)
for beta, gb in g_data:
    key = moment_key(beta)
    if key == (0, 0):
        entries[key] = -float(gb)   # SDPA flips → effective +gb * y_beta
    else:
        entries[key] = float(gb)
```
**PITFALL — Missing k=0 negation for inequalities:** If you write `+float(gb)` at k=0, SDPA flips it to `-gb * y_(0,0)`, making the localizing matrix always negative for feasible moments → solver reports unbounded. This was the root cause of `ball_ineq` returning unbounded in reference_sdp.py before the fix.

## ncpol2sdpa Quirks

### cvxopt backend broken with sympy >= 1.13
`AttributeError: 'SymmetricVariable' object has no attribute 'factors'` — the cvxopt backend is incompatible with sympy 1.13+. Downgrade to `sympy<1.13` or use SDPA route.

### Objective value reporting
- For ncpol-generated files: report `sdpr.primal` directly (ncpol already handles sign conversion).
- For direct SDPA files: report `objValPrimal` from the solver output directly.

### Commutative variables
Use `generate_variables("xyz", n)` instead of `generate_operators` for commutative polynomial optimization problems.

### Equality constraints
Pass via `equalities=[...]`, NOT via `substitutions={}`. Using substitutions drops equality information from the relaxation.

## Cross-Solver Comparison Patterns

### Irene equality encoding
Use `relations=` parameter (not `equalities=`) for equality-constrained problems in both Irene and IreneRewrite.

### Solver selection
- Irene/IreneRewrite: `solve(solver='sdpa')` — CVXOPT backend has strict-feasibility issues on some problems.
- ncpol2sdpa: SDPA route via `/usr/bin/sdpa` (cvxopt broken with sympy >= 1.13).

### Known result patterns
| Problem | True Min | IreneRewrite | ncpol L2 | Reference |
|---------|----------|-------------|----------|-----------|
| quartic_1d | -0.25 | -0.25 | -0.25 | -0.25 ✅ |
| circle_eq | +1.0 | +1.0 | +1.0 | +1.0 ✅ |
| sphere4_eq | +0.5 | +0.5 | 0.0 ⚠️ | +0.5 ✅ |
| ball_ineq L1 | -0.5 | +0.5 (sign issue) | — | -0.5 ✅ |

**PITFALL — ncpol sphere4_eq → 0.0:** ncpol2sdpa returns 0.0 for `sphere4_eq` (sum of squares on unit sphere in R⁴, expected min 0.5). This appears to be an ncpol-specific issue with the problem formulation or relaxation level; Irene and reference solver both return correct +0.5.

## Environment
- SDPA binary: `/usr/bin/sdpa`
- ncpol2sdpa venv: `/home/YOUR-USER/Code/Python/IreneComparison/.venv-ncpol`
- sympy version in ncpol venv: 1.12.1 (downgraded from 1.14.0)
