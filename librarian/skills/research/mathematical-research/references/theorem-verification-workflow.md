# Theorem Verification and Proof Simplification Workflow

Techniques for verifying mathematical claims, catching errors, and simplifying
proofs during manuscript revision. Based on the Positivstellensatz manuscript
refinement session.

## Formula verification via paper examples

When a paper states a formula (e.g., the objective of a GP), do NOT trust
the text extraction alone — cross-check against the paper's worked examples.

**Pattern:**
1. Extract the formula from the paper text.
2. Locate a concrete example in the paper where specific values are substituted.
3. Compute both YOUR reconstruction and the paper's formula on the example.
4. If the exponents don't match, your reconstruction is wrong.
5. Re-read the original (not extracted) source — PDF text extraction garbles equations.

**Concrete case:** The Dressler-Iliman-de Wolff (2019) Program (3.2) objective.
Extracted text suggested `(1/λ₀)·b^{λ₀}·Π(λⱼ/a)^{λⱼ}`. But Example 3.3
(λ₀=0.3, λ₁=0.3, λ₂=0.4) gave `a₁^{-1}` and `a₂^{-4/3}` — exponents that
match `λⱼ/λ₀ = 1, 4/3`, NOT `λⱼ = 0.3, 0.4`. The correct formula is
`λ₀·b^{1/λ₀}·Π(λⱼ/a)^{λⱼ/λ₀}`.

## Inequality chain verification

When a manuscript claims a chain like $A \subseteq B \subseteq C$, test with
known counterexamples from the same paper:

- **SOS vs SONC:** Choi-Lam form $Q$ is SONC but not SOS. $x^4 + y^4$ is SOS
  (via $(x^2)^2 + (y^2)^2$) but not a circuit polynomial. Both are correct.
  Therefore $f^{\text{SOS}} \leq f^{\text{SONC}}$ is FALSE — the cones are
  incomparable. Use $\max\{f^{\text{SOS}}, f^{\text{SONC}}\}$.

- **SOS ⊆ $T_{\text{mean}}^{(1)}$:** $(x^3 + y^5)^2$ is SOS but its argument
  is not a linear form. Requires products (depth >1). Qualify: SOS ⊆
  $T_{\text{mean}}^{(d_r)}$ with $d_r = O(r)$, not $T_{\text{mean}}^{(1)}$.

## Proof simplification pattern

When a proof uses induction over a structure (variables, monomials) but a
direct identity suffices:

**Before (four-step):** Linear $L^2 \in T$ → $L \in T-T$ via $(L+1)^2/4-(L-1)^2/4$
→ closure under multiplication → all monomials → all polynomials.

**After (one-step):** For any $p$, $p = (p+1)^2/4 - (p-1)^2/4$.
Since $(p±1)^2$ are squares, they are PSD, so $M_{2,1}((p±1,0),(1,1)) \in T$.
Done. No induction, no multiplication closure, no restriction on $p$.

**Signal:** If the proof enumerates a basis (linear forms, monomials), ask
whether the key identity can be applied directly to arbitrary elements.

## Definition relaxation check

When a definition restricts arguments (e.g., "$L_i$ must be monomial or linear"),
trace through every theorem to see whether the restriction is used:

- Lemma 6.2: pure algebra → no restriction needed ✓
- Theorem 6.4: the identity $p = ((p+1)^2-(p-1)^2)/4$ works for any $p$ → no restriction needed ✓
- §7 GP formulation: posynomial decomposition genuinely requires monomials or
  nonnegative-coefficient linear forms → restriction ONLY for computation

**Result:** The restriction should be removed from theoretical statements
and presented as a computational specialization in §7.
