# ADE+SDP Attack Vectors — Confirmed Dead Ends & Experimental Evidence

> **Date:** 2026-07-18 (verified experimentally)
> **Parent:** ade_sdp_attack_vectors.md — update that file to cross-reference these results.

---

## Confirmed Dead End: Differential Exponential ADE (Vector A)

**Tested:** 2026-07-18 with patched `dsdp.py` (Eq fix applied).

**Setup:** Added `build_ade_relations({x:1, y:y, z:-z})` to generate derivative
symbols d_x, d_y, d_z and relations `d_x-1=0, d_y-y=0, d_z+z=0`. Combined
with algebraic `yz-1=0` **as a `relations` entry** (Groebner basis — NOT
AddConstraint).

**Results:**
- Exp-x²: LB = -5.999999983 (gap 55.25%) — **identical to yz-1-only baseline**
- Cosh: LB = -4.500000326 — did NOT reproduce D2 Phase D near-exact result

**Root cause:** When yz-1 is in the Groebner basis (relations), the GB eliminates
the auxiliary variable z. The derivative symbols are also eliminated — they add
no new algebraic constraints on (x,y,z) beyond yz-1. The quotient algebra is
unchanged.

**Verdict:** DEAD END — derivative-coupled ADE with reciprocal in relations.

**CRITICAL DISTINCTION:** The **dual-ADE technique** is a DIFFERENT mechanism
that DOES work (exp-x² gap 55% → 9.4%). The difference: in dual-ADE, the
reciprocal goes through `AddConstraint` (localizing matrices) while derivative
relations stay in Groebner. This prevents the Groebner basis from eliminating
the auxiliary variable, creating a structurally constrained moment matrix.
See `ade_sdp_dual_ade_technique.md` for the full recipe.

---

## Confirmed: P7 d=3 Is Computationally Prohibitive (Vector B)

**Tested:** 2026-07-18. P7 problem: min(x·sin(xy) + y·sech(xy)) on [-π,π]².
6 generators (x, y, v1, v2, q, s), 2 circle relations.

**Results:**
- d=2, Parallel=False: succeeds in 39s, LB = -6.28318522 (gap 88.04%)
- d=3, Parallel=True: OSError "Too many open files" (multiprocessing fork bomb)
- d=3, Parallel=False: timed out at 300s

**Verdict:** P7 at d≥3 with 6 generators exceeds practical time budgets.
Generator reduction (dropping v2, s — not in objective) might make d=3
tractable but has not been tested.

---

## Confirmed: Tight Box Constraints Don't Help P7

**Tested:** 2026-07-18. Added explicit bounds on x, y, and then on v1, v2, q, s.

- Simple tight bounds on x,y: no improvement (88.04% unchanged)
- Full variable bounds: SDP becomes **primal infeasible**

**Root cause (infeasibility):** Adding explicit bounds like `v2 >= cos(π²)` while
`v1²+v2²=1` also holds creates a feasible set that IS non-empty in the original
variables, but the SDP relaxation's moment matrix representation can't satisfy
both simultaneously at order 2. The circle relation + box bounds interaction
produces a numerically singular localizing matrix.

**Verdict:** Tight bounds alone can't reduce the torus-curve gap. The 8.34%
residual (achieved by exp4-MOM-B with explicit moment fixing) represents
the practical limit at d=2.

---

## Pitfall: build_ade_relations() Adds Redundant Constraints for Exponential ADE

The `build_ade_relations()` method creates derivative *symbols* and relations
of the form `d_g - expr = 0`. These are reduced away by Groebner when the
derivative symbol is a leading term. The result: no new constraints survive
on the original generators. For the exponential ADE (yz=1), the derivative
relations `d_x(y)=y, d_x(z)=-z` add zero information beyond the algebraic
relation. Adding them only bloats the generator list (from 3 to 6), which
increases SDP matrix sizes without improving bounds.

**Lesson:** Before using `build_ade_relations()`, verify that the derivative
relations are NOT algebraically derivable from existing constraints. If the
quotient algebra already encodes the relation, adding derivatives is waste.

---

## Pitfall: Variable Range Constraints Can Make SDP Infeasible

When adding explicit inequality constraints like `v2 >= 0.90` to DSDP
relaxations, the SDP can become **primal infeasible** even when the original
problem is clearly feasible. This happens because:

1. The moment hierarchy approximates the feasible set at finite order
2. Inequality constraints + algebraic relations can create empty moment cones
   at low relaxation orders
3. The SDP solver's numerical conditioning degrades when tight bounds meet
   polynomial equalities (e.g., `v1²+v2²=1` + `v2 >= 0.90`)

**Workaround:** Instead of explicit variable bounds, use the `box_size` and
`original_gens` parameters to apply Archimedean boxing only to domain variables.
Let the algebraic relations (circle, etc.) handle the constraint geometry.

---

## Successful Pattern: Benchmark Rerun With Snapshot/Compare

This session validated a robust workflow for verifying code-impact on numerical results:

```bash
# 1. Snapshot old results
cp ade_benchmark.json ade_benchmark_before_fix.json

# 2. Re-run with patched code
unset CONDA_SHLVL CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_PYTHON_EXE
conda run -n sage python3 run_ade_benchmark.py

# 3. Compare via execute_code (not terminal — structured diff)
# Load both JSONs, compute per-test delta, produce comparison table

# 4. Add postscript to existing report (don't rewrite the whole thing)
```

This pattern is already documented in `irene_benchmark_comparison.md`.

---

## Successful Pattern: Research Plan Structure

The research plan template used in this session:

1. **Barrier map** — list each gap with dominant cause
2. **Literature search** — targeted arXiv/Google Scholar queries per barrier
3. **Paper extraction** — read PDFs, extract theorems, assess applicability
4. **Attack vector matrix** — per-barrier: approach, core idea, feasibility, expected gap, risk
5. **Experimentation** — test top-priority vectors, confirm dead ends
6. **Tight feedback** — document what worked and what didn't; update attack vectors reference

This structure ensures the next session starts at the frontier, not re-exploring dead ends.

---

## Literature: Key External References

| Paper | Key Result | Directly Applicable? |
|---|---|---|
| Choi, Nie, Tang, Zhong (2026). arXiv:2601.02797 | Moment hierarchy for log(polynomial) objectives | **Yes** — P8 (not yet implemented) |
| Bach (2022). arXiv:2211.04889 | SOS hierarchy converges exponentially for trig polynomials | **Yes** — explains why trig-only tests are near-exact |
| Slot (2026). "Nonconvergence of SOS hierarchy for global polynomial optimization." AIMS | Documents cases where SOS hierarchy fails to converge | Context for fundamental gap existence |

No paper was found that directly addresses differential-algebraic constraints in the Lasserre hierarchy — confirming the DSDP approach is novel research territory.

---

## Confirmed: Tan ADE with Compactification Doesn't Help

**Tested:** 2026-07-18. Tan ADE: d_x(y) = 1 + y², with compactification
M² - y² ≥ 0 where M = tan(B) for B < π/2.

**Results (B=0.5, 1.0, 1.4):**
- All LB values are box bounds (-B²), NOT tan-specific bounds
- d=1: LB = -0.250 (B=0.5 box bound), d=2: LB = -1.0 (B=1.0 box bound)
- B=1.4: diverges as B approaches π/2 (numerical blowup)

**Root cause:** The ADE alone (without a polynomial invariant) is too weak at
d≤2. The derivative relation d_x(y) = 1+y² enters the Groebner basis but
doesn't algebraically constrain y to equal tan(x) in the moment matrix.

**Verdict:** Compactification of the domain doesn't resolve the manifold-vs-curve\ngap. The ADE d_x(y)=1+y² defines the family tan(x+C) — without an initial\ncondition y(0)=0 encoded as a moment constraint, all members satisfy it.\n\n**✅ WORKING ALTERNATIVE:** Tan via sin/cos encoding ($f^2+g^2=1$ + $(f-xg)^2$)\nachieves near-exact at d=1. See `ade_sdp_tan_sincos.md`.

### Dead End: Tan Factorization (y=x·v) Doesn't Help (2026-07-18)

**Setup:** y = tan(x) with y(0)=0 → factor y = x·v where v = tan(x)/x is analytic
at x=0. Derive polynomial ADE: x·dv + v - x²v² - 1 = 0 from d_x(xv) = 1 + (xv)².
Encode via `build_ade_relations({x:1, v:dv})` + AddConstraint for ADE.

**Results:** All LB values are box bounds (-B²). Same as standard ADE encoding.
The factorization structurally guarantees y(0)=0 but doesn't create additional
cross-moment constraints at d≤2.

**Verdict:** Polynomial-invariant-free ADE encodings (even with algebraic
initial conditions) cannot tighten the SDP at low relaxation orders.

---

## Confirmed: Sinh/Cosh Invariant Is Non-Compact (Structural Gap)

**Tested:** 2026-07-18. Sinh/cosh with invariant z²-y²=1 and objective y+z
(which equals e^x on the true solution manifold).

**Results:**
- Baseline (invariant only): LB = -3.73 (gap 2857%, far below true min 0.135)
- Dual-ADE: Same result — derivatives don't tighten

**Root cause:** The hyperbola z²-y²=1 is non-compact. The SDP can pick
(y,z) = (-1.5, -1.803) satisfying invariant + box, giving y+z ≈ -3.3,
while the true sinh(x)+cosh(x) = e^x ≥ e^{-2} ≈ 0.135. Without a bound
on y+z directly, the SDP exploits the non-compactness.

**SOLUTION:** Rational parameterization — see `ade_sdp_rational_parameterization.md`.
This cured the gap (2857% → 0.00005% at d=1) by mapping the hyperbola to a
compact variety via bounded parameter t ∈ (-1, 1).

**Lesson:** Invariant-based ADE encodings only work when the invariant defines
a COMPACT variety (e.g., sin²+cos²=1 → circle). Non-compact varieties (hyperbola)
allow the SDP to produce loose bounds. Rational parameterization is the cure.

### Pitfall: Rational Parameterization — False Positive Risk (2026-07-18)

While rational parameterization gives near-exact results at d=1, the SDP
becomes primal-infeasible at d=2 with numerical explosion (cost → ∞). This
is a conditioning issue — the larger moment matrix at d=2 interacts poorly
with the rational constraint $s(1-t^2)=1$.

**More dangerous pitfall:** When `box_size` constrains $|s| \leq B$ but the ACTUAL
range of $s = 1/(1-t^2)$ is $[1, 1/(1-t_{\max}^2)] \gg B$, the SDP produces
**artificially tight bounds** — a false positive. The box over-restricts the
feasible set, and the SDP returns the optimum of this restricted set (not the
true optimum).

**Fix:** Exclude `s` from `original_gens` and use explicit bounds:
```python
s_max = 1.0 / (1.0 - t_max**2)
dsdp.AddConstraint(s >= 1.0)
dsdp.AddConstraint(s <= s_max)
```

With correct bounds, d=2 and d=3 become infeasible. Since d=1 is already
near-exact, higher orders are unnecessary.

---

## Confirmed: Log-Polynomial Paper Doesn't Directly Apply to P8

**Checked:** 2026-07-18. Choi, Nie, Tang, Zhong (2026) framework requires:
max Σ a_i log(p_i(x)) with a_i > 0 constants, p_i polynomials.

**P8 mismatch:**
- Coefficient on log(y) is x (a VARIABLE, not constant a_i > 0)
- P8 minimizes rather than maximizes
- P8 has non-log terms (y·sin(πx)·e^x)

**Verdict:** The log-polynomial hierarchy is the right theoretical direction but
P8 needs problem reformulation before it can benefit. Direct application fails
because the framework targets MLE/cross-entropy problems, not general optimization
with log terms.
