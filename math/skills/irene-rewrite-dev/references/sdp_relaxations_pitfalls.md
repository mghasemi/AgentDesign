# SDPRelaxations (Moment/SOS) Pitfalls

Created 2026-08-17. Context: norm-dependent gap analysis (OptimizationInNorm,
Vikunja #31) computing SOS lower bounds for Motzkin/Robinson forms via
`SDPRelaxations`. Four traps produce **silently-invalid** bounds — the SDP returns
a finite number, so nothing raises and the wrong value looks plausible.

## 1. Box constraints MUST be quadratic, not linear

Linear box constraints (`B - x`, `B - y`) define a **half-space**, not a bounded box
in the moment relaxation. The SDP then returns an invalid (often trivially `1.0`)
bound. Use quadratic box constraints:

```python
B = 2.0
rlx.AddConstraint(B**2 - x**2 >= 0)   # ✓ bounded box (RELATIONAL form!)
rlx.AddConstraint(B**2 - y**2 >= 0)
# ✗ WRONG: rlx.AddConstraint(B - x >= 0)  → half-space, invalid bound
```

Note the `>= 0` — a bare polynomial is silently dropped by `AddConstraint`, see §6.

Symptom: Robinson form returns SOS bound `1.0` instead of the true `0.7037`.

## 2. Build every polynomial from the SAME `SemigroupAlgebra` instance

If the objective/constraint polynomials are built from a module-level `sga` but a
freshly-constructed `SemigroupAlgebra` is passed to `SDPRelaxations` (or vice
versa), the monomial bases don't align and the bound is silently wrong. Build every
polynomial INSIDE the function from the same `sga` instance you pass to the
relaxation.

## 3. `RelaxationDeg` forces `MmntOrd ≥ ObjHalfDeg`

`SDPRelaxations.RelaxationDeg` (relaxations.py ~601-612) clamps the moment order to
at least the objective's half-degree. For Motzkin (deg 4 → ObjHalfDeg 3), relaxation
orders d=1,2,3 ALL map to moment order 3, giving **bit-identical** SOS bounds. This
is mathematically necessary (a degree-4 SOS certificate needs order ≥ 2, and the
localizing constraints push it to 3) — NOT a bug. Use the highest requested d as
the correct baseline.

## 4. `globalMinSOS()` is PURE SOS (not max of SOS and SONC)

`SOSONCRelaxations.globalMinSOS()` returns the pure SOS bound. The SOS+SONC
combination lives in `globalMinSOSPSONC(first='sos'|'sonc')`. Use `globalMinSOS()`
directly for the sup-norm (ρ_d^(∞)) baseline.

## Related: Lp quantile relaxation produces UPPER bounds

The primal Lp quantile relaxation
`γ_p*(ε) = sup{γ : ||(f-γ)_-||_{Lp} ≤ ε}` produces **upper** bounds (γ_p* ≥ f*),
not lower bounds. Topological justification (user-confirmed, numerically verified
in `OptimizationInNorm/experiments/e1_4_topological_justification.py`): on a finite
measure space, Lp norms are monotone for 1 ≤ p < q ≤ ∞, so the SOS/SONC closures
nest `Σ̄^(∞) ⊆ Σ̄^(q) ⊆ Σ̄^(p)`. The L∞ closure enforces pointwise nonnegativity
(valid lower bound); the larger Lp closure (p < ∞) admits an Lp-small but nonzero
negative part (upper bound). Monotone chain: ρ_d^(∞) ≤ ρ_d^(q) ≤ ρ_d^(p).

Note: this is the **primal Lp quantile** object. It is distinct from the **dual
moment relaxation** with the CGIK continuity bound (conjecture C1), whose ordering
is governed by the CGIK bound and dual feasible-region size — still open.

## 5. Equality constraints → `relations=`, never `Mom(g)==0` / `AddConstraint(Eq)` — user instruction (2026-09-26, restated)

Standing rule when building relaxations on Irene: an equality constraint that
holds **identically** on the feasible set must be passed as a **relation** to
the constructor — never as a moment constraint `Mom(g)==0`, never via
`AddConstraint(Eq)`.

```python
# ✓ equality → relations: exact Groebner quotient algebra (both entry points:
#   OptimizationProblem(sga, relations=[...]) AND SDPRelaxations(gens, relations=[...]))
rlx = SDPRelaxations([x, y], relations=[x + y - 1])
rlx.AddConstraint(B**2 - x**2 >= 0)   # only genuine inequalities — RELATIONAL form!

# ✗ equality as a MOMENT constraint: imposes E[g] = 0, not g ≡ 0
rlx = SDPRelaxations([x, y])
rlx.MomentConstraint(Mom(x + y - 1) == 0)

# ✗ equality via AddConstraint(Eq): becomes two localizing matrices ±ε
rlx.AddConstraint(sp.Eq(x + y, 1))
```

Why: `SDPRelaxations.__init__` (relaxations.py ~291–309) builds a Groebner basis
of ⟨relations⟩ and reduces every objective/constraint polynomial exactly modulo
it. By contrast:

- `MomentConstraint(Mom(g)==0)` (relaxations.py ~507–532) records only the scalar
  moment condition `E[g] = rhs` in `MomConst` — it is a condition on the **moment
  sequence**, not on the feasible set, so it changes nothing about the quotient
  algebra and leaves the full un-reduced monomial basis in place. The `eq` branch
  additionally splits into `rhs ∓ ErrorTolerance`, i.e. a relaxed two-sided
  inequality rather than an identity.
- The EQ branch of `AddConstraint` (relaxations.py ~495–505) appends
  `ErrorTolerance ± expr` as two localizing matrices — numerically loose,
  doubles the matrix count, and pollutes the quotient basis with near-zero rows.

Verified cost of the moment-constraint route (re-runnable probe
`scripts/probe_relations_vs_mom.py`, order-2 relaxation for `min x + y s.t.
xy = 1`): reduced basis size **9 with `relations=[xy-1]`** vs **15 with
`MomentConstraint(Mom(xy-1)==0)`** — same problem, 40 % more moment variables
plus two slack localizing blocks. Prefer `relations=` on both counts: exactness
(identity, not a moment) and a strictly smaller SDP.

How to probe this class of question: discriminate on **structural accounting**
(basis size, localizing-block count, moment-constraint count) — NOT on a bound
gap. The moment matrix's PSD already encodes the Jensen / Cauchy–Schwarz
inequalities that hold on the variety, so a moment-constrained relaxation often
returns the same bound as the quotient one; and a probe model whose objective is
unbounded below in the relation-free relaxation makes `Minimize()` report
`Infeasible`, hiding everything.

Un-resolved observation to keep in mind: on this model family the
relation-reduced case **also** reported `status='Infeasible'` at orders 1–2,
even though `min x + y` over `xy = 1` is 2. Treat `Infeasible` on a
quotient-algebra relaxation as un-diagnosed, and check the truncation against an
explicit feasible measure (the point mass at the known optimum) before
concluding anything about feasibility.

Caveat: relations model equalities true **identically** on the variety. If an
"equality" holds only at feasible points through complementarity (e.g. a KKT
multiplier condition with complementary slackness), it belongs in the SDP as a
corresponding PSD/localizing condition, not in `relations`.

## 6. `AddConstraint` requires RELATIONAL form — bare polynomials are SILENTLY dropped

Verified bug (2026-09-26; full report `/home/YOUR-USER/Code/Python/Reports/Irene_addconstraint_bug_2026-09-26.md`):
`AddConstraint(bare_poly)` matches no relational type in the dispatch and is recorded
only in `OrgConst`, NEVER in `Constraints`. The SDP then solves **unconstrained** while
`latex_code()` still prints the constraint under "subject to". Empirical: min x on box
[-1,1]² → bare form returns `-112.07` (status Optimal!), relational `g >= 0` returns
`-1.0` ✓; no warning raised.

```python
rlx.AddConstraint(g)          # ✗ SILENTLY DROPPED — unconstrained SDP, fake answer
rlx.AddConstraint(g >= 0)     # ✓ localizing matrix registered
```
Rule: every `AddConstraint` call on a directly-constructed relaxation MUST carry a
relational operator. Defensive check after setup:
`assert len(rlx.Constraints) == <number of AddConstraint calls>`.
The high-level path is safe: `OptimizationProblem.constraints` are wrapped as
`expr >= 0` by `SDPRelaxations.from_problem` (relaxations.py ~341).
