# ADE+SDP Attack Vectors — Status Updates (Experimental Evidence)

> **Date:** 2026-07-18
> **Parent:** Full taxonomy in `ade_sdp_attack_vectors.md`
> **Dead ends:** `ade_sdp_dead_ends_and_pitfalls.md`

This file records status updates based on experimental runs. Apply these
annotations to the main `ade_sdp_attack_vectors.md` next time you edit it.

---

## Verified Breakthroughs (2026-07-18)

| Technique | Function | Before | After | Reference |
|---|---|---|---|---|
| Dual-ADE | exp-x² | 55% gap | **9.44%** | ade_sdp_dual_ade_technique.md |
| Tan via sin/cos | tan | ~10¹⁷% gap | **~5×10⁻⁹** | ade_sdp_tan_sincos.md |
| P7 holonomic | torus-curve | 88%/8.34% gap | **5.98% at d=1** | ade_sdp_p7_holonomic.md |
| Rational param. | sinh/cosh | 2857% gap | **~0%** (⚠️ fragile, see pitfall) | ade_sdp_rational_parameterization.md |

## Confirmed Dead Ends

| Technique | Function | Result |
|---|---|---|
| Derivative-coupled ADE | exp-x² | No change |
| P7 d=3 | torus-curve | Timeout |
| Tight box bounds | P7 | No change |
| Tan ADE compactification | tan | Box bound |
| Tan y=x·v factorization | tan | Box bound |
| Dual-ADE for log | P8 | No change |
| Dual-ADE for tan | tan | No change |
| Log-polynomial hierarchy | P8 | Framework mismatch |
| Rational param. d≥2 | sinh/cosh | Numerically infeasible |

### Rational param. pitfall (2026-07-18) ⚠️

The rational parameterization for sinh/cosh is a **fragile breakthrough**.
When box_size constrains $|s| \leq B$ but $s = 1/(1-t^2) \gg B$, the SDP
returns artificially tight bounds (false positive). With correct bounds,
d=2 and d=3 become numerically infeasible (primal/dual gap → 10¹⁰).
d=1 is already near-exact, so higher orders are unnecessary.

## The Invariant Principle

ADE encodings at d≤2 are **tight iff** a compact polynomial invariant exists:
- ✅ $yu=1$ (exp, via dual-ADE), $f^2+g^2=1$ (trig, via tan-sin/cos),
  $u^2+v^2=1, w^2-s^2=1, wr=1$ (trig+hyp, via P7 holonomic)
- ❌ No invariant → box bound at any order (tan ADE, Airy, log)

---

### Vector A: Differential Exponential ADE — **DEAD END (confirmed)**

Originally rated ⭐⭐⭐⭐⭐. Tested 2026-07-18 with patched dsdp.py.
Adding build_ade_relations({x:1, y:y, z:-z}) + yz=1 **as a relation**
produced zero improvement: gap unchanged at 55% for Exp-x². The
derivative symbols are Groebner-eliminated — they add no new algebraic
constraints on (x,y,z) beyond yz=1.

**CRITICAL DISTINCTION:** A *different* mechanism — dual-ADE — was
discovered that DOES work. The difference: put the reciprocal constraint
(yu=1) through `AddConstraint` (localizing matrices) instead of
`relations` (Groebner). This prevents the Groebner basis from eliminating
the auxiliary variable. See `ade_sdp_dual_ade_technique.md`.

**Update:** Vector A (derivative-coupled exp ADE) is confirmed DEAD END.
But the dual-ADE technique (AddConstraint path) is a separate, verified
mechanism: exp-x² gap 55% → 9.4%. Do NOT conflate the two.

---

### NEW: Dual-ADE Technique — **VERIFIED (exp-x² 55%→9.4%)**

Discovered 2026-07-18. A new Groebner-constrained derivative encoding
mechanism. See `ade_sdp_dual_ade_technique.md` for full recipe.

**How it differs from Vector A (dead end):**
- Vector A: put `yz=1` in `relations` → Groebner eliminates z
- Dual-ADE: put `yu=1` in `AddConstraint` → Groebner keeps u as generator
  while ALSO reducing derivative symbols (du→-u, dy→y, dx→1)

**Mechanism:** Derivative relations in the Groebner basis force specific
moment matrix entries (e.g., M[dy] = M[y]). The auxiliary variable u is
NOT eliminated (it's in AddConstraint), so the moment matrix has an extra
dimension. The combined PSD condition is structurally tighter.

**Tested on:**
- exp-x²: LB = -3.5000 (9.44%) vs old -5.9999 (55.25%) → **6× tighter**
- cosh: Already near-exact (confirming no regression)
- tan: No improvement (manifold-vs-curve is fundamental, not constraint-routing)

**Generalization candidates:** Any function with first-order ODE dy/dx=g(x,y)
where g is polynomial AND d_x(1/g) simplifies to polynomial in generators.

---

### Vector B: Fourier Moment Matching / Higher Order — **d=3 PROHIBITIVE**

P7 at d=3 with 6 generators exceeds 300s budget. d=2+Parallel=False
succeeds in 39s (88.04% gap, matching baseline). d=3 times out
regardless of parallel mode (Parallel=True hits OSError "too many open
files"; Parallel=False exceeds 300s).

**Update:** Generator reduction (drop v2, s — not in objective) may make
d=3 tractable but is untested. Until then, P7 d=3 is rated as PROHIBITIVE.

---

### Tight Box Constraints — **DO NOT WORK for P7**

Simple bounds on x,y: no gap change from 88.04%.
Full variable bounds (v1,v2,q,s): primal infeasible.
Explicit inequality constraints conflict with circle invariants at order 2.

**Lesson:** The 8.34% residual achieved by exp4-MOM-B (tight bounds +
moment fixing on x,y) represents the practical limit at d=2.
Don't waste time on tighter bounds without moment fixing.

---

### Log-Polynomial Hierarchy (Choi et al. 2026) — **NOT DIRECTLY APPLICABLE to P8 (2026-07-18)**

Paper: Choi, Nie, Tang, Zhong (2026, arXiv:2601.02797). Proposes a moment
hierarchy for $\max \sum a_i \log(p_i(x))$ where $a_i > 0$ are **constants**
and $p_i$ are polynomials. Designed for MLE / cross-entropy problems.

**P8 incompatibility with the framework:**

| Requirement | P8 ($\min x\!\cdot\!\log(y) - y\!\cdot\!\sin(\pi x)\!\cdot\!e^x$) |
|---|---|
| Maximization ($\max$) | Minimization ($\min$) — sign flip possible but breaks $a_i>0$ |
| $a_i > 0$ constants | Coefficient of $\log(y)$ is $x$ (variable, can be negative) |
| $p_i$ polynomials | $\log(y)$ is log of monomial (OK), but mixed with $-y\sin(\pi x)e^x$ |
| Pure log-sum | Contains non-log transcendental term |

**What would be needed for P8:**
1. Reformulate as $\max -x\!\cdot\!\log(y) + y\!\cdot\!\sin(\pi x)\!\cdot\!e^x$
   but $-x$ may be negative → violates $a_i > 0$ requirement
2. Handle transcendental term via ADE (coupled oscillatory lift)
3. Build a **hybrid log-polynomial + DSDP framework** — does not exist yet

**Verdict:** Log-polynomial hierarchy is the right direction for log barriers
theoretically, but requires framework development. Not an immediate win.
The dual-ADE technique (exp-x² 55%→9.4%) is the best near-term improvement.
