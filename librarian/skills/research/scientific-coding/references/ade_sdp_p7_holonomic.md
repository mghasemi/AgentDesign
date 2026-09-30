# P7 Holonomic Encoding

**Verified:** 2026-07-18  
**Status:** ✅ 5.98% gap at d=1 (vs 8.34% best known exp4-MOM-B)  
**d=2:** Timeout (>600s) — Groebner bottleneck with ~16 generators

## Problem

P7: $\min_{x,y \in [-\pi,\pi]} x \cdot \sin(xy) + y / \cosh(xy)$

The two circle invariants $v_1^2+v_2^2=1$ and $q^2+s^2=1$ define $S^1 \times S^1$
(4D torus). The true 1D curve cannot be distinguished at d=2.

## Holonomic Encoding

Generators $(x, y, z, u, v, w, s, r)$:
- $u = \sin(xy)$, $v = \cos(xy)$ — trig circle: $u^2+v^2=1$
- $w = \cosh(xy)$, $s = \sinh(xy)$ — hyp hyperbola: $w^2-s^2=1$
- $r = 1/w = \operatorname{sech}(xy)$ — reciprocal: $wr=1$
- $z = x u + y r$ — objective encoded as relation

D_x dynamics (chain rule on $xy$ argument):
```python
dm = {
    x: 1,      # D_x(x) = 1
    y: 0,      # y independent of x
    z: 0,      # objective dynamics via Invariant
    u: y*v,    # D_x(sin(xy)) = y·cos(xy)
    v: -y*u,   # D_x(cos(xy)) = -y·sin(xy)
    w: y*s,    # D_x(cosh(xy)) = y·sinh(xy)
    s: y*w,    # D_x(sinh(xy)) = y·cosh(xy)
    r: -y*s*r**2,  # D_x(1/w) = -y·s·r²
}
```

## Recipe

```python
from sympy import symbols, Eq
from Irene.dsdp import DSDPRelaxations
import math

x, y = symbols('x y')
z, u, v, w, s, r = symbols('z u v w s r')

tmp = DSDPRelaxations([x, y, z, u, v, w, s, r])
dm = {x: 1, y: 0, z: 0, u: y*v, v: -y*u, w: y*s, s: y*w, r: -y*s*r**2}
dsyms, rels, gens = tmp.build_ade_relations(dm)

dsdp = DSDPRelaxations(
    gens=gens, relations=list(rels),
    verbosity=0, box_size=math.pi,
    original_gens=[x, y, z, u, v, w, s, r]
)
# Invariants
dsdp.AddConstraint(Eq(u**2 + v**2 - 1, 0))
dsdp.AddConstraint(Eq(w**2 - s**2 - 1, 0))
dsdp.AddConstraint(Eq(w*r - 1, 0))
dsdp.AddConstraint(Eq(z - x*u - y*r, 0))
# Objective
dsdp.SetObjective(z)
dsdp.Parallel = True
lb = dsdp.solve(order=1)  # 5.98% gap at d=1
```

## Why It Works

The $z = xu + yr$ relation couples the objective directly to all generators
through the Groebner basis. The reciprocal $r = 1/w$ with $wr=1$ provides
a compact-invariant-like coupling for the hyperbolic subsystem. The trig
subsystem has the compact circle invariant $u^2+v^2=1$.

**Key difference from old encoding:** The old encoding used $q = \operatorname{sech}(xy)$
and $s = \tanh(xy)$ with $q^2+s^2=1$, but without the $wr=1$ coupling. The
holonomic encoding adds $w = \cosh(xy)$ explicitly and the reciprocal $r$,
creating three mutually constraining invariants $(u^2+v^2=1, w^2-s^2=1, wr=1)$.

## Solver Settings

- `Parallel=True` — mandatory for d≥1 (8+ generators)
- d=1: 8s, 5.98% gap
- d=2: Timeout >600s (16 generators after adding derivative symbols)
- Use Irene `.venv`, not sage conda
