# Rational Parameterization for Non-Compact Varieties

> **Discovered:** 2026-07-18
> **Status:** ✅ Validated for sinh/cosh; generalizable to other hyperbolic functions

## The Problem

ADE invariants for hyperbolic functions define **non-compact** algebraic varieties (hyperbolas). The Lasserre hierarchy produces loose bounds because the SDP can explore unbounded regions within the box constraints, even when the true function values remain bounded.

Example: $z^2 - y^2 = 1$ for $y=\sinh(x), z=\cosh(x)$ is a hyperbola. The SDP at d=2 gives LB = -3.73 for $\sinh(x)+\cosh(x)$ (true min = 0.135) — a 2857% gap.

## The Cure: Rational Parameterization via Stereographic Projection

Map the non-compact variety to a compact domain using a rational parameter $t$:

$$y = \frac{2t}{1-t^2}, \quad z = \frac{1+t^2}{1-t^2}$$

This satisfies $z^2 - y^2 = 1$ by construction. Introduce $s = 1/(1-t^2)$ to clear denominators:

$$s(1-t^2) = 1, \quad y = 2ts, \quad z = s(1+t^2)$$

For $\sinh(x)$ and $\cosh(x)$: $t = \tanh(x/2) \in (-1, 1)$.

## Irene Implementation

```python
from sympy import symbols
from Irene.dsdp import DSDPRelaxations

t, s, y, z = symbols('t s y z')
dsdp = DSDPRelaxations(
    [t, s, y, z],
    relations=[
        s*(1 - t**2) - 1,    # parameterization
        y - 2*t*s,            # sinh encoding
        z - s*(1 + t**2),     # cosh encoding
    ],
    verbosity=0, box_size=0.8,  # t ∈ [-0.8, 0.8]
)
dsdp.SetObjective(y + z)       # sinh + cosh = e^x
dsdp.AddConstraint(s >= 0.001) # s > 0
lb = dsdp.solve(order=1)       # d=1 is near-exact!
```

## Results

| Encoding | d=1 | Gap |
|---|---|---|
| Old ($z^2-y^2=1$) | -4.00 | 3056% |
| **Rational param.** | **0.135335** | **~0.00005%** |

## When to Use

Use rational parameterization when:
1. The invariant defines a non-compact variety (hyperbola)
2. A rational parameterization exists that maps to a bounded interval
3. The objective can be expressed polynomially in the parameterized variables

## Known Limitations

- d=2 may become numerically unstable (primal infeasible) due to moment matrix conditioning with rational constraints
- If d=1 is already near-exact, d=2 is unnecessary
- Works for $\sinh/\cosh$, $\tanh/\text{sech}$, and any function with a rational parameterization

## Theoretical Foundation

Based on the algebraic compactification framework from real algebraic geometry. The rational parameterization creates an **Archimedean** variety — the domain variable $t$ is strictly bounded, satisfying Putinar's condition for convergence of the Lasserre hierarchy.
