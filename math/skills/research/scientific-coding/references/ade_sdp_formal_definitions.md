# Formal ADE Definitions for DSDP Relaxations

> **Date:** 2026-07-18
> **Source:** User-provided differential-algebraic formalizations
> **Use:** Reference when encoding ADE constraints in Irene's DSDP framework

---

## 1. sinh/cosh

**First-order system:** $d_x y = z$, $d_x z = y$

**Algebraic invariant:** $z^2 - y^2 - 1 = 0$

**Differential ideal:**
$$\mathcal{I}_{\text{ADE}} = [ d_x y - z, \ d_x z - y, \ z^2 - y^2 - 1 ]$$

**Initial conditions:** $y(0) = 0$, $z(0) = 1$ (sinh=0, cosh=1 at origin)

**Compactification:** The hyperbola $z^2-y^2=1$ is non-compact. Archimedean boxing
with finite $B$ is required for Putinar's condition to hold.

**Dual-ADE:** Use $w = 1/z$ (inverse derivative for $y$):
$d_x(w) = -y w^2$, with $z w = 1$

---

## 2. log(y)

**First-order system (with auxiliary $v = 1/y$):**
$$D w = v, \quad D v = -v^2$$
where $D = d/dy$ and $w = \log(y)$

**Algebraic constraint:** $y v - 1 = 0$

**Differential ideal:**
$$\mathcal{I}_{\text{ADE}} = [ D w - v, \ D v + v^2, \ y v - 1 ]$$

**Consistency check:** $D(yv-1) = v + y(-v^2) = v(1-yv) \in \mathcal{I}_{\text{ADE}}$ ✓

**Initial condition:** $w(1) = 0$, $v(1) = 1$ (log(1)=0, 1/1=1)
Note: cannot anchor at $y=0$ due to singularity.

**Compactification:** Must strictly bound $y$ away from $0$:
$K = \{ (y,w,v) \mid \epsilon \leq y \leq B,\ yv=1,\ v \in [1/B, 1/\epsilon] \}$

**DSDP encoding challenge:** Derivation $D = d/dy$ requires dual-derivation
framework (Irene currently supports only $d/dx$). Workaround: encode via
exponential $y = e^t$ with $t$ as primary derivation variable.

---

## 3. Bessel $J_0(x)$

**First-order system (with auxiliary $t = 1/x$):**
$$D y_1 = -y_2, \quad D y_2 = y_1 - t y_2, \quad D t = -t^2$$

**Algebraic constraint:** $x t - 1 = 0$

**Differential ideal:**
$$\mathcal{I}_{\text{ADE}} = [ D y_1 + y_2, \ D y_2 - y_1 + t y_2, \ D t + t^2, \ x t - 1 ]$$

**Consistency:** $D(x t - 1) = t(1 - x t) \in \mathcal{I}_{\text{ADE}}$ ✓

**Initial conditions:** Cannot anchor at $x=0$ (singularity for $t=1/x$).
Use $x=1$: $J_0(1) \approx 0.765$, $J_1(1) \approx 0.440$, $t(1) = 1$

**Generator count:** $\{x, y_1, y_2, t\}$ × 2 (primary + derivative symbols) = 8.
At order 2 → large SDP, likely timeout. Reduce: replace $t$ with explicit
bounds if domain is away from $x=0$.

**Boundedness:** $|J_0(x)| \leq 1$ and $|J_1(x)| \leq 1$ for $x \geq 0$, but
this is analytic, not algebraic. Must manually inject box constraints.

---

## 4. Airy $\operatorname{Ai}(x)$

**First-order system:**
$$D y_1 = y_2, \quad D y_2 = x y_1$$

**Differential ideal:**
$$\mathcal{I}_{\text{ADE}} = [ D y_1 - y_2, \ D y_2 - x y_1 ]$$

**No polynomial invariant.** Unlike $\sin/\cos$ ($y^2+z^2=1$) or $\sinh/\cosh$
($z^2-y^2=1$), Airy has no autonomous invariant. The Wronskian involves $\operatorname{Bi}(x)$.

**Initial conditions:** $y_1(0) = \frac{1}{3^{2/3}\Gamma(2/3)} \approx 0.355$,
$y_2(0) = -\frac{1}{3^{1/3}\Gamma(1/3)} \approx -0.259$

**Dual-ADE attempt:** $u = 1/y_2$, $d_x(u) = -x y_1 u^2$.
Result: gap improved from 1093% → 139% but far from tight. Lack of invariant
is fundamental.

**Riccati form:** $u = y_2/y_1$ satisfies $Du = x - u^2$. But $u$ diverges
at roots of $\operatorname{Ai}(x)$ → dangerous for SDP.

---

## 5. $\tan(x)$

**First-order (autonomous, single-variable):**
$$d_x y = 1 + y^2$$

**Differential ideal:**
$$\mathcal{I}_{\text{ADE}} = [ D y - y^2 - 1 ] \subset \mathbb{R}[x]\{y\}$$

**Family ambiguity:** Solutions are $y(x) = \tan(x - C)$ for any $C$.
To isolate $y = \tan(x)$, adjoin initial condition $y(0) = 0$.

**Compactification (critical):** The solution blows up at $x = \pm\pi/2$.
Restrict to $[-B, B]$ with $B < \pi/2$, and add $M^2 - y^2 \geq 0$ where
$M = \tan(B)$. Without this, moments diverge and the SDP becomes infeasible.

**Irene encoding:**
```python
x, y = symbols('x y')
tmp = DSDPRelaxations([x, y])
dm = {x: 1, y: 1 + y**2}
dsyms, rels, gens = tmp.build_ade_relations(dm)
dsdp = DSDPRelaxations(gens=gens, relations=rels, box_size=B, original_gens=[x, y])
dsdp.AddConstraint(M**2 - y**2 >= 0)  # B < pi/2
```

**KNOWN DEAD END (2026-07-18):** Compactification alone doesn't resolve the
manifold-vs-curve gap at d≤2. The ADE d_x(y)=1+y² defines the family
tan(x+C) — all members satisfy it. Without encoding y(0)=0 as a moment
constraint, the SDP bound reduces to the box bound -B².

**Dual-ADE attempt:** Using v = 1/(1+y²) with d_x(v) = -2yv² and (1+y²)v=1.
Failed — no change from baseline (~10¹⁷% gap).
