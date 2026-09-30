# Dual-ADE Technique — Groebner-Constrained Derivative Encoding

> **Date:** 2026-07-18  
> **Status:** ✅ VERIFIED — exp-x² gap reduced from 55% → 9.4%  
> **Category:** DSDP ADE encoding mechanism

## The Discovery

A new mechanism for tightening SDP bounds on ADE-constrained problems was
discovered. Unlike previous approaches, it uses **derivative symbols in the
Groebner basis** combined with an **algebraic `AddConstraint`** to create
structurally constrained moment matrices.

## Core Idea

For a function $y = f(x)$ satisfying $dy/dx = g(x,y)$ where $g$ is polynomial:

1. **Introduce auxiliary** $u = 1/g(x,y)$ — the inverse derivative
2. **Compute** $d_x(u)$ via chain rule: $d_x(u) = -(g_x + g_y \cdot g)/g^2$
3. **If** $d_x(u)$ simplifies to a polynomial in $(x, y, u)$, encode ALL three
   derivatives via `build_ade_relations()`
4. **Add** $g \cdot u = 1$ via `AddConstraint(Eq(...))` — NOT via `relations`

The key distinction: the derivative relations go through Groebner (creating
structured moment matrix entries), while the algebraic reciprocal goes through
`AddConstraint` (creating localizing matrices).

## Concrete Example: $y = e^x$

```python
from sympy import symbols, Eq
from Irene.dsdp import DSDPRelaxations

x, y, u = symbols('x y u')
tmp = DSDPRelaxations([x, y, u])

# g = y, so u = 1/y, and d_x(u) = -1/y = -u (polynomial!)
dm = {x: 1, y: y, u: -u}
dsyms, rels, gens = tmp.build_ade_relations(dm)
# gens = [d_x, d_y, d_u, x, y, u]
# rels = [d_x-1, d_y-y, d_u+u]

dsdp = DSDPRelaxations(
    gens=gens, relations=rels,
    verbosity=0, box_size=2,
    original_gens=[x, y, u]  # only box original variables
)
dsdp.SetObjective(y - x**2)

# CRITICAL: use AddConstraint, NOT relations
dsdp.AddConstraint(Eq(y*u - 1, 0))
dsdp.AddConstraint(y >= 0.001)

lb = dsdp.solve(order=2)
# → LB = -3.5000001189 (gap 9.44%)
# OLD yz=1-only: LB = -5.999999966 (gap 55.25%)

# NOTE: d=3 requires Parallel=True (sequential times out at 300s)
# d=3 gives same LB as d=2 (-3.5000, 9.44%) — relaxation-order floor
dsdp.Parallel = True
lb3 = dsdp.solve(order=3)
# → LB = -3.4999998636 (gap 9.44%), time = 3.9s
```

## Parallel=True Requirement

For dual-ADE configurations with 6+ generators (3 derivative symbols + 3 original),
`Parallel=True` is mandatory for d≥2:
- d=2: Parallel=True ≈ 1.1s (2× faster than sequential)
- d=3: **Requires** Parallel=True — sequential times out at 300s due to Groebner
- The gap floor at 9.44% confirms this is the relaxation-order limit for this encoding

## Why It Works

The Groebner basis reduces the derivative relations:
- $d_x \to 1$, $d_y \to y$, $d_u \to -u$

This forces specific entries in the moment matrix:
$$M[d_y] = M[y], \quad M[d_u] = -M[u], \quad M[d_x \cdot d_u] = -M[u]$$

The PSD condition on this constrained moment matrix is tighter than on a free
moment matrix with only $yu=1$ as a localizing constraint. The derivative
structure is baked into the moment matrix topology, not just added as an
optional constraint.

## When It Works

The technique requires $d_x(1/g)$ to simplify to a **polynomial** in the
generators. This holds when $g$ divides $g_x + g_y \cdot g$ in the polynomial
ring, or equivalently:

$$d_x(1/g) = -\frac{g_x + g_y \cdot g}{g^2} \in \mathbb{R}[x,y,u]$$

**Verified working:**
| Function | $g(x,y)$ | $u$ | $d_x(u)$ | Old Gap | Dual-ADE Gap | Verdict |
|---|---|---|---|---|---|---|
| $e^x - x^2$ | $y$ | $1/y$ | $-u$ | 55.25% | **9.44%** | ✅ 6× tighter |
| $\cosh x - 1$ | — | — | — | near-exact | near-exact | ✅ No regression |

**Partial improvement:**
| Function | Old Gap | Dual-ADE Gap | Why Partial |
|---|---|---|---|
| Airy $\operatorname{Ai}(x)$ | 1093% | 139% | No polynomial invariant exists |

**Confirmed NOT working:**
| Function | $g(x,y)$ | $u$ | $d_x(u)$ | Gap | Why |
|---|---|---|---|---|---|
| $\tan x$ | $1+u^2$ | $1/(1+u^2)$ | $-2uv$ | ~10¹⁷% unchanged | All $\tan(x+C)$ satisfy same ODE |
| $\log y$ | — | — | — | 88.6% unchanged | Inverse problem; derivative coupling too weak at d=2 |

## Key Distinction from Dead-End "Derivative-Coupled ADE"

The dead-end approach (Direction 4) also used `build_ade_relations` but put
the algebraic constraint in `relations` (Groebner) instead of `AddConstraint`
(localizing matrices). This causes the Groebner basis to **eliminate** the
auxiliary variable, destroying the structural constraint.

| Approach | Where is $yu=1$? | Aux variable survives? | Result |
|---|---|---|---|
| Dead End (Direction 4) | `relations` (Groebner) | Eliminated by GB | 55% gap |
| **Dual-ADE** | `AddConstraint` (localizing) | Kept as generator | **9.4% gap** |

## General Recipe

For any function $y=f(x)$ with $dy/dx = g(x,y)$:

```python
# 1. Define auxiliary: u = 1/g
# 2. Compute d_x(u) via chain rule: must be polynomial
# 3. Build ADE relations
dm = {x: 1, y: g, u: d_x_u_expression}
dsyms, rels, gens = tmp.build_ade_relations(dm)

# 4. Create DSDP with derivative relations in Groebner
dsdp = DSDPRelaxations(gens=gens, relations=rels, ...)

# 5. Add reciprocal via AddConstraint (NOT relations!)
dsdp.AddConstraint(Eq(g * u - 1, 0))

# 6. Add positivity constraint
dsdp.AddConstraint(u >= epsilon)
```

## Test to Request from User

For each candidate function, ask the user for the **first-order ODE**
$dy/dx = g(x,y)$ where $g$ is polynomial. From that, derive $u$ and $d_x(u)$
automatically, then test if the simplification is polynomial.
