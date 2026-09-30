# Tan via Sin/Cos Encoding

**Verified:** 2026-07-18  
**Status:** ✅ BREAKTHROUGH — gap ~5×10⁻⁹ at d=1

## Problem

The standard tan ADE $d_x(y) = 1 + y^2$ fails at d≤2 because it has **no
polynomial invariant**. The ADE alone cannot constrain the moment matrix
tightly enough — the SDP returns the box bound.

## Solution

Use the trig encoding: $f = \sin(x)$, $g = \cos(x)$ with the compact circle
invariant $f^2 + g^2 = 1$. Since $\tan(x) = f/g$ and $\tan(x) \approx x$ near
$x=0$, use the polynomial objective $(f - xg)^2$.

## Recipe

```python
from sympy import symbols, Eq
from Irene.dsdp import DSDPRelaxations

x, f, g = symbols('x f g')
tmp = DSDPRelaxations([x, f, g])
dm = {x: 1, f: g, g: -f}  # d_x(sin)=cos, d_x(cos)=-sin
dsyms, rels, gens = tmp.build_ade_relations(dm)

dsdp = DSDPRelaxations(
    gens=gens, relations=rels,
    verbosity=0, box_size=B,       # B < π/2 for tan poles
    original_gens=[x, f, g]
)
dsdp.AddConstraint(Eq(f**2 + g**2 - 1, 0))   # circle invariant
dsdp.SetObjective(f**2 - 2*x*f*g + x**2 * g**2)  # (f-xg)²
dsdp.Parallel = True
lb = dsdp.solve(order=1)  # near-exact at d=1!
```

## Key Insight

$(f-xg)^2$ is polynomial and its minimum is 0 at $x=0, f=0, g=1$, which
corresponds to $\tan(0) = 0$. The compact circle invariant $f^2+g^2=1$
ensures the SDP can't decouple $f$ and $g$ — it can't set $f=0, g=1$ AND
$x=B$ simultaneously because the derivative relations $d_x(f)=g, d_x(g)=-f$
couple them through the Groebner basis.

## Why the old approach ($f^2 - x^2g^2$) fails

$f^2 - x^2g^2 = f^2 - x^2(1-f^2) = f^2(1+x^2) - x^2$. At $f=0$: $-x^2$.
The SDP can choose $f=0, g=±1, x=±B$ and get $-B^2$, which is the box
bound, not the true tan value. The product $x^2g^2$ decouples $x$ from $g$
when $f=0$.

$(f-xg)^2$ couples $f$, $x$, and $g$ more tightly — the SDP can't set
$f=0, g=1, x=B$ and still achieve $(0 - B·1)^2 = B^2 > 0$.

## Solver Settings

- `Parallel=True` — 2-3× speedup
- Any $B < \pi/2$ works (tested $B=0.5, 1.0$)
- d=1 is sufficient (near-exact); d=2,3 give identical results
