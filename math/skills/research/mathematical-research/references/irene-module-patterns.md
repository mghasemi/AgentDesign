# Irene Package — Module Authoring Patterns

Conventions and patterns for writing new modules in the Irene polynomial
optimization framework (`/home/YOUR-USER/Code/Python/Irene/Irene/`).

## Project Structure

```
Irene/
├── Irene/
│   ├── __init__.py          # Public exports
│   ├── program.py           # OptimizationProblem
│   ├── grouprings.py        # SemigroupAlgebra, CommutativeSemigroup
│   ├── sonc.py              # SONCRelaxations (GP/signomial)
│   ├── sdp.py               # sdp solver class
│   ├── relaxations.py       # SDPRelaxations, SDRelaxSol, Mom
│   ├── sosonc.py            # SOSONCRelaxations (NEW pattern)
│   └── ...
└── tests/
    └── test_sosonc.py
```

## OptimizationProblem Setup

```python
from Irene.grouprings import CommutativeSemigroup, SemigroupAlgebra
from Irene.program import OptimizationProblem

# 1. Build the semigroup (STRING names, not sympy Symbols)
sg = CommutativeSemigroup(['x', 'y'])
sga = SemigroupAlgebra(sg)

# 2. Get variables by string key
x = sga['x']
y = sga['y']

# 3. Build polynomial expressions via sga arithmetic
f = 1 + 2 * x**2 * y**4 - 3 * x**2 * y**2

# 4. Create problem and set objective (NOT .Minimize()!)
prog = OptimizationProblem(sga)
prog.set_objective(f)                # unconstrained

# 5. With constraints (optional)
g1 = y - x**4 * y + y**5 - x**6 - y**6
prog.add_constraints([g1])
```

**Do NOT use `prog.Minimize()`** — that method does not exist.

## New Module Template

```python
r"""Module docstring with :math:`LaTeX` markup."""

import math
import time
from typing import Any, Optional

from .program import OptimizationProblem


class MyRelaxSol(object):
    """Result container for relaxation."""

    __slots__ = ("val", "status", "runtime")

    def __init__(self) -> None:
        self.val: float = -float("inf")
        self.status: str = "error"
        self.runtime: float = 0.0

    def __repr__(self) -> str:
        return f"MyRelaxSol(val={self.val}, status='{self.status}')"


class MyRelaxations(object):
    """Relaxation engine."""

    def __init__(self, prog: OptimizationProblem, **kwargs) -> None:
        self.prog = prog
        self.verbosity = kwargs.get("verbosity", 1)
        self.error_bound = kwargs.get("error_bound", 1e-10)

    def solve(self) -> float:
        """Main entry point. Returns lower bound."""
        pass
```

### Key conventions

- **Result containers**: `__slots__` (not `__dict__`), `__repr__`, typed fields
- **Engine classes**: `__init__` takes `OptimizationProblem` and `**kwargs`
- **Method naming**: `camelCase` for user-facing (matching Schick toolbox),
  `_underscore` for internal
- **Error handling**: `try/except` wraps, never crashes on solver failure
- **Docstrings**: `r"""..."""` with `:math:` for LaTeX, NumPy-style parameter lists

## Wrapping Existing Relaxations

```python
# SONC: from Irene.sonc import SONCRelaxations
sonc = SONCRelaxations(prog, verbosity=0, use_local_solve=True)
val = sonc.solve(verbosity=0)

# SDP: from Irene.relaxations import SDPRelaxations
sdp = SDPRelaxations(prog)
sol = sdp.Minimize(
    objective_index=0,
    relaxation_order=2,       # Lasserre relaxation order
    solver="cvxopt",          # or 'csdp', 'sdpa', 'dsdp'
)
# sol.Primal, sol.Dual, sol.Status, sol.Message, sol.RunTime
```

## Tests

Use `pytest` with fixtures that rebuild the semigroup for each test:

```python
import pytest
from Irene.grouprings import CommutativeSemigroup, SemigroupAlgebra
from Irene.program import OptimizationProblem

class TestModule:
    def setup_method(self):
        self.sg = CommutativeSemigroup(['x', 'y'])
        self.sga = SemigroupAlgebra(self.sg)

    def test_feature(self):
        x = self.sga['x']
        y = self.sga['y']
        prog = OptimizationProblem(self.sga)
        prog.set_objective(x**2 + y**2)
        # ... test logic
```

Run tests:
```bash
cd /home/YOUR-USER/Code/Python/Irene && python3 -m pytest tests/test_sosonc.py -v
```

## End-User SOS Certificate Workflow

For applying Irene's moment-SOS hierarchy to polynomial optimization problems
(not authoring new modules — for that see "New Module Template" above).

### Installation

```bash
# Irene is NOT on PyPI. Clone and pip-install:
git clone https://github.com/YOUR-GITHUB/Irene.git /tmp/Irene
pip install -e /tmp/Irene    # editable install

# Required dependencies (cvxpy is mandatory, not optional):
pip install cvxpy      # Irene's matrices.py imports cvxpy at module level
# Irene also needs at least one SDP solver:
#   cvxopt (pip install cvxopt) — always available via Python
#   sdpa   (apt install sdpa)   — system package, Irene detects automatically
```

**Verification**: `from Irene import SDPRelaxations` (capital I — the package
installs as `Irene-1.2.5.dist-info` but `import Irene`).

### Univariate Polynomial Optimization via SOS

For `min_{x} p(x)` where p is a univariate polynomial (SOS = nonnegativity
in one variable, so the moment-SOS hierarchy is exact):

```python
import sympy as sp
from Irene import SDPRelaxations
import cvxopt; cvxopt.solvers.options['show_progress'] = False

x = sp.Symbol('x', real=True)
p = x**4 - 2*x**2 + x + 1   # example polynomial

rlx = SDPRelaxations([x])
rlx.SetObjective(p)
rlx.MomentsOrd(3)           # order ≥ ceil(deg/2) + 1 = 3 for quartic
rlx.InitSDP()
f_min = rlx.Minimize()

if rlx.Solution.Status == 'Optimal':
    print(f"Global minimum: {f_min}")
    sos = rlx.Decompose()   # dict: {0: [σ₀(x), σ₁(x), ...], 1: [...], ...}
    print(f"SOS decomposition: p(x) − p* = Σ σᵢ(x)²  ({len(sos[0])} terms)")
```

### DSDP-Specific Patterns

For differential equation-constrained optimization (y^(n) = P(x,y,…), min ∫L dx):

1. **Use EXACT closed-form solutions** for linear ODEs, not truncated Taylor
   series. The truncated series produces an approximate objective whose
   minimum differs from the true minimum.

2. **For coupled/nonlinear systems without closed forms**: fit a Chebyshev
   polynomial to numerically-evaluated J(β) via `solve_ivp` + `np.trapezoid`,
   then apply Irene to the fitted polynomial. Use degree 6–10 with moment
   order ≥ (deg+1)//2 + 1.

3. **Moment order rule**: `MomentsOrd(ceil(deg/2) + 1)` where deg is the
   polynomial degree. For univariate polynomials this is always sufficient.

### Common Pitfalls

- **Symbol mismatch**: `CommutativeSemigroup([Symbol('x')])` fails. Use STRINGS:
  `CommutativeSemigroup(['x'])`.

- **Symbol mismatch**: `CommutativeSemigroup([Symbol('x')])` fails. Use STRINGS:
  `CommutativeSemigroup(['x'])`.
- **Key access**: `sga[sg.generators[0]]` fails. Use `sga['x']` (string key).
- **set_objective signature**: Takes ONE `SemigroupAlgebraElement`, not a
  sympy expression. Build the expression via SGA arithmetic.
- **SDPRelaxations.Minimize()**: Needs `objective_index=0` for unconstrained
  problems. Default `relaxation_order=1` may be insufficient — bump to 2+
  for quartic polynomials.
- **MomentMat KeyError (FIXED 2026-07-06)**: When `relations` produce
  Groebner-reduced monomials of degree > `2*MmntOrd`, `MomentMat()` used
  to crash with `KeyError`. Now fixed: missing monomials are reduced via
  `ReduceExp()` and re-expressed in known moments. If `KeyError` appears
  on a new problem, check `relaxations.py` lines 455-475.
- **Bilinear relations crash Groebner reducer**: ADE relations like
  $d_x z = -yw$ contain bilinear terms that crash Irene. **Workaround**:
  derive polynomial relations first (square the bilinear equations, use
  $z^2+w^2=1$ to absorb cross-terms). See `differential-algebra-constraints`
  skill, `references/cosxy_ade_lift.md`.
- **SDPA solver available**: In addition to `cvxopt`, Irene supports
  `sdpa` via `R.SetSDPSolver('sdpa')`. SDPA is better-conditioned for
  large-scale SDPs but still fails on problems with extreme dynamic range
  (see below). Install: `pip install sdpa-python`.
- **Extreme dynamic range → Infeasible**: When lifted variables span 3+
  orders of magnitude (e.g., $e^{-y} \in [0.002, 535]$, $\sinh(x) \in [-268, 268]$),
  both CVXOPT and SDPA return Infeasible even at d=1. Rescaling variables
  to [0,1] is necessary but not sufficient. The Archimedean property is
  effectively lost in the lifted space. Diagnostic: CVXOPT dual cost
  oscillating above $10^8$. See `differential-algebra-constraints` skill,
  Pitfall 6 and `references/exp_trig_hyp_lift.md`.
