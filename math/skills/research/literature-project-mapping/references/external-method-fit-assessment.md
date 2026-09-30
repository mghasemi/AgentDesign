# External Method / Package Fit Assessment

Depth for the "is this a good fit for repo Y, or a different topic?" question.
Companion to the *Fit assessment for an external method or code package* section
in SKILL.md.

## The classifier that saves the most time

Before reading any code, the dependency manifest tells you which side of a
mathematical object a candidate package attacks.

| Manifest signature | What it means | Which side it solves |
|---|---|---|
| `JuMP` / `Convex.jl` / `SDPA` / `cvxpy` / `clarabel` / `SCS` | convex-optimization stack | the **relaxation** of the problem |
| polynomial-system solvers, apolarity libraries, `LinearAlgebra` only | numerical algebraic geometry | the **non-convex** problem directly |
| `DynamicPolynomials` / `MultivariatePolynomials` | symbolic polynomial data structure | either — says nothing about the method |

Two packages targeting the same object from opposite sides are complementary,
not interchangeable: one certifies or bounds, the other constructs. State which
one the host project already is before recommending the other.

## Layered verdict template

Produce this table in the reply; it makes the verdict auditable and prevents
the "it's all related" non-answer.

| Layer | Content | Fit |
|---|---|---|
| convex / dual / moment | cone duality, moment matrices, flatness, atomic measures | usually strong when the host is a relaxation engine |
| target-object decision | deciding membership in the host's own cone | strong if the source gives an *exact* (not merely relaxational) characterization |
| constructive / algorithmic | actually building the decomposition, rank determination | usually **poor** for a relaxation engine — non-convex core, no relaxation structure |
| structural preconditions | surjectivity, Hilbert functions, ideal/quotient data | moderate — cheap, and may reuse existing host machinery |
| application-specific | downstream uses (quadrature, control, complexity bounds) | usually marginal — bloat risk |

Then the three buckets: **adopt** (name the host module the change lands in),
**maybe** (a cheap precondition or test), **don't-adopt** (reason + where the
artifact belongs instead).

## The degenerate-parameterization test

When a source claims a method makes a hard problem tractable, locate the
structural hypothesis it exploits and ask what the method becomes without it.
If the special case matching the host's actual target collapses the method to
the general hard instance, the source does **not** solve the host's problem —
say so explicitly rather than crediting it with a solution it does not provide.

General pattern: an efficiency gain that comes from a *dimension reduction* is
worthless exactly in the regime where no reduction is available.

## Worked boundary: Irene vs. Bechère–Kuhlmann–Mourrain / Σ_{2d}

### What Irene is

Convex-relaxation engine for polynomial optimization: SOS/SONC/SDP hierarchies
(`relaxations.py`, `sdp.py`, `sonc.py`, `sosonc.py`, `dsdp.py`,
`nonpopsdp.py`) plus the structural reductions that shrink them (`sparsity.py`,
`newton_polytope.py`, `border_basis.py`, `symbolic_engine.py`,
`cvxpy_solver.py`).

Vocabulary collisions to be careful about:

- `SDPRelaxations.Decompose()` is a **Cholesky of the Gram blocks** returning the
  SOS multipliers σ_i with `f - f_* = Σ σ_i g_i`. Convex factorisation of a
  solved relaxation — *not* a Waring / rank / tensor decomposition.
- `ExtractSolutionLH` is **Lasserre–Henrion** extraction: SVD of the moment
  matrix → truncate at `NumericalRank()` → multiplication matrices → Schur →
  support points in the *ambient* variable space. No variety-supported variant.
- `grep -rn -i "apolar\|catalecticant\|veronese\|waring" Irene/*.py` → nothing.
  Irene owns the moment-matrix/atom-extraction half of moment theory and none of
  the rank/decomposition geometry.

### What the sources are

- **Bechère–Kuhlmann–Mourrain**, *Symmetric tensor decomposition on rational
  varieties* (arXiv:2606.25712). Three separable layers: (i) dual-cone theorem —
  the dual of the cone of positive q-Symmetric tensors is the set of forms
  non-negative on the variety V_q; (ii) positive Waring decompositions ↔ r-atomic
  representing measures, with flatness `rank(H_0) = rank(H)` plus `H ⪰ 0` giving
  the decomposition; (iii) Algorithm 4.1, which is linear algebra plus a Waring
  routine — `M = A_k^{-1} W A_{hk}`, solve `Mw = v`, Waring-decompose ψ_q(p) in
  the reduced dimension, map back. Layers (i)+(ii) are Irene-shaped; (iii) is not.
- **`QSymDecomposition.jl`** implements Algorithm 4.1. Its deps
  (`TensorDec`, `AlgebraicSolvers`, `DynamicPolynomials`, `LinearAlgebra`) confirm
  no SDP anywhere in the stack.
- **`PowerDecompositions.jl`** is the k-th Waring counterpart: `decompose_powers(F, d)`
  returns real/complex atoms of degree `h = deg(F)/d`, plus `verified`, minimal
  rank, and residual. It is the closest existing implementation of an arbitrary
  "sum of equal powers" membership question, reached by the non-convex route,
  and is best used as a *positive-certificate generator / reference oracle*.
  `verified = false` is not a non-membership proof.

### The Σ_{2d} connection, and its limit

On homogeneous forms the sum-of-even-powers cone restricts to positive linear
combinations of linear-form powers, i.e. exactly a positive Waring cone:

    Σ_{2d} ∩ F_{2d} = { Σ λ_i ℓ_i(X)^{2d} : ℓ_i linear, λ_i > 0 } = CP(2d)

so the moment / atomic-measure characterization of that source *is* the exact
(not merely relaxational) characterization of the cone — the strongest reason to
route its moment layer into a relaxation engine.

Limit to state explicitly: the source's q is a rational map P^m → P^n, and the
computational gain comes only from `m < n`. At `h = 1`, `q_i = Z_i` the variety
is P^n, q-Sym is all symmetric tensors, and the algorithm collapses to the plain
Waring problem. The linear-atom case is exactly that degenerate case, so the
source's *algorithm* does not decide the general membership question — only its
*characterization* transfers.

### Where the parts belong

- **Adopt in Irene:** a variety-supported moment relaxation (moment matrix
  indexed by a q-graded basis, dual condition `p(q(ξ)) ≥ 0` on V_q), the flatness
  test as a pre-extraction guard, and the ψ_q transport (two diagonal multinomial
  rescalings plus one linear solve). Hilbert-function surjectivity of the
  substitution map is computable from the existing `BorderBasis` quotient data.
- **Do not adopt:** Waring rank determination, catalecticant/apolarity machinery,
  polynomial-system solving. Keep such packages as reference oracles for
  cross-validation of a sibling project's outputs, driven via subprocess — do not
  add them as a language-level dependency of a relaxation engine.
