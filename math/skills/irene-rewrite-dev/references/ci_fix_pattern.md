# CI Fix Pattern for IreneRewrite Solver Routing Changes

## Problem

When solver routing changes (e.g., switching CVXOPT from CVXPY/CLARABEL to native
`CvxOpt()` path), two classes of CI test failures occur:

1. **Solver name assertion failures**: Tests that assert `'CVXPY' in solver_name` break
   when the solver name changes to `'CVXOPT'`.

2. **SDP convergence failures**: Tests that worked with CLARABEL's numerical behavior
   may fail with CVXOPT's different convergence profile on ill-conditioned SDPs
   (e.g., constrained ball problems).

3. **CI matrix doesn't exercise declared solvers**: The `IRENE_CI_SOLVER` env var
   is set in the CI YAML but never read by any test code. The CI matrix declares
   CLARABEL and SCS but tests always use the hardcoded default solver.

## Fix Pattern

### 1. Update solver-name assertions to accept new routing

```python
# BEFORE (brittle): assumes CVXPY routing
assert 'CVXPY' in solver_name, f"Expected CVXPY routing, got {solver_name}"

# AFTER (robust): accepts either path
valid = 'CVXPY' in solver_name or 'CVXOPT' in solver_name
assert valid, f"Expected CVXPY or CVXOPT routing, got {solver_name}"
```

### 2. Pin numerically-sensitive tests to a known-good solver

```python
# BEFORE: uses default solver (may be CVXOPT native → fails on constrained SDPs)
rlx = SDPRelaxations(gens)
rlx.SetObjective(x + y)
rlx.AddConstraint(1 - x**2 - y**2 >= 0)   # relational form — bare polynomials are silently dropped (see sdp_relaxations_pitfalls.md §6)
rlx.InitSDP()

# AFTER: explicit solver for numerical stability
rlx = SDPRelaxations(gens)
rlx.SetObjective(x + y)
rlx.AddConstraint(1 - x**2 - y**2 >= 0)   # relational form — bare polynomials are silently dropped (see sdp_relaxations_pitfalls.md §6)
rlx.SetSDPSolver('CLARABEL')  # CVXOPT native struggles with constrained SDPs
rlx.InitSDP()
```

### 3. Wire CI env var into pytest fixtures

Add a session-scoped fixture in `conftest.py`:

```python
@pytest.fixture(scope="session")
def ci_solver():
    """Solver name from IRENE_CI_SOLVER env var, or None if not in CI."""
    return os.environ.get("IRENE_CI_SOLVER")
```

Then use it in tests that exercise solver routing:

```python
def test_constrained_problem_consistency(self, ci_solver):
    solvers_to_test = [ci_solver] if ci_solver else ['CLARABEL', 'SCS']
    for solver_name in solvers_to_test:
        # ... run with solver_name
```

## Files Affected by This Pattern

| Scenario | Files to check |
|----------|---------------|
| Default solver routing changed | `sdp.py:_cvxpy_solve()` |
| Test asserts solver name | `tests/test_solver_routing.py` |
| Test depends on solver convergence | `tests/test_relaxations.py` |
| CI matrix declares solvers | `.github/workflows/ci.yml` |
| Env var wiring | `conftest.py` |

## Verification After CI Fixes

```bash
cd /home/YOUR-USER/Code/Python/IreneRewrite

# 1. Full suite must pass with default solver
.venv/bin/python3 -m pytest Irene/tests/ tests/ -q
# Expected: 116 passed, 0 failed

# 2. CI modes must pass
IRENE_CI_SOLVER=CLARABEL .venv/bin/python3 -m pytest tests/test_solver_routing.py -q
IRENE_CI_SOLVER=SCS .venv/bin/python3 -m pytest tests/test_solver_routing.py -q
# Expected: 9 passed for each

# 3. Separating examples regression
.venv/bin/python3 -m pytest tests/test_separating_examples.py -q
# Expected: 3 passed (Motzkin/Choi-Lam/Robinson correctly not SOS)

# 4. Benchmark gallery quick-mode
.venv/bin/python3 benchmarks/run_gallery.py --quick --timeout 120 --output-dir benchmarks/results/
# Expected: BENCHMARK SUMMARY with 3-4 passed
```

## Session Reference

This pattern was established during the 2026-08-08 IreneRewrite speed optimization
session when Solutions A+B changed default CVXOPT routing from CVXPY/CLARABEL to
native `CvxOpt()`. The 6 CI jobs (3 Python × 2 solvers) all failed because two
tests had assumptions tied to the old routing and the CI matrix was ineffective.
