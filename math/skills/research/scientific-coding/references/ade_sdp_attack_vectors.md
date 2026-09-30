# ADE+SDP Numerical Improvement — Research Attack Vectors

Condensed knowledge bank of concrete approaches for improving numerical
results in the Differential SDP (DSDP) relaxation framework. Each entry
includes the barrier, attack vector, feasibility assessment, and the key
external reference that supports it.

---

## Gap Map (current state)

| Barrier | Gap | Dominant Cause |
|---|---|---|
| P7 Torus-Curve | 8.34% | S¹×S¹ torus ≠ 1D curve at d=2 |
| P8 Logarithmic | 10.73% | log(y) has no polynomial invariant |
| Exponential ADE | 55–2484% | yz=1 relation weak for asymmetric exp |
| tan Manifold | ~10¹⁷% | ADE defines 2D manifold; graph is 1D curve |
| KKT Boundary | Regression | ∇L=0 over-constrains at d≤2 for boundary-optima |

---

## Attack Vector A: Dual-ADE — Groebner-Constrained Derivative Encoding (Priority: ⭐⭐⭐⭐⭐)

**Barrier:** Exponential ADE (55–2484% gap)

**Status:** ✅ VERIFIED 2026-07-18 — exp-x² gap reduced from 55% → 9.4% (6× tightening)

**Core idea:** Use derivative symbols in the Groebner basis to constrain the
moment matrix (forces $M[d_y]=M[y]$, $M[d_u]=-M[u]$), combined with the
algebraic reciprocal $yu=1$ via `AddConstraint` (NOT via `relations`). This
keeps the auxiliary variable $u$ as a generator rather than having Groebner
eliminate it.

**CRITICAL:** The original version of this vector (derivative-coupled yz=1)
is a **CONFIRMED DEAD END** — see `ade_sdp_dead_ends_and_pitfalls.md`.
Putting the reciprocal in `relations` (Groebner) eliminates the auxiliary
variable, destroying the structural constraint. The fix is `AddConstraint`.

**Implementation:**
```python
x, y, u = symbols('x y u')
tmp = DSDPRelaxations([x, y, u])
dm = {x: 1, y: y, u: -u}   # d_x(y)=y, d_x(1/y)=-1/y
dsyms, rels, gens = tmp.build_ade_relations(dm)
dsdp = DSDPRelaxations(gens, relations=rels, original_gens=[x, y, u])
dsdp.SetObjective(y - x**2)
dsdp.AddConstraint(Eq(y*u - 1, 0))  # ← MUST be AddConstraint, NOT relations
dsdp.AddConstraint(y >= 0.001)
lb = dsdp.solve(order=2)   # → -3.5000 (9.44%) vs old -5.9999 (55.25%)
```

**Expanded results across functions:**
| Function | Old Gap | Dual-ADE Gap | Verdict |
|---|---|---|---|
| $e^x - x^2$ | 55.25% | 9.44% | ✅ Works |
| $\cosh x - 1$ | near-exact | near-exact | ✅ No regression |
| Airy $\operatorname{Ai}(x)$ | 1093% | 139% | Partial (no invariant) |
| $\tan(x)^2 - x^2$ | ~10¹⁷% | ~10¹⁷% | ❌ Manifold-vs-curve |
| $\log(y) - y^2$ | 88.6% | 88.6% | ❌ Inverse problem |

See `ade_sdp_dual_ade_technique.md` for full recipe and mechanism.

---

## Attack Vector B: Fourier Moment Matching (Priority: ⭐⭐⭐⭐)

**Barrier:** P7 Torus-Curve (8.34% residual)

**Core idea:** Pre-compute analytical mixed moments of sinᵏ(πt)·sechᵐ(t)
via Chebyshev/Fourier expansions. Add these as explicit `Mom()` constraints
to pin the SDP to the actual 1D curve within the S¹×S¹ torus.

**Why it works:** At d=2, the SDP can't distinguish the torus from the
curve. Direct moment injection bypasses Groebner and tells the relaxation
exactly which curve to optimize over.

**Implementation plan:**
1. Compute Chebyshev expansion of sech(t) on [-π,π] (degree 8–12)
2. From Chebyshev coefficients, compute mixed moments with sin/cos
3. Add `Mom(sinᵏ(πx)·sechᵐ(x)) = computed_value` as constraints
4. Re-run P7 with moment constraints

**Expected:** Gap from 8.34% → < 3%

**Feasibility:** Medium-High — Irene supports `Mom()` constraints directly.

**Risk:** Low-Med — pre-computed moments must be accurate on truncated domain.

**Reference:** exp4-MOM-B results in `DSDP_Synthesis_Numerical_Experiments_2026-07-17.md`

---

## Attack Vector C: Log-Polynomial Moment Hierarchy (Priority: ⭐⭐⭐⭐⭐)

**Barrier:** P8 Logarithmic Gap (10.73% floor)

**Core idea:** Adapt the moment hierarchy from Choi, Nie, Tang, Zhong (2026)
— "Log-Polynomial Optimization" [arXiv:2601.02797] — to handle log(p(x))
directly in moment space. The paper proves that log(polynomial) objectives
can be handled via concave log-linear objectives over SDP-constrained
moment variables — **no polynomial invariant for log is needed**.

**Key theorem (paraphrased):** For `max Σ a_i log(p_i(x))` with a_i > 0,
Archimedean constraints, the moment relaxation hierarchy converges.

**Adaptation for P8:**
- Handle `x·log(y)` via log-polynomial moment framework
- Handle `sin(πx)·e^x` via coupled oscillatory ADE lift
- Combine in a hybrid SDP with log-linear objective + SDP constraints

**Reference:** Choi, Nie, Tang, Zhong. "Log-Polynomial Optimization." arXiv:2601.02797 (January 2026). 24 pages. The paper uses MOSEK for the log-linear+SDP solver backend.

**Expected:** P8 gap from 10.73% → potentially near-exact

**Feasibility:** Medium — requires implementing the log-polynomial moment hierarchy over Irene's SDP infrastructure.

---

## Attack Vector D: Initial Condition Encoding for tan(x) (⭐⭐⭐)

**Barrier:** tan Manifold-vs-Curve (~10¹⁷% gap)

**Core idea:** ADE `u' = 1+u²` defines solutions `u(x) = tan(x + C)`.
Adding initial condition `u(0) = 0` pins C = 0 and eliminates the manifold
ambiguity.

**Implementation challenge:** Point-evaluation constraints require Dirac
delta measures, which the standard moment hierarchy doesn't natively support.
Possible workarounds: add generator t with constraint t·x=0 to encode x=0
locus, then add localizing matrix constraint for u at that locus.

**Risk:** High — may break Putinar Archimedean condition.

---

## Attack Vector E: KKT Complementary Slackness (⭐⭐)

**Barrier:** KKT at d≤2 over-constrains boundary-optimum problems

**Known workaround:** Don't use KKT for boundary-optimum problems at orders < 3.
This is documented in `DSDP_Synthesis_Numerical_Experiments_2026-07-17.md`
Section 9: "KKT+ADE instability: KKT degrades ADE bounds at d ≤ 3."

**Alternative approaches:**
- Selective KKT: skip ∇L=0 for variables at box boundary
- Fritz John conditions instead of KKT (weaker, less prone to over-constraining)

---

## Research Synthesis Methodology

The following workflow was used to generate the above attack vectors:

1. **Review existing barriers** — load the comprehensive synthesis report and forward plan
2. **Search literature** — arXiv, Google Scholar for keywords:
   - "log-polynomial optimization moment hierarchy" → found Choi et al. 2026
   - "exponential convergence SOS hierarchy trigonometric polynomials" → found Bach 2022
   - "moment SOS hierarchy algebraic differential equations" → no direct hits (confirms novelty of DSDP approach)
3. **Extract and read directly applicable papers** — use web_extract on PDF links
4. **Synthesize into priority matrix** — score each attack vector on:
   - Expected gap reduction
   - Implementation feasibility (existing Irene infrastructure?)
   - Risk (Groebner bottleneck? numerical stability?)
5. **Write concrete experiment scripts** for top candidates
6. **Save as reference** for future sessions to build on

---

## Key External References

| Paper | Key Result | Relevance |
|---|---|---|
| Choi, Nie, Tang, Zhong (2026). "Log-Polynomial Optimization." arXiv:2601.02797 | Moment hierarchy for log(polynomial) objectives; concave log-linear SDP relaxations | Directly applicable to P8 (log barrier) |
| Bach (2022). "Exponential convergence of sum-of-squares hierarchies for trigonometric polynomials." arXiv:2211.04889 | SOS hierarchy converges exponentially fast for trig polynomials | Explains why trig-only DSDP tests are near-exact |
| Lasserre (2024). "The Moment-SOS hierarchy: Applications and related topics." Acta Numerica | Survey of state-of-the-art | Background |
| Slot (2024). "Degree bounds for Putinar's Positivstellensatz on the hypercube." SIAGA | Worst-case degree bounds | Context for depth limits |
